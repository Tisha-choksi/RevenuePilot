from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "RevenuePilot API"
    environment: str = "development"

    database_url: str = "postgresql+asyncpg://revenuepilot:revenuepilot@localhost:5432/revenuepilot"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"


settings = Settings()
