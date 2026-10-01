---
name: stay-shortlist
description: Agoda·Airbnb에서 도쿄 아파트형 숙소를 조건(일정·인원·예산·면적)으로 수집하고, 침실·방 넓이·사진·좌표를 모아 HTML 슬라이드(사진 캐러셀, 지도)로 만들어 GitHub Pages에 배포한다. "숙소 후보 추가 수집", "예산/면적/일정 바꿔서 다시", "슬라이드 갱신" 요청에 사용.
---

# 숙소 후보 수집 → 슬라이드 갱신

이 프로젝트의 CLAUDE.md(파일 구조·조건·규칙)를 먼저 읽는다. 브라우저 추출 스크립트는 [references/browser-snippets.md](references/browser-snippets.md).

## 0. 준비

- Chrome 확장 도구(`mcp__claude-in-chrome__*`)를 한 번에 로드하고(`tabs_context_mcp` → 새 탭), 끝나면 만든 탭을 닫는다.
- 조건을 바꾸는 요청이면 CLAUDE.md의 "현재 조건"과 `build_data.py`의 `BUDGET`/`AREA_MIN`, 슬라이드 문구를 함께 수정한다. 일정·인원이 바뀌면 아래 URL 파라미터와 `price_basis` 문구도 바꾼다.
- 가격 상한은 총액 기준이다. 검색 필터는 **1박 기준**이라 `총액 ÷ 4`에 여유를 둔다.

## 1. 후보 찾기

**Airbnb** (`https://www.airbnb.co.kr/s/<Shibuya|Shinjuku>--Tokyo--Japan/homes?checkin=…&checkout=…&adults=4&price_min=…&price_max=<1박>&room_types%5B%5D=Entire%20home%2Fapt`)
- 카드의 `총액`이 4박 총액. 카드에 `11월 N일~M일` 날짜 라벨이 있으면 **다른 날짜 추천**이므로 제외한다.
- 페이지 이동 파라미터(`items_offset`)는 먹지 않는다. 가격 구간(`price_min/max`)과 지역을 바꿔가며 결과를 넓힌다.
- 카드 추출 스니펫: `references/browser-snippets.md` §A1.

**Agoda** (`https://www.agoda.com/ko-kr/search?city=5085&checkIn=…&los=4&adults=4&rooms=1&children=0&currencyCode=KRW&hotelAccom=29&hotelArea=28049,31077&sort=priceLowToHigh`)
- `hotelAccom=29` = 아파트 유형, `hotelArea=28049,31077` = 신주쿠+시부야(지역 체크박스를 한 번 눌러야 URL에 생긴다).
- 목록 가격은 두 개다: 큰 숫자는 세금 전, 작은 **"1박당 총 금액"이 세금 포함**. 총액 = 세금 포함 × 4. 정렬(`priceLowToHigh`)은 세금 전 가격 기준이다.
- **지연 로딩**: JS `scrollBy`로는 카드가 렌더링되지 않는다. `computer scroll`(실제 휠 입력) 10틱을 여러 번 한 뒤 추출한다. 49개씩 페이지가 나뉘며 "다음 페이지로" 버튼을 눌러 이동한다. 렌더링 전 카드는 `<a>`가 없어 링크를 못 읽는다.
- 상세 주소 형식은 `/ko-kr/<slug>/hotel/(all/)<지역>-jp.html`이라 **추측하면 404**가 난다. 목록에서 실제 href를 읽는다(스니펫 §B1). 웹 검색·텍스트 필터·홈 검색창은 불안정했다.

## 2. 상세 수집 (후보마다)

- **Airbnb 상세** `/rooms/<id>?check_in=…&check_out=…&adults=4`: 스니펫 §A2. 3.5초 대기 후 한 번에 추출한다. 침실 수·면적·좌표·사진·편의시설이 나온다.
  - 사진은 갤러리 조작 없이 페이지 `<script>` 안의 `a0.muscache.com/im/pictures/…/original/…` URL에서 모두 뽑는다(스크롤 로딩은 빈 칸이 된다). 숙소 ID를 포함한 디렉터리를 우선하고, `BnbProperty-…`는 건물 공통 사진일 수 있다.
  - `임대 호실`형(침실 수 없음)은 `bedrooms = null`(미공개). 원룸은 0.
  - 면적은 제목·설명 문구에서만 얻는다(없으면 null). 오탐이 잦으니(추천 목록 문구가 섞임) 본문 앞부분만 본다.
- **Agoda 상세**: 스니펫 §B2. 객실 면적(`m²`), 침실, 침대, 최대인원, 주방·세탁기, 취소 조건이 있다.
  - 사진: 첫 이미지를 클릭하면 갤러리가 로드된다. 주소 형식이 둘이다 — `pix*.agoda.net/hotelImages/<id>/0/<hash>.jpg`(서명 불필요)와 `q-xx.bstatic.com/…/<id>.jpg?k=<sig>&o=`(**서명 `k` 필수**, 없으면 401). 같은 페이지에 다른 숙소 이미지가 섞이니 첫 사진의 숙소 ID와 같은 것만 쓴다.
  - **좌표는 없다.** 가장 가까운 역 이름·거리(`○○역 280m`)를 읽고 역 좌표로 근사한다(Nominatim으로 확인, `build_data.py`의 `STATIONS`에 추가).
- JS 도구 출력에 쿼리 문자열(`?k=…`)이 있으면 `[BLOCKED: Cookie/query string data]`로 막힌다. `?`→`|`, `&o=` 제거처럼 치환해서 반환한다.
- JS 실행은 45초 제한이다. 대기 루프를 길게 돌리지 말고, 한 번 막히면 페이지를 새로 열어 다시 시도한다. 한 메시지에 `navigate` + `javascript_exec` 쌍을 최대 5개씩 묶는다.

## 3. 데이터 반영

1. 수집값을 `collected_v2.py`(사진·침실)와 `build_data.py`의 신규 후보 블록(`NEW_AIRBNB_V2`, `NEW_AGODA_V2`, 헬퍼 `A()`/`G()`)에 추가한다.
   - Airbnb 총액·평점(5점)·후기 수·위치 평점·슈퍼호스트·면적·도보·취소·편의시설·좌표를 `A()`에, Agoda는 세금 포함 1박 금액·평점(10점)·역·거리를 `G()`에 넣는다.
   - 못 읽은 값은 `None`. 편의시설이 `None`이면 슬라이드가 "?"로 표시한다.
2. `python3 build_data.py` — 출력의 `shown/excluded`, 사유별 개수, 후보 목록(거리·면적·침실·사진 수)을 확인한다. 목록 끝의 `ph`(저장된 사진 수)가 0이거나 예상보다 적은 후보는 사진 URL을 다시 확인한다.
3. 슬라이드의 **수동 문구**를 데이터와 맞춘다: `slides_template.html`의 `pickCard` 설명, "읽는 법" 카드, 체크리스트 카드.

## 4. 슬라이드 빌드·검증·배포

1. `python3 build_slides.py` → `index.html`
2. CLAUDE.md의 검증 3단계(문법, 캡처, DOM 검사)를 수행하고 상세/추천/지도/순위 슬라이드 캡처를 눈으로 확인한다. 캐러셀은 임시 복사본에 클릭 시나리오를 넣어 `--dump-dom`으로 검증할 수 있다.
3. 사용자가 요청하면 커밋·푸시(`index.html`, `images/`, `tokyo_candidates.json`, 스크립트). 커밋 메시지 끝에 시스템이 지정한 attribution을 붙인다. Pages는 main 루트에서 서빙된다.

## 알려진 함정 (실제로 겪은 것)

- Bash에서 `curl`이 훅에 막힐 수 있다 → 네트워크 확인은 `ctx_execute`(python)로 한다. 서버를 띄울 때는 `run_in_background`로 실행하고 종료는 `lsof -tiTCP:<포트>`로 PID를 찾아 `kill`.
- Airbnb 같은 숙소가 검색 가격대에 따라 다른 총액으로 보일 수 있다(방 유형 차이). **상세 페이지의 총액**을 기준으로 삼고 `conf`에 메모한다.
- 후기 수가 적은 숙소(1~10개)는 평점이 높아 보인다. 점수는 베이지안 보정을 하지만, 추천 문구에는 후기 수를 함께 적는다.
- 사진 URL을 슬라이드에 직접 링크하면 Agoda `bstatic`은 401이므로 항상 `images/`에 내려받은 사본을 쓴다.
- 이 세션에서 끝내 못 연 Agoda 후보: Flora Maison Kamiochiai(호수별 매물이라 주소 특정 실패), Tokyo LX Home(Kameari 지역, 번화가 밖). 필요하면 사용자에게 상세 URL을 받는다.
