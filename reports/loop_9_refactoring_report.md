# Loop 9 보고서

## 목표
`main_app.py`에 몰린 일부 helper/service 로직을 분리하고, URL과 화면 동작은 유지한다.

## 변경한 내용
- Local Analysis App 상태 계산 로직을 `backend/services/local_analysis_status.py`로 분리했다.
- 포트 확인, app-server 상태 판단, worker heartbeat 요약, stale worker 판단 결과 조합을 서비스 모듈에서 처리하도록 했다.
- `main_app.py`는 라우터와 템플릿 context 조립에 집중하도록 한 단계 정리했다.
- 기존 URL과 API 경로는 변경하지 않았다.

## 수정한 파일
- `backend/services/local_analysis_status.py`
- `main_app.py`

## 검증 결과
- Python 문법 검증 통과
- `/user` 200
- `/admin` 200
- `/api/local-analysis/status` 200
- `/api/admin/collection-quality` 200
- `/api/admin/analysis-reviews/summary` 200

## 남은 위험
- `main_app.py`에는 아직 사용자/관리자/job/document 라우트가 함께 남아 있다.
- 다음 리팩토링에서는 `backend/api/routes/*`로 라우터를 분리하고, view model을 별도 모듈로 옮기는 것이 좋다.

## 다음 루프 지시
Loop 10에서 운영 준비를 진행한다. DB 백업 스크립트, 원본 파일 보존 정책, 로컬 worker runbook, 장애 복구 문서를 추가한다.
