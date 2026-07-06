# 지속 개발 Loop Engineering 로드맵 지시서

작성일: 2026-07-05

## 1. 목적

이 문서는 현재 법원 공고 수집/분석 웹앱을 계속 개선하기 위한 다음 개발 지시서다.

기준 방향은 다음과 같다.

- 웹앱은 사용자가 결과를 쉽게 보고 요청할 수 있는 화면으로 유지한다.
- 크롤링, 분석, 웹앱을 역할별 도구로 나누되 운영은 단순하게 시작한다.
- 분석 워커는 사용자가 로컬에서 켜둔 Codex/ChatGPT CLI 환경에서 실행한다.
- 분석은 비동기 job으로 처리하고, 관리자 화면에서 진행 상태와 실패 원인을 확인할 수 있게 한다.
- Gemini 분석과 ChatGPT/Codex 분석은 서로 덮어쓰지 않고 모델별 결과로 보관한다.
- 같은 문서, 같은 모델, 같은 분석 유형의 중복 분석은 기본적으로 막는다.
- 매 단계는 구현, 검증, 관찰, 문서화, 다음 지시서 갱신까지 하나의 루프로 끝낸다.

## 2. 현재 기준선

현재 프로젝트의 주요 구성은 다음과 같다.

```text
web app
  - FastAPI
  - /user 사용자 화면
  - /admin 관리자 화면
  - SQLite auction_data.db

crawler tool
  - 법원 공고 목록 수집
  - PDF/HWP 다운로드
  - 2026-06-15 이후 수집 확장 스크립트
  - 로컬 격리 파일 DB 인입 스크립트

analysis app
  - analysis_jobs 큐
  - CLI worker
  - Codex app-server worker
  - job event 저장
  - 관리자 화면 상태 표시

documents
  - 기존 구현 보고서
  - app-server 2차 확장 지시서
  - 관리자/사용자 UI 개선 지시서
  - Gemini/ChatGPT 이중 모델 분석 지시서
```

기본 분석 도구는 ChatGPT/Codex 방향으로 전환되어 있으며, Gemini는 비교 가능한 별도 결과로 유지한다.

## 3. 운영 원칙

### 3.1 웹앱과 분석 워커

웹앱은 계속 켜두어도 된다. 분석 워커는 로컬 CLI에서 사용자가 직접 실행한다.

권장 실행 방식:

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\run_fastapi.ps1
```

분석이 필요할 때:

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\run_local_analysis_app.ps1 -Limit 1 -TimeoutSeconds 900 -IdleSleepSeconds 10
```

초기에는 app-server와 worker를 한 명령으로 함께 띄우는 방식을 유지한다. 운영이 커지면 다음과 같이 분리한다.

```text
1단계: run_local_analysis_app.ps1 하나로 app-server + worker 실행
2단계: app-server와 worker 분리 실행
3단계: worker heartbeat, 자동 재시작, 작업량 제한 추가
4단계: 별도 분석 머신 또는 서비스 프로세스로 확장
```

### 3.2 비동기 처리

웹에서 분석 요청 버튼을 누르면 즉시 분석을 끝내려고 하지 않는다.

기본 흐름:

```text
사용자/관리자 분석 요청
-> analysis_jobs 생성
-> 관리자 화면에 PENDING 표시
-> 로컬 분석 워커가 job 확인
-> RUNNING 변경
-> Codex/ChatGPT 분석
-> 결과 저장
-> 원본 파일 백업 또는 analyzed_documents 이동
-> SUCCEEDED/FAILED 표시
```

분석 워커가 꺼져 있으면 job은 대기 상태로 남는다. 워커를 다시 켜면 대기 작업부터 이어서 처리한다.

## 4. 다음 개발 우선순위

### 1순위: 운영 안정화

가장 먼저 해야 할 일은 “분석이 돌고 있는지 알 수 있는 상태”를 확실하게 만드는 것이다.

구현 항목:

- 관리자 화면 상단에 분석 앱 상태를 더 명확히 표시
- worker 마지막 응답 시간 표시
- 현재 처리 중인 사건번호 표시
- 대기/진행/성공/실패/취소 job 수 표시
- 오래된 RUNNING job을 감지해 “멈춘 작업 가능성”으로 표시
- 실패 job 재시도와 보류 버튼 제공
- 시작 명령, 테스트 명령, 정리 명령을 관리자 화면에 안내

완료 기준:

- 워커가 꺼져 있으면 관리자가 바로 알 수 있다.
- 워커가 켜져 있으면 마지막 감지 시간이 보인다.
- 분석이 오래 걸리는지, 멈췄는지 구분할 수 있다.
- 실패한 분석을 다시 요청할 수 있다.

### 2순위: Gemini/ChatGPT 이중 분석 저장 구조

현재의 단일 분석 결과 구조를 장기적으로 모델별 결과 구조로 확장한다.

권장 신규 테이블:

```text
analysis_results
  id
  event_id
  model_provider
  model_name
  analysis_type
  source_hash
  status
  item_details
  min_price
  bidding_date
  risk_comment
  detailed_analysis
  structured_json_path
  markdown_path
  prompt_version
  confidence
  created_at
  updated_at
  superseded_at
  run_count
```

중복 방지 기준:

```text
event_id + model_provider + analysis_type + source_hash + prompt_version
```

완료 기준:

- Gemini 결과와 ChatGPT 결과가 서로 덮어쓰지 않는다.
- 같은 조건의 성공 결과가 있으면 새 분석을 만들지 않는다.
- 강제 재분석은 관리자만 할 수 있다.
- 사용자 화면에서 두 모델 결과를 비교할 수 있다.

### 3순위: 사용자 화면 서비스화

사용자 화면은 개발자용 상태 확인 화면이 아니라 실제 검토용 화면으로 개선한다.

구현 항목:

- 분석 완료 물건을 앞으로 정렬
- 분석 미완료 물건은 뒤쪽으로 정렬
- 같은 그룹 안에서는 법원 등록일 기준 최신순 표시
- Gemini/ChatGPT 완료 배지 표시
- 모델별 위험 판단 차이가 있으면 “판단 차이 있음” 표시
- 기본 정보, 가격, 날짜, 권리 위험, 원문 근거를 한 화면에서 읽기 쉽게 배치
- 모바일에서도 카드가 너무 길어지지 않게 요약/펼침 구조 적용
- 상세 화면 또는 모달에서 Gemini, ChatGPT, 비교 탭 제공

완료 기준:

- 사용자가 분석 완료 물건부터 자연스럽게 검토할 수 있다.
- 분석되지 않은 물건도 목록에서 사라지지 않는다.
- 모델별 판단 차이를 놓치지 않는다.
- 모바일에서 글자가 겹치거나 버튼이 잘리지 않는다.

### 4순위: 관리자 화면 고도화

관리자 화면은 운영자가 “무엇이 막혔는지”를 바로 아는 화면이어야 한다.

구현 항목:

- 상태별 필터: 전체, 대기, 진행, 성공, 실패, 취소, 분석 없음
- 모델별 필터: Gemini, ChatGPT, Codex CLI, Codex app-server
- 기간 필터: 등록일, 마감일, 분석일
- 실패 원인별 그룹
- job 이벤트 로그 보기
- 분석 결과 원문 Markdown 보기
- 원본 PDF/HWP 바로 열기
- 대기열 전체 재시도, 선택 재시도, 선택 보류
- 너무 오래된 실패 job 정리 기능

완료 기준:

- 관리자가 문제 물건만 빠르게 볼 수 있다.
- 실패 이유가 화면에서 바로 보인다.
- 같은 분석을 불필요하게 여러 번 돌리지 않는다.
- 운영 중 DB와 파일 상태를 함께 확인할 수 있다.

### 5순위: 크롤링과 파일 인입 안정화

수집은 분석보다 앞단이므로 누락과 중복을 줄여야 한다.

구현 항목:

- 2026-06-15 이후 공고 수집 결과 재검증
- 페이지별 수집 로그 저장
- 공고 상세 페이지 URL 저장 강화
- PDF/HWP 다운로드 성공/실패 분리
- 같은 파일 hash 중복 저장 방지
- LOCAL_INGESTED, UNKNOWN 날짜 항목 정리 화면 추가
- 수집된 파일이 분석 가능한 텍스트를 포함하는지 사전 검사

완료 기준:

- 특정 기간의 수집 개수를 재현할 수 있다.
- 누락된 파일과 실패한 파일을 관리자 화면에서 볼 수 있다.
- 중복 파일이 분석 대기열을 오염시키지 않는다.

### 6순위: OCR/HWP 처리

PDF/HWP는 텍스트 추출 품질이 분석 품질을 결정한다.

구현 항목:

- 텍스트가 비어 있는 PDF를 OCR_REQUIRED로 표시
- OCR job 큐 추가
- OCR 결과와 원본 텍스트를 분리 저장
- HWP 변환 실패 상태를 명확히 저장
- HWP 변환 대체 경로 정리
- 관리자 화면에서 “분석 불가 원인” 표시

완료 기준:

- 텍스트 없는 문서는 분석 실패가 아니라 OCR 대기 상태가 된다.
- HWP 실패와 AI 분석 실패가 구분된다.
- 분석 워커는 텍스트 품질이 부족한 문서를 바로 분석하지 않는다.

### 7순위: 분석 품질 평가

분석 모델을 바꾸는 이유는 결과 품질을 올리기 위해서다. 따라서 평가 루프가 필요하다.

구현 항목:

- 대표 사건 20개를 golden case로 선정
- Gemini/ChatGPT 결과 비교표 생성
- 주요 평가 항목 정의
  - 가격 추출 정확도
  - 날짜 추출 정확도
  - 위험 요인 누락 여부
  - 원문 근거 포함 여부
  - 과장/환각 표현 여부
- 관리자 검수 점수 입력
- prompt_version별 품질 추적

완료 기준:

- “ChatGPT가 더 좋다”를 감각이 아니라 기록으로 확인할 수 있다.
- 프롬프트를 바꿨을 때 품질이 좋아졌는지 비교할 수 있다.
- 잘못된 분석을 사용자 화면에 그대로 노출하지 않는 기준이 생긴다.

### 8순위: 프로덕션 준비

서비스를 계속 켜둘 계획이라면 운영 보호 장치가 필요하다.

구현 항목:

- 관리자 로그인 또는 접근 제한
- DB 백업 스크립트
- 원본 파일 백업 정책
- 분석 완료 파일 보관 정책
- 로그 파일 회전
- 장기 실행 worker 재시작 가이드
- 장애 복구 절차
- 개인정보/민감정보 저장 여부 점검
- 비용 발생 API 호출과 로컬 CLI 호출 분리 표시

완료 기준:

- 웹앱, 수집, 분석을 각각 껐다 켜도 데이터가 망가지지 않는다.
- 운영자가 장애 발생 시 어떤 명령을 실행할지 안다.
- 분석 결과와 원본 파일이 추적 가능하게 남는다.

## 5. Loop Engineering 진행 방식

각 개발 단계는 다음 루프를 반드시 따른다.

```text
1. 목표 확정
2. 현재 상태 점검
3. 작은 범위 구현
4. 로컬 검증
5. 관리자/사용자 화면 확인
6. 실패 케이스 기록
7. 리팩토링
8. 지시서/보고서 갱신
9. 다음 루프 후보 선정
```

매 루프의 산출물:

```text
reports/YYYYMMDD_loop_N_report.md
reports/YYYYMMDD_loop_N_next_instruction.md
```

보고서에는 다음을 남긴다.

```text
무엇을 바꿨는가
왜 바꿨는가
어떤 파일을 수정했는가
어떤 검증을 했는가
남은 위험은 무엇인가
다음 루프에서 무엇을 해야 하는가
```

## 6. 다음 3개 루프 상세 지시

### Loop 1: 운영 상태 안정화

목표:

```text
관리자 화면에서 분석 워커와 job 상태를 신뢰할 수 있게 확인한다.
```

작업:

- worker heartbeat 테이블 또는 상태 파일 추가
- 워커 실행 시 last_seen_at 갱신
- 현재 job_id, 상태 메시지, 마지막 오류 저장
- 관리자 화면 상단에 worker 상태 표시
- 오래된 RUNNING job 경고 표시
- 실패 job 재시도/보류 UX 정리

검증:

- 워커 미실행 상태에서 관리자 화면 확인
- 워커 실행 후 상태 변경 확인
- mock job 1건 실행 후 PENDING -> RUNNING -> SUCCEEDED 확인
- 강제 실패 job 1건 생성 후 실패 사유 표시 확인

산출 문서:

```text
reports/loop_1_worker_status_report.md
reports/loop_2_dual_model_storage_instruction.md
```

### Loop 2: 이중 모델 결과 저장

목표:

```text
Gemini와 ChatGPT 분석 결과를 별도로 저장하고 비교 가능한 구조를 만든다.
```

작업:

- analysis_results 테이블 추가
- 기존 ai_analyses 호환 레이어 유지
- job 생성 시 model_provider, analysis_type, source_hash 확인
- 중복 분석 방지 로직 추가
- 관리자 화면에 모델별 결과 상태 표시
- 사용자 화면에 Gemini/ChatGPT 배지 표시

검증:

- 같은 문서에 Gemini basic, ChatGPT basic 결과를 각각 저장
- 같은 조건 재요청 시 새 job이 생기지 않는지 확인
- 강제 재분석 시 superseded 처리 확인
- 사용자 화면에서 두 모델 상태 확인

산출 문서:

```text
reports/loop_2_dual_model_storage_report.md
reports/loop_3_user_ui_service_instruction.md
```

### Loop 3: 사용자 화면 서비스화

목표:

```text
일반 사용자가 분석 완료 물건을 먼저 보고, 모델별 판단을 쉽게 비교한다.
```

작업:

- 목록 정렬 규칙 최종 확정
- 카드 정보 구조 개선
- 상세 보기 탭 추가
- 모델별 비교 요약 추가
- 분석 미완료 물건의 요청 버튼/상태 표시 정리
- 모바일 화면 점검

검증:

- 분석 완료/미완료 섞인 데이터로 정렬 확인
- Gemini만 있는 물건, ChatGPT만 있는 물건, 둘 다 있는 물건 확인
- 모바일 폭에서 텍스트 겹침 없음 확인
- 원문 PDF/HWP 링크 동작 확인

산출 문서:

```text
reports/loop_3_user_ui_service_report.md
reports/loop_4_crawler_file_quality_instruction.md
```

## 7. 이후 계속 진행하면 좋은 개발 후보

우선순위가 높은 후보:

- 관리자 화면에 “오늘 처리한 분석 수, 평균 처리 시간, 실패율” 표시
- 분석 job마다 예상 소요 시간과 실제 소요 시간 저장
- app-server 이벤트 로그를 너무 많이 저장하지 않도록 압축 저장
- 분석 프롬프트를 버전 관리하고 화면에서 prompt_version 확인
- 원문 일부와 분석 결론을 나란히 보여주는 근거 검증 화면
- 분석 결과를 Markdown 파일과 DB에 동시에 저장
- 분석 완료 후 원본 파일 백업 위치를 관리자 화면에서 확인
- 수집 실패 파일만 다시 다운로드하는 기능
- 수동 업로드 PDF/HWP 분석 요청 기능
- 분석 결과 내보내기: CSV, XLSX, Markdown
- 관리자 접근 제한
- 정기 DB 백업과 복구 테스트

나중에 검토할 후보:

- PostgreSQL 전환
- worker를 Windows 서비스 또는 작업 스케줄러로 등록
- Redis/RQ/Celery 기반 큐 전환
- 여러 대의 로컬 분석 머신 분산 처리
- 비용이 허용되는 범위에서 OpenAI API 분석 옵션 추가
- 브라우저 RPA 방식은 로그인/캡챠 리스크가 낮은 내부 보조 도구로만 제한

## 8. 다음 작업 시작 명령서

다음 개발자는 아래 순서로 시작한다.

```text
1. reports/project_build_summary_and_next_instructions.md 확인
2. reports/admin_operations_and_analysis_visibility_instruction.md 확인
3. reports/dual_model_analysis_and_user_ui_instruction.md 확인
4. 이 문서의 Loop 1부터 시작
5. 작은 변경 단위로 구현
6. /admin, /user, mock worker 검증
7. 보고서 작성
8. 다음 loop 지시서 갱신
```

실행 확인:

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\run_fastapi.ps1
```

분석 워커 확인:

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\run_local_analysis_app.ps1 -Limit 1 -Mock -RunOnce
```

실제 분석 워커:

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\run_local_analysis_app.ps1 -Limit 1 -TimeoutSeconds 900 -IdleSleepSeconds 10
```

## 9. 완료의 정의

이 로드맵의 단기 완료 기준은 다음과 같다.

- 관리자가 분석 상태를 혼동하지 않는다.
- 분석 워커가 꺼져도 job이 사라지지 않는다.
- 워커를 다시 켜면 대기 작업이 이어진다.
- Gemini/ChatGPT 결과가 분리 저장된다.
- 사용자는 분석 완료 물건을 먼저 볼 수 있다.
- 실패한 분석은 실패 이유와 재시도 경로가 보인다.
- 수집, 분석, 웹앱이 각각 독립적으로 개선 가능하다.
- 매 루프가 보고서와 다음 지시서를 남긴다.

