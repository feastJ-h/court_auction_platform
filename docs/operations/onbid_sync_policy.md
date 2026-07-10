# ONBID sync policy

- 목록 증분 동기화는 보수적으로 하루 수회 이하에서 시작하고 API 정책·응답 헤더를 확인해 환경 변수/스케줄러에서 조정한다.
- 상세 보강은 제한된 batch, 정합성·충돌 감사와 정리는 매일 수행한다.
- 각 실행은 `onbid_sync_runs`에 fetched/inserted/updated/duplicates/stale/unknown과 정제된 오류만 기록한다. raw payload와 API key는 기록하지 않는다.
- 실패 실행은 기존 공개 데이터를 삭제하지 않는다. stale/unknown/sample은 공개하지 않으며 관리 화면에서 조사한다.
- 국유일반재산이 0건이어도 stale/unknown 데이터를 대체 공개하지 않고 정확한 empty state를 유지한다.
