from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from backend.database.models import CrawlRun
from backend.database.session import init_db, session_scope
from backend.services.crawl_runs import begin_crawl_run, finish_crawl_run
from orchestrator import run_pipeline

KST = ZoneInfo("Asia/Seoul")


def default_start_date(days_back: int) -> str:
    return (datetime.now(tz=KST).date() - timedelta(days=max(days_back, 1))).isoformat()


def default_end_date() -> str:
    return datetime.now(tz=KST).date().isoformat()


async def run_scheduled_crawl(args: argparse.Namespace) -> int:
    init_db()
    target_start = args.start_date or default_start_date(args.days_back)
    target_end = args.end_date or default_end_date()

    with session_scope() as session:
        run = begin_crawl_run(
            session=session,
            run_type=args.run_type,
            target_start_date=target_start,
            target_end_date=target_end,
            max_pages=args.max_pages,
            log_path=args.log_path,
        )
        run_id = run.id

    try:
        if args.dry_run:
            with session_scope() as session:
                run = session.get(CrawlRun, run_id)
                finish_crawl_run(
                    session,
                    run,
                    status="SUCCEEDED",
                    documents_found=0,
                    documents_downloaded=0,
                    documents_inserted=0,
                    duplicates_skipped=0,
                )
            print(f"DRY_RUN crawl_run_id={run_id} target={target_start}..{target_end}")
            return 0

        result = await run_pipeline(
            max_items=args.limit,
            start_date=target_start,
            end_date=target_end,
            max_pages=args.max_pages,
        )
        failed = result.ai_failed
        status = "PARTIAL" if failed else "SUCCEEDED"
        with session_scope() as session:
            run = session.get(CrawlRun, run_id)
            finish_crawl_run(
                session,
                run,
                status=status,
                documents_found=result.downloaded + result.skipped_existing,
                documents_downloaded=result.downloaded,
                documents_inserted=result.stored,
                duplicates_skipped=result.skipped_existing,
                failed_downloads=failed,
            )
        print(
            f"crawl_run_id={run_id} status={status} downloaded={result.downloaded} "
            f"inserted={result.stored} duplicates={result.skipped_existing} failed={failed}"
        )
        return 0 if status in {"SUCCEEDED", "PARTIAL"} else 1
    except Exception as exc:
        with session_scope() as session:
            run = session.get(CrawlRun, run_id)
            finish_crawl_run(session, run, status="FAILED", error_message=str(exc))
        print(f"crawl_run_id={run_id} status=FAILED error={str(exc)}")
        return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run scheduled court notice crawling.")
    parser.add_argument("--run-type", default="scheduled", choices=["scheduled", "manual", "backfill", "retry_failed"])
    parser.add_argument("--limit", type=int, default=40)
    parser.add_argument("--max-pages", type=int, default=8)
    parser.add_argument("--days-back", type=int, default=7)
    parser.add_argument("--start-date", default="")
    parser.add_argument("--end-date", default="")
    parser.add_argument("--log-path", default="")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    return asyncio.run(run_scheduled_crawl(parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
