# Loop 4 보고서

## 목표
관리자가 운영 상태, 분석 상태, 실패 원인, 모델별 결과를 한 화면에서 빠르게 파악하게 한다.

## 변경한 내용
- 관리자 화면에 운영 필터를 추가했다.
  - Job 상태: 전체, 없음, 대기, 진행, 완료, 실패, 취소
  - 모델: 전체, Gemini 있음, ChatGPT/Codex 있음, Codex 상세 있음
  - 파싱 상태: 전체, PARSED, LOCAL_INGESTED, OCR_REQUIRED 등
- 실패 Job 섹션을 추가해 실패한 분석 작업과 오류 메시지를 상단에서 바로 볼 수 있게 했다.
- 오래 멈춘 RUNNING Job 섹션을 추가했다.
- Local Analysis App 카드에 worker heartbeat 정보를 표시했다.
- 각 물건 카드 하단에 모델별 분석 결과 펼쳐보기를 추가했다.
- 기존 URL `/admin`은 유지하고 query parameter 방식으로만 필터링한다.

## 수정한 파일
- `main_app.py`
- `frontend/templates/admin/dashboard.html`

## 검증 결과
- Python 문법 검증 통과
- `/admin` 200
- `/admin?job_status=FAILED` 200
- `/admin?job_status=NONE` 200
- `/admin?model=gemini` 200
- `/admin?model=codex` 200
- `/admin?parse_status=LOCAL_INGESTED` 200
- `/user` 200
- `/api/local-analysis/status` 200
- 관리자 HTML에 `Operations Filter`, `codex_app_server_worker`, `force-analysis-button` 렌더링 확인

## 남은 위험
- 필터는 서버 렌더링 기반이라 동작은 안정적이지만, 추후 물건 수가 수천 건 이상으로 늘면 관리자 목록에도 페이지네이션이 필요하다.
- 모델별 결과 상세는 현재 텍스트 요약 중심이다. JSON/Markdown 파일 열기 링크는 다음 운영 준비 Loop에서 더 다듬는 것이 좋다.

## 다음 루프 지시
Loop 5에서 사용자 화면을 `analysis_results` 중심으로 더 보강하고, 분석 완료 우선 정렬 및 모델 비교 UX를 검증한다.
