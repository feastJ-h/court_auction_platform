# 온비드 공고 저장 설계 v002

## 목적

v002의 목적은 온비드 공고 목록, 공고 상세, 공고 물건정보 API를 기존 온비드 물건 수집 흐름과 충돌 없이 저장하는 것이다. 회생/파산 AI 분석 흐름과 온비드 공매 데이터 수집 흐름은 분리한다.

## API 흐름

### 공고 목록

- 서비스: `OnbidPbancListSrvc2`
- 오퍼레이션: `getPbancList2`
- 클라이언트 함수: `OnbidClient.fetch_notice_items`
- 저장 대상: `AuctionNotice.raw_payload`
- 정규화 함수: `normalize_onbid_notice`

공고 목록은 `pbancMngNo`, `onbidPbancNo`, `pbancNo`, `noticeNo` 후보 필드를 공고 식별자로 사용한다.

### 공고 상세

- 서비스: `OnbidPbancDtlnfSrvc2`
- 오퍼레이션: `getPbancDtlInf2`
- 클라이언트 함수: `OnbidClient.fetch_notice_detail`
- 저장 대상: `AuctionNotice.detail_payload`

상세 API 응답은 목록 필드를 덮어쓸 수 있는 보강 자료로 사용한다. 제목, 본문, 기관, 입찰 방식, 상세 URL 등은 상세 응답에 더 명확한 값이 있으면 우선 반영한다.

### 공고 물건정보

- 서비스: `OnbidPbancCltrDtlSrvc2`
- 오퍼레이션: `getPbancCltrInf2`
- 클라이언트 함수: `OnbidClient.fetch_notice_cltr_items`
- 저장 대상: `AuctionItem`, `AuctionNoticeItemLink`

공고 물건정보는 `normalize_onbid_api_item(..., source_api="notice_cltr")`를 통해 기존 `AuctionItem` 구조로 정규화한다. 이후 `upsert_auction_item`을 재사용해 기존 중복 기준을 유지한다.

## DB 모델

### AuctionNotice

v002에서 다음 필드를 보강했다.

- `notice_no`: 공고 고유번호 후보
- `pbct_no`, `pbct_nsq`, `pbct_cdtn_no`: 입찰/회차 식별 보조값
- `notice_status`, `notice_type`, `notice_date`: 공고 상태와 유형
- `bid_start_at`, `bid_end_at`, `open_at`: 입찰 일정
- `department_name`: 담당 부서
- `detail_url`: 온비드 상세 URL 후보
- `item_count`: 공고에 연결된 물건 수
- `detail_payload`: 공고 상세 API 원문
- `last_seen_at`: 마지막 수집 확인 시각

기존 `source`, `pbanc_mng_no`, `notice_title`, `notice_body`, `agency_name`, `disposal_method`, `bid_method`, `raw_payload`는 유지한다.

### AuctionNoticeItemLink

공고와 물건의 관계를 추적하기 위한 association table이다.

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

unique 기준은 `source + notice_id + auction_item_id`다. 물건 자체의 중복 기준은 기존 `source + cltr_mng_no + pbct_cdtn_no`를 유지한다.

## 수집 워커

`backend/workers/onbid_sync.py`는 다음 옵션을 지원한다.

```text
--api-kind notice
--include-notice-details
--include-notice-items
```

`api_kind=all`은 기존 의미 그대로 부동산 목록과 동산 목록만 수집한다. 공고 API는 `api_kind=notice`로 명시한다.

## 샘플/테스트

API 키가 없거나 `sample=True`이면 다음 샘플을 사용한다.

- `SAMPLE_NOTICE_ITEMS`
- `SAMPLE_NOTICE_DETAILS`
- `SAMPLE_NOTICE_CLTR_ITEMS`

샘플 흐름은 공고 2건, 공고 물건 3건, 링크 3건을 만든다. 재실행하면 공고와 물건은 update/duplicate로 처리되고 링크는 update로 처리된다.

## 관찰성

`backend/services/onbid_observability.py`가 관리자 화면과 API의 공통 지표를 만든다.

- 온비드 물건 수
- 공고 수
- 상세 payload 보유 공고 수
- 공고-물건 링크 수
- 최근 실행 성공/실패
- 최근 실패 메시지
- 입찰 마감 분포

관리자 API는 다음 경로다.

```text
GET /api/admin/onbid-quality
```

## 남은 리스크

- 실제 공공데이터 응답 필드명이 문서와 다를 수 있으므로 raw payload 보존을 우선했다.
- 국유일반재산 입찰대상물건 API는 문서가 없어 v002에서는 구조 점검 대상으로 남겼다.
- 본격 운영 전 실제 API 응답 샘플을 한 번 저장해 normalizer 후보 키를 보강하는 단계가 필요하다.
