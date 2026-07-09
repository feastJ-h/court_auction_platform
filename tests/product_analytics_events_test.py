from __future__ import annotations

from _v007_helpers import configure_test_env, create_login_user, seed_items

TEST_DB_PATH = configure_test_env("product_analytics_events_test")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from backend.database.models import ProductAnalyticsEvent  # noqa: E402
from backend.database.session import init_db, session_scope  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    item_id, _ = seed_items()
    client = TestClient(app)
    cookies = create_login_user(client)
    client.get("/onbid/today", cookies=cookies)
    client.post(f"/onbid/{item_id}/preference", cookies=cookies, data={"action": "favorite", "enabled": "true", "next_url": f"/onbid/{item_id}"}, follow_redirects=False)
    client.get(f"/onbid/{item_id}/original-link", cookies=cookies, follow_redirects=False)
    client.post(f"/onbid/{item_id}/issue-report", cookies=cookies, data={"issue_type": "price", "note": "do not store raw memo"}, follow_redirects=False)
    client.post(f"/onbid/{item_id}/review-summary", cookies=cookies, follow_redirects=False)
    client.post(f"/onbid/{item_id}/development-insight", cookies=cookies, follow_redirects=False)
    with session_scope() as session:
        events = list(session.scalars(select(ProductAnalyticsEvent)))
        names = {event.event_name for event in events}
        assert {"view_today_queue", "favorite_item", "click_original_link", "submit_data_issue", "create_review_summary", "click_development_insight_cta"}.issubset(names)
        for event in events:
            assert "do not store raw memo" not in event.metadata_json
            assert "raw_payload" not in event.metadata_json
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - product analytics events")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
