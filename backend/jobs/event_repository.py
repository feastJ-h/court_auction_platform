import json
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import AnalysisJob, AnalysisJobEvent


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def create_job_event(
    session: Session,
    job: AnalysisJob,
    event_type: str,
    payload: dict[str, Any] | list[Any] | str | None = None,
    message: str = "",
) -> AnalysisJobEvent:
    if isinstance(payload, str):
        payload_text = payload
    else:
        payload_text = json.dumps(payload or {}, ensure_ascii=False)

    event = AnalysisJobEvent(
        job_id=job.id,
        event_type=event_type,
        event_payload=payload_text,
        message=message[:4000],
    )
    session.add(event)
    session.flush()
    return event


def list_job_events(session: Session, job_id: int, limit: int = 200) -> list[AnalysisJobEvent]:
    return list(
        session.scalars(
            select(AnalysisJobEvent)
            .where(AnalysisJobEvent.job_id == job_id)
            .order_by(AnalysisJobEvent.id.asc())
            .limit(limit)
        )
    )


def serialize_event(event: AnalysisJobEvent) -> dict:
    return {
        "id": event.id,
        "job_id": event.job_id,
        "event_type": event.event_type,
        "event_payload": event.event_payload,
        "message": event.message,
        "created_at": _iso(event.created_at),
    }
