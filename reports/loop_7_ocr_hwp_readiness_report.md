# Loop 7 보고서

## 목표
텍스트가 비어 있거나 OCR/HWP 처리가 필요한 문서를 AI 분석 실패로 처리하지 않고 별도 준비 상태로 관리한다.

## 변경한 내용
- `backend/jobs/readiness.py`를 추가했다.
- `OCR_REQUIRED`, `PARSE_FAILED`, `MANUAL_REVIEW`, `TEXT_EXTRACTION_FAILED`, `HWP_CONVERSION_REQUIRED` 등 차단 parse_status를 정의했다.
- deep 분석 job 생성 전에 `get_analysis_readiness()`를 호출하여 준비되지 않은 문서는 409로 차단한다.
- 사용자 payload에 `analysis_readiness`를 포함했다.
- 관리자 화면에 `분석 가능`/`분석 준비 필요` 배지와 분석 불가 원인을 표시했다.
- 사용자 상세 심층 분석 탭에서 준비되지 않은 문서는 분석 요청 버튼 대신 준비 필요 메시지를 보여준다.

## 수정한 파일
- `backend/jobs/readiness.py`
- `backend/jobs/service.py`
- `main_app.py`
- `frontend/templates/admin/dashboard.html`
- `frontend/static/app.js`

## 검증 결과
- Python 문법 검증 통과
- JavaScript 문법 검증 통과
- RP-20260703-008 / `MANUAL_REVIEW` 문서의 심층 분석 요청이 409로 차단됨
- 차단 메시지: `분석 준비가 필요합니다: 수동 검토가 필요한 문서입니다.`
- `/admin` 200
- `/user` 200
- `/api/local-analysis/status` 200
- 사용자 payload에 `analysis_readiness` 포함 확인

## 남은 위험
- OCR/HWP 실제 변환 job 큐는 아직 구현하지 않았다.
- `MANUAL_REVIEW`는 보수적으로 차단했다. 일부 문서가 충분한 텍스트를 갖고도 수동 검토로 남아 있다면 관리자 승인 후 분석하는 override가 필요할 수 있다.

## 다음 루프 지시
Loop 8에서 분석 품질 평가 테이블과 관리자 검수 기반을 추가한다. 우선 `analysis_reviews` 테이블과 간단한 입력 API/요약 API를 만든다.
