from __future__ import annotations

from fastapi import FastAPI, Query, Request

from backend.database.session import session_scope
from backend.jobs.ocr_service import create_or_get_ocr_job, enqueue_ocr_required_jobs, ocr_engine_status
from backend.jobs.service import JobServiceError
from backend.services.audit_logs import create_audit_log
from backend.web.dependencies import RequireAdmin, admin_login_required


def register_ocr_operation_routes(
    app: FastAPI,
    *,
    require_admin: RequireAdmin,
    raise_job_error,
) -> None:
    @app.post("/api/admin/events/{event_id}/ocr/jobs")
    def create_ocr_job_api(request: Request, event_id: int, force: bool = Query(False)) -> dict:
        with session_scope() as session:
            current_user = require_admin(request, session)
            if current_user is None:
                raise admin_login_required()
            try:
                result = create_or_get_ocr_job(session, event_id, requested_by=current_user.username, force=force)
                create_audit_log(
                    session,
                    current_user.id,
                    "ADMIN_OCR_JOB_REQUESTED",
                    "asset_event",
                    event_id,
                    "Admin requested OCR job",
                    {"force": force, "status": result.get("status")},
                )
                return result
            except JobServiceError as exc:
                raise_job_error(exc)

    @app.post("/api/admin/ocr/enqueue")
    def enqueue_ocr_jobs_api(request: Request, limit: int = Query(20, ge=1, le=200)) -> dict:
        with session_scope() as session:
            current_user = require_admin(request, session)
            if current_user is None:
                raise admin_login_required()
            queued = enqueue_ocr_required_jobs(session, limit=limit, requested_by=current_user.username)
            create_audit_log(
                session,
                current_user.id,
                "ADMIN_OCR_JOBS_ENQUEUED",
                "analysis_job",
                "OCR_EXTRACTION",
                "Admin enqueued OCR jobs",
                {"count": len(queued), "limit": limit},
            )
            return {"queued": queued, "count": len(queued)}

    @app.get("/api/admin/ocr/status")
    def read_ocr_status_api(request: Request) -> dict:
        with session_scope() as session:
            if require_admin(request, session) is None:
                raise admin_login_required()
            return ocr_engine_status()
