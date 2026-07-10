from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from math import ceil

from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from backend.config import get_settings
from backend.database.crud import count_user_events, get_event_with_details, list_user_events_page
from backend.database.session import session_scope
from backend.jobs.event_repository import list_job_events
from backend.jobs.readiness import get_analysis_readiness
from backend.jobs.repository import get_latest_job_for_event, get_latest_ocr_job_for_event
from backend.services.audit_logs import create_audit_log
from backend.services.user_event_actions import (
    ACTION_BOOKMARKED,
    ACTION_WATCHING,
    clear_event_action,
    list_action_events,
    list_passed_events,
    mark_event_action,
    mark_event_passed,
    unpass_event,
)
from backend.services.user_event_notes import upsert_user_event_note
from backend.web.dependencies import (
    AttachAnalysisResults,
    AttachEvents,
    AttachUserNotes,
    BuildEventPayload,
    LoginRedirect,
    RequireUser,
)
from backend.web.pagination import build_pagination, build_query_href


def register_case_routes(
    app: FastAPI,
    templates: Jinja2Templates,
    *,
    require_user: RequireUser,
    login_redirect: LoginRedirect,
    attach_view_metadata: AttachEvents,
    attach_analysis_result_metadata: AttachAnalysisResults,
    attach_user_note_metadata: AttachUserNotes,
    build_event_payload: BuildEventPayload,
) -> None:
    def _read_int(value, *, minimum: int = 0, maximum: int | None = None) -> int | None:
        if value in (None, ""):
            return None
        try:
            parsed = int(str(value).strip())
        except (TypeError, ValueError):
            return None
        if parsed < minimum:
            return None
        if maximum is not None and parsed > maximum:
            return maximum
        return parsed

    def _safe_external_url(value: str) -> str:
        text = str(value or "").strip()
        return text if text.startswith(("http://", "https://")) else ""

    def _date_d_day(value: str) -> dict:
        text = str(value or "").strip()
        if not text or text == "UNKNOWN":
            return {"label": "미정", "state": "unknown"}
        try:
            delta = (datetime.strptime(text[:10], "%Y-%m-%d").date() - date.today()).days
        except ValueError:
            return {"label": "미정", "state": "unknown"}
        if delta == 0:
            return {"label": "D-Day", "state": "urgent"}
        if delta < 0:
            return {"label": f"D+{abs(delta)}", "state": "closed"}
        return {"label": f"D-{delta}", "state": "urgent" if delta <= 7 else "normal"}

    def _public_case_view(event) -> dict:
        evidence = event.raw_document.evidence if event.raw_document else None
        description = ""
        if evidence and evidence.source_title:
            description = evidence.source_title
        elif event.title:
            description = event.title
        return {
            "id": event.id,
            "case_number": event.case_number,
            "title": event.title,
            "status": event.status,
            "parse_status": event.parse_status,
            "notice_date": event.notice_date,
            "expire_date": event.expire_date,
            "d_day": _date_d_day(event.expire_date),
            "main_category": event.asset.main_category,
            "sub_category": event.asset.sub_category,
            "address": event.asset.address,
            "description": description,
            "external_url": _safe_external_url(event.url or (event.raw_document.source_url if event.raw_document else "")),
            "attachment_name": evidence.attachment_name if evidence else "",
            "has_login_analysis": bool(event.analyses),
        }

    @app.get("/cases")
    def public_case_list(
        request: Request,
        page: str = Query("1"),
        q: str = Query(""),
        category: str = Query("ALL"),
        region: str = Query(""),
        status: str = Query(""),
        notice_date_from: str = Query(""),
        expire_date_to: str = Query(""),
    ):
        per_page = 20
        with session_scope() as session:
            current_user = require_user(request, session)
            total_count = count_user_events(session)
            total_pages = max(1, ceil(total_count / per_page))
            current_page = min(_read_int(page, minimum=1) or 1, total_pages)
            events = list_user_events_page(session, limit=per_page, offset=(current_page - 1) * per_page)
            views = [_public_case_view(event) for event in events]
            if q:
                views = [
                    view for view in views
                    if q in view["title"] or q in view["case_number"] or q in view["address"]
                ]
            if category != "ALL":
                views = [view for view in views if view["main_category"] == category]
            if region:
                views = [view for view in views if region in view["address"]]
            if status:
                views = [view for view in views if status in view["status"]]
            if notice_date_from:
                views = [view for view in views if view["notice_date"] >= notice_date_from]
            if expire_date_to:
                views = [view for view in views if view["expire_date"] <= expire_date_to]
            filters = {
                "q": q,
                "category": category,
                "region": region,
                "status": status,
                "notice_date_from": notice_date_from,
                "expire_date_to": expire_date_to,
            }
            return templates.TemplateResponse(
                request,
                "cases/index.html",
                {
                    "current_user": current_user,
                    "settings": get_settings(),
                    "active_section": "cases",
                    "active_subsection": "",
                    "active_category": filters.get("category", "ALL"),
                    "page_title": "회생·파산 공고",
                    "breadcrumbs": [{"label": "회생·파산", "href": "/cases"}],
                    "review_mode": get_settings().review_mode,
                    "cases": views,
                    "filters": filters,
                    "pagination": build_pagination(
                        "/cases",
                        current_page=current_page,
                        total_pages=total_pages,
                        query_state=filters,
                    ),
                    "total_count": total_count,
                },
            )

    @app.get("/cases/{event_id}")
    def public_case_detail(request: Request, event_id: int):
        with session_scope() as session:
            current_user = require_user(request, session)
            event = get_event_with_details(session, event_id)
            if event is None:
                raise HTTPException(status_code=404, detail="Case not found.")
            return templates.TemplateResponse(
                request,
                "cases/detail.html",
                {
                    "current_user": current_user,
                    "settings": get_settings(),
                    "active_section": "cases",
                    "active_subsection": "",
                    "active_category": "",
                    "page_title": event.title or "사건 상세",
                    "breadcrumbs": [
                        {"label": "회생·파산", "href": "/cases"},
                        {"label": event.case_number, "href": ""},
                    ],
                    "review_mode": get_settings().review_mode,
                    "case": _public_case_view(event),
                },
            )

    def prepare_user_events(session, events, user_id: int, *, include_job_events: bool) -> None:
        attach_view_metadata(events)
        attach_analysis_result_metadata(session, events)
        attach_user_note_metadata(session, events, user_id)
        for event in events:
            event.latest_deep_job = get_latest_job_for_event(session, event.id)
            event.latest_ocr_job = get_latest_ocr_job_for_event(session, event.id)
            event.latest_deep_job_events = (
                list_job_events(session, event.latest_deep_job.id, limit=8)
                if include_job_events and event.latest_deep_job
                else []
            )
            event.analysis_readiness = get_analysis_readiness(event)

    @app.get("/user")
    def user_dashboard(request: Request, page: int = Query(1, ge=1)):
        per_page = 5
        with session_scope() as session:
            current_user = require_user(request, session)
            if current_user is None:
                return login_redirect("/user")
            total_count = count_user_events(session, user_id=current_user.id)
            total_pages = max(1, ceil(total_count / per_page))
            current_page = min(page, total_pages)
            events = list_user_events_page(
                session,
                limit=per_page,
                offset=(current_page - 1) * per_page,
                user_id=current_user.id,
            )
            prepare_user_events(session, events, current_user.id, include_job_events=True)
            category_counts = Counter(event.asset.main_category for event in events)
            event_payload = [build_event_payload(event) for event in events]
            return templates.TemplateResponse(
                request,
                "user/index.html",
                {
                    "events": events,
                    "active_section": "my",
                    "active_subsection": "",
                    "active_category": "",
                    "page_title": "내 대시보드",
                    "breadcrumbs": [{"label": "My", "href": "/user"}],
                    "review_mode": get_settings().review_mode,
                    "event_payload": event_payload,
                    "total_count": total_count,
                    "current_user": current_user,
                    "category_counts": dict(category_counts),
                    "pagination": {
                        "page": current_page,
                        "per_page": per_page,
                        "total_pages": total_pages,
                        "has_prev": current_page > 1,
                        "has_next": current_page < total_pages,
                        "prev_page": current_page - 1,
                        "next_page": current_page + 1,
                        "pages": list(range(1, total_pages + 1)),
                    },
                },
            )

    @app.get("/user/passed")
    def user_passed_events(request: Request):
        with session_scope() as session:
            current_user = require_user(request, session)
            if current_user is None:
                return login_redirect("/user/passed")
            events = list_passed_events(session, current_user.id)
            prepare_user_events(session, events, current_user.id, include_job_events=False)
            return templates.TemplateResponse(
                request,
                "user/passed.html",
                {
                    "events": events,
                    "active_section": "my",
                    "active_subsection": "passed",
                    "active_category": "",
                    "page_title": "패스한 사건",
                    "breadcrumbs": [{"label": "My", "href": "/user"}],
                    "review_mode": get_settings().review_mode,
                    "current_user": current_user,
                },
            )

    def render_user_action_events(request: Request, action_type: str, title: str, description: str, return_url: str):
        with session_scope() as session:
            current_user = require_user(request, session)
            if current_user is None:
                return login_redirect(return_url)
            events = list_action_events(session, current_user.id, action_type)
            prepare_user_events(session, events, current_user.id, include_job_events=False)
            return templates.TemplateResponse(
                request,
                "user/action_list.html",
                {
                    "events": events,
                    "active_section": "my",
                    "active_subsection": action_type,
                    "active_category": "",
                    "page_title": title,
                    "breadcrumbs": [{"label": "My", "href": "/user"}],
                    "review_mode": get_settings().review_mode,
                    "current_user": current_user,
                    "title": title,
                    "description": description,
                    "action_type": action_type,
                    "return_url": return_url,
                },
            )

    @app.get("/user/bookmarks")
    def user_bookmarked_events(request: Request):
        return render_user_action_events(
            request,
            ACTION_BOOKMARKED,
            "관심 물건",
            "다시 검토하거나 비교하고 싶은 물건을 모아둔 목록입니다.",
            "/user/bookmarks",
        )

    @app.get("/user/my")
    def user_my_items(request: Request) -> RedirectResponse:
        return RedirectResponse(url="/user/bookmarks", status_code=303)

    @app.get("/user/watching")
    def user_watching_events(request: Request):
        return render_user_action_events(
            request,
            ACTION_WATCHING,
            "지켜보는 물건",
            "입찰일, 상세 분석, 추가 검토가 필요한 물건을 추적합니다.",
            "/user/watching",
        )

    @app.get("/user/watchlist")
    def user_watchlist_alias(request: Request) -> RedirectResponse:
        return RedirectResponse(url="/user/watching", status_code=303)

    @app.post("/user/events/{event_id}/pass")
    def pass_user_event(request: Request, event_id: int) -> RedirectResponse:
        with session_scope() as session:
            if get_settings().review_mode:
                raise HTTPException(status_code=403, detail="Review mode disables mutations.")
            current_user = require_user(request, session)
            if current_user is None:
                return login_redirect("/user")
            mark_event_passed(session, current_user.id, event_id)
            create_audit_log(session, current_user.id, "USER_EVENT_PASSED", "asset_event", event_id, "User passed event")
        return RedirectResponse(url="/user", status_code=303)

    @app.post("/user/events/{event_id}/unpass")
    def unpass_user_event_route(request: Request, event_id: int) -> RedirectResponse:
        with session_scope() as session:
            if get_settings().review_mode:
                raise HTTPException(status_code=403, detail="Review mode disables mutations.")
            current_user = require_user(request, session)
            if current_user is None:
                return login_redirect("/user/passed")
            unpass_event(session, current_user.id, event_id)
            create_audit_log(session, current_user.id, "USER_EVENT_UNPASSED", "asset_event", event_id, "User restored passed event")
        return RedirectResponse(url="/user/passed", status_code=303)

    @app.post("/user/events/{event_id}/bookmark")
    def bookmark_user_event(request: Request, event_id: int) -> RedirectResponse:
        with session_scope() as session:
            if get_settings().review_mode:
                raise HTTPException(status_code=403, detail="Review mode disables mutations.")
            current_user = require_user(request, session)
            if current_user is None:
                return login_redirect("/user")
            mark_event_action(session, current_user.id, event_id, ACTION_BOOKMARKED)
            create_audit_log(session, current_user.id, "USER_EVENT_BOOKMARKED", "asset_event", event_id, "User bookmarked event")
        return RedirectResponse(url="/user/bookmarks", status_code=303)

    @app.post("/user/events/{event_id}/unbookmark")
    def unbookmark_user_event(request: Request, event_id: int) -> RedirectResponse:
        with session_scope() as session:
            if get_settings().review_mode:
                raise HTTPException(status_code=403, detail="Review mode disables mutations.")
            current_user = require_user(request, session)
            if current_user is None:
                return login_redirect("/user/bookmarks")
            clear_event_action(session, current_user.id, event_id, ACTION_BOOKMARKED)
            create_audit_log(session, current_user.id, "USER_EVENT_UNBOOKMARKED", "asset_event", event_id, "User removed bookmark")
        return RedirectResponse(url="/user/bookmarks", status_code=303)

    @app.post("/user/events/{event_id}/watch")
    def watch_user_event(request: Request, event_id: int) -> RedirectResponse:
        with session_scope() as session:
            if get_settings().review_mode:
                raise HTTPException(status_code=403, detail="Review mode disables mutations.")
            current_user = require_user(request, session)
            if current_user is None:
                return login_redirect("/user")
            mark_event_action(session, current_user.id, event_id, ACTION_WATCHING)
            create_audit_log(session, current_user.id, "USER_EVENT_WATCHING", "asset_event", event_id, "User started watching event")
        return RedirectResponse(url="/user/watching", status_code=303)

    @app.post("/user/events/{event_id}/unwatch")
    def unwatch_user_event(request: Request, event_id: int) -> RedirectResponse:
        with session_scope() as session:
            if get_settings().review_mode:
                raise HTTPException(status_code=403, detail="Review mode disables mutations.")
            current_user = require_user(request, session)
            if current_user is None:
                return login_redirect("/user/watching")
            clear_event_action(session, current_user.id, event_id, ACTION_WATCHING)
            create_audit_log(session, current_user.id, "USER_EVENT_UNWATCHED", "asset_event", event_id, "User stopped watching event")
        return RedirectResponse(url="/user/watching", status_code=303)

    @app.post("/user/events/{event_id}/note")
    def save_user_event_note(
        request: Request,
        event_id: int,
        note: str = Form(""),
        tags: str = Form(""),
        next_url: str = Form("/user"),
    ) -> RedirectResponse:
        with session_scope() as session:
            if get_settings().review_mode:
                raise HTTPException(status_code=403, detail="Review mode disables mutations.")
            current_user = require_user(request, session)
            if current_user is None:
                return login_redirect("/user")
            upsert_user_event_note(session, current_user.id, event_id, note=note, tags=tags)
            create_audit_log(
                session,
                current_user.id,
                "USER_EVENT_NOTE_SAVED",
                "asset_event",
                event_id,
                "User saved event note",
                {"tags": tags[:128]},
            )
        return RedirectResponse(url=next_url if next_url.startswith("/") else "/user", status_code=303)
