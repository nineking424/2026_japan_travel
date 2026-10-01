# 도쿄 여행 숙소 후보 프로젝트

Agoda·Airbnb에서 도쿄 아파트형 숙소를 수집해 **HTML 슬라이드**(GitHub Pages)로 비교하는 프로젝트다.
저장소: https://github.com/nineking424/2026_japan_travel (main 루트를 Pages로 서빙)

## 현재 조건 (수정 시 `build_data.py` 상수와 슬라이드 문구를 함께 바꾼다)

- 일정 2026-11-05 ~ 11-09 (4박), 성인 4명, 호텔 제외(아파트·주택·스튜디오)
- 예산: 4박 총액 **1,200,000원 이하** (`BUDGET`)
- 객실 면적 **30㎡ 이상**, 면적 미기재는 유지 (`AREA_MIN`)
- 위치 구분: 시부야·신주쿠역 직선 3km 이내 = tier 1, 그 외 이케부쿠로역 2.5km 이내 = tier 2, 나머지 tier 0(본문 제외)
- 슬라이드 요구: 숙소별 사진 캐러셀(최대 12장), 지도(번화가까지 직선거리), 침실 수, 방 넓이

## 파일 구조와 파이프라인

```
collected_v2.py      브라우저로 뽑은 2차 수집 원본값(사진 경로, 침실 수)
build_data.py        1차 수집값 + 2차 값 병합 -> 좌표·거리·예산/면적 필터·사진 저장
tokyo_candidates.json  병합 결과(모든 후보 + exclude_reason)  ← 슬라이드의 유일한 데이터
slides_template.html 슬라이드 템플릿(데이터는 /*DATA*/null 자리에 주입)
build_slides.py      템플릿 + JSON -> index.html
index.html, images/  배포 산출물(images/는 build_data.py가 매번 지우고 다시 만든다)
public/              로컬 임시 서빙용 복사본(.gitignore)
```

재빌드: `python3 build_data.py && python3 build_slides.py` (macOS `sips` 필요)
배포: 커밋 후 `git push origin main` (사용자가 요청할 때만 커밋·푸시)

## 지켜야 할 규칙

- **데이터 변경은 JSON/수집 파일에**, 표시 변경은 `slides_template.html`에 한다. `index.html`을 직접 고치지 않는다.
- 수집값을 못 얻으면 `null`로 둔다(추측해서 채우지 않는다). 슬라이드는 null을 "미공개/미기재/미확인"으로 표시한다.
- 면적·도보 시간은 본문 정규식 추출이라 오탐이 있다. 확실하지 않으면 `null`로 두고 `conf`에 사유를 적는다.
- Agoda 가격은 목록의 **"1박당 총 금액"(세금 포함) × 4**, Airbnb는 상세 페이지의 **총액**을 쓴다. 기준이 다르므로 슬라이드 "가격 기준" 문구를 유지한다.
- 슬라이드 문구의 수치(거리·평점·후기 수)는 JSON 값과 일치해야 한다. 추천 카드(`pickCard`) 문구는 수동이므로 데이터가 바뀌면 다시 확인한다.
- 사진은 각 사이트 원본이므로 저작권 고지(README)를 유지한다.

## 검증 (완료 전에 반드시)

1. `node --check`로 index.html의 스크립트 문법 확인(스크립트를 임시 파일로 추출).
2. 헤드리스 Chrome 캡처: `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --window-size=1280,720 --virtual-time-budget=6000 --screenshot=out.png "file://$PWD/index.html#<슬라이드번호>"`
3. `--dump-dom` 결과에서 `undefined`/`NaN`/깨진 이미지 경로가 없는지 확인.

## 반복 수집 작업

새 후보를 수집하거나 조건(예산·면적·일정)을 바꿀 때는 `.claude/skills/stay-shortlist` 스킬을 따른다.
