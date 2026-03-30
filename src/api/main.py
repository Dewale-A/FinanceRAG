"""FastAPI application for FinanceRAG."""

import os
from typing import List, Optional, Dict, Any
from pathlib import Path
import structlog

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

# Initialize Sentry before app creation
sentry_dsn = os.getenv("SENTRY_DSN", "")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
        environment=os.getenv("ENVIRONMENT", "production"),
    )

from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config.settings import get_settings
from src.tools.document_processor import DocumentProcessor
from src.tools.vector_store import get_vector_store_manager
from src.tools.rag_chain import get_rag_chain
from src.database import init_db, log_query, log_document
from src.auth import verify_api_key

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="FinanceRAG API",
    description="Production-grade RAG system for financial document Q&A",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class QueryRequest(BaseModel):
    """Request model for RAG queries."""
    question: str = Field(..., description="The question to answer", min_length=3)
    k: Optional[int] = Field(default=5, description="Number of documents to retrieve", ge=1, le=20)


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request model for chat with history."""
    question: str = Field(..., description="The current question")
    history: List[ChatMessage] = Field(default=[], description="Conversation history")
    k: Optional[int] = Field(default=5, description="Number of documents to retrieve")


class SourceDocument(BaseModel):
    """Source document information."""
    filename: str
    chunk_index: int
    relevance_score: float
    preview: str


class QueryResponse(BaseModel):
    """Response model for RAG queries."""
    answer: str
    sources: List[SourceDocument]
    query: str
    documents_retrieved: int
    model: Optional[str] = None
    error: Optional[str] = None


class IngestRequest(BaseModel):
    """Request model for document ingestion."""
    source_path: str = Field(..., description="Path to file or directory to ingest")


class IngestResponse(BaseModel):
    """Response model for document ingestion."""
    success: bool
    documents_processed: int
    chunks_created: int
    message: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    collection_stats: Dict[str, Any]
    settings: Dict[str, Any]


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    try:
        init_db()
        logger.info("database_initialized")
    except Exception as e:
        logger.warning("database_init_skipped", error=str(e))


# Endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API info."""
    return {
        "name": "FinanceRAG API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with system status."""
    try:
        settings = get_settings()
        vector_store = get_vector_store_manager()
        stats = vector_store.get_collection_stats()
        
        return HealthResponse(
            status="healthy",
            collection_stats=stats,
            settings={
                "llm_model": settings.llm_model,
                "embedding_model": settings.embedding_model,
                "chunk_size": settings.chunk_size,
                "top_k": settings.top_k_results
            }
        )
    except Exception as e:
        logger.error("health_check_error", error=str(e))
        return HealthResponse(
            status="unhealthy",
            collection_stats={"error": str(e)},
            settings={}
        )


@app.post("/query", response_model=QueryResponse, dependencies=[Depends(verify_api_key)])
async def query_documents(request: QueryRequest):
    """
    Query the RAG system with a question.
    
    Returns an answer based on the ingested financial documents,
    along with source references.
    """
    try:
        import time
        start_time = time.time()
        
        rag_chain = get_rag_chain()
        result = rag_chain.query(request.question, k=request.k)
        
        response_time_ms = (time.time() - start_time) * 1000
        
        # Log query to PostgreSQL
        log_query(
            question=request.question,
            answer=result.get("answer"),
            model=result.get("model"),
            documents_retrieved=result.get("documents_retrieved", 0),
            sources=result.get("sources"),
            response_time_ms=response_time_ms
        )
        
        return QueryResponse(
            answer=result["answer"],
            sources=[SourceDocument(**s) for s in result["sources"]],
            query=result["query"],
            documents_retrieved=result["documents_retrieved"],
            model=result.get("model"),
            error=result.get("error")
        )
    except Exception as e:
        logger.error("query_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=QueryResponse, dependencies=[Depends(verify_api_key)])
async def chat_with_history(request: ChatRequest):
    """
    Chat with conversation history for context-aware responses.
    """
    try:
        rag_chain = get_rag_chain()
        history = [{"role": m.role, "content": m.content} for m in request.history]
        result = rag_chain.query_with_history(request.question, history, k=request.k)
        
        return QueryResponse(
            answer=result["answer"],
            sources=[SourceDocument(**s) for s in result["sources"]],
            query=result["query"],
            documents_retrieved=result["documents_retrieved"],
            model=result.get("model"),
            error=result.get("error")
        )
    except Exception as e:
        logger.error("chat_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest", response_model=IngestResponse, dependencies=[Depends(verify_api_key)])
async def ingest_documents(request: IngestRequest):
    """
    Ingest documents from a file or directory path.
    
    Supports: .txt, .pdf, .docx, .md files
    """
    try:
        processor = DocumentProcessor()
        vector_store = get_vector_store_manager()
        
        # Process documents
        chunks = processor.process_documents(request.source_path)
        
        if not chunks:
            return IngestResponse(
                success=False,
                documents_processed=0,
                chunks_created=0,
                message="No documents found to process"
            )
        
        # Add to vector store
        ids = vector_store.add_documents(chunks)
        
        # Count unique source files
        source_files = set(chunk.metadata.get("filename", "") for chunk in chunks)
        
        return IngestResponse(
            success=True,
            documents_processed=len(source_files),
            chunks_created=len(ids),
            message=f"Successfully ingested {len(source_files)} documents into {len(ids)} chunks"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("ingest_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/upload", response_model=IngestResponse, dependencies=[Depends(verify_api_key)])
async def upload_and_ingest(file: UploadFile = File(...)):
    """
    Upload and ingest a single document file.
    """
    try:
        # Save uploaded file temporarily
        temp_path = Path(f"/tmp/{file.filename}")
        
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process the file
        processor = DocumentProcessor()
        vector_store = get_vector_store_manager()
        
        chunks = processor.process_documents(str(temp_path))
        ids = vector_store.add_documents(chunks)
        
        # Clean up
        temp_path.unlink()
        
        return IngestResponse(
            success=True,
            documents_processed=1,
            chunks_created=len(ids),
            message=f"Successfully ingested {file.filename} into {len(ids)} chunks"
        )
    except Exception as e:
        logger.error("upload_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=Dict[str, Any])
async def get_stats():
    """Get vector store statistics."""
    try:
        vector_store = get_vector_store_manager()
        return vector_store.get_collection_stats()
    except Exception as e:
        logger.error("stats_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/collection", dependencies=[Depends(verify_api_key)])
async def clear_collection():
    """Clear all documents from the collection."""
    try:
        vector_store = get_vector_store_manager()
        success = vector_store.clear_collection()
        
        if success:
            return {"message": "Collection cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear collection")
    except Exception as e:
        logger.error("clear_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics")
async def get_analytics():
    """Get query analytics from PostgreSQL."""
    try:
        from src.database import get_session_factory, QueryLog
        from sqlalchemy import func, desc
        SessionLocal = get_session_factory()
        db = SessionLocal()

        total_queries = db.query(func.count(QueryLog.id)).scalar() or 0
        avg_response_time = db.query(func.avg(QueryLog.response_time_ms)).scalar() or 0
        avg_docs_retrieved = db.query(func.avg(QueryLog.documents_retrieved)).scalar() or 0

        recent_queries = db.query(
            QueryLog.id,
            QueryLog.question,
            QueryLog.model,
            QueryLog.documents_retrieved,
            QueryLog.response_time_ms,
            QueryLog.timestamp
        ).order_by(desc(QueryLog.timestamp)).limit(20).all()

        recent = [
            {
                "id": q.id,
                "question": q.question,
                "model": q.model,
                "documents_retrieved": q.documents_retrieved,
                "response_time_ms": round(q.response_time_ms, 1) if q.response_time_ms else None,
                "timestamp": q.timestamp.isoformat() if q.timestamp else None,
            }
            for q in recent_queries
        ]

        db.close()

        return {
            "total_queries": total_queries,
            "avg_response_time_ms": round(avg_response_time, 1) if avg_response_time else 0,
            "avg_docs_retrieved": round(avg_docs_retrieved, 1) if avg_docs_retrieved else 0,
            "recent_queries": recent,
        }
    except Exception as e:
        logger.error("analytics_error", error=str(e))
        return {
            "total_queries": 0,
            "avg_response_time_ms": 0,
            "avg_docs_retrieved": 0,
            "recent_queries": [],
            "error": str(e),
        }


@app.get("/test-sentry")
async def test_sentry():
    """Trigger a test error for Sentry. Remove after verifying."""
    raise ValueError("Sentry test error - delete this endpoint after testing!")


# Run with: uvicorn src.api.main:app --reload
if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
