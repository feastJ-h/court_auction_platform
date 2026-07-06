from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database.models import AuctionItem, AuctionNotice, AuctionNoticeItemLink, CrawlRun
from backend.services.auction_items import build_onbid_info_badges, derive_onbid_category


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
    missing_summary = get_onbid_missing_summary(session)
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
        "missing": missing_summary,
    }


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


def get_onbid_category_counts(session: Session) -> dict[str, int]:
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
