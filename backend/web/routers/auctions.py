from __future__ import annotations

from math import ceil
from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.templating import Jinja2Templates

from backend.database.crud import get_event_with_details
from backend.database.session import session_scope
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
    @app.get("/auctions")
    def auction_list_page(
        request: Request,
        page: int = Query(1, ge=1),
        status: str = Query("ALL"),
        asset_type: str = Query("ALL"),
        keyword: str = Query(""),
        linked: str = Query("ALL"),
    ):
        per_page = 20
        with session_scope() as session:
            current_user = require_user(request, session)
            if current_user is None:
                return login_redirect("/auctions")
            total_count = count_auction_items(
                session,
                status=status,
                asset_type=asset_type,
                keyword=keyword,
                linked=linked,
            )
            total_pages = max(1, ceil(total_count / per_page))
            current_page = min(page, total_pages)
            items = list_auction_items(
                session,
                status=status,
                asset_type=asset_type,
                keyword=keyword,
                linked=linked,
                limit=per_page,
                offset=(current_page - 1) * per_page,
            )
            return templates.TemplateResponse(
                request,
                "auctions/index.html",
                {
                    "current_user": current_user,
                    "items": [serialize_auction_item(item) for item in items],
                    "filters": {
                        "status": status,
                        "asset_type": asset_type,
                        "keyword": keyword,
                        "linked": linked,
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

    @app.get("/auctions/{auction_item_id}")
    def auction_detail_page(request: Request, auction_item_id: int):
        with session_scope() as session:
            current_user = require_user(request, session)
            if current_user is None:
                return login_redirect(f"/auctions/{auction_item_id}")
            item = get_auction_item(session, auction_item_id)
            if item is None:
                raise HTTPException(status_code=404, detail="Auction item not found.")
            return templates.TemplateResponse(
                request,
                "auctions/detail.html",
                {
                    "current_user": current_user,
                    "item": item,
                    "view": serialize_auction_item(item),
                },
            )

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
