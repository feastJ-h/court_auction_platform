from __future__ import annotations

from _v007_helpers import configure_test_env, seed_items

TEST_DB_PATH = configure_test_env("development_insight_cta_safety_test")

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.session import init_db  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    real_id, movable_id = seed_items()
    client = TestClient(app)
    real_page = client.get(f"/onbid/{real_id}")
    assert real_page.status_code == 200, real_page.status_code
    assert "개발 가능성 기초 검토" in real_page.text
    assert "사업성, 수익성, 법률 판단을 보장하지 않습니다" in real_page.text
    movable_page = client.get(f"/onbid/{movable_id}")
    assert movable_page.status_code == 200, movable_page.status_code
    assert "개발 가능성 기초 검토" not in movable_page.text
    insight = client.get(f"/onbid/{real_id}/development-insight")
    assert insight.status_code == 200, insight.status_code
    for phrase in ("수익성 확인", "개발 수익 계산", "낙찰 후 가치 상승 가능"):
        assert phrase not in insight.text
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - development insight CTA safety")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
