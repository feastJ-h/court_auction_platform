import secrets

from sqlalchemy import text

from backend.database.session import engine
from backend.services.onbid_sync_runs import finish_sync_run, start_sync_run


def test_sync_history_stores_aggregate_only():
    run_id = "test-" + secrets.token_hex(8)
    try:
        start_sync_run(run_id, "notice")
        finish_sync_run(run_id, status="succeeded", fetched=10, inserted=3, updated=4, duplicates=3, dropped_stale=1, dropped_unknown=2)
        with engine.begin() as connection:
            row = connection.execute(text("SELECT * FROM onbid_sync_runs WHERE run_id=:run_id"), {"run_id": run_id}).mappings().one()
        assert row["status"] == "succeeded"
        assert (row["fetched"], row["inserted"], row["updated"], row["duplicates"]) == (10, 3, 4, 3)
        assert "payload" not in row.keys()
    finally:
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM onbid_sync_runs WHERE run_id=:run_id"), {"run_id": run_id})
