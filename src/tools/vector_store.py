"""Vector store management for FinanceRAG."""

from typing import List, Optional, Dict, Any
import structlog

from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from src.config.settings import get_settings

logger = structlog.get_logger()


class VectorStoreManager:
    """Manage ChromaDB vector store operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.embeddings = OpenAIEmbeddings(
            model=self.settings.embedding_model,
            openai_api_key=self.settings.openai_api_key
        )
        self._vector_store: Optional[Chroma] = None
    
    @property
    def vector_store(self) -> Chroma:
        """Get or initialize vector store."""
        if self._vector_store is None:
            self._vector_store = Chroma(
                collection_name=self.settings.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.settings.chroma_persist_dir
            )
        return self._vector_store
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to the vector store."""
        if not documents:
            logger.warning("no_documents_to_add")
            return []
        
        try:
            ids = self.vector_store.add_documents(documents)
            logger.info("documents_added", count=len(ids))
            return ids
        except Exception as e:
            logger.error("add_documents_error", error=str(e))
            raise
    
    def similarity_search(
        self, 
        query: str, 
        k: Optional[int] = None,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Search for similar documents."""
        k = k or self.settings.top_k_results
        
        try:
            results = self.vector_store.similarity_search(
                query=query,
                k=k,
                filter=filter
            )
            logger.info("similarity_search", query_preview=query[:50], results=len(results))
            return results
        except Exception as e:
            logger.error("search_error", error=str(e))
            raise
    
    def similarity_search_with_scores(
        self, 
        query: str, 
        k: Optional[int] = None
    ) -> List[tuple[Document, float]]:
        """Search with relevance scores."""
        k = k or self.settings.top_k_results
        
        try:
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=k
            )
            logger.info("similarity_search_scored", 
                       query_preview=query[:50], 
                       results=len(results))
            return results
        except Exception as e:
            logger.error("search_error", error=str(e))
            raise
    
    def get_retriever(self, k: Optional[int] = None):
        """Get a retriever interface for the vector store."""
        k = k or self.settings.top_k_results
        return self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        try:
            collection = self.vector_store._collection
            count = collection.count()
            
            return {
                "collection_name": self.settings.collection_name,
                "document_count": count,
                "embedding_model": self.settings.embedding_model,
                "persist_directory": self.settings.chroma_persist_dir
            }
        except Exception as e:
            logger.error("stats_error", error=str(e))
            return {"error": str(e)}
    
    def clear_collection(self) -> bool:
        """Clear all documents from the collection."""
        try:
            # Delete and recreate collection
            self.vector_store._client.delete_collection(self.settings.collection_name)
            self._vector_store = None  # Reset to force recreation
            logger.info("collection_cleared", collection=self.settings.collection_name)
            return True
        except Exception as e:
            logger.error("clear_error", error=str(e))
            return False


# Singleton instance
_vector_store_manager: Optional[VectorStoreManager] = None


def get_vector_store_manager() -> VectorStoreManager:
    """Get singleton vector store manager instance."""
    global _vector_store_manager
    if _vector_store_manager is None:
        _vector_store_manager = VectorStoreManager()
    return _vector_store_manager
