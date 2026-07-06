from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from backend.database.models import AnalysisJob, AssetEvent, RawDocument
from backend.jobs.status import (
    ACTIVE_STATUSES,
    JOB_TYPE_DEEP_ANALYSIS,
    JOB_TYPE_OCR_EXTRACTION,
    PROVIDER_CODEX_CLI,
    PROVIDER_LOCAL_OCR,
    PROVIDER_MODE_EXEC,
    PROVIDER_MODE_MOCK,
)


def get_job(session: Session, job_id: int) -> AnalysisJob | None:
    return session.scalar(
        select(AnalysisJob)
        .options(
            joinedload(AnalysisJob.event)
            .joinedload(AssetEvent.raw_document)
            .joinedload(RawDocument.evidence),
            joinedload(AnalysisJob.event).joinedload(AssetEvent.asset),
            joinedload(AnalysisJob.event).joinedload(AssetEvent.analyses),
        )
        .where(AnalysisJob.id == job_id)
    )


def get_latest_job_for_event(session: Session, event_id: int) -> AnalysisJob | None:
    return session.scalar(
        select(AnalysisJob)
        .where(
            AnalysisJob.event_id == event_id,
            AnalysisJob.job_type == JOB_TYPE_DEEP_ANALYSIS,
        )
        .order_by(AnalysisJob.id.desc())
        .limit(1)
    )


def get_active_job_for_event(session: Session, event_id: int) -> AnalysisJob | None:
    return session.scalar(
        select(AnalysisJob)
        .where(
            AnalysisJob.event_id == event_id,
            AnalysisJob.job_type == JOB_TYPE_DEEP_ANALYSIS,
            AnalysisJob.status.in_(ACTIVE_STATUSES),
        )
        .order_by(AnalysisJob.id.desc())
        .limit(1)
    )


def get_latest_ocr_job_for_event(session: Session, event_id: int) -> AnalysisJob | None:
    return session.scalar(
        select(AnalysisJob)
        .where(
            AnalysisJob.event_id == event_id,
            AnalysisJob.job_type == JOB_TYPE_OCR_EXTRACTION,
        )
        .order_by(AnalysisJob.id.desc())
        .limit(1)
    )


def get_active_ocr_job_for_event(session: Session, event_id: int) -> AnalysisJob | None:
    return session.scalar(
        select(AnalysisJob)
        .where(
            AnalysisJob.event_id == event_id,
            AnalysisJob.job_type == JOB_TYPE_OCR_EXTRACTION,
            AnalysisJob.status.in_(ACTIVE_STATUSES),
        )
        .order_by(AnalysisJob.id.desc())
        .limit(1)
    )


def create_deep_analysis_job(
    session: Session,
    event_id: int,
    requested_by: str = "user",
    max_attempts: int = 2,
) -> AnalysisJob:
    job = AnalysisJob(
        event_id=event_id,
        job_type=JOB_TYPE_DEEP_ANALYSIS,
        provider=PROVIDER_CODEX_CLI,
        provider_mode=PROVIDER_MODE_EXEC,
        status="PENDING",
        requested_by=requested_by,
        max_attempts=max_attempts,
    )
    session.add(job)
    session.flush()
    return job


def create_ocr_job(
    session: Session,
    event_id: int,
    requested_by: str = "admin",
    max_attempts: int = 1,
    provider_mode: str = PROVIDER_MODE_MOCK,
) -> AnalysisJob:
    job = AnalysisJob(
        event_id=event_id,
        job_type=JOB_TYPE_OCR_EXTRACTION,
        provider=PROVIDER_LOCAL_OCR,
        provider_mode=provider_mode,
        execution_mode=provider_mode,
        status="PENDING",
        requested_by=requested_by,
        max_attempts=max_attempts,
        progress_message="OCR extraction queued",
    )
    session.add(job)
    session.flush()
    return job


def list_pending_jobs(session: Session, limit: int = 1) -> list[AnalysisJob]:
    return list(
        session.scalars(
            select(AnalysisJob)
            .options(
                joinedload(AnalysisJob.event)
                .joinedload(AssetEvent.raw_document)
                .joinedload(RawDocument.evidence),
                joinedload(AnalysisJob.event).joinedload(AssetEvent.asset),
                joinedload(AnalysisJob.event).joinedload(AssetEvent.analyses),
            )
            .where(
                AnalysisJob.status == "PENDING",
                AnalysisJob.job_type == JOB_TYPE_DEEP_ANALYSIS,
                AnalysisJob.attempt_count < AnalysisJob.max_attempts,
            )
            .order_by(AnalysisJob.requested_at.asc(), AnalysisJob.id.asc())
            .limit(limit)
        ).unique()
    )


def list_pending_ocr_jobs(session: Session, limit: int = 1, provider_mode: str | None = None) -> list[AnalysisJob]:
    conditions = [
        AnalysisJob.status == "PENDING",
        AnalysisJob.job_type == JOB_TYPE_OCR_EXTRACTION,
        AnalysisJob.attempt_count < AnalysisJob.max_attempts,
    ]
    if provider_mode:
        conditions.append(AnalysisJob.provider_mode == provider_mode)
    return list(
        session.scalars(
            select(AnalysisJob)
            .options(
                joinedload(AnalysisJob.event)
                .joinedload(AssetEvent.raw_document)
                .joinedload(RawDocument.evidence),
                joinedload(AnalysisJob.event).joinedload(AssetEvent.asset),
                joinedload(AnalysisJob.event).joinedload(AssetEvent.analyses),
            )
            .where(*conditions)
            .order_by(AnalysisJob.requested_at.asc(), AnalysisJob.id.asc())
            .limit(limit)
        ).unique()
    )


def count_jobs_by_status(session: Session) -> dict[str, int]:
    rows = session.execute(
        select(AnalysisJob.status, func.count(AnalysisJob.id)).group_by(AnalysisJob.status)
    ).all()
    return {str(status): int(count) for status, count in rows}


def mark_job_running(session: Session, job: AnalysisJob) -> None:
    job.status = "RUNNING"
    job.started_at = datetime.now(timezone.utc)
    job.attempt_count += 1
    job.error_code = ""
    job.error_message = ""
    job.cancel_requested = False
    session.flush()


def mark_job_succeeded(
    session: Session,
    job: AnalysisJob,
    result_summary: str,
    output_json_path: str,
    output_markdown_path: str,
    stderr_log_path: str = "",
) -> None:
    job.status = "SUCCEEDED"
    job.finished_at = datetime.now(timezone.utc)
    job.result_summary = result_summary
    job.output_json_path = output_json_path
    job.output_markdown_path = output_markdown_path
    job.stderr_log_path = stderr_log_path
    job.error_code = ""
    job.error_message = ""
    job.progress_percent = 100
    job.progress_message = "분석 완료"
    job.last_event_at = datetime.now(timezone.utc)
    session.flush()


def mark_job_failed(
    session: Session,
    job: AnalysisJob,
    error_code: str,
    error_message: str,
    stderr_log_path: str = "",
) -> None:
    job.status = "FAILED"
    job.finished_at = datetime.now(timezone.utc)
    job.error_code = error_code
    job.error_message = error_message[:4000]
    job.stderr_log_path = stderr_log_path
    job.progress_message = f"분석 실패: {error_code}"
    job.last_event_at = datetime.now(timezone.utc)
    session.flush()


def mark_job_canceled(session: Session, job: AnalysisJob) -> None:
    job.status = "CANCELED"
    job.finished_at = datetime.now(timezone.utc)
    job.progress_message = "분석 취소됨"
    job.last_event_at = datetime.now(timezone.utc)
    session.flush()


def reset_job_for_retry(session: Session, job: AnalysisJob) -> None:
    job.status = "PENDING"
    job.started_at = None
    job.finished_at = None
    job.error_code = ""
    job.error_message = ""
    job.result_summary = ""
    job.progress_message = ""
    job.progress_percent = 0
    job.cancel_requested = False
    session.flush()


def set_job_provider_mode(session: Session, job: AnalysisJob, provider_mode: str) -> None:
    job.provider_mode = provider_mode
    session.flush()


def set_job_execution_mode(session: Session, job: AnalysisJob, execution_mode: str) -> None:
    job.execution_mode = execution_mode
    session.flush()


def set_job_codex_thread(session: Session, job: AnalysisJob, thread_id: str) -> None:
    job.codex_thread_id = thread_id
    session.flush()


def set_job_codex_turn(session: Session, job: AnalysisJob, turn_id: str) -> None:
    job.codex_turn_id = turn_id
    session.flush()


def set_job_backup_path(session: Session, job: AnalysisJob, backup_path: str) -> None:
    job.backup_path = backup_path
    session.flush()


def update_job_progress(
    session: Session,
    job: AnalysisJob,
    message: str,
    progress_percent: int | None = None,
) -> None:
    job.progress_message = message[:4000]
    if progress_percent is not None:
        job.progress_percent = max(0, min(100, progress_percent))
    job.last_event_at = datetime.now(timezone.utc)
    session.flush()


def request_job_cancel(session: Session, job: AnalysisJob) -> None:
    job.cancel_requested = True
    job.progress_message = "취소 요청 접수"
    job.last_event_at = datetime.now(timezone.utc)
    session.flush()
