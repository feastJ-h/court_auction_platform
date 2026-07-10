from __future__ import annotations

from collections import Counter
from datetime import date


def _notice_key(item: dict) -> str:
    if item.get("pbanc_mng_no"):
        return str(item["pbanc_mng_no"])
    notices = item.get("notices") or []
    if notices:
        notice = notices[0] or {}
        return str(notice.get("id") or notice.get("notice_title") or "")
    return ""


def diversify_onbid_items(
    items: list[dict],
    *,
    limit: int,
    max_per_notice: int = 3,
    max_per_agency: int = 8,
) -> list[dict]:
    """Apply conservative display-only diversity caps without mutating data."""
    selected: list[dict] = []
    notice_counts: Counter[str] = Counter()
    agency_counts: Counter[str] = Counter()
    for item in items:
        notice = _notice_key(item)
        agency = str(item.get("agency_name") or "")
        if notice and notice_counts[notice] >= max_per_notice:
            continue
        if agency and agency_counts[agency] >= max_per_agency:
            continue
        selected.append(item)
        if notice:
            notice_counts[notice] += 1
        if agency:
            agency_counts[agency] += 1
        if len(selected) >= limit:
            break
    return selected


def build_today_review_state(item_views: list[dict], *, today: date | None = None, limit: int = 20) -> dict:
    basis_date = (today or date.today()).isoformat()
    today_items = [item for item in item_views if item.get("first_seen_date") == basis_date]
    queue = diversify_onbid_items(today_items, limit=limit)
    passed = [item for item in queue if item.get("preference", {}).get("is_passed")]
    favorited = [item for item in queue if item.get("preference", {}).get("is_favorite")]
    remaining = [
        item
        for item in queue
        if not item.get("preference", {}).get("is_passed")
        and not item.get("preference", {}).get("is_favorite")
    ]
    return {
        "items": remaining,
        "total": len(queue),
        "all_today_count": len(today_items),
        "passed": len(passed),
        "favorited": len(favorited),
        "complete": bool(queue) and not remaining,
        "basis": "first_seen_at",
        "basis_date": basis_date,
        "has_today_items": bool(today_items),
        "limited": len(today_items) > len(queue),
    }


def select_home_preview(items: list[dict], *, limit: int = 4) -> list[dict]:
    selected: list[dict] = []
    used_notices: set[str] = set()
    per_category = max(1, limit // 2)
    for category in ("real_estate", "movable"):
        category_count = 0
        for item in items:
            notice = _notice_key(item)
            if item.get("category") != category or (notice and notice in used_notices):
                continue
            selected.append(item)
            if notice:
                used_notices.add(notice)
            category_count += 1
            if category_count >= per_category or len(selected) >= limit:
                break
    if len(selected) < limit:
        for item in items:
            notice = _notice_key(item)
            if item in selected or (notice and notice in used_notices):
                continue
            selected.append(item)
            if notice:
                used_notices.add(notice)
            if len(selected) >= limit:
                break
    return selected[:limit]
