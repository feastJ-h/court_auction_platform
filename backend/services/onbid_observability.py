from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database.models import AuctionItem, AuctionNotice, AuctionNoticeItemLink, CrawlRun
from backend.services.auction_items import (
    audit_onbid_freshness,
    build_onbid_info_badges,
    derive_onbid_category,
    get_onbid_category_counts,
    get_onbid_deadline_status,
    get_onbid_external_url,
    is_onbid_item_public_visible,
)


def build_onbid_observability_summary(session: Session, *, days: int = 7) -> dict[str, Any]:
    cutoff = datetime.now() - timedelta(days=max(1, days))
    total_items = session.scalar(select(func.count(AuctionItem.id)).where(AuctionItem.source == "ONBID")) or 0
    total_notices = session.scalar(select(func.count(AuctionNotice.id)).where(AuctionNotice.source == "ONBID")) or 0
    notices_with_detail = (
        session.scalar(
            select(func.count(AuctionNotice.id)).where(
                AuctionNotice.source == "ONBID",
                AuctionNotice.detail_payload.notin_(("", "{}")),
            )
        )
        or 0
    )
    notice_item_links = session.scalar(select(func.count(AuctionNoticeItemLink.id)).where(AuctionNoticeItemLink.source == "ONBID")) or 0
    items_with_notice = (
        session.scalar(
            select(func.count(AuctionItem.id)).where(
                AuctionItem.source == "ONBID",
                AuctionItem.pbanc_mng_no != "",
            )
        )
        or 0
    )
    items_with_detail_payload = (
        session.scalar(
            select(func.count(AuctionItem.id)).where(
                AuctionItem.source == "ONBID",
                AuctionItem.raw_payload.like("%_raw_detail%"),
            )
        )
        or 0
    )
    recent_runs = list(
        session.scalars(
            select(CrawlRun)
            .where(CrawlRun.run_type.like("onbid_%"), CrawlRun.started_at >= cutoff)
            .order_by(CrawlRun.started_at.desc(), CrawlRun.id.desc())
        )
    )
    latest_failure = next((run for run in recent_runs if run.status == "FAILED"), None)
    distribution = get_onbid_deadline_distribution(session)
    category_counts = get_onbid_category_counts(session)
    public_category_counts = get_onbid_category_counts(session, public_only=True)
    missing_summary = get_onbid_missing_summary(session)
    freshness_summary = audit_onbid_freshness(session)
    return {
        "days": max(1, days),
        "items": {
            "total": total_items,
            "with_notice": items_with_notice,
            "with_detail_payload": items_with_detail_payload,
        },
        "notices": {
            "total": total_notices,
            "with_detail": notices_with_detail,
            "detail_coverage_rate": percentage(notices_with_detail, total_notices),
        },
        "links": {
            "notice_item_links": notice_item_links,
            "item_notice_link_rate": percentage(notice_item_links, max(total_items, 1)),
        },
        "runs": {
            "recent_total": len(recent_runs),
            "recent_success": sum(1 for run in recent_runs if run.status == "SUCCEEDED"),
            "recent_failed": sum(1 for run in recent_runs if run.status == "FAILED"),
            "latest_failure": serialize_run(latest_failure),
            "by_type": summarize_runs_by_type(recent_runs),
        },
        "deadline_distribution": distribution,
        "categories": category_counts,
        "public_categories": public_category_counts,
        "freshness": freshness_summary,
        "missing": missing_summary,
    }


def build_onbid_data_quality_summary(session: Session) -> dict[str, Any]:
    """Operational metrics for the admin-only ONBID data quality view."""
    items = list(session.scalars(select(AuctionItem).where(AuctionItem.source == "ONBID")))
    public_items = [item for item in items if is_onbid_item_public_visible(item)]
    active_items = [item for item in public_items if get_onbid_deadline_status(item.bid_end_at)["is_active"]]
    ended_items = [item for item in public_items if get_onbid_deadline_status(item.bid_end_at)["state"] == "closed"]
    source_counts: dict[str, int] = {}
    category_counts = {"real_estate": 0, "movable": 0, "national_property": 0, "other": 0}
    missing_original: list[dict[str, Any]] = []
    missing_detail: list[dict[str, Any]] = []
    active_status_conflicts: list[dict[str, Any]] = []
    with_original = 0
    detail_body = 0
    false_detail_available = 0
    for item in public_items:
        category = derive_onbid_category(item)
        category_counts[category] = category_counts.get(category, 0) + 1
        try:
            import json
            raw = json.loads(item.raw_payload or "{}")
        except (TypeError, ValueError):
            raw = {}
        source_api = str(raw.get("_source_api") or raw.get("sourceApi") or "unknown")
        source_counts[source_api] = source_counts.get(source_api, 0) + 1
        url = get_onbid_external_url(item)
        badges = build_onbid_info_badges(item)
        has_detail = "상세 설명: 확인됨" in badges["available"]
        if url:
            with_original += 1
        else:
            missing_original.append(_quality_item_view(item))
        if has_detail:
            detail_body += 1
        else:
            missing_detail.append(_quality_item_view(item))
        marker_only = "_raw_detail" in raw and not has_detail
        if marker_only:
            false_detail_available += 1
        deadline = get_onbid_deadline_status(item.bid_end_at)
        if deadline["state"] == "closed" and "진행" in (item.status or ""):
            active_status_conflicts.append(_quality_item_view(item))
    latest_runs = list(session.scalars(select(CrawlRun).where(CrawlRun.run_type.like("onbid_%")).order_by(CrawlRun.started_at.desc()).limit(50)))
    last_sync = next((run for run in latest_runs if run.status == "SUCCEEDED"), None)
    last_detail = next((run for run in latest_runs if "detail" in (run.run_type or "").lower() and run.status == "SUCCEEDED"), None)
    total_public = len(public_items)
    total_active = len(active_items)
    return {
        "public_visible_fresh_non_sample": total_public,
        "active_or_upcoming": total_active,
        "ended": len(ended_items),
        "category_counts": category_counts,
        "original_url_coverage": percentage(with_original, total_public),
        "active_original_url_coverage": percentage(sum(1 for item in active_items if get_onbid_external_url(item)), total_active),
        "detail_body_coverage": percentage(detail_body, total_public),
        "source_api_counts": source_counts,
        "missing_original_url_count": len(missing_original),
        "missing_price_count": sum(1 for item in public_items if not (item.minimum_bid_price or item.appraisal_price)),
        "missing_address_count": sum(1 for item in public_items if not (item.address or "").strip()),
        "missing_deadline_count": sum(1 for item in public_items if get_onbid_deadline_status(item.bid_end_at)["state"] == "unknown"),
        "false_detail_available_count": false_detail_available,
        "national_property_note": "Fresh public national-property rows depend on the source API date fields; no inference is used when the source does not provide a valid schedule.",
        "last_sync_at": last_sync.finished_at.isoformat() if last_sync and last_sync.finished_at else "",
        "last_detail_enrichment_at": last_detail.finished_at.isoformat() if last_detail and last_detail.finished_at else "",
        "missing_original_items": missing_original[:50],
        "missing_detail_items": missing_detail[:50],
        "ended_active_conflicts": active_status_conflicts[:50],
    }


def _quality_item_view(item: AuctionItem) -> dict[str, Any]:
    return {"id": item.id, "item_name": item.item_name, "category": derive_onbid_category(item), "bid_end_at": item.bid_end_at}


def get_onbid_deadline_distribution(session: Session) -> dict[str, int]:
    buckets = {
        "closed": 0,
        "today": 0,
        "within_3_days": 0,
        "within_7_days": 0,
        "within_14_days": 0,
        "within_30_days": 0,
        "over_30_days": 0,
        "unknown": 0,
    }
    today = date.today()
    values = session.scalars(select(AuctionItem.bid_end_at).where(AuctionItem.source == "ONBID"))
    for value in values:
        parsed = parse_date(value)
        if parsed is None:
            buckets["unknown"] += 1
            continue
        delta = (parsed - today).days
        if delta < 0:
            buckets["closed"] += 1
        elif delta == 0:
            buckets["today"] += 1
        elif delta <= 3:
            buckets["within_3_days"] += 1
        elif delta <= 7:
            buckets["within_7_days"] += 1
        elif delta <= 14:
            buckets["within_14_days"] += 1
        elif delta <= 30:
            buckets["within_30_days"] += 1
        else:
            buckets["over_30_days"] += 1
    return buckets


def get_onbid_category_counts_legacy(session: Session) -> dict[str, int]:
    counts = {"real_estate": 0, "movable": 0, "national_property": 0, "other": 0}
    items = session.scalars(select(AuctionItem).where(AuctionItem.source == "ONBID"))
    for item in items:
        category = derive_onbid_category(item)
        counts[category if category in counts else "other"] += 1
    return counts


def get_onbid_missing_summary(session: Session) -> dict[str, Any]:
    labels = {
        "가격 정보 확인 필요": "price_missing",
        "소재지 정보 확인 필요": "location_missing",
        "입찰 일정 확인 필요": "schedule_missing",
        "공고 연결 확인 필요": "notice_missing",
        "상세 정보 수집 필요": "detail_missing",
        "원문 링크 확인 필요": "source_url_missing",
    }
    counts = {value: 0 for value in labels.values()}
    total = 0
    items = session.scalars(
        select(AuctionItem)
        .where(AuctionItem.source == "ONBID")
        .options()
    )
    for item in items:
        total += 1
        badges = build_onbid_info_badges(item)
        for label in badges["missing"]:
            key = labels.get(label)
            if key:
                counts[key] += 1
    return {
        "total": total,
        **counts,
        "price_missing_rate": percentage(counts["price_missing"], total),
        "location_missing_rate": percentage(counts["location_missing"], total),
        "schedule_missing_rate": percentage(counts["schedule_missing"], total),
        "notice_missing_rate": percentage(counts["notice_missing"], total),
        "detail_missing_rate": percentage(counts["detail_missing"], total),
        "source_url_missing_rate": percentage(counts["source_url_missing"], total),
    }


def parse_date(value: str) -> date | None:
    text = str(value or "").strip()[:10]
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def percentage(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((part / total) * 100, 2)


def summarize_runs_by_type(runs: list[CrawlRun]) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = {}
    for run in runs:
        bucket = summary.setdefault(run.run_type, {"total": 0, "success": 0, "failed": 0})
        bucket["total"] += 1
        if run.status == "SUCCEEDED":
            bucket["success"] += 1
        if run.status == "FAILED":
            bucket["failed"] += 1
    return summary


def serialize_run(run: CrawlRun | None) -> dict[str, Any] | None:
    if run is None:
        return None
    return {
        "id": run.id,
        "run_type": run.run_type,
        "status": run.status,
        "started_at": run.started_at.isoformat() if run.started_at else "",
        "finished_at": run.finished_at.isoformat() if run.finished_at else "",
        "error_message": run.error_message,
    }
