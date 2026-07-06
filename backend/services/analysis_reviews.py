from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database.models import AnalysisResult, AnalysisReview


SCORE_FIELDS = (
    "price_score",
    "date_score",
    "risk_score",
    "evidence_score",
    "hallucination_score",
)


def _score(value) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError):
        score = 0
    return max(0, min(5, score))


def create_analysis_review(session: Session, analysis_result_id: int, payload: dict) -> AnalysisReview:
    result = session.get(AnalysisResult, analysis_result_id)
    if result is None:
        raise ValueError("analysis_result_not_found")
    review = AnalysisReview(
        analysis_result_id=analysis_result_id,
        reviewer=str(payload.get("reviewer") or "admin")[:128],
        price_score=_score(payload.get("price_score")),
        date_score=_score(payload.get("date_score")),
        risk_score=_score(payload.get("risk_score")),
        evidence_score=_score(payload.get("evidence_score")),
        hallucination_score=_score(payload.get("hallucination_score")),
        notes=str(payload.get("notes") or "")[:4000],
    )
    session.add(review)
    session.flush()
    return review


def serialize_analysis_review(review: AnalysisReview) -> dict:
    return {
        "id": review.id,
        "analysis_result_id": review.analysis_result_id,
        "reviewer": review.reviewer,
        "price_score": review.price_score,
        "date_score": review.date_score,
        "risk_score": review.risk_score,
        "evidence_score": review.evidence_score,
        "hallucination_score": review.hallucination_score,
        "notes": review.notes,
        "created_at": review.created_at.isoformat() if review.created_at else None,
    }


def list_recent_analysis_reviews(session: Session, limit: int = 20) -> list[dict]:
    rows = session.execute(
        select(AnalysisReview, AnalysisResult)
        .join(AnalysisResult, AnalysisResult.id == AnalysisReview.analysis_result_id)
        .order_by(AnalysisReview.created_at.desc(), AnalysisReview.id.desc())
        .limit(limit)
    ).all()
    return [
        {
            **serialize_analysis_review(review),
            "model_provider": result.model_provider,
            "analysis_type": result.analysis_type,
            "event_id": result.event_id,
            "model_name": result.model_name,
        }
        for review, result in rows
    ]


def list_reviews_for_results(session: Session, analysis_result_ids: list[int]) -> dict[int, list[dict]]:
    if not analysis_result_ids:
        return {}
    reviews = session.scalars(
        select(AnalysisReview)
        .where(AnalysisReview.analysis_result_id.in_(analysis_result_ids))
        .order_by(AnalysisReview.created_at.desc(), AnalysisReview.id.desc())
    )
    grouped: dict[int, list[dict]] = {}
    for review in reviews:
        grouped.setdefault(review.analysis_result_id, []).append(serialize_analysis_review(review))
    return grouped


def build_analysis_review_summary(session: Session) -> dict:
    total_reviews = session.scalar(select(func.count(AnalysisReview.id))) or 0
    if total_reviews == 0:
        return {
            "total_reviews": 0,
            "averages": {field: 0 for field in SCORE_FIELDS},
            "by_provider": {},
        }

    averages = {
        field: round(float(session.scalar(select(func.avg(getattr(AnalysisReview, field)))) or 0), 2)
        for field in SCORE_FIELDS
    }
    rows = session.execute(
        select(
            AnalysisResult.model_provider,
            AnalysisResult.analysis_type,
            func.count(AnalysisReview.id),
            func.avg(AnalysisReview.risk_score),
            func.avg(AnalysisReview.evidence_score),
            func.avg(AnalysisReview.hallucination_score),
        )
        .join(AnalysisResult, AnalysisResult.id == AnalysisReview.analysis_result_id)
        .group_by(AnalysisResult.model_provider, AnalysisResult.analysis_type)
    ).all()
    by_provider = {}
    for provider, analysis_type, count, risk_avg, evidence_avg, hallucination_avg in rows:
        by_provider.setdefault(str(provider), {})[str(analysis_type)] = {
            "count": int(count),
            "risk_score_avg": round(float(risk_avg or 0), 2),
            "evidence_score_avg": round(float(evidence_avg or 0), 2),
            "hallucination_score_avg": round(float(hallucination_avg or 0), 2),
        }
    return {
        "total_reviews": total_reviews,
        "averages": averages,
        "by_provider": by_provider,
    }
