from app.config import get_settings
from app import storage


class FakeS3Client:
    def __init__(self):
        self.uploads = []
        self.deletes = []

    def upload_file(self, filename, bucket, key, ExtraArgs):
        self.uploads.append((filename, bucket, key, ExtraArgs))

    def delete_object(self, **kwargs):
        self.deletes.append(kwargs)


def test_s3_storage_uploads_encrypted_and_restricts_deletion(monkeypatch, tmp_path):
    monkeypatch.setenv("STORAGE_BACKEND", "s3")
    monkeypatch.setenv("S3_BUCKET", "private-samples")
    monkeypatch.setenv("S3_PREFIX", "writers")
    get_settings.cache_clear()
    fake_client = FakeS3Client()
    monkeypatch.setattr(storage, "_s3_client", lambda: fake_client)

    try:
        image = tmp_path / "sample.png"
        image.write_bytes(b"image")
        locator = storage.persist_reference_image(image)
        assert locator == "s3://private-samples/writers/sample.png"
        assert not image.exists()
        assert fake_client.uploads[0][3] == {"ServerSideEncryption": "AES256"}

        assert storage.delete_reference_image(locator) is True
        assert fake_client.deletes == [{"Bucket": "private-samples", "Key": "writers/sample.png"}]
        assert storage.delete_reference_image("s3://another-bucket/writers/a.png") is False
        assert storage.delete_reference_image("s3://private-samples/outside/a.png") is False
    finally:
        get_settings.cache_clear()


def test_unknown_storage_backend_is_rejected(monkeypatch, tmp_path):
    monkeypatch.setenv("STORAGE_BACKEND", "unknown")
    get_settings.cache_clear()
    try:
        image = tmp_path / "sample.png"
        image.write_bytes(b"image")
        try:
            storage.persist_reference_image(image)
        except storage.StorageConfigurationError as exc:
            assert "Unsupported" in str(exc)
        else:
            raise AssertionError("Unknown backend was accepted")
    finally:
        get_settings.cache_clear()
