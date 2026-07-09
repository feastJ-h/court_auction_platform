from __future__ import annotations

from _v007_helpers import configure_test_env, seed_items

TEST_DB_PATH = configure_test_env("product_copy_safety_test")

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.session import init_db  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    item_id, _ = seed_items()
    client = TestClient(app)
    for path in ("/", "/onbid", f"/onbid/{item_id}", "/cases"):
        response = client.get(path)
        assert response.status_code == 200, f"{path}: {response.status_code}"
        for phrase in ("AI 분석", "권리분석", "추천 물건", "수익률", "낙찰 보장", "전문가 보고서"):
            assert phrase not in response.text, f"{path} leaked banned public copy: {phrase}"
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - product copy safety")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
