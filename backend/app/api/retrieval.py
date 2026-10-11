from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import time
from app.core.database import get_db
from app.schemas.api_schemas import RetrievalInspectResponse, RetrievedChunk
from app.services.retrieval_service import retrieval_service
from app.services.cache_service import cache_service
from app.api.auth import get_current_user

router = APIRouter(prefix="/retrieval", tags=["Retrieval & Explainability"])

@router.get("/inspect", response_model=RetrievalInspectResponse)
def inspect_retrieval(
    q: str = Query(..., description="Customer query or search terms"),
    top_k: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    cache_key = f"retrieval:inspect:{hash(q)}:{top_k}"
    cached = cache_service.get(cache_key)
    if cached:
        return cached

    # Run separate stages for complete explainability
    semantic_cands = retrieval_service.semantic_search(q, db, top_k=top_k)
    keyword_cands = retrieval_service.keyword_search(q, db, top_k=top_k)
    fused_cands = retrieval_service.hybrid_search(q, db, top_k=top_k)
    reranked_cands = retrieval_service.rerank(q, list(fused_cands), top_k=top_k)

    response_data = {
        "query": q,
        "semantic_candidates": semantic_cands,
        "keyword_candidates": keyword_cands,
        "fused_candidates": fused_cands,
        "reranked_candidates": reranked_cands
    }
    cache_service.set(cache_key, response_data, ttl=180)
    return response_data
