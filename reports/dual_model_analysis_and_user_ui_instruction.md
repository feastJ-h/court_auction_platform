# Gemini / ChatGPT 이중 분석 및 사용자 UI 개선 지시서

## 1. 목적

현재 시스템은 기본 분석과 상세 분석 결과가 하나의 대표 결과처럼 표시되는 구조다. 앞으로는 Gemini와 ChatGPT 분석 결과를 각각 보존하고, 사용자가 두 모델의 관점 차이를 비교할 수 있게 한다.

동시에 분석을 여러 번 반복하면 API/CLI/시간 자원이 낭비되므로, 동일 문서와 동일 모델에 대한 중복 분석을 막고, 필요한 경우에만 재분석하도록 한다.

최종 목표:

- Gemini 기본/상세 분석 결과를 별도 보존
- ChatGPT/Codex 기본/상세 분석 결과를 별도 보존
- 사용자 화면에서 두 결과를 쉽게 비교
- 관리자 화면에서 모델별 분석 상태와 비용성 작업 상태 확인
- 중복 분석 방지
- 실제 서비스에 가까운 UI/UX 개선

## 2. 핵심 원칙

1. 분석 결과는 모델별로 저장한다.
2. 같은 원본 문서, 같은 모델, 같은 분석 타입이면 기본적으로 재분석하지 않는다.
3. 재분석은 관리자 권한에서 명시적으로 요청할 때만 수행한다.
4. 사용자 화면은 “결과 비교와 의사결정”에 집중한다.
5. 관리자 화면은 “작업 상태, 실패 원인, 모델별 결과”에 집중한다.
6. 웹 요청 안에서 장시간 분석을 직접 수행하지 않는다.
7. 로컬 Codex/ChatGPT 분석은 큐와 워커를 통해 비동기로 처리한다.

## 3. 현재 구조의 한계

현재 주요 저장 구조:

```text
ai_analyses
  - event_id
  - item_details
  - min_price
  - bidding_date
  - risk_comment
  - detailed_analysis
  - analysis_provider
```

한계:

- 하나의 `event_id`에 여러 모델 결과를 안정적으로 보존하기 어렵다.
- Gemini 결과와 ChatGPT 결과를 동시에 비교하기 어렵다.
- 재분석하면 기존 결과를 덮어쓸 위험이 있다.
- 사용자는 어떤 모델이 어떤 판단을 했는지 명확히 보기 어렵다.
- 서비스 UI 관점에서 “검토해야 할 물건”, “분석 완료 물건”, “모델 간 의견 차이”가 잘 드러나지 않는다.

## 4. 목표 데이터 구조

### 4.1 권장 신규 테이블: `analysis_results`

기존 `ai_analyses`는 대표/호환용으로 유지하고, 모델별 결과는 새 테이블로 분리한다.

```text
analysis_results
  id
  event_id
  model_provider
  model_name
  analysis_type
  source_hash
  status
  item_details
  min_price
  bidding_date
  risk_comment
  detailed_analysis
  structured_json_path
  markdown_path
  confidence
  is_hallucinated
  created_at
  updated_at
  superseded_at
  run_count
```

`model_provider`:

```text
gemini
chatgpt
codex_cli
codex_app_server
```

`analysis_type`:

```text
basic
deep
followup
comparison
```

`status`:

```text
PENDING
RUNNING
SUCCEEDED
FAILED
CANCELED
CACHED
```

### 4.2 중복 분석 방지 키

중복 방지 기준:

```text
event_id + model_provider + analysis_type + source_hash
```

동일 조합의 `SUCCEEDED` 결과가 있으면 새 분석을 만들지 않고 기존 결과를 반환한다.

### 4.3 기존 `ai_analyses`와의 관계

단기:

- 기존 `ai_analyses`는 사용자 화면의 대표 분석으로 유지한다.
- 신규 `analysis_results`가 생기면 대표 결과는 선택 규칙에 따라 동기화한다.

중기:

- 사용자 화면은 `analysis_results`를 직접 읽는다.
- `ai_analyses`는 legacy 호환용 또는 대표 캐시로 축소한다.

대표 결과 선택 규칙:

```text
1. ChatGPT/Codex 상세 분석이 있으면 대표 상세 분석으로 사용
2. 없으면 Gemini 상세 분석 사용
3. 상세 분석이 없으면 기본 분석만 표시
4. 모델 간 결과가 다르면 “의견 차이 있음” 배지 표시
```

## 5. 분석 큐 설계

분석 요청은 모델별로 따로 생성한다.

예시:

```text
event_id 10, gemini, basic
event_id 10, chatgpt, basic
event_id 10, gemini, deep
event_id 10, codex_app_server, deep
```

분석 요청 생성 시 확인:

1. 같은 모델/분석타입의 성공 결과가 있는가?
2. 같은 모델/분석타입의 `PENDING` 또는 `RUNNING` job이 있는가?
3. 원본 문서 hash가 바뀌었는가?
4. 관리자가 강제 재분석을 요청했는가?

기본 정책:

```text
성공 결과 있음 -> CACHED 반환
진행 중 job 있음 -> 기존 job 반환
원본 변경 없음 -> 재분석하지 않음
강제 재분석 -> 새 버전 생성, 이전 결과 superseded 처리
```

## 6. 사용자 화면 개선 방향

### 6.1 목록 화면

사용자 화면은 단순 목록이 아니라 “검토 우선순위”를 보여줘야 한다.

정렬:

```text
1. 상세 분석 완료
2. Gemini/ChatGPT 둘 다 완료
3. 모델 간 위험 판단 차이가 큰 물건
4. 법원 등록일 최신순
5. 내부 id 오름차순
```

카드에 표시할 정보:

- 사건번호
- 제목
- 물건 유형
- 등록일 / 만료일 / 입찰일
- 최저가
- 분석 완료 상태
- Gemini 결과 상태
- ChatGPT 결과 상태
- 위험도 배지
- 모델 간 차이 배지

예시 배지:

```text
Gemini 완료
ChatGPT 완료
상세 분석 대기
모델 의견 차이
권리 리스크 높음
가격 검토 필요
```

### 6.2 상세 화면

상세 화면은 탭 구조를 권장한다.

```text
요약
Gemini 분석
ChatGPT 분석
비교
원문
작업 로그
```

`요약` 탭:

- 대표 결론
- 주요 리스크
- 확인해야 할 서류
- 입찰/매각 의사결정 메모

`Gemini 분석` 탭:

- Gemini 기본 분석
- Gemini 상세 분석
- 생성 시각
- 모델명
- 실패/경고

`ChatGPT 분석` 탭:

- ChatGPT/Codex 기본 분석
- ChatGPT/Codex 상세 분석
- 생성 시각
- thread/turn id
- 실패/경고

`비교` 탭:

- 두 모델이 공통으로 지적한 리스크
- 한쪽 모델만 지적한 리스크
- 가격 판단 차이
- 날짜/서류 차이
- 최종 검토 메모

`원문` 탭:

- PDF/HWP 원본 열기
- 추출 텍스트
- 상세 페이지 수집 증거

`작업 로그` 탭:

- 분석 요청 시각
- 대기/진행/완료/실패
- 최근 이벤트
- 재분석 여부

## 7. 관리자 화면 개선 방향

관리자 화면은 운영 콘솔이다.

상단:

```text
전체 물건
Gemini 완료
ChatGPT 완료
두 모델 모두 완료
분석 대기
분석 실패
```

필터:

```text
전체
Gemini 미완료
ChatGPT 미완료
두 모델 모두 완료
실패
모델 의견 차이
재분석 필요
```

물건별 표시:

- 기본 정보
- 모델별 분석 상태
- 모델별 최종 생성 시각
- 분석 결과 미리보기
- 재분석 버튼
- 강제 재분석 버튼
- 실패 사유
- 최근 이벤트

운영 경고:

- 로컬 분석 앱 꺼짐
- PENDING job 누적
- RUNNING job 장시간 유지
- 실패율 증가
- API key 없음
- Codex 로그인 필요

## 8. 비용/자원 절감 정책

### 8.1 캐시 우선

동일 조건 분석이 있으면 기존 결과를 사용한다.

```text
source_hash 동일
model_provider 동일
analysis_type 동일
prompt_version 동일
```

`prompt_version`도 추가하는 것이 좋다.

프롬프트가 바뀌면 새 분석이 필요할 수 있기 때문이다.

### 8.2 강제 재분석 제한

강제 재분석은 관리자만 가능하게 한다.

버튼 문구:

```text
재분석
강제 재분석
```

차이:

```text
재분석: 실패/취소/미완료만 다시 요청
강제 재분석: 성공 결과가 있어도 새 버전 생성
```

### 8.3 모델별 기본 실행 정책

초기 운영 추천:

```text
Gemini: 빠른 기본 분석 또는 보조 분석
ChatGPT/Codex: 상세 분석 및 최종 판단 보조
```

대량 운영 추천:

```text
1차: Gemini 기본 분석
2차: 조건부 ChatGPT 상세 분석
3차: 고위험/고가 물건만 두 모델 비교
```

## 9. 구현 순서

### Sprint A: 모델별 결과 저장

1. `analysis_results` 테이블 추가
2. 기존 `ai_analyses` 데이터를 `analysis_results`로 마이그레이션
3. 모델별 결과 조회 repository 추가
4. 중복 분석 방지 로직 추가
5. 대표 결과 선택 함수 추가

완료 기준:

- 하나의 물건에 Gemini/ChatGPT 결과를 동시에 저장할 수 있다.
- 기존 화면이 깨지지 않는다.

### Sprint B: 사용자 UI 개선

1. 목록 카드에 모델별 완료 배지 추가
2. 상세 화면에 Gemini/ChatGPT/비교 탭 추가
3. 분석 미완료 물건은 뒤로 정렬
4. 모델 간 차이 배지 추가
5. 모바일 상세 화면 UX 정리

완료 기준:

- 사용자가 두 모델 분석을 쉽게 비교할 수 있다.
- 분석 완료 물건이 먼저 보인다.

### Sprint C: 관리자 운영 콘솔 개선

1. 모델별 완료/실패 카운트 추가
2. 모델별 필터 추가
3. 재분석/강제 재분석 버튼 추가
4. 실패 사유와 최근 이벤트를 모델별로 표시
5. 로컬 분석 앱 상태와 큐 상태를 더 명확히 표시

완료 기준:

- 운영자가 어떤 모델 분석이 부족한지 바로 알 수 있다.
- 불필요한 재분석을 피할 수 있다.

### Sprint D: 비교 분석 생성

1. Gemini 결과와 ChatGPT 결과를 입력으로 비교 분석 job 생성
2. 공통 리스크/차이점/최종 검토 메모 생성
3. 비교 결과를 `analysis_results.analysis_type = comparison`으로 저장
4. 사용자 화면의 비교 탭에 표시

완료 기준:

- 두 모델이 같은 물건을 다르게 판단한 부분을 볼 수 있다.

## 10. UI 디자인 기준

서비스 화면은 운영 도구처럼 명확하고 빠르게 훑을 수 있어야 한다.

원칙:

- 카드 안에 카드를 과하게 중첩하지 않는다.
- 목록은 조밀하지만 읽기 쉽게 유지한다.
- 완료/대기/실패 상태는 색과 텍스트를 함께 사용한다.
- 버튼은 명확한 행동만 둔다.
- 사용자 화면에는 내부 로그를 과하게 노출하지 않는다.
- 관리자 화면에는 로그와 실패 사유를 충분히 노출한다.

사용자 화면 우선순위:

```text
1. 이 물건을 봐야 하는가?
2. 위험한가?
3. 두 모델이 동의하는가?
4. 원문 근거가 있는가?
5. 다음 확인 사항은 무엇인가?
```

관리자 화면 우선순위:

```text
1. 분석 앱이 살아 있는가?
2. 큐가 밀렸는가?
3. 어떤 모델 분석이 부족한가?
4. 실패한 이유는 무엇인가?
5. 재분석이 필요한가?
```

## 11. 추가 개발 권장

### 11.1 워커 heartbeat

분석 앱이 실제로 살아 있는지 표시하기 위해 heartbeat 테이블을 추가한다.

```text
analysis_worker_heartbeats
  worker_type
  last_seen_at
  current_job_id
  status_message
```

### 11.2 분석 품질 검수

관리자가 모델별 분석에 점수를 줄 수 있게 한다.

```text
analysis_reviews
  result_id
  reviewer
  score
  comment
  approved
```

### 11.3 프롬프트 버전 관리

프롬프트가 바뀌면 분석 결과도 버전을 구분해야 한다.

```text
prompt_version
prompt_name
model_provider
```

### 11.4 모델 비교 자동 요약

두 모델 결과가 모두 있으면 자동으로 비교 요약을 생성한다.

표시 예:

```text
공통 결론
차이점
추가 확인 사항
최종 검토 우선순위
```

## 12. 완료 기준

- Gemini와 ChatGPT 분석 결과를 동시에 저장한다.
- 같은 모델/같은 문서의 중복 분석을 막는다.
- 사용자 화면에서 두 모델 결과와 비교 결과를 볼 수 있다.
- 관리자 화면에서 모델별 완료/실패/대기 상태를 볼 수 있다.
- 재분석과 강제 재분석이 구분된다.
- 서비스 운영 중 자원 낭비를 줄일 수 있다.

