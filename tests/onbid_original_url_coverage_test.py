from __future__ import annotations

from _v007_helpers import configure_test_env, seed_items

TEST_DB_PATH = configure_test_env("onbid_original_url_coverage_test")

from backend.database.session import init_db, session_scope  # noqa: E402
from backend.services.onbid_observability import build_onbid_data_quality_summary  # noqa: E402


def main() -> int:
    init_db()
    seed_items()
    with session_scope() as session:
        summary = build_onbid_data_quality_summary(session)
    assert summary["public_visible_fresh_non_sample"] == 2
    assert summary["original_url_coverage"] == 50.0
    print(f"isolated_db={TEST_DB_PATH}")
    print("PASS - original URL coverage")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
