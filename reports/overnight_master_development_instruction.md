# 밤샘 개발용 마스터 지시서

작성일: 2026-07-05

프로젝트: 법원 공고 수집/분석 플랫폼  
작업 위치: `C:\Users\xogns\Documents\testAuction\court_auction_platform`

## 0. 이 문서의 목적

이 문서는 다음 개발자가 사용자의 추가 확인 없이도 긴 시간 동안 이어서 개발할 수 있도록 만든 마스터 지시서다.

목표는 단순 기능 추가가 아니라, 다음 네 가지가 함께 굴러가는 견고한 프로젝트를 만드는 것이다.

```text
1. 법원 공고와 PDF/HWP 파일을 안정적으로 수집한다.
2. 수집된 파일을 로컬 CLI 기반 ChatGPT/Codex 분석 워커가 비동기로 분석한다.
3. Gemini 분석과 ChatGPT/Codex 분석을 모델별로 분리 저장하고 비교한다.
4. 사용자 화면과 관리자 화면에서 운영 상태, 분석 결과, 실패 원인을 명확하게 보여준다.
```

이 프로젝트는 개발 중이지만 서비스 운영을 염두에 둔다. 따라서 모든 작업은 다음 원칙을 지킨다.

- 웹앱 요청에서 직접 오래 걸리는 분석을 실행하지 않는다.
- 분석은 job 큐에 넣고, 로컬 CLI 워커가 비동기로 처리한다.
- 분석 워커는 사용자가 로컬에서 직접 실행한다.
- 웹앱은 워커가 꺼져 있어도 정상 동작해야 한다.
- 워커가 다시 켜지면 대기 중인 job을 이어서 처리해야 한다.
- 같은 파일, 같은 모델, 같은 분석 유형을 불필요하게 반복 분석하지 않는다.
- Gemini와 ChatGPT/Codex 결과는 덮어쓰지 않고 각각 보존한다.
- 관리자 화면은 “무엇이 진행 중이고 무엇이 막혔는지”를 바로 알려야 한다.
- 사용자 화면은 “분석 완료된 물건을 먼저, 법원 등록 순서에 맞게” 보여주어야 한다.

## 1. 현재 프로젝트 기준선

### 1.1 주요 실행 파일

```text
main_app.py
  FastAPI 웹앱 진입점
  /user 사용자 화면
  /admin 관리자 화면
  분석 job API
  로컬 분석 앱 상태 API

orchestrator.py
  법원 공고 수집/다운로드/분석 파이프라인
  2026-06-15 이후 수집 확장 함수 포함

run_fastapi.ps1
  웹앱 실행

start_fastapi_background.ps1
  웹앱 백그라운드 실행

run_local_analysis_app.ps1
  Codex app-server와 app-server worker를 함께 실행하는 권장 로컬 분석 명령

run_cli_analysis_worker.ps1
  codex exec 방식의 단발 분석 worker

run_cli_analysis_worker_forever.ps1
  codex exec 방식 반복 worker

run_codex_app_server.ps1
  Codex app-server 실행

run_codex_app_server_worker.ps1
  Codex app-server worker 단발 실행

run_codex_app_server_worker_forever.ps1
  Codex app-server worker 반복 실행

collect_since_2026_06_15.ps1
  2026-06-15 이후 공고 수집

ingest_local_quarantine.ps1
  이미 로컬에 받은 파일을 DB에 인입
```

### 1.2 주요 백엔드 모듈

```text
backend/config.py
  기본 설정
  기본 분석 provider는 chatgpt 방향

backend/runtime_settings.py
  런타임 분석 provider 저장/조회

backend/database/models.py
  RawDocument
  CollectionEvidence
  Asset
  AssetEvent
  AiAnalysis
  AnalysisResult
  AnalysisJob
  AnalysisJobEvent

backend/database/crud.py
  사용자/관리자 목록 조회
  기본 분석 저장
  사용자 화면 정렬

backend/database/analysis_results.py
  모델별 분석 결과 저장/조회
  Gemini/ChatGPT/Codex 결과 정규화

backend/jobs/repository.py
  analysis_jobs 상태 변경
  대기 job 조회
  진행률/취소/재시도 처리

backend/jobs/service.py
  API에서 사용하는 job 서비스 계층

backend/jobs/event_repository.py
  job event 저장/조회

backend/analysis_worker/cli_worker.py
  codex exec 기반 worker

backend/analysis_worker/app_server_worker.py
  codex app-server 기반 worker

backend/analysis_worker/app_server_client.py
  app-server 연결 클라이언트

backend/analysis_worker/prompt_builder.py
  상세 분석 프롬프트 생성

backend/analysis_worker/result_parser.py
  분석 결과 파싱

backend/document_pipeline/extractor.py
  문서 텍스트 추출

backend/document_pipeline/hwp_handler.py
  HWP 처리

backend/document_pipeline/ocr_handler.py
  OCR 처리

backend/document_pipeline/quarantine.py
  격리 파일 처리

backend/document_pipeline/storage.py
  저장소 경로/파일 이동 처리
```

### 1.3 현재 구현된 핵심 기능

이미 구현된 것으로 간주한다.

```text
1. FastAPI 웹앱
2. 사용자 페이지 /user
3. 관리자 페이지 /admin
4. SQLite 기반 DB
5. 법원 공고 수집
6. PDF/HWP 다운로드 및 로컬 저장
7. raw_documents, asset_events, ai_analyses 저장
8. analysis_jobs 기반 비동기 상세 분석 job 구조
9. analysis_job_events 기반 진행 이벤트 저장
10. codex exec worker
11. codex app-server worker
12. run_local_analysis_app.ps1 단일 실행 명령
13. ChatGPT 기본 provider 전환
14. Gemini/ChatGPT 결과를 분리하려는 analysis_results 구조
15. 사용자 화면에서 분석 완료 항목을 우선 정렬하는 방향
16. 관리자 화면에서 분석 상태, 실패, 재시도, 취소 요청 표시 방향
17. 2026-06-15 이후 수집 확장 스크립트
18. 로컬 격리 파일 DB 인입 스크립트
```

단, 이미 구현되어 있더라도 다음 항목은 반드시 재검증한다.

```text
1. 실제 DB에 테이블이 생성되어 있는가
2. AnalysisResult가 실제 화면과 job 완료 과정에 연결되어 있는가
3. Gemini/ChatGPT 결과가 덮어쓰기 없이 저장되는가
4. 중복 분석 방지가 실제 job 생성 전에 작동하는가
5. 관리자 화면의 한글 문구가 깨지지 않는가
6. /user, /admin, 주요 API가 모두 200 응답하는가
7. 워커가 꺼져 있을 때도 웹앱이 정상 동작하는가
```

## 2. 최종 목표 아키텍처

### 2.1 세 도구 분리

최종 구조는 세 도구로 분리하되, 초기 운영은 단순한 명령으로 시작한다.

```text
crawler tool
  역할:
    법원 공고 목록 수집
    상세 페이지 확인
    PDF/HWP 다운로드
    중복 파일 제거
    수집 증거 저장
    DB 저장

analysis app
  역할:
    analysis_jobs 큐 확인
    로컬 Codex/ChatGPT CLI 또는 app-server 호출
    상세 분석 실행
    결과 Markdown/JSON 저장
    AnalysisResult 저장
    원본 파일 백업/이동
    진행 이벤트 저장

web app
  역할:
    사용자 목록/상세 표시
    관리자 운영 상태 표시
    분석 요청 생성
    분석 결과 조회
    실패/재시도/취소/보류 관리
```

### 2.2 권장 운영 흐름

웹앱 실행:

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\run_fastapi.ps1
```

분석 워커 실행:

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\run_local_analysis_app.ps1 -Limit 1 -TimeoutSeconds 900 -IdleSleepSeconds 10
```

검증용 mock 실행:

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\run_local_analysis_app.ps1 -Limit 1 -Mock -RunOnce
```

### 2.3 비동기 처리 규칙

분석 요청은 다음 순서로 흐른다.

```text
1. 사용자 또는 관리자가 분석 요청
2. 웹앱은 analysis_jobs에 PENDING job 생성
3. 같은 조건의 성공 결과가 있으면 새 job을 만들지 않고 CACHED 처리
4. 같은 조건의 PENDING/RUNNING job이 있으면 기존 job을 반환
5. 로컬 분석 워커가 PENDING job을 가져감
6. job 상태를 RUNNING으로 변경
7. input snapshot 저장
8. Codex/ChatGPT 분석 실행
9. 결과 JSON/Markdown 저장
10. analysis_results에 모델별 결과 저장
11. ai_analyses legacy 필드에는 대표 결과만 동기화
12. 원본 파일을 analyzed_documents 또는 백업 위치로 이동
13. job 상태를 SUCCEEDED로 변경
14. 실패 시 FAILED와 오류 메시지 저장
```

## 3. 반드시 지켜야 할 개발 원칙

### 3.1 안전 원칙

- 사용자가 만든 기존 파일과 DB를 임의로 삭제하지 않는다.
- 실제 분석 워커를 장시간 실행하는 작업은 사용자가 켜는 전제로 둔다.
- 테스트는 먼저 mock worker로 한다.
- 포트를 닫거나 프로세스를 종료해야 할 경우 반드시 의도를 명확히 한다.
- DB 스키마 변경 전에는 백업 또는 마이그레이션 경로를 준비한다.
- 기존 `ai_analyses`를 바로 제거하지 않는다.
- 기존 Gemini 결과를 덮어쓰지 않는다.
- API key가 필요한 기능은 key가 없을 때도 화면이 깨지지 않아야 한다.

### 3.2 사용자 경험 원칙

사용자 화면:

- 분석 완료 물건이 먼저 보여야 한다.
- 분석 미완료 물건도 목록에서 사라지면 안 된다.
- 법원 등록일 기준 최신순 흐름을 유지해야 한다.
- Gemini/ChatGPT 분석 완료 상태가 직관적으로 보여야 한다.
- 모델 간 판단 차이가 있으면 표시해야 한다.
- 원문 PDF/HWP를 열 수 있어야 한다.
- 모바일에서 글자와 버튼이 겹치면 안 된다.

관리자 화면:

- 워커가 켜져 있는지 바로 보여야 한다.
- 대기/진행/성공/실패/취소 job 수가 보여야 한다.
- 현재 어떤 물건이 분석 중인지 보여야 한다.
- 오래 멈춘 job을 감지해야 한다.
- 실패 사유와 최근 이벤트가 보여야 한다.
- 재시도, 취소 요청, 보류, 강제 재분석이 가능해야 한다.
- Gemini와 ChatGPT/Codex 결과를 각각 볼 수 있어야 한다.

### 3.3 분석 품질 원칙

- 분석 결과에는 원문 근거가 있어야 한다.
- 가격, 날짜, 사건번호는 구조화해서 저장한다.
- 권리 위험, 점유, 명도, 체납, 법정지상권, 공유자 이슈 등은 별도 항목으로 정리한다.
- “확실함”과 “확인 필요”를 구분한다.
- 원문에 없는 내용을 단정하지 않는다.
- hallucination 의심 결과는 사용자 화면에서 주의 표시한다.

## 4. 데이터 모델 목표

### 4.1 기존 테이블 유지

기존 테이블은 호환성을 위해 유지한다.

```text
raw_documents
collection_evidence
assets
asset_events
ai_analyses
analysis_jobs
analysis_job_events
analysis_results
```

### 4.2 analysis_results 역할

`analysis_results`는 앞으로의 핵심 분석 결과 테이블이다.

필수 의미:

```text
event_id
  어떤 공고/물건의 분석인지

model_provider
  gemini
  chatgpt
  codex_cli
  codex_app_server

model_name
  실제 모델명 또는 실행 방식

analysis_type
  basic
  deep
  comparison
  followup

source_hash
  원본 문서 hash

status
  PENDING
  RUNNING
  SUCCEEDED
  FAILED
  CANCELED
  CACHED

prompt_version
  분석 프롬프트 버전

superseded_at
  강제 재분석으로 대체된 과거 결과 표시
```

중복 방지 기준:

```text
event_id + model_provider + analysis_type + source_hash + prompt_version + superseded_at is null
```

현재 코드에 `prompt_version`이 중복 방지 조건에 빠져 있으면 추가한다.

### 4.3 ai_analyses 역할

`ai_analyses`는 당분간 legacy 대표 결과로 유지한다.

권장 규칙:

```text
1. 사용자 화면 기본 요약은 ai_analyses 또는 대표 analysis_results를 사용한다.
2. ChatGPT/Codex deep 결과가 있으면 대표 결과로 우선 사용한다.
3. 없으면 Gemini deep 결과를 사용한다.
4. deep 결과가 없으면 basic 결과를 사용한다.
5. 장기적으로는 사용자 화면이 analysis_results를 직접 읽도록 바꾼다.
```

### 4.4 worker heartbeat 추가

다음 단계에서 반드시 추가한다.

권장 테이블:

```text
analysis_worker_heartbeats
  id
  worker_id
  worker_type
  provider_mode
  status
  current_job_id
  status_message
  last_seen_at
  started_at
  app_server_endpoint
  pid
```

상태:

```text
STARTING
IDLE
RUNNING
STOPPING
STOPPED
ERROR
UNKNOWN
```

관리자 화면은 이 테이블을 기준으로 “워커 켜짐/꺼짐/멈춤 가능성”을 판단한다.

## 5. API 목표

### 5.1 기존 API 유지

다음 API는 계속 동작해야 한다.

```text
GET  /
GET  /user
GET  /admin
GET  /documents/raw/{raw_doc_id}

POST /api/analyze/deep/{event_id}/jobs
GET  /api/analyze/jobs/{job_id}
GET  /api/analyze/deep/{event_id}/jobs/latest
POST /api/analyze/jobs/{job_id}/cancel
POST /api/analyze/jobs/{job_id}/cancel-request
POST /api/analyze/jobs/{job_id}/retry
GET  /api/analyze/jobs/{job_id}/events
POST /api/analyze/jobs/{job_id}/continue
GET  /api/local-analysis/status
```

### 5.2 추가 권장 API

다음 API를 추가한다.

```text
GET /api/admin/summary
  관리자 대시보드 요약

GET /api/admin/jobs
  상태/모델/기간 필터 가능한 job 목록

GET /api/admin/workers
  worker heartbeat 목록

GET /api/events/{event_id}/analysis-results
  모델별 분석 결과 조회

POST /api/events/{event_id}/analysis-results/request
  모델별 분석 요청

POST /api/events/{event_id}/analysis-results/force
  관리자 강제 재분석

GET /api/events/{event_id}/comparison
  Gemini/ChatGPT 비교 요약

GET /api/admin/collection-quality
  수집/파일 품질 상태

POST /api/admin/jobs/stale/mark-failed
  오래 멈춘 RUNNING job 정리
```

## 6. 화면 목표

### 6.1 사용자 화면

목표:

```text
분석 완료된 물건을 먼저 보여주고,
Gemini와 ChatGPT/Codex 결과를 쉽게 비교하며,
원문 근거를 확인할 수 있는 검토 화면으로 만든다.
```

목록 정렬:

```text
1. ChatGPT/Codex deep 분석 완료
2. Gemini deep 분석 완료
3. basic 분석만 완료
4. 분석 미완료
5. 각 그룹 안에서는 법원 등록일 최신순
6. 등록일이 같으면 id 오름차순
```

카드 표시 항목:

```text
사건번호
제목
물건 유형
주소
법원 등록일
마감일
입찰일
최저가
D-day
분석 완료 배지
Gemini 상태
ChatGPT/Codex 상태
모델 판단 차이 배지
권리 위험 요약
원문 보기 버튼
상세 보기 버튼
분석 요청 버튼
```

상세 보기 탭:

```text
요약
ChatGPT/Codex 분석
Gemini 분석
비교
원문
작업 로그
```

### 6.2 관리자 화면

목표:

```text
운영자가 분석 상태와 데이터 품질을 혼동하지 않도록 만든다.
```

상단 상태:

```text
전체 물건 수
분석 완료 수
분석 미완료 수
대기 job 수
진행 job 수
성공 job 수
실패 job 수
취소 job 수
워커 상태
app-server 상태
마지막 heartbeat
현재 분석 중인 사건번호
오래 멈춘 job 수
```

필터:

```text
분석 상태
job 상태
모델
분석 유형
법원 등록일
마감일
수집 상태
파일 유형
오류 유형
```

관리 기능:

```text
분석 요청
모델별 분석 요청
강제 재분석
재시도
취소 요청
보류
오래 멈춘 job 정리
원본 파일 열기
Markdown 결과 열기
JSON 결과 열기
이벤트 로그 보기
```

## 7. 밤샘 개발 실행 계획

아래 순서대로 진행한다. 앞 단계가 깨지면 다음 단계로 넘어가지 말고 해당 단계에서 복구한다.

## Loop 1. 상태 안정화와 깨진 한글/문구 점검

목표:

```text
/admin, /user, 주요 API가 안정적으로 열리고 한글 문구가 깨지지 않게 한다.
```

작업:

```text
1. /admin, /user가 200 응답하는지 확인
2. 템플릿 파일의 인코딩 확인
3. Python 소스 안에 깨진 한글 문자열이 있는지 확인
4. 깨진 한글 문구를 정상 한국어로 교체
5. compute_d_day_str, build_local_analysis_status, job progress message의 한글 문구 점검
6. 분석 상태 배지 문구 통일
7. 사용자 화면과 관리자 화면의 기본 버튼 문구 정리
```

검증:

```text
python -m py_compile main_app.py backend/config.py backend/runtime_settings.py backend/database/crud.py backend/database/models.py backend/database/analysis_results.py backend/jobs/repository.py backend/jobs/service.py

/admin 200
/user 200
/api/local-analysis/status 200
```

완료 보고서:

```text
reports/loop_1_status_text_stabilization_report.md
```

## Loop 2. Worker heartbeat 구현

목표:

```text
관리자 화면에서 분석 워커가 실제로 살아 있는지 판단할 수 있게 한다.
```

작업:

```text
1. AnalysisWorkerHeartbeat 모델 추가
2. init_db에서 테이블 생성 확인
3. repository/service 추가
4. cli_worker와 app_server_worker가 시작/대기/진행/오류 때 heartbeat 갱신
5. run_local_analysis_app.ps1에서 worker_id를 넘기거나 기본값 생성
6. /api/local-analysis/status가 heartbeat를 함께 반환
7. 관리자 화면에 마지막 감지 시간, 현재 job, 상태 메시지 표시
8. last_seen_at이 오래되면 "멈춤 가능성" 표시
```

멈춤 판단 기준:

```text
RUNNING job인데 last_event_at 또는 worker last_seen_at이 10분 이상 갱신되지 않으면 stale 표시
```

검증:

```text
1. 워커 꺼진 상태에서 /admin 확인
2. mock worker 1회 실행
3. heartbeat row 생성 확인
4. /api/local-analysis/status에 worker 정보 포함 확인
5. 관리자 화면에 마지막 감지 시간 표시 확인
```

완료 보고서:

```text
reports/loop_2_worker_heartbeat_report.md
```

## Loop 3. analysis_results 완성

목표:

```text
Gemini와 ChatGPT/Codex 결과가 모델별로 분리 저장되고 중복 분석을 막는다.
```

작업:

```text
1. analysis_results 테이블이 실제 DB에 있는지 확인
2. prompt_version을 중복 방지 조건에 포함
3. create_or_get_basic_result, create_or_get_deep_result의 provider 정규화 점검
4. job 완료 시 deep analysis 결과를 analysis_results에 저장하는지 확인
5. ai_analyses.detailed_analysis에는 대표 결과만 동기화
6. 강제 재분석 force=True일 때 기존 결과 superseded_at 설정
7. 같은 조건 재요청 시 새 job을 만들지 않고 기존 결과 또는 기존 job 반환
8. 결과 상태 CACHED 처리 방식 결정
```

중복 방지 규칙:

```text
성공 결과 있음 -> 새 job 생성 금지
PENDING/RUNNING job 있음 -> 기존 job 반환
source_hash 변경됨 -> 새 job 가능
prompt_version 변경됨 -> 새 job 가능
관리자 force=True -> 새 job 가능, 기존 active result superseded 처리
```

검증:

```text
1. 같은 event에 gemini basic 저장
2. 같은 event에 chatgpt basic 저장
3. 같은 event에 codex_app_server deep 저장
4. 세 결과가 analysis_results에 별도 row로 존재하는지 확인
5. 같은 요청 반복 시 row가 늘어나지 않는지 확인
6. force 요청 시 superseded_at이 채워지는지 확인
```

완료 보고서:

```text
reports/loop_3_analysis_results_report.md
```

## Loop 4. 관리자 화면 고도화

목표:

```text
관리자가 운영 상태, 분석 상태, 실패 원인, 모델별 결과를 한 화면에서 파악하게 한다.
```

작업:

```text
1. 상단 요약 카드 정리
2. worker 상태 배너 추가
3. job 상태별 필터 추가
4. 모델별 필터 추가
5. 실패 job 섹션 추가
6. 오래 멈춘 RUNNING job 섹션 추가
7. 물건별 Gemini/ChatGPT/Codex 결과 상태 표시
8. 모델별 분석 결과 펼쳐보기 추가
9. 최근 job event 보기 추가
10. 재시도/취소/강제 재분석 버튼 정리
11. 실행 명령 안내 영역 정리
```

화면에 반드시 있어야 하는 정보:

```text
사건번호
제목
법원 등록일
마감일
원본 파일 링크
기본 분석 provider
Gemini basic/deep 상태
ChatGPT basic/deep 상태
Codex deep 상태
최신 job 상태
진행률
최근 이벤트
실패 사유
재시도 버튼
취소 요청 버튼
```

검증:

```text
/admin 200
대기 job이 있을 때 상태 표시
실패 job이 있을 때 오류 메시지 표시
분석 결과가 있는 물건에서 모델별 결과 표시
모바일 폭에서 카드 겹침 없음
```

완료 보고서:

```text
reports/loop_4_admin_operations_report.md
```

## Loop 5. 사용자 화면 서비스화

목표:

```text
일반 사용자가 분석 완료 물건을 우선 검토하고 모델별 판단 차이를 이해할 수 있게 한다.
```

작업:

```text
1. 사용자 목록 정렬 쿼리 재점검
2. analysis_results 기반 완료 상태 계산
3. 분석 완료 우선 정렬 구현 확인
4. 법원 등록일 최신순 정렬 확인
5. Gemini/ChatGPT/Codex 상태 배지 추가
6. 모델 판단 차이 배지 추가
7. 상세 패널에 요약/모델별 분석/비교/원문 탭 추가
8. 분석 미완료 물건에는 "분석 대기/요청 가능" 상태 표시
9. 원문 링크 동작 확인
10. 모바일 UI 점검
```

사용자에게 보여줄 표현:

```text
분석 완료
분석 대기
ChatGPT 완료
Gemini 완료
모델 판단 차이 있음
원문 확인 필요
가격 확인 필요
권리 위험 확인 필요
```

검증:

```text
/user 200
분석 완료 물건이 앞쪽
미완료 물건이 뒤쪽
같은 그룹 안에서 등록일 최신순
상세 패널 탭 동작
모바일 화면 겹침 없음
```

완료 보고서:

```text
reports/loop_5_user_service_ui_report.md
```

## Loop 6. 크롤링/수집 품질 강화

목표:

```text
2026-06-15 이후 수집 데이터의 누락, 중복, 실패 파일을 관리 가능하게 만든다.
```

작업:

```text
1. collect_since_2026_06_15.ps1 실행 흐름 점검
2. 수집 페이지별 로그 저장
3. 다운로드 성공/실패 건수 저장
4. 같은 file_hash 중복 방지 확인
5. collection_evidence의 notice_date/expire_date UNKNOWN 항목 파악
6. LOCAL_INGESTED 항목과 실제 상세 페이지 수집 항목 구분
7. 관리자 화면에 수집 품질 섹션 추가
8. 실패 다운로드 재시도 대상 목록 생성
9. PDF/HWP 텍스트 추출 가능 여부 사전 검사
```

검증:

```text
수집 스크립트 dry-run 또는 제한 실행
중복 file_hash가 늘어나지 않는지 확인
UNKNOWN 날짜 항목 개수 표시
다운로드 실패 항목 표시
```

완료 보고서:

```text
reports/loop_6_collection_quality_report.md
```

## Loop 7. OCR/HWP 분석 준비 상태 분리

목표:

```text
텍스트가 비어 있거나 HWP 변환이 필요한 문서를 AI 분석 실패로 처리하지 않고 별도 상태로 관리한다.
```

작업:

```text
1. parse_status 값 체계 정리
2. OCR_REQUIRED 상태 추가 또는 정리
3. HWP_CONVERSION_REQUIRED 상태 추가 또는 정리
4. TEXT_EXTRACTION_FAILED 상태 추가 또는 정리
5. worker가 텍스트 부족 문서를 분석하지 않도록 guard 추가
6. 관리자 화면에 "분석 불가 원인" 표시
7. OCR job 큐 설계
8. HWP 변환 실패 로그 저장
```

권장 parse_status:

```text
PARSED
EMPTY_TEXT
OCR_REQUIRED
OCR_SUCCEEDED
OCR_FAILED
HWP_CONVERSION_REQUIRED
HWP_CONVERSION_FAILED
TEXT_EXTRACTION_FAILED
LOCAL_INGESTED
UNKNOWN
```

검증:

```text
텍스트 빈 문서가 analysis_jobs로 바로 들어가지 않는지 확인
관리자 화면에서 OCR 필요 문서 표시
HWP 실패와 AI 분석 실패가 구분되는지 확인
```

완료 보고서:

```text
reports/loop_7_ocr_hwp_readiness_report.md
```

## Loop 8. 분석 품질 평가 루프

목표:

```text
Gemini와 ChatGPT/Codex 분석 품질을 기록으로 비교할 수 있게 한다.
```

작업:

```text
1. golden case 20개 선정
2. 평가 테이블 설계
3. 관리자 검수 점수 입력 UI 설계
4. prompt_version별 결과 비교
5. 가격/날짜/권리위험/근거/환각 점수 저장
6. 모델별 승패 또는 주의 항목 표시
```

권장 테이블:

```text
analysis_reviews
  id
  analysis_result_id
  reviewer
  price_score
  date_score
  risk_score
  evidence_score
  hallucination_score
  notes
  created_at
```

검증:

```text
대표 사건 3개로 평가 입력
모델별 점수 요약 표시
prompt_version별 비교 가능
```

완료 보고서:

```text
reports/loop_8_analysis_quality_report.md
```

## Loop 9. 리팩토링

목표:

```text
main_app.py에 몰린 API/화면 로직을 나누고, 장기 유지보수가 가능한 구조로 만든다.
```

권장 분리:

```text
backend/api/routes/user.py
backend/api/routes/admin.py
backend/api/routes/jobs.py
backend/api/routes/documents.py
backend/api/routes/settings.py
backend/view_models/user_events.py
backend/view_models/admin_dashboard.py
backend/services/local_analysis_status.py
```

작업:

```text
1. main_app.py의 순수 helper와 route 분리 대상 표시
2. route를 작은 단위로 이동
3. 기존 URL 유지
4. TestClient로 /user, /admin, 주요 API 회귀 검증
5. 템플릿에서 사용하는 payload 구조 문서화
```

주의:

```text
리팩토링 중 UI 기능을 바꾸지 않는다.
먼저 테스트 가능한 작은 단위로 나눈다.
라우트 경로는 유지한다.
```

완료 보고서:

```text
reports/loop_9_refactoring_report.md
```

## Loop 10. 운영 준비

목표:

```text
서비스를 장시간 켜두어도 데이터와 파일이 망가지지 않게 한다.
```

작업:

```text
1. DB 백업 스크립트 추가
2. 원본 파일 백업 정책 문서화
3. 분석 완료 파일 이동 정책 점검
4. 로그 파일 크기 제한 또는 회전 정책 추가
5. 관리자 접근 제한 설계
6. 장애 복구 절차 문서화
7. 포트 사용 현황 확인 명령 정리
8. worker 재시작 절차 정리
9. 데이터 보존/삭제 정책 정리
```

권장 문서:

```text
reports/operations_runbook.md
reports/backup_and_restore_instruction.md
reports/local_worker_runbook.md
```

완료 보고서:

```text
reports/loop_10_operations_readiness_report.md
```

## 8. 검증 체크리스트

각 루프가 끝날 때 다음을 가능한 범위에서 확인한다.

```text
Python 문법 검증
FastAPI 앱 import 가능
/user 200
/admin 200
/api/local-analysis/status 200
mock worker 1회 성공
같은 분석 요청 중복 생성 방지
실패 job 표시
원본 파일 링크 동작
analysis_results 저장 확인
관리자 화면 깨짐 없음
사용자 화면 모바일 깨짐 없음
```

권장 Python 문법 검증:

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
python -m py_compile main_app.py backend/config.py backend/runtime_settings.py backend/database/crud.py backend/database/models.py backend/database/analysis_results.py backend/jobs/repository.py backend/jobs/service.py backend/analysis_worker/cli_worker.py backend/analysis_worker/app_server_worker.py
```

권장 웹 검증:

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\start_fastapi_background.ps1
```

이후:

```text
http://127.0.0.1:8000/admin
http://127.0.0.1:8000/user
```

## 9. 보고서 작성 규칙

각 루프가 끝나면 반드시 보고서를 남긴다.

보고서 파일명:

```text
reports/loop_N_short_name_report.md
```

보고서 구조:

```text
# Loop N 보고서

## 목표

## 변경한 내용

## 수정한 파일

## 검증 결과

## 남은 위험

## 다음 루프 지시
```

다음 루프 지시서가 필요하면 별도 파일로 남긴다.

```text
reports/loop_N_plus_1_instruction.md
```

## 10. 다음 개발자에게 주는 즉시 실행 지시

다음 개발자는 아래 순서로 시작한다.

```text
1. 이 문서를 먼저 읽는다.
2. reports/project_build_summary_and_next_instructions.md를 참고한다.
3. reports/continuous_loop_engineering_roadmap.md를 참고한다.
4. /admin, /user 현재 상태를 확인한다.
5. Loop 1부터 시작한다.
6. 실제 장시간 분석은 사용자에게 맡기고, 개발 검증은 mock worker로 한다.
7. 한 루프가 끝날 때마다 보고서를 남긴다.
8. 다음 루프의 시작 조건을 보고서에 적는다.
```

## 11. 절대 하지 말아야 할 것

```text
1. auction_data.db를 임의로 삭제하지 않는다.
2. storage 아래 원본 파일을 임의로 삭제하지 않는다.
3. 기존 Gemini 결과를 덮어쓰지 않는다.
4. 장시간 실제 Codex 분석을 사용자 동의 없이 백그라운드로 돌리지 않는다.
5. 포트를 강제로 닫기 전에 현재 사용 중인 프로세스를 확인하지 않고 종료하지 않는다.
6. UI 리팩토링 중 URL을 바꾸지 않는다.
7. main_app.py를 대규모로 옮기면서 검증 없이 끝내지 않는다.
8. API key가 없다는 이유로 웹앱 전체가 실패하게 만들지 않는다.
9. 텍스트가 비어 있는 문서를 AI 분석 실패로만 처리하지 않는다.
10. 사용자가 볼 화면에 내부 디버그 메시지를 그대로 노출하지 않는다.
```

## 12. 완료 상태의 모습

이 마스터 지시서가 목표로 하는 완료 상태는 다음과 같다.

```text
웹앱
  사용자는 분석 완료 물건을 먼저 본다.
  모델별 결과와 비교를 쉽게 본다.
  원문 파일을 열 수 있다.

관리자
  워커 상태를 바로 본다.
  대기/진행/실패 job을 관리한다.
  Gemini/ChatGPT/Codex 결과를 각각 본다.
  실패 원인과 이벤트 로그를 본다.

분석 워커
  로컬 CLI에서 사용자가 실행한다.
  대기 job을 자동으로 처리한다.
  진행 상태를 DB에 남긴다.
  실패해도 웹앱을 멈추지 않는다.

데이터
  원본 파일이 보존된다.
  중복 분석이 방지된다.
  모델별 결과가 분리 저장된다.
  강제 재분석 이력이 남는다.

운영
  백업과 복구 절차가 있다.
  오래 멈춘 job을 찾을 수 있다.
  수집/파일/분석 품질을 구분해서 관리한다.
  매 루프마다 보고서와 다음 지시서가 남는다.
```

## 13. 우선순위 요약

자고 오는 동안 하나씩 진행한다면 이 순서를 따른다.

```text
1. 깨진 한글/상태 문구 정리
2. worker heartbeat
3. analysis_results 중복 방지 완성
4. 관리자 화면 운영성 강화
5. 사용자 화면 모델 비교 UX 강화
6. 수집 품질/UNKNOWN/LOCAL_INGESTED 관리
7. OCR/HWP 준비 상태 분리
8. 분석 품질 평가 테이블
9. main_app.py 라우트 리팩토링
10. 백업/운영 runbook
```

각 단계는 작게 끝내고 검증한 뒤 다음 단계로 넘어간다.  
밤새 개발의 목적은 “많이 바꾸는 것”이 아니라 “아침에 사용자가 이어서 확인할 수 있는 안정된 상태를 남기는 것”이다.

