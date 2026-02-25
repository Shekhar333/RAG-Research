from pydantic_settings import BaseSettings
from functools import lru_cache
# Updated for local RAG with lower similarity threshold (0.1 works for sentence-transformers)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Local Embedding Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384  # 384 for all-MiniLM-L6-v2
    
    # Local LLM Configuration (Ollama)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    llm_temperature: float = 0.0
    
    # Qdrant Configuration
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "research_papers"
    
    # Application Configuration
    max_pdf_size_mb: int = 20
    max_query_latency_seconds: int = 60  # Increased for local LLM (Ollama)
    chunk_size: int = 500
    chunk_overlap: int = 100
    top_k_retrieval: int = 5
    similarity_threshold: float = 0.75
    
    # Cache Configuration
    cache_dir: str = "./cache"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
