# 온비드 실제 API 연동 스프린트 리포트

## 1. 구현된 주요 기능
- 제공받은 Word 매뉴얼을 분석해 실제 온비드 부동산 물건목록 조회 오퍼레이션을 반영했습니다.
- 실제 엔드포인트:
  - `https://apis.data.go.kr/B010003/OnbidRlstListSrvc2/getRlstCltrList2`
- 필수 파라미터:
  - `serviceKey`
  - `pageNo`
  - `numOfRows`
  - `resultType=json`
  - `prptDivCd`
  - `pvctTrgtYn`
- `.env`에 온비드 API 설정을 추가했습니다.
  - `ONBID_API_BASE_URL`
  - `ONBID_API_KEY`
- `backend/onbid/client.py`를 실제 API 호출 가능 구조로 확장했습니다.
- 온비드 실제 응답 필드를 내부 DB 저장 형식으로 정규화했습니다.
  - `cltrMngNo` -> 물건관리번호
  - `pbctCdtnNo` -> 공매조건번호
  - `onbidPbancNo` -> 공고관리번호
  - `onbidCltrNm` -> 물건명
  - `prptDivNm` -> 재산유형
  - `dspsMthodNm` -> 처분방식
  - `cptnMthodNm/bidDivNm/bidMthodNm` -> 입찰방식
  - `apslEvlAmt` -> 감정가
  - `lowstBidPrcIndctCont` -> 최저입찰가
  - `cltrBidBgngDt/cltrBidEndDt` -> 입찰 시작/마감
  - `pbctStatNm` -> 진행상태
  - `landSqms/bldSqms` -> 토지/건물 면적
- 관리자 수집 화면에 `샘플 수집`과 `실제 API 수집` 버튼을 분리했습니다.

## 2. 보안 및 예외 처리
- 인증키는 코드에 하드코딩하지 않고 `.env`에서만 로드합니다.
- 로그와 리포트에는 인증키 원문을 기록하지 않습니다.
- 실제 API 호출 실패 시 `crawl_runs`에 실패 이력이 남습니다.
- HTTP 401/오류 응답 본문을 읽어 운영자가 실패 원인을 확인할 수 있게 했습니다.
- 샘플 모드는 계속 유지되어 API 키 활성화 전에도 화면/DB/연결 기능 개발이 가능합니다.

## 3. 테스트 결과
- 문법 검사 통과:
  - `backend/onbid/client.py`
  - `backend/workers/onbid_sync.py`
  - `backend/services/auction_items.py`
  - `main_app.py`
- 샘플 회귀 테스트 통과:
  - `tests/onbid_module_test.py`
- 샘플 수집 실행 성공:
  - `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_onbid_sync.ps1 -Sample -Limit 3`
- 실제 API 소량 호출:
  - `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_onbid_sync.ps1 -Limit 1 -PageNo 1`
  - 결과: 실패 기록
  - 실패 사유: `ONBID HTTP 401: Unauthorized`

## 4. 관리자 확인 필요 사항
- 공공데이터포털에서 해당 서비스 활용신청이 승인되었는지 확인해야 합니다.
- 제공받은 키가 일반 인증키의 `Decoding` 값인지 `Encoding` 값인지 확인해야 합니다.
- 서비스 신청 직후라면 키 활성화까지 지연될 수 있습니다.
- 포털의 호출 제한, IP 제한, 서비스별 승인 상태를 확인해야 합니다.

## 5. 다음 개발 루프
- 키 활성화가 확인되면 실제 1페이지 호출을 재검증합니다.
- 실제 응답 샘플을 DB에 저장한 뒤 화면 필드 누락을 보정합니다.
- 입찰 결과/상세/공고 API 매뉴얼이 추가되면 `AuctionNotice`, `AuctionResult` 실제 수집을 연결합니다.
- 사건 상세 화면에 `공매 연결` 탭을 추가합니다.
