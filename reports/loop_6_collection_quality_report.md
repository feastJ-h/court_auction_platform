# Loop 6 보고서

## 목표
2026-06-15 이후 수집 데이터의 누락, 중복, 실패 파일을 관리 가능하게 만든다.

## 변경한 내용
- `backend/services/collection_quality.py`를 추가했다.
- 수집 품질 API `/api/admin/collection-quality`를 추가했다.
- 관리자 화면에 `Collection Quality` 섹션을 추가했다.
- 다음 항목을 집계한다.
  - 원본 문서 수
  - 이벤트 수
  - 수집 증거 수
  - parse_status별 건수
  - 작성일 UNKNOWN 건수
  - 공고만료일 UNKNOWN 건수
  - LOCAL_INGESTED 건수
  - 중복 file_hash 건수
  - 원본 파일 누락 건수
  - 확장자별 파일 수
- 누락 파일이 있으면 관리자 화면에서 목록을 펼쳐볼 수 있게 했다.

## 수정한 파일
- `backend/services/collection_quality.py`
- `main_app.py`
- `frontend/templates/admin/dashboard.html`

## 검증 결과
- Python 문법 검증 통과
- `/api/admin/collection-quality` 200
- `/admin` 200
- `/user` 200
- 현재 품질 집계:
  - 원본 문서: 50건
  - 이벤트: 50건
  - 수집 증거: 50건
  - 파일 누락: 0건
  - 중복 hash: 0건
  - PDF: 48건
  - HWP: 2건
  - 작성일 UNKNOWN: 12건
  - 공고만료일 UNKNOWN: 5건
  - LOCAL_INGESTED: 26건
  - parse_status: PARSED 43건, OCR_REQUIRED 4건, PARSE_FAILED 2건, MANUAL_REVIEW 1건

## 남은 위험
- LOCAL_INGESTED 26건은 상세 페이지 메타데이터 보강이 필요하다.
- UNKNOWN 날짜 항목은 법원 상세 페이지 재방문 또는 파일명/본문 기반 보정 로직이 필요하다.
- 다운로드 실패 이력 테이블은 아직 별도로 없다. 다음 수집 파이프라인 개선 때 페이지별 수집 로그 테이블을 추가하는 것이 좋다.

## 다음 루프 지시
Loop 7에서 OCR/HWP 준비 상태를 분석 실패와 분리한다. 텍스트 부족 문서가 AI 분석 job으로 바로 들어가지 않도록 guard를 추가하고, 관리자 화면에 분석 불가 원인을 명확히 표시한다.
