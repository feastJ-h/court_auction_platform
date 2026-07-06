# Loop 8 보고서

## 목표
Gemini와 ChatGPT/Codex 분석 품질을 기록으로 비교할 수 있는 기반을 만든다.

## 변경한 내용
- `AnalysisReview` 모델과 `analysis_reviews` 테이블을 추가했다.
- `backend/services/analysis_reviews.py`를 추가했다.
- 검수 점수 필드:
  - 가격 정확도
  - 날짜 정확도
  - 리스크 판단
  - 근거 충실도
  - 환각 의심도
- 점수는 0~5 범위로 자동 보정한다.
- 관리자 검수 요약 API `/api/admin/analysis-reviews/summary`를 추가했다.
- 분석 결과별 리뷰 등록 API `/api/admin/analysis-results/{analysis_result_id}/reviews`를 추가했다.
- 관리자 화면에 `Analysis Quality` 요약 카드를 추가했다.

## 수정한 파일
- `backend/database/models.py`
- `backend/services/analysis_reviews.py`
- `main_app.py`
- `frontend/templates/admin/dashboard.html`

## 검증 결과
- Python 문법 검증 통과
- rollback 세션에서 리뷰 생성 검증
- `price_score=7` 입력 시 5로 제한 확인
- `hallucination_score=-1` 입력 시 0으로 제한 확인
- `/api/admin/analysis-reviews/summary` 200
- 없는 분석 결과 리뷰 등록 시 404
- `/admin` 200
- 관리자 화면에 `Analysis Quality` 섹션 렌더링 확인

## 남은 위험
- 아직 관리자 화면에서 직접 점수를 입력하는 폼은 없다. 현재는 API 기반이다.
- golden case 20개 선정과 prompt_version별 평가 비교 화면은 다음 품질 Sprint에서 확장해야 한다.

## 다음 루프 지시
Loop 9에서 `main_app.py`의 일부 helper/service 로직을 더 분리하되, URL과 화면 동작은 유지한다.
