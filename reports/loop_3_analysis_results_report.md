# Loop 3 보고서

## 목표
Gemini와 ChatGPT/Codex 결과가 모델별로 분리 저장되고, 같은 문서/모델/분석 유형/프롬프트 버전의 중복 분석을 막는다.

## 변경한 내용
- `analysis_results` 중복 조회 조건에 `prompt_version`을 추가했다.
- `create_or_get_basic_result`, `create_or_get_deep_result`가 `prompt_version`을 인자로 받을 수 있게 했다.
- provider alias(`exec` -> `codex_cli`, `app_server` -> `codex_app_server`, `openai` -> `chatgpt`) 정규화 상태에서 중복 조회가 작동하도록 확인했다.
- deep 분석 job 생성 전에 `codex_app_server`, `codex_cli`, `chatgpt`의 기존 deep 결과를 먼저 확인하도록 보강했다.
- 기존 결과가 있으면 새 job 생성 없이 `cached` 응답을 반환하는 경로를 확인했다.

## 수정한 파일
- `backend/database/analysis_results.py`
- `backend/jobs/service.py`

## 검증 결과
- Python 문법 검증 통과
- 같은 event/provider/type/source_hash/prompt_version 재요청 시 row 증가 없음
- `exec` provider alias가 `codex_cli`로 정규화되어 같은 결과를 재사용함
- `prompt_version`이 바뀌면 새 row 생성 가능
- `force=True`이면 기존 active result의 `superseded_at`이 채워지고 새 row 생성 가능
- `/user` 200
- `/admin` 200
- `/api/local-analysis/status` 200

## 남은 위험
- 기존 이관 데이터의 `prompt_version`은 `legacy-v1`이다. 현재 기본값 `v1`과 다르므로, 프롬프트 변경에 따른 새 분석 허용이라는 의미를 갖는다.
- legacy `ai_analyses.detailed_analysis` 캐시가 아직 존재하므로 장기적으로는 사용자 화면과 job cache 판단을 `analysis_results` 중심으로 더 옮기는 것이 좋다.

## 다음 루프 지시
Loop 4에서 관리자 화면의 운영성을 강화한다. 우선 필터, 실패 job 섹션, 멈춤 가능 job/worker 표시, 모델별 결과 펼쳐보기를 추가한다.
