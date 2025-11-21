"""Application settings using Pydantic."""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Database
    database_url: str = Field(..., description="PostgreSQL database URL")

    # OpenAI
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o", description="OpenAI model to use")

    # Email (SMTP)
    smtp_host: str = Field(..., description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: str = Field(..., description="SMTP username")
    smtp_password: str = Field(..., description="SMTP password")
    smtp_from_email: str = Field(..., description="From email address")
    smtp_to_email: str = Field(..., description="Recipient email address for digests")
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP")

    # YouTube API
    youtube_api_key: str = Field(..., description="YouTube Data API key")

    # Agent configuration
    agent_system_prompt: str = Field(
        default=(
            "You are an AI assistant analyzing news and blog posts from the tech industry. "
            "Focus on AI/ML developments, new product launches, research breakthroughs, "
            "and industry trends. Provide clear, concise summaries with actionable insights."
        ),
        description="System prompt for the AI agent"
    )

    # Sources configuration file
    sources_config_path: str = Field(
        default="config/sources.yaml",
        description="Path to sources configuration YAML file"
    )

    # Scraping settings
    max_articles_per_source: int = Field(
        default=10,
        description="Maximum number of articles to fetch per source"
    )
    scraping_timeout: int = Field(
        default=30,
        description="Timeout in seconds for scraping requests"
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "postgresql+psycopg2://")):
            raise ValueError("database_url must be a PostgreSQL URL")
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
