from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text

from backend.database.session import engine


def start_sync_run(run_id: str, api_kind: str) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("INSERT OR REPLACE INTO onbid_sync_runs(run_id, api_kind, started_at, status) VALUES (:run_id, :api_kind, :started_at, 'running')"),
            {"run_id": str(run_id), "api_kind": api_kind, "started_at": datetime.now(timezone.utc).isoformat()},
        )


def finish_sync_run(run_id: str, *, status: str, fetched: int = 0, inserted: int = 0, updated: int = 0, duplicates: int = 0, dropped_stale: int = 0, dropped_unknown: int = 0, error_code: str = "", error_summary: str = "") -> None:
    safe_summary = " ".join((error_summary or "").split())[:500]
    with engine.begin() as connection:
        connection.execute(
            text("""
                UPDATE onbid_sync_runs SET finished_at=:finished_at, status=:status,
                    fetched=:fetched, inserted=:inserted, updated=:updated, duplicates=:duplicates,
                    dropped_stale=:dropped_stale, dropped_unknown=:dropped_unknown,
                    error_code=:error_code, error_summary_sanitized=:error_summary
                WHERE run_id=:run_id
            """),
            {
                "run_id": str(run_id), "finished_at": datetime.now(timezone.utc).isoformat(), "status": status,
                "fetched": fetched, "inserted": inserted, "updated": updated, "duplicates": duplicates,
                "dropped_stale": dropped_stale, "dropped_unknown": dropped_unknown,
                "error_code": error_code[:64], "error_summary": safe_summary,
            },
        )


def latest_successful_sync() -> dict | None:
    with engine.begin() as connection:
        row = connection.execute(text("SELECT run_id, api_kind, finished_at, fetched, inserted, updated FROM onbid_sync_runs WHERE status='succeeded' ORDER BY finished_at DESC LIMIT 1")).mappings().first()
    return dict(row) if row else None
