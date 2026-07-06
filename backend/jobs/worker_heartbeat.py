from datetime import datetime, timedelta, timezone
import os
import socket

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import AnalysisWorkerHeartbeat


STALE_AFTER = timedelta(minutes=10)


def default_worker_id(worker_type: str, provider_mode: str, endpoint: str = "") -> str:
    endpoint_key = endpoint.replace("ws://", "").replace("http://", "") or "local"
    return f"{socket.gethostname()}:{worker_type}:{provider_mode}:{endpoint_key}"


def upsert_worker_heartbeat(
    session: Session,
    worker_id: str,
    worker_type: str,
    provider_mode: str,
    status: str,
    status_message: str = "",
    current_job_id: int | None = None,
    app_server_endpoint: str = "",
    pid: int | None = None,
) -> AnalysisWorkerHeartbeat:
    now = datetime.now(timezone.utc)
    heartbeat = session.scalar(
        select(AnalysisWorkerHeartbeat).where(AnalysisWorkerHeartbeat.worker_id == worker_id)
    )
    if heartbeat is None:
        heartbeat = AnalysisWorkerHeartbeat(
            worker_id=worker_id,
            worker_type=worker_type,
            provider_mode=provider_mode,
            started_at=now,
        )
        session.add(heartbeat)

    heartbeat.status = status
    heartbeat.status_message = status_message[:4000]
    heartbeat.current_job_id = current_job_id
    heartbeat.last_seen_at = now
    heartbeat.app_server_endpoint = app_server_endpoint
    heartbeat.pid = pid if pid is not None else os.getpid()
    session.flush()
    return heartbeat


def list_worker_heartbeats(session: Session) -> list[AnalysisWorkerHeartbeat]:
    return list(
        session.scalars(
            select(AnalysisWorkerHeartbeat).order_by(
                AnalysisWorkerHeartbeat.last_seen_at.desc(),
                AnalysisWorkerHeartbeat.id.desc(),
            )
        )
    )


def is_heartbeat_stale(heartbeat: AnalysisWorkerHeartbeat, now: datetime | None = None) -> bool:
    if heartbeat.status not in {"RUNNING", "STARTING"}:
        return False
    reference = now or datetime.now(timezone.utc)
    last_seen = heartbeat.last_seen_at
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)
    return reference - last_seen > STALE_AFTER


def serialize_worker_heartbeat(heartbeat: AnalysisWorkerHeartbeat) -> dict:
    return {
        "id": heartbeat.id,
        "worker_id": heartbeat.worker_id,
        "worker_type": heartbeat.worker_type,
        "provider_mode": heartbeat.provider_mode,
        "status": heartbeat.status,
        "current_job_id": heartbeat.current_job_id,
        "status_message": heartbeat.status_message,
        "last_seen_at": heartbeat.last_seen_at.isoformat() if heartbeat.last_seen_at else None,
        "started_at": heartbeat.started_at.isoformat() if heartbeat.started_at else None,
        "app_server_endpoint": heartbeat.app_server_endpoint,
        "pid": heartbeat.pid,
        "stale": is_heartbeat_stale(heartbeat),
    }
