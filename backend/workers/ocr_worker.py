from __future__ import annotations

import argparse
import json

from backend.database.session import init_db, session_scope
from backend.jobs.ocr_service import (
    enqueue_ocr_required_jobs,
    ocr_engine_status,
    run_pending_mock_ocr_jobs,
    run_pending_real_ocr_jobs,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local OCR extraction jobs.")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--enqueue", action="store_true")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    init_db()
    with session_scope() as session:
        queued = enqueue_ocr_required_jobs(session, limit=args.limit) if args.enqueue else []
        if args.dry_run:
            print(
                json.dumps(
                    {"queued": len(queued), "processed": 0, "mode": "dry_run", "engine": ocr_engine_status()},
                    ensure_ascii=False,
                )
            )
            return 0
        processed = (
            run_pending_mock_ocr_jobs(session, limit=args.limit)
            if args.mock
            else run_pending_real_ocr_jobs(session, limit=args.limit)
        )
        print(
            json.dumps(
                {
                    "queued": len(queued),
                    "processed": processed,
                    "mode": "mock" if args.mock else "tesseract",
                    "engine": ocr_engine_status(),
                },
                ensure_ascii=False,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
