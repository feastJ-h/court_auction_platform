from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.database.models import AuctionItem, UserAuctionPreference


MAX_TAGS_LENGTH = 512
MAX_NOTE_LENGTH = 4000


def _clean_tags(tags: str) -> str:
    parts = [part.strip() for part in (tags or "").replace("#", "").split(",")]
    return ", ".join(part for part in parts if part)[:MAX_TAGS_LENGTH]


def get_or_create_preference(session: Session, user_id: int, auction_item_id: int) -> UserAuctionPreference:
    preference = session.scalar(
        select(UserAuctionPreference).where(
            UserAuctionPreference.user_id == user_id,
            UserAuctionPreference.auction_item_id == auction_item_id,
        )
    )
    if preference:
        return preference
    preference = UserAuctionPreference(user_id=user_id, auction_item_id=auction_item_id)
    session.add(preference)
    session.flush()
    return preference


def get_preference(session: Session, user_id: int, auction_item_id: int) -> UserAuctionPreference | None:
    return session.scalar(
        select(UserAuctionPreference).where(
            UserAuctionPreference.user_id == user_id,
            UserAuctionPreference.auction_item_id == auction_item_id,
        )
    )


def get_preference_map(
    session: Session,
    user_id: int,
    auction_item_ids: list[int],
) -> dict[int, UserAuctionPreference]:
    if not auction_item_ids:
        return {}
    rows = session.scalars(
        select(UserAuctionPreference).where(
            UserAuctionPreference.user_id == user_id,
            UserAuctionPreference.auction_item_id.in_(auction_item_ids),
        )
    )
    return {row.auction_item_id: row for row in rows}


def update_preference(
    session: Session,
    user_id: int,
    auction_item_id: int,
    *,
    favorite: bool | None = None,
    passed: bool | None = None,
    watching: bool | None = None,
    note: str | None = None,
    tags: str | None = None,
) -> UserAuctionPreference:
    preference = get_or_create_preference(session, user_id, auction_item_id)
    if favorite is not None:
        preference.is_favorite = favorite
        if favorite:
            preference.is_passed = False
    if passed is not None:
        preference.is_passed = passed
        if passed:
            preference.is_favorite = False
            preference.is_watching = False
    if watching is not None:
        preference.is_watching = watching
        if watching:
            preference.is_passed = False
    if note is not None:
        preference.note = (note or "")[:MAX_NOTE_LENGTH]
    if tags is not None:
        preference.tags = _clean_tags(tags)
    preference.updated_at = datetime.now()
    session.flush()
    return preference


def serialize_preference(preference: UserAuctionPreference | None) -> dict:
    return {
        "is_favorite": bool(preference and preference.is_favorite),
        "is_passed": bool(preference and preference.is_passed),
        "is_watching": bool(preference and preference.is_watching),
        "note": preference.note if preference else "",
        "tags": preference.tags if preference else "",
    }


def list_preference_items(session: Session, user_id: int, preference_type: str) -> list[AuctionItem]:
    flag_by_type = {
        "favorites": UserAuctionPreference.is_favorite,
        "passed": UserAuctionPreference.is_passed,
        "watching": UserAuctionPreference.is_watching,
        "notes": UserAuctionPreference.note != "",
    }
    condition = flag_by_type.get(preference_type)
    if condition is None:
        condition = UserAuctionPreference.is_favorite
    return list(
        session.scalars(
            select(AuctionItem)
            .join(UserAuctionPreference, UserAuctionPreference.auction_item_id == AuctionItem.id)
            .options(
                joinedload(AuctionItem.case_links),
                joinedload(AuctionItem.notice_links),
            )
            .where(UserAuctionPreference.user_id == user_id, condition)
            .order_by(UserAuctionPreference.updated_at.desc(), UserAuctionPreference.id.desc())
        ).unique()
    )
