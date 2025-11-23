"""Application configuration management."""
from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys - Support both naming conventions
    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    
    # Additional fields from user's .env (optional)
    LLM_PROVIDER: Optional[str] = "gemini"
    GEMINI_EMBEDDING_MODEL: Optional[str] = "text-embedding-004"
    TAVILY_API_KEY: Optional[str] = None
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30
    VECTOR_DIMENSION: int = 768
    
    # Qdrant
    QDRANT_URL: str
    QDRANT_API_KEY: str
    QDRANT_COLLECTION: str = "retail_insights"
    
    # LangSmith - Tracing and monitoring
    LANGCHAIN_TRACING_V2: str = "true"  # Must be string "true" for LangSmith
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "retail-insights-assistant"
    
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 104857600  # 100MB
    UPLOAD_DIR: Path = Path("./data/uploads")
    PROCESSED_DIR: Path = Path("./data/processed")
    
    # Cache
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 3600  # 1 hour
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # DuckDB
    DUCKDB_PATH: Path = Path("./data/retail_insights.duckdb")
    
    # Chunking
    CHUNK_SIZE: int = 10000  # rows per chunk for large files
    SAMPLE_SIZE: int = 10000  # rows to sample for profiling
    
    @property
    def api_key(self) -> str:
        """Get API key - supports both GOOGLE_API_KEY and GEMINI_API_KEY."""
        return self.GOOGLE_API_KEY or self.GEMINI_API_KEY or ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from .env


# Global settings instance
settings = Settings()

# Create necessary directories
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
settings.DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)

