"""Protected audit-event listing and retention endpoints."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.security import require_api_key

router = APIRouter(
    prefix="/audit-events",
    tags=["Audit"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/", response_model=list[schemas.AuditEventResponse])
def list_audit_events(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.AuditEvent)
        .order_by(models.AuditEvent.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.delete("/retention")
def purge_audit_events(
    older_than_days: int = Query(..., ge=1, le=3650),
    db: Session = Depends(get_db),
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
    deleted = (
        db.query(models.AuditEvent)
        .filter(models.AuditEvent.created_at < cutoff)
        .delete(synchronize_session=False)
    )
    db.commit()
    return {"deleted": deleted, "cutoff": cutoff}
