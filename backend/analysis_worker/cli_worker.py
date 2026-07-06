import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from backend.analysis_worker.prompt_builder import job_dir, write_input_snapshot
from backend.analysis_worker.result_parser import ResultParseError, markdown_from_payload, parse_cli_output
from backend.config import PROJECT_ROOT
from backend.database.analysis_results import create_or_get_deep_result
from backend.database.session import init_db, session_scope
from backend.document_pipeline.storage import archive_event_document
from backend.jobs.repository import (
    get_job,
    list_pending_jobs,
    mark_job_failed,
    mark_job_running,
    mark_job_succeeded,
    set_job_backup_path,
    set_job_execution_mode,
)
from backend.jobs.status import (
    ERROR_CLI_NOT_AUTHENTICATED,
    ERROR_CLI_TIMEOUT,
    ERROR_FILE_NOT_FOUND,
    ERROR_NO_SOURCE_TEXT,
    ERROR_UNKNOWN,
)
from backend.jobs.worker_heartbeat import default_worker_id, upsert_worker_heartbeat


SCHEMA_PATH = PROJECT_ROOT / "backend" / "analysis_worker" / "schemas" / "deep_analysis.schema.json"


class WorkerError(RuntimeError):
    def __init__(self, message: str, error_code: str = ERROR_UNKNOWN) -> None:
        super().__init__(message)
        self.error_code = error_code


def has_source_text(job) -> bool:
    event = job.event
    evidence = event.raw_document.evidence
    analysis = event.analyses[0] if event.analyses else None
    parts = [
        event.extracted_text or "",
        evidence.detail_page_text if evidence else "",
        analysis.item_details if analysis else "",
        analysis.risk_comment if analysis else "",
    ]
    return any(part.strip() for part in parts)


def build_codex_command(
    input_path: Path,
    last_message_path: Path,
    codex_command: str = "codex",
) -> list[str]:
    instruction = (
        f"{input_path} 파일을 읽고 법원 회생·파산 매각 물건의 상세 분석 JSON을 작성하라. "
        "문서에 없는 사실은 확정하지 말고 추정이라고 표시하라. "
        "반드시 지정된 output schema를 만족하는 JSON만 반환하라."
    )
    return [
        codex_command,
        "exec",
        "--json",
        "--sandbox",
        "workspace-write",
        "--output-schema",
        str(SCHEMA_PATH),
        "--output-last-message",
        str(last_message_path),
        instruction,
    ]


def mock_cli_output(input_path: Path) -> str:
    text = input_path.read_text(encoding="utf-8")
    case_line = next((line for line in text.splitlines() if line.startswith("- case_number:")), "")
    case_number = case_line.replace("- case_number:", "").strip() or "UNKNOWN"
    payload = {
        "summary": f"{case_number} 물건에 대한 로컬 CLI 워커 테스트 분석입니다.",
        "asset_type": "문서 기반 확인",
        "price_opinion": "최저가와 감정가의 근거 자료를 추가 확인해야 합니다.",
        "key_dates": ["입찰일과 공고만료일을 원문 기준으로 재확인해야 합니다."],
        "rights_and_legal_risks": ["등기, 임차인, 유치권 등 인수 가능 권리를 확인해야 합니다."],
        "physical_or_market_risks": ["현장 상태와 시장성은 별도 실사 자료가 필요합니다."],
        "required_follow_up_documents": ["등기부등본", "매각물건명세서", "감정평가서", "현장 사진"],
        "recommended_action": "기본 정보가 맞는지 확인한 뒤 권리/가격 자료를 보강해 재검토합니다.",
        "confidence": "medium",
        "markdown_report": (
            f"# Codex CLI 상세 분석 결과\n\n"
            f"## 요약\n{case_number} 물건은 로컬 비동기 워커 테스트를 통해 분석되었습니다.\n\n"
            "## 주요 리스크\n"
            "- 권리관계와 인수 조건은 원문만으로 확정하지 않았습니다.\n"
            "- 가격 판단은 감정평가서와 시세 자료 보강이 필요합니다.\n\n"
            "## 권장 액션\n등기부등본, 감정평가서, 현장 사진을 확보한 뒤 실제 매입 가능성을 판단하세요.\n"
        ),
    }
    return json.dumps(payload, ensure_ascii=False)


def run_codex_exec(input_path: Path, timeout_seconds: int, codex_command: str, use_mock: bool) -> tuple[str, str]:
    if use_mock:
        return mock_cli_output(input_path), ""
    if shutil.which(codex_command) is None:
        raise WorkerError("Codex CLI executable was not found in PATH", ERROR_FILE_NOT_FOUND)

    last_message_path = input_path.parent / "codex_last_message.json"
    command = build_codex_command(
        input_path,
        last_message_path=last_message_path,
        codex_command=codex_command,
    )
    try:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise WorkerError(f"Codex CLI timed out after {timeout_seconds} seconds", ERROR_CLI_TIMEOUT) from exc

    stderr = completed.stderr or ""
    if completed.returncode != 0:
        message = stderr or completed.stdout or f"Codex CLI exited with {completed.returncode}"
        lowered = message.lower()
        error_code = ERROR_CLI_NOT_AUTHENTICATED if "auth" in lowered or "login" in lowered else ERROR_UNKNOWN
        raise WorkerError(message, error_code)
    if last_message_path.exists() and last_message_path.read_text(encoding="utf-8").strip():
        return last_message_path.read_text(encoding="utf-8"), stderr
    return completed.stdout, stderr


def write_result_files(job_id: int, payload: dict[str, Any], markdown: str, stderr: str) -> tuple[str, str, str]:
    directory = job_dir(job_id)
    output_json = directory / "output.json"
    output_markdown = directory / "output.md"
    stderr_log = directory / "stderr.log"
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    output_markdown.write_text(markdown, encoding="utf-8")
    stderr_log.write_text(stderr or "", encoding="utf-8")
    return (
        str(output_json.relative_to(PROJECT_ROOT)),
        str(output_markdown.relative_to(PROJECT_ROOT)),
        str(stderr_log.relative_to(PROJECT_ROOT)),
    )


def _heartbeat(
    worker_id: str | None,
    status: str,
    message: str,
    current_job_id: int | None = None,
) -> None:
    if not worker_id:
        return
    with session_scope() as session:
        upsert_worker_heartbeat(
            session=session,
            worker_id=worker_id,
            worker_type="codex_cli_worker",
            provider_mode="mock" if "mock" in worker_id else "exec",
            status=status,
            status_message=message,
            current_job_id=current_job_id,
        )


def process_job(
    job_id: int,
    timeout_seconds: int = 900,
    codex_command: str = "codex",
    use_mock: bool = False,
    worker_id: str | None = None,
) -> str:
    input_path: Path | None = None
    try:
        _heartbeat(worker_id, "RUNNING", f"job #{job_id} 분석을 시작합니다.", job_id)
        with session_scope() as session:
            job = get_job(session, job_id)
            if job is None:
                raise WorkerError(f"Job {job_id} not found", ERROR_FILE_NOT_FOUND)
            if job.status != "PENDING":
                return job.status
            if not has_source_text(job):
                raise WorkerError("No source text is available for analysis", ERROR_NO_SOURCE_TEXT)
            set_job_execution_mode(session, job, "mock" if use_mock else "codex_exec")
            mark_job_running(session, job)
            input_path = write_input_snapshot(job)

        raw_output, stderr = run_codex_exec(
            input_path=input_path,
            timeout_seconds=timeout_seconds,
            codex_command=codex_command,
            use_mock=use_mock,
        )
        payload = parse_cli_output(raw_output)
        markdown = markdown_from_payload(payload)
        output_json_path, output_markdown_path, stderr_log_path = write_result_files(
            job_id=job_id,
            payload=payload,
            markdown=markdown,
            stderr=stderr,
        )

        with session_scope() as session:
            job = get_job(session, job_id)
            if job is None:
                raise WorkerError(f"Job {job_id} not found after execution", ERROR_FILE_NOT_FOUND)
            if job.status == "CANCELED":
                return job.status
            analysis = job.event.analyses[0] if job.event.analyses else None
            if analysis is None:
                raise WorkerError("Base AI analysis is missing", ERROR_NO_SOURCE_TEXT)
            analysis.detailed_analysis = markdown
            backup_path = archive_event_document(session, job.event)
            set_job_backup_path(session, job, backup_path)
            create_or_get_deep_result(
                session=session,
                event=job.event,
                model_provider="codex_cli",
                model_name="mock" if use_mock else codex_command,
                detailed_analysis=markdown,
                structured_json_path=output_json_path,
                markdown_path=output_markdown_path,
                force=job.requested_by == "admin_force",
            )
            mark_job_succeeded(
                session=session,
                job=job,
                result_summary=str(payload.get("summary") or "")[:1000],
                output_json_path=output_json_path,
                output_markdown_path=output_markdown_path,
                stderr_log_path=stderr_log_path,
            )
            _heartbeat(worker_id, "IDLE", f"job #{job_id} 분석이 완료되었습니다.")
            return job.status
    except ResultParseError as exc:
        _mark_failed(job_id, exc.error_code, str(exc))
        _heartbeat(worker_id, "ERROR", f"job #{job_id} 결과 파싱 실패: {exc}", job_id)
        return "FAILED"
    except WorkerError as exc:
        _mark_failed(job_id, exc.error_code, str(exc))
        _heartbeat(worker_id, "ERROR", f"job #{job_id} 워커 오류: {exc}", job_id)
        return "FAILED"
    except Exception as exc:
        _mark_failed(job_id, ERROR_UNKNOWN, str(exc))
        _heartbeat(worker_id, "ERROR", f"job #{job_id} 알 수 없는 오류: {exc}", job_id)
        return "FAILED"


def _mark_failed(job_id: int, error_code: str, error_message: str) -> None:
    with session_scope() as session:
        job = get_job(session, job_id)
        if job is not None:
            mark_job_failed(session, job, error_code=error_code, error_message=error_message)


def run_pending_jobs(
    limit: int = 1,
    timeout_seconds: int = 900,
    codex_command: str = "codex",
    use_mock: bool = False,
    worker_id: str | None = None,
) -> list[tuple[int, str]]:
    init_db()
    worker_id = worker_id or default_worker_id("codex_cli_worker", "mock" if use_mock else "exec")
    _heartbeat(worker_id, "STARTING", "Codex CLI 워커가 시작되었습니다.")
    with session_scope() as session:
        jobs = list_pending_jobs(session, limit=limit)
        job_ids = [job.id for job in jobs]
    if not job_ids:
        _heartbeat(worker_id, "IDLE", "처리할 대기 job이 없습니다.")

    results: list[tuple[int, str]] = []
    for job_id in job_ids:
        status = process_job(
            job_id=job_id,
            timeout_seconds=timeout_seconds,
            codex_command=codex_command,
            use_mock=use_mock,
            worker_id=worker_id,
        )
        results.append((job_id, status))
    _heartbeat(worker_id, "IDLE", f"{len(results)}개 job 처리를 마쳤습니다.")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run pending Codex CLI analysis jobs.")
    parser.add_argument("--limit", type=int, default=1, help="Maximum pending jobs to process.")
    parser.add_argument("--timeout", type=int, default=900, help="Codex CLI timeout in seconds.")
    parser.add_argument("--codex-command", default="codex", help="Codex CLI executable name or path.")
    parser.add_argument("--mock", action="store_true", help="Use deterministic mock output instead of Codex CLI.")
    parser.add_argument("--worker-id", default="", help="Stable worker heartbeat id.")
    args = parser.parse_args()
    results = run_pending_jobs(
        limit=args.limit,
        timeout_seconds=args.timeout,
        codex_command=args.codex_command,
        use_mock=args.mock,
        worker_id=args.worker_id or None,
    )
    print(json.dumps({"processed": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
