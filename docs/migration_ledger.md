# Migration Ledger

## v005 - Public freshness, stored ONBID derived fields, and review readiness
Change date: 2026-07-07

### Purpose

v005 enforces the public ONBID freshness policy, keeps stale/unknown-date rows in the database while hiding them from public defaults, stores derived category/freshness fields for faster QA, and adds review-mode/operations readiness support.

### Schema Changes

Non-destructive columns added to `auction_items`:

- `public_category TEXT NOT NULL DEFAULT 'other'`
- `freshness_date TEXT NOT NULL DEFAULT ''`
- `freshness_status TEXT NOT NULL DEFAULT 'unknown_date'`
- `public_visible BOOLEAN NOT NULL DEFAULT 0`

Non-destructive indexes added if missing:

- `ix_auction_items_public_category`
- `ix_auction_items_freshness_date`
- `ix_auction_items_freshness_status`
- `ix_auction_items_public_visible`

### Data Handling

- Public `/onbid` and `sitemap.xml` default to items dated `2025-01-01` or later.
- Pre-2025 and unknown-date ONBID rows are not deleted; they are audited and hidden from public defaults.
- Review hardening also hides sentinel/implausible public dates (`2999-12-30`, `2999-12-31`, `9999-12-31`, `0001-01-01`, and dates beyond the configured max future window) and sample/fixture rows unless `REVIEW_SHOW_SAMPLE=true`.
- New sync/probe paths count stale and unknown-date payloads as dropped before fresh upsert.
- `national_property` remains its own public category and is not split into real-estate/movable.

### Review Hardening Addendum

The Cloudflare Tunnel review hardening continuation added no additional schema changes beyond the v005 columns/indexes above. It changed route parsing, public visibility policy, login hint rendering, and public detail form rendering only.

### Migration Method

SQLite uses `ensure_schema_migrations` with `ALTER TABLE ADD COLUMN` and `CREATE INDEX IF NOT EXISTS`. Existing rows can be refreshed with:

```powershell
powershell -ExecutionPolicy Bypass -File .\repair_onbid_derived_fields.ps1 -DryRun -MinDate 2025-01-01
```

Apply mode exists but was not run by Codex:

```powershell
powershell -ExecutionPolicy Bypass -File .\repair_onbid_derived_fields.ps1 -Apply -MinDate 2025-01-01
```

### Rollback

Code rollback restores prior behavior. Because SQLite does not easily drop columns safely, added columns/indexes should be left in place unless restoring a pre-v005 DB backup is required.

### Verification

- `py_compile` for changed backend modules and v005 tests
- v005 tests for navigation, freshness, category mapping, filters, admin readiness, public smoke, sitemap, security headers, legal pages, and review mode
- Existing ONBID/page/router/auth/operations tests
- ONBID sample sync and constrained real fresh probes with `Limit=20`, `MaxPages=1`, `MinDate=2025-01-01`
- Freshness audit dry run and derived-field repair dry run

## v004 - Real ONBID operations and public category UX
Change date: 2026-07-06

### Purpose

v004 adds real ONBID limited collection/probe support, public category derivation, missing-information badges, same-notice item lookup, and operations dry-run scripts.

### Schema Changes

No new table, column, index, or destructive migration was added in v004.

### Data Handling

- Existing `auction_items` duplicate key remains `source + cltr_mng_no + pbct_cdtn_no`.
- `national_property` is derived from normalized/raw payload metadata and is not split into real-estate/movable categories.
- Sparse external payloads without official duplicate identifiers receive deterministic derived keys based on stable source fields, not timestamps or random UUIDs.
- Raw payload remains stored in the DB/runtime storage and is not exposed in public DTOs.

### Rollback

Code rollback restores the previous public ONBID UX and sync behavior. The real API rows inserted during v004 should be handled by restoring the pre-run DB backup when a data rollback is required.

### Verification

- `py_compile` for edited backend modules and new tests
- `tests/onbid_category_filter_test.py`
- `tests/sitemap_public_routes_test.py`
- Existing ONBID/page/router/auth/operations tests
- `run_onbid_scheduled_sync.ps1 -Sample -ApiKind notice -Limit 20 -MaxPages 1 -IncludeNoticeDetails -IncludeNoticeItems`

## v003 - 온비드 사용자 개인화

변경일: 2026-07-06

### 변경 목적

로그인 사용자가 온비드 공매 물건에 관심, 패스, 감시, 메모, 태그를 저장할 수 있도록 비파괴 신규 테이블을 추가했다.

### 변경 테이블

#### `user_auction_preferences`

신규 테이블:

- `id`
- `user_id`
- `auction_item_id`
- `is_favorite BOOLEAN NOT NULL DEFAULT 0`
- `is_passed BOOLEAN NOT NULL DEFAULT 0`
- `is_watching BOOLEAN NOT NULL DEFAULT 0`
- `note TEXT NOT NULL DEFAULT ''`
- `tags TEXT NOT NULL DEFAULT ''`
- `created_at`
- `updated_at`

unique 제약:

```text
user_id + auction_item_id
```

### 적용 방식

- `Base.metadata.create_all(engine)`로 신규 테이블을 생성한다.
- 기존 테이블/컬럼/데이터 삭제는 수행하지 않는다.
- 기존 온비드 중복 기준 `source + cltr_mng_no + pbct_cdtn_no`는 변경하지 않는다.

### 기존 데이터 영향

- 기존 온비드 물건, 공고, 회생/파산 사건 데이터에는 영향을 주지 않는다.
- preference 행은 로그인 사용자가 온비드 preference POST/API를 호출할 때 생성된다.

### 수동 복구/롤백

코드 롤백만으로 기존 조회 기능은 유지된다. 신규 preference 데이터를 제거해야 하는 운영 상황은 별도 백업 복구 또는 명시적 데이터 정리 절차로 처리한다.

운영 전 권장:

```powershell
.\backup_database.ps1
```

### 검증

v003에서 다음 검증을 수행했다.

- `py_compile` 주요 backend/test 파일
- `tests/public_access_auth_boundary_test.py`
- `tests/onbid_module_test.py`
- `tests/page_response_smoke_test.py`
- `tests/router_boundary_test.py`
- `tests/isolated_operations_test.py`

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
