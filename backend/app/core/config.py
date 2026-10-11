from pydantic_settings import BaseSettings
from typing import Optional, List
from pydantic import Field
import os

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "MadadAI Resolution Platform"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = Field(default="madadai-super-secret-jwt-key-2026-production-ready-change-me", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    ALGORITHM: str = "HS256"
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/madadai",
        env="DATABASE_URL"
    )

    # Redis
    REDIS_URL: Optional[str] = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_ENABLED: bool = True
    CACHE_DEFAULT_TTL: int = 300  # 5 minutes

    # Vector & Retrieval
    VECTOR_DIMENSION: int = 384  # Default for all-MiniLM-L6-v2 / local embeddings
    SIMILARITY_THRESHOLD: float = 0.5
    DEFAULT_TOP_K: int = 5
    RRF_K: int = 60  # Standard Reciprocal Rank Fusion constant

    # Embeddings Provider: "local", "openai", or "ollama"
    EMBEDDING_PROVIDER: str = Field(default="local", env="EMBEDDING_PROVIDER")
    EMBEDDING_MODEL: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    EMBEDDING_API_KEY: Optional[str] = Field(default=None, env="EMBEDDING_API_KEY")

    # LLM Provider: "mock", "openai", "gemini", or "ollama"
    LLM_PROVIDER: str = Field(default="mock", env="LLM_PROVIDER")
    LLM_MODEL: str = Field(default="mock-model", env="LLM_MODEL")
    LLM_API_KEY: Optional[str] = Field(default=None, env="LLM_API_KEY")
    LLM_TEMPERATURE: float = 0.1

    # Reranker Provider: "none", "local_cross_encoder", "cohere"
    RERANKER_PROVIDER: str = Field(default="none", env="RERANKER_PROVIDER")
    RERANKER_API_KEY: Optional[str] = Field(default=None, env="RERANKER_API_KEY")

    # Uploads
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    MAX_UPLOAD_SIZE_MB: int = 15

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"

settings = Settings()
