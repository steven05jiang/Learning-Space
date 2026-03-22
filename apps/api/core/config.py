from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+asyncpg://learningspace:changeme@localhost:5432/learningspace"
    )
    database_echo: bool = False
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "changeme"
    redis_url: str = "redis://localhost:6379"

    # OAuth Settings
    github_client_id: str = ""
    github_client_secret: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    twitter_client_id: str = ""
    twitter_client_secret: str = ""
    oauth_redirect_base_url: str = ""  # Optional: override for OAuth redirects

    # JWT Settings
    jwt_secret_key: str  # No default - must be provided via environment
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30

    # LLM/AI Settings
    anthropic_api_key: str = ""  # Optional for development
    anthropic_model: str = "claude-haiku-4-5-20251001"  # Default model

    # URL fetcher: "httpx" (default) or "playwright" (opt-in, bypasses bot blocks)
    url_fetcher_backend: str = "httpx"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v):
        if not v or v == "your-secret-key-change-in-production":
            raise ValueError(
                "JWT_SECRET_KEY must be set to a secure value. "
                "Do not use the default value in production."
            )
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        return v


settings = Settings()
