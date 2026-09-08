"""Safe local image-upload storage shared by API and admin routes."""

from pathlib import Path
import os
import tempfile
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads")).resolve()
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
MAX_IMAGE_PIXELS = int(os.getenv("MAX_IMAGE_PIXELS", "40000000"))
ALLOWED_FORMATS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}
CHUNK_SIZE = 1024 * 1024


class InvalidUploadError(ValueError):
    """Raised when an uploaded file is unsafe or is not a supported image."""


def save_image_upload(file: UploadFile) -> Path:
    """Stream, size-limit, validate, and persist an uploaded image safely."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            dir=UPLOAD_DIR, prefix=".upload-", suffix=".tmp", delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
            total = 0
            while chunk := file.file.read(CHUNK_SIZE):
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise InvalidUploadError(
                        f"Image exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit"
                    )
                temporary.write(chunk)

        if total == 0:
            raise InvalidUploadError("Uploaded image is empty")

        try:
            with Image.open(temporary_path) as image:
                image_format = image.format
                if image.width * image.height > MAX_IMAGE_PIXELS:
                    raise InvalidUploadError("Image dimensions are too large")
                image.verify()
        except (UnidentifiedImageError, OSError) as exc:
            raise InvalidUploadError("Upload must be a valid image") from exc

        if image_format not in ALLOWED_FORMATS:
            raise InvalidUploadError("Only JPEG, PNG, and WebP images are supported")

        destination = UPLOAD_DIR / f"{uuid4().hex}{ALLOWED_FORMATS[image_format]}"
        temporary_path.replace(destination)
        temporary_path = None
        return destination
    finally:
        file.file.close()
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def delete_stored_file(image_path: str) -> bool:
    """Delete only files contained by the configured upload directory."""
    candidate = Path(image_path).resolve()
    if not candidate.is_relative_to(UPLOAD_DIR):
        return False
    if not candidate.exists():
        return False
    candidate.unlink()
    return True
