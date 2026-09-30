"""수집 원본(브라우저 추출값)을 tokyo_candidates.json 에 병합하고,
좌표·번화가 거리·예산 여부를 계산한 뒤 사진을 images/ 에 저장한다.

- 예산: 4박 총액 1,000,000원 미만
- 위치 구분(tier): 시부야·신주쿠역 직선 3.0km 이내 = 1, 그 외 이케부쿠로역 2.5km 이내 = 2, 그 밖 = 0(슬라이드 본문 제외)
사용: python3 build_data.py   (재실행해도 같은 결과가 되도록 idempotent)
"""
import json, math, subprocess, re
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).parent
JSON_PATH = HERE / "tokyo_candidates.json"
IMG_DIR = HERE / "images"
BUDGET = 1_200_000   # 4박 총액 상한(이하 포함)
AREA_MIN = 30        # 이 값 미만의 객실 면적은 제외(미기재는 유지)

HUBS = {
    "shinjuku": ("신주쿠역", 35.6896, 139.7006),
    "shibuya": ("시부야역", 35.6580, 139.7016),
    "ikebukuro": ("이케부쿠로역", 35.7295, 139.7109),
}
# Agoda는 좌표를 제공하지 않아 '가장 가까운 역' 좌표로 근사한다 (Nominatim/OSM 조회 + 공지 좌표)
STATIONS = {
    "takadanobaba": (35.7126, 139.7039), "hatsudai": (35.6812, 139.6862),
    "shin-okubo": (35.7012, 139.7001), "okubo": (35.7010, 139.6973),
    "higashi-shinjuku": (35.6985, 139.7076), "wakamatsu-kawada": (35.6993, 139.7184),
    "ochiai-minami-nagasaki": (35.7232, 139.6836),
    "nishi-shinjuku-gochome": (35.6899, 139.6845), "shimo-ochiai": (35.7158, 139.6962),
}

def hav(a, b, c, d):
    r = 6371.0
    p1, p2 = math.radians(a), math.radians(c)
    dphi, dl = p2 - p1, math.radians(d - b)
    x = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(x))

# ---------- Airbnb 사진 경로 복원 ----------
def abnb_photo(tok):
    m = re.match(r"H~(.+?)~(.+)$", tok)
    if m:
        hid, fn = m.groups()
        return f"https://a0.muscache.com/im/pictures/hosting/Hosting-{quote(hid, safe='%')}/original/{fn}"
    return "https://a0.muscache.com/im/pictures/" + tok

def agoda_signed(pid, sig):
    return f"https://q-xx.bstatic.com/xdata/images/hotel/max1024x768/{pid}.jpg?k={sig}&o="

def agoda_pix(path):
    return "https://" + path

BN = "BnbProperty/BnbProperty-"
def bnb(pid, *files):
    return [f"{BN}{pid}/original/{f}" for f in files]

def abnb_url(i):
    return f"https://www.airbnb.co.kr/rooms/{i}?check_in=2026-11-05&check_out=2026-11-09&adults=4"

def agoda_url(slug):
    return f"https://www.agoda.com/ko-kr/{slug}?checkIn=2026-11-05&los=4&adults=4&rooms=1&currencyCode=KRW"

def A(i, name, district, typ, total, r5, rv, loc5, sup, bed, beds, bath, cap, area, walk, nearest, fc, cn,
      k, w, e, a, conf, hl, photos, ll):
    return dict(
        id=f"abnb-{i}", platform="Airbnb", name=name, district=district, type=typ, url=abnb_url(i),
        total_krw=total, price_basis="Airbnb 총액",
        rating10=None if r5 is None else round(r5 * 2, 2), reviews=rv,
        loc10=None if loc5 is None else round(loc5 * 2, 1), superhost=sup,
        bedrooms=bed, beds=beds, baths=bath, capacity=cap, area_m2=area,
        walk_min=walk, nearest=nearest, free_cancel=fc, cancel_note=cn,
        kitchen=k, washer=w, elevator=e, aircon=a, conf=conf, highlights=hl,
        photos=[abnb_photo(p) for p in photos], lat=ll[0], lng=ll[1], coord_basis="Airbnb 공개 좌표(대략)")

NEW_AIRBNB = [
    A("1521657166688497666", "오쿠보역 3분 · 신오쿠보 6분 (안단테)", "신주쿠구(오쿠보)", "임대 호실(아파트)", 918646,
      4.75, 466, 4.9, 1, None, None, None, None, None, 3, "오쿠보역", 1, "취소 수수료 없음(기한 미확인)",
      1, 1, 0, 1, "낮음(침실·침대 수 미공개, 4인 수용 불확실)", "후기 466개, 신오쿠보 코리아타운 인접",
      bnb("1715239735288988381", "0b5abf8d-d091-4fcb-a7c6-424706d80202.png", "517355b7-907e-4f54-bf1d-8a3a9abe70be.png",
          "24029e55-c606-4942-a15a-ec9cffd84acf.png", "81bc811e-47e9-4f5f-8713-96851790a6e0.png"), (35.703, 139.6968)),
    A("1420091743706906101", "신주쿠 7분 / 침대 3+이불 / 다다미 (나카노)", "나카노(나카노사카우에 인근)", "임대 호실(전체)", 817262,
      4.9, 59, 4.9, 0, 1, 3, 1, 6, 40, None, "미확인", 1, "10/6까지 무료 취소",
      1, 1, 0, 1, "중간(도보 시간 미확인)", "다다미 + 이불 추가, 프로젝터",
      ["H~U3RheVN1cHBseUxpc3Rpbmc6MTQyMDA5MTc0MzcwNjkwNjEwMQ==~c34ccc40-f5de-412c-9d31-0ffd9ebca837.jpeg",
       "H~U3RheVN1cHBseUxpc3Rpbmc6MTQyMDA5MTc0MzcwNjkwNjEwMQ==~2634c3ca-7c0e-45a1-8c95-7d651fdbc9b9.jpeg",
       "H~U3RheVN1cHBseUxpc3Rpbmc6MTQyMDA5MTc0MzcwNjkwNjEwMQ==~18f8b754-f2a8-4348-8c57-6a79eb1193b3.jpeg",
       "H~U3RheVN1cHBseUxpc3Rpbmc6MTQyMDA5MTc0MzcwNjkwNjEwMQ==~6b027e7e-a445-4d55-abff-b021345d5276.jpeg"], (35.6926, 139.67483)),
    A("32995306", "신주쿠 10분 / 원룸 40㎡ / 침대 3개 (나카노)", "나카노(히가시나카노 방면)", "임대 호실(전체, 원룸)", 892892,
      4.56, 82, 4.6, 1, 1, 3, 1, 6, 40, 5, "미확인", 1, "10/6까지 무료 취소",
      1, 1, 1, 1, "중간", "주방·세탁기 완비, 엘리베이터",
      ["H~32995306~5dadb56d-f12c-4387-a06b-2c21fb35ce6a.png", "H~32995306~ced52843-5a2a-467a-9e19-4a88aef5db98.png",
       "H~32995306~f3617450-0672-403a-bec5-da8c3677178a.png", "H~32995306~22a27dec-beb9-46b7-adb2-7c4eed8d501b.png"], (35.6886, 139.6687)),
    A("1010395870676802741", "넓은 48㎡ / 시부야 4분 / 산겐자야 / 건조기", "세타가야구(산겐자야)", "임대 호실(전체)", 916930,
      4.9, 114, 4.8, 1, 1, 5, None, 8, 48, 10, "산겐자야역(추정)", 1, "10/22까지 무료 취소, 오늘 결제 0원",
      1, 1, 1, 1, "중간(도보 시간 추정)", "48㎡, 건조기·엘리베이터, 아기 침대",
      ["miso/Hosting-1010395870676802741/original/38164594-7aa7-42e0-98f1-c3f7119630f3.jpeg",
       "H~U3RheVN1cHBseUxpc3Rpbmc6MTAxMDM5NTg3MDY3NjgwMjc0MQ%3D%3D~243e99a9-52da-434a-bc3a-14f9c466f377.jpeg",
       "H~U3RheVN1cHBseUxpc3Rpbmc6MTAxMDM5NTg3MDY3NjgwMjc0MQ%3D%3D~5ee42318-27ac-4d6a-8f2a-035c2e99b714.jpeg",
       "miso/Hosting-1010395870676802741/original/29decd83-32fc-49af-b6be-6b9aaeef18cc.jpeg"], (35.64188, 139.66118)),
    A("36161452", "이케부쿠로 근처 60㎡ 콘도 (침실 3)", "도시마구(이케부쿠로 서쪽)", "콘도(전체)", 901475,
      4.91, 140, 4.8, 1, 3, 6, 1, 6, 60, 5, "이케부쿠로 인근 역", 1, "10/6까지 무료 취소",
      1, 1, 0, 0, "높음(에어컨 미확인)", "60㎡ 침실 3개, 건조세탁기",
      ["H~36161452~5d4c0ab2-d564-4c53-aa3c-c36125f084ff.jpeg", "H~36161452~97bd58de-058c-4c92-bb1e-54e9f84c85f4.jpeg",
       "miso/Hosting-36161452/original/50e635dd-d21e-4ec5-82df-6d1c467dc0ee.jpeg",
       "H~36161452~499613a4-e450-47a6-8c82-d798f047ede0.jpeg"], (35.72442, 139.69088)),
    A("888280265840698383", "2층 주택 / 이케부쿠로역 도보 3분 / 6인", "도시마구(이케부쿠로)", "주택(전체, 원룸형)", 770761,
      4.96, 52, 5.0, 1, 0, 4, 1, 6, None, 3, "이케부쿠로역", 1, "10/6까지 무료 취소",
      1, 1, 0, 1, "높음", "원룸형, 침대 4개, 후기 52개 평점 4.96",
      ["H~888280265840698383~6da459ac-8336-4fb3-b3e8-7a1ad749d6ad.jpeg", "H~888280265840698383~62bbf10c-c469-4d22-a8ba-3f15bebdc2d1.jpeg",
       "H~888280265840698383~76c1b884-9311-4ec7-8933-594482a9d93d.jpeg", "H~888280265840698383~d1ec3674-16ee-413c-9afb-11c62f28f7a9.jpeg"], (35.73893, 139.68751)),
    A("1495279101318765417", "오츠카역 도보 5분 / 이케부쿠로 2분·신주쿠 12분", "도시마구(오츠카)", "임대 호실(전체)", 660489,
      4.85, 27, 4.9, 1, 1, 1, 1, 8, 45, 5, "오츠카역", 1, "10/6까지 무료 취소",
      1, 1, 0, 1, "낮음(침대 1개 표기, 4인 수용 확인 필요)", "8인 정원 표기, 45㎡",
      ["H~1495279101318765417~a8516caf-a97a-45be-ad25-25144581659c.jpeg", "H~1495279101318765417~ca96d2a2-7395-47c0-a487-a263f744476b.jpeg",
       "H~1495279101318765417~90c3c1d7-f127-4d56-8e35-d4dfa0735bb2.jpeg", "H~1495279101318765417~a328991f-f83b-4f9f-a027-479481676783.jpeg"], (35.72766, 139.72766)),
    A("1496167663164950212", "스가모 지장 상점가 (스가모역 도보 8분)", "도시마구(스가모)", "임대 호실(전체)", 652496,
      4.86, 22, 4.8, 0, 1, 4, 1, 6, None, 7, "스가모역", 1, "10/6까지 무료 취소",
      1, 1, 1, 1, "중간", "신규 리모델링, 야마노테선·미타선",
      ["H~1496167663164950212~81df0d99-bcb6-4333-ad29-20de93cf09a7.png", "H~1496167663164950212~bce7a8f2-f47f-457b-a90b-740147e3d87e.png",
       "H~1496167663164950212~cb24abe2-b768-4c18-8af9-990c8893df0e.png", "H~1496167663164950212~394b88b4-4329-4dce-8d20-41af8ae8d904.png"], (35.7369, 139.7328)),
    A("1253453006733532295", "다 하우스 이케부쿠로 (지하철 1분)", "도시마구(이케부쿠로)", "임대 호실(아파트)", 810472,
      4.84, 149, 4.8, 1, None, None, None, None, None, 5, "이케부쿠로역", 0, "무료 취소 문구 없음(확인 필요)",
      1, 1, 0, 1, "낮음(침실·침대 수 미공개)", "후기 149개, 이케부쿠로 중심",
      bnb("1715245279386924085", "ec697369-c1d8-4a9f-8d11-e39ca084a9a6.jpeg", "f78d29ae-ff2b-4d02-a9f1-6df33393d027.jpeg",
          "c89e27e1-07d1-4899-bc7d-cb179b477e06.jpeg", "c50d4d11-b9a9-4715-a77c-f2bff0c8ba7b.jpeg"), (35.7326, 139.7065)),
    A("1317943575670833222", "신주쿠·이케부쿠로 접근 좋은 4인실(최대 6)", "도시마구(이케부쿠로 북쪽)", "임대 호실(아파트)", 910922,
      4.84, 122, 4.7, 1, None, None, None, 6, None, 9, "미확인", 1, "취소 수수료 없음(기한 미확인)",
      1, 1, 0, 1, "낮음(침실·침대 수 미공개)", "조용한 주택가, 편의점 2분",
      bnb("1781598878906765382", "97062c18-7fdd-48ba-8d79-7a7f32b13c6a.jpeg", "358a2884-f1da-4b1f-8934-1d727d3b73a8.jpeg",
          "22a07fec-fb6c-4921-9198-c55ecab94a1c.jpeg", "c3dbcf2d-e481-421e-932b-8604719e8c48.jpeg"), (35.7435, 139.7093)),
    # 이하 4건은 위치 기준으로 본문에서 제외되지만 자료로 보관
    A("1335105007846893950", "요스케와 리사의 아파트 (신에고타역 도보 8분)", "나카노구(북부)", "임대 호실(아파트)", 771570,
      4.9, 215, 4.6, 1, None, None, None, None, None, 8, "신에고타역", 1, "취소 수수료 없음(기한 미확인)",
      1, 1, 1, 1, "낮음", "신주쿠에서 멀다", bnb("1715246134803336160", "77f2c67e-f09a-4c78-b37a-305d06df0ca6.jpeg",
          "3c7a9d1a-a75a-47b3-a79a-252ab9502593.jpeg"), (35.73033, 139.67694)),
    A("775623360105108661", "호난초역 도보 5분 (스기나미)", "스기나미구", "임대 호실", 828404,
      4.75, 77, 4.9, 0, None, None, None, None, None, 5, "호난초역", 1, "취소 수수료 없음(기한 미확인)",
      1, 1, 0, 1, "낮음", "신주쿠까지 마루노우치선", bnb("1715242994370524595", "87a86192-ced5-4dce-a5fe-c1d86c548cc0.jpeg",
          "d6d36e38-eaff-485a-8efc-5a3429a27a6b.jpeg"), (35.68236, 139.65419)),
    A("1649608289393970055", "메구로 역 1분 / 시어터룸 & 키즈룸", "메구로구", "임대 호실(전체)", 753805,
      4.82, 11, 4.9, 1, 1, 4, 1, 8, None, 1, "메구로역", 0, "환불 불가",
      1, 1, 0, 1, "낮음(후기 11개)", "시부야 남쪽 4.5km", ["H~1649608289393970055~4f367c3f-601a-4cdc-8c7a-e4ec13f8c61a.png",
          "H~1649608289393970055~7f3ed6c1-8c4b-49ba-986d-81f0aacc468d.jpeg"], (35.6111, 139.694)),
]

def G(slug_key, gid, name, district, typ, per_night, r10, rv, sup, bed, beds, cap, area, station, dist_m, fc, cn, k, w, e, a, conf, hl, photos):
    walk = math.ceil(dist_m / 80) if dist_m else None
    lat, lng = STATIONS[station[0]]
    return dict(
        id=gid, platform="Agoda", name=name, district=district, type=typ, url=agoda_url(slug_key),
        total_krw=per_night * 4, price_basis=f"Agoda 1박 세금포함 {per_night:,} x 4",
        rating10=r10, reviews=rv, loc10=None, superhost=None,
        bedrooms=bed, beds=beds, baths=1, capacity=cap, area_m2=area,
        walk_min=walk, nearest=f"{station[1]} {dist_m}m", free_cancel=fc, cancel_note=cn,
        kitchen=k, washer=w, elevator=e, aircon=a, conf=conf, highlights=hl,
        photos=photos, lat=lat, lng=lng, coord_basis="가장 가까운 역 좌표로 근사")

NEW_AGODA = [
    G("takadababa-4mins-walk-4-302/hotel/tokyo-jp.html", "agoda-takadababa-302", "다카다노바바 역 도보 4분 스튜디오 (신주쿠권)",
      "신주쿠구(다카다노바바)", "아파트(스튜디오)", 106757, 8.8, 2, None, 0, 2, 4, 30, ("takadanobaba", "다카다노바바역"), 281,
      1, "무료 취소 가능", 1, 1, 1, 1, "낮음(후기 2개)", "30㎡ 스튜디오, 더블 2, 엘리베이터",
      [agoda_pix(p) for p in ["pix8.agoda.net/hotelImages/66187769/0/c9992ae92b5b975a01c3ce8e371c49ec.jpg",
        "pix8.agoda.net/hotelImages/66187769/0/cf4147f7eb4414c338b414ed6c443f79.jpg",
        "pix8.agoda.net/hotelImages/66187769/0/6abd7d5780499427248ee92d36733921.jpg",
        "pix8.agoda.net/hotelImages/66187769/0/54cb5a20ae75be245e3a6de8f13ce931.jpg",
        "pix8.agoda.net/hotelImages/66187769/0/0f1647992339ec6c3072143532dbeec9.jpg"]]),
    G("xlh101-modern-apartment-for-4-in-shinjuku-10-min/hotel/tokyo-jp.html", "agoda-xlh101", "XLH101 모던 아파트 (4인, 침실 1)",
      "신주쿠구(오치아이 방면)", "아파트(침실 1)", 135783, 8.0, 67, None, 1, 2, 4, 20, ("ochiai-minami-nagasaki", "오치아이미나미나가사키역"), 478,
      1, "무료 취소", 1, 1, 0, 1, "중간(20㎡에 4인, 협소)", "더블 + 소파베드, 20㎡",
      [agoda_pix("pix8.agoda.net/hotelImages/90373467/0/" + f) for f in ["7edeb6e23663a3a3da003bc93fa5af23.jpg",
        "96ddfeb5087dce09b298264f66deeeb3.jpg", "935c848753bb6791d8baf5812a0cf026.jpg", "fd31ec205db72aa0239bbfee98740afd.jpg",
        "c279b9d27c8bf8ecd73c6edf9646a92d.jpg"]]),
    G("unito-residence-shinjuku-wakamatsu-kawada/hotel/tokyo-jp.html", "agoda-unito-wakamatsu", "unito residence 신주쿠 와카마쓰카와다",
      "신주쿠구(와카마쓰카와다)", "아파트(스튜디오)", 137165, 8.5, 2, None, 0, None, 4, 30, ("wakamatsu-kawada", "와카마쓰카와다역"), 91,
      1, "무료 취소", 1, 1, 0, 1, "낮음(후기 2개, 침대 구성 미확인)", "30㎡ 스튜디오, 역 91m",
      [agoda_pix("pix8.agoda.net/hotelImages/96435542/0/" + f) for f in ["e4e161b306d76dbc98931097afd68b4e.jpg",
        "0689ddc9570aa3146f0c98d43cafe7f4.jpg", "12997db234957498157f7d1f47e4dd81.jpg"]]),
    G("keisei-haitsu-takadanobaba/hotel/all/kami-takada-jp.html", "agoda-keisei-haitsu", "Keisei Haitsu Takadanobaba",
      "신주쿠구(다카다노바바)", "아파트(스튜디오)", 158283, 9.3, 1189, None, 0, 3, 4, 28, ("takadanobaba", "다카다노바바역"), 425,
      1, "무료 취소", 1, 1, 0, 1, "높음(후기 1,189개)", "28㎡, 싱글 2 + 더블 1, 평점 9.3",
      [agoda_signed("827813908", "0cd1842c19b3d5909efeee51861e9052e547755e7922159b1143df554d66f40a"),
       agoda_signed("836412328", "1e8fee2a6249b43c96824bd965842fd4ff81bb788931cb06004be35d47a619c2"),
       agoda_signed("836412333", "da351da4689cbd2bab4d1e99e0daa1fea6e967e24e354518e13b46d3062f1644"),
       agoda_signed("836412008", "b724fec336b985b1919db01a308343b1a11203ae8da8ed0ee3a98c5d030a3d4c"),
       agoda_signed("836412004", "529bd0ffbc905fd91f68bc91529e725fb4b0386817da0c309ac4bd3aeaa66f54")]),
    G("shinjuku-shibuya-modern-full-furnished-apartment/hotel/tokyo-jp.html", "agoda-oak-stay-1", "Oak Stay Shibuya 1 (25㎡ 침실 1)",
      "시부야구(하쓰다이 방면)", "아파트(침실 1)", 160560, 9.2, 12, None, 1, 3, 4, 25, ("hatsudai", "하쓰다이역"), 341,
      1, "무료 취소 가능", 1, 1, 0, 1, "중간(역 거리는 같은 운영사 Oak Stay 2 기준 추정)", "싱글 2 + 더블 1, 신주쿠까지 전철 2분 표기",
      [agoda_pix("pix8.agoda.net/hotelImages/38500507/0/" + f) for f in ["95fc0073b77de4174c20c3bad5f7c51d.jpg",
        "d6465c54cec227436009ed423b8c4a19.jpg", "3ad11bfb1c745ac4cdf58c79adeb328f.jpg", "0047d12e30f4f269d4fbf971c42b34d4.jpg",
        "26dc267dde3ad5d650524d32428dd18c.jpg"]]),
    G("shinjuku-shibuya-modern-full-furnished-apartment2/hotel/tokyo-jp.html", "agoda-oak-stay-2", "Oak Stay Shibuya 2 (25㎡ 침실 1)",
      "시부야구(하쓰다이 방면)", "아파트(침실 1)", 163945, 8.6, 12, None, 1, 3, 4, 25, ("hatsudai", "하쓰다이역"), 341,
      1, "무료 취소 가능", 1, 1, 0, 1, "중간", "더블 1 + 소파베드 2",
      [agoda_pix("pix8.agoda.net/hotelImages/38540531/0/" + f) for f in ["c8d3a1c3bcfbf09b0c10e4847ee38635.jpg",
        "da9d4543ec22411f03116204eca68a51.jpg", "f6e05743de3ef3d50542596fb05c36d8.jpg", "2b0afc330bd98296ff09b8226b5fa9d7.jpg"]]),
    G("new-oak-stay-shibuya-2min-to-jr-shinjuku-via-train/hotel/tokyo-jp.html", "agoda-new-oak-stay", "New Oak Stay Shibuya (프라이빗 하우스 40㎡)",
      "시부야구(하쓰다이 방면)", "주택(침실 1)", 207401, 9.7, 117, None, 1, 2, 6, 40, ("hatsudai", "하쓰다이역"), 438,
      1, "무료 취소 가능", 1, 1, 0, 1, "높음(후기 117개)", "40㎡, 최대 6인, 평점 9.7",
      [agoda_pix("pix8.agoda.net/hotelImages/67518245/0/" + f) for f in ["2de2c245b38030524dd4be41f490db9d.jpg",
        "d8612516da8cc6f0c2690ebd1abe2907.jpg", "38db408f9d09d1abcf7ac73c9f44fe62.jpg", "940456ae81c9d5678468dc3e27bdb988.jpg",
        "3a2bb279d31452f3b6d67894248cbf01.jpg"]]),
    G("miaoyi-shinokubo-h74631186/hotel/all/tokyo-jp.html", "agoda-miaoyi-shinokubo", "Miaoyi Shinokubo (신오쿠보역 291m)",
      "신주쿠구(신오쿠보)", "아파트(스튜디오)", 198832, 9.5, 165, None, 0, 4, 4, 15, ("shin-okubo", "신오쿠보역"), 291,
      1, "무료 취소", 1, 1, 0, 1, "중간(15㎡, 4인에 매우 협소)", "싱글 2 + 요 이불 2, 평점 9.5",
      [agoda_signed("689947450", "41b0b6cd268df01a6fbd795721dcff39a6678eaab94e1f6aa70a0c773015c01d"),
       agoda_signed("689947624", "9ae29107f7ed145dafaebc8e6d810067e09b7ec14d091544cb4dbeef193c6a6e"),
       agoda_signed("689947653", "195f3299383c8bb1dd98cc75b4f49a86000b7a4b0472ff65ad7cb6dd6854293d"),
       agoda_signed("689947721", "62811a1e119af2e3379841528a22b655f654a2507dec3bd2fe52650c05536b5a"),
       agoda_signed("689947685", "862c5c92a6a88d429e00043c1589cfe7012f4e3ff7106b77f82214829ebab3dd")]),
    G("japanning/hotel/all/tokyo-jp.html", "agoda-japanning", "Shinjuku JAPANNING House (오쿠보역 119m)",
      "신주쿠구(오쿠보)", "아파트(스튜디오)", 200347, 9.0, 1927, None, 0, 2, 4, None, ("okubo", "오쿠보역"), 119,
      1, "무료 취소 가능", 1, 1, 0, 1, "높음(후기 1,927개, 면적 미기재)", "더블 2, 후기 1,927개",
      [agoda_signed("486734211", "63fe89acb874e5bc8c371b802f5770c303251a54ee4d5195ccb1097a1b8af15f"),
       agoda_signed("486734326", "15626a0304b3c40a699d905272644da385531dc62f002157da181513d6e332c9"),
       agoda_signed("486734310", "5facbbe0fc5b26b7668b7511ee471402c4116cb60789c3484d29a8d5b886cc66"),
       agoda_signed("486734318", "66438132539aaa5262218920a3cfd9c1e6dd10dc360bc76dca8db6ba2ee73535"),
       agoda_signed("486734279", "73baa70a773011f14057b5b1401860c4c0fbfb769bf7faff4403a907e4ecfc8f")]),
]

NEW_AIRBNB_V2 = [
    A("1714325842346013434", "Conforia Liv 시부야 혼초 (시부야·신주쿠 접근)", "시부야구(혼초)", "임대 호실(아파트)", 1149640,
      4.97, 63, 4.8, 1, None, None, None, None, 43, 5, "미확인", 1, "취소 수수료 없음(기한 미확인)",
      None, None, None, None, "낮음(침실·침대·편의시설 미공개)", "후기 63개 평점 4.97", [], (35.6855, 139.6778)),
    A("1492115040511521117", "선샤인시티 도보 10분 주택 (침실 2)", "도시마구(이케부쿠로 동쪽)", "주택(전체)", 1119204,
      4.92, 25, 4.7, 1, 2, 5, 1, 6, 45, 10, "미확인", 0, "무료 취소 문구 없음(확인 필요)",
      1, 1, 0, 1, "중간(도보 시간 추정)", "퀸 1 / 싱글 3+소파침대 1, 45㎡", [], (35.72664, 139.72358)),
    A("1050873822110318696", "더 본사이 파크사이드 아파트먼트", "도시마구(스가모 방면)", "임대 호실(아파트)", 974874,
      4.82, 759, 4.9, 1, None, None, None, None, 40, 6, "미확인", 1, "취소 수수료 없음(기한 미확인)",
      1, 1, 1, 1, "중간(침실 수 미공개)", "후기 759개, JR 신주쿠·우에노 접근", [], (35.7321, 139.7325)),
    A("1527378868268458620", "크리스털 다카다노바바 (임대 호실)", "신주쿠구(다카다노바바)", "임대 호실(아파트)", 751232,
      4.65, 20, 4.8, 0, None, None, None, None, None, 3, "다카다노바바역(추정)", 1, "11/4까지 무료 취소",
      1, 1, 0, 1, "낮음(침실 수 미공개, 검색 결과 가격과 차이)", "후기 20개", [], (35.7143, 139.70846)),
    A("32874558", "이케부쿠로역 도보 5분 (공항버스 정류장 5분)", "도시마구(이케부쿠로)", "아파트(임대 호실)", 1090358,
      4.76, 1280, 4.9, 1, None, None, None, None, None, 5, "이케부쿠로역", 1, "취소 수수료 없음(기한 미확인)",
      1, 1, 0, 1, "중간(침실 수 미공개)", "후기 1,280개", [], (35.7265, 139.7086)),
    A("1764570978167596245", "오쿠보역 도보 2분 #403 (unito residence)", "신주쿠구(오쿠보)", "임대 호실(전체)", 1089775,
      None, 1, None, 0, 1, 3, 1, 5, None, 2, "오쿠보역", 1, "10/6까지 무료 취소",
      1, 1, 1, 1, "낮음(후기 1개)", "침실 1(더블) + 거실 소파베드", [], (35.7017, 139.695)),
    A("1348949057139367275", "오쿠보역 10분 · 2LDK 주택 (최대 8)", "신주쿠구(오쿠보)", "주택(전체)", 1100661,
      4.56, 39, 4.6, 0, 2, 4, 1, 8, None, 10, "오쿠보역", 1, "10/6까지 무료 취소",
      1, 0, 0, 1, "중간(세탁기 미확인, 사진 2장)", "침실 2개 각각 더블 2", [], (35.7058, 139.6919)),
    A("1465635700933126006", "2층 단독주택 (2025 리노베이션, 6인)", "도시마구(이케부쿠로 서쪽)", "주택(전체)", 1005308,
      4.92, 36, 4.9, 1, 2, 4, 1, 6, None, 4, "미확인", 0, "무료 취소 문구 없음(확인 필요)",
      1, 1, 0, 1, "높음", "욕조, 키즈 공간", [], (35.7294, 139.6817)),
    A("1721567698226742624", "이케부쿠로 도보 8분 · 40㎡ (요초메역 6분)", "도시마구(이케부쿠로)", "임대 호실(아파트)", 922424,
      4.67, 3, 4.3, 1, 1, 4, 1, 4, 40, 8, "이케부쿠로역(추정)", 1, "10/6까지 무료 취소",
      1, 1, 1, 1, "낮음(후기 3개)", "싱글 4, 4인 정원", [], (35.73463, 139.70271)),
    A("1446383139984427189", "4베드 · 이케부쿠로 근처 역 4분 (1층 통째로)", "도시마구(이케부쿠로)", "임대 호실(전체)", 1115083,
      4.88, 43, 4.9, 1, 1, 4, 1, 8, None, 4, "미확인", 1, "10/6까지 무료 취소",
      1, 0, 0, 1, "중간", "슈퍼싱글 4개, 8인 정원", [], (35.7284, 139.6933)),
    A("1484390725924866344", "메구로 80㎡ 단독주택 (침실 2)", "메구로구", "주택(전체)", 1193385,
      4.96, 25, 4.6, 1, 2, 5, 1.5, 8, 80, 6, "미확인", 1, "10/6까지 무료 취소",
      1, 1, 0, 1, "중간", "80㎡ 독채", [], (35.62747, 139.70897)),
]
NEW_AGODA_V2 = [
    G("301-4-8-max5/hotel/all/tokyo-jp.html", "agoda-301-4-8-max5", "F301 시부야권 · 신주쿠 전철 4분 (최대 5인)",
      "시부야구(니시신주쿠 인접)", "아파트(스튜디오 40㎡)", 194907, 8.1, None, None, 0, 3, 5, 40,
      ("nishi-shinjuku-gochome", "니시신주쿠고초메역"), 660, 1, "무료 취소 가능", 1, 1, 1, 1,
      "중간(후기 수 미확인)", "싱글 1 + 더블 2, 엘리베이터·세탁기", []),
    G("newopen-shinjuku-shimo-ochiai-3min-apartment/hotel/all/kami-takada-jp.html", "agoda-newopen-shimo-ochiai",
      "Shinjuku 10min Top FL 아파트 (시모오치아이역 3분, 최대 7인)", "신주쿠구(시모오치아이)", "아파트(44㎡, 3베드)",
      262800, 9.7, 10, None, 0, 3, 7, 44, ("shimo-ochiai", "시모오치아이역"), 140, 1, "무료 취소", 1, 1, 1, 1,
      "낮음(후기 10개)", "44㎡ 싱글 3, 엘리베이터, 평점 9.7", []),
]

# 기존 항목 보정 (좌표·면적·사진)
EXISTING_COORDS = {
    "abnb-1469095319536089662": (35.68624, 139.67808), "abnb-1715816840417249516": (35.7016, 139.6926),
    "abnb-1589675254027255583": (35.70798, 139.72792), "abnb-31104721": (35.7313, 139.6838),
    "abnb-1257106666619099060": (35.7341, 139.7263), "abnb-1309282618081558951": (35.7288, 139.6985),
}
AREA_FIX = {  # 본문 정규식 오탐 제거 (제목/설명에 명시된 값만 유지)
    "abnb-1206287919554065802": None, "abnb-47297674": None,
}
HOUSE_B = dict(
    lat=STATIONS["higashi-shinjuku"][0], lng=STATIONS["higashi-shinjuku"][1], coord_basis="가장 가까운 역 좌표로 근사",
    photos=[agoda_signed("838639086", "631723a2db30aa356eed660676ff5ff180b9db6e0c6898bbb34a56eabfda13dc"),
            agoda_signed("661276074", "1740cd0f98ef59f3d3b2e05e18f90c394ae38a592b0b7c6341b3fe16c5677fc4")])

def apply_v2(by):
    """2차 수집: 신규 후보, 사진 확대, 침실 수, 좌표 보강."""
    import collected_v2 as C
    for n in NEW_AIRBNB_V2 + NEW_AGODA_V2:
        by[n["id"]] = {**by.get(n["id"], {}), **n}
    for i, (la, ln) in {"abnb-668489111328647720": (35.6748, 139.6776), "abnb-1206287919554065802": (35.68774, 139.68077)}.items():
        by[i].update(lat=la, lng=ln, coord_basis="Airbnb 공개 좌표(대략)")
    def abnb_url_of(dirname, fn):
        return f"https://a0.muscache.com/im/pictures/{dirname}/original/{fn}"
    for raw_id, groups in C.AIRBNB_PHOTOS.items():
        urls = [abnb_url_of(d, fn) for d, files in groups for fn in files.split()]
        urls += ["https://a0.muscache.com/im/pictures/" + fn for fn in C.AIRBNB_BARE.get(raw_id, "").split()]
        if f"abnb-{raw_id}" in by:
            by[f"abnb-{raw_id}"]["photos"] = urls
    for gid, urls in C.AGODA_PHOTOS.items():
        if gid in by:
            by[gid]["photos"] = urls
    for i, v in C.BEDROOMS.items():
        if i in by:
            by[i]["bedrooms"] = v
            by[i]["bedroom_note"] = C.BEDROOM_NOTE.get(i)


def download_photos(show, per=12, width=800):
    import shutil, concurrent.futures as cf
    if IMG_DIR.exists():
        shutil.rmtree(IMG_DIR)
    IMG_DIR.mkdir()
    jobs = []
    for l in show:
        for n, u in enumerate(l["photos"][:per], 1):
            jobs.append((l["id"], n, u))

    def one(job):
        lid, n, u = job
        dst = IMG_DIR / lid / f"{n}.jpg"
        dst.parent.mkdir(exist_ok=True)
        tmp = dst.with_suffix(".raw")
        url = u + ("?im_w=1200" if "muscache" in u and "?" not in u else "")
        r = subprocess.run(["curl", "-s", "-L", "-m", "40", "-o", str(tmp), "-w", "%{http_code}", "-A", "Mozilla/5.0", url],
                           capture_output=True, text=True)
        if r.stdout.strip() != "200" or not tmp.exists() or tmp.stat().st_size < 2000:
            tmp.unlink(missing_ok=True); return (lid, n, None)
        s = subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "72", "-Z", str(width), str(tmp), "--out", str(dst)], capture_output=True)
        tmp.unlink(missing_ok=True)
        if s.returncode != 0 or not dst.exists():
            dst.unlink(missing_ok=True); return (lid, n, None)
        return (lid, n, f"images/{lid}/{n}.jpg")

    got = {}
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for lid, n, p in ex.map(one, jobs):
            if p: got.setdefault(lid, []).append((n, p))
    for l in show:
        l["photos_local"] = [p for _, p in sorted(got.get(l["id"], []))]


def main():
    d = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    by = {l["id"]: l for l in d["listings"]}
    for n in NEW_AIRBNB + NEW_AGODA:
        by[n["id"]] = {**by.get(n["id"], {}), **n}
    for i, (la, ln) in EXISTING_COORDS.items():
        by[i].update(lat=la, lng=ln, coord_basis="Airbnb 공개 좌표(대략)")
    for i, v in AREA_FIX.items():
        if i in by: by[i]["area_m2"] = v
    by["agoda-house-b"].update(HOUSE_B)
    apply_v2(by)

    out = []
    for l in by.values():
        if l.get("lat") is not None:
            for k, (nm, hl, hn) in HUBS.items():
                l[f"dist_{k}_km"] = round(hav(l["lat"], l["lng"], hl, hn), 2)
            dsh = min(l["dist_shinjuku_km"], l["dist_shibuya_km"])
            l["tier"] = 1 if dsh <= 3.0 else (2 if l["dist_ikebukuro_km"] <= 2.5 else 0)
        else:
            l["tier"] = None
        l["budget_ok"] = l["total_krw"] <= BUDGET
        l["area_ok"] = l.get("area_m2") is None or l["area_m2"] >= AREA_MIN
        l["exclude_reason"] = (
            "예산 초과" if not l["budget_ok"] else
            f"면적 {l['area_m2']}㎡ (30㎡ 미만)" if not l["area_ok"] else
            "번화가에서 멂" if l["tier"] == 0 else
            "위치 정보 없음" if l["tier"] is None else None)
        out.append(l)
    d["listings"] = out
    m = d["meta"]
    m["budget_krw"] = BUDGET
    m["budget_note"] = "4박 총액 1,200,000원 이하만 슬라이드 본문에 사용. 초과 후보는 참고 표에만 표시."
    m["area_min_m2"] = AREA_MIN
    m["area_note"] = "객실 면적 30㎡ 미만은 제외(면적 미기재는 유지). Agoda는 객실 면적 표기, Airbnb는 호스트가 적은 경우만 수집."
    m["bedrooms_note"] = "bedrooms: 0 = 스튜디오/원룸(침실 분리 없음), null = 호스트 미공개(임대 호실형)."
    m["tier_note"] = "tier 1 = 시부야·신주쿠역 직선 3.0km 이내, tier 2 = 그 외 이케부쿠로역 2.5km 이내, tier 0 = 범위 밖, null = 좌표 없음"
    m["coord_note"] = "Airbnb 좌표는 공개된 '대략 위치'(수백 m 오차), Agoda는 좌표를 제공하지 않아 가장 가까운 역 좌표로 근사. 직선거리는 실제 이동거리가 아님."
    m["photo_note"] = "photos = 원본 URL(최대 16장), photos_local = images/ 에 저장한 슬라이드용 사본(최대 12장, 가로 800px)."

    show = [l for l in out if l["exclude_reason"] is None]
    download_photos(show)
    JSON_PATH.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print("total", len(out), "| shown", len(show), "| excluded", len(out) - len(show))
    from collections import Counter
    print("reasons:", dict(Counter((l["exclude_reason"] or "").split(" (")[0] for l in out if l["exclude_reason"])))
    for l in sorted(show, key=lambda x: (x["tier"], x["total_krw"])):
        print(l["tier"], l["platform"][:2], f"{l['total_krw']:>9,}", f"sh{l['dist_shinjuku_km']:.1f} sb{l['dist_shibuya_km']:.1f} ik{l['dist_ikebukuro_km']:.1f}",
              "a", l["area_m2"], "br", l["bedrooms"], l["name"][:26], "| ph", len(l["photos_local"]))


if __name__ == "__main__":
    main()
