from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from backend.config import PROJECT_ROOT
from backend.database.crud import get_event_with_details
from backend.database.models import AnalysisJob
from backend.jobs.event_repository import create_job_event
from backend.jobs.repository import (
    create_ocr_job,
    get_active_ocr_job_for_event,
    get_latest_ocr_job_for_event,
    list_pending_ocr_jobs,
    mark_job_failed,
    mark_job_running,
    mark_job_succeeded,
    update_job_progress,
)
from backend.jobs.service import JobServiceError, serialize_job
from backend.jobs.status import JOB_TYPE_OCR_EXTRACTION, PROVIDER_MODE_MOCK, PROVIDER_MODE_TESSERACT
from backend.ocr.tesseract_engine import OcrEngineError, find_tesseract_command, ocr_document


def create_or_get_ocr_job(
    session: Session,
    event_id: int,
    requested_by: str = "admin",
    force: bool = False,
    provider_mode: str = PROVIDER_MODE_TESSERACT,
) -> dict:
    event = get_event_with_details(session, event_id)
    if event is None:
        raise JobServiceError("OCR target event not found", status_code=404)

    if event.parse_status not in {"OCR_REQUIRED", "TEXT_EXTRACTION_FAILED", "MANUAL_REVIEW", "OCR_MOCKED"} and not force:
        return {
            "status": "not_required",
            "event_id": event_id,
            "job": serialize_job(get_latest_ocr_job_for_event(session, event_id)),
            "parse_status": event.parse_status,
        }

    active = get_active_ocr_job_for_event(session, event_id)
    if active and not force:
        return {
            "status": "existing",
            "event_id": event_id,
            "job": serialize_job(active),
            "parse_status": event.parse_status,
        }

    job = create_ocr_job(
        session,
        event_id=event_id,
        requested_by=requested_by,
        provider_mode=provider_mode,
    )
    create_job_event(session, job, "ocr/queued", message="OCR job queued")
    return {
        "status": "queued",
        "event_id": event_id,
        "job": serialize_job(job),
        "parse_status": event.parse_status,
    }


def enqueue_ocr_required_jobs(session: Session, limit: int = 20, requested_by: str = "scheduler") -> list[dict]:
    from sqlalchemy import select
    from backend.database.models import AssetEvent

    events = list(
        session.scalars(
            select(AssetEvent)
            .where(AssetEvent.parse_status.in_(("OCR_REQUIRED", "TEXT_EXTRACTION_FAILED")))
            .order_by(AssetEvent.notice_date.desc(), AssetEvent.id.asc())
            .limit(limit)
        )
    )
    queued: list[dict] = []
    for event in events:
        if get_active_ocr_job_for_event(session, event.id):
            continue
        queued.append(create_or_get_ocr_job(session, event.id, requested_by=requested_by))
    return queued


def run_pending_mock_ocr_jobs(session: Session, limit: int = 1) -> list[dict]:
    processed: list[dict] = []
    for job in list_pending_ocr_jobs(session, limit=limit, provider_mode=PROVIDER_MODE_MOCK):
        processed.append(run_mock_ocr_job(session, job))
    return processed


def run_pending_real_ocr_jobs(session: Session, limit: int = 1) -> list[dict]:
    processed: list[dict] = []
    for job in list_pending_ocr_jobs(session, limit=limit, provider_mode=PROVIDER_MODE_TESSERACT):
        processed.append(run_real_ocr_job(session, job))
    return processed


def ocr_engine_status() -> dict:
    command = find_tesseract_command()
    return {
        "engine": "tesseract",
        "available": bool(command),
        "command": command or "",
    }


def run_real_ocr_job(session: Session, job: AnalysisJob) -> dict:
    if job.job_type != JOB_TYPE_OCR_EXTRACTION:
        raise JobServiceError("Not an OCR job", status_code=400)
    event = get_event_with_details(session, job.event_id)
    if event is None:
        mark_job_failed(session, job, "EVENT_NOT_FOUND", "OCR target event not found")
        return {"job": serialize_job(job), "status": "failed"}

    mark_job_running(session, job)
    create_job_event(session, job, "ocr/started", message="Tesseract OCR started")
    raw_file_path = Path(event.raw_document.file_path) if event.raw_document else Path("")
    try:
        update_job_progress(session, job, "Tesseract OCR is reading pages", 30)
        result = ocr_document(raw_file_path)
    except OcrEngineError as exc:
        mark_job_failed(session, job, exc.code, exc.message)
        create_job_event(session, job, "ocr/failed", payload={"code": exc.code}, message=exc.message)
        return {"job": serialize_job(job), "status": "failed", "error_code": exc.code}

    if len(result.text.strip()) < 100:
        mark_job_failed(session, job, "OCR_TEXT_TOO_SHORT", "Tesseract OCR produced less than 100 characters")
        create_job_event(session, job, "ocr/failed", message="Tesseract OCR text too short")
        return {"job": serialize_job(job), "status": "failed", "error_code": "OCR_TEXT_TOO_SHORT"}

    output_dir = PROJECT_ROOT / "storage" / "processed" / "ocr_tesseract"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"event_{event.id}_ocr.txt"
    output_path.write_text(result.text, encoding="utf-8")

    event.extracted_text = result.text
    event.parse_status = "OCR_PARSED"
    event.status = "OCR_COMPLETED"
    update_job_progress(session, job, "Tesseract OCR text stored", 90)
    mark_job_succeeded(
        session,
        job,
        result_summary=f"Tesseract OCR stored {len(result.text)} chars from {result.page_count} page(s)",
        output_json_path="",
        output_markdown_path=str(output_path),
    )
    create_job_event(
        session,
        job,
        "ocr/succeeded",
        payload={
            "text_length": len(result.text),
            "page_count": result.page_count,
            "engine": result.engine,
            "language": result.language,
            "output_path": str(output_path),
        },
        message="Tesseract OCR succeeded",
    )
    return {
        "job": serialize_job(job),
        "status": "succeeded",
        "text_length": len(result.text),
        "page_count": result.page_count,
    }


def run_mock_ocr_job(session: Session, job: AnalysisJob) -> dict:
    if job.job_type != JOB_TYPE_OCR_EXTRACTION:
        raise JobServiceError("Not an OCR job", status_code=400)
    event = get_event_with_details(session, job.event_id)
    if event is None:
        mark_job_failed(session, job, "EVENT_NOT_FOUND", "OCR target event not found")
        return {"job": serialize_job(job), "status": "failed"}

    mark_job_running(session, job)
    create_job_event(session, job, "ocr/started", message="Mock OCR started")
    evidence = event.raw_document.evidence if event.raw_document else None
    raw_file_path = event.raw_document.file_path if event.raw_document else ""
    source_name = Path(raw_file_path).name if raw_file_path else event.title
    evidence_text = evidence.detail_page_text if evidence else ""

    update_job_progress(session, job, "Mock OCR extracting document hints", 40)
    mock_text = "\n".join(
        part
        for part in [
            "[MOCK_OCR_RESULT]",
            f"case_number: {event.case_number}",
            f"title: {event.title}",
            f"source_file: {source_name}",
            f"notice_date: {event.notice_date}",
            f"expire_date: {event.expire_date}",
            evidence_text[:3000],
        ]
        if part
    )
    if len(mock_text.strip()) < 100:
        mark_job_failed(session, job, "OCR_TEXT_TOO_SHORT", "Mock OCR could not build enough text")
        create_job_event(session, job, "ocr/failed", message="Mock OCR text too short")
        return {"job": serialize_job(job), "status": "failed"}

    output_dir = PROJECT_ROOT / "storage" / "processed" / "ocr_mock"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"event_{event.id}_ocr.txt"
    output_path.write_text(mock_text, encoding="utf-8")

    event.extracted_text = mock_text
    event.parse_status = "OCR_MOCKED"
    event.status = "OCR_COMPLETED"
    update_job_progress(session, job, "Mock OCR text stored", 90)
    mark_job_succeeded(
        session,
        job,
        result_summary=f"Mock OCR stored {len(mock_text)} chars",
        output_json_path="",
        output_markdown_path=str(output_path),
    )
    create_job_event(
        session,
        job,
        "ocr/succeeded",
        payload={"text_length": len(mock_text), "output_path": str(output_path)},
        message="Mock OCR succeeded",
    )
    return {"job": serialize_job(job), "status": "succeeded", "text_length": len(mock_text)}
