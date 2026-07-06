from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

TEST_DB_PATH = PROJECT_ROOT / "storage" / "test" / "admin_readiness_dashboard_test.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DB_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["APP_SECRET_KEY"] = "admin-readiness-test-secret"

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.models import AuctionItem  # noqa: E402
from backend.database.session import init_db, session_scope  # noqa: E402
from backend.services.auth import ensure_initial_admin  # noqa: E402
from main_app import app  # noqa: E402


def login_admin(client: TestClient):
    response = client.post("/login", data={"username": "admin", "password": "admin1234!", "next_url": "/admin/collection"}, follow_redirects=False)
    assert response.status_code in (302, 303), response.status_code
    return response.cookies


def main() -> int:
    init_db()
    with session_scope() as session:
        ensure_initial_admin(session)
        session.add_all(
            [
                AuctionItem(source="ONBID", cltr_mng_no="ADMIN-FRESH", pbct_cdtn_no="1", item_name="Admin fresh", asset_type="Real estate", bid_start_at="2025-06-01"),
                AuctionItem(source="ONBID", cltr_mng_no="ADMIN-STALE", pbct_cdtn_no="1", item_name="Admin stale", asset_type="Real estate", bid_start_at="2024-06-01"),
            ]
        )

    client = TestClient(app)
    cookies = login_admin(client)
    readiness = client.get("/admin/operations-readiness", cookies=cookies)
    assert readiness.status_code == 200, readiness.status_code
    assert 'data-active-section="admin"' in readiness.text
    assert 'data-active-subsection="operations_readiness"' in readiness.text

    runs = client.get("/admin/onbid-runs", cookies=cookies)
    assert runs.status_code == 200, runs.status_code
    assert 'data-active-subsection="run_history"' in runs.text
    assert 'data-onbid-freshness-audit="true"' in runs.text

    quality = client.get("/api/admin/onbid-quality", cookies=cookies)
    assert quality.status_code == 200, quality.text
    payload = quality.json()
    assert payload["freshness"]["fresh"] == 1, payload
    assert payload["freshness"]["stale"] == 1, payload

    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - admin readiness and run history")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
