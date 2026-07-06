# Migration Ledger

## v002 - 온비드 공고 저장과 관찰성

변경일: 2026-07-06

### 변경 목적

온비드 공고 목록, 공고 상세, 공고 물건정보 API를 저장하고 관리자 화면에서 수집 품질을 관찰하기 위해 비파괴 스키마 보강을 수행했다.

### 변경 테이블

#### `auction_notices`

추가 컬럼:

- `notice_no TEXT NOT NULL DEFAULT ''`
- `pbct_no TEXT NOT NULL DEFAULT ''`
- `pbct_nsq TEXT NOT NULL DEFAULT ''`
- `pbct_cdtn_no TEXT NOT NULL DEFAULT ''`
- `notice_status TEXT NOT NULL DEFAULT ''`
- `notice_type TEXT NOT NULL DEFAULT ''`
- `notice_date TEXT NOT NULL DEFAULT ''`
- `bid_start_at TEXT NOT NULL DEFAULT ''`
- `bid_end_at TEXT NOT NULL DEFAULT ''`
- `open_at TEXT NOT NULL DEFAULT ''`
- `department_name TEXT NOT NULL DEFAULT ''`
- `detail_url TEXT NOT NULL DEFAULT ''`
- `item_count INTEGER NOT NULL DEFAULT 0`
- `detail_payload TEXT NOT NULL DEFAULT '{}'`
- `last_seen_at DATETIME NULL`

기존 컬럼 삭제나 기존 데이터 변경은 수행하지 않는다.

#### `auction_notice_item_links`

신규 테이블:

- `id`
- `notice_id`
- `auction_item_id`
- `source`
- `notice_no`
- `pbanc_mng_no`
- `pbct_no`
- `pbct_nsq`
- `cltr_mng_no`
- `pbct_cdtn_no`
- `raw_payload`
- `created_at`
- `updated_at`

unique 제약:

```text
source + notice_id + auction_item_id
```

### 적용 방식

- `Base.metadata.create_all(engine)`로 신규 테이블을 생성한다.
- SQLite 기존 DB에는 `backend/database/session.py`의 `ensure_schema_migrations`에서 누락 컬럼만 `ALTER TABLE ADD COLUMN`으로 추가한다.
- 기존 `auction_items` unique 기준인 `source + cltr_mng_no + pbct_cdtn_no`는 변경하지 않는다.

### 기존 데이터 영향

- 기존 행은 삭제하지 않는다.
- 기존 `auction_notices` 행은 신규 컬럼 기본값으로 유지된다.
- `last_seen_at`은 해당 공고가 다시 수집될 때 채워진다.
- `auction_notice_item_links`는 공고 물건정보 수집을 실행한 이후부터 생성된다.

### 수동 복구/롤백

이 작업은 기존 데이터를 삭제하지 않는다. 코드 롤백만으로 기존 기능은 대부분 유지된다. 단, SQLite는 컬럼 삭제가 번거로우므로 DB 파일 자체를 되돌려야 한다면 작업 전 백업본을 복구하는 방식을 권장한다.

운영 전 권장:

```powershell
.\backup_database.ps1
```

### 검증

v002에서 다음 검증을 통과했다.

- `py_compile` 주요 backend/test 파일
- `tests/onbid_module_test.py`
- `tests/page_response_smoke_test.py`
- `tests/router_boundary_test.py`
- `tests/isolated_operations_test.py`
- `run_onbid_sync.ps1 -Sample -ApiKind notice -IncludeNoticeDetails -IncludeNoticeItems`
- `run_onbid_scheduled_sync.ps1 -Sample -ApiKind notice -IncludeNoticeDetails -IncludeNoticeItems`
