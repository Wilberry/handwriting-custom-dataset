from io import BytesIO

import pytest
from fastapi import UploadFile

from app import uploads


def test_upload_limit_removes_temporary_file(monkeypatch, tmp_path):
    monkeypatch.setattr(uploads, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(uploads, "MAX_UPLOAD_BYTES", 4)
    upload = UploadFile(filename="large.png", file=BytesIO(b"12345"))

    with pytest.raises(uploads.InvalidUploadError, match="exceeds"):
        uploads.save_image_upload(upload)

    assert list(tmp_path.iterdir()) == []


def test_delete_stored_file_never_deletes_outside_upload_directory(monkeypatch, tmp_path):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    inside = upload_dir / "sample.png"
    outside = tmp_path / "outside.png"
    inside.write_bytes(b"inside")
    outside.write_bytes(b"outside")
    monkeypatch.setattr(uploads, "UPLOAD_DIR", upload_dir)

    assert uploads.delete_stored_file(str(outside)) is False
    assert outside.exists()
    assert uploads.delete_stored_file(str(inside)) is True
    assert not inside.exists()
    assert uploads.delete_stored_file(str(inside)) is False
