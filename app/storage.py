"""Persistent reference-image storage with local and S3 backends."""

from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from app.config import get_settings
from app.uploads import delete_stored_file


class StorageConfigurationError(RuntimeError):
    """Raised when the selected storage backend is incomplete or unsupported."""


@lru_cache(maxsize=1)
def _s3_client():
    import boto3

    return boto3.client("s3")


def persist_reference_image(local_path: Path) -> str:
    """Persist a validated local image and return its durable locator."""
    settings = get_settings()
    if settings.storage_backend == "local":
        return str(local_path.resolve())
    if settings.storage_backend != "s3":
        raise StorageConfigurationError(f"Unsupported STORAGE_BACKEND: {settings.storage_backend}")
    if not settings.s3_bucket:
        raise StorageConfigurationError("S3_BUCKET is required for S3 storage")

    key = f"{settings.s3_prefix}/{local_path.name}" if settings.s3_prefix else local_path.name
    _s3_client().upload_file(
        str(local_path),
        settings.s3_bucket,
        key,
        ExtraArgs={"ServerSideEncryption": "AES256"},
    )
    local_path.unlink(missing_ok=True)
    return f"s3://{settings.s3_bucket}/{key}"


def delete_reference_image(locator: str) -> bool:
    """Delete a local or S3 reference image without accepting arbitrary paths."""
    if not locator.startswith("s3://"):
        return delete_stored_file(locator)

    parsed = urlparse(locator)
    settings = get_settings()
    if settings.storage_backend != "s3" or parsed.netloc != settings.s3_bucket:
        return False
    key = parsed.path.lstrip("/")
    allowed_prefix = f"{settings.s3_prefix}/" if settings.s3_prefix else ""
    if not key or (allowed_prefix and not key.startswith(allowed_prefix)):
        return False
    _s3_client().delete_object(Bucket=parsed.netloc, Key=key)
    return True
