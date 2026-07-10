from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import urlencode


ELLIPSIS = "ellipsis"


def pagination_window(current_page: int, total_pages: int, *, radius: int = 2) -> list[int | str]:
    """Return a compact, stable pagination window.

    Small result sets are shown in full. Larger result sets always include the
    first/last page and a radius around the current page, with a single marker
    for every omitted range.
    """
    total = max(1, int(total_pages or 1))
    current = min(max(1, int(current_page or 1)), total)
    if total <= 7:
        return list(range(1, total + 1))

    visible = {1, total}
    visible.update(range(max(1, current - radius), min(total, current + radius) + 1))
    result: list[int | str] = []
    previous = 0
    for page in sorted(visible):
        if previous and page - previous > 1:
            result.append(ELLIPSIS)
        result.append(page)
        previous = page
    return result


def clean_query_state(state: Mapping[str, object] | None, *, omit: set[str] | None = None) -> dict[str, object]:
    omitted = omit or set()
    cleaned: dict[str, object] = {}
    for key, value in (state or {}).items():
        if key in omitted or value is None or value == "":
            continue
        if key == "category" and value in {"all", "ALL"}:
            continue
        if key in {"status", "asset_type", "linked", "has_notice", "has_detail", "data_quality"} and value == "ALL":
            continue
        cleaned[key] = value
    return cleaned


def build_query_href(
    base_path: str,
    state: Mapping[str, object] | None = None,
    *,
    omit: set[str] | None = None,
    **updates: object,
) -> str:
    merged = dict(state or {})
    merged.update(updates)
    cleaned = clean_query_state(merged, omit=omit)
    query = urlencode(cleaned, doseq=True)
    return f"{base_path}?{query}" if query else base_path


def build_pagination(
    base_path: str,
    *,
    current_page: int,
    total_pages: int,
    query_state: Mapping[str, object] | None = None,
) -> dict[str, object]:
    total = max(1, int(total_pages or 1))
    current = min(max(1, int(current_page or 1)), total)
    items: list[dict[str, object]] = []
    for value in pagination_window(current, total):
        if value == ELLIPSIS:
            items.append({"type": ELLIPSIS})
        else:
            items.append(
                {
                    "type": "page",
                    "page": value,
                    "href": build_query_href(base_path, query_state, page=value),
                    "current": value == current,
                }
            )
    return {
        "page": current,
        "total_pages": total,
        "items": items,
        "has_prev": current > 1,
        "has_next": current < total,
        "prev_href": build_query_href(base_path, query_state, page=current - 1) if current > 1 else "",
        "next_href": build_query_href(base_path, query_state, page=current + 1) if current < total else "",
        "first_href": build_query_href(base_path, query_state, page=1),
        "last_href": build_query_href(base_path, query_state, page=total),
    }
