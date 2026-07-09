from __future__ import annotations

from _v007_helpers import configure_test_env, create_login_user, seed_items

TEST_DB_PATH = configure_test_env("onbid_shared_summary_manage_test")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from backend.database.models import OnbidReviewSummaryShare  # noqa: E402
from backend.database.session import init_db, session_scope  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    item_id, _ = seed_items()
    client = TestClient(app)
    cookies = create_login_user(client, "v008_share_user")
    created = client.post(f"/onbid/{item_id}/review-summary", cookies=cookies, follow_redirects=False)
    assert created.status_code in (302, 303), created.status_code
    page = client.get("/my/onbid/shared-summaries", cookies=cookies)
    assert page.status_code == 200, page.status_code
    assert "공유 요약 관리" in page.text
    with session_scope() as session:
        token = session.scalar(select(OnbidReviewSummaryShare.token))
    revoked = client.post(f"/my/onbid/shared-summaries/{token}/revoke", cookies=cookies, follow_redirects=False)
    assert revoked.status_code in (302, 303), revoked.status_code
    share = client.get(f"/onbid/share/{token}")
    assert share.status_code == 404, share.status_code
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - shared summary manage")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
