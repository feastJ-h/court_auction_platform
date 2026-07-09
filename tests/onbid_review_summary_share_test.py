from __future__ import annotations

from _v007_helpers import configure_test_env, create_login_user, seed_items

TEST_DB_PATH = configure_test_env("onbid_review_summary_share_test")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from backend.database.models import OnbidReviewSummaryShare  # noqa: E402
from backend.database.session import init_db, session_scope  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    item_id, _ = seed_items()
    client = TestClient(app)
    login_required = client.post(f"/onbid/{item_id}/review-summary", follow_redirects=False)
    assert login_required.status_code in (302, 303), login_required.status_code
    cookies = create_login_user(client)
    client.post(
        f"/api/onbid/{item_id}/preference",
        cookies=cookies,
        json={"note": "PRIVATE MEMO SHOULD NOT LEAK", "favorite": True},
    )
    created = client.post(f"/onbid/{item_id}/review-summary", cookies=cookies, follow_redirects=False)
    assert created.status_code in (302, 303), created.status_code
    with session_scope() as session:
        share = session.scalar(select(OnbidReviewSummaryShare))
        assert share is not None
        token = share.token
    page = client.get(f"/onbid/share/{token}")
    assert page.status_code == 200, page.status_code
    assert page.headers.get("X-Robots-Tag") == "noindex, noarchive"
    assert "V007 complete real estate" in page.text
    assert "PRIVATE MEMO SHOULD NOT LEAK" not in page.text
    assert "raw_payload" not in page.text
    assert "AI 분석" not in page.text
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - ONBID review summary share")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
