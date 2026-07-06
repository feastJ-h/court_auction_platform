from datetime import datetime

from sqlalchemy.orm import Session

from backend.database.crud import get_event_with_details
from backend.database.analysis_results import (
    DEFAULT_PROMPT_VERSION,
    get_active_result,
    source_hash_for_event,
)
from backend.database.models import AnalysisJob
from backend.jobs.repository import (
    create_deep_analysis_job,
    get_active_job_for_event,
    get_job,
    get_latest_job_for_event,
    mark_job_canceled,
    request_job_cancel,
    reset_job_for_retry,
    set_job_provider_mode,
)
from backend.jobs.event_repository import create_job_event, list_job_events, serialize_event
from backend.jobs.readiness import get_analysis_readiness
from backend.jobs.status import ACTIVE_STATUSES, PROVIDER_MODE_APP_SERVER


class JobServiceError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def serialize_job(job: AnalysisJob | None) -> dict | None:
    if job is None:
        return None
    return {
        "id": job.id,
        "event_id": job.event_id,
        "job_type": job.job_type,
        "provider": job.provider,
        "status": job.status,
        "requested_by": job.requested_by,
        "requested_at": _iso(job.requested_at),
        "started_at": _iso(job.started_at),
        "finished_at": _iso(job.finished_at),
        "attempt_count": job.attempt_count,
        "max_attempts": job.max_attempts,
        "input_snapshot_path": job.input_snapshot_path,
        "output_json_path": job.output_json_path,
        "output_markdown_path": job.output_markdown_path,
        "stderr_log_path": job.stderr_log_path,
        "backup_path": job.backup_path,
        "error_code": job.error_code,
        "error_message": job.error_message,
        "result_summary": job.result_summary,
        "codex_thread_id": job.codex_thread_id,
        "codex_turn_id": job.codex_turn_id,
        "progress_message": job.progress_message,
        "progress_percent": job.progress_percent,
        "last_event_at": _iso(job.last_event_at),
        "cancel_requested": job.cancel_requested,
        "provider_mode": job.provider_mode,
        "execution_mode": job.execution_mode,
    }


def create_or_get_deep_analysis_job(
    session: Session,
    event_id: int,
    requested_by: str = "user",
    force: bool = False,
) -> dict:
    event = get_event_with_details(session, event_id)
    if event is None:
        raise JobServiceError("분석 대상 물건을 찾을 수 없습니다.", status_code=404)
    if not event.analyses:
        raise JobServiceError("기본 AI 분석이 먼저 필요합니다.", status_code=409)
    readiness = get_analysis_readiness(event)
    if not readiness["ready"]:
        raise JobServiceError(f"분석 준비가 필요합니다: {readiness['reason']}", status_code=409)

    analysis = event.analyses[0]
    source_hash = source_hash_for_event(event)
    existing_deep_result = (
        get_active_result(session, event_id, "codex_app_server", "deep", source_hash, DEFAULT_PROMPT_VERSION)
        or get_active_result(session, event_id, "codex_cli", "deep", source_hash, DEFAULT_PROMPT_VERSION)
        or get_active_result(session, event_id, "chatgpt", "deep", source_hash, DEFAULT_PROMPT_VERSION)
    )
    if existing_deep_result and not force:
        latest = get_latest_job_for_event(session, event_id)
        return {
            "status": "cached",
            "event_id": event_id,
            "job": serialize_job(latest),
            "detailed_analysis": existing_deep_result.detailed_analysis,
            "analysis_result_id": existing_deep_result.id,
        }

    if analysis.detailed_analysis.strip() and not force:
        latest = get_latest_job_for_event(session, event_id)
        return {
            "status": "cached",
            "event_id": event_id,
            "job": serialize_job(latest),
            "detailed_analysis": analysis.detailed_analysis,
        }

    active = get_active_job_for_event(session, event_id)
    if active:
        return {
            "status": "existing",
            "event_id": event_id,
            "job": serialize_job(active),
            "detailed_analysis": "",
        }

    job = create_deep_analysis_job(session, event_id=event_id, requested_by=requested_by)
    if force:
        job.requested_by = "admin_force"
        job.progress_message = "강제 재분석 요청"
    return {
        "status": "force_queued" if force else "queued",
        "event_id": event_id,
        "job": serialize_job(job),
        "detailed_analysis": "",
    }


def get_job_status(session: Session, job_id: int) -> dict:
    job = get_job(session, job_id)
    if job is None:
        raise JobServiceError("작업을 찾을 수 없습니다.", status_code=404)

    analysis = job.event.analyses[0] if job.event and job.event.analyses else None
    return {
        "job": serialize_job(job),
        "detailed_analysis": analysis.detailed_analysis if analysis else "",
    }


def get_latest_deep_job_status(session: Session, event_id: int) -> dict:
    event = get_event_with_details(session, event_id)
    if event is None:
        raise JobServiceError("분석 대상 물건을 찾을 수 없습니다.", status_code=404)
    job = get_latest_job_for_event(session, event_id)
    analysis = event.analyses[0] if event.analyses else None
    return {
        "job": serialize_job(job),
        "detailed_analysis": analysis.detailed_analysis if analysis else "",
    }


def cancel_job(session: Session, job_id: int) -> dict:
    job = get_job(session, job_id)
    if job is None:
        raise JobServiceError("작업을 찾을 수 없습니다.", status_code=404)
    if job.status not in ACTIVE_STATUSES:
        raise JobServiceError("대기 또는 진행 중인 작업만 취소할 수 있습니다.", status_code=409)
    mark_job_canceled(session, job)
    create_job_event(session, job, "job/canceled", message="작업이 즉시 취소되었습니다.")
    return {"job": serialize_job(job)}


def request_cancel_job(session: Session, job_id: int) -> dict:
    job = get_job(session, job_id)
    if job is None:
        raise JobServiceError("작업을 찾을 수 없습니다.", status_code=404)
    if job.status not in ACTIVE_STATUSES:
        raise JobServiceError("대기 또는 진행 중인 작업만 취소 요청할 수 있습니다.", status_code=409)
    request_job_cancel(session, job)
    create_job_event(session, job, "job/cancel_requested", message="취소 요청이 접수되었습니다.")
    return {"job": serialize_job(job)}


def retry_job(session: Session, job_id: int) -> dict:
    job = get_job(session, job_id)
    if job is None:
        raise JobServiceError("작업을 찾을 수 없습니다.", status_code=404)
    if job.status not in {"FAILED", "CANCELED"}:
        raise JobServiceError("실패 또는 취소된 작업만 재시도할 수 있습니다.", status_code=409)
    if job.status == "FAILED" and job.attempt_count >= job.max_attempts:
        raise JobServiceError("최대 재시도 횟수를 초과했습니다.", status_code=409)
    reset_job_for_retry(session, job)
    create_job_event(session, job, "job/retry_requested", message="재시도 요청이 접수되었습니다.")
    return {"job": serialize_job(job)}


def get_job_events_status(session: Session, job_id: int) -> dict:
    status = get_job_status(session, job_id)
    events = list_job_events(session, job_id)
    status["events"] = [serialize_event(event) for event in events]
    return status


def continue_job(session: Session, job_id: int, instruction: str) -> dict:
    instruction = (instruction or "").strip()
    if not instruction:
        raise JobServiceError("추가 지시가 비어 있습니다.", status_code=400)
    if len(instruction) > 1000:
        raise JobServiceError("추가 지시는 1000자 이하로 입력해야 합니다.", status_code=400)
    if any(blocked in instruction.lower() for blocked in ("..\\", "../", "auth.json", "password", "token")):
        raise JobServiceError("허용되지 않는 경로 또는 민감 단어가 포함되어 있습니다.", status_code=400)

    previous = get_job(session, job_id)
    if previous is None:
        raise JobServiceError("작업을 찾을 수 없습니다.", status_code=404)
    if not previous.codex_thread_id:
        raise JobServiceError("이어가기에는 Codex thread id가 필요합니다.", status_code=409)

    next_job = create_deep_analysis_job(
        session=session,
        event_id=previous.event_id,
        requested_by="admin",
        max_attempts=previous.max_attempts,
    )
    next_job.codex_thread_id = previous.codex_thread_id
    next_job.progress_message = f"이어가기 요청: {instruction[:200]}"
    set_job_provider_mode(session, next_job, PROVIDER_MODE_APP_SERVER)
    create_job_event(
        session,
        next_job,
        "job/continue_requested",
        payload={"previous_job_id": previous.id, "instruction": instruction},
        message="이어가기 작업이 생성되었습니다.",
    )
    return {"job": serialize_job(next_job)}
