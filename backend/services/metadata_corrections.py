from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from backend.database.crud import get_event_with_details


ALLOWED_PARSE_STATUSES = {
    "PARSED",
    "OCR_REQUIRED",
    "OCR_MOCKED",
    "OCR_PARSED",
    "MANUAL_REVIEW",
    "PARSE_FAILED",
    "TEXT_EXTRACTION_FAILED",
    "LOCAL_INGESTED",
    "UNKNOWN",
}


def _clean_date(value: str) -> str:
    clean = (value or "").strip()
    if not clean or clean.upper() == "UNKNOWN":
        return "UNKNOWN"
    try:
        datetime.strptime(clean, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("invalid_date") from exc
    return clean


def update_event_metadata(
    session: Session,
    event_id: int,
    notice_date: str,
    expire_date: str,
    parse_status: str,
    title: str = "",
) -> dict:
    event = get_event_with_details(session, event_id)
    if event is None:
        raise ValueError("event_not_found")

    clean_notice = _clean_date(notice_date)
    clean_expire = _clean_date(expire_date)
    clean_parse_status = (parse_status or "").strip() or event.parse_status
    if clean_parse_status not in ALLOWED_PARSE_STATUSES:
        raise ValueError("invalid_parse_status")

    old = {
        "notice_date": event.notice_date,
        "expire_date": event.expire_date,
        "parse_status": event.parse_status,
        "title": event.title,
    }

    event.notice_date = clean_notice
    event.expire_date = clean_expire
    event.parse_status = clean_parse_status
    if title.strip():
        event.title = title.strip()[:512]

    evidence = event.raw_document.evidence if event.raw_document else None
    if evidence:
        evidence.notice_date = clean_notice
        evidence.expire_date = clean_expire
        if title.strip():
            evidence.source_title = title.strip()[:512]

    session.flush()
    return {
        "old": old,
        "new": {
            "notice_date": event.notice_date,
            "expire_date": event.expire_date,
            "parse_status": event.parse_status,
            "title": event.title,
        },
    }
