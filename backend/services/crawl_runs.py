from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.database.models import AssetEvent, CrawlRun

KST = ZoneInfo("Asia/Seoul")
COURT_SCHEDULE_WEEKDAY = ((8, 10), (15, 10))
COURT_SCHEDULE_WEEKEND = ((9, 10),)
ONBID_SCHEDULE_DAILY = (
    (6, 30),
    (8, 30),
    (10, 30),
    (12, 30),
    (14, 30),
    (16, 30),
    (18, 30),
    (20, 30),
    (22, 30),
)


def begin_crawl_run(
    session: Session,
    run_type: str,
    target_start_date: str,
    target_end_date: str,
    max_pages: int,
    log_path: str,
) -> CrawlRun:
    run = CrawlRun(
        run_type=run_type,
        status="RUNNING",
        target_start_date=target_start_date,
        target_end_date=target_end_date,
        pages_scanned=max_pages,
        log_path=log_path,
    )
    session.add(run)
    session.flush()
    return run


def finish_crawl_run(
    session: Session,
    run: CrawlRun,
    *,
    status: str,
    documents_found: int = 0,
    documents_downloaded: int = 0,
    documents_inserted: int = 0,
    duplicates_skipped: int = 0,
    failed_downloads: int = 0,
    error_message: str = "",
) -> CrawlRun:
    run.status = status
    run.finished_at = datetime.now(tz=KST)
    run.documents_found = documents_found
    run.documents_downloaded = documents_downloaded
    run.documents_inserted = documents_inserted
    run.duplicates_skipped = duplicates_skipped
    run.failed_downloads = failed_downloads
    run.error_message = error_message[:4000]
    session.flush()
    return run


def list_recent_crawl_runs(session: Session, limit: int = 20) -> list[CrawlRun]:
    return list(
        session.scalars(
            select(CrawlRun)
            .order_by(CrawlRun.started_at.desc(), CrawlRun.id.desc())
            .limit(limit)
        )
    )


def latest_crawl_run(session: Session) -> CrawlRun | None:
    return session.scalar(
        select(CrawlRun).order_by(CrawlRun.started_at.desc(), CrawlRun.id.desc()).limit(1)
    )


def latest_successful_crawl_run(session: Session) -> CrawlRun | None:
    return session.scalar(
        select(CrawlRun)
        .where(CrawlRun.status == "SUCCEEDED")
        .order_by(CrawlRun.finished_at.desc(), CrawlRun.id.desc())
        .limit(1)
    )


def count_events_created_today(session: Session) -> int:
    today = datetime.now(tz=KST).date().isoformat()
    return session.scalar(
        select(func.count(AssetEvent.id)).where(AssetEvent.notice_date == today)
    ) or 0


def _build_prefix_filter(prefixes: tuple[str, ...]):
    prefix_conditions = [CrawlRun.run_type.startswith(prefix) for prefix in prefixes]
    if not prefix_conditions:
        return None
    return or_(*prefix_conditions)


def latest_crawl_run_for_prefixes(session: Session, prefixes: tuple[str, ...]) -> CrawlRun | None:
    statement = select(CrawlRun)
    prefix_filter = _build_prefix_filter(prefixes)
    if prefix_filter is not None:
        statement = statement.where(prefix_filter)
    return session.scalar(statement.order_by(CrawlRun.started_at.desc(), CrawlRun.id.desc()).limit(1))


def latest_successful_crawl_run_for_prefixes(session: Session, prefixes: tuple[str, ...]) -> CrawlRun | None:
    statement = select(CrawlRun).where(CrawlRun.status == "SUCCEEDED")
    prefix_filter = _build_prefix_filter(prefixes)
    if prefix_filter is not None:
        statement = statement.where(prefix_filter)
    return session.scalar(statement.order_by(CrawlRun.finished_at.desc(), CrawlRun.id.desc()).limit(1))


def list_recent_crawl_runs_for_prefixes(
    session: Session,
    prefixes: tuple[str, ...],
    *,
    limit: int = 20,
    include_matches: bool = True,
) -> list[CrawlRun]:
    statement = select(CrawlRun)
    prefix_filter = _build_prefix_filter(prefixes)
    if prefix_filter is not None:
        statement = statement.where(prefix_filter if include_matches else ~prefix_filter)
    return list(
        session.scalars(
            statement.order_by(CrawlRun.started_at.desc(), CrawlRun.id.desc()).limit(limit)
        )
    )


def format_schedule_times(schedule: tuple[tuple[int, int], ...]) -> str:
    return " / ".join(f"{hour:02d}:{minute:02d}" for hour, minute in schedule)


def estimate_next_from_schedule(schedule: tuple[tuple[int, int], ...], now: datetime | None = None) -> datetime:
    current = now.astimezone(KST) if now else datetime.now(tz=KST)
    for hour, minute in schedule:
        candidate = current.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate > current:
            return candidate
    tomorrow = current + timedelta(days=1)
    first_hour, first_minute = schedule[0]
    return tomorrow.replace(hour=first_hour, minute=first_minute, second=0, microsecond=0)


def court_schedule_for_day(day: datetime) -> tuple[tuple[int, int], ...]:
    return COURT_SCHEDULE_WEEKEND if day.weekday() >= 5 else COURT_SCHEDULE_WEEKDAY


def estimate_next_scheduled_crawl(now: datetime | None = None) -> datetime:
    current = now.astimezone(KST) if now else datetime.now(tz=KST)
    schedule = court_schedule_for_day(current)
    today_candidate = estimate_next_from_schedule(schedule, current)
    if today_candidate.date() == current.date():
        return today_candidate
    tomorrow = current + timedelta(days=1)
    tomorrow_schedule = court_schedule_for_day(tomorrow)
    first_hour, first_minute = tomorrow_schedule[0]
    return tomorrow.replace(hour=first_hour, minute=first_minute, second=0, microsecond=0)


def estimate_next_onbid_scheduled_sync(now: datetime | None = None) -> datetime:
    return estimate_next_from_schedule(ONBID_SCHEDULE_DAILY, now)


def build_crawl_run_summary(session: Session) -> dict:
    latest = latest_crawl_run(session)
    latest_success = latest_successful_crawl_run(session)
    recent_runs = list_recent_crawl_runs(session, limit=20)
    onbid_prefixes = ("onbid_",)
    onbid_latest = latest_crawl_run_for_prefixes(session, onbid_prefixes)
    onbid_latest_success = latest_successful_crawl_run_for_prefixes(session, onbid_prefixes)
    onbid_recent_runs = list_recent_crawl_runs_for_prefixes(session, onbid_prefixes, limit=20)
    court_recent_runs = list_recent_crawl_runs_for_prefixes(
        session,
        onbid_prefixes,
        limit=20,
        include_matches=False,
    )
    return {
        "latest_run": latest,
        "latest_success": latest_success,
        "recent_runs": recent_runs,
        "court_recent_runs": court_recent_runs,
        "today_notice_events": count_events_created_today(session),
        "next_scheduled_at": estimate_next_scheduled_crawl(),
        "court_schedule_label": f"평일 {format_schedule_times(COURT_SCHEDULE_WEEKDAY)} / 주말 {format_schedule_times(COURT_SCHEDULE_WEEKEND)}",
        "onbid_latest_run": onbid_latest,
        "onbid_latest_success": onbid_latest_success,
        "onbid_recent_runs": onbid_recent_runs,
        "next_onbid_scheduled_at": estimate_next_onbid_scheduled_sync(),
        "onbid_schedule_label": format_schedule_times(ONBID_SCHEDULE_DAILY),
    }
