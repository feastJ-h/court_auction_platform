from __future__ import annotations

import json
import re
import secrets
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import (
    AuctionItem,
    OnbidDataIssueReport,
    OnbidReviewSummaryShare,
    ProductAnalyticsEvent,
)
from backend.services.auction_items import serialize_auction_item


ALLOWED_EVENTS = {
    "view_today_queue",
    "pass_item",
    "undo_pass_item",
    "favorite_item",
    "watch_item",
    "write_memo",
    "click_original_link",
    "complete_today_review",
    "view_review_box",
    "report_data_issue",
    "submit_data_issue",
    "create_review_summary",
    "open_shared_summary",
    "copy_shared_summary_link",
    "view_development_insight_cta",
    "click_development_insight_cta",
    "open_badge_tooltip",
    "view_disclaimer",
    "restore_passed_item",
    "category_view_share",
}
MAX_METADATA_LENGTH = 2000
MAX_PUBLIC_NOTE_LENGTH = 500
MAX_REPORT_NOTE_LENGTH = 200
PERSONAL_INFO_PATTERN = re.compile(r"(\d{2,3}-\d{3,4}-\d{4}|\d{6}-\d{7}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+)")


def safe_session_id(value: str | None) -> str:
    return (value or "")[:128]


def _safe_metadata(metadata: dict[str, Any] | None) -> str:
    cleaned: dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        if key in {"note", "memo", "raw_payload", "raw", "url", "source_url"}:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            cleaned[key[:64]] = value
    return json.dumps(cleaned, ensure_ascii=False, sort_keys=True)[:MAX_METADATA_LENGTH]


def record_product_event(
    session: Session,
    event_name: str,
    *,
    auction_item_id: int | None = None,
    user_id: int | None = None,
    session_id: str = "",
    category: str = "",
    metadata: dict[str, Any] | None = None,
) -> ProductAnalyticsEvent:
    if event_name not in ALLOWED_EVENTS:
        raise ValueError(f"Unsupported product event: {event_name}")
    event = ProductAnalyticsEvent(
        event_name=event_name,
        auction_item_id=auction_item_id,
        user_id=user_id,
        session_id=safe_session_id(session_id),
        category=(category or "")[:64],
        metadata_json=_safe_metadata(metadata),
    )
    session.add(event)
    session.flush()
    return event


def create_data_issue_report(
    session: Session,
    *,
    auction_item_id: int,
    user_id: int | None,
    session_id: str,
    issue_types: list[str],
    note: str,
) -> OnbidDataIssueReport:
    allowed_types = {
        "price",
        "schedule",
        "source_link",
        "photo_address",
        "location",
        "area",
        "closed_status",
        "duplicate",
        "personal_info",
    }
    normalized_types = [issue_type for issue_type in issue_types if issue_type in allowed_types]
    contains_personal_info = "personal_info" in normalized_types or bool(PERSONAL_INFO_PATTERN.search(note or ""))
    report = OnbidDataIssueReport(
        auction_item_id=auction_item_id,
        user_id=user_id,
        reporter_session_id=safe_session_id(session_id),
        issue_types_json=json.dumps(normalized_types, ensure_ascii=False),
        note=(note or "")[:MAX_REPORT_NOTE_LENGTH],
        contains_personal_info=contains_personal_info,
        status="pending",
    )
    session.add(report)
    session.flush()
    record_product_event(
        session,
        "submit_data_issue",
        auction_item_id=auction_item_id,
        user_id=user_id,
        session_id=session_id,
        metadata={"issue_type_count": len(normalized_types), "contains_personal_info": contains_personal_info},
    )
    return report


def _public_summary_payload(item: AuctionItem, public_note: str = "") -> dict[str, Any]:
    view = serialize_auction_item(item)
    return {
        "item_name": view["item_name"],
        "category_label": view["category_label"],
        "address": view["address"],
        "minimum_bid_price": view["minimum_bid_price"],
        "appraisal_price": view["appraisal_price"],
        "bid_end_at": view["bid_end_at"],
        "agency_name": view["agency_name"],
        "data_status": "자료 확인 필요" if view["info_badges"]["has_critical_missing"] else "공개 자료 기준 정리",
        "external_url": view["external_url"],
        "public_note": public_note[:MAX_PUBLIC_NOTE_LENGTH],
    }


def create_review_summary_share(
    session: Session,
    *,
    item: AuctionItem,
    user_id: int,
    session_id: str,
    public_note: str = "",
) -> OnbidReviewSummaryShare:
    token = secrets.token_urlsafe(24)
    public_note = (public_note or "")[:MAX_PUBLIC_NOTE_LENGTH]
    share = OnbidReviewSummaryShare(
        token=token,
        auction_item_id=item.id,
        created_by_user_id=user_id,
        public_note=public_note,
        summary_json=json.dumps(_public_summary_payload(item, public_note), ensure_ascii=False, sort_keys=True),
    )
    session.add(share)
    session.flush()
    record_product_event(
        session,
        "create_review_summary",
        auction_item_id=item.id,
        user_id=user_id,
        session_id=session_id,
        category=serialize_auction_item(item)["category"],
    )
    return share


def get_review_summary_share(session: Session, token: str) -> OnbidReviewSummaryShare | None:
    return session.scalar(
        select(OnbidReviewSummaryShare).where(
            OnbidReviewSummaryShare.token == token,
            OnbidReviewSummaryShare.revoked_at.is_(None),
        )
    )


def parse_share_summary(share: OnbidReviewSummaryShare) -> dict[str, Any]:
    try:
        return json.loads(share.summary_json or "{}")
    except json.JSONDecodeError:
        return {}
