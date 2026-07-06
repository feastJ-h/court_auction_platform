# Sprint 5 완료 결과 리포트

## 1. 구현된 주요 기능 (Summary)
- Gemini 분석 프롬프트를 고도화하여 `item_details`, `bidding_date`를 추가 추출하도록 변경했습니다.
- `AiAnalysis` 테이블에 `item_details`, `bidding_date`, `analysis_provider` 컬럼을 추가했습니다.
- Gemini 모델 호출 순서를 `gemini-1.5-flash-latest` -> `gemini-flash-latest` fallback으로 구성했습니다.
- 무료 API RPM 제한 회피를 위해 실제 API 호출 전 `time.sleep(4)` 지연을 추가했습니다.
- 분석 제공자 옵션을 추가했습니다.
  - `ANALYSIS_PROVIDER=gemini`: 기본값, 현재 실전 테스트 완료
  - `ANALYSIS_PROVIDER=openai`: OpenAI/ChatGPT API 옵션, `OPENAI_API_KEY` 필요
- FastAPI 라우터에 D-Day 계산 로직을 추가했습니다.
  - `D-14`, `D-Day`, `D+3(마감)`, `미정` 형태로 Jinja2 템플릿에 전달
- 사용자 UI에 D-Day 뱃지, 상품 상세 요약 박스, 기본 분석/상세 심층 분석 섹션을 추가했습니다.
- 상세 심층 분석 버튼은 현재 “준비 중입니다. 부동산 실거래가 / 동산 중고 시세 연동 예정” 모달을 표시합니다.
- 관리자 UI에 입찰일, D-Day, 상품 상세, 분석 엔진 표시를 추가했습니다.

## 2. 보안 및 예외 처리 내역 (Security & Edge Cases Handled)
- Gemini API 키와 OpenAI API 키는 `.env`에서만 로드하며 리포트/로그에 값을 노출하지 않았습니다.
- `OPENAI_API_KEY`는 비워 둔 상태입니다. OpenAI 옵션은 키가 없으면 명확한 예외를 반환합니다.
- 분석 로그는 처리 건수 중심으로 유지하며 원문 텍스트를 출력하지 않습니다.
- Gemini 모델 404/unsupported 오류 발생 시 fallback 모델로 재시도합니다.
- `bidding_date`는 `YYYY-MM-DD`만 정상 날짜로 인정하고, 그 외는 `미정`으로 정규화합니다.
- `min_price`는 숫자만 남기고 없으면 `0`으로 저장합니다.

## 3. 단위 및 통합 테스트 결과 (Test Results)
- 실행한 테스트: `python -m py_compile ...`
  - 결과: Pass
- 실행한 테스트: `python -m backend.ai_engine.test_analyzer`
  - 결과: Pass
- 실행한 테스트: `python -m backend.parser.test_parser`
  - 결과: Pass
- 실행한 테스트: `python test_orchestrator.py`
  - 결과: Pass
  - 출력: `처리 건수: 5, 다운로드: 5, 파싱: 5, AI 성공: 5, AI 실패: 0`
  - 실행 시간: 약 101초
  - 비고: Gemini primary 모델 실패 후 fallback 모델과 4초 지연이 반영되어 이전보다 실행 시간이 증가했습니다.
- DB 검증:
  - `raw_documents`: 5건
  - `assets`: 5건
  - `asset_events`: 5건
  - `ai_analyses`: 5건
  - `item_details` 채움: 5건
  - `bidding_date != 미정`: 5건
- 웹 검증:
  - `GET /user`: HTTP 200
  - `GET /admin`: HTTP 200
  - 사용자 화면: D-Day, 입찰일, 상품 상세, 상세 심층 분석 버튼 확인
  - 심층 분석 버튼: 준비중 모달 표시 확인
  - 관리자 화면: 입찰일, 상품 상세, 분석 엔진 표시 확인

## 4. 실제 5건 분석 결과 요약
| 내부번호 | 대분류 | 세부 분류 | 입찰일 | 최저가 | 분석 엔진 |
|---|---|---|---:|---:|---|
| RP-20260703-001 | 동산 | 상표권 | 2026-07-10 | 500000 | gemini |
| RP-20260703-002 | 동산 | 자동차 | 2026-07-15 | 19000000 | gemini |
| RP-20260703-003 | 부동산 | 오피스텔 | 2026-08-13 | 250000000 | gemini |
| RP-20260703-004 | 동산 | 컴퓨터 및 모니터 | 2026-07-21 | 1000000 | gemini |
| RP-20260703-005 | 부동산 | 임야 | 2026-07-17 | 6000000 | gemini |

## 5. UI 캡처
- 사용자 D-Day UI: `reports/sprint_5_user_dday.png`
- 상세 심층 분석 준비중 모달: `reports/sprint_5_deep_modal.png`
- 관리자 UI: `reports/sprint_5_admin.png`

## 6. OpenAI/ChatGPT 연결 준비 사항
- 현재 Codex 유료 결제는 이 앱의 OpenAI API 호출 권한으로 자동 사용되지 않습니다.
- OpenAI 분석을 실제로 쓰려면 다음 값이 필요합니다.
  - `OPENAI_API_KEY`: OpenAI Platform에서 발급한 API 키
  - `OPENAI_MODEL`: 기본값 `gpt-5.5`
  - `ANALYSIS_PROVIDER=openai`
- OpenAI Python SDK는 설치 완료했고 `requirements.txt`에 `openai`를 추가했습니다.
- OpenAI 키가 준비되면 `.env`에서 `ANALYSIS_PROVIDER=openai`로 바꾼 뒤 `python test_orchestrator.py`로 동일한 5건 분석을 테스트할 수 있습니다.

## 7. 다음 Sprint 검토 필요 사항
- `google-generativeai` 패키지는 deprecation 경고가 발생합니다. 다음 단계에서 `google-genai` SDK로 이전하는 것을 권장합니다.
- 상세 심층 분석 버튼은 현재 UI 기반만 마련했습니다. 다음 Sprint에서는 부동산 실거래가, 동산 중고 시세, 감정가 대비 할인율 계산 모듈을 붙이면 됩니다.
- OpenAI provider는 키가 없어서 실제 호출 검증은 수행하지 않았습니다.
