# _research 원본 → images/ (사이트가 쓰는 사진). 자르기 + 색 통일(채도 낮춤·살짝 따뜻하게).
# 실행: python -X utf8 _prep_images.py   — 사진을 바꾸고 싶으면 아래 표만 고친다.
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).parent
R = ROOT / "_research"
OUT = ROOT / "images"
OUT.mkdir(exist_ok=True)

# 이름: (원본, 자를 비율 상자 x0 y0 x1 y1 — None이면 전체)
PHOTOS = {
    "hero-pano":      ("best/v_FmnQm_32.jpg",            (0.00, 0.28, 0.66, 0.64)),   # 테라스에서 본 청풍호 띠 (AI 드론 나오면 교체)
    "hero-m":         ("best/v_HKyQL_42.jpg",            (0.00, 0.06, 1.00, 0.84)),   # 가을 테라스 세로
    "front":          ("ota/y02.jpg",                    None),
    "front-lawn":     ("ota/y05.jpg",                    None),
    "arch":           ("ota/y08.jpg",                    (0.60, 0.08, 1.00, 0.86)),
    "sign":           ("ota/y02.jpg",                    (0.36, 0.20, 0.72, 0.66)),
    "living":         ("ota/y01.jpg",                    None),                        # 스크롤 따라 천장→창 훑기
    "living-sofa":    ("ota/y01.jpg",                    (0.00, 0.30, 0.48, 1.00)),
    "living-light":   ("ota/y01.jpg",                    (0.44, 0.00, 0.78, 0.40)),
    "dining":         ("ota/y04.jpg",                    (0.06, 0.34, 0.86, 1.00)),
    "dining-wide":    ("ota/y44.jpg",                    None),
    "bed-view":       ("ota/y23.jpg",                    (0.02, 0.14, 0.58, 0.78)),
    "bed-twin":       ("ota/y50.jpg",                    None),
    "bed-lamp":       ("ota/y29.jpg",                    None),
    "kitchen":        ("ota/y27.jpg",                    None),
    "bath":           ("ota/y46.jpg",                    None),
    "lawn-lake":      ("ota/y20.jpg",                    (0.00, 0.10, 0.92, 0.95)),
    "lawn-path":      ("ota/y09.jpg",                    None),
    "terrace-fire":   ("ota/y07.jpg",                    (0.00, 0.10, 1.00, 0.95)),
    "terrace-autumn": ("best/v_HKyQL_48.jpg",            (0.00, 0.06, 1.00, 0.86)),
    "fog":            ("best/v_O7vpT_44.jpg",            (0.00, 0.26, 1.00, 0.72)),
    "rain-deck":      ("best/v_MswiO_2.jpg",             (0.00, 0.10, 1.00, 0.90)),
    "pheasant":       ("best/v_fMz72_6.jpg",             (0.00, 0.38, 1.00, 0.96)),
    "pool":           ("youtube/frames/dCCX8JQt3Ec_03.jpg", (0.00, 0.10, 1.00, 0.90)),
    "bbq":            ("youtube/frames/oTRjEucc6gw_04.jpg", (0.00, 0.10, 1.00, 0.90)),
    "gathering-lawn": ("youtube/frames/1WUD4Sr58lo_01.jpg", (0.00, 0.12, 1.00, 0.92)),
    "pingpong":       ("ota/y06.jpg",                    None),
    "drone-small":    ("ota/y17.jpg",                    None),                        # 800px — 작게만
}


def grade(im):
    im = ImageEnhance.Color(im).enhance(0.82)
    im = ImageEnhance.Contrast(im).enhance(0.94)
    r, g, b = im.split()
    r = r.point(lambda v: min(255, int(v * 1.03 + 2)))
    b = b.point(lambda v: int(v * 0.96))
    return Image.merge("RGB", (r, g, b))


for name, (src, box) in PHOTOS.items():
    im = Image.open(R / src).convert("RGB")
    if box:
        W, H = im.size
        im = im.crop((int(box[0] * W), int(box[1] * H), int(box[2] * W), int(box[3] * H)))
    im = grade(im)
    if im.width < 1600 and im.width >= 700:  # ponytail: 단순 확대+샤픈. 화면 꽉 채우는 장면은 AI 업스케일로 교체
        im = im.resize((1600, int(im.height * 1600 / im.width)), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 50, 2))
    im.save(OUT / f"{name}.jpg", quality=92)
    print(f"{name:16} {im.size[0]}x{im.size[1]}")

# AI 시안(촬영 전 자리) — 같은 색 보정만 하고 jpg로
for p in sorted((R / "ai").glob("*.png")):
    im = grade(Image.open(p).convert("RGB"))
    im.save(OUT / f"{p.stem}.jpg", quality=92)
    print(f"{p.stem:16} {im.size[0]}x{im.size[1]}  (AI)")
