from __future__ import annotations

from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from backend.config import get_settings
from backend.database.analysis_results import count_results_by_provider
from backend.database.crud import list_admin_events
from backend.database.session import session_scope
from backend.jobs.event_repository import list_job_events
from backend.jobs.ocr_service import ocr_engine_status
from backend.jobs.repository import count_jobs_by_status, get_latest_job_for_event, get_latest_ocr_job_for_event
from backend.jobs.worker_heartbeat import list_worker_heartbeats
from backend.jobs.readiness import get_analysis_readiness
from backend.runtime_settings import read_runtime_settings, write_analysis_provider
from backend.services.analysis_reviews import (
    build_analysis_review_summary,
    list_recent_analysis_reviews,
)
from backend.services.auction_items import count_auction_items
from backend.services.audit_logs import list_recent_audit_logs
from backend.services.collection_quality import build_collection_quality_summary
from backend.services.crawl_runs import build_crawl_run_summary
from backend.services.local_analysis_status import build_local_analysis_status
from backend.services.metadata_corrections import ALLOWED_PARSE_STATUSES
from backend.services.onbid_observability import build_onbid_observability_summary
from backend.web.dependencies import (
    AdminFilter,
    AttachAnalysisResults,
    AttachEvents,
    LoginRedirect,
    RequireAdmin,
    StaleJobCheck,
    admin_login_required,
)


ADMIN_SECTIONS = {
    "settings": ("운영 설정", "분석 도구, 토글, 로컬 실행 경로를 관리하는 영역입니다."),
}


def register_admin_operation_routes(
    app: FastAPI,
    templates: Jinja2Templates,
    *,
    require_admin: RequireAdmin,
    login_redirect: LoginRedirect,
    attach_view_metadata: AttachEvents,
    attach_analysis_result_metadata: AttachAnalysisResults,
    event_matches_admin_filters: AdminFilter,
    is_stale_job: StaleJobCheck,
) -> None:
    @app.get("/admin")
    def admin_dashboard(
        request: Request,
        job_status: str = Query("ALL"),
        model: str = Query("ALL"),
        parse_status: str = Query("ALL"),
    ):
        with session_scope() as session:
            current_user = require_admin(request, session)
            if current_user is None:
                return login_redirect("/admin")
            events = list_admin_events(session)
            attach_view_metadata(events)
            attach_analysis_result_metadata(session, events)
            for event in events:
                event.latest_deep_job = get_latest_job_for_event(session, event.id)
                event.latest_ocr_job = get_latest_ocr_job_for_event(session, event.id)
                event.latest_deep_job_events = (
                    list_job_events(session, event.latest_deep_job.id, limit=8)
                    if event.latest_deep_job
                    else []
                )
                event.analysis_readiness = get_analysis_readiness(event)
            failed_events = [
                event for event in events
                if getattr(event, "latest_deep_job", None) and event.latest_deep_job.status == "FAILED"
            ]
            stale_events = [
                event for event in events
                if is_stale_job(getattr(event, "latest_deep_job", None))
            ]
            filtered_events = [
                event for event in events
                if event_matches_admin_filters(event, job_status, model, parse_status)
            ]
            runtime = read_runtime_settings()
            settings = get_settings()
            job_counts = count_jobs_by_status(session)
            worker_heartbeats = list_worker_heartbeats(session)
            return templates.TemplateResponse(
                request,
                "admin/dashboard.html",
                {
                    "events": filtered_events,
                    "event_count": len(events),
                    "filtered_count": len(filtered_events),
                    "failed_events": failed_events,
                    "stale_events": stale_events,
                    "job_counts": job_counts,
                    "model_result_counts": count_results_by_provider(session),
                    "local_analysis_status": build_local_analysis_status(job_counts, worker_heartbeats),
                    "collection_quality": build_collection_quality_summary(session),
                    "analysis_review_summary": build_analysis_review_summary(session),
                    "recent_analysis_reviews": list_recent_analysis_reviews(session, limit=12),
                    "recent_audit_logs": list_recent_audit_logs(session, limit=20),
                    "parse_status_options": sorted(ALLOWED_PARSE_STATUSES),
                    "ocr_engine_status": ocr_engine_status(),
                    "current_provider": runtime["analysis_provider"],
                    "chatgpt_ready": bool(settings.chatgpt_api_key or settings.openai_api_key),
                    "current_user": current_user,
                    "filters": {
                        "job_status": job_status,
                        "model": model,
                        "parse_status": parse_status,
                    },
                },
            )

    @app.post("/admin/analysis-provider")
    def update_analysis_provider(request: Request, analysis_provider: str = Form(...)) -> RedirectResponse:
        with session_scope() as session:
            current_user = require_admin(request, session)
            if current_user is None:
                return login_redirect("/admin")
            write_analysis_provider(analysis_provider)
        return RedirectResponse(url="/admin", status_code=303)

    def render_admin_section(request: Request, section_name: str):
        with session_scope() as session:
            current_user = require_admin(request, session)
            if current_user is None:
                return login_redirect(f"/admin/{section_name}")
            section = ADMIN_SECTIONS.get(section_name)
            if section is None:
                raise HTTPException(status_code=404, detail="Admin section not found.")
            return templates.TemplateResponse(
                request,
                "admin/section_placeholder.html",
                {
                    "current_user": current_user,
                    "section_name": section_name,
                    "section_title": section[0],
                    "section_description": section[1],
                },
            )

    @app.get("/admin/assets")
    def admin_assets_page(request: Request):
        with session_scope() as session:
            current_user = require_admin(request, session)
            if current_user is None:
                return login_redirect("/admin/assets")
            events = list_admin_events(session)
            attach_view_metadata(events)
            for event in events:
                event.analysis_readiness = get_analysis_readiness(event)
            return templates.TemplateResponse(
                request,
                "admin/assets.html",
                {
                    "current_user": current_user,
                    "events": events,
                    "collection_quality": build_collection_quality_summary(session),
                    "auction_count": count_auction_items(session),
                },
            )

    @app.get("/admin/analysis")
    def admin_analysis_page(request: Request):
        with session_scope() as session:
            current_user = require_admin(request, session)
            if current_user is None:
                return login_redirect("/admin/analysis")
            events = list_admin_events(session)
            attach_view_metadata(events)
            attach_analysis_result_metadata(session, events)
            for event in events:
                event.latest_deep_job = get_latest_job_for_event(session, event.id)
                event.latest_ocr_job = get_latest_ocr_job_for_event(session, event.id)
                event.analysis_readiness = get_analysis_readiness(event)
            return templates.TemplateResponse(
                request,
                "admin/analysis.html",
                {
                    "current_user": current_user,
                    "events": events,
                    "job_counts": count_jobs_by_status(session),
                    "model_result_counts": count_results_by_provider(session),
                    "analysis_review_summary": build_analysis_review_summary(session),
                },
            )

    @app.get("/admin/collection")
    def admin_collection_page(request: Request):
        with session_scope() as session:
            current_user = require_admin(request, session)
            if current_user is None:
                return login_redirect("/admin/collection")
            return templates.TemplateResponse(
                request,
                "admin/collection.html",
                {
                    "current_user": current_user,
                    "collection_quality": build_collection_quality_summary(session),
                    "crawl_summary": build_crawl_run_summary(session),
                    "onbid_metrics": build_onbid_observability_summary(session),
                },
            )

    @app.get("/admin/settings")
    def admin_settings_page(request: Request):
        return render_admin_section(request, "settings")

    @app.get("/admin/reviews")
    def admin_reviews_page(request: Request):
        with session_scope() as session:
            current_user = require_admin(request, session)
            if current_user is None:
                return login_redirect("/admin/reviews")
            return templates.TemplateResponse(
                request,
                "admin/reviews.html",
                {
                    "current_user": current_user,
                    "analysis_review_summary": build_analysis_review_summary(session),
                    "recent_reviews": list_recent_analysis_reviews(session, limit=30),
                    "recent_audit_logs": list_recent_audit_logs(session, limit=30),
                },
            )

    @app.get("/api/admin/collection-quality")
    def read_collection_quality(request: Request) -> dict:
        with session_scope() as session:
            if require_admin(request, session) is None:
                raise admin_login_required()
            return build_collection_quality_summary(session)

    @app.get("/api/admin/onbid-quality")
    def read_onbid_quality(request: Request, days: int = Query(7, ge=1, le=90)) -> dict:
        with session_scope() as session:
            if require_admin(request, session) is None:
                raise admin_login_required()
            return build_onbid_observability_summary(session, days=days)
