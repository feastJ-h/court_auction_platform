from __future__ import annotations

from datetime import date
from math import ceil
from urllib.parse import urlencode
from fastapi import Body, FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from backend.database.crud import get_event_with_details
from backend.database.session import session_scope
from backend.config import get_settings
from backend.services.auction_items import (
    count_auction_items,
    create_case_auction_link,
    find_auction_candidates_for_case,
    find_link_candidates_for_auction,
    get_auction_item,
    get_onbid_category_counts,
    list_same_notice_items,
    list_auction_items,
    normalize_public_category,
    is_onbid_item_public_visible,
    serialize_auction_item,
)
from backend.services.audit_logs import create_audit_log
from backend.services.product_engagement import (
    create_data_issue_report,
    create_review_summary_share,
    get_review_summary_share,
    parse_share_summary,
    record_product_event,
)
from backend.services.user_auction_preferences import (
    get_preference,
    get_preference_map,
    list_preference_items,
    serialize_preference,
    update_preference,
)
from backend.web.dependencies import LoginRedirect, RequireAdmin, RequireUser, admin_login_required
from backend.workers.onbid_sync import run_onbid_sync


def build_query_href(base_path: str, **params) -> str:
    cleaned = {}
    for key, value in params.items():
        if value is None or value == "":
            continue
        if key == "category" and value == "all":
            continue
        cleaned[key] = value
    query = urlencode(cleaned)
    return f"{base_path}?{query}" if query else base_path


def build_price_presets(base_path: str, *, category: str, region: str) -> list[dict[str, str]]:
    return [
        {"key": "all", "label": "가격 전체", "href": build_query_href(base_path, category=category, region=region)},
        {"key": "under_100m", "label": "1억 이하", "href": build_query_href(base_path, price_max=100000000, category=category, region=region)},
        {"key": "100m_300m", "label": "1억-3억", "href": build_query_href(base_path, price_min=100000000, price_max=300000000, category=category, region=region)},
        {"key": "300m_500m", "label": "3억-5억", "href": build_query_href(base_path, price_min=300000000, price_max=500000000, category=category, region=region)},
        {"key": "over_500m", "label": "5억 이상", "href": build_query_href(base_path, price_min=500000000, category=category, region=region)},
    ]


def build_category_links(base_path: str, filters: dict, counts: dict[str, int]) -> list[dict[str, str | int]]:
    labels = {
        "all": "전체",
        "real_estate": "부동산",
        "movable": "동산",
        "national_property": "국유일반재산",
        "other": "기타",
    }
    return [
        {
            "value": value,
            "label": label,
            "count": counts.get(value, 0),
            "href": build_query_href(
                base_path,
                category=value,
                region=filters.get("region"),
                price_min=filters.get("price_min"),
                price_max=filters.get("price_max"),
                data_quality=filters.get("data_quality"),
            ),
        }
        for value, label in labels.items()
    ]


def register_auction_routes(
    app: FastAPI,
    templates: Jinja2Templates,
    *,
    require_user: RequireUser,
    require_admin: RequireAdmin,
    login_redirect: LoginRedirect,
) -> None:
    def _read_int(
        value,
        *,
        minimum: int = 0,
        maximum: int | None = None,
        default: int | None = None,
    ) -> int | None:
        if value in (None, ""):
            return default
        try:
            parsed = int(str(value).strip())
        except (TypeError, ValueError):
            return default
        if parsed < minimum:
            return default
        if maximum is not None and parsed > maximum:
            return maximum
        return parsed

    def _read_float(value, *, minimum: float = 0.0, maximum: float | None = None) -> float | None:
        if value in (None, ""):
            return None
        try:
            parsed = float(str(value).strip())
        except (TypeError, ValueError):
            return None
        if parsed < minimum:
            return None
        if maximum is not None and parsed > maximum:
            return maximum
        return parsed

    def _analytics_session_id(request: Request) -> str:
        session_cookie = request.cookies.get("court_session") or ""
        if session_cookie:
            return session_cookie[:128]
        return request.cookies.get("session") or ""

    def _is_today_review_item(view: dict) -> bool:
        return view.get("freshness_date") == date.today().isoformat()

    def _today_review_state(item_views: list[dict]) -> dict:
        today_items = [view for view in item_views if _is_today_review_item(view)]
        if not today_items:
            today_items = item_views[:20]
        passed = [view for view in today_items if view.get("preference", {}).get("is_passed")]
        favorited = [view for view in today_items if view.get("preference", {}).get("is_favorite")]
        remaining = [
            view
            for view in today_items
            if not view.get("preference", {}).get("is_passed") and not view.get("preference", {}).get("is_favorite")
        ]
        return {
            "items": remaining,
            "total": len(today_items),
            "passed": len(passed),
            "favorited": len(favorited),
            "complete": bool(today_items) and not remaining,
        }

    def _render_auction_list(
        request: Request,
        *,
        page: int,
        status: str,
        asset_type: str,
        keyword: str,
        linked: str,
        region: str,
        usage: str,
        agency: str,
        price_min: int | None,
        price_max: int | None,
        closing_within_days: int | None,
        min_discount_rate: float | None,
        has_notice: str,
        has_detail: str,
        data_quality: str,
        category: str,
        notice_id: int | None,
        pbanc_mng_no: str,
        sort: str,
        base_path: str,
    ):
        per_page = 20
        public_only = base_path == "/onbid"
        category = normalize_public_category(category)
        with session_scope() as session:
            current_user = require_user(request, session)
            total_count = count_auction_items(
                session,
                status=status,
                asset_type=asset_type,
                keyword=keyword,
                linked=linked,
                region=region,
                usage=usage,
                agency=agency,
                price_min=_read_int(price_min),
                price_max=_read_int(price_max),
                closing_within_days=_read_int(closing_within_days, maximum=365),
                min_discount_rate=_read_float(min_discount_rate, maximum=100),
                has_notice=has_notice,
                has_detail=has_detail,
                data_quality=data_quality,
                category=category,
                public_only=public_only,
                notice_id=_read_int(notice_id, minimum=1),
                pbanc_mng_no=pbanc_mng_no,
            )
            total_pages = max(1, ceil(total_count / per_page))
            current_page = min(page, total_pages)
            items = list_auction_items(
                session,
                status=status,
                asset_type=asset_type,
                keyword=keyword,
                linked=linked,
                region=region,
                usage=usage,
                agency=agency,
                price_min=_read_int(price_min),
                price_max=_read_int(price_max),
                closing_within_days=_read_int(closing_within_days, maximum=365),
                min_discount_rate=_read_float(min_discount_rate, maximum=100),
                has_notice=has_notice,
                has_detail=has_detail,
                data_quality=data_quality,
                category=category,
                public_only=public_only,
                notice_id=_read_int(notice_id, minimum=1),
                pbanc_mng_no=pbanc_mng_no,
                sort=sort,
                limit=per_page,
                offset=(current_page - 1) * per_page,
            )
            item_views = [serialize_auction_item(item) for item in items]
            preferences = (
                get_preference_map(session, current_user.id, [item.id for item in items])
                if current_user
                else {}
            )
            for view in item_views:
                view["preference"] = serialize_preference(preferences.get(view["id"]))
            filters = {
                "status": status,
                "asset_type": asset_type,
                "keyword": keyword,
                "linked": linked,
                "region": region.strip(),
                "usage": usage,
                "agency": agency,
                "price_min": _read_int(price_min) or "",
                "price_max": _read_int(price_max) or "",
                "closing_within_days": _read_int(closing_within_days, maximum=365) or "",
                "min_discount_rate": _read_float(min_discount_rate, maximum=100) or "",
                "has_notice": has_notice,
                "has_detail": has_detail,
                "data_quality": data_quality,
                "category": category,
                "notice_id": _read_int(notice_id, minimum=1) or "",
                "pbanc_mng_no": pbanc_mng_no,
                "sort": sort,
            }
            category_counts = get_onbid_category_counts(session, public_only=public_only)
            return templates.TemplateResponse(
                request,
                "auctions/index.html",
                {
                    "current_user": current_user,
                    "settings": get_settings(),
                    "active_section": "onbid",
                    "active_subsection": "",
                    "active_category": category,
                    "page_title": "온비드 공매 공개 목록" if public_only else "공매 목록",
                    "breadcrumbs": [{"label": "ONBID", "href": base_path}],
                    "review_mode": get_settings().review_mode,
                    "items": item_views,
                    "base_path": base_path,
                    "filters": filters,
                    "category_counts": category_counts,
                    "category_links": build_category_links(base_path, filters, category_counts),
                    "price_presets": build_price_presets(base_path, category=category, region=filters["region"]),
                "pagination": {
                        "page": current_page,
                        "pages": list(range(1, total_pages + 1)),
                        "has_prev": current_page > 1,
                        "has_next": current_page < total_pages,
                        "prev_page": max(1, current_page - 1),
                        "next_page": min(total_pages, current_page + 1),
                        "prev_href": build_query_href(base_path, page=max(1, current_page - 1), region=filters["region"], category=category, price_min=filters["price_min"], price_max=filters["price_max"], data_quality=filters["data_quality"]),
                        "next_href": build_query_href(base_path, page=min(total_pages, current_page + 1), region=filters["region"], category=category, price_min=filters["price_min"], price_max=filters["price_max"], data_quality=filters["data_quality"]),
                        "page_links": [
                            {
                                "page": p,
                                "href": build_query_href(base_path, page=p, region=filters["region"], category=category, price_min=filters["price_min"], price_max=filters["price_max"], data_quality=filters["data_quality"]),
                            }
                            for p in range(1, total_pages + 1)
                        ],
                    },
                    "total_count": total_count,
                },
            )

    @app.get("/auctions")
    def auction_list_page(
        request: Request,
        page: str = Query("1"),
        status: str = Query("ALL"),
        asset_type: str = Query("ALL"),
        keyword: str = Query(""),
        q: str = Query(""),
        linked: str = Query("ALL"),
        region: str = Query(""),
        usage: str = Query(""),
        agency: str = Query(""),
        price_min: str = Query(""),
        price_max: str = Query(""),
        closing_within_days: str = Query(""),
        min_discount_rate: str = Query(""),
        has_notice: str = Query("ALL"),
        has_detail: str = Query("ALL"),
        data_quality: str = Query("ALL"),
        category: str = Query("all"),
        notice_id: str = Query(""),
        pbanc_mng_no: str = Query(""),
        sort: str = Query("closing_soon"),
    ):
        return _render_auction_list(
            request,
            page=_read_int(page, minimum=1, default=1) or 1,
            status=status,
            asset_type=asset_type,
            keyword=q or keyword,
            linked=linked,
            region=region,
            usage=usage,
            agency=agency,
            price_min=price_min,
            price_max=price_max,
            closing_within_days=closing_within_days,
            min_discount_rate=min_discount_rate,
            has_notice=has_notice,
            has_detail=has_detail,
            data_quality=data_quality,
            category=category,
            notice_id=notice_id,
            pbanc_mng_no=pbanc_mng_no,
            sort=sort,
            base_path="/auctions",
        )

    @app.get("/onbid")
    def onbid_list_page(
        request: Request,
        page: str = Query("1"),
        status: str = Query("ALL"),
        asset_type: str = Query("ALL"),
        q: str = Query(""),
        keyword: str = Query(""),
        linked: str = Query("ALL"),
        region: str = Query(""),
        usage: str = Query(""),
        agency: str = Query(""),
        price_min: str = Query(""),
        price_max: str = Query(""),
        closing_within_days: str = Query(""),
        min_discount_rate: str = Query(""),
        has_notice: str = Query("ALL"),
        has_detail: str = Query("ALL"),
        data_quality: str = Query("ALL"),
        category: str = Query("all"),
        notice_id: str = Query(""),
        pbanc_mng_no: str = Query(""),
        sort: str = Query("closing_soon"),
    ):
        return _render_auction_list(
            request,
            page=_read_int(page, minimum=1, default=1) or 1,
            status=status,
            asset_type=asset_type,
            keyword=q or keyword,
            linked=linked,
            region=region,
            usage=usage,
            agency=agency,
            price_min=price_min,
            price_max=price_max,
            closing_within_days=closing_within_days,
            min_discount_rate=min_discount_rate,
            has_notice=has_notice,
            has_detail=has_detail,
            data_quality=data_quality,
            category=category,
            notice_id=notice_id,
            pbanc_mng_no=pbanc_mng_no,
            sort=sort,
            base_path="/onbid",
        )

    @app.get("/onbid/today")
    def onbid_today_page(request: Request):
        with session_scope() as session:
            current_user = require_user(request, session)
            items = list_auction_items(
                session,
                public_only=True,
                sort="newest",
                limit=200,
                offset=0,
            )
            item_views = [serialize_auction_item(item) for item in items]
            preferences = (
                get_preference_map(session, current_user.id, [item.id for item in items])
                if current_user
                else {}
            )
            for view in item_views:
                view["preference"] = serialize_preference(preferences.get(view["id"]))
            today_review = _today_review_state(item_views)
            record_product_event(
                session,
                "view_today_queue",
                user_id=current_user.id if current_user else None,
                session_id=_analytics_session_id(request),
                metadata={"total": today_review["total"], "remaining": len(today_review["items"])},
            )
            if today_review["complete"]:
                record_product_event(
                    session,
                    "complete_today_review",
                    user_id=current_user.id if current_user else None,
                    session_id=_analytics_session_id(request),
                    metadata={"total": today_review["total"], "passed": today_review["passed"], "favorited": today_review["favorited"]},
                )
            return templates.TemplateResponse(
                request,
                "auctions/today.html",
                {
                    "current_user": current_user,
                    "settings": get_settings(),
                    "active_section": "onbid",
                    "active_subsection": "today",
                    "active_category": "",
                    "page_title": "오늘 보기",
                    "breadcrumbs": [{"label": "ONBID", "href": "/onbid"}, {"label": "오늘 보기", "href": "/onbid/today"}],
                    "review_mode": get_settings().review_mode,
                    "items": today_review["items"],
                    "today_review": today_review,
                    "base_path": "/onbid",
                },
            )

    @app.get("/auctions/{auction_item_id}")
    def auction_detail_page(request: Request, auction_item_id: int):
        return _render_auction_detail(request, auction_item_id, base_path="/auctions")

    @app.get("/onbid/{auction_item_id}")
    def onbid_detail_page(request: Request, auction_item_id: int):
        return _render_auction_detail(request, auction_item_id, base_path="/onbid")

    def _render_auction_detail(request: Request, auction_item_id: int, *, base_path: str):
        with session_scope() as session:
            current_user = require_user(request, session)
            item = get_auction_item(session, auction_item_id)
            if item is None:
                raise HTTPException(status_code=404, detail="Auction item not found.")
            if base_path == "/onbid" and current_user is None and not is_onbid_item_public_visible(item):
                raise HTTPException(status_code=404, detail="Auction item not found.")
            preference = get_preference(session, current_user.id, auction_item_id) if current_user else None
            same_notice_items = [serialize_auction_item(other) for other in list_same_notice_items(session, item, limit=20)]
            view = serialize_auction_item(item)
            if base_path == "/onbid" and view["supports_development_insight"]:
                record_product_event(
                    session,
                    "view_development_insight_cta",
                    auction_item_id=item.id,
                    user_id=current_user.id if current_user else None,
                    session_id=_analytics_session_id(request),
                    category=view["category"],
                )
            return templates.TemplateResponse(
                request,
                "auctions/detail.html",
                {
                    "current_user": current_user,
                    "settings": get_settings(),
                    "active_section": "onbid",
                    "active_subsection": "",
                    "active_category": view["category"],
                "page_title": item.item_name or "온비드 상세",
                    "breadcrumbs": [
                        {"label": "ONBID", "href": base_path},
                        {"label": item.item_name or str(item.id), "href": ""},
                    ],
                    "review_mode": get_settings().review_mode,
                    "item": item,
                    "view": view,
                    "same_notice_items": same_notice_items,
                    "preference": serialize_preference(preference),
                    "base_path": base_path,
                    "issue_submitted": request.query_params.get("issue_reported") == "1",
                    "share_created": request.query_params.get("share") or "",
                },
            )

    def _redirect_after_preference(next_url: str, auction_item_id: int) -> RedirectResponse:
        target = next_url if next_url.startswith("/") else f"/onbid/{auction_item_id}"
        return RedirectResponse(url=target, status_code=303)

    def _save_preference(
        request: Request,
        auction_item_id: int,
        *,
        favorite: bool | None,
        passed: bool | None,
        watching: bool | None,
        note: str | None,
        tags: str | None,
        next_url: str,
    ):
        with session_scope() as session:
            if get_settings().review_mode:
                raise HTTPException(status_code=403, detail="Review mode disables mutations.")
            current_user = require_user(request, session)
            if current_user is None:
                return login_redirect(next_url if next_url.startswith("/") else f"/onbid/{auction_item_id}")
            item = get_auction_item(session, auction_item_id)
            if item is None:
                raise HTTPException(status_code=404, detail="Auction item not found.")
            preference = update_preference(
                session,
                current_user.id,
                auction_item_id,
                favorite=favorite,
                passed=passed,
                watching=watching,
                note=note,
                tags=tags,
            )
            create_audit_log(
                session,
                current_user.id,
                "USER_AUCTION_PREFERENCE_SAVED",
                "auction_item",
                auction_item_id,
                "User saved ONBID preference",
                {"favorite": favorite, "passed": passed, "watching": watching},
            )
            event_name = None
            if favorite is True:
                event_name = "favorite_item"
            elif passed is True:
                event_name = "pass_item"
            elif passed is False:
                event_name = "undo_pass_item"
            elif watching is True:
                event_name = "watch_item"
            elif note is not None:
                event_name = "write_memo"
            if event_name:
                record_product_event(
                    session,
                    event_name,
                    auction_item_id=auction_item_id,
                    user_id=current_user.id,
                    session_id=_analytics_session_id(request),
                    category=serialize_auction_item(item)["category"],
                    metadata={
                        "favorite": preference.is_favorite,
                        "passed": preference.is_passed,
                        "watching": preference.is_watching,
                    },
                )
        return _redirect_after_preference(next_url, auction_item_id)

    @app.post("/onbid/{auction_item_id}/preference")
    def save_onbid_preference(
        request: Request,
        auction_item_id: int,
        action: str = Form("favorite"),
        enabled: bool = Form(True),
        note: str = Form(""),
        tags: str = Form(""),
        next_url: str = Form(""),
    ):
        return _save_preference(
            request,
            auction_item_id,
            favorite=enabled if action == "favorite" else None,
            passed=enabled if action == "passed" else None,
            watching=enabled if action == "watching" else None,
            note=note if action == "note" else None,
            tags=tags if action == "note" else None,
            next_url=next_url or f"/onbid/{auction_item_id}",
        )

    @app.post("/api/onbid/{auction_item_id}/preference")
    def save_onbid_preference_api(request: Request, auction_item_id: int, payload: dict = Body(...)):
        with session_scope() as session:
            if get_settings().review_mode:
                raise HTTPException(status_code=403, detail="Review mode disables mutations.")
            current_user = require_user(request, session)
            if current_user is None:
                raise HTTPException(status_code=401, detail="Login required.")
            item = get_auction_item(session, auction_item_id)
            if item is None:
                raise HTTPException(status_code=404, detail="Auction item not found.")
            preference = update_preference(
                session,
                current_user.id,
                auction_item_id,
                favorite=payload.get("favorite"),
                passed=payload.get("passed"),
                watching=payload.get("watching"),
                note=payload.get("note") if "note" in payload else None,
                tags=payload.get("tags") if "tags" in payload else None,
            )
            event_name = None
            if payload.get("favorite") is True:
                event_name = "favorite_item"
            elif payload.get("passed") is True:
                event_name = "pass_item"
            elif payload.get("passed") is False:
                event_name = "undo_pass_item"
            elif payload.get("watching") is True:
                event_name = "watch_item"
            elif "note" in payload:
                event_name = "write_memo"
            if event_name:
                record_product_event(
                    session,
                    event_name,
                    auction_item_id=auction_item_id,
                    user_id=current_user.id,
                    session_id=_analytics_session_id(request),
                    category=serialize_auction_item(item)["category"],
                    metadata={
                        "favorite": preference.is_favorite,
                        "passed": preference.is_passed,
                        "watching": preference.is_watching,
                    },
                )
            return {"status": "saved", "preference": serialize_preference(preference)}

    @app.get("/onbid/{auction_item_id}/original-link")
    def open_onbid_original_link(request: Request, auction_item_id: int):
        with session_scope() as session:
            current_user = require_user(request, session)
            item = get_auction_item(session, auction_item_id)
            if item is None or not is_onbid_item_public_visible(item):
                raise HTTPException(status_code=404, detail="Auction item not found.")
            view = serialize_auction_item(item)
            if not view["external_url"]:
                raise HTTPException(status_code=404, detail="Original link not available.")
            record_product_event(
                session,
                "click_original_link",
                auction_item_id=auction_item_id,
                user_id=current_user.id if current_user else None,
                session_id=_analytics_session_id(request),
                category=view["category"],
            )
            return RedirectResponse(url=view["external_url"], status_code=303)

    @app.post("/onbid/{auction_item_id}/issue-report")
    def submit_onbid_issue_report(
        request: Request,
        auction_item_id: int,
        issue_type: list[str] = Form([]),
        note: str = Form(""),
        next_url: str = Form(""),
    ):
        with session_scope() as session:
            current_user = require_user(request, session)
            item = get_auction_item(session, auction_item_id)
            if item is None or not is_onbid_item_public_visible(item):
                raise HTTPException(status_code=404, detail="Auction item not found.")
            create_data_issue_report(
                session,
                auction_item_id=auction_item_id,
                user_id=current_user.id if current_user else None,
                session_id=_analytics_session_id(request),
                issue_types=issue_type,
                note=note,
            )
            create_audit_log(
                session,
                current_user.id if current_user else None,
                "ONBID_DATA_ISSUE_REPORTED",
                "auction_item",
                auction_item_id,
                "ONBID data issue report submitted",
                {"issue_type_count": len(issue_type)},
            )
        target = next_url if next_url.startswith("/") else f"/onbid/{auction_item_id}"
        sep = "&" if "?" in target else "?"
        return RedirectResponse(url=f"{target}{sep}issue_reported=1", status_code=303)

    @app.post("/onbid/{auction_item_id}/review-summary")
    def create_onbid_review_summary(
        request: Request,
        auction_item_id: int,
        public_note: str = Form(""),
    ):
        with session_scope() as session:
            current_user = require_user(request, session)
            if current_user is None:
                return login_redirect(f"/onbid/{auction_item_id}")
            item = get_auction_item(session, auction_item_id)
            if item is None or not is_onbid_item_public_visible(item):
                raise HTTPException(status_code=404, detail="Auction item not found.")
            share = create_review_summary_share(
                session,
                item=item,
                user_id=current_user.id,
                session_id=_analytics_session_id(request),
                public_note=public_note,
            )
            token = share.token
        return RedirectResponse(url=f"/onbid/{auction_item_id}?share={token}", status_code=303)

    @app.get("/onbid/share/{token}")
    def read_onbid_review_summary(request: Request, token: str):
        with session_scope() as session:
            current_user = require_user(request, session)
            share = get_review_summary_share(session, token)
            if share is None:
                raise HTTPException(status_code=404, detail="Shared summary not found.")
            item = get_auction_item(session, share.auction_item_id)
            if item is None or not is_onbid_item_public_visible(item):
                raise HTTPException(status_code=404, detail="Shared summary not found.")
            payload = parse_share_summary(share)
            record_product_event(
                session,
                "open_shared_summary",
                auction_item_id=item.id,
                user_id=current_user.id if current_user else None,
                session_id=_analytics_session_id(request),
                category=serialize_auction_item(item)["category"],
            )
            response = templates.TemplateResponse(
                request,
                "auctions/shared_summary.html",
                {
                    "current_user": current_user,
                    "settings": get_settings(),
                    "active_section": "onbid",
                    "active_subsection": "share",
                    "active_category": "",
                    "breadcrumbs": [{"label": "ONBID", "href": "/onbid"}, {"label": "검색 공유 요약", "href": ""}],
                    "review_mode": get_settings().review_mode,
                    "share": share,
                    "summary": payload,
                    "view": serialize_auction_item(item),
                },
            )
            response.headers["X-Robots-Tag"] = "noindex, noarchive"
            return response

    @app.post("/onbid/share/{token}/copy")
    def copy_onbid_review_summary_link(request: Request, token: str):
        with session_scope() as session:
            current_user = require_user(request, session)
            share = get_review_summary_share(session, token)
            if share is None:
                raise HTTPException(status_code=404, detail="Shared summary not found.")
            record_product_event(
                session,
                "copy_shared_summary_link",
                auction_item_id=share.auction_item_id,
                user_id=current_user.id if current_user else None,
                session_id=_analytics_session_id(request),
            )
        return RedirectResponse(url=f"/onbid/share/{token}", status_code=303)

    @app.post("/onbid/{auction_item_id}/development-insight")
    def click_development_insight(request: Request, auction_item_id: int):
        with session_scope() as session:
            current_user = require_user(request, session)
            item = get_auction_item(session, auction_item_id)
            if item is None or not is_onbid_item_public_visible(item):
                raise HTTPException(status_code=404, detail="Auction item not found.")
            view = serialize_auction_item(item)
            if not view["supports_development_insight"]:
                raise HTTPException(status_code=404, detail="Development insight is not available.")
            record_product_event(
                session,
                "click_development_insight_cta",
                auction_item_id=auction_item_id,
                user_id=current_user.id if current_user else None,
                session_id=_analytics_session_id(request),
                category=view["category"],
            )
        return RedirectResponse(url=f"/onbid/{auction_item_id}/development-insight", status_code=303)

    @app.get("/onbid/{auction_item_id}/development-insight")
    def development_insight_page(request: Request, auction_item_id: int):
        with session_scope() as session:
            current_user = require_user(request, session)
            item = get_auction_item(session, auction_item_id)
            if item is None or not is_onbid_item_public_visible(item):
                raise HTTPException(status_code=404, detail="Auction item not found.")
            view = serialize_auction_item(item)
            if not view["supports_development_insight"]:
                raise HTTPException(status_code=404, detail="Development insight is not available.")
            return templates.TemplateResponse(
                request,
                "auctions/development_insight.html",
                {
                    "current_user": current_user,
                    "settings": get_settings(),
                    "active_section": "onbid",
                    "active_subsection": "development_insight",
                    "active_category": view["category"],
                    "breadcrumbs": [{"label": "ONBID", "href": "/onbid"}, {"label": view["item_name"], "href": f"/onbid/{auction_item_id}"}, {"label": "개발 가능성 기초 검토", "href": ""}],
                    "review_mode": get_settings().review_mode,
                    "view": view,
                },
            )

    def _render_my_onbid(request: Request, preference_type: str, title: str, description: str):
        with session_scope() as session:
            current_user = require_user(request, session)
            if current_user is None:
                return login_redirect("/my/onbid/favorites")
            items = list_preference_items(session, current_user.id, preference_type)
            preferences = get_preference_map(session, current_user.id, [item.id for item in items])
            views = [serialize_auction_item(item) for item in items]
            for view in views:
                view["preference"] = serialize_preference(preferences.get(view["id"]))
            return templates.TemplateResponse(
                request,
                "auctions/my_list.html",
                {
                    "current_user": current_user,
                    "settings": get_settings(),
                    "active_section": "my",
                    "active_subsection": preference_type,
                    "active_category": "",
                    "page_title": title,
                    "breadcrumbs": [{"label": "My ONBID", "href": "/my/onbid/favorites"}],
                    "review_mode": get_settings().review_mode,
                    "items": views,
                    "preference_type": preference_type,
                    "title": title,
                    "description": description,
                },
            )

    @app.get("/my")
    def my_dashboard(request: Request) -> RedirectResponse:
        return RedirectResponse(url="/my/onbid/favorites", status_code=303)

    @app.get("/my/onbid/favorites")
    def my_onbid_favorites(request: Request):
        return _render_my_onbid(request, "favorites", "관심 온비드", "다시 검토할 온비드 공매 물건입니다.")

    @app.get("/my/onbid/passed")
    def my_onbid_passed(request: Request):
        return _render_my_onbid(request, "passed", "패스한 온비드", "목록에서 제외한 온비드 공매 물건입니다.")

    @app.get("/my/onbid/watching")
    def my_onbid_watching(request: Request):
        return _render_my_onbid(request, "watching", "감시 중인 온비드", "입찰 일정과 상태를 추적할 온비드 공매 물건입니다.")

    @app.get("/my/onbid/notes")
    def my_onbid_notes(request: Request):
        return _render_my_onbid(request, "notes", "메모 있는 물건", "검토 이유를 남긴 온비드 공매 물건입니다.")

    @app.post("/api/admin/auctions/onbid/sync")
    def sync_onbid_auctions_api(
        request: Request,
        sample: bool = Query(True),
        limit: int = Query(20, ge=1, le=20),
        max_pages: int = Query(1, ge=1, le=1),
        api_kind: str = Query("real_estate", pattern="^(real_estate|movable|all|notice|national_property)$"),
        include_details: bool = Query(False),
        include_notice_details: bool = Query(False),
        include_notice_items: bool = Query(False),
        min_date: str = Query("2025-01-01"),
    ) -> dict:
        with session_scope() as session:
            current_user = require_admin(request, session)
            if current_user is None:
                raise admin_login_required()
            if get_settings().review_mode:
                raise HTTPException(status_code=403, detail="Review mode disables admin mutations.")
        if not sample:
            if limit > 20 or max_pages > 1 or min_date != "2025-01-01":
                raise HTTPException(status_code=422, detail="Real ONBID calls require Limit=20, MaxPages=1, MinDate=2025-01-01.")
        result = run_onbid_sync(
            limit=limit,
            sample=sample,
            api_kind=api_kind,
            max_pages=max_pages,
            include_details=include_details,
            include_notice_details=include_notice_details,
            include_notice_items=include_notice_items,
            min_date=min_date,
        )
        with session_scope() as session:
            current_user = require_admin(request, session)
            create_audit_log(
                session,
                current_user.id if current_user else None,
                "ADMIN_ONBID_SYNC_REQUESTED",
                "auction_item",
                "ONBID",
                "Admin requested ONBID auction sync",
                result,
            )
        if result.get("status") != "SUCCEEDED":
            raise HTTPException(status_code=502, detail=result.get("error", "ONBID sync failed."))
        return result

    @app.post("/api/admin/auctions/{auction_item_id}/links")
    def create_auction_case_link_api(request: Request, auction_item_id: int, payload: dict = Body(...)) -> dict:
        with session_scope() as session:
            current_user = require_admin(request, session)
            if current_user is None:
                raise admin_login_required()
            case_id = int(payload.get("case_id") or 0)
            if not case_id:
                raise HTTPException(status_code=422, detail="case_id is required.")
            if get_event_with_details(session, case_id) is None:
                raise HTTPException(status_code=404, detail="Recovery case not found.")
            if get_auction_item(session, auction_item_id) is None:
                raise HTTPException(status_code=404, detail="Auction item not found.")
            link = create_case_auction_link(
                session,
                case_id=case_id,
                auction_item_id=auction_item_id,
                link_status=str(payload.get("link_status") or "confirmed"),
                match_type=str(payload.get("match_type") or "manual"),
                match_score=float(payload.get("match_score") or 100),
                memo=str(payload.get("memo") or ""),
                assigned_user_id=current_user.id,
            )
            create_audit_log(
                session,
                current_user.id,
                "ADMIN_AUCTION_CASE_LINK_CREATED",
                "case_auction_link",
                link.id,
                "Admin linked auction item to case",
                {"case_id": case_id, "auction_item_id": auction_item_id, "status": link.link_status},
            )
            return {"status": "linked", "link_id": link.id}

    @app.get("/api/admin/auctions/{auction_item_id}/link-candidates")
    def read_auction_link_candidates_api(
        request: Request,
        auction_item_id: int,
        limit: int = Query(20, ge=1, le=100),
    ) -> dict:
        with session_scope() as session:
            if require_admin(request, session) is None:
                raise admin_login_required()
            if get_auction_item(session, auction_item_id) is None:
                raise HTTPException(status_code=404, detail="Auction item not found.")
            return {"candidates": find_link_candidates_for_auction(session, auction_item_id, limit=limit)}

    @app.get("/api/cases/{case_id}/auction-link-candidates")
    def read_case_auction_candidates_api(
        request: Request,
        case_id: int,
        limit: int = Query(20, ge=1, le=100),
    ) -> dict:
        with session_scope() as session:
            if require_admin(request, session) is None:
                raise admin_login_required()
            if get_event_with_details(session, case_id) is None:
                raise HTTPException(status_code=404, detail="Recovery case not found.")
            return {"candidates": find_auction_candidates_for_case(session, case_id, limit=limit)}
