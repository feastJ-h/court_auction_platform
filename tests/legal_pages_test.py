from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

TEST_DB_PATH = PROJECT_ROOT / "storage" / "test" / "legal_pages_test.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DB_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["APP_SECRET_KEY"] = "legal-pages-test-secret"

from fastapi.testclient import TestClient  # noqa: E402
from backend.database.session import init_db  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    client = TestClient(app)
    for path, marker in (("/privacy", "/privacy"), ("/terms", "/terms"), ("/disclaimer", "/disclaimer")):
        response = client.get(path)
        assert response.status_code == 200, f"{path}: {response.status_code}"
        assert 'data-active-section="legal"' in response.text, path
        assert f'href="{marker}"' in response.text, path
        assert 'href="/privacy"' in response.text, path
        assert 'href="/terms"' in response.text, path
        assert 'href="/disclaimer"' in response.text, path
        assert "beta" in response.text.lower() or "초안" in response.text, path
        assert "개인정보" in response.text or "privacy" in response.text.lower(), path

    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - legal pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
