# 인수인계 (2026-10-01 기준)

도쿄 4박(2026-11-05~09, 성인 4명) 숙소 후보를 HTML 슬라이드로 정리하는 작업. 새 세션은 `CLAUDE.md`와 `.claude/skills/stay-shortlist/`를 먼저 읽는다.

## 현재 상태

- 배포: https://nineking424.github.io/2026_japan_travel/ (Pages: main 루트, 빌드 완료)
- 조건: 4박 총액 120만원 이하, 객실 30㎡ 이상(미기재 유지), 호텔 제외
- 후보 31곳 본문(번화가권 17 · 이케부쿠로권 14), 제외 25곳(예산 초과 12 · 번화가에서 멂 7 · 면적 미달 6) — 총 56건이 `tokyo_candidates.json`에 있음
- 슬라이드 40장: 표지, 읽는 법, 상황별 추천, 전체 지도, 가중치 조절 순위표, 번화가권/이케부쿠로권 상세(사진 캐러셀·지도·침실·면적), 제외 후보 표, 예약 전 체크리스트
- 최종 산출물은 엑셀이 아니라 **HTML 슬라이드**(엑셀·총점 수식 계획은 폐기)

## 데이터 한계 (본문 31곳 기준)

- 방 넓이 미기재 17곳(주로 Airbnb), 침실 수 미공개 10곳(임대 호실형), 신뢰도 "낮음" 14곳
- Airbnb 위치는 공개된 대략 위치, Agoda는 가장 가까운 역 좌표로 근사(수백 m 오차)
- 면적·도보 시간은 본문 정규식 추출이라 일부 오탐 가능

## 열린 항목

1. **포함하지 못한 Agoda 후보**: Flora Maison Kamiochiai(1박 242,402원, 평점 8.0), Tokyo LX Home(Kameari 지역, 번화가 밖 가능성 큼). Agoda 목록의 지연 로딩 때문에 상세 주소를 못 읽었다. **사용자가 상세 URL을 주면** `stay-shortlist` 스킬 §2로 바로 수집한다.
2. 사용자가 "최대한 예외 없이 후보를 포함"하길 원한다. 새 후보 요청이 오면 제외 사유를 먼저 확인한다(예산·면적·거리).
3. 선택 사항: 최종 2~3곳 선정 후 같은 날짜로 재검색해 잔여·가격 갱신, Airbnb 미기재 면적은 호스트 문의.

## 다음 세션에서 하는 법

- 조건 변경(예산·면적·일정): CLAUDE.md "현재 조건", `build_data.py`의 `BUDGET`/`AREA_MIN`, 슬라이드 문구를 함께 수정 → `python3 build_data.py && python3 build_slides.py`
- 후보 추가: 스킬 §1~3(수집 → `collected_v2.py`/`build_data.py` 신규 블록 → 빌드)
- 슬라이드 문구: `slides_template.html`만 수정(`index.html` 직접 수정 금지). 추천 카드 문구는 수동이라 데이터 변경 시 재확인
- 배포: 사용자가 요청하면 커밋·푸시. 사진은 `images/`(약 31MB)

## 이번 세션에서 확인된 함정

- Agoda 목록은 JS 스크롤로 렌더링되지 않는다(실제 휠 입력 필요), 상세 주소는 추측하면 404
- Agoda `bstatic` 사진은 서명(`?k=`) 없이 401 → `images/`에 내려받은 사본 사용
- JS 도구 출력에 쿼리 문자열이 있으면 차단되고 45초 제한이 있다
- Bash의 `curl`이 훅에 막힐 수 있다 → 네트워크 확인은 `ctx_execute`(python) 사용
- 헤드리스 검증은 `/Applications/Google Chrome.app`을 직접 호출한다(CLAUDE.md 검증 절차)
- 상세는 스킬의 `references/browser-snippets.md` 참고

## 사용자 성향·작업 방침

- 한국어로 응답한다.
- 요구사항을 대화 중에 계속 추가·변경한다(엑셀→HTML 슬라이드, 예산 100만→120만원, 지도·사진·침실·면적 추가). 변경이 오면 조건 상수와 슬라이드 문구를 함께 고친다.
- "최대한 예외 없이 후보를 포함"이 명시된 방침이다. 후보를 뺄 때는 사유(예산·면적·거리)가 보이게 둔다(슬라이드 참고 표에 이미 있음).
- 커밋·푸시는 **사용자가 요청할 때만** 한다.
- 로컬 서버(8080)와 브라우저 탭은 모두 정리했고, 실행 중인 백그라운드 작업은 없다.

## 참조 위치

- 저장소: https://github.com/nineking424/2026_japan_travel (조건·파이프라인은 `CLAUDE.md`)
- 자동 메모리: `~/.claude/projects/-Users-nineking-workspace-work-20261001-japan-reservation/memory/project_tokyo_output_html_slides.md` (누적 조건 요약)

## 추천 스킬

- `stay-shortlist` — 후보 수집, 조건 변경, 슬라이드 재빌드·배포의 기본 절차(프로젝트 스킬)
- `anthropic-skills:chrome-browser` — Chrome 확장 도구 사용 전 규칙(도구 일괄 로드, 새 탭 사용, 대화상자 회피)
- `commit-commands:commit` — 사용자가 커밋을 요청했을 때(attribution 줄 포함)
- `mattpocock-skills:code-review` — 슬라이드·빌드 스크립트를 크게 바꾼 뒤 검토가 필요할 때(선택)
