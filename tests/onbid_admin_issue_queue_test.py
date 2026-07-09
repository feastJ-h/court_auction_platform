from __future__ import annotations

from _v007_helpers import configure_test_env, seed_items

TEST_DB_PATH = configure_test_env("onbid_admin_issue_queue_test")

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.session import init_db, session_scope  # noqa: E402
from backend.services.auth import ensure_initial_admin  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    item_id, _ = seed_items()
    client = TestClient(app)
    client.post(f"/onbid/{item_id}/issue-report", data={"issue_type": ["price"], "note": "가격 확인 필요"}, follow_redirects=False)
    with session_scope() as session:
        ensure_initial_admin(session)
    login = client.post("/login", data={"username": "admin", "password": "admin1234!", "next_url": "/admin/onbid-issue-reports"}, follow_redirects=False)
    cookies = login.cookies
    page = client.get("/admin/onbid-issue-reports", cookies=cookies)
    assert page.status_code == 200, page.status_code
    assert "ONBID 오류 제보" in page.text
    assert "개인정보 의심" not in page.text
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - admin issue queue")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
