from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    nyt_api_key: str | None = None
    google_books_api_key: str | None = None
    popularity_cache_ttl_hours: int = 24
    catalog_cache_ttl_hours: int = 24
    store_request_timeout_seconds: float = 8.0
    cache_dir: Path = Path("cache")


settings = Settings()
