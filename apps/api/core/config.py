from functools import lru_cache
from typing import Literal

from pydantic import AnyUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False
    secret_key: str = "change-me-in-production"

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://learningspace:learningspace@localhost:5432/learningspace"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "learningspace"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # OAuth — Twitter/X
    twitter_client_id: str = ""
    twitter_client_secret: str = ""

    # OAuth — Google
    google_client_id: str = ""
    google_client_secret: str = ""

    # OAuth — GitHub
    github_client_id: str = ""
    github_client_secret: str = ""

    # OAuth callback
    oauth_callback_base_url: str = "http://localhost:8000"

    # LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Frontend URL (for CORS)
    frontend_url: str = "http://localhost:3000"

    @field_validator("secret_key")
    @classmethod
    def secret_key_not_default_in_production(cls, v: str, info) -> str:
        # info.data may not have 'environment' yet during validation order
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()