from __future__ import annotations

import socket

from backend.jobs.worker_heartbeat import (
    is_heartbeat_stale,
    serialize_worker_heartbeat,
)


LOCAL_APP_SERVER_HOST = "127.0.0.1"
LOCAL_APP_SERVER_PORT = 4500


def is_local_port_open(host: str, port: int, timeout_seconds: float = 0.2) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True
    except OSError:
        return False


def build_local_analysis_status(job_counts: dict[str, int], worker_heartbeats=None) -> dict:
    worker_heartbeats = worker_heartbeats or []
    app_server_online = is_local_port_open(LOCAL_APP_SERVER_HOST, LOCAL_APP_SERVER_PORT)
    pending = job_counts.get("PENDING", 0)
    running = job_counts.get("RUNNING", 0)
    failed = job_counts.get("FAILED", 0)
    active_workers = [worker for worker in worker_heartbeats if worker.status in {"STARTING", "IDLE", "RUNNING"}]
    stale_workers = [worker for worker in worker_heartbeats if is_heartbeat_stale(worker)]
    latest_worker = worker_heartbeats[0] if worker_heartbeats else None
    if stale_workers:
        message = "분석 워커가 멈췄을 가능성이 있습니다. 마지막 감지 시간을 확인하세요."
        state = "stale"
    elif pending > 0 and running == 0 and not app_server_online and not active_workers:
        message = "분석 요청이 대기 중입니다. 로컬 분석 앱을 실행해야 처리됩니다."
        state = "needs_app"
    elif running > 0:
        message = "분석 작업이 진행 중입니다."
        state = "running"
    elif pending > 0:
        message = "분석 요청이 대기 중입니다. 로컬 분석 앱 또는 워커 상태를 확인하세요."
        state = "pending"
    elif failed > 0:
        message = "실패한 분석 작업이 있습니다. 실패 사유를 확인하고 재시도하세요."
        state = "failed"
    elif app_server_online:
        message = "Codex app-server가 실행 중입니다. 새 분석 요청을 처리할 준비가 되어 있습니다."
        state = "ready"
    else:
        message = "대기 중인 분석 요청은 없습니다. 필요할 때 로컬 분석 앱을 실행하세요."
        state = "idle"
    return {
        "state": state,
        "message": message,
        "app_server_online": app_server_online,
        "endpoint": f"ws://{LOCAL_APP_SERVER_HOST}:{LOCAL_APP_SERVER_PORT}",
        "pending_jobs": pending,
        "running_jobs": running,
        "failed_jobs": failed,
        "worker_count": len(worker_heartbeats),
        "active_worker_count": len(active_workers),
        "stale_worker_count": len(stale_workers),
        "latest_worker": serialize_worker_heartbeat(latest_worker) if latest_worker else None,
        "workers": [serialize_worker_heartbeat(worker) for worker in worker_heartbeats],
    }
