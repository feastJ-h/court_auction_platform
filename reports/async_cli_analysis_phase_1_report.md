# Async CLI Analysis Phase 1 완료 리포트

## 1. 구현된 주요 기능
- `analysis_jobs` 테이블을 추가하여 상세 분석 작업을 `PENDING`, `RUNNING`, `SUCCEEDED`, `FAILED`, `CANCELED` 상태로 추적합니다.
- 상세 분석 요청 API를 비동기 job 생성 방식으로 전환했습니다.
  - `POST /api/analyze/deep/{event_id}/jobs`
  - `GET /api/analyze/jobs/{job_id}`
  - `GET /api/analyze/deep/{event_id}/jobs/latest`
  - `POST /api/analyze/jobs/{job_id}/cancel`
  - `POST /api/analyze/jobs/{job_id}/retry`
- 기존 `POST /api/analyze/deep/{event_id}`는 호환용으로 유지하되, 내부적으로 job 생성 흐름으로 연결했습니다.
- `backend/analysis_worker/cli_worker.py`를 추가하여 `codex exec` 기반 비동기 상세 분석 워커를 구현했습니다.
- `run_cli_analysis_worker.ps1`을 추가하여 PowerShell에서 CLI 워커를 바로 실행할 수 있게 했습니다.
- `--mock` 모드를 추가하여 실제 Codex 호출 없이도 end-to-end 검증이 가능하게 했습니다.
- 분석 입력 스냅샷을 `storage/analysis_jobs/{job_id}/input.md`에 저장합니다.
- 분석 결과를 `output.json`, `output.md`, `stderr.log`로 분리 저장합니다.
- 분석 완료 후 기존 `ai_analyses.detailed_analysis`에 Markdown 리포트를 저장합니다.

## 2. 원본 PDF/HWP 보관 처리
- 분석 성공 시 원본 파일을 `storage/processed/analyzed_documents`로 이동하도록 구현했습니다.
- DB의 `raw_documents.file_path`를 새 보관 경로로 갱신합니다.
- 웹에서 `/documents/raw/{raw_doc_id}`로 원본 PDF/HWP를 열 수 있습니다.
- 수집 파이프라인에서 이미 존재하는 해시의 중복 다운로드 파일은 즉시 삭제하도록 보강했습니다.

## 3. 보안 및 예외 처리
- 사용자 입력을 셸 명령에 직접 연결하지 않고, 고정된 지시문과 입력 스냅샷 파일 경로만 CLI에 전달합니다.
- CLI 출력은 JSON 스키마 기반으로 검증하고, 파싱 실패 시 `CLI_OUTPUT_INVALID`로 기록합니다.
- CLI 미설치, 인증 실패, 타임아웃, 원문 없음, 파일 없음 오류를 구분할 수 있는 구조를 추가했습니다.
- 이미 상세 분석 결과가 있으면 새 job을 만들지 않고 `cached`로 반환합니다.
- 같은 물건에 `PENDING` 또는 `RUNNING` job이 있으면 중복 생성하지 않습니다.

## 4. 테스트 결과
- `py_compile`: 주요 신규/수정 Python 모듈 통과
- DB 마이그레이션: `analysis_jobs` 테이블 생성 확인
- API 테스트:
  - `/user`: 200
  - `/admin`: 200
  - `/api/analyze/jobs/1`: 200
  - `/documents/raw/1`: 200
- Codex CLI 설치 확인:
  - `codex-cli 0.142.5`
  - `codex exec --help`에서 `--json`, `--sandbox`, `--output-schema`, `--output-last-message` 옵션 확인
- Mock 워커 end-to-end:
  - Job #1: `SUCCEEDED`
  - Job #2: `SUCCEEDED`
  - `analysis_jobs`: 2건
  - 성공 job: 2건
  - 보관소 이동 문서: 2건
- 브라우저 검증:
  - 사용자 화면에서 상세 분석 결과, 원본 파일 링크, 원문 탭 표시 확인
  - 관리자 화면에서 상세 분석 Job 상태와 원본 파일 열기 링크 확인

## 5. 실행 방법
```powershell
# 상세 분석 job 생성은 웹에서 [분석 요청] 버튼 클릭

# 대기 job을 실제 Codex CLI로 1건 처리
powershell -ExecutionPolicy Bypass -File .\run_cli_analysis_worker.ps1 -Limit 1

# 실제 Codex 호출 없이 mock으로 검증
powershell -ExecutionPolicy Bypass -File .\run_cli_analysis_worker.ps1 -Limit 1 -Mock

# 아직 상세 분석이 없는 기본 분석 완료 건을 큐에 등록
powershell -ExecutionPolicy Bypass -File .\enqueue_deep_analysis_jobs.ps1 -Limit 20
```

## 6. 남은 이슈
- 실제 `codex exec` 분석은 인증된 로컬 CLI 세션에서 실행해야 합니다.
- `codex exec`의 실제 출력 품질은 샘플 문서별로 평가 데이터셋을 만들어 검수해야 합니다.
- OCR이 필요한 스캔 PDF는 별도 OCR 큐가 필요합니다.
- HWP 파싱 실패 문서는 변환/수동 검수 경로가 필요합니다.
