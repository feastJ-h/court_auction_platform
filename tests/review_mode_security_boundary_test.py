from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

TEST_DB_PATH = PROJECT_ROOT / "storage" / "test" / "review_mode_security_boundary_test.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DB_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["APP_SECRET_KEY"] = "review-mode-test-secret"
os.environ["REVIEW_MODE"] = "true"

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.models import AuctionItem, RawDocument  # noqa: E402
from backend.database.session import init_db, session_scope  # noqa: E402
from backend.services.auth import create_user, ensure_initial_admin  # noqa: E402
from main_app import app  # noqa: E402


def login(client: TestClient, username: str, password: str, next_url: str):
    response = client.post("/login", data={"username": username, "password": password, "next_url": next_url}, follow_redirects=False)
    assert response.status_code in (302, 303), response.status_code
    return response.cookies


def main() -> int:
    init_db()
    raw_path = PROJECT_ROOT / "storage" / "test" / "review_raw.txt"
    raw_path.write_text("review raw", encoding="utf-8")
    with session_scope() as session:
        ensure_initial_admin(session)
        create_user(session, "review_user", "review1234!", "Review User", "user")
        item = AuctionItem(
            source="ONBID",
            cltr_mng_no="REVIEW-FRESH",
            pbct_cdtn_no="1",
            item_name="Review fresh item",
            asset_type="Real estate",
            bid_start_at="2025-05-01",
            bid_end_at="2025-05-02",
        )
        raw = RawDocument(file_path=str(raw_path), source_url="https://example.test/review", file_hash="review-raw-hash")
        session.add_all([item, raw])
        session.flush()
        item_id, raw_id = item.id, raw.id

    client = TestClient(app)
    page = client.get("/onbid")
    assert page.status_code == 200, page.status_code
    assert page.headers["x-review-mode"] == "true"
    assert "noindex" in page.headers["x-robots-tag"]
    assert 'data-review-mode="true"' in page.text

    user_cookies = login(client, "review_user", "review1234!", "/onbid")
    preference = client.post(f"/api/onbid/{item_id}/preference", cookies=user_cookies, json={"favorite": True})
    assert preference.status_code == 403, preference.status_code
    raw_response = client.get(f"/documents/raw/{raw_id}", cookies=user_cookies)
    assert raw_response.status_code == 403, raw_response.status_code

    admin_cookies = login(client, "admin", "admin1234!", "/admin/collection")
    sync = client.post("/api/admin/auctions/onbid/sync?sample=true&limit=20&max_pages=1&api_kind=real_estate&min_date=2025-01-01", cookies=admin_cookies)
    assert sync.status_code == 403, sync.status_code

    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - review mode security boundary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
