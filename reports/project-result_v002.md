# 프로젝트 상태 정리 v002

작성일: 2026-07-06

## 1. 프로젝트 한줄 요약

이 프로젝트는 회생/파산 사건 문서 수집과 AI 분석, 그리고 온비드 공매 물건 수집/조회 기능을 함께 제공하는 로컬 자산 분석 플랫폼이다. v002에서는 온비드 공고 API 저장 흐름과 관리자 관찰성이 강화되었다.

## 2. 큰 서비스 경계

### 회생/파산

- 법원 공고 문서 수집
- 원문 저장
- OCR 준비
- 사건/물건 후보 관리
- 사용자별 관심/제외/메모
- 관리자 AI 분석 job 관리
- ChatGPT/Codex 기반 분석 결과 관리

AI 분석은 현재 회생/파산 영역에 집중한다.

### 온비드 공매

- 부동산 물건 목록 수집
- 부동산 물건 상세 수집
- 동산 물건 목록 수집
- 동산 물건 상세 수집
- 공고 목록 수집
- 공고 상세 payload 저장
- 공고 물건정보를 `AuctionItem`으로 저장
- 공고와 물건의 연결 추적
- 관리자 수집/데이터 품질 관찰

온비드는 회생/파산 사건과 자동 연결하거나 전체 AI 분석을 자동 적용하지 않는다.

## 3. v001 대비 v002 변화

v001에서는 온비드 부동산/동산 목록과 상세 수집, 스케줄러 분리, 관리자 수집 화면 정리가 중심이었다.

v002에서 추가된 핵심:

- `AuctionNotice` 저장 구조 확장
- `AuctionNoticeItemLink` 신규 테이블
- 온비드 공고 목록/상세/공고 물건정보 샘플 및 수집 흐름
- `api_kind=notice`
- `--include-notice-details`
- `--include-notice-items`
- `/api/admin/onbid-quality`
- 관리자 수집 화면의 온비드 품질 카드
- 온비드 스케줄러 문서 정리
- 공고 저장 설계 문서와 migration ledger

## 4. 현재 주요 파일 구조

### Backend

- `main_app.py`: FastAPI 앱 진입점
- `backend/database/models.py`: SQLAlchemy 모델
- `backend/database/session.py`: DB 엔진, 세션, SQLite 보정 마이그레이션
- `backend/onbid/client.py`: 온비드 API 클라이언트와 샘플 payload
- `backend/workers/onbid_sync.py`: 온비드 수집 worker/CLI
- `backend/workers/scheduled_crawl.py`: 회생/파산 예약 수집 worker
- `backend/services/auction_items.py`: 온비드 물건/공고 upsert와 직렬화
- `backend/services/onbid_observability.py`: 온비드 데이터 품질 지표
- `backend/services/crawl_runs.py`: 수집 실행 이력과 스케줄 요약
- `backend/web/routers/auctions.py`: 온비드 공매 화면/API
- `backend/web/routers/admin_operations.py`: 관리자 운영 화면/API

### Frontend

- `frontend/templates/admin/collection.html`: 수집 운영 및 온비드 품질 화면
- `frontend/templates/auctions/index.html`: 온비드 물건 목록
- `frontend/templates/auctions/detail.html`: 온비드 물건 상세
- `frontend/templates/admin/dashboard.html`: 관리자 대시보드
- `frontend/templates/user/*.html`: 사용자 사건/관심/제외/메모 화면

### Scripts

- `run_onbid_sync.ps1`: 수동 온비드 수집
- `run_onbid_scheduled_sync.ps1`: lock 포함 온비드 예약 수집
- `run_scheduled_crawl.ps1`: 회생/파산 예약 수집
- `backup_database.ps1`: 운영 전 DB 백업 권장 스크립트

### Docs/Reports

- `docs/onbid_scheduled_sync_runbook.md`
- `docs/onbid_notice_persistence_design.md`
- `docs/migration_ledger.md`
- `docs/production_crawling_schedule_runbook.md`
- `reports/codex-devpack-v002-report.md`
- `reports/project-result_v002.md`
- `project-result_v001.md`

## 5. 현재 DB 모델 요약

### 회생/파산 관련

- `RawDocument`: 수집 원문 파일
- `CollectionEvidence`: 원문 출처/공고일/만료일 등 수집 근거
- `Asset`: 자산 기본 정보
- `AssetEvent`: 사건 단위 데이터
- `AiAnalysis`: 레거시 분석 결과
- `AnalysisResult`: 분석 결과 정규 저장
- `AnalysisJob`: 심층 분석 job
- `AnalysisJobEvent`: job 이벤트 로그
- `AnalysisWorkerHeartbeat`: 분석 worker 상태
- `AnalysisReview`: 분석 품질 리뷰
- `UserEventAction`, `UserEventNote`: 사용자 행동/메모

### 온비드 관련

- `AuctionItem`: 온비드 물건
- `AuctionItemSnapshot`: 수집 시점별 가격/상태 스냅샷
- `AuctionNotice`: 온비드 공고
- `AuctionNoticeItemLink`: 공고와 물건 연결
- `AuctionResult`: 낙찰/결과 저장 준비
- `CaseAuctionLink`: 회생/파산 사건과 온비드 물건의 수동/후보 연결
- `AuctionAlert`: 알림 준비 구조

## 6. 온비드 API 연동 상태

### 구현된 API 계열

- 부동산 물건목록: `OnbidRlstListSrvc2 / getRlstCltrList2`
- 부동산 물건상세: `OnbidRlstDtlSrvc2 / getRlstDtlInf2`
- 동산 물건목록: `OnbidMvastListSrvc2 / getMvastCltrList2`
- 동산 물건상세: `OnbidMvastDtlSrvc2 / getMvastDtlInf2`
- 공고목록: `OnbidPbancListSrvc2 / getPbancList2`
- 공고상세: `OnbidPbancDtlnfSrvc2 / getPbancDtlInf2`
- 공고상세 물건정보: `OnbidPbancCltrDtlSrvc2 / getPbancCltrInf2`

### 준비만 된 API

- 국유일반재산 입찰대상물건: `kamcoRlcBidTrgtCltr / cltrLst`

문서가 없어 v002에서는 실제 매핑을 보류했다. 설정 기반 호출 함수는 유지되어 있다.

## 7. 온비드 수집 흐름

### 물건 목록/상세

```text
run_onbid_sync
-> OnbidClient.fetch_real_estate_items / fetch_movable_items
-> optional detail merge
-> upsert_auction_item
-> AuctionItemSnapshot 생성
-> pbanc_mng_no가 있으면 AuctionNotice 기본 upsert
```

### 공고 목록/상세/물건정보

```text
run_onbid_sync(api_kind="notice")
-> collect_notice_pages
-> fetch_notice_items
-> optional fetch_notice_detail
-> upsert_auction_notice_payload
-> optional fetch_notice_cltr_items
-> normalize_onbid_api_item(source_api="notice_cltr")
-> upsert_auction_item
-> upsert_auction_notice_item_link
```

### 중복 기준

온비드 물건:

```text
source + cltr_mng_no + pbct_cdtn_no
```

공고-물건 링크:

```text
source + notice_id + auction_item_id
```

## 8. 관리자 관찰성

### 화면

```text
/admin/collection
```

표시 내용:

- 회생/파산 마지막 수집 상태
- 온비드 마지막 수집 상태
- 각 수집 다음 예정 시각
- 온비드 전체 물건 수
- 공고 저장 수
- 공고 상세 payload 보유 수
- 공고-물건 링크 수
- 최근 7일 온비드 수집 성공/실패
- 입찰 마감 분포
- 최근 수집 이력 테이블

### API

```text
GET /api/admin/collection-quality
GET /api/admin/onbid-quality
```

`/api/admin/onbid-quality`는 관리자 인증이 필요하다.

## 9. 스케줄러 운영

### 회생/파산 권장 스케줄

```text
평일 08:10, 15:10
주말 09:10
```

### 온비드 권장 스케줄

```text
목록 수집: 06:30부터 22:30까지 2시간 간격
공고 상세/물건정보: 23:10
상세 API 보강: 23:40 등 별도 시간
```

### 대표 명령

```powershell
.\run_onbid_scheduled_sync.ps1 -RunType scheduled -ApiKind all -Limit 100 -MaxPages 8
.\run_onbid_scheduled_sync.ps1 -RunType scheduled -ApiKind notice -Limit 100 -MaxPages 8 -IncludeNoticeDetails -IncludeNoticeItems
.\run_scheduled_crawl.ps1 -RunType scheduled -Limit 40 -MaxPages 8 -DaysBack 7
```

## 10. 테스트 현황

v002에서 확인한 검증:

- 주요 Python 파일 `py_compile`
- `tests/onbid_module_test.py`
- `tests/page_response_smoke_test.py`
- `tests/router_boundary_test.py`
- `tests/isolated_operations_test.py`
- `run_onbid_sync.ps1` 샘플 공고 수집
- `run_onbid_scheduled_sync.ps1` 샘플 공고 수집
- `run_scheduled_crawl.ps1` dry-run

주의:

- FastAPI TestClient 실행 시 Starlette/httpx deprecation warning이 출력된다. 현재 실패는 아니다.
- 실제 온비드 API 호출은 네트워크 제한과 키 노출 금지 때문에 샘플 모드로 검증했다.

## 11. 운영 전 체크리스트

- DB 백업 실행
- `.env` 또는 운영 환경 변수에 온비드 API 키 설정
- `/admin/collection` 접속 확인
- `run_onbid_scheduled_sync.ps1 -Sample -ApiKind notice -IncludeNoticeDetails -IncludeNoticeItems` 확인
- 실제 API는 `Limit=5`, `MaxPages=1`처럼 작게 시작
- 실패 시 `storage/logs/onbid/`와 `/api/admin/onbid-quality` 확인

## 12. 알려진 경고/미완료

- 국유일반재산 입찰대상물건 API는 응답 문서가 없어 v002에서 보류했다.
- 실제 공공데이터 API 응답 필드명이 문서와 다를 수 있어 raw payload 보존을 우선했다.
- 관리자 수집 화면과 온비드 runbook은 UTF-8 정리 완료, 다른 일부 템플릿/테스트 fixture에는 깨진 문자열이 남아 있을 수 있다.
- 프로젝트 폴더에서 새 Git 저장소가 초기화되어 모든 파일이 untracked로 보이는 상태다. 실제 원격 저장소가 있다면 연결 후 브랜치/커밋 전략을 정리해야 한다.

## 13. 다음 개발 우선순위

1. 실제 온비드 공고 API 응답 샘플 수집 및 normalizer 보강
2. 국유일반재산 입찰대상물건 API 실제 호출/매핑
3. 온비드 목록 화면 필터 강화: 공고 연결 여부, 상세 수집 여부, 마감 D-day, 가격대
4. 온비드 상세 화면에 공고 상세 payload 요약과 연결 공고 표시
5. 관리자 관찰성에 API 종류별 실패율, payload 누락률, 최근 신규/갱신/중복 추이 추가
6. 남은 UTF-8 깨짐 템플릿과 fixture 정리
7. DB 마이그레이션 체계를 Alembic으로 전환할지 검토
8. 운영 배포 전 백업/복원 리허설

## 14. 서비스 계획 논의용 질문

앞으로 ChatGPT에서 서비스 계획을 세울 때 다음 질문을 기준으로 논의하면 좋다.

- 온비드 데이터는 어느 정도 주기로 실제 운영 DB에 적재할 것인가?
- 무료/유료 사용자에게 온비드 공매 기능을 어디까지 공개할 것인가?
- 회생/파산 AI 분석과 온비드 물건은 수동 연결만 유지할 것인가, 후보 추천까지 허용할 것인가?
- 국유재산 API를 별도 카테고리로 볼 것인가, 온비드 공매 안에 포함할 것인가?
- 관리자 관찰성 지표 중 운영 알림으로 올릴 기준은 무엇인가?
- 실제 사용자에게 가장 먼저 필요한 온비드 필터는 무엇인가?
