from __future__ import annotations

from math import ceil
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
    list_auction_items,
    serialize_auction_item,
)
from backend.services.audit_logs import create_audit_log
from backend.services.user_auction_preferences import (
    get_preference,
    get_preference_map,
    list_preference_items,
    serialize_preference,
    update_preference,
)
from backend.web.dependencies import LoginRedirect, RequireAdmin, RequireUser, admin_login_required
from backend.workers.onbid_sync import run_onbid_sync


def register_auction_routes(
    app: FastAPI,
    templates: Jinja2Templates,
    *,
    require_user: RequireUser,
    require_admin: RequireAdmin,
    login_redirect: LoginRedirect,
) -> None:
    def _read_price(value: int | None) -> int | None:
        return value if value and value > 0 else None

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
        sort: str,
        base_path: str,
    ):
        per_page = 20
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
                price_min=_read_price(price_min),
                price_max=_read_price(price_max),
                closing_within_days=closing_within_days,
                min_discount_rate=min_discount_rate,
                has_notice=has_notice,
                has_detail=has_detail,
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
                price_min=_read_price(price_min),
                price_max=_read_price(price_max),
                closing_within_days=closing_within_days,
                min_discount_rate=min_discount_rate,
                has_notice=has_notice,
                has_detail=has_detail,
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
            return templates.TemplateResponse(
                request,
                "auctions/index.html",
                {
                    "current_user": current_user,
                    "settings": get_settings(),
                    "items": item_views,
                    "base_path": base_path,
                    "filters": {
                        "status": status,
                        "asset_type": asset_type,
                        "keyword": keyword,
                        "linked": linked,
                        "region": region,
                        "usage": usage,
                        "agency": agency,
                        "price_min": price_min or "",
                        "price_max": price_max or "",
                        "closing_within_days": closing_within_days or "",
                        "min_discount_rate": min_discount_rate or "",
                        "has_notice": has_notice,
                        "has_detail": has_detail,
                        "sort": sort,
                    },
                    "pagination": {
                        "page": current_page,
                        "pages": list(range(1, total_pages + 1)),
                        "has_prev": current_page > 1,
                        "has_next": current_page < total_pages,
                        "prev_page": max(1, current_page - 1),
                        "next_page": min(total_pages, current_page + 1),
                    },
                    "total_count": total_count,
                },
            )

    @app.get("/auctions")
    def auction_list_page(
        request: Request,
        page: int = Query(1, ge=1),
        status: str = Query("ALL"),
        asset_type: str = Query("ALL"),
        keyword: str = Query(""),
        q: str = Query(""),
        linked: str = Query("ALL"),
        region: str = Query(""),
        usage: str = Query(""),
        agency: str = Query(""),
        price_min: int | None = Query(None, ge=0),
        price_max: int | None = Query(None, ge=0),
        closing_within_days: int | None = Query(None, ge=0, le=365),
        min_discount_rate: float | None = Query(None, ge=0, le=100),
        has_notice: str = Query("ALL"),
        has_detail: str = Query("ALL"),
        sort: str = Query("closing_soon"),
    ):
        return _render_auction_list(
            request,
            page=page,
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
            sort=sort,
            base_path="/auctions",
        )

    @app.get("/onbid")
    def onbid_list_page(
        request: Request,
        page: int = Query(1, ge=1),
        status: str = Query("ALL"),
        asset_type: str = Query("ALL"),
        q: str = Query(""),
        keyword: str = Query(""),
        linked: str = Query("ALL"),
        region: str = Query(""),
        usage: str = Query(""),
        agency: str = Query(""),
        price_min: int | None = Query(None, ge=0),
        price_max: int | None = Query(None, ge=0),
        closing_within_days: int | None = Query(None, ge=0, le=365),
        min_discount_rate: float | None = Query(None, ge=0, le=100),
        has_notice: str = Query("ALL"),
        has_detail: str = Query("ALL"),
        sort: str = Query("closing_soon"),
    ):
        return _render_auction_list(
            request,
            page=page,
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
            sort=sort,
            base_path="/onbid",
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
            preference = get_preference(session, current_user.id, auction_item_id) if current_user else None
            return templates.TemplateResponse(
                request,
                "auctions/detail.html",
                {
                    "current_user": current_user,
                    "settings": get_settings(),
                    "item": item,
                    "view": serialize_auction_item(item),
                    "preference": serialize_preference(preference),
                    "base_path": base_path,
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
            current_user = require_user(request, session)
            if current_user is None:
                return login_redirect(next_url if next_url.startswith("/") else f"/onbid/{auction_item_id}")
            if get_auction_item(session, auction_item_id) is None:
                raise HTTPException(status_code=404, detail="Auction item not found.")
            update_preference(
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
            current_user = require_user(request, session)
            if current_user is None:
                raise HTTPException(status_code=401, detail="Login required.")
            if get_auction_item(session, auction_item_id) is None:
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
            return {"status": "saved", "preference": serialize_preference(preference)}

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

    @app.post("/api/admin/auctions/onbid/sync")
    def sync_onbid_auctions_api(
        request: Request,
        sample: bool = Query(True),
        limit: int = Query(20, ge=1, le=100),
        api_kind: str = Query("real_estate", pattern="^(real_estate|movable|all|notice)$"),
        include_details: bool = Query(False),
        include_notice_details: bool = Query(False),
        include_notice_items: bool = Query(False),
    ) -> dict:
        with session_scope() as session:
            current_user = require_admin(request, session)
            if current_user is None:
                raise admin_login_required()
        result = run_onbid_sync(
            limit=limit,
            sample=sample,
            api_kind=api_kind,
            include_details=include_details,
            include_notice_details=include_notice_details,
            include_notice_items=include_notice_items,
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
