from __future__ import annotations

from _v007_helpers import configure_test_env, create_login_user, seed_items

TEST_DB_PATH = configure_test_env("onbid_today_review_completion_test")

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.session import init_db  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    complete_id, sparse_id = seed_items()
    client = TestClient(app)
    anonymous = client.get("/onbid/today")
    assert anonymous.status_code == 200, anonymous.status_code
    assert 'action="/onbid/' not in anonymous.text
    assert "/login?next=/onbid/today" in anonymous.text

    cookies = create_login_user(client)
    before = client.get("/onbid/today", cookies=cookies)
    assert before.status_code == 200, before.status_code
    assert "오늘 새로 확인할 공매 정보를 모두 정리했습니다" not in before.text
    client.post(f"/onbid/{complete_id}/preference", cookies=cookies, data={"action": "favorite", "enabled": "true", "next_url": "/onbid/today"}, follow_redirects=False)
    client.post(f"/onbid/{sparse_id}/preference", cookies=cookies, data={"action": "passed", "enabled": "true", "next_url": "/onbid/today"}, follow_redirects=False)
    after = client.get("/onbid/today", cookies=cookies)
    assert after.status_code == 200, after.status_code
    assert "오늘 새로 확인할 공매 정보를 모두 정리했습니다" in after.text
    assert "2건 중 1건을 패스하고 1건을 관심" in after.text
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - ONBID today review completion")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
