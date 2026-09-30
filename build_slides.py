"""tokyo_candidates.json 을 slides_template.html 에 삽입해 단일 HTML 슬라이드를 만든다.

사용: python3 build_slides.py
결과: index.html (GitHub Pages 루트 문서, 이미지는 images/ 상대경로)
"""
import json
from pathlib import Path

here = Path(__file__).parent
data = json.loads((here / "tokyo_candidates.json").read_text(encoding="utf-8"))
tpl = (here / "slides_template.html").read_text(encoding="utf-8")
assert "/*DATA*/null" in tpl, "template placeholder missing"
# </script> 안전 처리
payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
out = tpl.replace("/*DATA*/null", payload)
(here / "index.html").write_text(out, encoding="utf-8")
print("built", len(data["listings"]), "listings ->", here / "index.html")
