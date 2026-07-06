# Codex 개발팩 v004 작업 지시서

## Real ONBID API & Public Beta Operations Megapack

- 작성일: 2026-07-06
- 대상 저장소: `C:\Users\xogns\Documents\testAuction\court_auction_platform`
- 원격 저장소: `https://github.com/feastJ-h/court_auction_platform.git`
- 권장 기준 상태: v003 Public Beta Readiness Pack 1 커밋과 push 완료 이후
- 권장 작업 브랜치: `codex/devpack-v004-real-onbid-operations`
- 지시서 위치: `reports/devpacks/devpack_v004_instruction.md`
- 최종 결과 bundle 위치: `reports/devpacks/devpack_v004_result_bundle.md`
- 최신 프로젝트 상태 문서: `reports/project-result_current.md`
- 마이그레이션 장부: `docs/migration_ledger.md`

이 개발팩은 단발성 작은 수정이 아니라 장시간 작업을 전제로 한 v004 통합 개발팩이다. v003에서 비로그인 공개 탐색, 로그인 온비드 개인화, 회생/파산 AI/raw 노출 차단, 광고 슬롯 feature flag, SEO/고지 초안, 권한 경계 테스트가 추가되었다. v004는 이 공개 베타 기반 위에서 **실제 온비드 API 소량 운영 수집, 국유일반재산 독립 카테고리 구현, 온비드 카테고리/지역/가격 중심 UX 정리, 운영 DB 백필 전략, 대량 데이터 성능 점검, 관리자 운영 준비도 강화, 로그/개인정보/약관 정리**를 한 번에 진행한다.

---

## 0. 최상위 목표

v004의 최상위 목표는 다음 한 문장으로 정의한다.

```text
실제 온비드 API 데이터를 20건 단위로 안전하게 받아와 정규화 기반을 확정하고, 국유일반재산을 독립 카테고리로 수집/표시하며, 공개 베타 운영에 필요한 검색 UX·관리자 관찰성·백필·성능·로그·개인정보/고지 체계를 크게 강화한다.
```

제품 방향:

```text
Public browsing:
  비로그인 사용자는 온비드와 회생/파산 기본 정보를 편하게 볼 수 있다.

Simple ONBID search:
  온비드 공개 필터는 지역, 가격, 카테고리 중심으로 단순화한다.

Real data readiness:
  실제 온비드 API 응답을 20건 단위로 수집/분석해 normalizer field mapping을 보강한다.

Operations readiness:
  운영자는 관리자 화면에서 데이터 누락, 수집 실패, API 상태, 백업/로그/스케줄러 준비 상태를 볼 수 있다.
```

---

## 1. 작업 시작 전 필수 절차

### 1.1 Git 상태 확인

작업 시작 직후 아래 명령을 실행하고 결과를 최종 bundle에 기록한다.

```powershell
git rev-parse --show-toplevel
git branch --show-current
git status --short
git remote -v
git --no-pager log --oneline --decorate -8
```

정상 기대값:

```text
Git root: C:/Users/xogns/Documents/testAuction/court_auction_platform
Branch: codex/devpack-v004-real-onbid-operations
Remote: https://github.com/feastJ-h/court_auction_platform.git
```

다음이면 기능 개발을 중단하고 result bundle에 기록한다.

- Git root가 예상 경로가 아니다.
- 현재 브랜치가 `main`이다.
- `git init`이 필요해 보인다.
- `.env`, DB, `storage/`, 로그, runtime 파일이 stage되어 있다.
- 작업 시작 전 사용자 변경분이 있어 덮어쓸 위험이 있다.

### 1.2 AGENTS.md 읽기

repo root의 `AGENTS.md`를 먼저 읽고 따른다. 지시서와 AGENTS.md가 충돌하면 이 v004 지시서가 우선한다. 보안/금지 규칙은 더 엄격한 쪽을 따른다.

### 1.3 작업 중 질문 기준

사소한 판단은 사용자에게 묻지 말고 이 지시서의 기준에 따라 진행한다.

다음 상황은 구현을 멈추지 말고 안전한 대안을 적용하거나 보류 처리 후 result bundle에 기록한다.

- 외부 API 호출이 실패한 경우
- API quota, timeout, network, 인증 오류가 발생한 경우
- 실제 API 응답 필드가 예상과 다른 경우
- 파괴적 DB 변경이 필요한 경우
- 원문 파일/개인정보/AI 분석 노출 위험이 있는 경우
- 기존 테스트를 무력화해야만 진행 가능한 경우

---

## 2. 절대 금지 사항

- `git init` 실행 금지
- `main` 브랜치 직접 개발 금지
- `.git` 삭제 금지
- `git reset --hard`, `git clean -fd`, `git clean -fdx` 금지
- `.env`, `*.db`, `*.sqlite`, `storage/`, `logs/`, `runtime_settings.json` 커밋 금지
- DB/storage/raw documents 삭제 금지
- 내부 원문 파일 전체 공개 금지
- 회생/파산 AI 분석 비로그인 공개 금지
- 온비드 전체 물건 AI 분석 자동 적용 금지
- 회생/파산 사건과 온비드 물건 자동 강제 연결 금지
- destructive migration 금지
- Alembic 본격 전환 금지
- 실제 AdSense 송출/운영 연동 금지
- 알림 후보/이메일 알림/web push/브라우저 push 구현 금지
- 낙찰결과/AuctionResult 본 구현 금지
- 결제/구독 기능 금지
- 실제 Windows 작업 스케줄러 등록 강제 실행 금지
- API key 출력, 로그 기록, 문서 기록 금지
- 테스트 삭제/무력화 금지

---

## 3. v004에서 명시적으로 제외하는 범위

사용자 결정에 따라 v004에서 제외한다.

```text
알림:
  회원 동의, 이메일/web push, 개인정보 처리, 수신 거부가 함께 필요한 영역이므로 v004에서 제외한다.

AdSense:
  v003의 feature flag와 placeholder는 유지하되 실제 client/slot 운영 연동은 제외한다.

낙찰결과:
  AuctionResult/낙찰/결과 데이터는 추후 별도 논의한다.

입찰/저감률 필터:
  공개 필터로 노출하지 않는다. 카드/상단 안내 문구로만 간단히 보여준다.

데이터 품질 수치:
  공개 화면에 숫자 점수로 표시하지 않는다. 부족한 정보 안내만 제공한다.
```

---

## 4. 작업 범위 운영 방식

작업은 세 단계로 진행한다.

```text
Core Scope:
  반드시 완료해야 하는 v004 핵심 범위.

Extended Scope:
  Core 완료 후 계속 진행할 운영/품질 강화 범위.

Stretch Scope:
  시간이 남으면 진행할 polish/추가 안정화 범위.
```

진행 원칙:

- Core Scope 완료 후 멈추지 않는다.
- Core Scope 테스트가 통과하면 Extended Scope로 넘어간다.
- Extended Scope까지 안정화되면 Stretch Scope를 우선순위대로 진행한다.
- 중간 결과서를 여러 개 만들지 않는다.
- 모든 판단, 보류, 실패, 테스트, 운영 확인은 `reports/devpacks/devpack_v004_result_bundle.md` 하나에 통합한다.
- commit/push는 하지 않는다. 사용자가 로컬 확인 후 직접 수행한다.

---

# Core Scope

## 5. 온비드 공개 UX 재정리: 지역/가격/카테고리 중심

### 5.1 공개 필터 정책

v003의 온비드 필터는 기능적으로 넓게 들어갔지만, v004에서는 공개 UX를 단순화한다.

공개 목록 `/onbid`에 노출할 필터:

```text
1. 지역
2. 가격
3. 카테고리
```

공개 UI에서 제거하거나 숨길 필터:

```text
- 입찰/마감 필터
- 저감률 필터
- 데이터 품질 필터
- 공고 연결 여부 필터
- 상세 수집 여부 필터
```

단, 내부 service/query에서 기존 파라미터를 완전히 삭제할 필요는 없다. 기존 테스트나 URL 호환을 위해 backend에서 지원은 유지할 수 있다. 하지만 공개 UI의 기본 노출은 지역/가격/카테고리 중심으로 정리한다.

### 5.2 입찰/저감률 정보 표시 방식

입찰 마감과 저감률은 필터가 아니라 안내 정보로만 사용한다.

목록 상단 또는 카드에 간단히 표시:

```text
- 오늘/이번주 마감 안내
- 마감 D-day
- 감정가 대비 최저가 차이
- 저감률이 있으면 텍스트 또는 badge로 표시
```

하지만 사용자가 상세 필터에서 `마감일`, `저감률`을 고르는 구조는 v004에서 노출하지 않는다.

### 5.3 가격 필터

가격 필터는 사용자가 가장 이해하기 쉬운 preset과 직접 입력을 함께 제공한다.

권장 UI:

```text
가격 전체
1억 이하
1억 ~ 3억
3억 ~ 5억
5억 이상
직접 입력: 최저가 min/max
```

가격 기준은 우선 `min_bid_price`를 중심으로 한다. 감정가가 필요한 경우 상세 카드에 표시하되, 필터의 기본 기준은 최저입찰가 또는 최저가로 통일한다.

### 5.4 지역 필터

지역 필터는 `location`, `address`, `site`, 기타 소재지 후보에서 시/도 또는 주요 지역 키워드를 추출한다.

권장 구현:

```text
- 지역 전체
- 서울
- 경기
- 인천
- 부산
- 대구
- 대전
- 광주
- 울산
- 세종
- 강원
- 충북
- 충남
- 전북
- 전남
- 경북
- 경남
- 제주
- 직접 검색어
```

지역 데이터가 부족한 물건은 제외하지 말고 `지역 정보 확인 필요`로 표시한다.

### 5.5 no-result UX

필터 결과가 없을 때 빈 화면만 보여주지 않는다.

문구 예시:

```text
조건에 맞는 물건이 없습니다.
지역을 전체로 바꾸거나 가격 범위를 넓혀보세요.
현재는 실제 API 수집 초기 단계라 일부 지역/카테고리 데이터가 부족할 수 있습니다.
```

---

## 6. 온비드 카테고리 구조 구현

### 6.1 카테고리 원칙

물건 유형은 단순 필터가 아니라 공개 탐색의 큰 카테고리로 다룬다.

공개 카테고리:

```text
전체
부동산
동산
국유일반재산
기타
```

포함 규칙:

```text
부동산:
  토지, 건물, 상가, 주거, 기타 부동산성 물건을 모두 포함한다.

동산:
  차량, 운송, 기계, 장비, 기타 동산성 물건을 모두 포함한다.

국유일반재산:
  동산/부동산을 구분하지 않고 독립 카테고리로 묶는다.
  category=national_property로 표시한다.

기타:
  위 규칙으로 분류하기 어려운 물건.
```

### 6.2 URL 정책

라우트를 많이 만들지 말고 `/onbid?category=...`를 기본으로 한다.

```text
/onbid
/onbid?category=real_estate
/onbid?category=movable
/onbid?category=national_property
/onbid?category=other
```

화면에서는 탭처럼 보여준다.

```text
[전체] [부동산] [동산] [국유일반재산] [기타]
```

### 6.3 카테고리 derivation

`AuctionItem`의 기존 필드에서 카테고리를 파생하는 service 함수를 만든다.

후보 함수명:

```python
derive_onbid_category(item_or_payload) -> str
get_onbid_category_label(category: str) -> str
```

분류 기준 후보:

```text
source_api
source
asset_type
usage
category
raw_payload keys
API kind
국유일반재산 API에서 온 payload 여부
```

DB 컬럼 추가 여부:

- 우선 service-derived category로 구현한다.
- 대량 데이터 성능 테스트에서 필요성이 확인되면 `AuctionItem`에 비파괴 신규 컬럼을 추가할 수 있다.
- 신규 컬럼 추가 시 `docs/migration_ledger.md`에 기록한다.

### 6.4 테스트

다음 테스트를 추가한다.

```text
- 토지/건물/상가/주거가 부동산으로 분류되는지
- 차량/운송/기계/장비가 동산으로 분류되는지
- 국유일반재산 API payload가 national_property로 분류되는지
- 알 수 없는 payload는 other로 분류되는지
- /onbid?category=national_property가 비로그인 200을 유지하는지
```

---

## 7. 정보 부족 안내: 수치 점수 금지

### 7.1 공개 화면 정책

공개 화면에 `품질 점수 73점` 같은 숫자를 표시하지 않는다.

대신 부족한 정보만 사용자 친화적으로 표시한다.

부족 정보 후보:

```text
가격 정보 확인 필요
소재지 정보 확인 필요
입찰 일정 확인 필요
공고 연결 전
상세 정보 수집 전
원문 링크 확인 필요
기관 정보 확인 필요
```

충족 정보 badge 후보:

```text
가격 정보 있음
소재지 있음
입찰 일정 있음
공고 연결
상세 수집됨
원문 링크 있음
```

### 7.2 service 함수

후보 함수:

```python
build_onbid_info_badges(item) -> dict
```

반환 예시:

```python
{
    "available": ["가격 정보 있음", "공고 연결"],
    "missing": ["소재지 정보 확인 필요", "입찰 일정 확인 필요"],
    "has_critical_missing": True,
}
```

수치 점수를 반환하더라도 공개 템플릿에 표시하지 않는다. 관리자 내부 계산에만 사용 가능하다.

### 7.3 관리자 화면 정책

관리자에게는 수치가 아니라 비율/누락률을 보여준다.

```text
가격 누락률
소재지 누락률
입찰 일정 누락률
공고 연결률
상세 payload 보유율
원문 링크 보유율
```

---

## 8. 같은 공고의 다른 물건 UX

v003에서는 연결 공고 요약은 구현됐지만 같은 공고의 다른 물건 탐색은 보류됐다. v004에서 구현한다.

### 8.1 상세 화면

`/onbid/{auction_item_id}`에 섹션을 추가한다.

```text
같은 공고의 다른 물건
- 같은 공고 내 물건 수
- 현재 물건 표시
- 다른 물건 최대 10~20건
- 물건명
- 지역
- 최저가
- 카테고리
- 정보 부족 badge
- 상세 보기 링크
```

### 8.2 목록 링크

상세의 공고 요약에서 같은 공고 보기 링크를 제공한다.

예:

```text
/onbid?notice_id={notice_id}
```

또는 기존 식별자가 더 안전하면:

```text
/onbid?pbanc_mng_no={pbanc_mng_no}
```

### 8.3 데이터 기준

`AuctionNoticeItemLink`를 사용한다.

```text
same notice_id
-> linked auction_item_id list
-> current item 제외
-> 최신/가격/카테고리 기준 정렬
```

공고-물건 링크 unique 기준 `source + notice_id + auction_item_id`는 변경하지 않는다.

---

## 9. 실제 온비드 API 소량 운영 수집

사용자 확인: API key는 현재 준비되어 있다. v004에서는 실제 API를 20건 단위로 소량 수집한다.

### 9.1 사전 안전 절차

실제 API/DB 수집 전 반드시 DB 백업을 시도한다.

```powershell
.\backup_database.ps1
```

백업 스크립트가 실패하면 실제 DB 저장형 수집은 진행하지 말고, probe/dry-run만 진행한다.

### 9.2 API key 정책

- `.env` 또는 환경 변수에서만 읽는다.
- key 값은 출력하지 않는다.
- key의 존재 여부만 true/false 또는 configured/not configured로 기록한다.
- 로그와 result bundle에 key 일부도 기록하지 않는다.

### 9.3 실제 수집 목표

각 API를 기본 20건, 1 page로 제한한다.

권장 실제 수집 명령 후보:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_onbid_scheduled_sync.ps1 -RunType manual -ApiKind real_estate -Limit 20 -MaxPages 1 -IncludeDetails
powershell -ExecutionPolicy Bypass -File .\run_onbid_scheduled_sync.ps1 -RunType manual -ApiKind movable -Limit 20 -MaxPages 1 -IncludeDetails
powershell -ExecutionPolicy Bypass -File .\run_onbid_scheduled_sync.ps1 -RunType manual -ApiKind notice -Limit 20 -MaxPages 1 -IncludeNoticeDetails -IncludeNoticeItems
```

국유일반재산 API는 별도 probe/수집 명령을 만든 뒤 실행한다.

```powershell
powershell -ExecutionPolicy Bypass -File .\run_onbid_probe.ps1 -ApiKind national_property -Limit 20 -MaxPages 1
```

명령명은 구현 상황에 맞게 조정 가능하다. 단 result bundle에 실제 실행한 명령을 정확히 기록한다.

### 9.4 실행 실패 처리

네트워크, API key, quota, endpoint 오류가 발생하면:

```text
- 작업 전체를 중단하지 않는다.
- sample mode 테스트는 계속 수행한다.
- API 실패 원인과 응답 status/code를 key 없이 기록한다.
- normalizer 보강은 확보된 sample/fixture 기준으로 진행한다.
```

### 9.5 결과 기록

result bundle에 다음을 기록한다.

```text
- API kind
- Limit/MaxPages
- 저장/갱신/중복/실패 건수
- 대표 top-level response keys
- normalizer가 채운 필드
- 누락 필드
- raw payload 저장 위치, 단 Git 커밋 제외
- 실제 API key 값 미노출 확인
```

---

## 10. 국유일반재산 API 실제 샘플 기반 구현

v002/v003에서 문서 부족으로 보류된 `kamcoRlcBidTrgtCltr / cltrLst`를 v004에서 실제 샘플 기반으로 구현한다.

### 10.1 핵심 정책

- 국유일반재산은 동산/부동산으로 재분류하지 않는다.
- 공개 화면에서는 독립 카테고리 `국유일반재산`으로 묶는다.
- 내부 category 값은 `national_property`를 사용한다.
- field mapping은 실제 응답 샘플을 기준으로 한다.
- 필드가 불확실하면 raw payload에 보존하고, 공개 화면에는 `정보 확인 필요`로 표시한다.

### 10.2 클라이언트/worker

기존 `OnbidClient.fetch_bid_target_items` 또는 준비된 설정 기반 호출 함수를 점검한다.

필요하면 다음을 보강한다.

```text
backend/onbid/client.py
backend/workers/onbid_sync.py
backend/services/auction_items.py
run_onbid_probe.ps1 또는 run_onbid_scheduled_sync.ps1 옵션
```

지원 API kind 후보:

```text
national_property
bid_target
```

화면/문서에서는 `national_property` 명칭을 우선한다.

### 10.3 저장 정책

가능하면 `AuctionItem`으로 저장한다.

필수/우선 매핑 후보:

```text
물건명
소재지
기관명
감정가
최저입찰가
보증금
입찰 시작일
입찰 마감일
개찰일
용도
공고 번호
물건 번호
원문 URL/detail URL
```

불확실한 필드:

```text
raw_payload에 보존
공개 화면에는 직접 노출하지 않음
result bundle에 field 후보만 key 이름 중심으로 요약
```

중복 기준:

- 기존 `AuctionItem` unique 기준 `source + cltr_mng_no + pbct_cdtn_no`를 약화하지 않는다.
- 국유일반재산 응답에 `cltr_mng_no` 또는 `pbct_cdtn_no`와 동등한 식별자가 없으면 공식 응답 내 안정 식별자 조합으로 deterministic key를 구성한다.
- 임의 UUID, 실행 시각, row index만으로 중복 key를 만들지 않는다.

### 10.4 테스트

테스트 fixture를 추가한다.

```text
- 국유일반재산 sample payload normalizer
- AuctionItem upsert
- category=national_property
- 공개 /onbid?category=national_property 200
- 정보 부족 badge 표시
```

---

## 11. field mapping 확정과 normalizer 보강

실제 API 20건 수집 또는 probe 결과를 바탕으로 normalizer 후보 필드를 보강한다.

대상 파일 후보:

```text
backend/services/auction_items.py
backend/onbid/client.py
backend/workers/onbid_sync.py
```

보강 대상:

```text
물건명
소재지
기관명
감정가
최저입찰가
보증금
입찰 시작일
입찰 마감일
개찰일
용도
물건 유형/카테고리
원문 URL/detail URL
공고 번호
물건 번호
회차 번호
```

원칙:

- 실제 응답에서 확인된 필드를 우선한다.
- 기존 샘플 fixture와 기존 후보 필드는 유지한다.
- 문서만 보고 추측 매핑을 크게 바꾸지 않는다.
- raw payload는 DB에는 보존 가능하지만 Git에 커밋하지 않는다.
- mapping 변경은 result bundle에 API kind별로 정리한다.

---

## 12. 운영 DB 백필 전략

v004에서는 실제 전체 백필을 대량으로 돌리는 것이 아니라, 운영 가능한 백필 전략과 작은 batch 실행 구조를 준비한다.

### 12.1 백필 정책

백필은 다음 원칙을 따른다.

```text
- 실행 전 DB 백업
- 작은 batch
- RunType=backfill
- Limit/MaxPages 명시
- 실패 시 재시작 가능
- 중복 기준 유지
- 로그 저장
- 관리자 지표로 결과 확인
```

### 12.2 명령 예시

```powershell
powershell -ExecutionPolicy Bypass -File .\run_onbid_scheduled_sync.ps1 -RunType backfill -ApiKind notice -Limit 20 -MaxPages 1 -IncludeNoticeDetails -IncludeNoticeItems
powershell -ExecutionPolicy Bypass -File .\run_onbid_scheduled_sync.ps1 -RunType backfill -ApiKind real_estate -Limit 20 -MaxPages 1 -IncludeDetails
powershell -ExecutionPolicy Bypass -File .\run_onbid_scheduled_sync.ps1 -RunType backfill -ApiKind movable -Limit 20 -MaxPages 1 -IncludeDetails
```

국유일반재산 백필은 실제 field mapping이 안정화된 뒤 적용한다.

### 12.3 result bundle 기록

```text
- 백필 전제 조건
- 추천 실행 순서
- 중단/재시작 방식
- 백업 위치
- 실패 로그 확인 위치
- 관리자 화면 확인 항목
```

---

## 13. 대량 데이터 성능 점검

실제 대량 API 수집을 무리하게 하지 않고, synthetic 또는 isolated test DB로 성능 하네스를 만든다.

### 13.1 테스트 목표

```text
- /onbid category 필터 성능
- 지역 필터 성능
- 가격 필터 성능
- pagination 성능
- 같은 공고 다른 물건 조회 성능
- 관리자 onbid-quality API 성능
```

### 13.2 synthetic data

테스트에서는 실제 운영 DB를 오염시키지 않는다.

```text
storage/test/*.db 또는 in-memory DB 사용
AuctionItem 5,000~20,000건 synthetic 생성
AuctionNotice/AuctionNoticeItemLink 일부 생성
```

### 13.3 인덱스 검토

필요하면 비파괴 인덱스를 추가한다.

후보:

```text
auction_items.source
auction_items.cltr_mng_no
auction_items.pbct_cdtn_no
auction_items.min_bid_price
auction_items.bid_end_at
auction_items.location
auction_items.usage
auction_items.agency_name
auction_notices.pbanc_mng_no
auction_notice_item_links.notice_id
auction_notice_item_links.auction_item_id
```

인덱스 추가 시:

```text
- SQLite에서 비파괴적으로 추가
- docs/migration_ledger.md 업데이트
- 테스트 통과 확인
```

---

# Extended Scope

## 14. 관리자 관찰성 2차 강화

v004에서는 운영자가 실제 데이터 수집 상태를 매일 볼 수 있도록 `/admin/collection`과 `/api/admin/onbid-quality`를 강화한다.

추가 지표:

```text
- 최근 24시간 신규 물건 수
- 최근 7일 신규 물건 수
- 최근 24시간 갱신 물건 수
- 최근 7일 갱신 물건 수
- API kind별 성공/실패
- 공고 연결률
- 공고 상세 payload 보유율
- 상세 payload 보유율
- 가격 정보 누락률
- 소재지 정보 누락률
- 입찰 일정 누락률
- 원문 링크 보유율
- 국유일반재산 수집 건수
- 카테고리별 물건 수
- 최근 실패 메시지 top N
- lock file 존재 여부
- 최근 로그 파일 경로
```

관리자에게는 품질 점수가 아니라 비율/누락률/상태 중심으로 보여준다.

---

## 15. 관리자 운영 준비도 화면 또는 섹션

가능하면 신규 route를 추가한다.

```text
/admin/operations-readiness
```

또는 기존 `/admin/collection`에 섹션으로 포함한다.

점검 항목:

```text
- DB 백업 최근 생성 여부
- 실제 온비드 API key 설정 여부, 값은 노출 금지
- 최근 온비드 real_estate 수집 성공 여부
- 최근 온비드 movable 수집 성공 여부
- 최근 온비드 notice 수집 성공 여부
- 최근 국유일반재산 probe/수집 성공 여부
- 공고 연결률
- 정보 부족 비율
- robots.txt 응답 여부
- sitemap.xml 응답 여부
- /privacy, /terms, /disclaimer 존재 여부
- 로그 보관 dry-run 가능 여부
- 스케줄러 점검 dry-run 가능 여부
```

---

## 16. 백업/복원 리허설

### 16.1 backup 점검

기존 `backup_database.ps1`를 점검하고, 실패 시 오류 메시지가 명확하도록 개선한다.

### 16.2 restore dry-run

가능하면 `restore_database.ps1`를 추가한다.

기본은 dry-run이다.

```powershell
.\restore_database.ps1 -BackupPath storage\backups\auction_data_YYYYMMDD_HHMMSS.db -DryRun
```

실제 복원은 명시 옵션 없이는 금지한다.

```powershell
.\restore_database.ps1 -BackupPath ... -ConfirmRestore
```

`-ConfirmRestore` 없이 실제 DB를 덮어쓰면 안 된다.

### 16.3 문서화

별도 markdown 문서를 만들기보다 result bundle에 runbook을 통합한다. 필요하면 script help에 사용법을 포함한다.

---

## 17. 스케줄러 점검 dry-run

실제 Windows 작업 스케줄러 등록을 강제하지 않는다. 점검 도구를 준비한다.

후보 스크립트:

```text
check_scheduled_tasks.ps1
```

기능:

```text
- 권장 온비드 목록 수집 작업 존재 여부 확인
- 권장 온비드 공고 상세/물건정보 작업 존재 여부 확인
- 회생/파산 수집 작업 존재 여부 확인
- 마지막 실행 결과
- 다음 실행 시각
- 누락된 작업의 권장 등록 명령 출력
```

실제 등록은 하지 않는다. 등록이 필요한 경우 result bundle에 사용자 실행 명령만 제시한다.

---

## 18. 로그 보관 정책

v004에서는 실제 삭제가 아니라 dry-run 중심의 로그 보관 정책을 준비한다.

후보 스크립트:

```text
run_log_retention.ps1
```

기본 정책 후보:

```text
storage/logs/onbid/: 30일
uvicorn/codex/app server logs: 14~30일
storage/backups/: 최근 N개 또는 30일
storage/raw_quarantine/: 삭제 금지
storage/processed/: 삭제 금지
```

명령 예:

```powershell
.\run_log_retention.ps1 -DryRun
.\run_log_retention.ps1 -Apply -LogsOnly
```

안전 규칙:

- 기본은 DryRun이다.
- `-Apply` 없이는 삭제하지 않는다.
- raw/processed 원문 문서 삭제 금지.
- 삭제 대상 목록을 먼저 출력한다.

---

## 19. 동적 sitemap / robots 강화

v003 sitemap은 정적 공개 URL 중심이었다. v004에서는 공개 베타 수준으로 강화한다.

### 19.1 robots.txt

다음 보호 경로를 명확히 차단한다.

```text
/admin
/api/admin
/user
/my
/documents/raw
/storage
```

### 19.2 sitemap.xml

포함 후보:

```text
/
/onbid
/cases
/about
/disclaimer
/privacy
/terms
/onbid/{id} 일부
/cases/{id} 일부, 단 민감 정보 과다 노출 주의
```

동적 URL 정책:

- 온비드 상세는 정보가 충분하고 공개 가능한 물건만 제한적으로 포함한다.
- 국유일반재산도 공개 가능한 경우 포함 가능하다.
- 회생/파산 상세는 공개 DTO 기준으로 안전한 경우만 포함한다.
- `/admin`, `/user`, `/my`, `/documents/raw`, `/api/admin`은 sitemap에 절대 포함하지 않는다.
- 최대 개수 제한을 둔다.

---

## 20. 회생/파산 공개 검색 개선

v004에서 가능한 범위로 `/cases` 공개 검색을 강화한다.

필터:

```text
- 검색어
- 법원/기관
- 지역
- 상태
- 공고일 범위
- 마감일 범위
```

정렬:

```text
- 최신 공고순
- 마감 임박순
```

권한 경계:

- AI 분석, OCR 전문, raw file path, `/documents/raw/{id}`는 계속 공개하지 않는다.
- 기존 `tests/public_access_auth_boundary_test.py`를 확장한다.

---

## 21. 개인정보 처리방침/약관/고지 정리

v003의 `/privacy-draft`를 v004에서 베타용 초안 수준으로 정리한다.

라우트 후보:

```text
/privacy
/terms
/disclaimer
```

`/privacy-draft`는 유지하거나 `/privacy`로 redirect한다.

포함할 내용:

```text
수집하는 정보:
- 계정 ID
- 표시명
- 로그인 세션
- 관심/패스/감시/메모
- 접속/운영 로그

수집하지 않는 정보:
- 결제 정보 없음
- 알림 수신 정보 없음, 알림 미구현
- 광고 개인화 정보 없음, AdSense 실제 미연동

이용 목적:
- 개인화 목록
- 관심/패스 관리
- 서비스 운영/보안

보관 기간:
- 계정 삭제 전까지 또는 운영 정책 기준
- 로그는 v004 로그 보관 정책 기준

제3자 제공:
- 없음
- 단, 원문 링크 클릭 시 외부 사이트로 이동

AI 분석 고지:
- 회생/파산 AI 분석은 참고자료
- 원문 공고 확인 필요
- 입찰/투자 판단 책임은 사용자에게 있음
```

법률 검토 전 초안임을 명확히 표시한다.

---

# Stretch Scope

## 22. 원문 링크/출처 신뢰 표시 강화

공개 온비드와 회생/파산 상세에 다음을 표시한다.

```text
- 데이터 출처
- 마지막 수집 시각
- 원문 확인 권장 문구
- 외부 원문 링크
```

내부 raw payload와 storage 경로는 공개하지 않는다.

---

## 23. 공개 상세 meta / Open Graph 개선

가능하면 상세 페이지별 meta를 개선한다.

온비드:

```text
title: 물건명 + 지역 + 가격 정보
description: 소재지, 최저가, 기관, 원문 확인 안내
```

회생/파산:

```text
title: 공고 제목 + 기관/법원
description: 공개 기본 정보 + 원문 확인 안내
```

회생/파산은 민감할 수 있으므로 meta에 과도한 정보는 넣지 않는다.

---

## 24. UTF-8 깨진 문구 1차 정리

가능하면 실제 서비스 템플릿과 테스트 fixture 중심으로 깨진 한글을 정리한다.

대상:

```text
frontend/templates
frontend/static
main_app.py route text
selected tests fixture strings
```

제외:

```text
과거 reports/devpacks 또는 오래된 결과 보고서 전체 대량 수정
대량 포맷팅
```

---

## 25. 테스트 하네스 대폭 강화

v004 기능에 맞춰 테스트를 추가한다.

후보 파일:

```text
tests/onbid_category_filter_test.py
tests/onbid_real_api_probe_test.py
tests/admin_observability_test.py
tests/sitemap_public_routes_test.py
tests/backup_restore_runbook_test.py
tests/scheduler_scripts_test.py
tests/public_case_search_test.py
tests/onbid_performance_smoke_test.py
```

필수 검증:

```text
- /onbid 공개 200
- /onbid category 필터
- /onbid region/price 필터
- /onbid national_property category
- 정보 부족 badge
- 같은 공고 다른 물건 섹션
- /cases 공개 검색
- /documents/raw 비로그인 차단 유지
- /api/admin/onbid-quality 비로그인 차단 유지
- robots/sitemap 보호 경로 제외
- backup/restore dry-run
- scheduler check dry-run
- log retention dry-run
```

---

## 26. AGENTS.md 보강

필요하면 repo root `AGENTS.md`를 v004 기준으로 보강한다.

추가할 내용:

```text
- 실제 API 호출 20건 제한
- 국유일반재산 독립 카테고리 규칙
- 공개 필터 지역/가격/카테고리 중심 규칙
- 정보 부족 안내, 수치 품질 점수 비노출 규칙
- 알림/AdSense/낙찰결과 v004 제외 규칙
- 로그 보관 dry-run 규칙
- 실제 DB restore ConfirmRestore 요구 규칙
```

---

# 검증 요구사항

## 27. 기본 검증 명령

Codex runtime Python을 사용한다.

```powershell
$Py = "C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

& $Py -m py_compile main_app.py backend/database/models.py backend/database/session.py backend/web/routers/auctions.py backend/web/routers/cases.py backend/web/routers/admin_operations.py backend/services/auction_items.py backend/services/onbid_observability.py
& $Py tests/onbid_module_test.py
& $Py tests/page_response_smoke_test.py
& $Py tests/router_boundary_test.py
& $Py tests/isolated_operations_test.py
& $Py tests/public_access_auth_boundary_test.py
powershell -ExecutionPolicy Bypass -File .\run_onbid_scheduled_sync.ps1 -Sample -ApiKind notice -Limit 20 -MaxPages 1 -IncludeNoticeDetails -IncludeNoticeItems
```

## 28. v004 추가 검증 명령

구현한 파일명에 맞춰 실제 명령을 조정하되, result bundle에 정확히 기록한다.

예상:

```powershell
& $Py tests/onbid_category_filter_test.py
& $Py tests/admin_observability_test.py
& $Py tests/sitemap_public_routes_test.py
& $Py tests/backup_restore_runbook_test.py
& $Py tests/scheduler_scripts_test.py
& $Py tests/public_case_search_test.py
& $Py tests/onbid_performance_smoke_test.py
```

실제 API 수집/probe는 key가 준비되어 있으므로 20건 제한으로 실행을 시도한다.

```powershell
powershell -ExecutionPolicy Bypass -File .\run_onbid_scheduled_sync.ps1 -RunType manual -ApiKind real_estate -Limit 20 -MaxPages 1 -IncludeDetails
powershell -ExecutionPolicy Bypass -File .\run_onbid_scheduled_sync.ps1 -RunType manual -ApiKind movable -Limit 20 -MaxPages 1 -IncludeDetails
powershell -ExecutionPolicy Bypass -File .\run_onbid_scheduled_sync.ps1 -RunType manual -ApiKind notice -Limit 20 -MaxPages 1 -IncludeNoticeDetails -IncludeNoticeItems
```

국유일반재산은 구현한 명령으로 실행한다.

```powershell
powershell -ExecutionPolicy Bypass -File .\run_onbid_probe.ps1 -ApiKind national_property -Limit 20 -MaxPages 1
```

실제 명령이 다르면 result bundle에 실제 명령을 기록한다.

## 29. 민감 파일 검사

최종 stage는 하지 않더라도, 민감 파일이 변경/추적되지 않았는지 검사한다.

```powershell
git status --short
$trackedSensitive = git ls-files | Select-String -Pattern '(^|[\\/])\.env($|[\\/])|(^|[\\/])storage[\\/]|(^|[\\/])logs[\\/]|(^|[\\/])runtime_settings\.json$|\.(db|sqlite|sqlite3)$|(^|[\\/])\.git\.bad-init'
if ($trackedSensitive) {
    $trackedSensitive
    throw "민감 파일이 tracked 상태입니다. 확인 필요."
}
```

---

# 결과 bundle 작성 요구사항

## 30. 필수 결과 파일

Codex는 최종적으로 다음 파일을 작성/갱신한다.

```text
reports/devpacks/devpack_v004_result_bundle.md
reports/project-result_current.md
docs/migration_ledger.md
```

필요 시 `AGENTS.md`를 보강할 수 있다.

새로운 문서성 markdown을 남발하지 않는다. 별도 운영 문서가 꼭 필요하면 result bundle에 이유와 파일명을 기록한다.

## 31. result bundle 구조

`reports/devpacks/devpack_v004_result_bundle.md`는 반드시 다음 섹션을 포함한다.

```markdown
# Codex 개발 결과 Bundle v004

## 1. 작업 메타데이터
- Git root:
- Branch:
- Base commit:
- Final commit(s): commit/push 미수행
- Remote:
- 작업 시작 status:
- 작업 종료 status:

## 2. 고수준 결과 요약

## 3. Core Scope 결과
### 3.1 온비드 지역/가격/카테고리 UX
### 3.2 카테고리 분류 규칙
### 3.3 정보 부족 안내
### 3.4 같은 공고 다른 물건 UX
### 3.5 실제 API 20건 수집/probe
### 3.6 국유일반재산 API 구현
### 3.7 field mapping/normalizer 보강
### 3.8 백필 전략
### 3.9 대량 데이터 성능 점검

## 4. Extended Scope 결과
### 4.1 관리자 관찰성 2차
### 4.2 운영 준비도
### 4.3 백업/복원 dry-run
### 4.4 스케줄러 점검 dry-run
### 4.5 로그 보관 정책
### 4.6 sitemap/robots
### 4.7 회생/파산 공개 검색
### 4.8 개인정보/약관/고지

## 5. Stretch Scope 결과

## 6. 실제 API 호출 결과
| API kind | Limit | MaxPages | 결과 | 저장/갱신/중복/실패 | 비고 |

## 7. 국유일반재산 field mapping 요약
| 원본 key 후보 | 매핑 필드 | 확신도 | 비고 |

## 8. 변경 파일 목록
| 파일 | 변경 요약 | 위험도 | 비고 |

## 9. DB/마이그레이션 변경
- 신규 테이블:
- 신규 컬럼:
- 신규 인덱스:
- 비파괴 여부:
- rollback 방법:

## 10. 공개/로그인/관리자 경계

## 11. 테스트 결과
| 명령 | 결과 | 비고 |

## 12. 로컬 서버 확인 가이드

## 13. 미완료/보류/리스크

## 14. v005 추천 작업

## 15. Codex CLI 운영 메모
```

## 32. project-result_current.md 갱신

`reports/project-result_current.md`에는 v004 이후 최신 상태를 짧고 정확히 정리한다.

반드시 포함:

```text
- v004 완료 기능
- 공개 온비드 카테고리 정책
- 실제 API 수집 결과 요약
- 국유일반재산 구현 상태
- 관리자 운영 준비도 상태
- 새 테스트
- 남은 리스크
- v005 우선순위
```

## 33. migration ledger 갱신

다음 중 하나라도 있으면 `docs/migration_ledger.md`를 갱신한다.

```text
- 신규 테이블
- 신규 컬럼
- 신규 인덱스
- ensure_schema_migrations 변경
- category 저장 구조 변경
- 국유일반재산 저장을 위한 schema 변경
```

---

# v004 완료 기준

v004는 다음을 만족하면 완료로 본다.

```text
1. /onbid 공개 필터 UI가 지역/가격/카테고리 중심으로 정리된다.
2. 카테고리는 전체/부동산/동산/국유일반재산/기타 구조를 갖는다.
3. 부동산은 토지/건물/상가/주거를 포함하고, 동산은 차량/운송을 포함한다.
4. 국유일반재산은 동산/부동산으로 나누지 않고 독립 카테고리로 표시된다.
5. 입찰/저감률은 필터가 아니라 안내/카드 정보로만 표시된다.
6. 공개 화면에 데이터 품질 숫자 점수는 표시하지 않고, 정보 부족 안내만 표시한다.
7. /onbid/{id}에서 같은 공고의 다른 물건을 볼 수 있다.
8. 실제 API key가 있으면 real_estate/movable/notice를 20건 단위로 수집/probe한다.
9. 국유일반재산 API를 실제 샘플 기반으로 호출/분석하고 가능한 범위로 AuctionItem 저장 또는 probe 구조를 구현한다.
10. field mapping과 normalizer가 실제 응답 기준으로 보강된다.
11. 운영 DB 백필 전략과 작은 batch 실행 기준이 result bundle에 정리된다.
12. 대량 데이터 성능 점검 하네스 또는 테스트가 추가된다.
13. 관리자 관찰성에 누락률, 연결률, 카테고리별 건수, API별 성공/실패가 추가된다.
14. 백업/복원, 스케줄러 점검, 로그 보관은 dry-run 중심으로 준비된다.
15. 개인정보/약관/고지 페이지가 베타용 초안 수준으로 정리된다.
16. 알림, AdSense 실제 연동, 낙찰결과는 구현하지 않는다.
17. public/auth/admin 권한 경계 테스트가 계속 통과한다.
18. devpack_v004_result_bundle.md 하나에 전체 결과가 통합된다.
```

---

# Codex CLI 실행용 goal 문구

Codex CLI에서 지시서 파일을 저장한 뒤 아래 goal을 사용할 수 있다.

```text
/goal Implement reports/devpacks/devpack_v004_instruction.md on branch codex/devpack-v004-real-onbid-operations. Complete Core Scope first, then Extended Scope, then Stretch Scope as far as safely possible. Use real ONBID API calls with Limit=20 MaxPages=1 when the configured key is available, without printing secrets. Keep ONBID public filters focused on region, price, and category; treat national_property as an independent category; show missing information badges instead of numeric quality scores; exclude alerts, real AdSense integration, and auction results. Produce one consolidated result bundle at reports/devpacks/devpack_v004_result_bundle.md and update reports/project-result_current.md and docs/migration_ledger.md as needed. Do not commit or push.
```

---

# 최종 주의

이번 v004는 실제 API와 운영 DB를 다루므로 반드시 작은 범위로 시작한다.

- 실제 API는 `Limit=20`, `MaxPages=1`을 기본으로 한다.
- API key는 절대 출력하지 않는다.
- DB 백업 전 실제 저장형 수집을 하지 않는다.
- raw payload 파일은 Git에 커밋하지 않는다.
- 공개 화면에서 AI 분석, 내부 원문, raw payload를 노출하지 않는다.
- commit/push는 하지 않는다.
