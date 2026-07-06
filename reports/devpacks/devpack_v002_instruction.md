# Codex 개발팩 v002 작업 지시서

문서 버전: v002  
작업명: 온비드 공고 API 저장 구조 확장 및 운영 관찰성 강화  
기준 프로젝트: `court_auction_platform`  
기준 문서: `project-result_v001.md`  
권장 작업 브랜치: `codex/devpack-v002-onbid-observability`  
작업 방식: 새 브랜치에서 장시간 개발, 검증, 결과 리포트 작성까지 한 번에 진행

---

## 0. 이번 작업의 핵심 목표

이번 v002 개발팩의 목적은 기능을 무작정 늘리는 것이 아니라, 온비드 공매 데이터가 더 안정적으로 저장되고, 관리자가 수집 상태와 데이터 품질을 빠르게 확인할 수 있도록 만드는 것이다.

v001 기준 현재 프로젝트는 다음 상태다.

- 회생·파산 영역은 법원 공고 수집, 문서 저장, OCR 준비, AI 분석 job 관리, 사용자 관심/패스/메모, 관리자 검토 흐름을 갖추고 있다.
- 온비드 영역은 부동산/동산 목록·상세 수집, 온비드 목록/상세 화면, 수집 스크립트, 스케줄 문서를 갖추고 있다.
- 온비드 공고 목록, 공고 상세, 공고 상세 물건정보, 국유일반재산 입찰대상 API는 클라이언트와 분석 기반은 있으나 저장/화면 연결이 다음 과제로 남아 있다.
- 관리자 수집 화면은 회생·파산과 온비드를 분리해서 보여주지만, 실제 운영 관찰에 필요한 성공률, 중복률, API별 실패율, 상세 누락률, 입찰 마감 D-day 분포 등은 더 강화할 필요가 있다.
- 일부 템플릿/샘플/테스트에는 깨져 보이는 한글 문자열이 남아 있어 UTF-8 정리가 필요하다.

이번 v002에서 반드시 달성할 큰 목표는 다음 네 가지다.

1. 온비드 공고 API 저장 흐름 1차 완성
2. 공고 물건정보 API와 `AuctionItem` 매핑 강화
3. 관리자 수집/데이터 품질 관찰성 강화
4. UTF-8 문구 정리, 검증 테스트, 운영 문서, 결과 리포트 정리

---

## 1. 작업 시작 전 필수 절차

### 1.1 브랜치 생성

반드시 새 브랜치에서 작업한다.

```powershell
git status
git checkout -b codex/devpack-v002-onbid-observability
```

이미 같은 이름의 브랜치가 있으면 다음 규칙으로 진행한다.

```powershell
git checkout codex/devpack-v002-onbid-observability
git pull --ff-only
```

충돌이나 pull 실패가 있으면 임의 병합하지 말고 리포트에 기록한 뒤 현재 로컬 상태 기준으로 안전하게 진행한다.

### 1.2 기준 문서와 코드 먼저 읽기

작업 전에 아래 문서와 파일을 먼저 확인한다.

필수 문서:

- `project-result_v001.md`
- `docs/onbid_scheduled_sync_runbook.md`
- `docs/production_crawling_schedule_runbook.md`
- `docs/service_boundary_refactoring_plan.md`

필수 코드:

- `backend/onbid/client.py`
- `backend/workers/onbid_sync.py`
- `backend/database/models.py` 또는 현재 DB 모델 정의 파일
- `backend/database/connection.py` 또는 현재 DB 초기화/보정 파일
- `backend/web/routers/auctions.py`
- `backend/web/routers/admin_operations.py`
- `backend/services/crawl_runs.py`
- `frontend/templates/admin/collection.html`
- `frontend/templates/admin/dashboard.html`
- `frontend/templates/auctions/index.html`
- `frontend/templates/auctions/detail.html`
- `tests/onbid_module_test.py`
- `tests/page_response_smoke_test.py`
- `tests/router_boundary_test.py`
- `tests/isolated_operations_test.py`

### 1.3 작업 중 질문 금지 원칙

작업 중 사소한 의문이 생겨도 사용자에게 질문하지 말고, 이 문서의 우선순위와 판단 기준에 따라 합리적으로 결정해 진행한다.

단, 다음 상황에서는 구현을 멈추지 말고 안전한 대안을 적용한 뒤 결과 리포트에 명확히 기록한다.

- 외부 온비드 API 키가 없어 실제 API 호출이 불가능한 경우
- 로컬 Windows 작업 스케줄러 등록이 권한/환경 문제로 불가능한 경우
- 기존 DB 스키마와 충돌이 있어 destructive migration이 필요해 보이는 경우
- 테스트 데이터 부족으로 완전 검증이 어려운 경우
- API 응답 필드명이 문서와 다르거나 일부 누락된 경우
- 기존 코드 구조가 지시서의 예상과 다르게 되어 있는 경우

이 경우에도 가능한 범위에서 mock/sample 기반 테스트, 비파괴적 스키마 보정, 문서화, 리포트 기록을 진행한다.

---

## 2. 절대 지켜야 할 제약 조건

### 2.1 삭제 금지

아래 파일과 디렉터리는 임의 삭제하지 않는다.

- `auction_data.db`
- `storage/raw_quarantine/`
- `storage/processed/`
- `storage/logs/`
- 기존 수집 원문 파일
- 기존 DB 백업 파일

테스트를 위해 DB 초기화가 필요하면 반드시 별도 임시 DB 또는 테스트 fixture를 사용한다.

### 2.2 API 키 노출 금지

온비드 API 키, AI API 키, 세션 secret 등은 다음 위치에 노출하지 않는다.

- 소스코드
- 테스트 fixture
- 마크다운 문서
- 화면 템플릿
- 로그
- 결과 리포트

필요할 경우 `.env.example`에는 이름만 예시로 둔다.

### 2.3 원문 문서 접근 경계 유지

`/documents/raw/{raw_doc_id}`는 로그인 사용자에게만 제공되어야 한다. 이 보안 경계를 약화시키지 않는다.

### 2.4 온비드 중복 기준 유지

온비드 물건 중복 판단은 단순 `cltr_mng_no` 하나만으로 처리하지 않는다.

현재 핵심 unique 기준은 다음 방향을 유지한다.

```text
source + cltr_mng_no + pbct_cdtn_no
```

또한 입찰 회차 구분을 위해 아래 식별자는 가능한 보존한다.

- `onbid_cltr_no`
- `pbct_no`
- `pbct_nsq`
- `pbct_cdtn_no`
- `cltr_mng_no`

공고 API와 공고 물건정보 API를 연결할 때도 이 원칙을 깨지 않는다.

### 2.5 서비스 방향 유지

이번 v002에서는 다음을 하지 않는다.

- 온비드 전체 물건에 AI 분석을 자동 적용하지 않는다.
- 회생·파산 사건과 온비드 물건을 억지로 자동 연결하지 않는다.
- 법원경매 메뉴나 지도탐색 메뉴를 다시 사용자 UI에 노출하지 않는다.
- 결제/구독/유료화 기능을 구현하지 않는다.
- 외부 배포 인프라를 구성하지 않는다.
- 대규모 권한 모델 개편을 하지 않는다.
- Alembic을 본격 도입하지 않는다. 단, 이번 변경에 필요한 비파괴적 스키마 보정 또는 migration ledger 문서화는 허용한다.

### 2.6 대량 포맷팅 금지

UTF-8 문구 정리를 하더라도 전체 파일을 자동 포맷팅해서 의미 없는 diff를 크게 만들지 않는다.

다음은 금지한다.

- 기능 변경 없는 전체 파일 재포맷
- import 순서 대량 변경
- 템플릿 들여쓰기 대량 변경
- 테스트 기대값과 무관한 문구 대량 변경

---

## 3. 구현 범위 요약

이번 v002 작업 범위는 우선순위 순서로 다음과 같다.

| 우선순위 | 작업 | 필수 여부 |
|---|---|---|
| P0 | 작업 브랜치 생성, 현재 구조 파악, 안전장치 확인 | 필수 |
| P1 | 온비드 공고 목록/상세 API 저장 흐름 연결 | 필수 |
| P1 | 공고 상세 물건정보 API와 `AuctionItem` 매핑 | 필수 |
| P1 | 관리자 수집/데이터 품질 지표 강화 | 필수 |
| P1 | 관련 테스트 추가/수정 | 필수 |
| P2 | UTF-8 깨진 문구 정리 | 필수에 가까움 |
| P2 | 스케줄러 운영 문서/스크립트 점검 보강 | 필수에 가까움 |
| P3 | 국유일반재산 입찰대상 API 저장 구조 검토 또는 최소 연결 | 가능하면 수행 |
| P3 | 온비드 사용자 검색/필터 일부 개선 | 시간이 허용되면 수행 |
| P3 | `AGENTS.md` 또는 repo-level 작업 규칙 정리 | 가능하면 수행 |

P0~P2는 반드시 시도한다. P3는 구현 안정성을 해치지 않는 범위에서 진행하고, 미완료 시 결과 리포트에 다음 작업으로 남긴다.

---

## 4. 온비드 공고 API 저장 흐름 확장

### 4.1 현재 상태 가정

`backend/onbid/client.py`에는 다음 API 함수 또는 이에 준하는 함수가 준비되어 있을 가능성이 높다.

- 공고 목록: `OnbidPbancListSrvc2 / getPbancList2`
- 공고 상세: `OnbidPbancDtlnfSrvc2 / getPbancDtlInf2`
- 공고 상세 물건정보: `OnbidPbancCltrDtlSrvc2 / getPbancCltrInf2`
- 국유일반재산 입찰대상물건: `kamcoRlcBidTrgtCltr / cltrLst`

현재 실제 저장 흐름에 직접 연결된 것은 부동산 목록/상세와 동산 목록/상세다. 이번 v002에서는 공고 계열 API를 실제 저장 흐름까지 연결한다.

### 4.2 `AuctionNotice` 저장/갱신 구현

기존 `AuctionNotice` 모델을 먼저 확인한다. 이미 필요한 필드가 있으면 기존 구조를 우선 사용한다.

필요 필드가 부족하면 비파괴적으로 nullable 컬럼을 추가하거나 기존 DB 초기화/보정 패턴에 맞춰 확장한다.

권장 필드 후보:

- `id`
- `source`
- `notice_no` 또는 공고 고유번호 계열 필드
- `pbct_no`
- `pbct_nsq`
- `pbct_cdtn_no`
- `title`
- `institution_name`
- `department_name`
- `notice_type`
- `notice_status`
- `notice_date`
- `bid_start_at`
- `bid_end_at`
- `open_at`
- `detail_url`
- `raw_payload`
- `detail_payload`
- `item_count`
- `created_at`
- `updated_at`
- `last_seen_at`

실제 온비드 응답 필드명이 다르면, 응답 필드명을 그대로 모델에 무리하게 박지 말고 normalizer에서 내부 표준명으로 변환한다.

### 4.3 공고 unique key 원칙

공고 저장은 idempotent 해야 한다. 같은 공고를 여러 번 수집해도 중복 row가 무한히 생기면 안 된다.

권장 unique key 우선순위:

1. 온비드가 제공하는 명확한 공고 고유번호가 있으면 사용
2. `pbct_no + pbct_nsq` 조합이 안정적이면 사용
3. `source + notice_no` 조합 사용
4. 위 식별자가 불명확하면 `source + title + notice_date + institution_name` 기반의 보조 해시 사용

단, 보조 해시는 최후 수단으로만 사용하고, 결과 리포트에 그 이유를 기록한다.

### 4.4 공고 목록 수집 함수

`backend/workers/onbid_sync.py` 또는 온비드 수집 서비스 계층에 공고 목록 수집 함수를 추가한다.

권장 함수명 예시:

```python
collect_notice_pages(...)
upsert_auction_notice(...)
normalize_onbid_notice(...)
merge_notice_detail(...)
```

기존 네이밍과 다르면 기존 스타일을 따른다.

기능 요구사항:

- `page_no`, `max_pages`, `limit`, `sample` 옵션을 지원한다.
- 응답이 단일 dict 또는 list 모두일 수 있으므로 안전하게 처리한다.
- API 응답 필드 누락에 강해야 한다.
- 저장 시 raw payload를 보존한다.
- 수집 건수, 신규 건수, 갱신 건수, 실패 건수, 중복 추정 건수를 집계한다.
- `CrawlRun`에 요약 정보를 남긴다.

### 4.5 공고 상세 수집 옵션

공고 목록 수집에 상세 수집 옵션을 붙인다.

권장 CLI 옵션:

```text
--api-kind notice
--include-notice-details
--include-notice-items
```

기존 `--api-kind all`의 의미를 갑자기 무겁게 만들지 않는다. 기존 `all`이 부동산+동산만 의미했다면, 다음 둘 중 하나를 선택한다.

- 안전안: `all`은 기존 의미를 유지하고, 공고는 `notice`로 명시 실행
- 확장안: `all`에 notice를 포함하되 `--include-notice-details`, `--include-notice-items`가 없으면 가벼운 목록만 수집

어느 쪽을 선택했는지 결과 리포트에 적는다.

### 4.6 공고 상세 payload 병합

공고 상세 API가 가능하면 `AuctionNotice.detail_payload` 또는 이에 준하는 필드에 저장한다.

상세 API에서 얻은 값 중 목록보다 더 신뢰할 수 있는 값은 내부 표준 필드에 병합한다.

예시:

- 공고 제목
- 기관명
- 입찰 시작/마감일
- 개찰일
- 공고 상태
- 상세 설명
- 유의사항
- 관련 URL

필드명이 확실하지 않으면 raw/detail payload 보존을 우선한다.

---

## 5. 공고 물건정보 API와 `AuctionItem` 매핑

### 5.1 목표

공고 상세 물건정보 API 결과를 `AuctionItem`에 연결한다.

목표는 다음이다.

- 공고에 포함된 물건을 `AuctionItem`으로 upsert한다.
- 기존 온비드 물건 unique 기준을 깨지 않는다.
- `AuctionNotice`와 `AuctionItem` 사이의 관계를 가능한 범위에서 추적 가능하게 한다.
- API 응답 원문은 보존한다.

### 5.2 관계 표현 방식

기존 모델을 먼저 확인한다.

가능한 관계 표현 우선순위:

1. 이미 `AuctionNotice`와 `AuctionItem` 관계 필드가 있으면 사용
2. `AuctionItem`에 공고 식별자 필드가 이미 있으면 사용
3. nullable 컬럼 몇 개로 충분히 표현 가능하면 비파괴적으로 추가
4. 다대다 관계가 명확히 필요하면 최소 association table 추가 검토

association table을 추가할 경우 권장 이름은 다음 중 기존 컨벤션에 맞춘다.

- `AuctionNoticeItem`
- `AuctionNoticeItemLink`

권장 필드 후보:

- `id`
- `notice_id`
- `auction_item_id`
- `source`
- `notice_no`
- `pbct_no`
- `pbct_nsq`
- `cltr_mng_no`
- `pbct_cdtn_no`
- `raw_payload`
- `created_at`
- `updated_at`

단, 테이블 추가가 기존 테스트/스키마 보정 방식과 충돌하면 무리해서 추가하지 말고, `AuctionItem` 쪽 식별자 저장과 raw payload 보존으로 1차 구현한다.

### 5.3 `AuctionItem` upsert 원칙

공고 물건정보에서 나온 물건도 기존 `upsert_auction_item` 또는 이에 준하는 함수를 최대한 재사용한다.

필수 유지사항:

- `source + cltr_mng_no + pbct_cdtn_no` 기준 유지
- `onbid_cltr_no`, `pbct_no`, `pbct_nsq` 보존
- 감정가, 최저입찰가, 보증금, 입찰 시작/마감/개찰일 보존
- 소재지, 기관명, 용도, 상세 설명, 유의사항 보존
- raw payload 보존
- 가격/상태 변화가 있으면 `AuctionItemSnapshot` 기록 흐름을 깨지 않음

### 5.4 API 응답 필드 안정성

온비드 API 응답은 한글명, 영문 축약명, XML 변환 dict 구조 등이 섞일 수 있다.

따라서 normalizer는 다음 유틸 패턴을 사용한다.

```python
get_first(payload, ["fieldA", "field_b", "한글필드명", ...])
parse_number(value)
parse_date(value)
parse_datetime(value)
clean_text(value)
```

이미 유사 유틸이 있으면 재사용한다.

---

## 6. 국유일반재산 입찰대상 API 처리

국유일반재산 입찰대상물건 API는 이번 v002에서 완전한 서비스화까지 무리하지 않는다.

우선순위는 다음이다.

1. 기존 클라이언트 함수가 실제 호출 가능한지 확인한다.
2. sample/mock 기반 normalizer를 만든다.
3. `AuctionItem`에 안전하게 매핑 가능한 필드가 있으면 1차 저장한다.
4. 매핑이 불명확하면 raw payload 보존 구조와 설계 문서만 남긴다.

이 API를 처리하면서 기존 온비드 물건 저장 흐름을 깨면 안 된다.

결과 리포트에는 다음을 반드시 적는다.

- 실제 저장 연결 여부
- 매핑한 필드 목록
- 매핑하지 못한 필드와 이유
- 다음 v003에서 필요한 모델 확장안

---

## 7. 관리자 수집/데이터 품질 관찰성 강화

### 7.1 목표

관리자가 실제 운영 중 다음 질문에 빠르게 답할 수 있게 만든다.

- 온비드 수집이 마지막으로 언제 성공했는가?
- 최근 실패가 있었는가?
- 어떤 API 종류에서 실패가 많은가?
- 최근 24시간/7일 동안 몇 건이 수집되었는가?
- 중복률은 어느 정도인가?
- 상세 수집 누락률은 어느 정도인가?
- 입찰 마감이 임박한 물건은 얼마나 있는가?
- 공고 데이터는 얼마나 쌓이고 있는가?

### 7.2 서비스 함수 분리

가능하면 템플릿이나 라우터에 직접 집계 쿼리를 몰아넣지 말고 서비스 함수를 만든다.

권장 위치:

- `backend/services/collection_quality.py`
- 또는 기존 `backend/services/crawl_runs.py` 확장

권장 함수 예시:

```python
get_collection_quality_summary(db)
get_onbid_collection_metrics(db, days=7)
get_crawl_run_status_by_type(db)
get_auction_data_freshness(db)
get_onbid_deadline_distribution(db)
```

기존 구조와 다르면 기존 스타일을 따른다.

### 7.3 관리자 화면 지표

`frontend/templates/admin/collection.html` 또는 관리자 대시보드에 다음 지표를 추가한다.

필수 지표:

- 회생·파산 마지막 수집 상태
- 온비드 마지막 수집 상태
- 온비드 마지막 성공 시각
- 온비드 마지막 실패 시각과 실패 메시지
- 최근 24시간 온비드 수집 실행 수
- 최근 7일 온비드 수집 실행 수
- 최근 7일 성공/실패 횟수
- 최근 7일 API 종류별 실행 현황
- 온비드 전체 물건 수
- 온비드 공고 수
- 상세 payload 보유 물건 수/비율
- 입찰 마감 D-day 분포

가능하면 추가할 지표:

- 신규/갱신/중복 추정 건수
- API별 실패율
- API 호출량 추정
- raw payload 누락 건수
- 가격 정보 누락 건수

### 7.4 D-day 분포 기준

입찰 마감일 기준 분포는 다음 버킷을 권장한다.

```text
마감 지남
오늘 마감
1~3일
4~7일
8~14일
15~30일
30일 초과
마감일 없음
```

날짜 필드명이 다르면 현재 `AuctionItem`의 입찰 마감일 컬럼을 확인해 가장 적절한 값을 사용한다.

### 7.5 API 응답 또는 JSON 엔드포인트

이미 관리자 수집 품질 API가 있으면 확장한다.

없거나 부족하면 다음 중 하나를 추가한다.

```text
GET /admin/api/collection-quality
GET /admin/api/onbid-quality
```

단, 인증/권한 경계를 반드시 유지한다. 관리자 전용 API는 관리자만 접근 가능해야 한다.

---

## 8. 온비드 사용자 화면 검색/필터 개선

이 작업은 P3이지만, 핵심 작업이 안정적으로 끝나면 가능한 범위에서 수행한다.

`frontend/templates/auctions/index.html`과 `backend/web/routers/auctions.py`를 확인하고 다음 필터 중 2~4개를 안전하게 추가한다.

우선순위:

1. 소재지/주소 키워드
2. 기관명
3. 물건 유형 또는 API 종류
4. 입찰 마감일 범위
5. 감정가/최저입찰가 가격대
6. 할인율 범위
7. 상세 수집 여부
8. 공고 연결 여부

필터 추가 시 주의사항:

- 기존 목록 조회가 느려지지 않도록 인덱스 필요성을 검토한다.
- 필터 파라미터는 빈 값에 안전해야 한다.
- 잘못된 숫자/날짜 입력 시 500 오류가 나지 않아야 한다.
- 기존 테스트가 깨지지 않도록 기본 동작은 유지한다.

---

## 9. UTF-8 문구 정리

### 9.1 대상

다음 영역에서 깨져 보이는 한글 문자열을 점진적으로 정리한다.

- `frontend/templates/admin/*.html`
- `frontend/templates/user/*.html`
- `frontend/templates/auctions/*.html`
- 테스트 샘플 문자열
- 문서 중 눈에 띄는 깨진 한글

### 9.2 정리 기준

- 화면에 보이는 문구 중심으로 정리한다.
- 테스트 기대 문구를 수정해야 하면 실제 화면 문구와 함께 수정한다.
- 기능 로직과 무관한 대량 포맷팅은 하지 않는다.
- 확실히 깨진 문구만 수정한다.
- 의미가 불명확한 문구는 추정으로 과하게 바꾸지 말고 리포트에 남긴다.

### 9.3 확인 방법

가능하면 다음 패턴을 검색한다.

```text
ì
ë
ê
í
�
```

단, 외부 라이브러리 파일이나 바이너리 파일은 건드리지 않는다.

---

## 10. 스케줄러 운영 점검 보조

이번 v002에서 로컬 Windows 작업 스케줄러를 실제 등록하는 것은 환경 의존성이 크므로 필수 구현으로 보지 않는다.

대신 다음을 보강한다.

### 10.1 문서 보강

다음 문서를 점검하고 필요하면 업데이트한다.

- `docs/onbid_scheduled_sync_runbook.md`
- `docs/production_crawling_schedule_runbook.md`

반드시 포함할 내용:

- 수동 실행 명령
- sample 실행 명령
- 스케줄러 등록 예시
- 로그 경로
- 실패 확인 방법
- 중복 실행 lock 설명
- 운영 전 체크리스트

### 10.2 스크립트 점검

다음 스크립트가 현재 옵션과 문서에 맞는지 확인한다.

- `run_onbid_sync.ps1`
- `run_onbid_scheduled_sync.ps1`
- `run_scheduled_crawl.ps1`

가능하면 다음 명령을 검증한다.

```powershell
powershell -ExecutionPolicy Bypass -File .\run_onbid_sync.ps1 -Sample
powershell -ExecutionPolicy Bypass -File .\run_onbid_scheduled_sync.ps1 -Sample
powershell -ExecutionPolicy Bypass -File .\run_scheduled_crawl.ps1 -DryRun
```

환경 문제로 실행이 불가능하면 리포트에 기록한다.

---

## 11. 테스트 요구사항

### 11.1 기존 테스트 유지

최소한 다음 검증을 시도한다.

```powershell
python -m py_compile main_app.py
python tests/onbid_module_test.py
python tests/page_response_smoke_test.py
python tests/router_boundary_test.py
python tests/isolated_operations_test.py
```

프로젝트의 실제 테스트 실행 방식이 pytest라면 기존 방식에 맞춰 실행해도 된다.

### 11.2 신규/수정 테스트

다음 테스트를 추가하거나 기존 테스트에 보강한다.

필수:

- 공고 목록 응답 normalizer 테스트
- 공고 상세 응답 merge 테스트
- 공고 upsert idempotency 테스트
- 공고 물건정보 -> `AuctionItem` 매핑 테스트
- 관리자 수집 품질 지표 API 또는 페이지 응답 테스트
- UTF-8 문구 수정으로 인한 page smoke test 보정

가능하면:

- 국유일반재산 입찰대상 응답 normalizer 테스트
- 잘못된 날짜/가격 필드 처리 테스트
- API 키 없음/sample 모드 테스트
- 상세 payload 누락률 집계 테스트

### 11.3 외부 API 의존성 줄이기

테스트는 실제 온비드 API 키에 의존하지 않도록 한다.

권장 방식:

- sample payload fixture
- monkeypatch/mock client
- 로컬 테스트 DB
- `--sample` 모드 활용

실제 API 호출 검증은 가능하면 수동 검증 명령으로만 남긴다.

---

## 12. DB/스키마 변경 지침

### 12.1 비파괴 원칙

스키마 변경은 비파괴적으로만 진행한다.

허용:

- nullable 컬럼 추가
- 신규 테이블 추가
- 신규 인덱스 추가
- 기존 row에 영향을 주지 않는 기본값 추가
- 기존 DB 초기화/보정 패턴에 맞춘 ensure 함수 추가

금지:

- 기존 테이블 drop
- 기존 컬럼 drop
- 기존 데이터 truncate
- 기존 unique 기준을 약화시키는 변경
- 기존 데이터를 임의 변환하는 destructive migration

### 12.2 migration ledger

Alembic을 본격 도입하지 말되, 스키마 변경이 있으면 다음 문서 중 하나를 생성/업데이트한다.

권장:

- `docs/migration_ledger.md`

포함 내용:

- 변경 일자
- 변경 버전 v002
- 변경 테이블/컬럼
- 변경 이유
- 기존 데이터 영향
- rollback 또는 수동 복구 방법

---

## 13. 문서화 요구사항

작업 완료 후 반드시 다음 문서를 작성하거나 업데이트한다.

### 13.1 결과 리포트

생성 파일:

```text
reports/codex-devpack-v002-report.md
```

아래 템플릿을 따른다.

```markdown
# Codex 개발 결과 리포트 v002

## 1. 작업 브랜치
- 브랜치명:
- 기준 커밋:
- 최종 커밋 또는 최종 작업 상태:

## 2. 작업 요약
- 이번 작업에서 달성한 핵심 결과:

## 3. 변경 파일 목록
| 파일 | 변경 요약 | 위험도 |
|---|---|---|

## 4. 구현 상세
### 4.1 온비드 공고 API 저장 구조
### 4.2 공고 물건정보와 AuctionItem 매핑
### 4.3 국유일반재산 입찰대상 API 처리
### 4.4 관리자 데이터 품질/수집 관찰성
### 4.5 UI UTF-8 문구 정리
### 4.6 스케줄러/운영 문서 보강
### 4.7 테스트 보강

## 5. DB/마이그레이션 변경
- 새 테이블:
- 새 컬럼:
- 인덱스/unique:
- 기존 데이터 영향:
- rollback 방법:

## 6. 검증 결과
| 검증 명령 | 결과 | 비고 |
|---|---|---|

## 7. 실패/미완료/보류 항목
| 항목 | 이유 | 다음 조치 |
|---|---|---|

## 8. 운영 시 주의사항
- API 키:
- 작업 스케줄러:
- 로그:
- DB 백업:
- known warnings:

## 9. 다음 개발팩 추천
- 우선순위 1:
- 우선순위 2:
- 우선순위 3:

## 10. 자체 리뷰
- 위험한 변경이 있는가?
- 기존 기능 회귀 가능성은?
- 추가 수동 확인이 필요한 화면/명령은?
```

### 13.2 프로젝트 상태 문서

생성 파일:

```text
reports/project-result_v002.md
```

이 문서는 앞선 대화 없이도 프로젝트 상태를 이해할 수 있어야 한다.

포함 내용:

- 프로젝트 한 줄 요약
- v001 대비 v002에서 달라진 점
- 현재 주요 파일 구조
- 현재 DB 모델 요약
- 온비드 API 연동 상태
- 온비드 수집 흐름
- 관리자 관찰성 지표
- UI/UX 현황
- 운영 스크립트와 스케줄러 문서
- 테스트 현황
- 알려진 경고/미완료
- 중요한 주의사항
- 다음 개발 우선순위

### 13.3 온비드 공고 저장 설계 문서

가능하면 다음 문서를 생성한다.

```text
docs/onbid_notice_persistence_design.md
```

포함 내용:

- 공고 목록 API 매핑
- 공고 상세 API 매핑
- 공고 물건정보 API 매핑
- `AuctionNotice` 필드 설명
- `AuctionItem` 연결 방식
- unique key 기준
- sample/mock 테스트 방식
- 남은 리스크

---

## 14. `AGENTS.md` 또는 repo-level 작업 규칙 정리

가능하면 프로젝트 루트에 `AGENTS.md`가 있는지 확인한다.

없으면 짧고 실용적인 `AGENTS.md`를 생성한다. 이미 있으면 이번 v002에서 반복된 주의사항만 최소한으로 보강한다.

권장 내용:

```markdown
# AGENTS.md

## Project context
- FastAPI + SQLite 기반 로컬 자산 분석 플랫폼이다.
- 회생·파산은 AI 분석 중심, 온비드는 공매 데이터 수집/정규화/조회 중심이다.

## Do not
- `auction_data.db`, `storage/raw_quarantine`, `storage/processed`, `storage/logs`를 삭제하지 않는다.
- API 키를 코드/문서/로그에 노출하지 않는다.
- 온비드 중복 기준을 단순 `cltr_mng_no` 하나로 축소하지 않는다.
- 온비드 전체 물건에 AI 분석을 자동 적용하지 않는다.
- 법원경매/지도탐색 메뉴를 임의로 다시 노출하지 않는다.

## Verify
- `python -m py_compile main_app.py`
- `python tests/onbid_module_test.py`
- `python tests/page_response_smoke_test.py`
- `python tests/router_boundary_test.py`
- `python tests/isolated_operations_test.py`
```

단, `AGENTS.md` 생성/수정 때문에 이번 핵심 구현이 지연되면 생략하고 리포트에 추천사항으로 남긴다.

---

## 15. 완료 기준

이번 v002 작업은 다음 조건을 만족하면 완료로 본다.

### 15.1 필수 완료 기준

- 새 브랜치에서 작업했다.
- 온비드 공고 목록 저장 흐름이 구현되었다.
- 온비드 공고 상세 저장 또는 detail payload 보존 흐름이 구현되었다.
- 공고 물건정보 API 결과를 `AuctionItem`에 매핑하는 1차 흐름이 구현되었다.
- 기존 온비드 부동산/동산 수집 흐름이 깨지지 않았다.
- 관리자 수집/데이터 품질 지표가 기존보다 강화되었다.
- 주요 화면이 500 오류 없이 응답한다.
- 핵심 테스트를 실행했고 결과를 리포트에 남겼다.
- DB/storage/API 키 관련 안전 조건을 지켰다.
- `reports/codex-devpack-v002-report.md`를 작성했다.
- `reports/project-result_v002.md`를 작성했다.

### 15.2 권장 완료 기준

- `docs/onbid_notice_persistence_design.md`를 작성했다.
- `docs/migration_ledger.md`를 작성 또는 업데이트했다.
- UTF-8 깨진 문구를 눈에 띄는 범위에서 정리했다.
- 스케줄러 runbook과 실제 스크립트 옵션이 일치한다.
- 국유일반재산 입찰대상 API의 저장 가능성/모델 확장안을 리포트에 정리했다.
- 온비드 사용자 목록에 검색/필터 2~4개가 안전하게 추가되었다.

---

## 16. 권장 작업 순서

아래 순서대로 진행한다.

1. `git status` 확인 및 새 브랜치 생성
2. v001 문서와 온비드/관리자 관련 코드 파악
3. 현재 테스트 1회 실행 또는 최소 py_compile 실행으로 기준 상태 확인
4. 온비드 공고 API client 함수 상태 확인
5. normalizer/upsert 설계
6. `AuctionNotice` 저장/갱신 구현
7. 공고 상세 payload 병합 구현
8. 공고 물건정보 -> `AuctionItem` 매핑 구현
9. 필요 시 스키마 보정/문서화
10. worker CLI 옵션 확장
11. 관리자 수집/데이터 품질 service 함수 구현
12. 관리자 화면/API 반영
13. UTF-8 문구 정리
14. 스케줄러 문서/스크립트 옵션 점검
15. 테스트 추가/수정
16. 전체 검증 명령 실행
17. 결과 리포트 작성
18. `reports/project-result_v002.md` 작성
19. `git diff --stat`, `git status` 확인 후 최종 요약

---

## 17. 자체 리뷰 체크리스트

작업 마지막에 반드시 스스로 확인한다.

- [ ] 새 브랜치에서 작업했는가?
- [ ] 기존 DB/storage를 삭제하지 않았는가?
- [ ] API 키를 노출하지 않았는가?
- [ ] 온비드 중복 기준을 약화시키지 않았는가?
- [ ] 기존 부동산/동산 수집 테스트가 통과하는가?
- [ ] 공고 API 저장은 idempotent한가?
- [ ] 공고 물건정보가 `AuctionItem`에 무리 없이 매핑되는가?
- [ ] 관리자 화면에서 운영자가 실패/성공/누락을 볼 수 있는가?
- [ ] 템플릿 변경으로 500 오류가 나지 않는가?
- [ ] UTF-8 정리가 기능 변경과 섞이지 않았는가?
- [ ] 스키마 변경이 비파괴적인가?
- [ ] 결과 리포트에 실패/미완료/보류 항목을 솔직히 적었는가?
- [ ] 다음 v003 우선순위를 구체적으로 남겼는가?

---

## 18. Codex 최종 응답 형식

작업이 끝나면 Codex는 마지막 응답을 아래 형식으로 작성한다.

```markdown
# v002 작업 완료 보고

## 브랜치
- `codex/devpack-v002-onbid-observability`

## 핵심 결과
- 

## 변경 파일
- 

## 검증 결과
- 

## 생성/업데이트 문서
- `reports/codex-devpack-v002-report.md`
- `reports/project-result_v002.md`
- 기타:

## 미완료/주의사항
- 

## 다음 추천 작업
- 
```

마지막 응답은 짧게 쓰되, 상세 내용은 반드시 리포트 문서에 남긴다.
