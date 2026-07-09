from __future__ import annotations

from _v007_helpers import configure_test_env, seed_items

TEST_DB_PATH = configure_test_env("onbid_data_issue_report_test")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from backend.database.models import OnbidDataIssueReport  # noqa: E402
from backend.database.session import init_db, session_scope  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    item_id, _ = seed_items()
    client = TestClient(app)
    response = client.post(
        f"/onbid/{item_id}/issue-report",
        data={"issue_type": ["price", "personal_info"], "note": "가격 확인 필요", "next_url": f"/onbid/{item_id}"},
        follow_redirects=False,
    )
    assert response.status_code in (302, 303), response.status_code
    public = client.get(f"/onbid/{item_id}")
    assert "가격 확인 필요" not in public.text
    with session_scope() as session:
        report = session.scalar(select(OnbidDataIssueReport))
        assert report is not None
        assert report.status == "pending"
        assert report.contains_personal_info is True
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - ONBID data issue report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
