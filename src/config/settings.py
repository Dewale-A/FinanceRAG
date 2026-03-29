"""Configuration settings for FinanceRAG."""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    embedding_model: str = Field(default="text-embedding-ada-002", env="EMBEDDING_MODEL")
    llm_model: str = Field(default="gpt-4o-mini", env="LLM_MODEL")
    llm_temperature: float = Field(default=0.1, env="LLM_TEMPERATURE")
    
    # ChromaDB
    chroma_persist_dir: str = Field(default="./data/chroma", env="CHROMA_PERSIST_DIR")
    collection_name: str = Field(default="finance_docs", env="COLLECTION_NAME")
    
    # Chunking
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    
    # Retrieval
    top_k_results: int = Field(default=5, env="TOP_K_RESULTS")
    
    # API
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    
    # Auth
    api_key: str = Field(default="", env="API_KEY")
    
    # Database
    database_url: str = Field(
        default="sqlite:///data/financerag.db",
        env="DATABASE_URL"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "forbid"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
