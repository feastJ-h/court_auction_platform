import argparse
import asyncio
import json
import re
from pathlib import Path
from typing import Any

from backend.analysis_worker.app_server_client import AppServerClientError, CodexAppServerClient
from backend.analysis_worker.cli_worker import WorkerError, has_source_text, mock_cli_output, write_result_files
from backend.analysis_worker.event_stream import (
    FINAL_EVENT_TYPES,
    event_message,
    event_type,
    extract_final_text,
    extract_turn_id,
)
from backend.analysis_worker.prompt_builder import write_input_snapshot
from backend.analysis_worker.result_parser import ResultParseError, markdown_from_payload, parse_cli_output
from backend.config import PROJECT_ROOT
from backend.database.analysis_results import create_or_get_deep_result
from backend.database.session import init_db, session_scope
from backend.document_pipeline.storage import archive_event_document
from backend.jobs.event_repository import create_job_event
from backend.jobs.repository import (
    get_job,
    list_pending_jobs,
    mark_job_canceled,
    mark_job_failed,
    mark_job_running,
    mark_job_succeeded,
    set_job_codex_thread,
    set_job_codex_turn,
    set_job_backup_path,
    set_job_execution_mode,
    set_job_provider_mode,
    update_job_progress,
)
from backend.jobs.status import (
    ERROR_APP_SERVER_PROTOCOL,
    ERROR_CANCEL_FAILED,
    ERROR_FILE_NOT_FOUND,
    ERROR_NO_SOURCE_TEXT,
    ERROR_UNKNOWN,
    PROVIDER_MODE_APP_SERVER,
)
from backend.jobs.worker_heartbeat import default_worker_id, upsert_worker_heartbeat


def _heartbeat(
    worker_id: str | None,
    status: str,
    message: str,
    current_job_id: int | None = None,
    endpoint: str = "",
) -> None:
    if not worker_id:
        return
    with session_scope() as session:
        upsert_worker_heartbeat(
            session=session,
            worker_id=worker_id,
            worker_type="codex_app_server_worker",
            provider_mode="mock" if "mock" in worker_id else PROVIDER_MODE_APP_SERVER,
            status=status,
            status_message=message,
            current_job_id=current_job_id,
            app_server_endpoint=endpoint,
        )


def _analysis_instruction(input_path: Path) -> str:
    return (
        f"{input_path} 파일을 읽고 법원 회생·파산 매각 물건의 상세 분석 JSON을 작성하라. "
        "문서에 없는 사실은 확정하지 말고 추정이라고 표시하라. "
        "반드시 backend/analysis_worker/schemas/deep_analysis.schema.json 구조를 만족하는 JSON만 반환하라."
    )


def _is_resumable_app_server_thread_id(thread_id: str) -> bool:
    if not thread_id:
        return False
    candidate = thread_id.removeprefix("urn:uuid:")
    return re.fullmatch(r"[0-9a-fA-F-]{32,36}", candidate) is not None


def _mark_failed(job_id: int, error_code: str, error_message: str) -> None:
    with session_scope() as session:
        job = get_job(session, job_id)
        if job is not None:
            mark_job_failed(session, job, error_code=error_code, error_message=error_message)
            create_job_event(
                session,
                job,
                "error",
                payload={"error_code": error_code, "error_message": error_message},
                message=f"{error_code}: {error_message[:500]}",
            )


def _save_event(
    job_id: int,
    raw_event: dict[str, Any],
    message: str = "",
    progress: int | None = None,
    worker_id: str | None = None,
    endpoint: str = "",
) -> None:
    with session_scope() as session:
        job = get_job(session, job_id)
        if job is None:
            return
        event_name = event_type(raw_event)
        create_job_event(session, job, event_name, payload=raw_event, message=message or event_message(raw_event))
        update_job_progress(session, job, message or event_message(raw_event), progress_percent=progress)
        turn_id = extract_turn_id(raw_event)
        if turn_id and not job.codex_turn_id:
            set_job_codex_turn(session, job, turn_id)
    _heartbeat(worker_id, "RUNNING", message or event_message(raw_event), job_id, endpoint)


def _save_success(job_id: int, payload: dict[str, Any], markdown: str, stderr: str = "") -> None:
    output_json_path, output_markdown_path, stderr_log_path = write_result_files(
        job_id=job_id,
        payload=payload,
        markdown=markdown,
        stderr=stderr,
    )
    with session_scope() as session:
        job = get_job(session, job_id)
        if job is None:
            raise WorkerError(f"Job {job_id} not found after app-server execution", ERROR_FILE_NOT_FOUND)
        analysis = job.event.analyses[0] if job.event.analyses else None
        if analysis is None:
            raise WorkerError("Base AI analysis is missing", ERROR_NO_SOURCE_TEXT)
        analysis.detailed_analysis = markdown
        backup_path = archive_event_document(session, job.event)
        set_job_backup_path(session, job, backup_path)
        create_or_get_deep_result(
            session=session,
            event=job.event,
            model_provider="codex_app_server",
            model_name=job.execution_mode or "codex_app_server",
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
        create_job_event(session, job, "turn/completed", payload=payload, message="분석이 완료되었습니다.")


async def _process_mock(job_id: int, input_path: Path) -> str:
    mock_events = [
        ("thread/started", "Mock app-server thread가 시작되었습니다.", 20),
        ("turn/started", "Mock 분석 turn이 시작되었습니다.", 35),
        ("item/started", "문서 스냅샷을 읽는 중입니다.", 50),
        ("item/completed", "상세 분석 JSON을 생성했습니다.", 80),
    ]
    with session_scope() as session:
        job = get_job(session, job_id)
        if job is None:
            raise WorkerError(f"Job {job_id} not found", ERROR_FILE_NOT_FOUND)
        if not job.codex_thread_id:
            set_job_codex_thread(session, job, f"mock-thread-{job_id}")
        set_job_codex_turn(session, job, f"mock-turn-{job_id}")

    for event_name, message, progress in mock_events:
        _save_event(job_id, {"method": event_name, "params": {"message": message}}, message, progress)
        await asyncio.sleep(0.05)

    payload = parse_cli_output(mock_cli_output(input_path))
    markdown = markdown_from_payload(payload)
    _save_success(job_id, payload, markdown)
    return "SUCCEEDED"


async def process_job_with_app_server(
    job_id: int,
    endpoint: str,
    timeout_seconds: int = 900,
    model: str | None = None,
    use_mock: bool = False,
    worker_id: str | None = None,
) -> str:
    input_path: Path | None = None
    try:
        _heartbeat(worker_id, "RUNNING", f"job #{job_id} app-server 분석을 시작합니다.", job_id, endpoint)
        with session_scope() as session:
            job = get_job(session, job_id)
            if job is None:
                raise WorkerError(f"Job {job_id} not found", ERROR_FILE_NOT_FOUND)
            if job.status != "PENDING":
                return job.status
            if job.cancel_requested:
                mark_job_canceled(session, job)
                create_job_event(session, job, "job/canceled", message="실행 전 취소 요청으로 작업을 취소했습니다.")
                return "CANCELED"
            if not has_source_text(job):
                raise WorkerError("No source text is available for analysis", ERROR_NO_SOURCE_TEXT)
            set_job_provider_mode(session, job, PROVIDER_MODE_APP_SERVER)
            set_job_execution_mode(session, job, "mock" if use_mock else "codex_app_server")
            mark_job_running(session, job)
            create_job_event(session, job, "job/running", message="app-server 워커가 작업을 시작했습니다.")
            input_path = write_input_snapshot(job)

        if use_mock:
            status = await _process_mock(job_id, input_path)
            _heartbeat(worker_id, "IDLE", f"job #{job_id} mock 분석이 완료되었습니다.", None, endpoint)
            return status

        client = CodexAppServerClient(endpoint=endpoint, timeout_seconds=timeout_seconds)
        final_text = ""
        agent_delta_chunks: list[str] = []
        try:
            await client.connect()
            _save_event(job_id, {"method": "app_server/connected", "params": {"endpoint": endpoint}}, "app-server에 연결되었습니다.", 10, worker_id, endpoint)
            await client.initialize()
            _save_event(job_id, {"method": "app_server/initialized", "params": {}}, "app-server 초기화 완료", 15, worker_id, endpoint)

            with session_scope() as session:
                job = get_job(session, job_id)
                if job is None:
                    raise WorkerError(f"Job {job_id} not found", ERROR_FILE_NOT_FOUND)
                thread_id = job.codex_thread_id
                if thread_id and not _is_resumable_app_server_thread_id(thread_id):
                    create_job_event(
                        session,
                        job,
                        "thread/resume_skipped",
                        payload={"thread_id": thread_id},
                        message="기존 thread id가 실제 app-server 형식이 아니어서 새 thread를 시작합니다.",
                    )
                    thread_id = ""
                if not thread_id:
                    thread_id = await client.start_thread(model=model)
                    set_job_codex_thread(session, job, thread_id)
                create_job_event(session, job, "thread/started", payload={"thread_id": thread_id}, message="Codex thread가 준비되었습니다.")
                update_job_progress(session, job, "Codex thread가 준비되었습니다.", 25)

            turn_id = await client.start_turn(
                thread_id=thread_id,
                cwd=str(PROJECT_ROOT),
                input_text=_analysis_instruction(input_path),
            )
            with session_scope() as session:
                job = get_job(session, job_id)
                if job is not None:
                    set_job_codex_turn(session, job, turn_id)
                    create_job_event(session, job, "turn/started", payload={"turn_id": turn_id}, message="Codex turn이 시작되었습니다.")
                    update_job_progress(session, job, "Codex turn이 시작되었습니다.", 35)

            async for event in client.events():
                event_name = event_type(event)
                message = event_message(event)
                if event_name == "item/agentMessage/delta" and message:
                    agent_delta_chunks.append(message)
                _save_event(job_id, event, message, progress=60 if event_name not in FINAL_EVENT_TYPES else 90, worker_id=worker_id, endpoint=endpoint)

                with session_scope() as session:
                    job = get_job(session, job_id)
                    if job and job.cancel_requested:
                        try:
                            await client.interrupt_turn(job.codex_thread_id, job.codex_turn_id)
                            mark_job_canceled(session, job)
                            create_job_event(session, job, "turn/interrupted", message="Codex turn interrupt를 전송했습니다.")
                            return "CANCELED"
                        except Exception as exc:
                            raise WorkerError(f"Cancel request failed: {exc}", ERROR_CANCEL_FAILED) from exc

                candidate_text = extract_final_text(event)
                if candidate_text:
                    final_text = candidate_text
                if event_name in FINAL_EVENT_TYPES:
                    break
        finally:
            await client.close()

        if not final_text and agent_delta_chunks:
            final_text = "".join(agent_delta_chunks)
        if not final_text:
            raise WorkerError("App-server completed without a final agent message", ERROR_APP_SERVER_PROTOCOL)
        payload = parse_cli_output(final_text)
        markdown = markdown_from_payload(payload)
        _save_success(job_id, payload, markdown)
        _heartbeat(worker_id, "IDLE", f"job #{job_id} 분석이 완료되었습니다.", None, endpoint)
        return "SUCCEEDED"
    except ResultParseError as exc:
        _mark_failed(job_id, exc.error_code, str(exc))
        _heartbeat(worker_id, "ERROR", f"job #{job_id} 결과 파싱 실패: {exc}", job_id, endpoint)
        return "FAILED"
    except AppServerClientError as exc:
        _mark_failed(job_id, exc.error_code, str(exc))
        _heartbeat(worker_id, "ERROR", f"job #{job_id} app-server 오류: {exc}", job_id, endpoint)
        return "FAILED"
    except WorkerError as exc:
        _mark_failed(job_id, exc.error_code, str(exc))
        _heartbeat(worker_id, "ERROR", f"job #{job_id} 워커 오류: {exc}", job_id, endpoint)
        return "FAILED"
    except Exception as exc:
        _mark_failed(job_id, ERROR_UNKNOWN, str(exc))
        _heartbeat(worker_id, "ERROR", f"job #{job_id} 알 수 없는 오류: {exc}", job_id, endpoint)
        return "FAILED"


async def run_pending_jobs(
    endpoint: str,
    limit: int = 1,
    timeout_seconds: int = 900,
    model: str | None = None,
    use_mock: bool = False,
    worker_id: str | None = None,
) -> list[tuple[int, str]]:
    init_db()
    worker_id = worker_id or default_worker_id("codex_app_server_worker", "mock" if use_mock else PROVIDER_MODE_APP_SERVER, endpoint)
    _heartbeat(worker_id, "STARTING", "Codex app-server 워커가 시작되었습니다.", endpoint=endpoint)
    with session_scope() as session:
        jobs = list_pending_jobs(session, limit=limit)
        job_ids = [job.id for job in jobs]
    if not job_ids:
        _heartbeat(worker_id, "IDLE", "처리할 대기 job이 없습니다.", endpoint=endpoint)

    results: list[tuple[int, str]] = []
    for job_id in job_ids:
        status = await process_job_with_app_server(
            job_id=job_id,
            endpoint=endpoint,
            timeout_seconds=timeout_seconds,
            model=model,
            use_mock=use_mock,
            worker_id=worker_id,
        )
        results.append((job_id, status))
    _heartbeat(worker_id, "IDLE", f"{len(results)}개 job 처리를 마쳤습니다.", endpoint=endpoint)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run pending Codex app-server analysis jobs.")
    parser.add_argument("--endpoint", default="ws://127.0.0.1:4500", help="Codex app-server websocket endpoint.")
    parser.add_argument("--limit", type=int, default=1, help="Maximum pending jobs to process.")
    parser.add_argument("--timeout", type=int, default=900, help="App-server timeout in seconds.")
    parser.add_argument("--model", default=None, help="Optional Codex model name.")
    parser.add_argument("--mock", action="store_true", help="Use deterministic mock app-server events.")
    parser.add_argument("--worker-id", default="", help="Stable worker heartbeat id.")
    args = parser.parse_args()
    results = asyncio.run(
        run_pending_jobs(
            endpoint=args.endpoint,
            limit=args.limit,
            timeout_seconds=args.timeout,
            model=args.model,
            use_mock=args.mock,
            worker_id=args.worker_id or None,
        )
    )
    print(json.dumps({"processed": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
