from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./events.db"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30

    use_redis: bool = False

    api_key: str = "dev-api-key-change-me"
    rate_limit: str = "100/minute"
    log_level: str = "INFO"
    notification_email: str = "ops@company.com"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
