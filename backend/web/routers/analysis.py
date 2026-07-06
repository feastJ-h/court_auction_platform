from __future__ import annotations

from fastapi import Body, FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from backend.ai_engine.analyzer import (
    AiAnalysisProviderError,
    GeminiAnalysisError,
    analyze_asset_text,
    is_hallucinated as is_ai_hallucinated,
)
from backend.database.crud import create_ai_analysis, get_event_with_details
from backend.database.session import session_scope
from backend.jobs.readiness import get_analysis_readiness
from backend.jobs.service import (
    JobServiceError,
    cancel_job,
    continue_job,
    create_or_get_deep_analysis_job,
    get_job_events_status,
    get_job_status,
    get_latest_deep_job_status,
    request_cancel_job,
    retry_job,
)
from backend.jobs.repository import count_jobs_by_status
from backend.jobs.worker_heartbeat import list_worker_heartbeats
from backend.services.analysis_reviews import (
    build_analysis_review_summary,
    create_analysis_review,
    serialize_analysis_review,
)
from backend.services.audit_logs import create_audit_log
from backend.services.local_analysis_status import build_local_analysis_status
from backend.web.dependencies import LoginRedirect, RequireAdmin, admin_login_required


from typing import Callable

RaiseJobError = Callable[[JobServiceError], None]


def register_analysis_routes(
    app: FastAPI,
    *,
    require_admin: RequireAdmin,
    login_redirect: LoginRedirect,
    raise_job_error: RaiseJobError,
) -> None:
    @app.post("/api/admin/events/{event_id}/basic-analysis")
    def create_basic_analysis_api(request: Request, event_id: int, force: bool = Query(False)) -> dict:
        with session_scope() as session:
            current_user = require_admin(request, session)
            if current_user is None:
                raise admin_login_required()

            event = get_event_with_details(session, event_id)
            if event is None:
                raise HTTPException(status_code=404, detail="Event not found.")
            if event.analyses and not force:
                return {"status": "cached", "event_id": event.id, "analysis_id": event.analyses[0].id}

            readiness = get_analysis_readiness(event)
            if not readiness.get("ready"):
                raise HTTPException(status_code=422, detail=readiness.get("reason", "Analysis is not ready."))

            try:
                payload = analyze_asset_text(event.extracted_text)
            except (GeminiAnalysisError, AiAnalysisProviderError) as exc:
                create_audit_log(
                    session,
                    current_user.id,
                    "ADMIN_BASIC_ANALYSIS_FAILED",
                    "asset_event",
                    event_id,
                    "Admin basic AI analysis failed",
                    {"error": str(exc)[:512]},
                )
                raise HTTPException(status_code=502, detail=f"AI analysis failed: {str(exc)}") from exc

            event.asset.main_category = payload.get("main_category") or event.asset.main_category
            event.asset.sub_category = payload.get("sub_category") or event.asset.sub_category
            event.asset.address = payload.get("address") or event.asset.address
            analysis = create_ai_analysis(
                session=session,
                event=event,
                payload=payload,
                is_hallucinated=is_ai_hallucinated(payload),
            )
            create_audit_log(
                session,
                current_user.id,
                "ADMIN_BASIC_ANALYSIS_CREATED",
                "asset_event",
                event_id,
                "Admin approved basic AI analysis",
                {"provider": payload.get("analysis_provider"), "force": force},
            )
            return {
                "status": "created",
                "event_id": event.id,
                "analysis_id": analysis.id,
                "provider": analysis.analysis_provider,
            }

    @app.get("/api/local-analysis/status")
    def read_local_analysis_status() -> dict:
        with session_scope() as session:
            job_counts = count_jobs_by_status(session)
            worker_heartbeats = list_worker_heartbeats(session)
            return build_local_analysis_status(job_counts, worker_heartbeats)

    @app.get("/api/admin/analysis-reviews/summary")
    def read_analysis_review_summary(request: Request) -> dict:
        with session_scope() as session:
            if require_admin(request, session) is None:
                raise admin_login_required()
            return build_analysis_review_summary(session)

    @app.post("/api/admin/analysis-results/{analysis_result_id}/reviews")
    def create_analysis_result_review(request: Request, analysis_result_id: int, payload: dict = Body(...)) -> dict:
        with session_scope() as session:
            if require_admin(request, session) is None:
                raise admin_login_required()
            try:
                review = create_analysis_review(session, analysis_result_id, payload)
                user = require_admin(request, session)
                create_audit_log(
                    session,
                    user.id if user else None,
                    "ADMIN_ANALYSIS_REVIEW_CREATED",
                    "analysis_result",
                    analysis_result_id,
                    "Admin API analysis review created",
                )
            except ValueError as exc:
                if str(exc) == "analysis_result_not_found":
                    raise HTTPException(status_code=404, detail="Analysis result not found.") from exc
                raise
            return {"review": serialize_analysis_review(review)}

    @app.post("/admin/analysis-results/{analysis_result_id}/reviews")
    def create_analysis_result_review_form(
        request: Request,
        analysis_result_id: int,
        price_score: int = Form(0),
        date_score: int = Form(0),
        risk_score: int = Form(0),
        evidence_score: int = Form(0),
        hallucination_score: int = Form(0),
        notes: str = Form(""),
    ) -> RedirectResponse:
        with session_scope() as session:
            current_user = require_admin(request, session)
            if current_user is None:
                return login_redirect("/admin")
            try:
                create_analysis_review(
                    session,
                    analysis_result_id,
                    {
                        "reviewer": current_user.username,
                        "price_score": price_score,
                        "date_score": date_score,
                        "risk_score": risk_score,
                        "evidence_score": evidence_score,
                        "hallucination_score": hallucination_score,
                        "notes": notes,
                    },
                )
                create_audit_log(
                    session,
                    current_user.id,
                    "ADMIN_ANALYSIS_REVIEW_CREATED",
                    "analysis_result",
                    analysis_result_id,
                    "Admin analysis review created",
                    {
                        "price_score": price_score,
                        "date_score": date_score,
                        "risk_score": risk_score,
                        "evidence_score": evidence_score,
                        "hallucination_score": hallucination_score,
                    },
                )
            except ValueError as exc:
                if str(exc) == "analysis_result_not_found":
                    raise HTTPException(status_code=404, detail="analysis result not found") from exc
                raise
        return RedirectResponse(url="/admin", status_code=303)

    @app.post("/api/analyze/deep/{event_id}")
    def request_deep_analysis_compat(event_id: int) -> dict:
        return create_deep_analysis_job(event_id)

    @app.post("/api/analyze/deep/{event_id}/jobs")
    def create_deep_analysis_job(event_id: int, requested_by: str = "user", force: bool = Query(False)) -> dict:
        with session_scope() as session:
            try:
                return create_or_get_deep_analysis_job(
                    session,
                    event_id,
                    requested_by=requested_by,
                    force=force,
                )
            except JobServiceError as exc:
                raise_job_error(exc)

    @app.get("/api/analyze/jobs/{job_id}")
    def read_analysis_job(job_id: int) -> dict:
        with session_scope() as session:
            try:
                return get_job_status(session, job_id)
            except JobServiceError as exc:
                raise_job_error(exc)

    @app.get("/api/analyze/deep/{event_id}/jobs/latest")
    def read_latest_deep_analysis_job(event_id: int) -> dict:
        with session_scope() as session:
            try:
                return get_latest_deep_job_status(session, event_id)
            except JobServiceError as exc:
                raise_job_error(exc)

    @app.post("/api/analyze/jobs/{job_id}/cancel")
    def cancel_analysis_job(job_id: int) -> dict:
        with session_scope() as session:
            try:
                return cancel_job(session, job_id)
            except JobServiceError as exc:
                raise_job_error(exc)

    @app.post("/api/analyze/jobs/{job_id}/cancel-request")
    def request_cancel_analysis_job(job_id: int) -> dict:
        with session_scope() as session:
            try:
                return request_cancel_job(session, job_id)
            except JobServiceError as exc:
                raise_job_error(exc)

    @app.post("/api/analyze/jobs/{job_id}/retry")
    def retry_analysis_job(job_id: int) -> dict:
        with session_scope() as session:
            try:
                return retry_job(session, job_id)
            except JobServiceError as exc:
                raise_job_error(exc)

    @app.get("/api/analyze/jobs/{job_id}/events")
    def read_analysis_job_events(job_id: int) -> dict:
        with session_scope() as session:
            try:
                return get_job_events_status(session, job_id)
            except JobServiceError as exc:
                raise_job_error(exc)

    @app.post("/api/analyze/jobs/{job_id}/continue")
    def continue_analysis_job(job_id: int, payload: dict = Body(...)) -> dict:
        with session_scope() as session:
            try:
                return continue_job(session, job_id, instruction=str(payload.get("instruction") or ""))
            except JobServiceError as exc:
                raise_job_error(exc)
