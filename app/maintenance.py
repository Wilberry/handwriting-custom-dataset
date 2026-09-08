"""Retention maintenance for audit events and orphaned local uploads."""

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app import models
from app.config import get_settings
from app.database import SessionLocal
from app.uploads import UPLOAD_DIR


def purge_old_audit_events(db: Session, retention_days: int) -> int:
    if retention_days < 1:
        raise ValueError("retention_days must be at least 1")
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    deleted = (
        db.query(models.AuditEvent)
        .filter(models.AuditEvent.created_at < cutoff)
        .delete(synchronize_session=False)
    )
    db.commit()
    return deleted


def cleanup_local_orphans(db: Session, grace_hours: int = 24) -> int:
    """Delete old local upload files that have no sample database record."""
    if grace_hours < 1:
        raise ValueError("grace_hours must be at least 1")
    if get_settings().storage_backend != "local" or not UPLOAD_DIR.exists():
        return 0

    referenced = {
        Path(locator).resolve()
        for (locator,) in db.query(models.HandwritingSample.image_path).all()
        if not locator.startswith("s3://")
    }
    cutoff = datetime.now(timezone.utc).timestamp() - (grace_hours * 3600)
    deleted = 0
    for candidate in UPLOAD_DIR.iterdir():
        if (
            candidate.is_file()
            and not candidate.name.startswith(".")
            and candidate.resolve() not in referenced
            and candidate.stat().st_mtime < cutoff
        ):
            candidate.unlink()
            deleted += 1
    return deleted


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-retention-days", type=int, default=365)
    parser.add_argument("--orphan-grace-hours", type=int, default=24)
    args = parser.parse_args()

    with SessionLocal() as db:
        audits = purge_old_audit_events(db, args.audit_retention_days)
        orphans = cleanup_local_orphans(db, args.orphan_grace_hours)
    print(f"Deleted {audits} audit events and {orphans} orphaned local files")


if __name__ == "__main__":
    main()
