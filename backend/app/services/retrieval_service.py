import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.entities import DocumentChunk, Document
from app.services.embedding_service import embedding_service
from app.core.config import settings

logger = logging.getLogger(__name__)

class RetrievalService:
    def __init__(self):
        self.rrf_k = settings.RRF_K
        self.default_top_k = settings.DEFAULT_TOP_K

    def semantic_search(
        self, 
        query: str, 
        db: Session, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top_k document chunks using vector cosine distance with pgvector.
        """
        query_embedding = embedding_service.embed_text(query)
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        # Using pgvector <=> cosine distance operator
        # Distance = 1 - cosine_similarity. Similarity = 1 - distance.
        sql = text("""
            SELECT 
                dc.id,
                dc.document_id,
                d.title as document_title,
                d.doc_category,
                dc.content,
                dc.page_number,
                (1.0 - (dc.embedding <=> :embedding::vector)) as similarity_score
            FROM document_chunks dc
            JOIN documents d ON d.id = dc.document_id
            WHERE dc.embedding IS NOT NULL AND d.status = 'indexed'
            ORDER BY dc.embedding <=> :embedding::vector ASC
            LIMIT :top_k
        """)

        try:
            results = db.execute(sql, {"embedding": embedding_str, "top_k": top_k}).fetchall()
            candidates = []
            for r in results:
                candidates.append({
                    "id": r.id,
                    "document_id": r.document_id,
                    "document_title": r.document_title,
                    "doc_category": r.doc_category,
                    "content": r.content,
                    "page_number": r.page_number,
                    "semantic_score": float(r.similarity_score) if r.similarity_score is not None else 0.0,
                    "retrieval_method": "semantic_pgvector"
                })
            return candidates
        except Exception as e:
            logger.warning(f"pgvector query failed ({e}), using in-memory cosine fallback.")
            return self._fallback_semantic_search(query_embedding, db, top_k)

    def _fallback_semantic_search(
        self, 
        query_embedding: List[float], 
        db: Session, 
        top_k: int
    ) -> List[Dict[str, Any]]:
        """In-memory cosine similarity fallback in case pgvector extension is unconfigured."""
        import numpy as np
        chunks = (
            db.query(DocumentChunk, Document.title, Document.doc_category)
            .join(Document, Document.id == DocumentChunk.document_id)
            .filter(Document.status == "indexed")
            .all()
        )
        scored = []
        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)

        for chunk, doc_title, category in chunks:
            if chunk.embedding is None:
                continue
            c_vec = np.array(chunk.embedding, dtype=np.float32)
            c_norm = np.linalg.norm(c_vec)
            if q_norm > 0 and c_norm > 0:
                sim = float(np.dot(q_vec, c_vec) / (q_norm * c_norm))
            else:
                sim = 0.0
            scored.append({
                "id": chunk.id,
                "document_id": chunk.document_id,
                "document_title": doc_title,
                "doc_category": category,
                "content": chunk.content,
                "page_number": chunk.page_number,
                "semantic_score": sim,
                "retrieval_method": "semantic_cosine_fallback"
            })
        scored.sort(key=lambda x: x["semantic_score"], reverse=True)
        return scored[:top_k]

    def keyword_search(
        self, 
        query: str, 
        db: Session, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        PostgreSQL Full-Text Search using ts_rank and plainto_tsquery.
        """
        sql = text("""
            SELECT 
                dc.id,
                dc.document_id,
                d.title as document_title,
                d.doc_category,
                dc.content,
                dc.page_number,
                ts_rank(to_tsvector('english', dc.content), plainto_tsquery('english', :query)) as rank_score
            FROM document_chunks dc
            JOIN documents d ON d.id = dc.document_id
            WHERE to_tsvector('english', dc.content) @@ plainto_tsquery('english', :query)
              AND d.status = 'indexed'
            ORDER BY rank_score DESC
            LIMIT :top_k
        """)

        try:
            results = db.execute(sql, {"query": query, "top_k": top_k}).fetchall()
            candidates = []
            for r in results:
                candidates.append({
                    "id": r.id,
                    "document_id": r.document_id,
                    "document_title": r.document_title,
                    "doc_category": r.doc_category,
                    "content": r.content,
                    "page_number": r.page_number,
                    "keyword_score": float(r.rank_score),
                    "retrieval_method": "postgresql_fts"
                })
            return candidates
        except Exception as e:
            logger.warning(f"PostgreSQL FTS failed ({e}), using ILIKE fallback.")
            return self._fallback_keyword_search(query, db, top_k)

    def _fallback_keyword_search(self, query: str, db: Session, top_k: int) -> List[Dict[str, Any]]:
        """Token-based substring matching fallback."""
        tokens = [t.lower() for t in query.split() if len(t) > 2]
        chunks = (
            db.query(DocumentChunk, Document.title, Document.doc_category)
            .join(Document, Document.id == DocumentChunk.document_id)
            .filter(Document.status == "indexed")
            .all()
        )
        scored = []
        for chunk, doc_title, category in chunks:
            content_lower = chunk.content.lower()
            matches = sum(1 for t in tokens if t in content_lower)
            if matches > 0:
                score = matches / max(1, len(tokens))
                scored.append({
                    "id": chunk.id,
                    "document_id": chunk.document_id,
                    "document_title": doc_title,
                    "doc_category": category,
                    "content": chunk.content,
                    "page_number": chunk.page_number,
                    "keyword_score": score,
                    "retrieval_method": "token_match_fallback"
                })
        scored.sort(key=lambda x: x["keyword_score"], reverse=True)
        return scored[:top_k]

    def hybrid_search(
        self, 
        query: str, 
        db: Session, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF) combining Semantic and Keyword rankings.
        RRF Score formula: Score(d) = SUM( 1 / (k + rank_i(d)) ) for each strategy i.
        Avoids double-counting and balances keyword precision with semantic depth.
        """
        # Fetch candidate pools
        pool_size = max(top_k * 2, 10)
        semantic_results = self.semantic_search(query, db, top_k=pool_size)
        keyword_results = self.keyword_search(query, db, top_k=pool_size)

        rrf_scores: Dict[int, float] = {}
        chunk_map: Dict[int, Dict[str, Any]] = {}

        # 1. Score semantic ranks
        for rank, item in enumerate(semantic_results, start=1):
            c_id = item["id"]
            rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (self.rrf_k + rank))
            if c_id not in chunk_map:
                chunk_map[c_id] = item.copy()
            chunk_map[c_id]["semantic_score"] = item.get("semantic_score")

        # 2. Score keyword ranks
        for rank, item in enumerate(keyword_results, start=1):
            c_id = item["id"]
            rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (self.rrf_k + rank))
            if c_id not in chunk_map:
                chunk_map[c_id] = item.copy()
            chunk_map[c_id]["keyword_score"] = item.get("keyword_score")

        # 3. Compile fused ranking
        fused_candidates = []
        for c_id, score in rrf_scores.items():
            entry = chunk_map[c_id]
            entry["rrf_score"] = round(score, 6)
            entry["source_passage_label"] = f"{entry['document_title']} (Page {entry.get('page_number', 1)})"
            fused_candidates.append(entry)

        fused_candidates.sort(key=lambda x: x["rrf_score"], reverse=True)
        return fused_candidates[:top_k]

    def rerank(
        self, 
        query: str, 
        candidates: List[Dict[str, Any]], 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Configurable reranker service with sensible fallback.
        """
        if not candidates or settings.RERANKER_PROVIDER == "none":
            for c in candidates:
                c["rerank_score"] = c.get("rrf_score", 0.0)
            return candidates[:top_k]

        # In production with cross-encoder or cohere, apply reranker
        # Here we apply lexical-overlap boost as local heuristic reranker
        for c in candidates:
            query_terms = set(query.lower().split())
            content_terms = set(c["content"].lower().split())
            overlap = len(query_terms.intersection(content_terms)) / max(1, len(query_terms))
            c["rerank_score"] = round(c.get("rrf_score", 0.0) * (1.0 + overlap), 6)

        candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        return candidates[:top_k]

retrieval_service = RetrievalService()
