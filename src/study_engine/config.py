"""Centralized Configuration Settings using Pydantic Settings (P2)."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized configuration for KASIU engine, providers, and storage."""

    # API Keys
    gemini_api_key: Optional[str] = Field(default=None, validation_alias="GEMINI_API_KEY")
    groq_api_key: Optional[str] = Field(default=None, validation_alias="GROQ_API_KEY")
    nvidia_api_key: Optional[str] = Field(default=None, validation_alias="NVIDIA_API_KEY")
    openrouter_api_key: Optional[str] = Field(default=None, validation_alias="OPENROUTER_API_KEY")
    xkiro_api_key: Optional[str] = Field(default=None, validation_alias="XKIRO_API_KEY")
    xkiro_model: str = Field(default="qwen/qwen3.8-max:free", validation_alias="XKIRO_MODEL")
    xkiro_base_url: str = Field(default="https://api.xkiro.com/v1", validation_alias="XKIRO_BASE_URL")
    jina_api_key: Optional[str] = Field(default=None, validation_alias="JINA_API_KEY")
    jina_rerank_model: str = Field(default="jina-reranker-v2-base-multilingual", validation_alias="JINA_RERANK_MODEL")

    # Provider defaults
    default_provider: str = Field(default="groq", validation_alias="STUDY_ENGINE_LLM_PROVIDER")
    default_model: Optional[str] = Field(default=None, validation_alias="STUDY_ENGINE_LLM_MODEL")
    default_timeout: float = Field(default=10.0, validation_alias="STUDY_ENGINE_GEMINI_TIMEOUT")

    # Database
    database_url: str = Field(default="sqlite:///./data/storage/knowledge.db", validation_alias="DATABASE_URL")

    # Flags
    live_tests_enabled: bool = Field(default=False, validation_alias="KASIU_LIVE_TESTS")

    # Single-user identity (proyecto personal — un único estudiante canónico)
    student_id: str = Field(default="agustin", validation_alias="KASIU_STUDENT_ID")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Singleton instance
settings = Settings()

# Alias de conveniencia: ID canónico del único estudiante del sistema
CANONICAL_STUDENT_ID: str = settings.student_id
