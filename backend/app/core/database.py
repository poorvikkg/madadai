from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Determine if we should connect to PostgreSQL or fallback gracefully for local testing
db_url = settings.DATABASE_URL
connect_args = {}

if "sqlite" in db_url:
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        connect_args=connect_args
    )
    # Test connection
    with engine.connect() as conn:
        pass
except Exception as e:
    logger.warning(f"PostgreSQL connection to {db_url} failed ({e}). Falling back to local SQLite database for development.")
    sqlite_url = "sqlite:///./madadai.db"
    engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency that provides an active database session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
