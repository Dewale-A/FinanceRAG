"""RAG chain implementation for FinanceRAG."""

from typing import List, Dict, Any, Optional
import structlog

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from src.config.settings import get_settings
from src.tools.vector_store import get_vector_store_manager

logger = structlog.get_logger()

# System prompt for financial document Q&A
SYSTEM_PROMPT = """You are a knowledgeable financial services assistant specializing in regulatory compliance, risk management, and banking operations. Your role is to provide accurate, helpful answers based on the provided context documents.

Guidelines:
1. Base your answers strictly on the provided context
2. If the context doesn't contain enough information, say so clearly
3. Cite specific sections or documents when possible
4. Use precise financial and regulatory terminology
5. If asked about specific thresholds, ratios, or requirements, quote them exactly
6. Highlight any important compliance considerations or risks

Context from financial documents:
{context}

Question: {question}

Provide a comprehensive answer based on the context above. If the context doesn't contain sufficient information to answer the question, state that clearly and explain what information would be needed."""


class RAGChain:
    """Retrieval-Augmented Generation chain for financial documents."""
    
    def __init__(self):
        self.settings = get_settings()
        self.vector_store_manager = get_vector_store_manager()
        
        self.llm = ChatOpenAI(
            model=self.settings.llm_model,
            temperature=self.settings.llm_temperature,
            openai_api_key=self.settings.openai_api_key
        )
        
        self.prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)
    
    def _format_docs(self, docs: List[Document]) -> str:
        """Format retrieved documents for the prompt."""
        formatted = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("filename", "Unknown source")
            content = doc.page_content.strip()
            formatted.append(f"[Document {i}: {source}]\n{content}")
        
        return "\n\n---\n\n".join(formatted)
    
    def query(
        self, 
        question: str, 
        k: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute RAG query and return answer with sources.
        
        Args:
            question: The user's question
            k: Number of documents to retrieve (optional)
            
        Returns:
            Dict containing answer, sources, and metadata
        """
        k = k or self.settings.top_k_results
        
        try:
            # Retrieve relevant documents
            docs_with_scores = self.vector_store_manager.similarity_search_with_scores(
                query=question,
                k=k
            )
            
            if not docs_with_scores:
                return {
                    "answer": "No relevant documents found in the knowledge base. Please ensure documents have been ingested.",
                    "sources": [],
                    "query": question,
                    "documents_retrieved": 0
                }
            
            # Extract documents and scores
            docs = [doc for doc, score in docs_with_scores]
            scores = [score for doc, score in docs_with_scores]
            
            # Format context
            context = self._format_docs(docs)
            
            # Generate answer
            chain = self.prompt | self.llm | StrOutputParser()
            answer = chain.invoke({
                "context": context,
                "question": question
            })
            
            # Prepare sources
            sources = []
            for doc, score in docs_with_scores:
                sources.append({
                    "filename": doc.metadata.get("filename", "Unknown"),
                    "chunk_index": doc.metadata.get("chunk_index", 0),
                    "relevance_score": round(1 - score, 4),  # Convert distance to similarity
                    "preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })
            
            logger.info("rag_query_complete", 
                       question_preview=question[:50],
                       docs_retrieved=len(docs),
                       avg_score=round(sum(scores)/len(scores), 4))
            
            return {
                "answer": answer,
                "sources": sources,
                "query": question,
                "documents_retrieved": len(docs),
                "model": self.settings.llm_model
            }
            
        except Exception as e:
            logger.error("rag_query_error", error=str(e))
            return {
                "answer": f"An error occurred while processing your query: {str(e)}",
                "sources": [],
                "query": question,
                "error": str(e)
            }
    
    def query_with_history(
        self,
        question: str,
        chat_history: List[Dict[str, str]],
        k: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute RAG query with conversation history for context.
        
        Args:
            question: The user's current question
            chat_history: List of {"role": "user/assistant", "content": "..."}
            k: Number of documents to retrieve
            
        Returns:
            Dict containing answer, sources, and metadata
        """
        # For now, use simple query (can be enhanced with history-aware retrieval)
        # Prepend relevant history context to the question if needed
        
        history_context = ""
        if chat_history:
            recent_history = chat_history[-4:]  # Last 2 exchanges
            history_parts = []
            for msg in recent_history:
                role = "User" if msg["role"] == "user" else "Assistant"
                history_parts.append(f"{role}: {msg['content']}")
            history_context = "Recent conversation:\n" + "\n".join(history_parts) + "\n\nCurrent question: "
        
        enhanced_question = history_context + question if history_context else question
        
        return self.query(enhanced_question, k=k)


# Singleton instance
_rag_chain: Optional[RAGChain] = None


def get_rag_chain() -> RAGChain:
    """Get singleton RAG chain instance."""
    global _rag_chain
    if _rag_chain is None:
        _rag_chain = RAGChain()
    return _rag_chain


def query(question: str, k: Optional[int] = None) -> Dict[str, Any]:
    """Convenience function to query the RAG chain."""
    chain = get_rag_chain()
    return chain.query(question, k=k)
