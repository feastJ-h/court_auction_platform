from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from backend.database.models import AssetEvent, UserEventAction
from backend.database.models import RawDocument

ACTION_PASSED = "PASSED"
ACTION_BOOKMARKED = "BOOKMARKED"
ACTION_WATCHING = "WATCHING"
VALID_ACTIONS = {ACTION_PASSED, ACTION_BOOKMARKED, ACTION_WATCHING}


def mark_event_action(
    session: Session,
    user_id: int,
    event_id: int,
    action_type: str,
    reason: str = "",
) -> UserEventAction:
    if action_type not in VALID_ACTIONS:
        raise ValueError("invalid_action_type")
    session.execute(
        delete(UserEventAction).where(
            UserEventAction.user_id == user_id,
            UserEventAction.event_id == event_id,
            UserEventAction.action_type != action_type,
        )
    )
    existing = session.scalar(
        select(UserEventAction).where(
            UserEventAction.user_id == user_id,
            UserEventAction.event_id == event_id,
            UserEventAction.action_type == action_type,
        )
    )
    if existing:
        existing.reason = reason or existing.reason
        session.flush()
        return existing
    action = UserEventAction(
        user_id=user_id,
        event_id=event_id,
        action_type=action_type,
        reason=reason or "",
    )
    session.add(action)
    session.flush()
    return action


def clear_event_action(session: Session, user_id: int, event_id: int, action_type: str) -> None:
    if action_type not in VALID_ACTIONS:
        raise ValueError("invalid_action_type")
    session.execute(
        delete(UserEventAction).where(
            UserEventAction.user_id == user_id,
            UserEventAction.event_id == event_id,
            UserEventAction.action_type == action_type,
        )
    )
    session.flush()


def list_action_event_ids(session: Session, user_id: int, action_type: str) -> list[int]:
    if action_type not in VALID_ACTIONS:
        raise ValueError("invalid_action_type")
    return list(
        session.scalars(
            select(UserEventAction.event_id).where(
                UserEventAction.user_id == user_id,
                UserEventAction.action_type == action_type,
            )
        )
    )


def list_action_events(session: Session, user_id: int, action_type: str) -> list[AssetEvent]:
    if action_type not in VALID_ACTIONS:
        raise ValueError("invalid_action_type")
    return list(
        session.scalars(
            select(AssetEvent)
            .join(UserEventAction, UserEventAction.event_id == AssetEvent.id)
            .options(
                joinedload(AssetEvent.asset),
                joinedload(AssetEvent.analyses),
                joinedload(AssetEvent.raw_document).joinedload(RawDocument.evidence),
            )
            .where(
                UserEventAction.user_id == user_id,
                UserEventAction.action_type == action_type,
            )
            .order_by(UserEventAction.updated_at.desc(), UserEventAction.id.desc())
        ).unique()
    )


def mark_event_passed(session: Session, user_id: int, event_id: int, reason: str = "") -> UserEventAction:
    return mark_event_action(session, user_id, event_id, ACTION_PASSED, reason)


def unpass_event(session: Session, user_id: int, event_id: int) -> None:
    clear_event_action(session, user_id, event_id, ACTION_PASSED)


def list_passed_event_ids(session: Session, user_id: int) -> list[int]:
    return list_action_event_ids(session, user_id, ACTION_PASSED)


def list_passed_events(session: Session, user_id: int) -> list[AssetEvent]:
    return list_action_events(session, user_id, ACTION_PASSED)
