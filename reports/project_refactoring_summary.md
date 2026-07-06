# 프로젝트 리팩토링 요약

## 1. 이번에 정리한 계층

### Jobs 계층
추가 경로:
- `backend/jobs/status.py`
- `backend/jobs/repository.py`
- `backend/jobs/service.py`
- `backend/jobs/scheduler.py`

역할:
- 상세 분석 job 생성, 조회, 중복 방지, 취소, 재시도
- 스케줄러 기반 일괄 job 등록
- 웹 API와 워커가 동일한 job 상태 규칙을 사용하도록 분리

### Analysis Worker 계층
추가 경로:
- `backend/analysis_worker/cli_worker.py`
- `backend/analysis_worker/prompt_builder.py`
- `backend/analysis_worker/result_parser.py`
- `backend/analysis_worker/job_repository.py`
- `backend/analysis_worker/schemas/deep_analysis.schema.json`

역할:
- 웹 요청 밖에서 장시간 상세 분석 수행
- 입력 스냅샷 생성
- Codex CLI 실행
- 출력 JSON 검증
- 결과 Markdown 저장
- 실패 원인 기록

### Document Pipeline 계층
추가 경로:
- `backend/document_pipeline/storage.py`
- `backend/document_pipeline/extractor.py`
- `backend/document_pipeline/quarantine.py`
- `backend/document_pipeline/ocr_handler.py`
- `backend/document_pipeline/hwp_handler.py`

역할:
- 분석 완료 원본 문서 보관
- 기존 parser와 새 document pipeline 사이의 어댑터 제공
- OCR/HWP 변환 확장 지점 명시

### AI Provider 계층 초안
추가 경로:
- `backend/ai_engine/providers/base.py`
- `backend/ai_engine/providers/gemini_provider.py`
- `backend/ai_engine/providers/openai_provider.py`
- `backend/ai_engine/providers/codex_cli_provider.py`

역할:
- 기존 Gemini/ChatGPT 기본 분석 함수를 provider 형태로 감싸는 초안
- Codex CLI는 기본 분석이 아니라 `analysis_jobs` 기반 상세 분석 전용 provider로 분리

## 2. 유지한 기존 구조
- 기존 기본 분석 경로 `backend/ai_engine/analyzer.py`는 깨지지 않게 유지했습니다.
- 기존 파서 `backend/parser/extractor.py`도 유지하고, 새 document pipeline에서 re-export하는 방식으로 연결했습니다.
- 기존 `ai_analyses.detailed_analysis` 컬럼은 웹 표시용 캐시로 유지했습니다.

## 3. 개선된 운영성
- 웹 요청 안에서 장시간 AI 상세 분석을 수행하지 않습니다.
- 분석 결과와 실패 로그가 파일 및 DB에 남습니다.
- 분석 완료 원본 파일은 보관소로 이동되어 웹에서 직접 열 수 있습니다.
- 중복 다운로드 파일은 수집 파이프라인에서 삭제됩니다.

## 4. 남은 리팩토링
- `main_app.py`의 API 라우터를 `backend/api` 계층으로 분리
- `orchestrator.py`를 수집/파싱/기본분석 서비스 계층으로 분리
- `backend/ai_engine/analyzer.py`를 provider 기반 호출 구조로 완전히 전환
- OCR/HWP 변환 큐와 job 타입 추가
- `codex app-server` 기반 이벤트 스트림 워커 추가
