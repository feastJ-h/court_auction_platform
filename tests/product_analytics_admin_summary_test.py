from __future__ import annotations

from _v007_helpers import configure_test_env, seed_items

TEST_DB_PATH = configure_test_env("product_analytics_admin_summary_test")

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.session import init_db, session_scope  # noqa: E402
from backend.services.auth import ensure_initial_admin  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    item_id, _ = seed_items()
    client = TestClient(app)
    client.get("/onbid/today")
    client.get(f"/onbid/{item_id}/original-link", follow_redirects=False)
    with session_scope() as session:
        ensure_initial_admin(session)
    login = client.post("/login", data={"username": "admin", "password": "admin1234!", "next_url": "/admin/product-analytics"}, follow_redirects=False)
    page = client.get("/admin/product-analytics", cookies=login.cookies)
    assert page.status_code == 200, page.status_code
    assert "제품 사용 요약" in page.text
    assert "raw_payload" not in page.text
    assert "private memo" not in page.text.lower()
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - product analytics admin summary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
