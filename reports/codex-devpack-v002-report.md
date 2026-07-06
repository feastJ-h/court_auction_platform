# Codex 개발 결과 리포트 v002

## 1. 작업 브랜치

- 브랜치명: `codex/devpack-v002-onbid-observability`
- 작업 경로: `C:\Users\xogns\Documents\testAuction\court_auction_platform`
- Git 상태 참고: 상위 폴더의 기존 `.git`은 유효한 저장소로 인식되지 않아 프로젝트 폴더 내부에서 새 Git 저장소를 초기화하고 지정 브랜치를 생성했다. 따라서 현재 저장소에서는 기존 파일들이 untracked로 표시된다.
- API 키/DB/storage: 삭제 또는 노출하지 않았다.

## 2. 작업 요약

v002에서는 온비드 공고 목록, 공고 상세, 공고 물건정보 API를 수집/저장하는 1차 운영 흐름을 연결했다. 공고는 `AuctionNotice`에 독립 저장하고, 공고 물건정보는 기존 `AuctionItem` 중복 기준을 유지하며 저장한 뒤 `AuctionNoticeItemLink`로 관계를 추적한다.

관리자 수집 화면은 깨진 UTF-8 문구를 정리하고, 온비드 데이터 품질 카드와 `/api/admin/onbid-quality` 지표 API를 추가했다. 스케줄러 스크립트는 공고 전용 수집 옵션을 받을 수 있게 확장했다.

## 3. 변경 파일 목록

| 파일 | 변경 요약 | 위험도 |
|---|---|---|
| `backend/database/models.py` | `AuctionNotice` 필드 확장, `AuctionNoticeItemLink` 신규 모델 추가 | 중 |
| `backend/database/session.py` | SQLite 비파괴 `ALTER TABLE` 보정 추가 | 중 |
| `backend/onbid/client.py` | 공고 목록/상세/공고물건 샘플 및 sample fallback 추가 | 중 |
| `backend/workers/onbid_sync.py` | `api_kind=notice`, 공고 상세/물건정보 저장 흐름 추가 | 중 |
| `backend/services/auction_items.py` | 공고 normalizer/upsert/link upsert 추가 | 중 |
| `backend/services/onbid_observability.py` | 온비드 품질 지표 계산 서비스 추가 | 낮음 |
| `backend/web/routers/admin_operations.py` | 관리자 수집 화면 지표 주입, `/api/admin/onbid-quality` 추가 | 낮음 |
| `backend/web/routers/auctions.py` | 온비드 수집 API에 notice 옵션 추가 | 낮음 |
| `frontend/templates/admin/collection.html` | UTF-8 문구 정리, 온비드 관찰성 UI와 공고 수집 버튼 추가 | 중 |
| `run_onbid_sync.ps1` | `notice`, `IncludeNoticeDetails`, `IncludeNoticeItems` 옵션 추가 | 낮음 |
| `run_onbid_scheduled_sync.ps1` | 스케줄러용 공고 옵션 추가 | 낮음 |
| `docs/onbid_scheduled_sync_runbook.md` | v002 스케줄 운영 문서로 재작성 | 낮음 |
| `docs/onbid_notice_persistence_design.md` | 공고 저장 설계 문서 추가 | 낮음 |
| `docs/migration_ledger.md` | 스키마 변경 장부 추가 | 낮음 |
| `tests/onbid_module_test.py` | 공고 저장, 링크, 관찰성 API 테스트 추가 | 낮음 |
| `tests/page_response_smoke_test.py` | 온비드 품질 API 스모크 추가 | 낮음 |
| `tests/router_boundary_test.py` | 새 관리자 API 라우트 경계 테스트 추가 | 낮음 |

## 4. 구현 상세

### 4.1 온비드 공고 API 저장 구조

- `OnbidClient.fetch_notice_items`에 `sample` 옵션을 추가했다.
- `OnbidClient.fetch_notice_detail`과 `fetch_notice_cltr_items`도 API 키가 없거나 샘플 모드일 때 샘플 payload를 반환한다.
- 공고 목록은 `AuctionNotice.raw_payload`에 저장한다.
- 공고 상세는 `AuctionNotice.detail_payload`에 저장한다.
- 공고 식별자는 `pbancMngNo`, `onbidPbancNo`, `pbancNo`, `noticeNo` 후보를 순서대로 사용한다.

### 4.2 공고 물건정보와 AuctionItem 매핑

- `normalize_onbid_api_item(..., source_api="notice_cltr")`로 공고 물건정보 API 응답을 기존 `AuctionItem` 필드로 매핑한다.
- `source + cltr_mng_no + pbct_cdtn_no` 중복 기준은 그대로 유지했다.
- 공고와 물건의 관계는 신규 `AuctionNoticeItemLink` 테이블에 저장한다.
- 샘플 기준 공고 2건, 공고 물건 3건, 링크 3건이 생성된다.
- 재수집 시 공고는 update, 물건은 duplicate, 링크는 update로 처리된다.

### 4.3 국유일반재산 입찰대상물건 API

- v002에서는 문서가 없어 실제 매핑 구현까지 진행하지 않았다.
- 기존 `fetch_bid_target_items`는 설정 기반 호출 구조가 있으므로 유지했다.
- 다음 단계에서 실제 응답 샘플을 확보한 뒤 `AuctionItem` 매핑 후보 필드를 확정하는 것이 안전하다.

### 4.4 관리자 관찰성

신규 서비스 `backend/services/onbid_observability.py`가 다음 지표를 제공한다.

- 온비드 전체 물건 수
- 공고번호 보유 물건 수
- 상세 payload 보유 물건 수
- 공고 수
- 공고 상세 보유율
- 공고-물건 링크 수
- 최근 7일 온비드 수집 성공/실패 수
- 최근 실패 메시지
- 입찰 마감 D-day 분포

관리자 API:

```text
GET /api/admin/onbid-quality
```

관리자 화면:

```text
/admin/collection
```

### 4.5 UI UTF-8 문구 정리

`frontend/templates/admin/collection.html`을 정상 UTF-8 한글 UI로 재작성했다. 회생/파산 수집과 온비드 수집을 좌우 운영 카드로 구분하고, 온비드 데이터 품질 섹션을 추가했다.

### 4.6 스케줄러/운영 문서

PowerShell 스크립트 옵션:

```powershell
-ApiKind notice
-IncludeNoticeDetails
-IncludeNoticeItems
```

`ApiKind=all`은 기존처럼 부동산+동산 목록 수집을 뜻한다. 공고는 `ApiKind=notice`로 명시 실행한다.

운영 문서 `docs/onbid_scheduled_sync_runbook.md`는 목록 수집과 공고 상세/물건정보 수집을 별도 스케줄로 설명하도록 재작성했다.

### 4.7 테스트 보강

`tests/onbid_module_test.py`는 다음을 확인한다.

- 부동산 샘플 수집
- 부동산 상세 샘플 재수집
- 동산 샘플 수집
- 공고 목록/상세/물건정보 샘플 수집
- 공고 재수집 idempotency
- `AuctionNotice`, `AuctionNoticeItemLink`, `AuctionItem` 개수
- 관리자 수집 화면 렌더링
- `/api/admin/onbid-quality`
- 수동 사건-온비드 물건 연결 API

## 5. DB/마이그레이션 변경

- 신규 테이블: `auction_notice_item_links`
- 확장 테이블: `auction_notices`
- 기존 데이터 삭제 없음
- 기존 unique 기준 약화 없음
- `Base.metadata.create_all`과 `ensure_schema_migrations` 조합으로 SQLite 기존 DB를 비파괴 보정한다.

상세 내용은 `docs/migration_ledger.md`에 정리했다.

## 6. 검증 결과

| 검증 명령 | 결과 | 비고 |
|---|---|---|
| `python -m py_compile ...` | 통과 | 번들 Python 사용 |
| `python tests/onbid_module_test.py` | 통과 | Starlette/httpx deprecation warning만 발생 |
| `python tests/page_response_smoke_test.py` | 통과 | Starlette/httpx deprecation warning만 발생 |
| `python tests/router_boundary_test.py` | 통과 | 신규 API 포함 |
| `python tests/isolated_operations_test.py` | 통과 | Starlette/httpx deprecation warning만 발생 |
| `run_onbid_sync.ps1 -Sample -ApiKind notice -IncludeNoticeDetails -IncludeNoticeItems` | 통과 | ExitCode 0 |
| `run_onbid_scheduled_sync.ps1 -Sample -ApiKind notice -IncludeNoticeDetails -IncludeNoticeItems` | 통과 | ExitCode 0 |
| `run_scheduled_crawl.ps1 -DryRun -Limit 1 -MaxPages 1 -DaysBack 1` | 통과 | ExitCode 0 |

사용한 Python:

```text
C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
```

## 7. 실패/미완료/보류 항목

| 항목 | 이유 | 다음 조치 |
|---|---|---|
| 실제 온비드 API 호출 검증 | 네트워크 제한 및 실제 운영 키 노출 금지 | 운영 환경에서 `-Sample` 없이 소량 실행 후 payload 점검 |
| 국유일반재산 입찰대상물건 API 매핑 | 문서가 없어 응답 필드 확정 불가 | 실제 응답 샘플 저장 후 normalizer 추가 |
| 전체 UTF-8 정리 | v002에서는 관리자 수집 화면과 관련 문서 중심으로 정리 | 남은 템플릿/테스트 문구는 별도 UTF-8 cleanup sprint 권장 |
| Git diff stat | 프로젝트 폴더에서 새 repo를 초기화해 기존 파일이 untracked | 실제 원격 저장소가 있다면 연결 후 변경분 비교 필요 |

## 8. 운영 주의사항

- 실제 API 키는 `.env` 또는 운영 환경 변수에서만 관리한다.
- 온비드 공고 수집은 `ApiKind=notice`로 별도 실행한다.
- `-IncludeNoticeItems`는 `AuctionItem` upsert와 링크 생성을 수행하므로 첫 운영에서는 `Limit`/`MaxPages`를 작게 시작한다.
- `storage/onbid_scheduled_sync.lock`이 남아 있으면 중복 실행으로 판단될 수 있다.
- 운영 전 DB 백업을 권장한다.

## 9. 다음 개발 추천

1. 실제 온비드 공고 API 응답 샘플 10~50건을 수집해 field mapping 보강
2. 국유일반재산 입찰대상물건 API normalizer 추가
3. 온비드 목록 화면에 공고 연결 여부, 상세 수집 여부, 마감 D-day 필터 추가
4. 관리자 화면에 API 종류별 성공/실패와 최근 payload 누락률 표시
5. 남은 템플릿과 테스트 fixture의 UTF-8 문구 정리
6. 운영 DB 백업/복원 runbook 강화

## 10. 자체 리뷰

- 위험한 변경: 비파괴 컬럼/테이블 추가만 수행했다.
- 기존 기능 회귀 가능성: 기존 ONBID 부동산/동산 수집 테스트가 통과했다.
- 수동 확인 필요: 실제 API 응답 필드명, 국유일반재산 API 매핑, 운영 스케줄러 등록 권한.
- AI 분석 범위: 온비드는 수집/조회 중심으로 유지했고 AI 분석 자동 적용은 추가하지 않았다.
