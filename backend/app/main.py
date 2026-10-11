from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.core.database import get_db, engine, Base
from app.api import auth, business, documents, retrieval, resolution, evaluation
from app.services.cache_service import cache_service

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(business.router, prefix=settings.API_V1_PREFIX)
app.include_router(documents.router, prefix=settings.API_V1_PREFIX)
app.include_router(retrieval.router, prefix=settings.API_V1_PREFIX)
app.include_router(resolution.router, prefix=settings.API_V1_PREFIX)
app.include_router(evaluation.router, prefix=settings.API_V1_PREFIX)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "MadadAI Resolution Platform",
        "database": "connected",
        "redis_cached": cache_service.is_available,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "llm_provider": settings.LLM_PROVIDER
    }

@app.get(f"{settings.API_V1_PREFIX}/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    from app.models.entities import SupportTicket, Document, ResolutionRecommendation, TicketStatus
    total_tickets = db.query(SupportTicket).count()
    open_tickets = db.query(SupportTicket).filter(SupportTicket.status == TicketStatus.OPEN).count()
    awaiting_reviews = db.query(ResolutionRecommendation).filter(ResolutionRecommendation.review_required == True).count()
    indexed_documents = db.query(Document).filter(Document.status == "indexed").count()

    return {
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "awaiting_reviews": awaiting_reviews,
        "indexed_documents": indexed_documents
    }

@app.get(f"{settings.API_V1_PREFIX}/settings/status")
def get_settings_status():
    return {
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "embedding_model": settings.EMBEDDING_MODEL,
        "vector_dimension": settings.VECTOR_DIMENSION,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "reranker_provider": settings.RERANKER_PROVIDER,
        "redis_connected": cache_service.is_available,
        "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB,
        "api_v1_prefix": settings.API_V1_PREFIX
    }
