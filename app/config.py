"""Environment-backed application configuration."""

from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass(frozen=True)
class Settings:
    environment: str
    api_key: str | None
    admin_username: str | None
    admin_password: str | None
    storage_backend: str
    s3_bucket: str | None
    s3_prefix: str

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def security_is_configured(self) -> bool:
        return bool(self.api_key and self.admin_username and self.admin_password)

    @property
    def storage_is_configured(self) -> bool:
        if self.storage_backend == "local":
            return True
        if self.storage_backend == "s3":
            return bool(self.s3_bucket)
        return False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Read settings once per process; clear the cache when changing test env vars."""
    return Settings(
        environment=os.getenv("APP_ENV", "development"),
        api_key=os.getenv("API_KEY"),
        admin_username=os.getenv("ADMIN_USERNAME"),
        admin_password=os.getenv("ADMIN_PASSWORD"),
        storage_backend=os.getenv("STORAGE_BACKEND", "local").lower(),
        s3_bucket=os.getenv("S3_BUCKET"),
        s3_prefix=os.getenv("S3_PREFIX", "handwriting-samples").strip("/"),
    )
