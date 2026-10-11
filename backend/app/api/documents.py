import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.core.database import get_db
from app.core.config import settings
from app.models.entities import Document, DocumentChunk, DocumentStatus, User
from app.schemas.api_schemas import DocumentResponse
from app.services.ingestion_service import ingestion_service
from app.services.embedding_service import embedding_service
from app.services.cache_service import cache_service
from app.api.auth import get_current_user

router = APIRouter(prefix="/documents", tags=["Documents & Knowledge Base"])

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Document).order_by(Document.created_at.desc()).all()

@router.post("/upload", response_model=DocumentResponse)
def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str = Form("policy"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate extension
    file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in ["pdf", "txt", "md", "markdown"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format: .{file_ext}. Allowed: .pdf, .txt, .md"
        )

    # Save to disk
    safe_filename = f"{int(datetime.utcnow().timestamp())}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)
    if file_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    # Create document record
    doc = Document(
        title=title,
        filename=file.filename,
        file_path=file_path,
        file_type=file_ext,
        file_size_bytes=file_size,
        doc_category=category,
        status=DocumentStatus.PROCESSING,
        uploaded_by=current_user.id
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Process ingestion and vectorization
    try:
        pages_and_texts = ingestion_service.extract_text_from_file(file_path, file_ext)
        all_chunks = []
        for text_content, page_num in pages_and_texts:
            page_chunks = ingestion_service.chunk_text(text_content, chunk_size=400, overlap=80, page_number=page_num)
            all_chunks.extend(page_chunks)

        if not all_chunks:
            doc.status = DocumentStatus.FAILED
            doc.error_message = "Document contained no extractable text."
            db.commit()
            return doc

        # Generate embeddings in batch
        texts_to_embed = [c["content"] for c in all_chunks]
        embeddings = embedding_service.embed_batch(texts_to_embed)

        for idx, (chunk_data, emb) in enumerate(zip(all_chunks, embeddings)):
            chunk_rec = DocumentChunk(
                document_id=doc.id,
                chunk_index=idx,
                content=chunk_data["content"],
                page_number=chunk_data["page_number"],
                chunk_metadata={"word_count": chunk_data["word_count"]},
                embedding=emb
            )
            db.add(chunk_rec)

        doc.total_chunks = len(all_chunks)
        doc.status = DocumentStatus.INDEXED
        doc.indexed_at = datetime.utcnow()
        db.commit()
        db.refresh(doc)

        # Invalidate cached retrieval results because document store changed
        cache_service.invalidate_prefix("retrieval:")

    except Exception as e:
        doc.status = DocumentStatus.FAILED
        doc.error_message = str(e)
        db.commit()
        db.refresh(doc)

    return doc

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete physical file
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    # Cascade deletes chunks from DB
    db.delete(doc)
    db.commit()

    # Invalidate retrieval cache
    cache_service.invalidate_prefix("retrieval:")

    return {"message": f"Document '{doc.title}' and all associated chunks deleted successfully."}
