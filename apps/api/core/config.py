from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://changeme:changeme@localhost:5432/learningspace"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "changeme"
    redis_url: str = "redis://localhost:6379"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
