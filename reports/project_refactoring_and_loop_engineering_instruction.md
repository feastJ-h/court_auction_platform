# 프로젝트 리팩토링 및 Loop Engineering 지시서

## 1. 목적

이 문서는 비동기 Codex CLI 상세 분석 구축 이후, 프로젝트를 지속적으로 개선 가능한 구조로 정리하기 위한 지시서다. 목표는 기능 추가가 누적될수록 코드와 문서가 흐트러지는 것을 막고, 매 Sprint마다 구현, 검증, 관찰, 리팩토링, 문서화가 반복되도록 만드는 것이다.

## 2. 리팩토링 목표

현재 프로젝트는 수집, 파싱, 기본 분석, 상세 분석, UI 표시가 빠르게 붙어 있는 상태다. 앞으로 Codex CLI 워커, Codex app-server, OCR, HWP 변환, 예약 분석이 추가되므로 계층을 명확히 나눈다.

목표 구조:

```text
backend/
  crawler/
  document_pipeline/
  analysis/
  ai_engine/
  jobs/
  analysis_worker/
  database/
  runtime_settings.py

frontend/
  templates/
  static/

reports/
  sprint reports
  architecture reports
  evaluation reports
  next instructions
```

## 3. 우선 리팩토링 항목

### 3.1 Job 계층 신설

분석 요청, 예약, 재시도, 실패 처리를 `backend/jobs`로 분리한다.

권장 파일:

```text
backend/jobs/models.py
backend/jobs/repository.py
backend/jobs/service.py
backend/jobs/scheduler.py
backend/jobs/status.py
```

### 3.2 Analysis Worker 계층 신설

Codex CLI와 app-server 호출은 웹 API에서 분리한다.

권장 파일:

```text
backend/analysis_worker/cli_worker.py
backend/analysis_worker/app_server_worker.py
backend/analysis_worker/prompt_builder.py
backend/analysis_worker/result_parser.py
backend/analysis_worker/schemas/
```

### 3.3 AI Provider 계층 정리

Gemini, OpenAI API, Codex CLI, Codex app-server를 같은 인터페이스로 감싼다.

권장 파일:

```text
backend/ai_engine/providers/base.py
backend/ai_engine/providers/gemini_provider.py
backend/ai_engine/providers/openai_provider.py
backend/ai_engine/providers/codex_cli_provider.py
backend/ai_engine/providers/codex_app_server_provider.py
```

### 3.4 Document Pipeline 계층 정리

PDF, HWP, OCR, 격리 저장 처리를 분석과 분리한다.

권장 파일:

```text
backend/document_pipeline/extractor.py
backend/document_pipeline/hwp_handler.py
backend/document_pipeline/ocr_handler.py
backend/document_pipeline/quarantine.py
backend/document_pipeline/storage.py
```

## 4. 문서화 산출물

각 단계가 끝날 때 다음 문서를 작성한다.

```text
reports/async_cli_analysis_phase_1_report.md
reports/async_cli_analysis_phase_2_report.md
reports/project_refactoring_summary.md
reports/project_build_summary_and_next_instructions.md
reports/evaluation_results.md
```

`project_build_summary_and_next_instructions.md`는 최종 인수인계 문서로 사용한다.

필수 포함 내용:

- 프로젝트 목적
- 지금까지 구현된 기능
- 주요 결정과 이유
- 현재 아키텍처
- 실행 방법
- DB 구조
- API 목록
- 워커 실행 방법
- 테스트 방법
- 실패 사례
- 남은 위험
- 다음 작업 지시

## 5. Sprint Loop 규칙

모든 후속 작업은 아래 루프를 따른다.

```text
1. Plan
2. Build
3. Verify
4. Observe
5. Refactor
6. Document
7. Next Instruction
```

각 단계 산출물:

- Plan: 목표, 범위, 완료 기준
- Build: 구현 변경 사항
- Verify: 테스트 결과
- Observe: 로그, 실패, 사용자 화면 확인
- Refactor: 정리한 코드와 남은 중복
- Document: 보고서와 지시서 업데이트
- Next Instruction: 다음 Sprint에서 바로 실행할 목록

## 6. 품질 기준

- 웹 요청 안에서 장시간 작업을 실행하지 않는다.
- 외부 사용자 입력을 셸 명령에 직접 연결하지 않는다.
- 원본 문서, 추출 텍스트, 분석 결과, 실패 로그는 추적 가능해야 한다.
- 분석 결과는 Markdown 표시용과 JSON 구조화 데이터를 모두 남긴다.
- 새 provider를 추가할 때 기존 provider를 깨지 않게 한다.
- 새 기능 추가 후에는 최소 하나의 실제 문서 샘플로 end-to-end 검증한다.

## 7. 다음 작업 지시

다음 Sprint는 `reports/async_cli_analysis_instruction.md`의 1차 구현부터 시작한다.

권장 순서:

1. `analysis_jobs` 테이블 추가
2. job 생성/조회 API 추가
3. 상세 분석 버튼을 비동기 방식으로 변경
4. `codex exec` 워커 추가
5. 실제 문서 1건으로 end-to-end 검증
6. `async_cli_analysis_phase_1_report.md` 작성
7. `project_refactoring_summary.md` 초안 작성

