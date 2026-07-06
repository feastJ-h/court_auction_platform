# 온비드 API 문서 분석 메모

## 1. 확인한 문서
- `OpenAPI활용가이드_01_온비드_부동산_물건목록_조회서비스.docx`
- `OpenAPI활용가이드_04_온비드_부동산_물건상세_조회서비스.docx`
- `OpenAPI활용가이드_10_온비드_공고목록_조회서비스.docx`
- `OpenAPI활용가이드_11_온비드_공고상세_조회서비스.docx`
- `OpenAPI활용가이드_13_온비드_공고상세_물건정보_조회서비스.docx`
- `OpenAPI활용가이드_02_온비드_동산_물건목록_조회서비스.docx`
- `OpenAPI활용가이드_05_온비드_동산_물건상세_조회서비스.docx`

## 2. 핵심 연결 키
- 물건 기준 기본 키
  - `cltrMngNo`
  - `pbctCdtnNo`
- 온비드 식별/회차 키
  - `onbidCltrno`
  - `onbidPbancNo`
  - `pbctNo`
  - `pbctNsq`
  - `pbctsn`
- 공고 기준 기본 키
  - `pbancMngNo`

## 3. 서비스별 필수 입력값
- 부동산 물건목록 `getRlstCltrList2`
  - `serviceKey`, `pageNo`, `numOfRows`, `resultType`, `prptDivCd`, `pvctTrgtYn`
- 부동산 물건상세 `getRlstDtlInf2`
  - `serviceKey`, `pageNo`, `numOfRows`, `resultType`, `cltrMngNo`
  - `pbctCdtnNo`는 옵션
- 공고목록 `getPbancList2`
  - `serviceKey`, `pageNo`, `numOfRows`, `resultType`, `cltrTypeCd`, `prptDivCd`, `opbdDtStart`, `opbdDtEnd`
- 공고상세 `getPbancDtlInf2`
  - `serviceKey`, `pageNo`, `numOfRows`, `resultType`, `pbancMngNo`
- 공고상세 물건정보 `getPbancCltrInf2`
  - `serviceKey`, `pageNo`, `numOfRows`, `resultType`, `pbancMngNo`
- 동산 물건목록 `getMvastCltrList2`
  - `serviceKey`, `pageNo`, `numOfRows`, `resultType`, `prptDivCd`, `pvctTrgtYn`
- 동산 물건상세 `getMvastDtlInf2`
  - `serviceKey`, `pageNo`, `numOfRows`, `resultType`, `cltrMngNo`
  - `pbctCdtnNo`는 옵션

## 4. 현재 구현에 반영한 방향
- 부동산/동산 목록과 상세를 각각 독립 메서드로 분리
- 공고목록, 공고상세, 공고상세 물건정보를 별도 메서드로 분리
- 코드 기본값과 `.env`에 실제 서비스 URL / 오퍼레이션명을 반영
- 필터 파라미터는 문서상 변동 가능성이 있어 notice 계열은 `extra_filters` 방식으로 유연하게 유지

## 5. 입찰대상물건내역 조회서비스 메모
- 문서 없음
- 현재 확인한 정보
  - Base URL: `https://apis.data.go.kr/B010003/kamcoRlcBidTrgtCltr`
  - Operation: `/cltrLst`
- 2026-07-06 실제 소량 호출 확인
  - 추가 필터 없이 `limit=1`, `pageNo=1` 호출 성공
  - `totalCount=80925` 확인
  - 응답 아이템 키는 camelCase가 아니라 대문자 스네이크 케이스
  - 샘플 키: `CRTR_YMD`, `BID_NO`, `PBANC_NO`, `PBANC_NFT`, `LAND_SQMS`, `BLD_SQMS`, `FRST_BID_AMT`, `LNG_SCHD_AMT`
- 아직 확인이 더 필요한 부분
  - 검색 필터 파라미터 목록
  - `PBANC_NO` 등이 기존 `pbancMngNo`, `pbctNo`, `cltrMngNo`와 어떻게 연결되는지
  - 응답 루트 구조가 일반 온비드 계열과 완전히 동일한지, 또는 일부 코드 체계가 다른지
- 따라서 현재 코드는 유연한 `params` 기반 호출 메서드만 추가했고, 실제 연결 키와 정규화 규칙은 후속 호출로 확정해야 함

## 6. 다음 권장 작업
- 실제 API 소량 호출로 공고상세 물건정보와 입찰대상물건내역 응답 샘플 저장
- 공고계열 응답을 `AuctionNotice` 또는 별도 `OnbidNotice*` 테이블군으로 분리 저장
- 온비드를 회생/파산 워크플로우와 분리된 독립 패키지/도메인으로 재구성
