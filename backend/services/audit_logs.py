from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.database.models import AuditLog


def create_audit_log(
    session: Session,
    actor_user_id: int | None,
    action: str,
    target_type: str = "",
    target_id: str | int = "",
    summary: str = "",
    metadata: dict | None = None,
) -> AuditLog:
    log = AuditLog(
        actor_user_id=actor_user_id,
        action=action[:128],
        target_type=target_type[:64],
        target_id=str(target_id)[:128],
        summary=summary[:512],
        metadata_json=json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True)[:4000],
    )
    session.add(log)
    session.flush()
    return log


def list_recent_audit_logs(session: Session, limit: int = 50) -> list[AuditLog]:
    return list(
        session.scalars(
            select(AuditLog)
            .options(joinedload(AuditLog.actor))
            .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .limit(limit)
        )
    )
