from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database.models import AiAnalysis, AnalysisResult, AssetEvent

DEFAULT_PROMPT_VERSION = "v1"


def normalize_result_provider(provider: str) -> str:
    value = (provider or "").strip().lower()
    if value in {"openai", "chatgpt"}:
        return "chatgpt"
    if value == "app_server":
        return "codex_app_server"
    if value == "exec":
        return "codex_cli"
    return value or "chatgpt"


def source_hash_for_event(event: AssetEvent) -> str:
    return event.raw_document.file_hash if event.raw_document else ""


def get_active_result(
    session: Session,
    event_id: int,
    model_provider: str,
    analysis_type: str,
    source_hash: str,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
) -> AnalysisResult | None:
    return session.scalar(
        select(AnalysisResult)
        .where(
            AnalysisResult.event_id == event_id,
            AnalysisResult.model_provider == normalize_result_provider(model_provider),
            AnalysisResult.analysis_type == analysis_type,
            AnalysisResult.source_hash == source_hash,
            AnalysisResult.prompt_version == prompt_version,
            AnalysisResult.superseded_at.is_(None),
        )
        .order_by(AnalysisResult.id.desc())
        .limit(1)
    )


def create_or_get_basic_result(
    session: Session,
    event: AssetEvent,
    analysis: AiAnalysis,
    force: bool = False,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
) -> AnalysisResult:
    provider = normalize_result_provider(analysis.analysis_provider)
    source_hash = source_hash_for_event(event)
    existing = get_active_result(session, event.id, provider, "basic", source_hash, prompt_version)
    if existing and not force:
        return existing
    if existing and force:
        existing.superseded_at = datetime.now(timezone.utc)

    result = AnalysisResult(
        event_id=event.id,
        model_provider=provider,
        model_name=provider,
        analysis_type="basic",
        source_hash=source_hash,
        status="SUCCEEDED",
        item_details=analysis.item_details,
        min_price=analysis.min_price,
        bidding_date=analysis.bidding_date,
        risk_comment=analysis.risk_comment,
        detailed_analysis="",
        is_hallucinated=analysis.is_hallucinated,
        prompt_version=prompt_version,
        run_count=1,
    )
    session.add(result)
    session.flush()
    return result


def create_or_get_deep_result(
    session: Session,
    event: AssetEvent,
    model_provider: str,
    model_name: str,
    detailed_analysis: str,
    structured_json_path: str = "",
    markdown_path: str = "",
    force: bool = False,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
) -> AnalysisResult:
    analysis = event.analyses[0] if event.analyses else None
    provider = normalize_result_provider(model_provider)
    source_hash = source_hash_for_event(event)
    existing = get_active_result(session, event.id, provider, "deep", source_hash, prompt_version)
    if existing and not force:
        return existing
    if existing and force:
        existing.superseded_at = datetime.now(timezone.utc)

    result = AnalysisResult(
        event_id=event.id,
        model_provider=provider,
        model_name=model_name or provider,
        analysis_type="deep",
        source_hash=source_hash,
        status="SUCCEEDED",
        item_details=analysis.item_details if analysis else "",
        min_price=analysis.min_price if analysis else "0",
        bidding_date=analysis.bidding_date if analysis else "미정",
        risk_comment=analysis.risk_comment if analysis else "",
        detailed_analysis=detailed_analysis,
        structured_json_path=structured_json_path,
        markdown_path=markdown_path,
        is_hallucinated=analysis.is_hallucinated if analysis else False,
        prompt_version=prompt_version,
        run_count=1,
    )
    session.add(result)
    session.flush()
    return result


def list_results_for_event(session: Session, event_id: int) -> list[AnalysisResult]:
    return list(
        session.scalars(
            select(AnalysisResult)
            .where(
                AnalysisResult.event_id == event_id,
                AnalysisResult.superseded_at.is_(None),
            )
            .order_by(AnalysisResult.analysis_type.asc(), AnalysisResult.model_provider.asc(), AnalysisResult.id.desc())
        )
    )


def list_results_for_events(session: Session, event_ids: Iterable[int]) -> dict[int, list[AnalysisResult]]:
    ids = list(event_ids)
    if not ids:
        return {}
    results = session.scalars(
        select(AnalysisResult)
        .where(
            AnalysisResult.event_id.in_(ids),
            AnalysisResult.superseded_at.is_(None),
        )
        .order_by(AnalysisResult.event_id.asc(), AnalysisResult.analysis_type.asc(), AnalysisResult.model_provider.asc())
    ).all()
    grouped: dict[int, list[AnalysisResult]] = {}
    for result in results:
        grouped.setdefault(result.event_id, []).append(result)
    return grouped


def count_results_by_provider(session: Session) -> dict[str, dict[str, int]]:
    rows = session.execute(
        select(AnalysisResult.model_provider, AnalysisResult.analysis_type, AnalysisResult.status, func.count(AnalysisResult.id))
        .where(AnalysisResult.superseded_at.is_(None))
        .group_by(AnalysisResult.model_provider, AnalysisResult.analysis_type, AnalysisResult.status)
    ).all()
    counts: dict[str, dict[str, int]] = {}
    for provider, analysis_type, status, count in rows:
        key = f"{analysis_type}_{str(status).lower()}"
        counts.setdefault(str(provider), {})[key] = int(count)
    return counts


def serialize_result(result: AnalysisResult) -> dict:
    return {
        "id": result.id,
        "event_id": result.event_id,
        "model_provider": result.model_provider,
        "model_name": result.model_name,
        "analysis_type": result.analysis_type,
        "source_hash": result.source_hash,
        "status": result.status,
        "item_details": result.item_details,
        "min_price": result.min_price,
        "bidding_date": result.bidding_date,
        "risk_comment": result.risk_comment,
        "detailed_analysis": result.detailed_analysis,
        "structured_json_path": result.structured_json_path,
        "markdown_path": result.markdown_path,
        "confidence": result.confidence,
        "is_hallucinated": result.is_hallucinated,
        "prompt_version": result.prompt_version,
        "created_at": result.created_at.isoformat() if result.created_at else None,
        "updated_at": result.updated_at.isoformat() if result.updated_at else None,
        "run_count": result.run_count,
    }
