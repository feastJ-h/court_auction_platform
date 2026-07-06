from pathlib import Path

from backend.config import PROJECT_ROOT
from backend.database.models import AnalysisJob, AssetEvent


ANALYSIS_JOB_ROOT = PROJECT_ROOT / "storage" / "analysis_jobs"


def job_dir(job_id: int) -> Path:
    path = ANALYSIS_JOB_ROOT / str(job_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _analysis_text(event: AssetEvent) -> tuple[str, str, str, str]:
    analysis = event.analyses[0] if event.analyses else None
    if not analysis:
        return "확인 필요", "0", "미정", "기본 분석 없음"
    return (
        analysis.item_details,
        analysis.min_price,
        analysis.bidding_date,
        analysis.risk_comment,
    )


def build_deep_analysis_input(job: AnalysisJob) -> str:
    event = job.event
    evidence = event.raw_document.evidence
    item_details, min_price, bidding_date, risk_comment = _analysis_text(event)
    raw_file_path = event.raw_document.file_path if event.raw_document else ""

    return f"""# 물건 상세 분석 요청

## 기본 정보
- job_id: {job.id}
- event_id: {event.id}
- case_number: {event.case_number}
- title: {event.title}
- main_category: {event.asset.main_category}
- sub_category: {event.asset.sub_category}
- address: {event.asset.address}
- notice_date: {event.notice_date}
- expire_date: {event.expire_date}
- raw_file_path: {raw_file_path}

## 기본 AI 분석
- item_details: {item_details}
- min_price: {min_price}
- bidding_date: {bidding_date}
- risk_comment: {risk_comment}

## 수집 증거
- source_title: {evidence.source_title if evidence else ""}
- attachment_name: {evidence.attachment_name if evidence else ""}
- notice_date: {evidence.notice_date if evidence else ""}
- expire_date: {evidence.expire_date if evidence else ""}

### 상세 페이지 텍스트
{evidence.detail_page_text if evidence else ""}

## 문서 추출 텍스트
{event.extracted_text or ""}

## 분석 지시
문서에 없는 사실은 확정하지 말고, 추정은 반드시 추정이라고 표시한다.
입찰/매각 판단에 필요한 권리, 가격, 일정, 서류, 현장 확인 리스크를 구분해 작성한다.
부동산이면 명도, 숨은 권리, 토지이용/용도변경 가능성, 감정가 대비 시세 추론을 포함한다.
동산이면 연식/모델/수량, 감가상각, 이전/보관 비용, 훼손/부품 결품 가능성을 포함한다.
반드시 지정된 JSON 스키마에 맞는 JSON만 반환한다.

## 추가/이어가기 지시
{job.progress_message if job.progress_message.startswith("이어가기 요청:") else ""}
"""


def write_input_snapshot(job: AnalysisJob) -> Path:
    path = job_dir(job.id) / "input.md"
    path.write_text(build_deep_analysis_input(job), encoding="utf-8")
    job.input_snapshot_path = str(path.relative_to(PROJECT_ROOT))
    return path
