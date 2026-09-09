import os
from time import time

import pytest

from app.database import SessionLocal
from app.maintenance import cleanup_local_orphans, purge_old_audit_events


def test_cleanup_only_removes_old_orphaned_files(monkeypatch, tmp_path):
    monkeypatch.setattr("app.maintenance.UPLOAD_DIR", tmp_path)
    old_file = tmp_path / "old.png"
    new_file = tmp_path / "new.png"
    hidden_file = tmp_path / ".upload-part"
    for path in (old_file, new_file, hidden_file):
        path.write_bytes(b"content")
    old_time = time() - (48 * 3600)
    os.utime(old_file, (old_time, old_time))
    os.utime(hidden_file, (old_time, old_time))

    with SessionLocal() as db:
        assert cleanup_local_orphans(db, grace_hours=24) == 1
    assert not old_file.exists()
    assert new_file.exists()
    assert hidden_file.exists()


def test_retention_arguments_are_validated():
    with SessionLocal() as db:
        with pytest.raises(ValueError, match="at least 1"):
            purge_old_audit_events(db, 0)
