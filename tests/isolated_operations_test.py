from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
TEST_DB_PATH = PROJECT_ROOT / "storage" / "test" / "isolated_route_test.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DB_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["APP_SECRET_KEY"] = "isolated-test-secret"

from fastapi.testclient import TestClient
from sqlalchemy import select

from main_app import app
from backend.database.models import Asset, AssetEvent, RawDocument, UserEventAction
from backend.database.session import init_db, session_scope
from backend.services.auth import create_user, ensure_initial_admin


def seed_event() -> int:
    with session_scope() as session:
        ensure_initial_admin(session)
        create_user(session, "normal_user", "normal1234!", "일반 사용자", "user")
        raw = RawDocument(
            file_path=str(PROJECT_ROOT / "storage" / "raw_quarantine" / "isolated.pdf"),
            source_url="isolated://test",
            file_hash="isolated-test-hash",
        )
        asset = Asset(main_category="부동산", sub_category="테스트", address="서울 테스트")
        session.add_all([raw, asset])
        session.flush()
        event = AssetEvent(
            asset_id=asset.id,
            raw_doc_id=raw.id,
            case_number="TEST-OCR-001",
            status="LOCAL_INGESTED",
            title="격리 테스트 OCR 문서",
            url="isolated://event",
            notice_date="UNKNOWN",
            expire_date="UNKNOWN",
            parse_status="OCR_REQUIRED",
            extracted_text="",
        )
        session.add(event)
        session.flush()
        return event.id


def main() -> int:
    init_db()
    event_id = seed_event()
    client = TestClient(app)
    login = client.post(
        "/login",
        data={"username": "admin", "password": "admin1234!", "next_url": "/admin"},
        follow_redirects=False,
    )
    assert login.status_code in (302, 303), login.status_code
    cookies = login.cookies

    metadata_response = client.post(
        f"/admin/events/{event_id}/metadata",
        cookies=cookies,
        data={
            "notice_date": "2026-07-05",
            "expire_date": "2026-08-05",
            "parse_status": "OCR_REQUIRED",
            "title": "격리 테스트 보정 문서",
        },
        follow_redirects=False,
    )
    assert metadata_response.status_code in (302, 303), metadata_response.status_code

    ocr_response = client.post(
        f"/api/admin/events/{event_id}/ocr/jobs?force=true",
        cookies=cookies,
    )
    assert ocr_response.status_code == 200, ocr_response.text
    assert ocr_response.json()["status"] == "queued", ocr_response.json()

    status_response = client.get("/api/admin/ocr/status", cookies=cookies)
    assert status_response.status_code == 200, status_response.text
    assert status_response.json()["engine"] == "tesseract", status_response.json()

    admin_page = client.get("/user", cookies=cookies)
    assert admin_page.status_code == 200, admin_page.status_code
    assert "Admin" in admin_page.text

    normal_login = client.post(
        "/login",
        data={"username": "normal_user", "password": "normal1234!", "next_url": "/user"},
        follow_redirects=False,
    )
    assert normal_login.status_code in (302, 303), normal_login.status_code
    normal_cookies = normal_login.cookies
    normal_page = client.get("/user", cookies=normal_cookies)
    assert normal_page.status_code == 200, normal_page.status_code
    assert "Admin" not in normal_page.text

    for route in ("bookmark", "watch", "pass"):
        action_response = client.post(
            f"/user/events/{event_id}/{route}",
            cookies=normal_cookies,
            follow_redirects=False,
        )
        assert action_response.status_code in (302, 303), action_response.status_code

    with session_scope() as session:
        actions = list(
            session.scalars(
                select(UserEventAction).where(UserEventAction.event_id == event_id)
            )
        )
        assert len(actions) == 1, [action.action_type for action in actions]
        assert actions[0].action_type == "PASSED", actions[0].action_type

    basic_analysis_response = client.post(
        f"/api/admin/events/{event_id}/basic-analysis",
        cookies=cookies,
    )
    assert basic_analysis_response.status_code == 422, basic_analysis_response.text

    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - isolated role menu, exclusive actions, OCR and basic analysis guard routes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
