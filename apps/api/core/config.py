from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    log_level: str = "INFO"

    database_url: str = (
        "postgresql+asyncpg://learningspace:changeme@localhost:5432/learningspace"
    )
    database_echo: bool = False
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
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
    # LLM provider: "anthropic" | "groq" | "siliconflow" | "fireworks"
    llm_provider: str = "anthropic"

    # Provider API keys (only the one matching llm_provider needs to be set)
    anthropic_api_key: str = ""  # Optional for development
    groq_api_key: str = ""
    siliconflow_api_key: str = ""
    fireworks_api_key: str = ""

    # Model overrides per provider (sensible defaults below)
    anthropic_model: str = "claude-haiku-4-5-20251001"  # Default model
    groq_model: str = "llama-3.1-8b-instant"
    siliconflow_model: str = "Qwen/Qwen2.5-7B-Instruct"
    fireworks_model: str = "accounts/fireworks/models/llama-v3p1-8b-instruct"

    # Base URL overrides per provider
    siliconflow_base_url: str = "https://api.siliconflow.com/v1"
    fireworks_base_url: str = "https://api.fireworks.ai/inference/v1"

    # Embedding Settings
    # Provider for embeddings (any OpenAI-compatible provider).
    # Set EMBEDDING_API_KEY / EMBEDDING_BASE_URL to override; falls back to siliconflow.
    embedding_model: str = "Qwen/Qwen3-Embedding-4B"
    embedding_dimensions: int = 2560
    embedding_api_key: str = ""      # Falls back to siliconflow_api_key if empty
    embedding_base_url: str = "https://api.siliconflow.com/v1"

    # Search Settings
    search_mode: str = "keyword"  # "keyword" (default) | "hybrid"

    # URL fetcher: "httpx" (default) or "playwright" (opt-in, bypasses bot blocks)
    url_fetcher_backend: str = "httpx"

    # Tiered fetcher: domains that require API access (domain:provider pairs).
    # These return NOT_SUPPORTED until an API integration is implemented.
    # Default is empty — all domains are attempted with best effort.
    api_required_domains: str = ""

    # Comma-separated list of allowed emails. Empty = allow all (open access).
    allowed_emails: str = ""

    # Comma-separated list of allowed CORS origins. Always includes localhost:3000.
    cors_origins: str = ""

    # Observability
    otlp_traces_endpoint: str = ""  # e.g. http://localhost:6006/v1/traces
    prometheus_metrics: bool = False  # expose /metrics for Prometheus scraping
    otel_service_name: str = "learning-space-api"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def cors_origins_list(self) -> list[str]:
        origins = ["http://localhost:3000"]
        if self.cors_origins:
            origins += [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        return origins

    @property
    def allowed_emails_set(self) -> set[str]:
        if not self.allowed_emails:
            return set()
        return {e.strip().lower() for e in self.allowed_emails.split(",") if e.strip()}

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        """Ensure asyncpg driver is used for PostgreSQL (Railway provides postgresql://)."""
        if isinstance(v, str) and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

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
