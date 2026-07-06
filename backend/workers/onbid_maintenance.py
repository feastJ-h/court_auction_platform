from __future__ import annotations

import argparse
import json

from backend.database.session import init_db, session_scope
from backend.services.auction_items import audit_onbid_freshness, repair_onbid_derived_fields


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ONBID freshness and derived-field maintenance.")
    parser.add_argument(
        "command",
        choices=("audit-freshness", "dry-run-derived-fields", "apply-derived-fields"),
    )
    parser.add_argument("--min-date", default="2025-01-01")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    init_db()
    with session_scope() as session:
        if args.command == "audit-freshness":
            result = audit_onbid_freshness(session, min_date=args.min_date)
        else:
            result = repair_onbid_derived_fields(
                session,
                dry_run=args.command != "apply-derived-fields",
                min_date=args.min_date,
            )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
