from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Multi-Currency Wallet Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    database_url: str = Field(
        default="postgresql+asyncpg://wallet:wallet@localhost:5432/wallet_db"
    )
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "change-me-in-production-use-long-random-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15

    bcrypt_rounds: int = 12

    exchange_provider: str = "frankfurter"
    exchange_base_url: str = "https://api.frankfurter.dev/v1"
   
    exchange_refresh_interval_minutes: int = 60
    exchange_max_stale_hours: int = 24

    supported_currencies: list[str] = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF"]
    default_currency: str = "USD"

    login_rate_limit_attempts: int = 5
    login_rate_limit_window_seconds: int = 900

    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    log_level: str = "INFO"
    log_json: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
