"""Database module for FinanceRAG - PostgreSQL integration."""

from datetime import datetime
from typing import Optional, Generator

from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, JSON
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import structlog

from src.config.settings import get_settings

logger = structlog.get_logger()

Base = declarative_base()


class QueryLog(Base):
    """Log every RAG query for analytics and auditing."""
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    model = Column(String(100))
    documents_retrieved = Column(Integer, default=0)
    sources = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    response_time_ms = Column(Float)


class DocumentMetadata(Base):
    """Track ingested documents."""
    __tablename__ = "document_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(500), nullable=False)
    file_type = Column(String(50))
    file_size_bytes = Column(Integer)
    chunk_count = Column(Integer, default=0)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="active")


# Database engine and session factory
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            echo=False
        )
        logger.info("database_engine_created", url=settings.database_url.split("@")[-1])
    return _engine


def get_session_factory():
    """Get or create session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Get database session (FastAPI dependency)."""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("database_tables_created")


def log_query(
    question: str,
    answer: Optional[str] = None,
    model: Optional[str] = None,
    documents_retrieved: int = 0,
    sources: Optional[list] = None,
    response_time_ms: Optional[float] = None
):
    """Log a RAG query to the database."""
    try:
        SessionLocal = get_session_factory()
        db = SessionLocal()
        log_entry = QueryLog(
            question=question,
            answer=answer,
            model=model,
            documents_retrieved=documents_retrieved,
            sources=sources,
            response_time_ms=response_time_ms
        )
        db.add(log_entry)
        db.commit()
        db.close()
        logger.info("query_logged", question_preview=question[:50])
    except Exception as e:
        logger.error("query_log_error", error=str(e))


def log_document(
    filename: str,
    file_type: str,
    file_size_bytes: int = 0,
    chunk_count: int = 0
):
    """Log an ingested document to the database."""
    try:
        SessionLocal = get_session_factory()
        db = SessionLocal()
        doc_entry = DocumentMetadata(
            filename=filename,
            file_type=file_type,
            file_size_bytes=file_size_bytes,
            chunk_count=chunk_count
        )
        db.add(doc_entry)
        db.commit()
        db.close()
        logger.info("document_logged", filename=filename)
    except Exception as e:
        logger.error("document_log_error", error=str(e))
