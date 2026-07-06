from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session, joinedload

from backend.database.analysis_results import create_or_get_basic_result
from backend.database.models import (
    AiAnalysis,
    AnalysisResult,
    Asset,
    AssetEvent,
    CollectionEvidence,
    RawDocument,
    UserEventAction,
)


def raw_document_exists_by_hash(session: Session, file_hash: str) -> bool:
    return session.scalar(select(RawDocument.id).where(RawDocument.file_hash == file_hash)) is not None


def get_raw_document_by_hash(session: Session, file_hash: str) -> RawDocument | None:
    return session.scalar(select(RawDocument).where(RawDocument.file_hash == file_hash))


def get_or_create_raw_document(
    session: Session,
    file_path: str,
    source_url: str,
    file_hash: str,
) -> RawDocument:
    existing = get_raw_document_by_hash(session, file_hash)
    if existing:
        return existing

    document = RawDocument(file_path=file_path, source_url=source_url, file_hash=file_hash)
    session.add(document)
    session.flush()
    return document


def upsert_collection_evidence(
    session: Session,
    document: RawDocument,
    source_title: str,
    attachment_name: str,
    notice_date: str,
    expire_date: str,
    detail_page_text: str,
) -> CollectionEvidence:
    existing = session.scalar(
        select(CollectionEvidence).where(CollectionEvidence.raw_doc_id == document.id)
    )
    if existing:
        existing.source_title = source_title
        existing.attachment_name = attachment_name
        existing.notice_date = notice_date or "UNKNOWN"
        existing.expire_date = expire_date or "UNKNOWN"
        existing.detail_page_text = detail_page_text or ""
        session.flush()
        return existing

    evidence = CollectionEvidence(
        raw_doc_id=document.id,
        source_title=source_title,
        attachment_name=attachment_name,
        notice_date=notice_date or "UNKNOWN",
        expire_date=expire_date or "UNKNOWN",
        detail_page_text=detail_page_text or "",
    )
    session.add(evidence)
    session.flush()
    return evidence


def create_asset(session: Session, payload: dict) -> Asset:
    asset = Asset(
        main_category=str(payload.get("main_category") or "동산"),
        sub_category=str(payload.get("sub_category") or "확인 필요"),
        address=str(payload.get("address") or "확인 필요"),
    )
    session.add(asset)
    session.flush()
    return asset


def create_asset_event(
    session: Session,
    asset: Asset,
    document: RawDocument,
    case_number: str,
    status: str,
    title: str,
    url: str,
    notice_date: str,
    expire_date: str,
    parse_status: str,
    extracted_text: str,
) -> AssetEvent:
    event = AssetEvent(
        asset_id=asset.id,
        raw_doc_id=document.id,
        case_number=case_number,
        status=status,
        title=title,
        url=url,
        notice_date=notice_date or "UNKNOWN",
        expire_date=expire_date or "UNKNOWN",
        parse_status=parse_status,
        extracted_text=extracted_text,
    )
    session.add(event)
    session.flush()
    return event


def create_ai_analysis(
    session: Session,
    event: AssetEvent,
    payload: dict,
    is_hallucinated: bool,
) -> AiAnalysis:
    analysis = AiAnalysis(
        event_id=event.id,
        item_details=str(payload.get("item_details") or "확인 필요"),
        min_price=str(payload.get("min_price") or "0"),
        bidding_date=str(payload.get("bidding_date") or "미정"),
        risk_comment=str(payload.get("risk_comment") or "확인 필요"),
        detailed_analysis=str(payload.get("detailed_analysis") or ""),
        is_hallucinated=is_hallucinated,
        analysis_provider=str(payload.get("analysis_provider") or "chatgpt"),
    )
    session.add(analysis)
    session.flush()
    create_or_get_basic_result(session, event, analysis)
    return analysis


def list_user_events(session: Session) -> list[AssetEvent]:
    return list(
        session.scalars(
            select(AssetEvent)
            .outerjoin(AiAnalysis, AiAnalysis.event_id == AssetEvent.id)
            .options(
                joinedload(AssetEvent.asset),
                joinedload(AssetEvent.analyses),
                joinedload(AssetEvent.raw_document).joinedload(RawDocument.evidence),
            )
            .order_by(*_user_event_ordering())
        ).unique()
    )


def _passed_event_ids_subquery(user_id: int | None):
    if not user_id:
        return None
    return select(UserEventAction.event_id).where(
        UserEventAction.user_id == user_id,
        UserEventAction.action_type == "PASSED",
    )


def count_user_events(session: Session, user_id: int | None = None) -> int:
    statement = select(func.count(AssetEvent.id))
    passed_subquery = _passed_event_ids_subquery(user_id)
    if passed_subquery is not None:
        statement = statement.where(AssetEvent.id.not_in(passed_subquery))
    return session.scalar(statement) or 0


def list_user_events_page(session: Session, limit: int, offset: int, user_id: int | None = None) -> list[AssetEvent]:
    statement = (
        select(AssetEvent)
        .outerjoin(AiAnalysis, AiAnalysis.event_id == AssetEvent.id)
        .options(
            joinedload(AssetEvent.asset),
            joinedload(AssetEvent.analyses),
            joinedload(AssetEvent.raw_document).joinedload(RawDocument.evidence),
        )
        .order_by(*_user_event_ordering())
        .limit(limit)
        .offset(offset)
    )
    passed_subquery = _passed_event_ids_subquery(user_id)
    if passed_subquery is not None:
        statement = statement.where(AssetEvent.id.not_in(passed_subquery))
    return list(
        session.scalars(
            statement
        ).unique()
    )


def _has_result_exists(analysis_type: str, providers: tuple[str, ...] | None = None):
    conditions = [
        AnalysisResult.event_id == AssetEvent.id,
        AnalysisResult.analysis_type == analysis_type,
        AnalysisResult.status.in_(("SUCCEEDED", "CACHED")),
        AnalysisResult.superseded_at.is_(None),
    ]
    if providers:
        conditions.append(AnalysisResult.model_provider.in_(providers))
    return exists(select(AnalysisResult.id).where(*conditions))


def _user_event_ordering():
    codex_or_chatgpt_deep = _has_result_exists(
        "deep",
        ("chatgpt", "codex_app_server", "codex_cli"),
    )
    gemini_deep = _has_result_exists("deep", ("gemini",))
    any_basic = _has_result_exists("basic")
    legacy_detailed = func.length(func.trim(func.coalesce(AiAnalysis.detailed_analysis, ""))) > 0
    return (
        codex_or_chatgpt_deep.desc(),
        gemini_deep.desc(),
        legacy_detailed.desc(),
        any_basic.desc(),
        AssetEvent.notice_date.desc(),
        AssetEvent.id.asc(),
    )


def get_event_with_details(session: Session, event_id: int) -> AssetEvent | None:
    return session.scalar(
        select(AssetEvent)
        .options(
            joinedload(AssetEvent.asset),
            joinedload(AssetEvent.analyses),
            joinedload(AssetEvent.raw_document).joinedload(RawDocument.evidence),
        )
        .where(AssetEvent.id == event_id)
    )


def save_detailed_analysis(session: Session, analysis: AiAnalysis, detailed_analysis: str) -> None:
    analysis.detailed_analysis = detailed_analysis
    session.flush()


def list_admin_events(session: Session) -> list[AssetEvent]:
    return list_user_events(session)
