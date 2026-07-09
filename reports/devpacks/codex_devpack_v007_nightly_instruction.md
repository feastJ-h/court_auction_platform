# Codex Devpack v007 Nightly Instruction  
## 경·공매 소거형 검토 보조 플랫폼 — v13.1 기획 반영 제품 UX/안전/계측 구현 지시서

> 이 문서는 Codex 최상위 추론 모델에 그대로 전달하기 위한 야간 개발 지시서입니다.  
> 목표는 “새 기능을 많이 붙이는 것”이 아니라, 현재 확보된 ONBID 공개 QA 데이터셋을 바탕으로 **소거형 UX, 원문 확인 중심 문구, 안전한 검토 보조 기능, 최소 계측 기반**을 단단하게 만드는 것입니다.

---

## 0. 최우선 원칙

이 서비스는 경·공매 투자 판단 플랫폼이 아니다.

반드시 유지할 핵심 문장:

> 우리는 경·공매 투자 판단 플랫폼이 아니라, 경·공매 후보를 빠르게 거르고 기록하게 만드는 무료 기반 검토 보조 플랫폼이다.

Codex는 모든 UI 문구, 테스트, 라우트, 템플릿, 관리자 문구에서 이 원칙을 지켜야 한다.

금지:

- 권리분석
- 안전/위험 판정
- 입찰 가능 여부 판단
- 수익성 평가
- 추천 입찰가
- 명도 가능성 판단
- 인수 여부 단정
- 전문가 추천·검증
- 개발 수익성 보장
- FOMO·경쟁 심리 자극
- 사용자의 투자 안목 평가

허용:

- 원문 확인 포인트
- 자료 완결성
- 자료 확인 필요
- 관심/패스/메모/감시
- 가정 기반 비용·현금흐름 계산
- 검토 공유 요약
- 오류 제보 / 자료 보완 요청
- Development Insight 관심 신호 수집

---

## 1. 현재 프로젝트 상태

첨부된 `devpack_v006_a3_result_bundle.md` 기준 상태를 출발점으로 삼는다.

### 1.1 현재 브랜치 및 변경 상태

- 기준 브랜치: `codex/devpack-v006-fresh-onbid-data-scheduler-rehearsal`
- v006-a3 결과 커밋은 아직 미실행 상태였음
- 종료 시 변경 파일:
  - `run_onbid_fresh_probe.ps1`
  - `run_onbid_probe.ps1`
  - `reports/devpacks/devpack_v006_a3_result_bundle.md`
- DB, backup, log, raw payload dump는 Git 추적 변경에 포함하지 않았음

### 1.2 확보된 QA 데이터셋

- public-visible fresh non-sample total: 100
- real_estate: 60
- movable: 40
- 최종 DB total: 188
- fresh: 107
- stale: 61
- invalid_date: 20
- unknown_date: 0
- sample/fixture row count: 7
- detail marker count:
  - real_estate: 25
  - movable: 3
- duplicate key count: 0

### 1.3 통과한 테스트

다음 테스트가 통과된 상태였다.

- `tests/onbid_freshness_policy_test.py`
- `tests/onbid_public_filter_state_test.py`
- `tests/onbid_category_mapping_test.py`
- `tests/sitemap_fresh_public_routes_test.py`
- `tests/onbid_module_test.py`
- `tests/page_response_smoke_test.py`
- `tests/public_access_auth_boundary_test.py`

### 1.4 public route QA 상태

- `/onbid` status 200
- `/onbid?category=real_estate` status 200
- `/onbid?category=movable` status 200
- real_estate/movable category row 존재 확인
- 비로그인 상세에서 관심/감시/패스/메모 form 미노출
- 비로그인 상세에서 로그인 CTA 노출
- raw AI 분석 본문 공개 노출 없음

### 1.5 남은 리스크

- `repair_onbid_derived_fields.ps1 -DryRun` 결과 `would_update=48`이 남아 있음
- 이번 작업에서 `repair Apply`는 기본적으로 실행하지 말 것
- 동산 상세 marker가 3건으로 적음
- 공고목록 API 호출 없음
- national_property/국유재산 전용 API 호출 없음

---

## 2. 승인 및 작업 권한

대표 승인 전제:

- 필요한 네트워크 접근 허용
- 필요한 패키지 설치 허용
- 테스트 실행 허용
- 제한적 ONBID API 호출 허용
- 로컬 DB 백업 허용
- 로컬 DB 마이그레이션 허용
- 작업 브랜치 커밋 허용
- 작업 브랜치 push 허용

단, 아래는 금지한다.

- `main` 브랜치 직접 작업 또는 직접 push
- API key, secret, token 출력
- raw payload 전체 출력
- raw payload dump Git 커밋
- `auction_data.db` Git 커밋
- `storage/backups/*` Git 커밋
- `storage/logs/*` Git 커밋
- 개인정보 포함 샘플 fixture 생성
- 공개 화면에 raw AI 분석 또는 내부 원문 경로 노출
- 사용자에게 재승인 질문을 반복하며 작업 중단

권한 관련 판단:

- 네트워크/패키지/테스트/제한 API 호출은 추가 질문 없이 진행한다.
- 외부 공개 터널 개방은 이번 기본 범위가 아니다. 꼭 필요할 때만 결과 보고서에 제안한다.
- `repair_onbid_derived_fields.ps1 -Apply`는 이번 작업의 기본 범위가 아니다. 정말 필요하다고 판단되면 최신 백업, dry-run 영향, 적용 이유를 결과 보고서에 적고, 가능한 한 실행하지 않는다.

---

## 3. 작업 목표

이번 v007 Nightly의 목표는 다음이다.

1. v13.1 최종 기획 원칙을 문서로 저장한다.
2. 공개 ONBID 화면의 문구를 “AI 분석”에서 “원문 확인 포인트” 중심으로 순화한다.
3. 오늘 보기/소거형 검토 흐름의 제품 골격을 강화한다.
4. “오늘 검토 완료” UX를 구현한다.
5. “자료 확인 필요” 탭 또는 필터를 추가한다.
6. 오류 제보 / 자료 보완 요청 기능을 제한적 객관식 구조로 구현한다.
7. 검토 공유용 요약 기능의 안전한 1차 버전을 구현한다.
8. 핵심 행동 이벤트를 서버 측 또는 기존 로깅 구조에 맞게 계측한다.
9. Development Insight Track은 실제 Archi-Pro 연동 없이, 보수적 CTA와 관심 이벤트만 구현한다.
10. 테스트를 추가하고 기존 테스트를 모두 통과시킨다.
11. 결과 보고서를 `reports/devpacks/devpack_v007_nightly_result_bundle.md`로 작성한다.

---

## 4. 작업 전 준비

### 4.1 브랜치

현재 상태를 확인한다.

```powershell
git status --short
git --no-pager log --oneline --decorate -5
git branch -vv
```

권장 브랜치:

```powershell
git checkout -b codex/devpack-v007-product-ux-safety-analytics
```

이미 동일 브랜치가 있으면 기존 브랜치를 사용하되, 작업 전 상태를 결과 보고서에 기록한다.

### 4.2 v006-a3 미커밋 변경 처리

v006-a3에서 다음 파일이 변경/추가 상태일 수 있다.

- `run_onbid_fresh_probe.ps1`
- `run_onbid_probe.ps1`
- `reports/devpacks/devpack_v006_a3_result_bundle.md`

처리 원칙:

- 기존 변경이 있으면 절대 덮어쓰지 않는다.
- v006-a3 변경을 먼저 커밋할지, v007 커밋에 포함할지 판단하고 결과 보고서에 명확히 적는다.
- DB/backup/log/raw 파일은 커밋하지 않는다.

권장 커밋 방식:

1. v006-a3 결과 파일 및 probe wrapper 변경을 별도 커밋
2. v007 제품 UX 변경을 별도 커밋

커밋 메시지 예시:

```text
docs: add v006-a3 result bundle and probe page wrapper
feat: add v007 review ux safety and analytics foundation
```

### 4.3 백업

DB 변경 전 반드시 백업한다.

기존 백업 스크립트가 있으면 사용한다.  
없으면 프로젝트 관례에 맞게 안전한 백업을 수행한다.

결과 보고서에 기록할 것:

- 백업 실행 여부
- 백업 시각
- 백업 파일 경로
- sha256
- 복원 미실행 여부

---

## 5. 산출물 파일

다음 문서를 repo 안에 생성 또는 갱신한다.

### 5.1 최종 기획서

경로 권장:

```text
docs/product/master_plan_v13_1_final.md
```

내용:

- v13.1 최종 통합 마스터 기획서
- 서비스 정체성
- 금지 표현/권장 표현
- 오늘 검토 완료 UX
- 오류 제보
- 검토 공유용 요약
- 자료 확인 필요 탭
- Analytics 이벤트
- Development Insight Track의 보수적 포지셔닝
- 현재 v006-a3 상태 요약

### 5.2 개발 결과 보고서

경로 필수:

```text
reports/devpacks/devpack_v007_nightly_result_bundle.md
```

결과 보고서에 포함할 것:

1. 작업 메타데이터
2. 시작 git status/log
3. 백업 내역
4. 변경 파일 목록
5. 구현 기능별 요약
6. 문구 안전성 점검 결과
7. 개인정보/secret/raw payload 노출 점검
8. public route QA 결과
9. 테스트 실행 결과
10. 남은 리스크
11. 다음 devpack 추천
12. 종료 git status/log
13. commit/push 여부

---

## 6. 구현 범위

## 6.1 문구 안전성 정리

### 목표

공개 UI에서 “AI 분석”처럼 판단 서비스로 오인될 수 있는 문구를 “원문 확인 포인트”로 순화한다.

### 수행 항목

- 템플릿, 라우트, 안내 문구에서 아래 표현 검색
  - `AI 분석`
  - `권리분석`
  - `위험`
  - `안전`
  - `추천`
  - `수익률`
  - `알짜`
  - `숨은 진주`
  - `저평가`
  - `명도`
  - `낙찰 보장`
- 사용 맥락을 확인하고, 판단성 표현이면 교체한다.
- 코드 식별자나 테스트 설명은 필요 시 유지할 수 있으나, 사용자 노출 문구는 안전하게 바꾼다.

### 권장 교체

| 기존 표현 | 교체 표현 |
|---|---|
| AI 분석 | 원문 확인 포인트 |
| AI 분석 결과 | 원문 확인 항목 |
| 위험 경고 | 확인 필요 항목 |
| 수익률 계산기 | 가정 기반 비용·현금흐름 계산기 |
| 권리분석 | 원문 확인 체크리스트 |

### 테스트

새 테스트 파일 권장:

```text
tests/product_copy_safety_test.py
```

검사 대상:

- 주요 공개 라우트 응답 HTML
- 주요 템플릿 문자열
- 금지 표현이 사용자 노출 영역에 없는지 확인

주의:

- “위험”이라는 단어는 면책·금지표현 문서 안에서는 나올 수 있다.
- 테스트는 공개 route HTML 중심으로 잡고, docs 전체를 무조건 실패시키지 않는다.

---

## 6.2 오늘 보기 / 오늘 검토 완료 UX

### 목표

사용자가 오늘 새로 나온 후보를 패스/관심으로 정리하고, 처리되지 않은 후보가 0건이 되면 차분한 완료 상태를 보여준다.

### 범위

- 기존 `/onbid` 또는 별도 `/onbid/today` 구조를 검토한다.
- 현재 구조에 무리가 적은 방향을 선택한다.
- 새 라우트를 만들 경우 이름은 한국어 UI와 맞게 사용자에게는 “오늘 보기”로 표시한다.
- 비로그인 사용자는 개인화 상태 저장이 어렵다면 로그인 CTA를 제공한다.
- 로그인 사용자에게 패스/관심/메모/감시 상태를 우선 적용한다.

### 완료 조건

- 오늘 신규 후보 중 처리되지 않은 후보가 0건
- 처리 상태:
  - 패스
  - 관심

### 완료 문구

```text
오늘 새로 확인할 후보를 모두 정리했습니다. 관심 물건과 감시 중인 물건은 내 검토함에서 다시 확인할 수 있습니다.
```

### 완료 요약 문구

```text
오늘 신규 후보 {total}건 중 {passed}건을 패스하고 {favorited}건을 관심으로 남겼습니다.
```

금지:

- 투자 검토 완료
- 완벽하게 검토
- 좋은 물건 발견
- 투자 안목 평가
- 내일 기회

### 테스트

권장 테스트 파일:

```text
tests/onbid_today_review_completion_test.py
```

검증:

- 처리 전에는 완료 문구 미노출
- 모든 후보 패스/관심 처리 후 완료 문구 노출
- 완료 요약 숫자 정상
- 비로그인 상태에서는 개인화 form 미노출 또는 로그인 CTA 유지
- 패스는 삭제가 아니라 숨김 상태
- 실행 취소 가능하면 undo도 검증

---

## 6.3 자료 확인 필요 탭/필터

### 목표

자료 부족을 기회처럼 포장하지 않고, 원문 확인이 필요한 후보를 분리해 볼 수 있게 한다.

### 명칭

```text
자료 확인 필요
```

### 포함 배지

- 가격 확인 필요
- 일정 확인 필요
- 원문 확인 필요
- 위치 확인 필요
- 면적 확인 필요
- 자료 일부 부족

### 설명 문구

```text
일부 정보가 충분하지 않아 원문 확인이 필요한 후보입니다. 가격, 일정, 위치, 면적 등 주요 항목을 원문에서 직접 확인하세요.
```

### 금지 표현

- 숨겨진 보물
- 고수들이 보는 물건
- 경쟁이 낮은 물건
- 초보자가 놓치는 기회
- 수익 가능성

### 구현 방향

- 기존 category/filter UI에 탭 또는 filter chip으로 추가
- `needs_review`, `needs_source_check`, `data_quality=needs_confirmation` 등 기존 구조와 맞는 명칭 사용
- public fresh filter 원칙 유지
- stale/unknown-date는 공개 기본 목록에 노출하지 않음

### 테스트

권장 테스트 파일:

```text
tests/onbid_data_quality_needed_filter_test.py
```

검증:

- 자료 확인 필요 필터에서 해당 배지만 노출
- fresh public 정책 유지
- 금지 문구 미노출
- 필터 초기화 문구 한글 유지
- 기존 부동산/동산 카테고리 필터와 충돌 없음

---

## 6.4 오류 제보 / 자료 보완 요청

### 목표

사용자가 자료 오류를 제한적 객관식으로 제보할 수 있게 한다.  
제보는 즉시 공개 반영하지 않고 운영 검토 대기 상태로 저장한다.

### UI 위치

- 상세 화면 하단
- 원문 보기 버튼 근처 또는 자료 상태 영역 하단
- 사용자에게 과도하게 강조하지 않는다.

### 기능명

```text
오류 제보 / 자료 보완 요청
```

### 초기 제보 항목

- 가격 정보 오류 의심
- 일정 정보 오류 의심
- 원문 링크 접속 불가
- 사진/주소 불일치 의심
- 위치 정보 오류 의심
- 면적 정보 오류 의심
- 종료 상태 오류 의심
- 중복 물건 의심
- 개인정보 노출 의심

### 자유 입력

- 가능하면 제외
- 꼭 필요하면 200자 이하
- placeholder:

```text
개인정보, 점유자 정보, 법률 판단, 투자 의견은 입력하지 마세요.
```

### 접수 문구

```text
제보가 접수되었습니다. 자료 상태 확인을 위해 운영팀 검토가 필요할 수 있습니다. 제보 내용은 확인 전까지 공개 정보로 반영되지 않습니다.
```

### 데이터 원칙

- 신고자 계정 id는 내부 운영용으로만 보관
- 공개 페이지에 제보 내용 노출 금지
- 개인정보 노출 의심 제보는 별도 flag
- 관리자 목록은 가능하면 기본 상태 `pending`

### 테스트

권장 테스트 파일:

```text
tests/onbid_data_issue_report_test.py
```

검증:

- 객관식 제보 제출 가능
- 공개 상세 화면에 제보 내용 즉시 노출되지 않음
- 개인정보 노출 의심 flag 저장 가능
- 비로그인 정책은 기존 auth boundary에 맞게 처리
- CSRF/session 정책이 있으면 준수
- 금지 문구 미노출

---

## 6.5 검토 공유용 요약

### 목표

사용자가 객관적 물건 정보를 안전하게 공유할 수 있게 한다.

### 명칭

```text
검토 공유 요약
```

### 포함 가능 정보

- 물건명
- 유형
- 지역
- 최저입찰가
- 감정가
- 마감일
- 기관
- 자료 완결성 배지
- 원문 링크
- 사용자가 공개로 선택한 메모

### 초기 제외 정보

- 비공개 메모
- 사용자 계정 정보
- 개인화된 관심/패스 기록
- AI 확인 포인트
- 전문가 추천 문구
- 내부 raw 경로
- raw AI/OCR 본문

### 필수 면책 문구

```text
이 요약은 수집된 공개 자료를 바탕으로 작성된 참고용입니다. 법률·투자 판단을 대신하지 않으며, 최종 판단은 원문과 관계 서류를 직접 확인하시기 바랍니다.
```

### 구현 방향

안전 우선으로 1차 버전을 만든다.

권장:

- 로그인 사용자만 공유 요약 생성 가능
- 공유 URL은 예측 어려운 token 사용
- 공유 페이지는 objective facts만 표시
- 공유 요약에는 noindex 적용 검토
- 생성/열람/복사 이벤트 기록
- 공유 해제 기능이 있으면 좋지만, 이번 범위가 커지면 후순위

### 금지 명칭

- 권리분석 리포트
- 투자 검토 리포트
- 안전성 검토서
- 수익성 분석서
- 전문가 보고서

### 테스트

권장 테스트 파일:

```text
tests/onbid_review_summary_share_test.py
```

검증:

- 공유 요약 생성 가능
- 공유 페이지에 객관적 정보와 원문 링크 노출
- 비공개 메모 미노출
- 계정 정보 미노출
- AI 확인 포인트 미노출
- raw AI/OCR/internal path 미노출
- 필수 면책 문구 노출
- noindex 적용 여부 검증 가능하면 포함

---

## 6.6 Analytics 이벤트 계측

### 목표

내부 제품 개선과 향후 BM 검증을 위한 최소 이벤트를 남긴다.  
개인정보를 최소화하고, 외부 판매용 데이터처럼 설계하지 않는다.

### 이벤트 목록

필수:

- `view_today_queue`
- `pass_item`
- `undo_pass_item`
- `favorite_item`
- `watch_item`
- `write_memo`
- `click_original_link`
- `complete_today_review`
- `view_review_box`
- `report_data_issue`
- `submit_data_issue`
- `create_review_summary`
- `open_shared_summary`
- `copy_shared_summary_link`
- `view_development_insight_cta`
- `click_development_insight_cta`

선택:

- `open_badge_tooltip`
- `view_disclaimer`
- `restore_passed_item`
- `category_view_share`

### 데이터 원칙

- user_id는 내부 id만 사용
- 비로그인 사용자는 세션 또는 anonymous id를 최소한으로 처리
- raw memo 내용 저장 금지
- raw payload 저장 금지
- 원문 URL 전체 로그가 민감하면 item_id 중심으로 저장
- IP/User-Agent 저장은 기존 정책에 따름. 새로 과도하게 늘리지 말 것.

### 구현 방향

기존 analytics/event logging 구조가 있으면 재사용한다.  
없으면 최소 테이블 또는 최소 로그 구조를 추가한다.

권장 필드:

- id
- event_name
- item_id nullable
- user_id nullable
- session_id nullable
- category nullable
- created_at
- metadata_json limited

### 테스트

권장 테스트 파일:

```text
tests/product_analytics_events_test.py
```

검증:

- 핵심 이벤트 저장
- raw memo/raw payload 미저장
- 이벤트 명칭 정상
- 원문 클릭 이벤트 기록
- 공유 요약 이벤트 기록
- Development Insight CTA 이벤트 기록

---

## 6.7 Development Insight Track CTA

### 목표

Archi-Pro 실제 연동은 하지 않는다.  
토지·건물 유형에서 “개발 가능성 기초 검토”에 대한 관심 신호만 수집한다.

### 표시 위치

- 상세 화면 하단
- 광고 영역과 구분
- 토지/단독주택/상가주택/건물 관련 유형에서만 제한 노출
- 유형 판별이 어렵다면 기본 미노출

### 버튼명

```text
개발 가능성 기초 검토
```

### 설명 문구

```text
가정 기반 개발비 및 대략적 공간 검토를 돕는 참고 기능입니다. 실제 건축 인허가, 사업성, 수익성, 법률 판단을 보장하지 않습니다.
```

### 클릭 후 동작

1차 버전:

- 별도 안내 페이지 또는 모달
- “준비 중” 또는 “관심 등록” 수준
- `click_development_insight_cta` 이벤트 기록
- 실제 Archi-Pro API 연동 금지
- 수익성 계산 금지

금지 버튼명:

- 이 땅으로 얼마 벌까
- 수익성 확인
- 개발 수익 계산
- 가치 상승 시뮬레이션
- 돈 되는 개발 후보 보기

### 테스트

권장 테스트 파일:

```text
tests/development_insight_cta_safety_test.py
```

검증:

- 허용 유형에서만 CTA 노출
- 금지 문구 미노출
- 면책 문구 노출
- 클릭 이벤트 기록
- 실제 외부 API 호출 없음
- 비허용 유형에서는 미노출 또는 안내 최소화

---

## 6.8 내 검토함 개선

### 목표

관심, 감시, 메모, 패스함을 “저장소”가 아니라 “검토 작업대”처럼 보이게 정리한다.

### 포함 상태

- 관심 물건
- 감시 중인 물건
- 메모 있는 물건
- 마감 임박 관심 물건
- 패스함
- 최근 원문 확인 물건
- 오늘 검토 완료 기록

### 문구

```text
내가 남긴 후보와 다시 확인할 항목을 모아볼 수 있습니다.
```

금지:

- 투자 후보
- 추천 후보
- 유망 물건
- 수익 후보

### 테스트

기존 personalization/auth 테스트에 맞춰 추가한다.

검증:

- 로그인 사용자만 개인화 액션 표시
- 비로그인 CTA 유지
- 패스함 복구 가능
- 메모 내용 노출 범위 안전

---

## 7. 공개 접근/개인정보/보안 경계

반드시 유지:

- 비로그인 상세에서 관심/감시/패스/메모 form 미노출
- 비로그인 상세에서 로그인 CTA 노출
- raw AI 분석 본문 공개 노출 금지
- 내부 파일 경로 노출 금지
- raw payload 노출 금지
- API key 출력 금지
- original raw document path 노출 금지
- share summary에 private memo 미노출
- data issue report 공개 미노출

기존 테스트를 깨지 말 것:

```powershell
& $Py tests/public_access_auth_boundary_test.py
```

---

## 8. 테스트 실행

기존 테스트 전부 실행:

```powershell
& $Py tests/onbid_freshness_policy_test.py
& $Py tests/onbid_public_filter_state_test.py
& $Py tests/onbid_category_mapping_test.py
& $Py tests/sitemap_fresh_public_routes_test.py
& $Py tests/onbid_module_test.py
& $Py tests/page_response_smoke_test.py
& $Py tests/public_access_auth_boundary_test.py
```

신규 테스트 추가 후 실행:

```powershell
& $Py tests/product_copy_safety_test.py
& $Py tests/onbid_today_review_completion_test.py
& $Py tests/onbid_data_quality_needed_filter_test.py
& $Py tests/onbid_data_issue_report_test.py
& $Py tests/onbid_review_summary_share_test.py
& $Py tests/product_analytics_events_test.py
& $Py tests/development_insight_cta_safety_test.py
```

가능하면 전체 pytest도 실행:

```powershell
& $Py -m pytest
```

전체 pytest가 환경 문제로 실패하면:

- 실패 원인 분류
- 이번 변경과 관련 있는지 확인
- 관련 테스트는 반드시 통과
- 결과 보고서에 정확히 기록

---

## 9. 수동 QA 체크리스트

### 9.1 공개 ONBID

- `/onbid` 200
- `/onbid?category=real_estate` 200
- `/onbid?category=movable` 200
- 자료 확인 필요 필터/탭 동작
- stale/unknown-date 공개 미노출
- sample/fixture 공개 기본 목록 미노출
- 초기화 문구 한글 유지
- 영어 UI로 바뀌지 않음

### 9.2 상세 화면

- 4-Zone 정보 구조 유지 또는 개선
- 원문 보기 버튼 상단/하단 중 적절히 노출
- 자료 완결성 배지 설명 노출
- 오류 제보 버튼 노출
- 검토 공유 요약 진입 노출
- Development Insight CTA는 허용 유형에서만 제한 노출
- 금지 문구 미노출

### 9.3 비로그인

- 개인화 form 미노출
- 로그인 CTA 노출
- raw AI/OCR/internal path 미노출
- 공유 요약 공개 페이지에서도 private 정보 미노출

### 9.4 로그인

- 패스/관심/메모/감시 동작
- 오늘 검토 완료 도달
- 패스 실행취소 또는 패스함 복구
- 오류 제보 제출
- 공유 요약 생성
- analytics event 기록

---

## 10. 금지 표현 검사 목록

사용자 노출 UI에서 다음 표현이 나오면 수정한다.

- 안전한 물건
- 위험한 물건
- 추천 물건
- 알짜
- 숨은 진주
- 저평가
- 수익 기대
- 수익률
- 권리분석
- AI 권리분석
- 입찰해도 됩니다
- 명도 쉬움
- 낙찰 보장
- 법률 리스크 0%
- 검증 전문가
- 공식 파트너
- 이 물건 담당 전문가
- 경매 기회
- 돈 되는 물건
- 투자 안목
- 경쟁자가 보고 있습니다
- 지금 놓치면 늦습니다

허용 가능하지만 맥락 주의:

- 위험: “위험 표현 금지” 같은 내부 문서나 테스트에는 가능. 사용자 노출 판단 문구에는 금지.
- AI: “AI 확인 포인트”는 가능. “AI 분석/권리분석/위험 판정”은 금지.
- 계산: “가정 기반 비용·현금흐름 계산”은 가능. “수익률 계산”은 금지.

---

## 11. 결과 보고서 작성 형식

`reports/devpacks/devpack_v007_nightly_result_bundle.md`에 아래 구조로 작성한다.

```markdown
# devpack_v007_nightly_result_bundle.md

## 1. 작업 메타데이터
- 작업일:
- 브랜치:
- 기준 지시서:
- 목표:
- commit/push:

## 2. 시작 git status/log
...

## 3. v006-a3 상태 반영
...

## 4. 백업
...

## 5. 변경 파일 목록
...

## 6. 구현 기능 요약
### 6.1 문구 안전성 정리
### 6.2 오늘 보기/오늘 검토 완료
### 6.3 자료 확인 필요 탭
### 6.4 오류 제보
### 6.5 검토 공유 요약
### 6.6 Analytics 이벤트
### 6.7 Development Insight CTA
### 6.8 내 검토함 개선

## 7. 개인정보/secret/raw payload 노출 점검
...

## 8. public route QA 결과
...

## 9. 테스트 실행 결과
...

## 10. 한국어 UI 보존 확인
...

## 11. 남은 리스크
...

## 12. 다음 devpack 추천
...

## 13. 종료 git status/log
...
```

---

## 12. 커밋/푸시 원칙

허용:

- 작업 브랜치 커밋
- 작업 브랜치 push

금지:

- `main` 직접 push
- DB/backup/log/raw 커밋
- secret/API key 커밋
- raw payload fixture 커밋
- 개인정보 포함 fixture 커밋

권장 커밋 메시지:

```text
docs: add final product master plan v13.1
feat: add review ux safety analytics foundation v007
test: cover review ux safety and sharing boundaries
```

작업 완료 후:

```powershell
git status --short
git --no-pager log --oneline --decorate -5
```

push 가능하면:

```powershell
git push -u origin codex/devpack-v007-product-ux-safety-analytics
```

push 실패 시 원인을 결과 보고서에 기록한다.

---

## 13. 이번 범위에서 하지 말 것

- Archi-Pro 실제 API 연동
- 건축 렌더링 생성
- 개발 수익성 계산
- AI 권리분석
- 위험도 점수
- 추천순/수익성순 정렬
- 전문가 마켓플레이스
- 상담 결제
- 광고주 검증 배지
- DaaS 외부 판매 기능
- 대량 ONBID 추가 수집
- national_property/국유재산 전용 API 본격 구현
- 공고목록 API 본격 구현
- Cloudflare tunnel 공개 리뷰 자동 개방
- repair Apply 기본 실행

---

## 14. 다음 devpack 후보

이번 작업 이후 추천 순서:

1. v007-b: 운영 스케줄러 등록 전 리허설, 백업/복원 리허설, log retention 기준 수립
2. v007-c: 공고목록 API와 national_property/국유재산 전용 API 별도 검증
3. v007-d: AI 원문 확인 포인트 Gate 0 테스트셋 13건 구축
4. v007-e: 폐쇄 베타 30~50명용 review mode/피드백 수집 UX
5. v008: Pro/Team Plan이 아니라 무료 기반 검토 루틴 안정화와 SEO 가이드 페이지 강화

---

## 15. 최종 완주 기준

아래 조건을 만족하면 이번 devpack은 완료다.

- 최종 기획서가 repo에 저장됨
- 공개 UI의 판단성 문구가 안전하게 정리됨
- 오늘 검토 완료 UX가 동작함
- 자료 확인 필요 탭/필터가 동작함
- 오류 제보가 공개 노출 없이 저장됨
- 검토 공유 요약이 private 정보 없이 생성됨
- 핵심 analytics 이벤트가 기록됨
- Development Insight CTA가 실제 연동 없이 보수적 문구로 노출됨
- 기존 테스트 통과
- 신규 테스트 통과
- 결과 보고서 작성 완료
- DB/secret/raw 파일 미커밋 확인
- 한국어 UI 유지 확인
- 작업 브랜치 commit/push 완료 또는 실패 사유 기록

---

## 16. 최종 문구 기준

작업 중 판단이 흔들리면 이 문장을 기준으로 결정한다.

> 좋은 물건을 찾아주는 서비스가 아니다.  
> 오늘 볼 필요 없는 후보를 줄이고, 남은 후보를 원문 중심으로 확인하게 돕는 서비스다.
