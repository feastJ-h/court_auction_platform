# Sprint 3 완료 결과 리포트

## 1. 구현된 주요 기능 (Summary)
- `court_auction_platform` 신규 구조를 구성하고 `storage/raw_quarantine`, `storage/processed`, `backend`, `frontend`, `reports` 디렉토리를 생성했습니다.
- SQLite 기반 SQLAlchemy 모델 `RawDocument`, `AssetEvent`, `AiAnalysis`와 CRUD/세션 모듈을 구현했습니다.
- Playwright 기반 법원 부동산 공고 게시판 크롤러를 구현하고, 첨부 PDF/HWP 계열 파일을 격리 저장소에 저장하도록 구성했습니다.
- PDF/HWP/HWPX 텍스트 추출 모듈과 선택형 PII 마스킹 모듈을 구현했습니다. 현재 `.env` 기준 `ENABLE_PII_MASKING=False`라 원문 텍스트가 DB와 AI에 전달됩니다.
- Gemini 분석 모듈을 구현했습니다. 요청 모델 `gemini-1.5-flash`를 우선 시도하고, 현재 API에서 해당 모델이 404로 거부될 경우 `gemini-flash-latest`로 대체해 Flash 분석 흐름을 유지합니다.
- FastAPI + Jinja2 + Tailwind CDN 기반 `/user`, `/admin` 웹 대시보드를 구현했습니다.
- PowerShell 실행 스크립트 `run_fastapi.ps1`, `start_fastapi_background.ps1`, `stop_fastapi.ps1`, `run_pipeline.ps1`을 추가했습니다.

## 2. 보안 및 예외 처리 내역 (Security & Edge Cases Handled)
- 크롤러 다운로드 직후 0 Byte 파일, 존재하지 않는 파일, 비정상 확장자 파일을 삭제/거부하는 Phantom 다운로드 방어 로직을 적용했습니다.
- 다운로드 파일의 SHA-256 해시를 계산해 `RawDocument.file_hash`로 저장하고 중복 원본을 방지합니다.
- PII 마스킹은 토글 기반으로 구현했습니다. 주민등록번호와 휴대폰 번호 정규식은 준비되어 있으며, `ENABLE_PII_MASKING=True`일 때만 실행됩니다.
- Gemini 호출은 Tenacity 기반 지수 백오프 3회 재시도를 적용했습니다.
- Gemini 응답 JSON에 필수 키가 누락되면 `is_hallucinated=True`로 저장할 수 있도록 필터를 구현했습니다.
- 관리/사용자 화면은 원본 파일이나 비밀키를 노출하지 않고 DB 분석 결과 중심으로 조회합니다.

## 3. 단위 및 통합 테스트 결과 (Test Results)
- 실행한 테스트 스크립트: `python -m backend.parser.test_parser`
  - 결과: Pass
  - 비고: 다운로드된 PDF가 없는 초기 상태에서는 통합 파서 테스트를 스킵하도록 방어했습니다.
- 실행한 테스트 스크립트: `python -m backend.ai_engine.test_analyzer`
  - 결과: Pass
- 실행한 테스트 스크립트: `python -m backend.crawler.test_scraper`
  - 결과: Pass
  - 검증: 실제 대법원 부동산 공고 게시판에서 파일 다운로드 성공
- 실행한 테스트 스크립트: `python test_orchestrator.py`
  - 결과: Pass
  - 검증: 법원 크롤링 -> 파일 저장 -> 텍스트 추출 -> Gemini Flash JSON 분석 -> SQLite 저장 성공
- 웹 렌더링 검증:
  - `GET http://127.0.0.1:8000/user` -> HTTP 200
  - `GET http://127.0.0.1:8000/admin` -> HTTP 200
  - 인앱 브라우저에서 `/user`, `/admin` 페이지 제목/목록 렌더링 확인

## 4. 실제 실행 결과 스냅샷
- DB 저장 건수: RawDocument 1건, AssetEvent 1건, AiAnalysis 1건
- 격리 저장소 파일: `storage/raw_quarantine/2026하합1080_가림종합건설_주식회사_지식재산권_매각_공고.pdf`
- 처리 텍스트 파일: `storage/processed/2026하합1080_가림종합건설_주식회사_지식재산권_매각_공고.txt`
- FastAPI 서버: `http://127.0.0.1:8000`

## 5. 관리자 검토 필요 사항
- 현재 Google `google-generativeai` 패키지는 실행 가능하지만 deprecation 경고가 발생합니다. 다음 Sprint에서는 공식 최신 SDK인 `google-genai`로 이전하는 것을 권장합니다.
- 사용자가 지정한 `gemini-1.5-flash`는 현재 제공된 API 키의 모델 목록에서 호출 가능 모델로 확인되지 않았습니다. 서비스 연속성을 위해 404 발생 시 `gemini-flash-latest`로 자동 대체하도록 구현했습니다.
- 현재 `ENABLE_PII_MASKING=False`이므로 관리자 화면과 AI 분석 입력에 원문 텍스트가 사용됩니다. 실서비스 전환 시 반드시 `True` 전환을 검토해야 합니다.
- 법원 사이트 HTML 구조 변경 시 크롤러 셀렉터 보강이 필요할 수 있습니다.
