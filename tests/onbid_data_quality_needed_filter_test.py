from __future__ import annotations

from _v007_helpers import configure_test_env, seed_items

TEST_DB_PATH = configure_test_env("onbid_data_quality_needed_filter_test")

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.session import init_db  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    _, sparse_id = seed_items()
    client = TestClient(app)
    response = client.get("/onbid?data_quality=needs_confirmation")
    assert response.status_code == 200, response.status_code
    assert "V007 sparse movable" in response.text
    assert "V007 complete real estate" not in response.text
    assert "자료 확인 필요" in response.text or "?먮즺 ?뺤씤 ?꾩슂" in response.text
    detail = client.get(f"/onbid/{sparse_id}")
    assert detail.status_code == 200, detail.status_code
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - ONBID data quality needed filter")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
