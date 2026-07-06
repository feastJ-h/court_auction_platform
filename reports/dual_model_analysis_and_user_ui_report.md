# Dual Model Analysis & User UI 완료 결과 리포트

## 1. 구현된 주요 기능 (Summary)
- `analysis_results` 테이블을 추가하여 Gemini, ChatGPT, Codex app-server, Codex CLI 결과를 모델별/분석 타입별로 분리 저장하도록 구현했다.
- 기존 `ai_analyses` 및 상세 분석 결과를 `analysis_results`로 자동 이관하는 SQLite 마이그레이션/시드 로직을 추가했다.
- 동일 문서 해시, 동일 이벤트, 동일 모델, 동일 분석 타입의 활성 결과가 있으면 중복 분석 결과를 만들지 않고 기존 결과를 재사용하도록 했다.
- 관리자 강제 재분석 요청 시 기존 결과는 `superseded_at`으로 비활성화하고 새 결과를 저장할 수 있는 경로를 마련했다.
- 사용자 화면에 Gemini 분석, ChatGPT/Codex 분석, 모델 비교, 작업 로그 탭을 추가했다.
- 관리자 화면에 Gemini 기본, ChatGPT 기본, Codex 상세, 모델 의견 차이 집계와 물건별 모델 상태 배지를 추가했다.
- 관리자 화면에서 물건별 `강제 재분석` 버튼을 제공하여 기존 분석 데이터와 별개로 재분석 job을 요청할 수 있게 했다.

## 2. 보안 및 예외 처리 내역 (Security & Edge Cases Handled)
- 원본 문서 해시(`source_hash`)를 기준으로 결과를 분리하여 법원 게시물 번호가 변경되거나 삭제되어도 로컬 문서 기준의 분석 이력을 보존한다.
- `app_server`, `exec`, `openai` 등 과거 provider 명칭을 `codex_app_server`, `codex_cli`, `chatgpt`로 정규화했다.
- 기존 성공 결과를 `CACHED` 상태로 덮어쓰지 않도록 수정해 성공/실패/캐시 상태의 의미가 오염되지 않게 했다.
- 강제 재분석은 `admin_force` 요청으로 기록되며 기존 결과를 물리 삭제하지 않는다.
- 사용자 화면에는 원문과 모델 결과를 탭으로 분리해 혼동을 줄이고, 모델 간 결과 차이가 있을 때 배지로 표시하도록 했다.

## 3. 단위 테스트 및 화면 검증 결과 (Test Results)
- Python 문법 검증: `py_compile` 통과
- JavaScript 문법 검증: `node --check frontend/static/app.js` 통과
- FastAPI 라우터 검증:
  - `/user` 200
  - `/admin` 200
  - `/api/local-analysis/status` 200
- DB 검증:
  - `analysis_results_total`: 22
  - 활성 결과: 22
  - Gemini 기본 분석: 16건
  - Gemini 상세 분석: 1건
  - Codex app-server 상세 분석: 3건
  - Codex CLI 상세 분석: 2건
- 브라우저 검증:
  - 사용자 화면 카드 5건 렌더링 확인
  - `요약`, `Gemini 분석`, `ChatGPT 분석`, `비교`, `심층 요청`, `공고 원문 보기`, `작업 로그` 탭 렌더링 확인
  - 관리자 화면 Gemini/ChatGPT/Codex 집계 렌더링 확인
  - 관리자 화면 강제 재분석 버튼 50건 렌더링 확인

## 4. 현재 남은 한계 및 관리자 검토 필요 사항
- ChatGPT 웹 UI를 Playwright로 직접 조작하는 RPA 방식은 운영 안정성과 약관 리스크가 있어 아직 기본 경로로 넣지 않았다. 현재 ChatGPT 계열은 OpenAI API 또는 Codex CLI/app-server 상세 분석 경로로 분리했다.
- ChatGPT 기본 분석 결과는 아직 0건이다. API 키 또는 로컬 Codex 분석 정책을 확정한 뒤 기본 분석 배치 실행이 필요하다.
- 모델 비교는 현재 저장된 두 모델 결과의 핵심 필드를 비교하는 결정적 요약 방식이다. 추후 별도 비교 AI 프롬프트를 붙이면 품질을 더 높일 수 있다.
- 실패 job 4건은 관리자 화면에서 재시도 또는 보류 판단이 필요하다.

## 5. 실행 상태
- FastAPI 서버 재시작 완료
- 접속 URL:
  - 사용자 화면: `http://127.0.0.1:8000/user`
  - 관리자 화면: `http://127.0.0.1:8000/admin`
