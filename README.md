# 2026 도쿄 여행 숙소 후보

2026-11-05 ~ 11-09 (4박), 성인 4명, 4박 총액 120만원 이하, 객실 30㎡ 이상(면적 미기재 포함), 호텔 제외(아파트형) 숙소를 Agoda·Airbnb에서 수집해 비교한 자료입니다.

- 슬라이드: `index.html` (GitHub Pages로 호스팅, 이미지는 `images/`)
- 원본 데이터: `tokyo_candidates.json` (침실 수 `bedrooms`, 객실 면적 `area_m2`, 사진 `photos`/`photos_local` 포함)
- 2차 수집 원본값: `collected_v2.py` (사진 경로·침실 수)
- 수집 시점: 2026-10-01 (가격·잔여 객실은 이후 바뀔 수 있음)

## 다시 만들기

```bash
python3 build_data.py     # tokyo_candidates.json 보정·거리 계산·사진 저장(images/)
python3 build_slides.py   # slides_template.html + 데이터 -> index.html
```

- `build_data.py`의 사진 저장은 macOS `sips`를 사용합니다.
- 위치 구분: 시부야·신주쿠역 직선 3km 이내 = 번화가권, 그 외 이케부쿠로역 2.5km 이내 = 이케부쿠로권.
- Airbnb 위치는 공개된 대략 위치, Agoda는 가장 가까운 역 좌표로 근사한 값입니다.
- 침실 수: 0 = 스튜디오/원룸, null = 호스트 미공개. 사진은 숙소당 최대 12장(가로 800px)을 `images/`에 저장하고 슬라이드 안에서 넘겨볼 수 있습니다.
- 사진은 각 사이트에서 가져온 것으로, 저작권은 각 호스트·플랫폼에 있습니다.
