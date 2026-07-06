from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import AiAnalysis, AssetEvent
from backend.jobs.repository import get_active_job_for_event
from backend.jobs.service import create_or_get_deep_analysis_job


def enqueue_missing_deep_analysis_jobs(
    session: Session,
    limit: int = 20,
    requested_by: str = "scheduler",
) -> list[dict]:
    events = list(
        session.scalars(
            select(AssetEvent)
            .join(AiAnalysis)
            .where(AiAnalysis.detailed_analysis == "")
            .order_by(AssetEvent.notice_date.desc(), AssetEvent.id.asc())
            .limit(limit)
        )
    )

    queued: list[dict] = []
    for event in events:
        if get_active_job_for_event(session, event.id):
            continue
        queued.append(
            create_or_get_deep_analysis_job(
                session=session,
                event_id=event.id,
                requested_by=requested_by,
            )
        )
    return queued
