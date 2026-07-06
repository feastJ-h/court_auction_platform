from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
TEST_DB_PATH = PROJECT_ROOT / "storage" / "test" / "onbid_module_test.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DB_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["APP_SECRET_KEY"] = "onbid-test-secret"

from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.database.models import (
    Asset,
    AssetEvent,
    AuctionItem,
    AuctionNotice,
    AuctionNoticeItemLink,
    CaseAuctionLink,
    RawDocument,
)
from backend.database.session import init_db, session_scope
from backend.services.auth import ensure_initial_admin
from backend.workers.onbid_sync import run_onbid_sync
from main_app import app


def seed_case_event() -> int:
    with session_scope() as session:
        ensure_initial_admin(session)
        raw = RawDocument(
            file_path=str(PROJECT_ROOT / "storage" / "raw_quarantine" / "onbid-case.pdf"),
            source_url="isolated://onbid-case",
            file_hash="onbid-case-hash",
        )
        asset = Asset(main_category="ONBID", sub_category="sample", address="Seoul Jongno-gu sample 1")
        session.add_all([raw, asset])
        session.flush()
        event = AssetEvent(
            asset_id=asset.id,
            raw_doc_id=raw.id,
            case_number="TEST-ONBID-CASE-001",
            status="AI_ANALYZED",
            title="ONBID sample recovery case",
            url="isolated://onbid-event",
            notice_date="2026-07-05",
            expire_date="2026-08-05",
            parse_status="TEXT_PARSED",
            extracted_text="ONBID sample recovery text",
        )
        session.add(event)
        session.flush()
        return event.id


def assert_onbid_sample_sync() -> None:
    sync_result = run_onbid_sync(limit=20, sample=True)
    assert sync_result["status"] == "SUCCEEDED", sync_result
    assert sync_result["inserted"] == 3, sync_result

    detail_sync_result = run_onbid_sync(limit=1, sample=True, include_details=True)
    assert detail_sync_result["status"] == "SUCCEEDED", detail_sync_result
    assert detail_sync_result["duplicates"] == 1, detail_sync_result

    movable_sync_result = run_onbid_sync(limit=20, sample=True, api_kind="movable")
    assert movable_sync_result["status"] == "SUCCEEDED", movable_sync_result
    assert movable_sync_result["inserted"] == 2, movable_sync_result

    notice_sync_result = run_onbid_sync(
        limit=20,
        sample=True,
        api_kind="notice",
        include_notice_details=True,
        include_notice_items=True,
    )
    assert notice_sync_result["status"] == "SUCCEEDED", notice_sync_result
    assert notice_sync_result["notices_inserted"] == 2, notice_sync_result
    assert notice_sync_result["notice_items_inserted"] == 3, notice_sync_result
    assert notice_sync_result["notice_item_links_created"] == 3, notice_sync_result

    notice_resync_result = run_onbid_sync(
        limit=20,
        sample=True,
        api_kind="notice",
        include_notice_details=True,
        include_notice_items=True,
    )
    assert notice_resync_result["status"] == "SUCCEEDED", notice_resync_result
    assert notice_resync_result["notices_updated"] == 2, notice_resync_result
    assert notice_resync_result["notice_items_duplicates"] == 3, notice_resync_result
    assert notice_resync_result["notice_item_links_updated"] == 3, notice_resync_result


def main() -> int:
    init_db()
    event_id = seed_case_event()
    assert_onbid_sample_sync()

    with session_scope() as session:
        auction_item = session.scalar(select(AuctionItem).order_by(AuctionItem.id.asc()))
        assert auction_item is not None
        auction_item_id = auction_item.id
        total_items = len(list(session.scalars(select(AuctionItem))))
        notice_count = len(list(session.scalars(select(AuctionNotice))))
        notice_link_count = len(list(session.scalars(select(AuctionNoticeItemLink))))
        assert total_items == 8, total_items
        assert notice_count == 7, notice_count
        assert notice_link_count == 3, notice_link_count

    client = TestClient(app)
    login = client.post(
        "/login",
        data={"username": "admin", "password": "admin1234!", "next_url": "/auctions"},
        follow_redirects=False,
    )
    assert login.status_code in (302, 303), login.status_code
    cookies = login.cookies

    for path in ("/auctions", f"/auctions/{auction_item_id}", "/admin/assets", "/admin/analysis", "/admin/reviews"):
        page = client.get(path, cookies=cookies)
        assert page.status_code == 200, path

    collection_page = client.get("/admin/collection", cookies=cookies)
    assert collection_page.status_code == 200, collection_page.status_code
    assert "온비드 공매 수집" in collection_page.text
    assert "온비드 데이터 품질" in collection_page.text

    onbid_quality_response = client.get("/api/admin/onbid-quality", cookies=cookies)
    assert onbid_quality_response.status_code == 200, onbid_quality_response.text
    onbid_quality = onbid_quality_response.json()
    assert onbid_quality["items"]["total"] == 8, onbid_quality
    assert onbid_quality["notices"]["total"] == 7, onbid_quality
    assert onbid_quality["links"]["notice_item_links"] == 3, onbid_quality

    link_response = client.post(
        f"/api/admin/auctions/{auction_item_id}/links",
        cookies=cookies,
        json={"case_id": event_id, "memo": "manual test link"},
    )
    assert link_response.status_code == 200, link_response.text
    assert link_response.json()["status"] == "linked"

    with session_scope() as session:
        link_count = len(list(session.scalars(select(CaseAuctionLink))))
        assert link_count == 1, link_count

    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - ONBID item, notice, observability, and case link")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
