# Sprint 4 완료 결과 리포트

## 1. 구현된 주요 기능 (Summary)
- DB 스키마를 `RawDocument`, `Asset`, `AssetEvent`, `AiAnalysis` 구조로 정규화했습니다.
- `Asset`에는 변하지 않는 물리적 정보인 `main_category`, `sub_category`, `address`를 저장하도록 구성했습니다.
- `AssetEvent`에는 `asset_id`, `raw_doc_id`, `case_number`, `status`를 포함하고, 운영 추적을 위해 `title`, `url`, `notice_date`, `expire_date`, `parse_status`, `extracted_text`를 함께 보관합니다.
- 법원 게시글 번호 변경에 대비해 내부 고유번호 `RP-작성일-순번` 체계를 도입했습니다.
- 크롤러가 상세 게시글의 작성일/공고만료일 후보를 추출하고, 최상단 게시물 순서대로 최대 5개 첨부파일만 보관하도록 제한했습니다.
- Gemini 프롬프트를 Sprint 4 JSON 스키마로 갱신했습니다.
  - `main_category`: `부동산` 또는 `동산` 강제 분류
  - `sub_category`, `address`, `min_price`, `risk_comment` 추출
- 사용자 UI를 GNB, 부동산/동산 탭 필터, 좌우 Split 상세 분석 View로 전면 개편했습니다.
- 관리자 UI를 정규화 DB 기준의 읽기 전용 통합 검수 화면으로 갱신했습니다.

## 2. 보안 및 예외 처리 내역 (Security & Edge Cases Handled)
- `.env`의 Gemini API 키는 로드 여부만 확인했고, 리포트나 로그에 키 값을 노출하지 않았습니다.
- `ENABLE_PII_MASKING=False` 상태를 확인했습니다. 현재 요구에 따라 원문 텍스트가 DB와 AI에 전달됩니다.
- 크롤러는 0 Byte 파일과 비정상 확장자 파일을 삭제/거부합니다.
- 다운로드 파일 SHA-256 해시를 저장해 원본 추적성을 유지합니다.
- Gemini 호출은 3회 재시도와 Flash fallback 로직을 유지합니다.
- 콘솔 로그는 `처리 건수`, `다운로드`, `파싱`, `AI 성공/실패`만 출력하며 원문 텍스트나 개인정보를 출력하지 않습니다.

## 3. 단위 및 통합 테스트 결과 (Test Results)
- 실행한 테스트: `python -m py_compile main_app.py orchestrator.py backend/...`
  - 결과: Pass
- 실행한 테스트: `python -m backend.ai_engine.test_analyzer`
  - 결과: Pass
- 실행한 테스트: `python -m backend.parser.test_parser`
  - 결과: Pass
- 실행한 테스트: `python test_orchestrator.py`
  - 결과: Pass
  - 출력: `처리 건수: 5, 다운로드: 5, 파싱: 5, AI 성공: 5, AI 실패: 0`
- DB 검증:
  - `raw_documents`: 5건
  - `assets`: 5건
  - `asset_events`: 5건
  - `ai_analyses`: 5건
- 웹 검증:
  - `GET /user`: HTTP 200
  - `GET /admin`: HTTP 200
  - 사용자 화면 GNB 항목 확인: 회생·파산, 법원경매 Lock, 온비드공매 Lock, 지도 탐색 Lock, Admin Dashboard
  - 사용자 화면 리스트: 5건
  - 동산 탭 필터 후 표시: 3건
  - 관리자 화면 행: 5건

## 4. 실제 5건 분석 결과 요약
| 내부번호 | 작성일 | 공고만료일 | 대분류 | 세부 분류 | 최저가 |
|---|---:|---:|---|---|---:|
| RP-20260703-001 | 2026-07-03 | 2026-07-31 | 동산 | 상표권 | 500000 |
| RP-20260703-002 | 2026-07-03 | 2026-07-27 | 동산 | 자동차 | 19000000 |
| RP-20260703-003 | 2026-07-03 | 2026-09-14 | 부동산 | 오피스텔 | 250000000 |
| RP-20260703-004 | 2026-07-03 | 2026-08-04 | 동산 | 사무기기 | 1000000 |
| RP-20260703-005 | 2026-07-03 | 2026-07-31 | 부동산 | 임야 지분 | 6000000 |

## 5. UI 캡처
- 사용자 Split UI 캡처: `reports/sprint_4_user_split.png`
- 관리자 Dashboard 캡처: `reports/sprint_4_admin.png`

## 6. 다음 Sprint 검토 필요 사항
- 현재 `google-generativeai` 패키지는 실행 가능하지만 deprecation 경고가 발생합니다. 다음 단계에서 `google-genai` SDK로 이전하는 것을 권장합니다.
- `gemini-1.5-flash`는 현재 제공된 키의 호출 가능 모델 목록에서 제외되어 있어 404가 발생합니다. 현재는 요청 모델을 먼저 시도하고 실패 시 `gemini-flash-latest`로 대체합니다.
- 작성일/만료일은 상세 페이지 본문에서 정규식으로 추출합니다. 법원 사이트 표기 방식이 바뀌면 추출 규칙을 보강해야 합니다.
- 실서비스 전환 시 `ENABLE_PII_MASKING=True` 전환과 관리자 접근 제어가 필요합니다.
