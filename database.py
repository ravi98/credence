import os
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()

# Authoritative Database URL
# In production/Docker: postgresql+psycopg2://postgres:postgres@localhost:5432/credence
# Fallback for local development/testing: sqlite:///./credence_crm.db
DEFAULT_SQLITE_URL = "sqlite:///./credence_crm.db"
DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_SQLITE_URL)

is_sqlite = DATABASE_URL.startswith("sqlite")

# Dialect-safe JSON: Uses PostgreSQL native JSONB for performance, falls back to JSON on SQLite
JSON_VARIANT = JSON().with_variant(JSONB(), "postgresql")

# Configure engine with robust pooling
engine_kwargs = {}
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db() -> Generator:
    """
    FastAPI dependency yielding a thread-safe database session per request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

