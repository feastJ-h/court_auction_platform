from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

TEST_DB_PATH = PROJECT_ROOT / "storage" / "test" / "public_access_auth_boundary_test.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DB_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["APP_SECRET_KEY"] = "public-boundary-test-secret"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from backend.database.models import (  # noqa: E402
    AiAnalysis,
    Asset,
    AssetEvent,
    AuctionItem,
    RawDocument,
    UserAuctionPreference,
)
from backend.database.session import init_db, session_scope  # noqa: E402
from backend.services.auth import create_user, ensure_initial_admin  # noqa: E402
from main_app import app  # noqa: E402


def seed_data() -> tuple[int, int, int]:
    raw_file = PROJECT_ROOT / "storage" / "test" / "public_boundary_raw.txt"
    raw_file.write_text("INTERNAL RAW FILE TEXT", encoding="utf-8")
    with session_scope() as session:
        ensure_initial_admin(session)
        user = create_user(session, "public_user", "public1234!", "공개 테스트 사용자", "user")
        raw = RawDocument(
            file_path=str(raw_file),
            source_url="https://example.test/source-notice",
            file_hash="public-boundary-hash",
        )
        asset = Asset(main_category="부동산", sub_category="테스트", address="서울 공개 테스트")
        session.add_all([raw, asset])
        session.flush()
        event = AssetEvent(
            asset_id=asset.id,
            raw_doc_id=raw.id,
            case_number="PUBLIC-CASE-001",
            status="AI_ANALYZED",
            title="공개 경계 테스트 사건",
            url="https://example.test/case",
            notice_date="2026-07-06",
            expire_date="2026-08-06",
            parse_status="TEXT_PARSED",
            extracted_text="SECRET OCR BODY SHOULD NOT LEAK",
        )
        session.add(event)
        session.flush()
        session.add(
            AiAnalysis(
                event_id=event.id,
                item_details="SECRET AI ITEM DETAILS",
                min_price="123456",
                bidding_date="2026-08-01",
                risk_comment="SECRET AI RISK",
                detailed_analysis="SECRET DEEP AI ANALYSIS",
            )
        )
        auction_item = AuctionItem(
            source="ONBID",
            cltr_mng_no="PUB-CLTR-001",
            pbct_cdtn_no="PUB-PBCT-CDTN-001",
            item_name="공개 온비드 테스트 물건",
            asset_type="부동산",
            address="서울 온비드 테스트",
            appraisal_price=100000000,
            minimum_bid_price=70000000,
            bid_start_at="2026-07-10",
            bid_end_at="2026-07-20",
            status="입찰중",
            agency_name="테스트 기관",
            item_description="공개 가능한 온비드 상세",
        )
        session.add(auction_item)
        session.flush()
        return event.id, auction_item.id, raw.id


def login_user(client: TestClient):
    response = client.post(
        "/login",
        data={"username": "public_user", "password": "public1234!", "next_url": "/onbid"},
        follow_redirects=False,
    )
    assert response.status_code in (302, 303), response.status_code
    return response.cookies


def main() -> int:
    init_db()
    event_id, auction_item_id, raw_doc_id = seed_data()
    client = TestClient(app)

    for path in ("/", "/onbid", f"/onbid/{auction_item_id}", "/cases", f"/cases/{event_id}", "/about", "/disclaimer", "/robots.txt", "/sitemap.xml"):
        response = client.get(path)
        assert response.status_code == 200, f"{path}: {response.status_code}"

    case_page = client.get(f"/cases/{event_id}")
    assert "SECRET AI" not in case_page.text
    assert "SECRET OCR" not in case_page.text
    assert "documents/raw" not in case_page.text
    assert "public_boundary_raw" not in case_page.text
    assert "https://example.test/case" in case_page.text

    raw_response = client.get(f"/documents/raw/{raw_doc_id}")
    assert raw_response.status_code == 401, raw_response.status_code

    admin_page = client.get("/admin", follow_redirects=False)
    assert admin_page.status_code in (302, 303), admin_page.status_code
    admin_api = client.get("/api/admin/onbid-quality")
    assert admin_api.status_code == 401, admin_api.status_code

    preference_post = client.post(
        f"/onbid/{auction_item_id}/preference",
        data={"action": "favorite", "enabled": "true", "next_url": f"/onbid/{auction_item_id}"},
        follow_redirects=False,
    )
    assert preference_post.status_code in (302, 303), preference_post.status_code
    assert "/login" in preference_post.headers["location"]

    preference_api = client.post(f"/api/onbid/{auction_item_id}/preference", json={"favorite": True})
    assert preference_api.status_code == 401, preference_api.status_code

    with session_scope() as session:
        assert session.scalar(select(UserAuctionPreference)) is None

    cookies = login_user(client)
    saved = client.post(
        f"/api/onbid/{auction_item_id}/preference",
        cookies=cookies,
        json={"favorite": True, "watching": True, "note": "검토 메모"},
    )
    assert saved.status_code == 200, saved.text
    payload = saved.json()["preference"]
    assert payload["is_favorite"] is True
    assert payload["is_watching"] is True
    assert payload["is_passed"] is False

    with session_scope() as session:
        preference = session.scalar(select(UserAuctionPreference))
        assert preference is not None
        assert preference.is_favorite is True
        assert preference.is_watching is True
        assert preference.note == "검토 메모"

    my_page = client.get("/my/onbid/favorites", cookies=cookies)
    assert my_page.status_code == 200, my_page.status_code
    assert "공개 온비드 테스트 물건" in my_page.text

    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - public access and auth boundary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
