from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Finance RAG Assistant"
    app_env: str = "local"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = "postgresql+psycopg://finance_rag:change-me-for-local-use@localhost:5432/finance_rag"
    jwt_secret_key: str = ""
    access_token_expire_minutes: int = Field(default=30, ge=5, le=1440)
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_url: str = "http://localhost:8001"
    chroma_collection: str = "finance_documents"

    embedding_provider: str = "fastembed"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    openai_api_key: str | None = None
    groq_api_key: str | None = None
    llm_provider: str = "openai"
    llm_model: str = ""
    anthropic_api_key: str | None = None
    chunk_size: int = Field(default=1000, ge=256, le=10000)
    chunk_overlap: int = Field(default=150, ge=0, le=9999)
    max_upload_size_mb: int = Field(default=25, ge=1, le=100)
    upload_dir: Path = Path("/data/uploads")
    retrieval_top_k: int = Field(default=5, ge=1, le=50)
    retrieval_max_top_k: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def validate_ingestion_settings(self) -> "Settings":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        if self.retrieval_top_k > self.retrieval_max_top_k:
            raise ValueError("RETRIEVAL_TOP_K cannot exceed RETRIEVAL_MAX_TOP_K")
        if len(self.jwt_secret_key) < 32:
            raise ValueError("JWT_SECRET_KEY must contain at least 32 characters")
        if bool(self.bootstrap_admin_email) != bool(self.bootstrap_admin_password):
            raise ValueError("Set both BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD, or neither")
        if self.bootstrap_admin_password and len(self.bootstrap_admin_password) < 12:
            raise ValueError("BOOTSTRAP_ADMIN_PASSWORD must contain at least 12 characters")
        return self

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
