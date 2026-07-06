# Loop 5 보고서

## 목표
일반 사용자가 분석 완료 물건을 우선 검토하고, Gemini와 ChatGPT/Codex 판단 차이를 쉽게 이해할 수 있게 한다.

## 변경한 내용
- 사용자 목록 정렬 쿼리를 `analysis_results` 기반으로 고도화했다.
- 정렬 우선순위:
  1. ChatGPT/Codex deep 완료
  2. Gemini deep 완료
  3. legacy detailed 완료
  4. basic 분석 완료
  5. 법원 등록일 최신순
  6. id 오름차순
- 사용자 화면 배지 문구를 `ChatGPT`에서 `ChatGPT/Codex`로 명확히 바꿨다.
- 상세 분석 요청 문구를 `Codex CLI 워커`에서 `로컬 분석 워커`로 바꿔 app-server/CLI 양쪽을 모두 포괄하게 했다.

## 수정한 파일
- `backend/database/crud.py`
- `frontend/templates/user/index.html`
- `frontend/static/app.js`

## 검증 결과
- Python 문법 검증 통과
- JavaScript 문법 검증 통과
- `/user` 200
- `/user?page=2` 200
- `/admin` 200
- `/api/local-analysis/status` 200
- 사용자 첫 10건 정렬 확인:
  - RP-20260703-001, 002, 004, 006, 007: ChatGPT/Codex 완료 + Gemini 완료
  - 이후 항목: Gemini 완료 중심으로 날짜순 정렬

## 남은 위험
- 사용자 페이지는 5건 페이지네이션이라, 전체 결과의 카테고리 카운트는 현재 페이지 기준이다. 전체 카테고리 카운트가 필요하면 별도 집계 쿼리를 추가해야 한다.
- 모바일 아코디언은 기존 JS 구조를 유지했다. 최종 브라우저 모바일 폭 검증은 전체 작업 종료 시 한 번 더 수행한다.

## 다음 루프 지시
Loop 6에서 수집 품질을 관리자 화면과 API에서 볼 수 있게 한다. UNKNOWN 날짜, LOCAL_INGESTED, 중복 hash, 파일 존재 여부, 파싱 상태별 건수를 집계한다.
