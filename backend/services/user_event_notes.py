from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import UserEventNote


MAX_TAGS_LENGTH = 512
MAX_NOTE_LENGTH = 4000


def _clean_tags(tags: str) -> str:
    parts = [part.strip() for part in tags.replace("#", "").split(",")]
    return ", ".join(part for part in parts if part)[:MAX_TAGS_LENGTH]


def upsert_user_event_note(
    session: Session,
    user_id: int,
    event_id: int,
    note: str = "",
    tags: str = "",
) -> UserEventNote:
    existing = session.scalar(
        select(UserEventNote).where(
            UserEventNote.user_id == user_id,
            UserEventNote.event_id == event_id,
        )
    )
    clean_note = (note or "")[:MAX_NOTE_LENGTH]
    clean_tags = _clean_tags(tags or "")
    if existing:
        existing.note = clean_note
        existing.tags = clean_tags
        session.flush()
        return existing
    user_note = UserEventNote(
        user_id=user_id,
        event_id=event_id,
        note=clean_note,
        tags=clean_tags,
    )
    session.add(user_note)
    session.flush()
    return user_note


def get_user_event_note(session: Session, user_id: int, event_id: int) -> UserEventNote | None:
    return session.scalar(
        select(UserEventNote).where(
            UserEventNote.user_id == user_id,
            UserEventNote.event_id == event_id,
        )
    )


def get_user_event_note_map(session: Session, user_id: int, event_ids: list[int]) -> dict[int, UserEventNote]:
    if not event_ids:
        return {}
    rows = session.scalars(
        select(UserEventNote).where(
            UserEventNote.user_id == user_id,
            UserEventNote.event_id.in_(event_ids),
        )
    )
    return {row.event_id: row for row in rows}
