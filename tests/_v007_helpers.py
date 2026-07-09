from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def configure_test_env(name: str) -> Path:
    db_path = PROJECT_ROOT / "storage" / "test" / f"{name}.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    os.environ["DB_URL"] = f"sqlite:///{db_path}"
    os.environ["APP_SECRET_KEY"] = f"{name}-secret"
    os.environ["REVIEW_MODE"] = "false"
    os.environ["LOCAL_DEV_LOGIN_HINT"] = "false"
    return db_path


def seed_items():
    from backend.database.models import AuctionItem, AuctionNotice, AuctionNoticeItemLink
    from backend.database.session import session_scope

    today = date.today().isoformat()
    next_week = (date.today() + timedelta(days=7)).isoformat()
    with session_scope() as session:
        complete = AuctionItem(
            source="ONBID",
            cltr_mng_no="V007-COMPLETE",
            pbct_cdtn_no="1",
            item_name="V007 complete real estate",
            asset_type="부동산",
            address="서울 중구 테스트로 1",
            appraisal_price=150000000,
            minimum_bid_price=100000000,
            bid_start_at=today,
            bid_end_at=next_week,
            status="입찰중",
            agency_name="KAMCO",
            item_description="공개 자료 기준 상세 설명",
            attachment_summary="공고문",
            land_area="100㎡",
            building_area="80㎡",
            public_category="real_estate",
            freshness_date=today,
            freshness_status="fresh",
            public_visible=True,
        )
        sparse = AuctionItem(
            source="ONBID",
            cltr_mng_no="V007-SPARSE",
            pbct_cdtn_no="1",
            item_name="V007 sparse movable",
            asset_type="동산",
            address="",
            appraisal_price=0,
            minimum_bid_price=0,
            bid_start_at=today,
            bid_end_at="",
            status="입찰중",
            agency_name="KAMCO",
            public_category="movable",
            freshness_date=today,
            freshness_status="fresh",
            public_visible=True,
        )
        session.add_all([complete, sparse])
        session.flush()
        notice = AuctionNotice(
            source="ONBID",
            pbanc_mng_no="V007-NOTICE",
            notice_no="V007-NOTICE",
            notice_title="V007 notice",
            detail_url="https://example.test/onbid-source",
        )
        session.add(notice)
        session.flush()
        session.add(
            AuctionNoticeItemLink(
                source="ONBID",
                notice_id=notice.id,
                auction_item_id=complete.id,
                notice_no=notice.notice_no,
                pbanc_mng_no=notice.pbanc_mng_no,
                cltr_mng_no=complete.cltr_mng_no,
                pbct_cdtn_no=complete.pbct_cdtn_no,
            )
        )
        session.flush()
        return complete.id, sparse.id


def create_login_user(client, username: str = "v007_user"):
    from backend.database.session import session_scope
    from backend.services.auth import create_user

    password = "v007-user-pass!"
    with session_scope() as session:
        create_user(session, username, password, "V007 User", "user")
    response = client.post(
        "/login",
        data={"username": username, "password": password, "next_url": "/onbid"},
        follow_redirects=False,
    )
    assert response.status_code in (302, 303), response.status_code
    return response.cookies
