from io import BytesIO
import os
import tempfile

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

TEST_DIRECTORY = tempfile.TemporaryDirectory()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DIRECTORY.name}/test.db"
os.environ["UPLOAD_DIR"] = f"{TEST_DIRECTORY.name}/uploads"

from app import models, uploads  # noqa: E402
from app.database import engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_database():
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    uploads.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    for path in uploads.UPLOAD_DIR.iterdir():
        if path.is_file():
            path.unlink()
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def image_bytes():
    buffer = BytesIO()
    Image.new("RGB", (32, 32), color="white").save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def fake_embedding(monkeypatch):
    embedding = np.ones(2048, dtype=np.float32)
    monkeypatch.setattr("app.main.extract_embedding", lambda _path: embedding)
    monkeypatch.setattr("app.routers.samples.extract_embedding", lambda _path: embedding)
    return embedding
