from __future__ import annotations

from _v007_helpers import configure_test_env, seed_items

TEST_DB_PATH = configure_test_env("onbid_original_link_prominence_test")

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.session import init_db  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    item_id, _ = seed_items()
    client = TestClient(app)
    for path in ("/onbid", f"/onbid/{item_id}"):
        response = client.get(path)
        assert response.status_code == 200, f"{path}: {response.status_code}"
        assert "원문 보기" in response.text
        assert 'rel="noopener noreferrer"' in response.text
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - original link prominence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
