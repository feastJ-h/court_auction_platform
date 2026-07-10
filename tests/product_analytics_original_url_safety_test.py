from __future__ import annotations

from _v007_helpers import configure_test_env, create_login_user, seed_items

TEST_DB_PATH = configure_test_env("product_analytics_original_url_safety_test")

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
    response = client.get(f"/onbid/{item_id}/original-link", cookies=cookies, follow_redirects=False)
    assert response.status_code == 303
    with session_scope() as session:
        event = session.scalar(select(ProductAnalyticsEvent).where(ProductAnalyticsEvent.event_name == "click_original_link"))
        assert event is not None
        assert "example.test" not in event.metadata_json
        assert "url" not in event.metadata_json.lower()
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - analytics original URL safety")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
