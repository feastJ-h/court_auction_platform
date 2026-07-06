from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

TEST_DB_PATH = PROJECT_ROOT / "storage" / "test" / "onbid_category_filter_test.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DB_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["APP_SECRET_KEY"] = "onbid-category-test-secret"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from backend.database.models import AuctionItem  # noqa: E402
from backend.database.session import init_db, session_scope  # noqa: E402
from backend.services.auction_items import (  # noqa: E402
    build_onbid_info_badges,
    derive_onbid_category,
    get_onbid_category_label,
)
from backend.services.auth import ensure_initial_admin  # noqa: E402
from backend.workers.onbid_sync import run_onbid_sync  # noqa: E402
from main_app import app  # noqa: E402


def login_admin(client: TestClient):
    response = client.post(
        "/login",
        data={"username": "admin", "password": "admin1234!", "next_url": "/admin/collection"},
        follow_redirects=False,
    )
    assert response.status_code in (302, 303), response.status_code
    return response.cookies


def main() -> int:
    init_db()
    with session_scope() as session:
        ensure_initial_admin(session)

    assert run_onbid_sync(limit=20, sample=True, api_kind="real_estate")["status"] == "SUCCEEDED"
    assert run_onbid_sync(limit=20, sample=True, api_kind="movable")["status"] == "SUCCEEDED"
    assert run_onbid_sync(limit=20, sample=True, api_kind="national_property")["status"] == "SUCCEEDED"
    assert run_onbid_sync(
        limit=20,
        sample=True,
        api_kind="notice",
        include_notice_details=True,
        include_notice_items=True,
    )["status"] == "SUCCEEDED"

    with session_scope() as session:
        items = list(session.scalars(select(AuctionItem)))
        categories = {derive_onbid_category(item) for item in items}
        assert "real_estate" in categories, categories
        assert "movable" in categories, categories
        assert "national_property" in categories, categories
        national = next(item for item in items if derive_onbid_category(item) == "national_property")
        assert get_onbid_category_label("national_property") == "국유일반재산"
        badges = build_onbid_info_badges(national)
        assert "가격 정보 있음" in badges["available"], badges

    client = TestClient(app)
    response = client.get("/onbid?category=national_property")
    assert response.status_code == 200, response.status_code
    assert "National property sample asset" in response.text
    assert "검색 사이" not in response.text

    missing_response = client.get("/onbid?category=other&region=NoSuchRegion")
    assert missing_response.status_code == 200, missing_response.status_code
    assert "조건에 맞는 물건이 없습니다" in missing_response.text

    with session_scope() as session:
        same_notice_item = session.scalar(
            select(AuctionItem)
            .where(AuctionItem.cltr_mng_no == "NOTICE-CLTR-202607-A-001")
        )
        assert same_notice_item is not None
        same_notice_item_id = same_notice_item.id

    detail = client.get(f"/onbid/{same_notice_item_id}")
    assert detail.status_code == 200, detail.status_code
    assert "같은 공고의 다른 물건" in detail.text
    assert "검색 사이" not in detail.text

    cookies = login_admin(client)
    quality = client.get("/api/admin/onbid-quality", cookies=cookies)
    assert quality.status_code == 200, quality.text
    payload = quality.json()
    assert payload["categories"]["national_property"] >= 1, payload
    assert "price_missing_rate" in payload["missing"], payload

    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - ONBID v004 category, badges, same notice, national property")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
