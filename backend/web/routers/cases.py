from __future__ import annotations

from collections import Counter
from math import ceil

from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from backend.database.crud import count_user_events, list_user_events_page
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
            current_user = require_user(request, session)
            if current_user is None:
                return login_redirect("/user")
            mark_event_passed(session, current_user.id, event_id)
            create_audit_log(session, current_user.id, "USER_EVENT_PASSED", "asset_event", event_id, "User passed event")
        return RedirectResponse(url="/user", status_code=303)

    @app.post("/user/events/{event_id}/unpass")
    def unpass_user_event_route(request: Request, event_id: int) -> RedirectResponse:
        with session_scope() as session:
            current_user = require_user(request, session)
            if current_user is None:
                return login_redirect("/user/passed")
            unpass_event(session, current_user.id, event_id)
            create_audit_log(session, current_user.id, "USER_EVENT_UNPASSED", "asset_event", event_id, "User restored passed event")
        return RedirectResponse(url="/user/passed", status_code=303)

    @app.post("/user/events/{event_id}/bookmark")
    def bookmark_user_event(request: Request, event_id: int) -> RedirectResponse:
        with session_scope() as session:
            current_user = require_user(request, session)
            if current_user is None:
                return login_redirect("/user")
            mark_event_action(session, current_user.id, event_id, ACTION_BOOKMARKED)
            create_audit_log(session, current_user.id, "USER_EVENT_BOOKMARKED", "asset_event", event_id, "User bookmarked event")
        return RedirectResponse(url="/user/bookmarks", status_code=303)

    @app.post("/user/events/{event_id}/unbookmark")
    def unbookmark_user_event(request: Request, event_id: int) -> RedirectResponse:
        with session_scope() as session:
            current_user = require_user(request, session)
            if current_user is None:
                return login_redirect("/user/bookmarks")
            clear_event_action(session, current_user.id, event_id, ACTION_BOOKMARKED)
            create_audit_log(session, current_user.id, "USER_EVENT_UNBOOKMARKED", "asset_event", event_id, "User removed bookmark")
        return RedirectResponse(url="/user/bookmarks", status_code=303)

    @app.post("/user/events/{event_id}/watch")
    def watch_user_event(request: Request, event_id: int) -> RedirectResponse:
        with session_scope() as session:
            current_user = require_user(request, session)
            if current_user is None:
                return login_redirect("/user")
            mark_event_action(session, current_user.id, event_id, ACTION_WATCHING)
            create_audit_log(session, current_user.id, "USER_EVENT_WATCHING", "asset_event", event_id, "User started watching event")
        return RedirectResponse(url="/user/watching", status_code=303)

    @app.post("/user/events/{event_id}/unwatch")
    def unwatch_user_event(request: Request, event_id: int) -> RedirectResponse:
        with session_scope() as session:
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
