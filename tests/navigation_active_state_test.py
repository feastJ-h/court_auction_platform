from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

TEST_DB_PATH = PROJECT_ROOT / "storage" / "test" / "navigation_active_state_test.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DB_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["APP_SECRET_KEY"] = "navigation-active-test-secret"

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.models import Asset, AssetEvent, AuctionItem, RawDocument  # noqa: E402
from backend.database.session import init_db, session_scope  # noqa: E402
from backend.services.auth import create_user, ensure_initial_admin  # noqa: E402
from main_app import app  # noqa: E402


def seed() -> tuple[int, int]:
    with session_scope() as session:
        ensure_initial_admin(session)
        create_user(session, "nav_user", "nav1234!", "Nav User", "user")
        auction = AuctionItem(
            source="ONBID",
            cltr_mng_no="NAV-REAL",
            pbct_cdtn_no="1",
            item_name="Navigation real estate item",
            asset_type="Real estate",
            bid_start_at="2025-02-01",
            bid_end_at="2025-02-10",
            minimum_bid_price=10,
            freshness_status="fresh",
            public_visible=True,
        )
        raw = RawDocument(file_path="storage/test/nav.txt", source_url="https://example.test/nav", file_hash="nav-hash")
        asset = Asset(main_category="부동산", sub_category="office", address="Seoul")
        session.add_all([auction, raw, asset])
        session.flush()
        event = AssetEvent(
            asset_id=asset.id,
            raw_doc_id=raw.id,
            case_number="NAV-CASE-001",
            status="OPEN",
            title="Navigation case",
            url="https://example.test/nav-case",
            notice_date="2026-07-01",
            expire_date="2026-08-01",
            parse_status="TEXT_PARSED",
            extracted_text="internal",
        )
        session.add(event)
        session.flush()
        return auction.id, event.id


def login(client: TestClient, username: str, password: str, next_url: str):
    response = client.post("/login", data={"username": username, "password": password, "next_url": next_url}, follow_redirects=False)
    assert response.status_code in (302, 303), response.status_code
    return response.cookies


def assert_active(response, section: str, category: str = "", subsection: str = "") -> None:
    assert response.status_code == 200, response.status_code
    assert f'data-active-section="{section}"' in response.text, response.text[:500]
    if category:
        assert f'data-active-category="{category}"' in response.text, response.text[:500]
    if subsection:
        assert f'data-active-subsection="{subsection}"' in response.text, response.text[:500]


def assert_nav_markers(text: str, expect_local_scope: bool) -> None:
    assert 'data-nav-scope="global"' in text
    if expect_local_scope:
        assert 'data-nav-scope="local-filter"' in text


def main() -> int:
    init_db()
    auction_id, event_id = seed()
    client = TestClient(app)

    home = client.get("/")
    assert_active(home, "home")

    onbid = client.get("/onbid")
    assert_active(onbid, "onbid", "all")
    assert_nav_markers(onbid.text, expect_local_scope=True)

    onbid_filtered = client.get("/onbid?category=movable")
    assert_active(onbid_filtered, "onbid", "movable")
    assert_nav_markers(onbid_filtered.text, expect_local_scope=True)

    assert onbid_filtered.text.count('data-nav-scope="global"') == 1, onbid_filtered.text[:300]

    onbid_detail = client.get(f"/onbid/{auction_id}")
    assert_active(onbid_detail, "onbid", "real_estate")
    assert_nav_markers(onbid_detail.text, expect_local_scope=True)

    cases = client.get("/cases")
    assert_active(cases, "cases")
    assert_nav_markers(cases.text, expect_local_scope=True)

    case_detail = client.get(f"/cases/{event_id}")
    assert_active(case_detail, "cases")
    assert_nav_markers(case_detail.text, expect_local_scope=False)

    privacy = client.get("/privacy")
    assert_active(privacy, "legal", subsection="privacy")
    assert_nav_markers(privacy.text, expect_local_scope=False)

    user_cookies = login(client, "nav_user", "nav1234!", "/my/onbid/favorites")
    favorites = client.get("/my/onbid/favorites", cookies=user_cookies)
    assert_active(favorites, "my", subsection="favorites")
    passed = client.get("/my/onbid/passed", cookies=user_cookies)
    assert_active(passed, "my", subsection="passed")
    watching = client.get("/my/onbid/watching", cookies=user_cookies)
    assert_active(watching, "my", subsection="watching")

    admin_cookies = login(client, "admin", "admin1234!", "/admin/collection")
    admin_collection = client.get("/admin/collection", cookies=admin_cookies)
    assert_active(admin_collection, "admin", subsection="collection")
    admin_operations = client.get("/admin/operations-readiness", cookies=admin_cookies)
    assert_active(admin_operations, "admin", subsection="operations_readiness")
    admin_runs = client.get("/admin/onbid-runs", cookies=admin_cookies)
    assert_active(admin_runs, "admin", subsection="run_history")

    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - navigation active state markers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
