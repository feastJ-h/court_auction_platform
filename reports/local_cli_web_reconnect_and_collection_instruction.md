# 로컬 CLI 분석 앱, 웹앱 재연결, 2026-06-15 이후 수집 지시서

## 1. 현재 정리된 운영 원칙

웹앱은 계속 실행해도 된다. 분석 워커는 사용자가 로컬 CLI에서 직접 실행한다. 웹앱과 분석 워커는 같은 DB와 파일 저장소를 공유하며, 웹앱이 분석을 직접 수행하지 않는다.

권장 분리:

```text
웹앱
  - 사용자 화면
  - 관리자 화면
  - 분석 요청 생성
  - 상태 조회

크롤링 도구
  - 법원 공고 수집
  - PDF/HWP 다운로드
  - DB 저장

로컬 분석 앱
  - Codex CLI 또는 Codex app-server 사용
  - PENDING job 처리
  - 분석 결과 저장
  - 분석 완료 파일 백업
```

## 2. app-server와 worker를 꼭 따로 띄워야 하는가

반드시 따로 띄울 필요는 없다. 내부 구조상 app-server와 worker는 역할이 다르지만, 사용자는 하나의 로컬 CLI 명령만 실행하도록 만들 수 있다.

역할 차이:

```text
codex app-server
  - Codex와 JSON-RPC로 통신하는 로컬 서버
  - thread/turn/event stream 담당

app-server worker
  - DB에서 PENDING job을 가져옴
  - app-server에 분석 요청
  - 결과를 DB와 파일로 저장
```

사용자 입장에서는 다음 하나만 실행하면 된다.

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\run_local_analysis_app.ps1 -Limit 1 -TimeoutSeconds 900 -IdleSleepSeconds 10
```

이 스크립트는 내부에서 app-server를 숨김 프로세스로 띄우고, 현재 CLI 창에서는 worker loop를 실행한다. Ctrl+C로 worker를 끄면 app-server도 함께 종료한다.

## 3. 웹앱과 분석 앱의 통신 방식

1차 안정 운영에서는 DB queue를 기본으로 사용한다.

```text
웹앱
  -> analysis_jobs에 PENDING 생성

분석 앱
  -> PENDING 감지
  -> RUNNING 변경
  -> storage/analysis_jobs/{job_id}/input.md 생성
  -> Codex 분석
  -> output.json / output.md 저장
  -> ai_analyses.detailed_analysis 저장
  -> SUCCEEDED 변경

웹앱
  -> 3초마다 상태 조회
  -> 완료 결과 표시
```

파일 변경 감지 방식도 가능하지만, 1차 운영에서는 보조 신호로만 둔다.

권장:

```text
Primary: DB queue
Secondary: storage/analysis_jobs/{job_id}/input.md 파일 생성
```

파일 감지만 단독으로 쓰면 DB 상태와 파일 상태가 어긋날 수 있으므로, 최종 상태의 기준은 DB로 둔다.

## 4. 현재 포트 정리 상태

정리 후 프로젝트 관련 포트는 다음 상태가 목표다.

```text
127.0.0.1:8000  웹앱만 실행
127.0.0.1:4500  닫힘 또는 사용자가 로컬 분석 앱 실행 시에만 열림
0.0.0.0:8080    닫힘
```

현재 웹앱 접속:

```text
http://127.0.0.1:8000
```

포트 확인:

```powershell
netstat -ano | Select-String -Pattern ':4500|:8000|:8080'
```

## 5. 사용자가 로컬에서 실행할 명령

### 웹앱만 실행

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\run_fastapi.ps1
```

### 로컬 분석 앱 실행

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\run_local_analysis_app.ps1 -Limit 1 -TimeoutSeconds 900 -IdleSleepSeconds 10
```

### mock 분석 테스트

```powershell
.\run_local_analysis_app.ps1 -Limit 1 -Mock
```

### 기존 exec worker fallback

```powershell
.\run_cli_analysis_worker_forever.ps1 -Limit 1 -TimeoutSeconds 900 -IdleSleepSeconds 10
```

## 6. 2026-06-15 이후 수집 상태

추가된 스크립트:

```text
collect_since_2026_06_15.ps1
```

실행:

```powershell
cd C:\Users\xogns\Documents\testAuction\court_auction_platform
.\collect_since_2026_06_15.ps1 -Limit 50
```

이번 실행 결과:

```text
다운로드 확인: 10건
중복 스킵: 10건
새 저장: 0건
```

현재 DB:

```text
raw_documents: 10건
asset_events: 10건
ai_analyses: 9건
analysis_jobs: 13건
```

현재 저장된 공고일:

```text
2026-07-02: 1건
2026-07-03: 9건
```

주의: 현재 크롤러는 첫 목록에서 잡히는 상세 페이지를 기준으로 수집한다. 따라서 2026-06-15 이후 조건은 추가되었지만, 실제로 6월 15일까지 넓게 수집하려면 법원 목록의 페이지네이션 또는 검색 기간 조건 처리가 추가로 필요하다.

## 7. 다음 개발 필요 항목

### 7.1 크롤링 개선

현재 필요한 개선:

- 법원 공고 목록 페이지네이션 지원
- 시작일/종료일 검색 조건 입력 지원
- `2026-06-15 <= notice_date`가 될 때까지 여러 페이지 순회
- 중복 파일은 해시로 건너뛰고, 기존 문서의 evidence는 갱신
- 수집 결과 보고서 자동 생성

권장 완료 기준:

```text
2026-06-15 이후 공고 전체를 조회
기존 7월 10건 외 6월 하순 데이터가 있으면 DB에 추가 저장
수집 범위와 누락 사유를 reports에 기록
```

### 7.2 분석 앱 개선

- `run_local_analysis_app.ps1`를 표준 실행 명령으로 정리
- app-server 연결 실패 시 사용자에게 명확한 메시지 출력
- 분석 완료 후 원본/입력/결과 파일을 `storage/processed/analyzed_documents`에 백업
- `analysis_jobs`에 `backup_path` 필드 추가 검토
- 웹 관리자 화면에 "로컬 분석 앱 실행 필요" 상태 표시

### 7.3 웹앱 개선

- 대기/진행/실패/완료 job 카운트 표시
- 워커가 꺼져 있으면 "요청은 접수됨, 로컬 분석 앱을 실행해야 처리됨" 표시
- 분석 요청이 큐에 들어간 시각 표시
- 상세 분석 결과가 mock인지 실제 Codex 분석인지 구분 표시

### 7.4 파일 감지 방식 보조 도입

선택 사항:

```text
storage/analysis_requests/{job_id}.json 생성
로컬 분석 앱이 폴더 감지
처리 완료 후 storage/analysis_results/{job_id}.json 생성
웹앱은 DB 갱신 기준으로 최종 표시
```

이 방식은 외부 도구 연동에는 좋지만, 현재 프로젝트 내부에서는 DB queue가 더 안정적이다.

## 8. 권장 최종 구조

```text
도구 1: 웹앱
  - 항상 켜둠
  - 포트 8000

도구 2: 크롤링 도구
  - 필요할 때 실행
  - 날짜 범위 수집
  - DB 저장

도구 3: 로컬 분석 앱
  - 사용자가 CLI에서 실행
  - app-server + worker를 한 명령으로 관리
  - 분석 결과 저장 및 백업
```

이 구조가 가장 단순하고, 운영 중 어떤 프로세스가 무엇을 하는지 추적하기 쉽다.

