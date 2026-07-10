from __future__ import annotations

from datetime import date, timedelta

from _v007_helpers import configure_test_env

TEST_DB_PATH = configure_test_env("onbid_today_excludes_ended_by_default_test")

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.models import AuctionItem  # noqa: E402
from backend.database.session import init_db, session_scope  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    today = date.today()
    with session_scope() as session:
        session.add_all([
            AuctionItem(source="ONBID", cltr_mng_no="ENDED", pbct_cdtn_no="1", item_name="Ended today queue", bid_end_at=(today - timedelta(days=1)).isoformat(), freshness_date=today.isoformat(), freshness_status="fresh", public_visible=True),
            AuctionItem(source="ONBID", cltr_mng_no="ACTIVE", pbct_cdtn_no="1", item_name="Active today queue", bid_end_at=(today + timedelta(days=1)).isoformat(), freshness_date=today.isoformat(), freshness_status="fresh", public_visible=True),
        ])
    page = TestClient(app).get("/onbid/today")
    assert page.status_code == 200
    assert "Active today queue" in page.text
    assert "Ended today queue" not in page.text
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - today excludes ended")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
