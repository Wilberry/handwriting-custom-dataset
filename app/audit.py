"""Helpers for durable, privacy-conscious audit events."""

import json

from fastapi import Request
from sqlalchemy.orm import Session

from app import models


def record_event(
    db: Session,
    request: Request,
    event_type: str,
    entity_type: str,
    entity_id: int | None = None,
    details: dict | None = None,
) -> models.AuditEvent:
    """Persist an event using identity/request context set by dependencies."""
    event = models.AuditEvent(
        event_type=event_type,
        actor=getattr(request.state, "actor", "anonymous"),
        entity_type=entity_type,
        entity_id=entity_id,
        request_id=getattr(request.state, "request_id", None),
        details=json.dumps(details or {}, sort_keys=True),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
