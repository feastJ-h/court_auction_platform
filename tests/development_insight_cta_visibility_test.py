from __future__ import annotations

from _v007_helpers import configure_test_env, seed_items

TEST_DB_PATH = configure_test_env("development_insight_cta_visibility_test")

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.session import init_db  # noqa: E402
from main_app import app  # noqa: E402


def main() -> int:
    init_db()
    real_id, movable_id = seed_items()
    client = TestClient(app)
    real = client.get(f"/onbid/{real_id}")
    movable = client.get(f"/onbid/{movable_id}")
    assert real.status_code == 200 and movable.status_code == 200
    assert 'data-development-insight-cta="true"' in real.text
    assert "개발 가능성 기초 검토" in real.text
    assert 'data-development-insight-cta="true"' not in movable.text
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - development insight CTA visibility")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
