# 프로젝트 빌드 요약 및 다음 작업 지시

## 1. 프로젝트 목적
법원 회생·파산 공고의 PDF/HWP 첨부파일을 수집하고, 문서 텍스트를 추출한 뒤, AI 기본 분석과 상세 심층 분석을 통해 매입/매각 검토에 필요한 정보를 웹에서 확인하는 플랫폼이다.

## 2. 현재 구현된 기능
- Playwright 기반 법원 공고 수집
- PDF/HWP 파일 격리 저장
- 파일 해시 기반 중복 방지
- SQLite 기반 RawDocument, Asset, AssetEvent, AiAnalysis 저장
- Gemini/ChatGPT 선택형 기본 분석 구조
- 사용자 페이지 `/user`
  - 5건 페이징
  - 데스크톱 Split UI
  - 모바일 Accordion UI
  - 기본 분석, 상세 심층 분석, 공고 원문 보기 탭
- 관리자 페이지 `/admin`
  - 원본, 파싱 텍스트, AI 분석, 상세 분석 job 상태 조회
- Codex CLI 기반 비동기 상세 분석 job 구조
- Codex app-server 기반 thread/turn 상세 분석 job 구조
- 상세 분석 진행 이벤트 DB 저장 및 관리자/사용자 UI 노출
- 작업 취소 요청 및 이어서 분석 요청 API
- `run_local_analysis_app.ps1` 단일 명령 기반 로컬 분석 앱 실행 구조
- 관리자 화면 Local Analysis App 상태 배너
- 관리자 화면 기본/상세 분석 가시성 카드
- 실패/취소 상세 분석 job 재시도 버튼
- 분석 job 실행 모드 구분(`mock`, `codex_exec`, `codex_app_server`)
- `2026-06-15` 이후 수집용 페이지네이션 수집 스크립트
- 로컬 격리소 미등록 파일 DB 인입 스크립트
- 분석 완료 원본 PDF/HWP 보관소 이동
- 웹에서 원본 파일 열기
- 모델별 분석 결과 분리 저장(`analysis_results`)
- 사용자 화면 Gemini/ChatGPT/Codex 결과 탭 및 비교 탭
- 관리자 화면 모델별 결과 집계와 강제 재분석 버튼
- Worker heartbeat 기반 로컬 분석 워커 상태 표시
- 관리자 운영 필터, 실패 job, 멈춤 가능 job 섹션
- 수집/파일 품질 집계 API 및 관리자 섹션
- OCR/HWP/수동검토 문서 분석 준비 상태 guard
- 분석 품질 검수 테이블 및 API
- DB 백업 스크립트와 운영 Runbook
- 세션 쿠키 기반 간단 로그인
- 사용자별 PASSED 물건 제외/복구 기능
- 사용자 화면 정보량 축소 및 운영성 탭 제거
- 관리자 화면 및 관리자 API 접근 제한 기반

## 3. 주요 결정
- ChatGPT 웹 UI를 Playwright/Selenium으로 조작하는 RPA 방식은 운영 경로에서 제외했다.
- 상세 분석은 웹 요청에서 직접 실행하지 않고 `analysis_jobs` 큐를 통해 비동기로 처리한다.
- 1차 워커는 `codex exec`를 사용한다.
- 2차 워커는 `codex app-server`를 사용하며, `codex exec`는 fallback 경로로 유지한다.
- 실제 출력 파싱 안정성을 위해 `--output-last-message` 파일을 사용한다.
- 분석 완료 파일은 `storage/processed/analyzed_documents`로 이동한다.
- app-server는 로컬 루프백 주소(`ws://127.0.0.1:4500`)에서만 실행한다.

## 4. 주요 DB 테이블
- `raw_documents`
  - 원본 파일 경로, 원본 URL, SHA-256 해시
- `collection_evidence`
  - 게시글 제목, 첨부파일명, 작성일, 만료일, 상세 페이지 텍스트
- `assets`
  - 부동산/동산, 세부 카테고리, 주소
- `asset_events`
  - 내부 사건번호, 공고 상태, 파싱 상태, 추출 텍스트
- `ai_analyses`
  - 기본 분석, 입찰일, 리스크 코멘트, 상세 분석 Markdown
- `analysis_jobs`
  - 비동기 상세 분석 작업 상태, 파일 경로, 실패 원인, 결과 요약
- `analysis_job_events`
  - app-server/워커 진행 이벤트, 메시지, payload
- `analysis_results`
  - 모델별 기본/상세 분석 결과, 원문 해시, 결과 상태, supersede 이력
- `analysis_worker_heartbeats`
  - 로컬 분석 워커 상태, 현재 job, 마지막 감지 시간, PID
- `analysis_reviews`
  - 관리자 검수 점수, 환각 의심도, 메모
- `users`
  - 로그인 사용자, 비밀번호 해시, 역할
- `user_event_actions`
  - 사용자별 PASSED/관심/보류 등 물건 액션 기록

## 5. 주요 API
```text
GET  /user
GET  /login
POST /login
GET  /logout
GET  /user/passed
POST /user/events/{event_id}/pass
POST /user/events/{event_id}/unpass
GET  /admin
GET  /documents/raw/{raw_doc_id}
GET  /api/admin/collection-quality
GET  /api/admin/analysis-reviews/summary
POST /api/admin/analysis-results/{analysis_result_id}/reviews

POST /api/analyze/deep/{event_id}/jobs
GET  /api/analyze/jobs/{job_id}
GET  /api/analyze/deep/{event_id}/jobs/latest
POST /api/analyze/jobs/{job_id}/cancel
POST /api/analyze/jobs/{job_id}/cancel-request
POST /api/analyze/jobs/{job_id}/retry
GET  /api/analyze/jobs/{job_id}/events
POST /api/analyze/jobs/{job_id}/continue
```

## 6. 실행 방법
```powershell
# 웹 서버 실행
powershell -ExecutionPolicy Bypass -File .\run_fastapi.ps1

# 백그라운드 웹 서버 실행
powershell -ExecutionPolicy Bypass -File .\start_fastapi_background.ps1

# 법원 데이터 수집/기본 분석
powershell -ExecutionPolicy Bypass -File .\run_pipeline.ps1

# 상세 분석 job 일괄 등록
powershell -ExecutionPolicy Bypass -File .\enqueue_deep_analysis_jobs.ps1 -Limit 20

# Codex CLI 상세 분석 워커 실행
powershell -ExecutionPolicy Bypass -File .\run_cli_analysis_worker.ps1 -Limit 1

# Codex CLI 상세 분석 워커 상시 루프
powershell -ExecutionPolicy Bypass -File .\run_cli_analysis_worker_forever.ps1 -Limit 1 -IdleSleepSeconds 10

# Codex app-server 실행
powershell -ExecutionPolicy Bypass -File .\run_codex_app_server.ps1 -Endpoint ws://127.0.0.1:4500

# Codex app-server 상세 분석 워커 실행
powershell -ExecutionPolicy Bypass -File .\run_codex_app_server_worker.ps1 -Endpoint ws://127.0.0.1:4500 -Limit 1

# Codex app-server 상세 분석 워커 상시 루프
powershell -ExecutionPolicy Bypass -File .\run_codex_app_server_worker_forever.ps1 -Endpoint ws://127.0.0.1:4500 -IdleSleepSeconds 10

# 외부 호출 없이 mock 워커 검증
powershell -ExecutionPolicy Bypass -File .\run_cli_analysis_worker.ps1 -Limit 1 -Mock

# 외부 호출 없이 app-server mock 워커 검증
powershell -ExecutionPolicy Bypass -File .\run_codex_app_server_worker.ps1 -Limit 1 -Mock

# 권장: 로컬 분석 앱 단일 명령 실행
powershell -ExecutionPolicy Bypass -File .\run_local_analysis_app.ps1 -Limit 1 -TimeoutSeconds 900 -IdleSleepSeconds 10

# 권장: 로컬 분석 앱 1회 mock 테스트
powershell -ExecutionPolicy Bypass -File .\run_local_analysis_app.ps1 -Limit 1 -Mock -RunOnce

# 2026-06-15 이후 공고 수집
powershell -ExecutionPolicy Bypass -File .\collect_since_2026_06_15.ps1 -Limit 50 -MaxPages 15

# 이미 다운로드된 격리소 파일 DB 인입
powershell -ExecutionPolicy Bypass -File .\ingest_local_quarantine.ps1 -Limit 100
```

## 7. 테스트 결과
- Python 문법 검증 통과
- `/user`, `/admin`, `/api/analyze/jobs/1`, `/documents/raw/1` 200 응답 확인
- Codex CLI 설치 확인: `codex-cli 0.142.5`
- `codex exec --help`에서 필요한 옵션 확인
- Mock 상세 분석 end-to-end 2건 성공
- 원본 PDF 2건 `storage/processed/analyzed_documents`로 이동
- 사용자/관리자 UI 브라우저 검증 완료
- app-server mock 성공/실패/취소/이어가기 검증 완료
- 실제 `codex app-server` 연결 및 job #13 상세 분석 성공
- `/admin`에서 app-server thread/turn, 진행 이벤트, 상태 카운트 렌더링 확인
- 기본 분석 provider `chatgpt` 설정 확인
- 사용자 화면 상세 분석 완료 물건 우선 정렬 확인
- 관리자 화면 기본 분석/상세 분석/실패 사유/최근 이벤트/재시도 버튼 표시 확인
- `2026-06-15` 이후 수집 확장 결과 raw_documents 50건, asset_events 50건까지 확보
- Local Analysis App 상태 API `/api/local-analysis/status` 200 응답 확인
- `run_local_analysis_app.ps1 -Mock -RunOnce` 검증 완료
- `analysis_results` 활성 결과 22건 확인
- `/user`, `/admin`, `/api/local-analysis/status` 200 응답 재확인
- 브라우저에서 사용자 화면 5건 카드와 Gemini/ChatGPT/비교/작업 로그 탭 렌더링 확인
- 브라우저에서 관리자 화면 모델별 집계 및 강제 재분석 버튼 렌더링 확인
- 밤샘 Loop 1~10 완료
- Worker heartbeat mock 검증 완료
- 수집 품질: 원본 50건, 파일 누락 0건, 중복 hash 0건 확인
- OCR/HWP/수동검토 분석 준비 상태 guard 검증 완료
- 분석 품질 리뷰 API rollback 검증 완료
- DB 백업 스크립트 실행 및 SHA-256 출력 확인
- 로그인 전 `/user`, `/admin` 접근 차단 확인
- 기본 관리자 로그인 확인
- 사용자별 PASSED 저장/복구 확인
- 관리자 API 비로그인 401 확인

## 8. 알려진 한계
- 실제 `codex exec` 분석은 로그인된 Codex CLI 세션과 네트워크 상태에 의존한다.
- 스캔 PDF는 OCR 없이는 원문 텍스트가 비어 있을 수 있다.
- HWP 변환 실패 문서는 아직 수동 검수 또는 변환 큐가 필요하다.
- `codex app-server` delta 이벤트가 매우 세밀해 이벤트 테이블이 빠르게 커질 수 있다.
- `LOCAL_INGESTED` 항목은 원 상세 페이지 메타데이터가 부족해 일부 날짜가 `UNKNOWN`이다.
- 실패 job 4건이 남아 있어 관리자 검토 후 재시도 또는 보류 판단이 필요하다.
- API 라우터가 아직 `main_app.py`에 남아 있어 다음 단계에서 분리하는 것이 좋다.

## 9. 다음 Sprint 지시
1. 수집 파이프라인을 파일 1건 다운로드 즉시 DB 저장 방식으로 바꾼다.
2. `LOCAL_INGESTED` 및 `UNKNOWN` 날짜 항목의 관리자 검수 화면을 추가한다.
3. app-server delta 이벤트를 1초 또는 500자 단위로 묶어 저장하는 압축 정책을 추가한다.
4. OCR job 타입을 추가하고 `OCR_REQUIRED` 문서를 자동 큐잉한다.
5. HWP 변환 실패 상태를 세분화한다.
6. `main_app.py` 라우터를 `backend/api`로 분리한다.
7. 관리자 화면에 job 평균 처리 시간과 최근 실패 원인 통계를 추가한다.
8. ChatGPT 기본 분석 배치를 실행할지, Codex app-server 상세 분석만 ChatGPT 계열로 운영할지 정책을 확정한다.
9. 모델 비교 전용 AI 프롬프트와 비교 결과 저장 컬럼을 추가한다.
10. 관리자 화면에서 분석 품질 리뷰를 직접 입력하는 UI를 추가한다.
11. LOCAL_INGESTED와 UNKNOWN 날짜 항목을 상세 페이지 재방문으로 보강한다.
12. OCR job 큐와 OCR 실행기를 구현한다.
13. 사용자 계정 관리와 비밀번호 변경 기능을 추가한다.
14. BOOKMARKED/WATCHING 사용자 액션을 추가한다.
15. auth/user 라우터부터 `backend/api/routes`로 분리한다.

## 10. 다음 개인화 스프린트 반영 완료
- `/admin/users` 사용자 관리 화면을 추가했다.
- `/account/password` 비밀번호 변경 화면을 추가했다.
- 사용자 액션을 `BOOKMARKED`, `WATCHING`, `PASSED`로 확장했다.
- `/user/bookmarks`, `/user/watching` 개인 목록 화면을 추가했다.
- `/user` 카드에서 관심, 지켜보기, 패스를 바로 처리할 수 있게 했다.
- `/admin` 모델별 분석 결과 카드에서 관리자 검수 점수와 메모를 직접 저장할 수 있게 했다.
- 자기 계정 비활성화 방지, 중복 사용자 액션 방지, 비밀번호 해시 비노출을 확인했다.

## 11. 다음 스텝 제안
1. 관리자 검수 히스토리를 화면에 표시한다.
2. 사용자별 물건 메모와 태그를 추가한다.
3. 사용자 삭제 대신 비활성화/감사 로그 정책을 명확히 한다.
4. `main_app.py`에 모인 라우터를 `backend/api/routes`로 분리한다.
5. OCR_REQUIRED 문서를 실제 OCR 큐에 넣는 워커를 구현한다.
6. LOCAL_INGESTED/UNKNOWN 날짜 물건을 관리자 화면에서 보정할 수 있게 한다.

## 12. 운영 추적성 스프린트 반영 완료
- `user_event_notes` 테이블을 추가하고 사용자별 물건 메모/태그 저장 기능을 구현했다.
- `audit_logs` 테이블을 추가하고 사용자 액션, 계정 관리, 분석 검수 저장 로그를 남기도록 했다.
- 관리자 대시보드에 최근 검수 이력과 최근 운영 로그를 노출했다.
- 모델별 분석 결과 카드에서 해당 분석 결과의 검수 이력을 바로 확인할 수 있게 했다.
- `/user`와 개인 목록 화면에서 메모/태그를 저장할 수 있게 했다.

## 13. 다음 스프린트 권장 순서
1. `OCR_REQUIRED` 문서를 자동 OCR 큐에 넣고, OCR 결과를 기존 파싱 흐름으로 재투입한다.
2. `LOCAL_INGESTED`와 `UNKNOWN` 날짜/메타데이터를 관리자 화면에서 수동 보정할 수 있게 한다.
3. 테스트 전용 SQLite DB를 분리해 라우터 테스트가 운영 DB에 기록을 남기지 않게 한다.
4. 감사 로그 전용 검색/필터 페이지를 만든다.
5. `main_app.py`의 auth/user/admin 라우터를 `backend/api/routes`로 분리한다.

## 14. OCR/메타데이터/테스트 분리 스프린트 반영 완료
- `OCR_EXTRACTION` job type과 `local_ocr` provider를 추가했다.
- `OCR_REQUIRED` 문서를 큐잉하는 `backend/jobs/ocr_service.py`를 추가했다.
- mock OCR 워커 `backend/workers/ocr_worker.py`와 `run_ocr_worker.ps1`를 추가했다.
- 관리자 화면에서 물건별 OCR 큐 요청 버튼을 추가했다.
- 관리자 화면에서 등록일, 만료일, 파싱 상태, 제목을 보정하는 폼을 추가했다.
- `tests/isolated_operations_test.py`와 `run_isolated_operations_test.ps1`로 운영 DB와 분리된 테스트 흐름을 만들었다.
- 운영 DB 기준 OCR 큐 3건 생성, mock OCR 2건 성공 처리를 검증했다.

## 15. 다음 스프린트 권장 순서
1. OCR 엔진 어댑터 인터페이스를 만들고 Tesseract/PaddleOCR 중 하나를 연결한다.
2. `OCR_MOCKED`와 실제 OCR 완료 상태를 분리해 `OCR_PARSED` 정책을 확정한다.
3. OCR 완료 후 기본 AI 분석 큐로 자동 연결할지 관리자 승인 후 연결할지 결정한다.
4. 감사 로그 전용 검색/필터 페이지를 만든다.
5. `main_app.py`의 라우터를 `backend/api/routes`로 분리한다.

## 16. 무료 Tesseract OCR 연동 반영 완료
- 무료 로컬 OCR 기본 엔진을 Tesseract로 결정했다.
- `backend/ocr/tesseract_engine.py`를 추가해 PDF/이미지 OCR 어댑터를 구현했다.
- `run_ocr_worker.ps1`를 실제 Tesseract 모드, mock 모드, dry-run 모드로 분리했다.
- 실제 OCR 성공 상태 `OCR_PARSED`를 추가하고 mock 상태 `OCR_MOCKED`와 분리했다.
- 관리자 화면에 `Free OCR Engine` 상태 카드를 추가했다.
- `GET /api/admin/ocr/status` API를 추가했다.
- `.env`에 `TESSERACT_CMD`, `OCR_LANGUAGE`, `OCR_DPI`, `OCR_MAX_PAGES`를 추가했다.
- `docs/tesseract_ocr_setup.md` 설치 안내 문서를 추가했다.
- 현재 PC에는 `tesseract.exe`, `winget`, `choco`가 없어 실제 OCR 설치는 아직 필요하다.

## 17. 다음 스프린트 권장 순서
1. Tesseract OCR과 한국어 언어팩 설치 후 실제 스캔 PDF 1건을 OCR 처리한다.
2. `OCR_PARSED` 완료 문서를 기본 AI 분석 큐로 자동 연결하는 정책을 구현한다.
3. 관리자 화면에서 OCR 실패 사유별 재시도/보류 버튼을 분리한다.
4. 감사 로그 전용 검색/필터 페이지를 만든다.
5. `main_app.py` 라우터를 분리한다.

## 18. Tesseract 실제 OCR 및 명세 정리 완료
- `AGENTS.md`, `PROJECT_BRIEF.md`, `docs/sprint_execution_protocol.md`를 추가해 다음 작업 시 전체 소스 재검토를 줄이도록 했다.
- Tesseract OCR 설치 후 dry-run에서 엔진 감지를 확인했다.
- Poppler 변환 경로를 `pdftoppm.exe` 우선 사용으로 보강했다.
- event #43을 실제 Tesseract OCR로 처리해 `OCR_PARSED` 상태로 전환했다.
- OCR 결과 파일 `storage/processed/ocr_tesseract/event_43_ocr.txt`를 생성했다.
- 관리자 화면 필터가 `OCR_PARSED`, `OCR_MOCKED` 등 새 상태를 자동 반영하도록 개선했다.
- 백그라운드 FastAPI 시작 스크립트를 안정화했다.

## 19. 다음 스프린트 권장 순서
1. `OCR_PARSED` 문서에 대해 관리자 승인 기반 기본 AI 분석 실행 버튼을 추가한다.
2. OCR 실패 job에 대해 재시도/보류/수동 검수 완료 버튼을 분리한다.
3. OCR 결과 품질 검수 UI를 관리자 화면에 추가한다.
4. 감사 로그 검색/필터 페이지를 만든다.
5. `main_app.py` 라우터를 기능별 모듈로 분리한다.
