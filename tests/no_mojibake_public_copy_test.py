from __future__ import annotations

from _v007_helpers import configure_test_env, seed_items

TEST_DB_PATH = configure_test_env("no_mojibake_public_copy_test")

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.session import init_db  # noqa: E402
from main_app import app  # noqa: E402


MOJIBAKE_MARKERS = ("占", "癒", "揶", "媛", "怨", "留", "�")


def main() -> int:
    init_db()
    item_id, _ = seed_items()
    client = TestClient(app)
    for path in ("/", "/onbid", "/onbid/today", f"/onbid/{item_id}", "/disclaimer"):
        response = client.get(path)
        assert response.status_code == 200, f"{path}: {response.status_code}"
        for marker in MOJIBAKE_MARKERS:
            assert marker not in response.text, f"{path} contains mojibake marker {marker}"
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - no mojibake public copy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
