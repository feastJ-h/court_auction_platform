# 비동기 Codex CLI 상세 분석 구축 지시서

## 1. 최종 목표

웹앱에서 사용자가 상세 분석을 요청하면 웹 요청은 즉시 반환하고, 실제 상세 분석은 로그인된 Codex CLI 기반 워커가 비동기로 처리한다. 1차 구현은 `codex exec` 기반으로 빠르게 안정화하고, 2차 구현은 `codex app-server` 기반으로 확장해 진행 로그, 장기 thread, 중단/추가 지시, 이벤트 스트리밍까지 지원한다.

이 문서는 단발 구현 지시서가 아니라, 구현 이후에도 수집, 파싱, 분석, UI, 운영, 문서화가 반복 개선되는 loop engineering 기준 문서로 사용한다.

## 2. 기존 검토 통합 결론

기존 문서:

- `reports/chatgpt_rpa_and_marketability_review.md`
- `reports/analysis_tool_and_july_collection_report.md`
- `reports/sprint_6_report.md`
- `reports/rp_20260703_008_and_data_quality_report.md`

통합 결론:

- ChatGPT 웹 화면을 Playwright/Selenium으로 조작하는 RPA 방식은 로그인, 캡챠, UI 변경에 취약하므로 운영 경로에서 제외한다.
- OpenAI API 방식은 안정적이지만 사용량 기반 비용이 발생한다.
- 현재 프로젝트는 비용을 줄이면서 ChatGPT/Codex 로그인 세션과 로컬 파일 접근성을 활용하는 방향이 적합하다.
- 상세 분석은 동기 웹 요청이 아니라 작업 큐 기반 비동기 처리로 전환한다.
- 1차는 `codex exec` 워커, 2차는 `codex app-server` 확장, 3차는 운영 자동화와 품질 루프를 목표로 한다.

## 3. 전체 아키텍처

```text
웹앱
  - 상세 분석 요청
  - 예약 분석 요청
  - 작업 상태 조회
  - 결과 표시

분석 요청 API
  - job 생성
  - 중복 요청 방지
  - 캐시 결과 반환

Job DB
  - PENDING
  - RUNNING
  - SUCCEEDED
  - FAILED
  - CANCELED

1차 워커
  - codex exec 실행
  - 입력 스냅샷 파일 전달
  - JSON/Markdown 결과 저장

2차 워커
  - codex app-server 연결
  - thread 유지
  - 진행 이벤트 수신
  - 중단/추가 지시 지원

저장소
  - 원본 PDF/HWP
  - 추출 텍스트
  - OCR 결과
  - 분석 입력 스냅샷
  - 분석 결과
  - 실패 로그
```

## 4. 1차 구현: `codex exec` 기반 비동기 워커

### 4.1 목적

가장 작은 변경으로 웹앱의 동기 상세 분석을 비동기 분석 구조로 전환한다. 실시간 진행 로그보다 안정적인 작업 등록, 완료, 실패, 재시도 흐름을 우선한다.

### 4.2 구현 항목

1. `analysis_jobs` 테이블 추가
2. 상세 분석 job 생성/조회 API 추가
3. 기존 상세 분석 버튼을 job 생성 방식으로 변경
4. 작업 상태 폴링 UI 추가
5. 입력 스냅샷 생성기 추가
6. `codex exec` 워커 추가
7. 결과 JSON 검증 후 `ai_analyses.detailed_analysis` 저장
8. 실패 원인 저장 및 재시도 API 추가
9. 관리자 화면에 job 상태와 실패 사유 표시
10. 실제 PDF/HWP 샘플로 end-to-end 검증

### 4.3 DB 모델

새 테이블: `analysis_jobs`

권장 필드:

- `id`
- `event_id`
- `job_type`: `DEEP_ANALYSIS`
- `provider`: `codex_cli`
- `status`: `PENDING`, `RUNNING`, `SUCCEEDED`, `FAILED`, `CANCELED`
- `requested_by`: `user`, `admin`, `scheduler`
- `requested_at`
- `started_at`
- `finished_at`
- `attempt_count`
- `max_attempts`
- `input_snapshot_path`
- `output_json_path`
- `output_markdown_path`
- `stderr_log_path`
- `error_code`
- `error_message`
- `result_summary`

기존 `ai_analyses.detailed_analysis`는 웹 표시를 위해 유지한다. 상세 분석 생성 과정의 추적은 `analysis_jobs`가 담당한다.

### 4.4 API

```text
POST /api/analyze/deep/{event_id}/jobs
GET  /api/analyze/jobs/{job_id}
GET  /api/analyze/deep/{event_id}/jobs/latest
POST /api/analyze/jobs/{job_id}/cancel
POST /api/analyze/jobs/{job_id}/retry
```

동작 기준:

- 이미 `detailed_analysis`가 있으면 새 job을 만들지 않고 `cached`를 반환한다.
- 같은 `event_id`에 `PENDING` 또는 `RUNNING` job이 있으면 기존 `job_id`를 반환한다.
- job 생성 API는 분석을 직접 수행하지 않는다.
- 웹앱은 `job_id`로 상태를 폴링한다.

### 4.5 워커 파일 구조

```text
backend/analysis_worker/__init__.py
backend/analysis_worker/cli_worker.py
backend/analysis_worker/prompt_builder.py
backend/analysis_worker/result_parser.py
backend/analysis_worker/job_repository.py
backend/analysis_worker/schemas/deep_analysis.schema.json
run_cli_analysis_worker.ps1
```

워커 처리 순서:

1. `PENDING` job 조회
2. job을 `RUNNING`으로 변경
3. `storage/analysis_jobs/{job_id}/input.md` 생성
4. `codex exec` 실행
5. 출력 JSON 검증
6. Markdown 보고서 추출
7. `ai_analyses.detailed_analysis` 갱신
8. job을 `SUCCEEDED`로 변경
9. 실패 시 `FAILED`와 `error_code` 저장

### 4.6 Codex CLI 호출 방식

입력 본문을 명령 인자로 길게 넣지 않는다. 반드시 입력 스냅샷 파일을 만들고, CLI에는 파일 경로와 고정 지시만 전달한다.

예시:

```powershell
codex exec --json --sandbox workspace-write --output-schema .\backend\analysis_worker\schemas\deep_analysis.schema.json "storage/analysis_jobs/{job_id}/input.md 파일을 읽고 경매/공매 물건 상세 분석 JSON을 작성하라."
```

운영 기준:

- 실행 디렉터리는 `court_auction_platform`으로 고정한다.
- Codex CLI 로그인 세션은 신뢰된 로컬 또는 내부 서버에서만 사용한다.
- 인증 파일은 비밀번호처럼 취급한다.
- 외부 사용자가 입력한 자유 프롬프트를 CLI에 직접 전달하지 않는다.

### 4.7 출력 스키마

```json
{
  "summary": "",
  "asset_type": "",
  "price_opinion": "",
  "key_dates": [],
  "rights_and_legal_risks": [],
  "physical_or_market_risks": [],
  "required_follow_up_documents": [],
  "recommended_action": "",
  "confidence": "low",
  "markdown_report": ""
}
```

웹앱 상세 표시에는 `markdown_report`를 우선 사용하고, 목록 배지와 검색/필터에는 구조화 필드를 사용한다.

### 4.8 1차 완료 기준

- 상세 분석 버튼 클릭 후 웹 요청이 즉시 반환된다.
- 작업 상태가 대기, 진행, 완료, 실패로 표시된다.
- 동일 물건에 중복 상세 분석 job이 생성되지 않는다.
- 워커가 로컬 문서와 추출 텍스트를 읽어 분석 결과를 생성한다.
- 분석 결과가 기존 상세 분석 영역에 표시된다.
- CLI 인증 실패, 시간 초과, JSON 파싱 실패가 DB에 기록된다.
- 실패 job을 재시도할 수 있다.

## 5. 2차 구현: `codex app-server` 확장

### 5.1 목적

1차 워커가 안정화된 뒤, 분석 진행 상태를 더 세밀하게 보여주고 장기 thread 기반 분석을 지원한다. `codex exec`는 단발 작업에 적합하고, `codex app-server`는 연결을 유지하며 thread, turn, 이벤트 스트림을 다룰 수 있다.

### 5.2 전환 조건

다음 중 2개 이상 필요해지면 2차 구현으로 전환한다.

- 웹앱에서 실시간 분석 진행 로그를 보여줘야 한다.
- 분석 도중 사용자가 추가 지시를 넣어야 한다.
- 하나의 물건에 대해 여러 차례 이어지는 분석 thread가 필요하다.
- 분석 취소, 중단, 재개가 중요하다.
- 관리자 화면에서 Codex 이벤트를 직접 확인해야 한다.
- 워커 시작 비용이 커져 상시 연결이 유리하다.

### 5.3 추가 DB 필드

`analysis_jobs`에 다음 필드를 추가한다.

- `codex_thread_id`
- `codex_turn_id`
- `progress_message`
- `progress_percent`
- `last_event_at`
- `cancel_requested`

새 테이블 예시: `analysis_job_events`

- `id`
- `job_id`
- `event_type`
- `event_payload`
- `created_at`

### 5.4 app-server 브리지

추가 파일:

```text
backend/analysis_worker/app_server_client.py
backend/analysis_worker/app_server_worker.py
backend/analysis_worker/event_stream.py
run_codex_app_server_worker.ps1
```

역할:

- `codex app-server` 프로세스 시작 또는 기존 서버 연결
- `initialize` / `initialized` 수행
- thread 생성 또는 재개
- turn 시작
- 이벤트 수신
- 이벤트를 `analysis_job_events`에 저장
- 최종 agent message를 결과로 저장

### 5.5 UI 확장

추가 표시:

- 진행 로그 타임라인
- 현재 단계
- 마지막 이벤트 시간
- 취소 요청 버튼
- 이어서 분석 요청 버튼
- 관리자용 원문 이벤트 보기

### 5.6 2차 완료 기준

- app-server 기반 job이 생성되고 완료된다.
- 분석 진행 이벤트가 DB에 저장된다.
- 웹앱에서 진행 로그를 볼 수 있다.
- job 취소 요청이 워커에 전달된다.
- 기존 `codex exec` 방식으로 fallback 가능하다.
- thread id와 turn id가 저장되어 후속 분석에 재사용된다.

## 6. 3차 이후 추가 진행 권장 사항

### 6.1 OCR 파이프라인

스캔 PDF는 텍스트 추출이 비어 있을 수 있다. `OCR_REQUIRED` 상태를 별도 큐로 보내고, OCR 결과를 `extracted_text` 또는 별도 필드에 저장한다.

권장 순서:

1. PDF 텍스트 추출 실패 감지
2. OCR job 생성
3. OCR 결과 저장
4. 상세 분석 job 자동 생성

### 6.2 HWP 처리 안정화

HWP 파싱 실패 문서를 격리하고, 변환 가능 여부를 별도 상태로 관리한다.

권장 상태:

- `HWP_PARSED`
- `HWP_CONVERT_REQUIRED`
- `HWP_PARSE_FAILED`
- `MANUAL_REVIEW`

### 6.3 분석 품질 평가 데이터셋

분석 품질을 감으로 판단하지 않도록 샘플 케이스를 축적한다.

추가 산출물:

```text
reports/evaluation_cases/
reports/evaluation_results.md
```

평가 항목:

- 문서 사실 충실도
- 권리 리스크 식별
- 가격 판단 근거
- 일정/서류 누락 여부
- 환각 여부
- 사용자가 실제로 이해하기 쉬운지

### 6.4 API 병행 전략

다중 사용자 운영, 처리량, 감사 로그, 비용 추적이 중요해지면 OpenAI API 또는 다른 LLM API를 병행한다.

권장 구조:

- 기본 상세 분석: Codex CLI
- 대량 배치: API
- 실패 fallback: API 또는 Codex CLI
- 고위험/고가 물건: 두 엔진 교차 검토

### 6.5 운영 대시보드

관리자 화면에 다음 지표를 추가한다.

- 대기 job 수
- 실패 job 수
- 평균 처리 시간
- CLI 인증 상태
- 최근 실패 원인
- OCR 필요 문서 수
- HWP 실패 문서 수
- 분석 품질 검수 대기 수

## 7. 프로젝트 리팩토링 지시

비동기 분석 도입과 함께 다음 리팩토링을 진행한다.

### 7.1 분석 provider 추상화

현재 기본 분석, Gemini 상세 분석, 향후 Codex CLI 분석이 섞이지 않도록 provider 인터페이스를 나눈다.

권장 구조:

```text
backend/ai_engine/
  analyzer.py
  providers/
    gemini_provider.py
    openai_provider.py
    codex_cli_provider.py
    codex_app_server_provider.py
```

### 7.2 작업 처리 계층 분리

웹 API, DB 조회, 워커 실행, 결과 저장을 분리한다.

권장 구조:

```text
backend/jobs/
  models.py
  repository.py
  service.py
  scheduler.py
```

### 7.3 문서 처리 계층 정리

PDF/HWP/OCR 처리를 분석 엔진과 분리한다.

권장 구조:

```text
backend/document_pipeline/
  extractor.py
  hwp_handler.py
  ocr_handler.py
  quarantine.py
```

### 7.4 UI 상태 모델 정리

프론트엔드는 분석 결과 존재 여부와 job 상태를 혼동하지 않게 한다.

구분:

- 기본 분석 상태
- 상세 분석 job 상태
- 상세 분석 결과 상태
- 문서 파싱 상태
- OCR 상태

## 8. Loop Engineering 운영 방식

각 Sprint는 다음 루프를 반드시 따른다.

```text
Plan
  - 목표와 완료 기준 작성

Build
  - 작은 단위로 구현

Verify
  - 단위 테스트
  - API 테스트
  - 실제 샘플 문서 end-to-end 테스트

Observe
  - 실패 로그
  - 처리 시간
  - 사용자 화면 캡처
  - 분석 품질 검수

Refactor
  - 중복 제거
  - 계층 분리
  - 설정 정리

Document
  - 구현 결과
  - 남은 이슈
  - 다음 Sprint 지시서 업데이트
```

루프 규칙:

- 구현 완료 후 반드시 문서를 업데이트한다.
- 실패 사례는 삭제하지 말고 원인과 처리 방안을 기록한다.
- 분석 품질 개선은 프롬프트, 입력 데이터, 파서, UI 중 어느 층의 문제인지 구분한다.
- 다음 작업자가 이어받을 수 있도록 `다음 작업 지시`를 문서 말미에 남긴다.

## 9. 구축 후 반드시 작성할 문서

1차 구현 완료 후:

- `reports/async_cli_analysis_phase_1_report.md`
- `reports/project_refactoring_summary.md`

2차 구현 완료 후:

- `reports/async_cli_analysis_phase_2_report.md`
- `reports/codex_app_server_integration_report.md`

전체 정리 문서:

- `reports/project_build_summary_and_next_instructions.md`

전체 정리 문서에는 다음을 포함한다.

- 지금까지 구현된 기능 요약
- 기존 문서별 핵심 결론
- 현재 아키텍처
- DB 테이블과 주요 필드
- API 목록
- 워커 실행 방법
- 테스트 방법
- 알려진 한계
- 리팩토링 완료/미완료 항목
- 다음 Sprint 지시

## 10. 전체 완료 기준

- 1차 `codex exec` 기반 비동기 상세 분석이 동작한다.
- 2차 `codex app-server` 기반 진행 이벤트 수집이 동작한다.
- 실패/재시도/취소/예약 흐름이 웹앱과 DB에 반영된다.
- OCR/HWP 실패 문서의 후속 처리 경로가 정의된다.
- 프로젝트 구조가 provider, job, document pipeline 계층으로 정리된다.
- 구현 결과와 다음 지시가 문서화되어 다음 작업자가 맥락 없이도 이어갈 수 있다.

