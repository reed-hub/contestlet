import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

def get_database_url():
    """Get appropriate database URL based on environment"""
    # Check if running on Vercel
    if os.getenv("VERCEL_ENV"):
        # If external database URL is provided, use it
        if settings.DATABASE_URL and not settings.DATABASE_URL.startswith("sqlite:///"):
            return settings.DATABASE_URL
        # Otherwise use in-memory SQLite for Vercel (fallback)
        return "sqlite:///:memory:"
    
    # Use configured database URL for local/other environments
    return settings.DATABASE_URL

# Create database engine
database_url = get_database_url()
engine = create_engine(
    database_url,
    # SQLite specific - remove these for PostgreSQL
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
