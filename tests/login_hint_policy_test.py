from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

TEST_DB_PATH = PROJECT_ROOT / "storage" / "test" / "login_hint_policy_test.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DB_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["APP_SECRET_KEY"] = "login-hint-test-secret"

from fastapi.testclient import TestClient  # noqa: E402

from backend.config import get_settings  # noqa: E402
from backend.database.session import init_db  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    client = TestClient(app)

    os.environ.pop("LOCAL_DEV_LOGIN_HINT", None)
    os.environ.pop("REVIEW_MODE", None)
    get_settings.cache_clear()
    public_login = client.get("/login")
    assert public_login.status_code == 200, public_login.status_code
    assert "admin1234!" not in public_login.text

    os.environ["LOCAL_DEV_LOGIN_HINT"] = "true"
    os.environ["REVIEW_MODE"] = "false"
    get_settings.cache_clear()
    local_login = client.get("/login")
    assert "admin / admin1234!" in local_login.text

    os.environ["REVIEW_MODE"] = "true"
    get_settings.cache_clear()
    review_login = client.get("/login")
    assert "admin1234!" not in review_login.text

    os.environ.pop("LOCAL_DEV_LOGIN_HINT", None)
    os.environ.pop("REVIEW_MODE", None)
    get_settings.cache_clear()

    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - login hint policy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
