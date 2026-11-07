"""청풍파노라마뷰 홈페이지 빌드 — site.config.json + templates/ + images/ → dist/

    python -X utf8 build.py

dist/ 에는 배포할 파일만 들어간다. 값은 전부 site.config.json, 구조는 templates/ (THE뷰는 config만 새로 채운다).
빈 칸("")으로 남은 값은 끝에 [확인 필요] 목록으로만 나오고 손님 화면에는 안 보인다.
"""
import datetime
import hashlib
import json
import os
import re
import shutil
from html import escape
from pathlib import Path
from urllib.parse import quote

from PIL import Image

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
T = ROOT / "templates"
cfg = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))
todo_list = []
today = datetime.date.today()

name, phone, a = cfg["name"], cfg["phone"], cfg["address"]
tel = re.sub(r"[^0-9]", "", phone)
sms_tel = re.sub(r"[^0-9]", "", cfg["sms"])
domain = cfg["domain"].rstrip("/")
base = os.environ.get("BASE", "").rstrip("/") or domain or cfg["preview_url"].rstrip("/")  # BASE=http://localhost:8784/dist 로 로컬 확인
noindex = cfg["photos_temporary"] or not domain
addr = f"{a['region']} {a['city']} {a['street']}"
cap = cfg["capacity"]
g = cfg["geo"]
AI = set(cfg["ai_images"])

for k, label in (("domain", "도메인"), ("owner", "대표자 이름"), ("biz_no", "사업자등록번호"), ("ga4", "GA4 측정 ID"),
                 ("google_verify", "구글 서치콘솔 소유확인 값"), ("naver_verify", "네이버 서치어드바이저 소유확인 값")):
    if not cfg[k]:
        todo_list.append(label)
if not g["lat"]:
    todo_list.append("위도·경도 (네이버 지도 주소의 lat·lng)")
if not a["jibun"]:
    todo_list.append("지번 주소")
if cfg["photos_temporary"]:
    todo_list.append("사진 — OTA·유튜브 사진과 AI 시안 5장. 촬영본으로 교체 후 photos_temporary=false")
for c in cfg["channels"]:
    if not c["url"]:
        todo_list.append(f"채널 주소 — {c['name']}")
for row, val in cfg["rates"]:
    if not val:
        todo_list.append(f"요금 — {row}")

# ── 사진: images/*.jpg → dist/images/*.webp (1600·800·400) ─────────────────
shutil.rmtree(DIST, ignore_errors=True)
(DIST / "images").mkdir(parents=True)
(DIST / "posts").mkdir()
_size = {}


def prep(stem):
    if stem not in _size:
        src = Image.open(ROOT / "images" / f"{stem}.jpg").convert("RGB")
        for w, suffix in ((1600, ""), (800, "-800"), (400, "-400")):
            im = src.copy()
            im.thumbnail((w, w * 2))
            im.save(DIST / "images" / f"{stem}{suffix}.webp", quality=80, method=6)
        _size[stem] = src.size
    return _size[stem]


def img(stem, alt, sizes="(min-width: 1024px) 50vw, 100vw", eager=False, cls=""):
    w, h = prep(stem)
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    return (f'<img{" class=" + chr(34) + cls + chr(34) if cls else ""} src="{base}/images/{stem}-800.webp" '
            f'srcset="{base}/images/{stem}-400.webp 400w, {base}/images/{stem}-800.webp 800w, {base}/images/{stem}.webp 1600w" '
            f'sizes="{sizes}" width="{w}" height="{h}" alt="{escape(alt)}" {load} decoding="async">')


def ai_note(*stems):
    """촬영 전 자리 — AI 시안이면 사진 아래 한 줄. 촬영본으로 바꾸면(ai_images에서 빼면) 사라진다."""
    return '<p class="ai">촬영 예정 자리입니다. 지금 보이는 사진은 AI로 만든 시안입니다.</p>' if cfg["photos_temporary"] and any(s in AI for s in stems) else ""


# 공유 카드 1200x630
og_src = Image.open(ROOT / "images" / f"{cfg['images']['og']}.jpg").convert("RGB")
W, H = og_src.size
h = int(W * 630 / 1200)
og_src.crop((0, (H - h) // 2, W, (H - h) // 2 + h)).resize((1200, 630)).save(DIST / "og.jpg", quality=85)
og_image = f"{base}/og.jpg"

# ── 공통 조각 ───────────────────────────────────────────────────────────
ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{}</svg>'
ico_call = ICON.format('<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z"/>')
ico_sms = ICON.format('<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>')
ico_pin = ICON.format('<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>')
ico_menu = ICON.format('<path d="M3 7h18M3 12h18M3 17h18"/>')
ico_x = ICON.format('<path d="M6 6l12 12M18 6L6 18"/>')
mark = (ROOT / "static" / "favicon.svg").read_text(encoding="utf-8").strip().replace("<svg ", '<svg aria-hidden="true" ', 1)

ADMIN_KEY = "pano_gh_token"  # 관리 화면 열쇠 저장 이름(기기별 localStorage) — 사이트마다 다르게
MENU = [("house.html", "공간"), ("gathering.html", "모임"), ("pet.html", "반려견"), ("guide.html", "이용 안내"), ("around.html", "오시는 길"), ("blog.html", "소식")]
sms_href = f"sms:{sms_tel}?&body={quote(cfg['sms_body'])}"
if g["lat"]:
    route_url = f"https://map.kakao.com/link/to/{quote(name)},{g['lat']},{g['lng']}"
else:
    route_url = f"https://map.kakao.com/link/search/{quote(addr)}"
naver_map_url = f"https://map.naver.com/p/search/{quote(addr)}"
filled = [c for c in cfg["channels"] if c["url"]]
css_v = hashlib.md5((ROOT / "static" / "site.css").read_bytes()).hexdigest()[:8]
js_v = hashlib.md5((ROOT / "static" / "site.js").read_bytes()).hexdigest()[:8]
biz = " · ".join(x for x in (f"대표 {cfg['owner']}" if cfg["owner"] else "", f"사업자등록번호 {cfg['biz_no']}" if cfg["biz_no"] else "") if x)
shell = (T / "shell.html").read_text(encoding="utf-8")


def fill(tpl, v):
    return re.sub(r"\{\{(\w+)\}\}", lambda m: str(v[m.group(1)]), tpl)


def ld(*objs):
    return "\n".join('<script type="application/ld+json">' + json.dumps(o, ensure_ascii=False).replace("<", "\\u003c") + "</script>" for o in objs)


def crumbs(path, title):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "홈", "item": f"{base}/"},
        {"@type": "ListItem", "position": 2, "name": title, "item": f"{base}/{path}"}]}


def page(path, title, description, body, lds, og_title=None, extra="", preload="", current=None):
    menu = "".join(f'<a href="{base}/{p}"{" aria-current=" + chr(34) + "page" + chr(34) if p == current else ""}>{t}</a>' for p, t in [("index.html", "처음")] + MENU)
    v = dict(
        robots='<meta name="robots" content="noindex">' if noindex else "",
        title=escape(title), description=escape(description), url=f"{base}/{path}" if path != "index.html" else f"{base}/",
        name=escape(name), og_title=escape(og_title or title), og_image=og_image, base=base,
        verify="".join(f'<meta name="{k}" content="{cfg[c]}">' for k, c in (("google-site-verification", "google_verify"), ("naver-site-verification", "naver_verify")) if cfg[c]),
        css_v=css_v, js_v=js_v, preload=preload, ld=ld(*lds),
        ga4=(f'<script async src="https://www.googletagmanager.com/gtag/js?id={cfg["ga4"]}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());gtag("config","{cfg["ga4"]}");</script>') if cfg["ga4"] else "",
        mark=mark, menu=menu, ico_menu=ico_menu, ico_x=ico_x, ico_call=ico_call, ico_sms=ico_sms, ico_pin=ico_pin,
        tel=tel, phone=phone, body=body, addr=escape(addr), checkin=cfg["checkin"], checkout=cfg["checkout"],
        foot_menu="".join(f'<li><a href="{base}/{p}">{t}</a></li>' for p, t in MENU),
        channels="".join(f'<li><a href="{escape(c["url"])}" target="_blank" rel="noopener">{escape(c["name"])}</a></li>' for c in filled) or "<li>준비 중</li>",
        biz=(escape(biz) + " · ") if biz else "", year=today.year, updated=today.isoformat(),
        sms_href=sms_href, route_url=route_url, extra=extra,
    )
    out = DIST / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(fill(shell, v), encoding="utf-8")


def book_form():
    opts = "".join(f'<option{" selected" if n == cap["base"] else ""}>{n}</option>' for n in range(2, cap["max"] + 1))
    return (f'<form class="ask" data-name="{escape(name)}" data-sms="{sms_tel}">'
            f'<label><span>입실 날짜</span><input type="date" name="date" min="{today.isoformat()}"></label>'
            f'<label><span>몇 박</span><select name="nights"><option>1</option><option>2</option><option>3</option></select></label>'
            f'<label><span>인원</span><select name="people">{opts}</select></label>'
            f'<button class="btn btn-fill" type="submit">{ico_sms}문자로 빈 날짜 묻기</button></form>')


def faq_html(items):
    return "".join(f'<details><summary>{escape(q)}</summary><p>{escape(ans)}</p></details>' for q, ans in items)


def faq_ld(items):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": ans}} for q, ans in items]}


rates_rows = "".join(f'<tr><th>{escape(r)}</th>{"<td>" + escape(v) + "</td>" if v else "<td class=" + chr(34) + "ask" + chr(34) + ">문의</td>"}</tr>' for r, v in cfg["rates"])
extras_html = "".join(f'<div><b>{escape(k)}</b><span>{escape(v)}</span></div>' for k, v in cfg["extras"])
seats_html = "".join(f'<div class="rv"><b>{escape(n)}</b><p>{escape(d)}</p></div>' for n, d in cfg["gathering"]["seats"])
around_html = "".join(f'<div><div><b>{escape(n)}</b><span>{escape(d)}</span></div><em>{escape(m)}</em></div>' for n, d, m in cfg["around"])

# ── 블로그 글(글해줌 연결) ─────────────────────────────────────────────────
posts_path = ROOT / "posts.json"
posts = json.loads(posts_path.read_text(encoding="utf-8")) if posts_path.exists() else []
posts = sorted([x for x in posts if isinstance(x, dict) and x.get("id")], key=lambda x: -int(x["id"]))
plain = lambda t, n: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(t or ""))).strip()[:n]


def post_card(x):
    return (f'<article class="post rv"><time datetime="{escape(str(x["date"]))}">{escape(str(x["date"]))}</time>'
            f'<h3><a href="{base}/posts/{x["id"]}.html">{escape(x["title"])}</a></h3><p>{escape(plain(x.get("summary") or x.get("content"), 110))}</p>'
            f'<a class="go" href="{base}/posts/{x["id"]}.html">읽기</a></article>')


# ── 첫 화면 ───────────────────────────────────────────────────────────────
hero, hero_m = cfg["images"]["hero"], cfg["images"]["hero_m"]
hw, hh = prep(hero)
mw, mh = prep(hero_m)
hero_pic = (f'<picture><source media="(max-width: 719px)" srcset="{base}/images/{hero_m}-800.webp 800w, {base}/images/{hero_m}.webp 1600w" sizes="100vw">'
            f'<img src="{base}/images/{hero}-800.webp" srcset="{base}/images/{hero}-800.webp 800w, {base}/images/{hero}.webp 1600w" sizes="100vw" '
            f'width="{hw}" height="{hh}" alt="{escape(name)} 전경, 청풍호와 금수산 사이 잔디 마당 위의 벽돌집" fetchpriority="high" decoding="async"></picture>')
preload = (f'<link rel="preload" as="image" href="{base}/images/{hero}-800.webp" imagesrcset="{base}/images/{hero}-800.webp 800w, {base}/images/{hero}.webp 1600w" imagesizes="100vw" media="(min-width: 720px)">'
           f'<link rel="preload" as="image" href="{base}/images/{hero_m}-800.webp" media="(max-width: 719px)">')

three_html = ""
for i, (word, title, text, stem) in enumerate(cfg["three"]):
    fig = (f'<figure class="rv{" big" if i == 0 else ""}">{img(stem, f"{name} {title}", "(min-width: 1024px) 58vw, 100vw" if i == 0 else "(min-width: 1024px) 40vw, 100vw")}'
           f'<figcaption><span class="word">{escape(word)}</span><h3>{escape(title)}</h3><p>{escape(text)}</p>{ai_note(stem)}</figcaption></figure>')
    if i == 0:
        three_html += fig + '<div class="side">'
    else:
        three_html += fig
three_html += "</div>"

day_html = ""
for i, (t, label, title, text, p1, p2) in enumerate(cfg["day"], 1):
    if i == 2:  # 거실: 스크롤 따라 훑기
        pics = f'<div class="pan"><div class="stick">{img(p1, f"{name} 거실, 천장 조명부터 창밖 호수까지", "100vw")}</div></div>'
    else:
        pics = f'<div class="pics">{img(p1, f"{name} {label} {title}", "(min-width: 1024px) 60vw, 100vw")}{img(p2, f"{name} {label} 풍경", "(min-width: 1024px) 40vw, 100vw") if p2 else ""}</div>'
    day_html += (f'<article class="moment m{i}"><div class="t"><b>{escape(t)}</b><span>{escape(label)}</span></div>'
                 f'<div class="rv">{pics}<h3>{escape(title)}</h3><p class="txt">{escape(text)}</p>{ai_note(p1, p2)}</div></article>')

seasons_html = "".join(f'<figure>{img(stem, f"{name} {s} {d}", "(min-width: 720px) 520px, 78vw")}<figcaption><b>{escape(s)}</b><span>{escape(d)}</span></figcaption></figure>'
                       for s, d, stem in cfg["seasons"])
pet = cfg["pet"]
gath = cfg["gathering"]
cw, ch = prep(gath["photos"][1])
description = (f"제천 청풍호 옆 독채 펜션 {name}. 대지 {cfg['site_area']}, 집 {cfg['house_area']}를 하루 한 팀이 씁니다. "
               f"기준 {cap['base']}명 최대 {cap['max']}명, 유리 식당과 바비큐, 불멍, 반려견 동반. 칠순과 돌잔치, 동창회 모임. 문의 {phone}.")
posts_section = (f'<section><div class="wrap"><div class="head rv"><h2>소식</h2></div><div class="posts">{"".join(post_card(x) for x in posts[:3])}</div>'
                 f'<p class="rv" style="margin-top:30px"><a class="link" href="{base}/blog.html">글 전체 보기</a></p></div></section>') if posts else ""

index_body = fill((T / "index.html").read_text(encoding="utf-8"), dict(
    hero_pic=hero_pic, tagline="".join(f"<span><i>{escape(l.strip())}</i></span>" for l in cfg["tagline"].split("|")),
    hero_sub=escape(cfg.get("hero_sub") or f"대지 {cfg['site_area']}에 {cfg['house_area']} 집 한 채. 기준 {cap['base']}명, 최대 {cap['max']}명이 호수를 보며 묵습니다."),
    # 공지 한 줄 — 사장님이 관리 화면에서 켜고 끈다
    notice_html=(f'<p class="notice"><span>공지</span>{escape(cfg["notice"])}</p>' if cfg.get("notice_on") and cfg.get("notice") else ""),
    hero_cap=f'<p class="cap">촬영 예정 자리, AI 시안</p>' if hero in AI and cfg["photos_temporary"] else "",
    tel=tel, phone=phone, ico_call=ico_call, ico_sms=ico_sms, name=escape(name), sms_tel=sms_tel, today=today.isoformat(),
    people_opts="".join(f'<option{" selected" if n == cap["base"] else ""}>{n}</option>' for n in range(2, cap["max"] + 1)),
    site_area=cfg["site_area"], house_area=cfg["house_area"], cap_max=cap["max"], cap_base=cap["base"],
    statement=escape(f"{cfg['site_area']} 잔디 위의 {cfg['house_area']} 벽돌집, 열다섯 명까지. 정면은 청풍호, 뒤는 금수산. 대문을 닫으면 오늘은 한 가족만의 집입니다."),
    declare_sub=escape(f"하루 한 팀만 받습니다. 기준 {cap['base']}명, 최대 {cap['max']}명. 객실 단위 예약은 받지 않습니다."),
    quote=escape(cfg["quote"][0]), quote_by=escape(cfg["quote"][1]), book_form=book_form(),
    three_html=three_html, day_lead=escape("도착부터 다음 날 아침까지, 시간 순서대로 보여 드립니다."), day_html=day_html,
    base=base, cover_img=gath["photos"][1], cover_w=cw, cover_h=ch, cover_alt=escape(f"{name} 유리 식당, 열두 명이 앉는 긴 식탁"),
    g_title=escape(gath["title"]), g_lead=escape(gath["lead"]), seats_html=seats_html,
    pet_img=img(pet["photos"][0], f"{name} 마당의 황금계", "(min-width: 720px) 45vw, 100vw"), pet_title=escape(pet["title"]), pet_lead=escape(pet["lead"]),
    pet_rules="".join(f'<div><dt>{escape(k)}</dt><dd>{escape(v)}</dd></div>' for k, v in pet["rules"][:3]), pet_kids=escape(pet["kids"]),
    seasons_html=seasons_html, checkin=cfg["checkin"], checkout=cfg["checkout"], rates_rows=rates_rows, rate_note=escape(cfg["rate_note"]),
    extras_html=extras_html, faq_html=faq_html(cfg["faq"]), addr=escape(addr), route_url=route_url, naver_map_url=naver_map_url,
    nearby_line=escape(", ".join(f"{n} {d}" for n, d in cfg["nearby"])), around_html=around_html, around_note=escape(cfg["around_note"]),
    posts_section=posts_section))

business = {
    "@context": "https://schema.org", "@type": "LodgingBusiness", "additionalType": "https://schema.org/VacationRental",
    "name": name, "alternateName": cfg["name_alt"], "description": description, "telephone": "+82-" + phone.lstrip("0"),
    "address": {"@type": "PostalAddress", "streetAddress": a["street"], "addressLocality": a["city"], "addressRegion": a["region"], "addressCountry": "KR"},
    "checkinTime": cfg["checkin"], "checkoutTime": cfg["checkout"], "petsAllowed": True, "image": og_image,
    "amenityFeature": [{"@type": "LocationFeatureSpecification", "name": n, "value": v} for n, v in (
        ("독채 (하루 한 팀)", True), ("대지", cfg["site_area"]), ("건물", cfg["house_area"]), ("최대 인원", f"{cap['max']}명"),
        ("유리 식당", "12인 식탁"), ("개별 바비큐", True), ("불멍 화로", True), ("잔디 마당", True), ("탁구대", True), ("OTT", True), ("반려견", "10kg 이하 2마리"))],
}
if g["lat"]:
    business["geo"] = {"@type": "GeoCoordinates", "latitude": g["lat"], "longitude": g["lng"]}
if domain:
    business["url"] = domain + "/"
if filled:
    business["sameAs"] = [c["url"] for c in filled]
page("index.html", f"{name} | 청풍호 독채 펜션, 하루 한 팀 최대 {cap['max']}명", description, index_body,
     [business, faq_ld(cfg["faq"])], og_title=f"{name}, {cfg['tagline'].replace('|', ' ')}", preload=preload)

# ── 공간 ─────────────────────────────────────────────────────────────────
rooms_html, gallery = "", []
for title, text, stems in cfg["house_rooms"]:
    btns = ""
    for i, s in enumerate(stems):
        prep(s)
        btns += f'<button type="button" data-full="{base}/images/{s}.webp" aria-label="{escape(title)} 사진 크게 보기">{img(s, f"{name} {title} {i + 1}", "(min-width: 1024px) 60vw, 100vw" if i == 0 else "(min-width: 1024px) 20vw, 50vw")}</button>'
        gallery.append({"@type": "ImageObject", "contentUrl": f"{base}/images/{s}.webp", "name": f"{name} {title}"})
    rooms_html += f'<article class="room"><div class="info rv"><h2>{escape(title)}</h2><p>{escape(text)}</p>{ai_note(*stems)}</div><div class="g rv">{btns}</div></article>'
house_body = (f'<div class="page"><div class="wrap phead"><h1>{cfg["house_area"]} 집 한 채, 방마다 다른 풍경</h1><p class="lead">{escape(cfg["house_rooms"][0][1])} 침실은 여러 개, 욕실도 여러 개. 열다섯 명이 각자 쉴 자리가 있습니다.</p></div>'
              f'<div class="pcover">{img("front", f"{name} 외관, 벽돌집과 유리 식당", "100vw", eager=True)}</div>'
              f'<div class="wrap" style="padding-top:clamp(60px,8vw,110px);padding-bottom:clamp(80px,10vw,140px)"><div class="rooms">{rooms_html}</div>'
              f'<p class="small" style="margin-top:40px">{escape(cfg["house_note"])}</p></div></div>')
page("house.html", f"공간 | {name}", f"{name}의 거실, 유리 식당, 주방, 침실, 욕실, 마당과 테라스. {cfg['house_area']} 집 한 채를 하루 한 팀이 씁니다.",
     house_body, [{"@context": "https://schema.org", "@type": "ImageGallery", "name": f"{name} 공간 사진", "url": f"{base}/house.html", "image": gallery}, crumbs("house.html", "공간")],
     extra='<dialog class="lb"><button type="button" aria-label="닫기">×</button><img src="" alt=""></dialog>', current="house.html")

# ── 모임 ─────────────────────────────────────────────────────────────────
gl = "".join(f'<figure class="rv">{img(s, f"{name} 모임 {i + 1}", "(min-width: 720px) 33vw, 100vw")}</figure>' for i, s in enumerate(gath["photos"]))
gath_body = (f'<div class="page"><div class="wrap phead"><h1>{escape(gath["title"])}</h1><p class="lead">{escape(gath["lead"])}</p></div>'
             f'<div class="pcover">{img("ai-table", f"{name} 유리 식당에 차린 열두 명 상", "100vw", eager=True)}</div>'
             f'<div class="wrap" style="padding-top:clamp(40px,5vw,64px)">{ai_note("ai-table")}<div class="seats">{seats_html}</div>'
             f'<ul class="points">{"".join(f"<li>{escape(p)}</li>" for p in gath["points"])}</ul></div>'
             f'<section><div class="wrap"><div class="gl">{gl}</div></div></section>'
             f'<section id="book"><div class="wrap"><div class="head rv"><h2>모임 날짜를 먼저 잡아 두세요</h2><p class="lead">하루 한 팀이라 주말과 연휴는 일찍 찹니다. 날짜와 인원만 보내 주시면 빈 날짜를 바로 알려 드립니다.</p></div><div class="book" style="border:1px solid var(--line)"><div class="wrap">{book_form()}</div></div></div></section></div>')
page("gathering.html", f"칠순, 돌잔치, 동창회 모임 | {name}", f"{name}에서 열다섯 명까지 모이는 가족 행사와 동창회. 유리 식당 12인 식탁, 거실 식탁, 잔디 마당. 하루 한 팀이라 조용히 모입니다.",
     gath_body, [{"@context": "https://schema.org", "@type": "WebPage", "name": f"{name} 모임 안내", "url": f"{base}/gathering.html", "description": gath["lead"]}, crumbs("gathering.html", "모임")], current="gathering.html")

# ── 반려견 ───────────────────────────────────────────────────────────────
pet_body = (f'<div class="page"><div class="wrap phead"><h1>{escape(pet["title"])}</h1><p class="lead">{escape(pet["lead"])}</p></div>'
            f'<section style="padding-top:0;border-top:0"><div class="wrap"><div class="split"><figure class="rv">{img(pet["photos"][1], f"{name} 잔디 마당과 돌길, 해먹", "(min-width: 720px) 45vw, 100vw", eager=True)}</figure>'
            f'<div><dl class="rules rv">{"".join(f"<div><dt>{escape(k)}</dt><dd>{escape(v)}</dd></div>" for k, v in pet["rules"])}</dl><p class="kids rv">{escape(pet["kids"])}</p></div></div></div></section>'
            f'<section><div class="wrap"><div class="gl">{"".join(f"<figure class=" + chr(34) + "rv" + chr(34) + f">{img(s, f"{name} 마당 {i + 1}", "(min-width: 720px) 33vw, 100vw")}</figure>" for i, s in enumerate([pet["photos"][0], "lawn-lake", "rain-deck"]))}</div></div></section></div>')
page("pet.html", f"반려견 동반 | {name}", f"{name}은 10kg 이하 반려견 2마리까지 무료로 함께 옵니다. 거실과 410평 잔디 마당에서 자유롭게, 침실과 침구는 출입하지 않습니다.",
     pet_body, [{"@context": "https://schema.org", "@type": "WebPage", "name": f"{name} 반려견 안내", "url": f"{base}/pet.html", "description": pet["lead"]}, crumbs("pet.html", "반려견")], current="pet.html")

# ── 이용 안내 ────────────────────────────────────────────────────────────
guide_body = (f'<div class="page"><div class="wrap phead"><h1>요금과 이용 안내</h1><p class="lead">기준 인원 {cap["base"]}명, 최대 {cap["max"]}명. 입실 {cfg["checkin"]}, 퇴실 {cfg["checkout"]}. 날짜와 인원을 보내 주시면 빈 날짜와 요금을 바로 답합니다.</p></div>'
              f'<div class="book" id="book" style="border-top:1px solid var(--line)"><div class="wrap">{book_form()}</div></div>'
              f'<section><div class="wrap"><div class="rates"><div><h2 style="margin-bottom:20px">1박 요금</h2><table>{rates_rows}</table><p class="note">{escape(cfg["rate_note"])}</p></div>'
              f'<div><h2 style="margin-bottom:20px">추가 요금</h2><div class="extras">{extras_html}</div></div></div></div></section>'
              f'<section><div class="wrap"><div class="head"><h2>이용 규칙</h2></div><dl class="rules" style="max-width:46em">{"".join(f"<div><dt>{escape(k)}</dt><dd>{escape(v)}</dd></div>" for k, v in cfg["rules"])}</dl></div></section>'
              f'<section><div class="wrap"><div class="head"><h2>자주 묻는 질문</h2></div><div class="faq">{faq_html(cfg["faq"])}</div></div></section></div>')
page("guide.html", f"요금과 이용 안내 | {name}", f"{name} 1박 요금, 인원 추가와 바비큐, 불멍 장작 요금, 입실과 퇴실 시간, 이용 규칙. 기준 {cap['base']}명 최대 {cap['max']}명.",
     guide_body, [faq_ld(cfg["faq"]), crumbs("guide.html", "이용 안내")], current="guide.html")

# ── 오시는 길 ────────────────────────────────────────────────────────────
# 제천에서 머무는 법 — config "jecheon" (십경·축제와 문화·먹을 곳·공식 안내). 값은 공식 페이지에서 확인한 것만, 빈 절은 안 나옴
J = cfg.get("jecheon", {})
ext = lambda items: ('<div class="ext">' + "".join(
    f'<a href="{escape(u)}" target="_blank" rel="noopener"><span><b>{escape(n)}</b><span>{escape(d)}</span></span><small>{escape(re.sub(r"^https?://(www\.)?", "", u).split("/")[0])}</small></a>'
    for n, d, u in items) + "</div>") if items else ""


def jsec(title, lead, body):
    return f'<section class="jsec"><div class="wrap"><div class="head"><h2>{escape(title)}</h2>{"<p class=" + chr(34) + "lead" + chr(34) + ">" + escape(lead) + "</p>" if lead else ""}</div>{body}</div></section>' if body else ""


ten_html = ('<ol class="ten">' + "".join(f'<li><span><b>{"<a href=" + chr(34) + escape(u) + chr(34) + " target=" + chr(34) + "_blank" + chr(34) + " rel=" + chr(34) + "noopener" + chr(34) + ">" + escape(n) + "</a>" if u else escape(n)}</b><span>{escape(d)}</span></span><em>{escape(m)}</em></li>' for n, d, m, u in J.get("ten", [])) + "</ol>"
            + (f'<p class="jnote"><a class="link" href="{escape(J["ten_url"])}" target="_blank" rel="noopener">제천시 문화관광 누리집의 제천 10경 안내</a></p>' if J.get("ten_url") else "")) if J.get("ten") else ""
food_html = ((f'<p class="jnote" style="margin:0 0 22px">{escape(J["food_intro"])}</p>' if J.get("food_intro") else "") + ext(J.get("food", []))) if J.get("food") else ""
around_body = (f'<div class="page"><div class="wrap phead"><h1>청풍호 옆, 제천에서 머무는 법</h1><p class="lead">{escape(addr)}. {escape(", ".join(f"{n} {d}" for n, d in cfg["nearby"]))}. 차로 10분 안에 출렁다리와 문화유산단지, 정방사가 있고, 단양까지 30분 안팎입니다.</p>'
               f'<div class="maps"><a class="btn btn-fill" href="{route_url}" target="_blank" rel="noopener">카카오맵 길찾기</a><a class="btn btn-line" href="{naver_map_url}" target="_blank" rel="noopener">네이버 지도</a></div></div>'
               f'<div class="pcover">{img("lawn-lake", f"{name} 마당에서 본 청풍호", "100vw", eager=True)}</div>'
               f'<section class="jsec" style="border-top:0"><div class="wrap"><div class="head"><h2>집에서 차로 10분 안팎</h2><p class="lead">{escape(cfg["around_note"])}</p></div><div class="around">{around_html}</div></div></section>'
               + jsec("제천 10경", J.get("ten_lead", ""), ten_html)
               + jsec("축제와 문화", J.get("culture_lead", ""), ext(J.get("culture", [])))
               + jsec("먹을 곳", J.get("food_lead", ""), food_html)
               + jsec("공식 안내", J.get("links_lead", ""), ext(J.get("links", [])))
               + "</div>")
around_ld = {"@context": "https://schema.org", "@type": "WebPage", "name": f"{name} 오시는 길과 제천 안내", "url": f"{base}/around.html",
             "description": f"{addr}. 제천 10경, 축제와 문화, 먹을 곳, 공식 안내 링크"}
if J.get("ten"):
    around_ld["mainEntity"] = {"@type": "ItemList", "name": "제천 10경", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": n, "description": d} for i, (n, d, _, _u) in enumerate(J["ten"], 1)]}
page("around.html", f"오시는 길과 제천 안내 | {name}", f"{name} 오시는 길. {addr}. 차로 10분 안의 케이블카와 출렁다리, 제천 10경, 음악영화제와 문화재단지, 약채락 먹을 곳, 제천시 공식 안내.",
     around_body, [around_ld, crumbs("around.html", "오시는 길")], current="around.html")

# ── 블로그: posts.json → blog.html, posts/N.html (글해줌이 가장 큰 번호 글을 견본으로 복제) ──
for x in posts:
    title, content, date = x["title"], x.get("content") or "", str(x.get("date") or today)[:10]
    desc = plain(x.get("summary") or content, 150)
    url = f"{base}/posts/{x['id']}.html"
    m = re.search(r'<img[^>]+src="([^"]+)"', content)
    image = (base + "/" + m.group(1)[3:]) if m and m.group(1).startswith("../") else (m.group(1) if m else og_image)
    tags = "".join(f'<span class="blog-tag">#{escape(t)}</span> ' for t in x.get("tags") or [])
    body = (f'<div class="page"><article class="wrap" style="max-width:820px"><header class="phead"><p class="blog-post-meta small"><time datetime="{date}">{date}</time></p>'
            f'<h1>{escape(title)}</h1><p class="blog-card-tags small">{tags}</p></header>'
            f'<div class="blog-post-content" style="padding-bottom:clamp(80px,10vw,140px)">{content}</div>'
            # 「이 글 수정」 — 관리 화면에 들어와 있는 기기(열쇠가 저장된 기기)에서만 보인다
            f'<a class="edit-link" id="editLink" href="{base}/admin.html#{x["id"]}" hidden>이 글 수정</a>'
            f'<script>try{{if(localStorage.getItem("{ADMIN_KEY}"))document.getElementById("editLink").hidden=false}}catch(e){{}}</script>'
            f'<p style="padding-bottom:80px"><a class="link" href="{base}/blog.html">소식 목록으로</a></p></article></div>')
    lds = [{"@context": "https://schema.org", "@type": "Article", "headline": title, "description": desc, "image": image, "datePublished": date, "dateModified": date,
            "author": {"@type": "Organization", "name": name}, "publisher": {"@type": "Organization", "name": name, "logo": {"@type": "ImageObject", "url": f"{base}/favicon.svg"}},
            "mainEntityOfPage": url, "keywords": ", ".join((x.get("tags") or [])[:5]) or title},
           {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
               {"@type": "ListItem", "position": 1, "name": "홈", "item": f"{base}/"}, {"@type": "ListItem", "position": 2, "name": "소식", "item": f"{base}/blog.html"},
               {"@type": "ListItem", "position": 3, "name": title, "item": url}]}]
    page(f"posts/{x['id']}.html", f"{title} | {name}", desc, body, lds, current="blog.html")
    shutil.copy(DIST / "posts" / f"{x['id']}.html", ROOT / "posts" / f"{x['id']}.html")  # 저장소에도 둠 — 글해줌 견본
blog_body = (f'<div class="page"><div class="wrap phead"><h1>소식</h1><p class="lead">청풍호 계절과 집 소식을 적습니다.</p></div>'
             f'<section style="padding-top:0;border-top:0"><div class="wrap"><div class="posts">{"".join(post_card(x) for x in posts) or "<p>첫 글을 준비하고 있습니다.</p>"}</div></div></section></div>')
page("blog.html", f"소식 | {name}", f"{name} 소식과 청풍호 계절 안내 글.", blog_body,
     [{"@context": "https://schema.org", "@type": "CollectionPage", "name": f"{name} 소식", "url": f"{base}/blog.html", "inLanguage": "ko-KR",
       "hasPart": [{"@type": "Article", "headline": x["title"], "url": f"{base}/posts/{x['id']}.html", "datePublished": str(x["date"])[:10]} for x in posts]}, crumbs("blog.html", "소식")], current="blog.html")
if posts_path.exists():
    shutil.copy(posts_path, DIST / "posts.json")
if (ROOT / "images" / "posts").is_dir():
    shutil.copytree(ROOT / "images" / "posts", DIST / "images" / "posts")

# ── 404 ──────────────────────────────────────────────────────────────────
page("404.html", f"페이지를 찾을 수 없습니다 | {name}", "주소가 바뀌었거나 잘못 적혔을 수 있습니다.",
     f'<div class="page"><div class="wrap phead"><h1>그 주소에는 페이지가 없습니다</h1><p class="lead">주소가 바뀌었거나 잘못 적혔을 수 있습니다.</p>'
     f'<div class="maps"><a class="btn btn-fill" href="{base}/">처음으로</a><a class="btn btn-line" href="tel:{tel}">전화 {phone}</a></div></div></div>', [])
(DIST / "404.html").write_text((DIST / "404.html").read_text(encoding="utf-8").replace('<meta name="robots" content="noindex">', "", 1).replace("<title>", '<meta name="robots" content="noindex">\n<title>', 1), encoding="utf-8")

# ── llms.txt · robots · sitemap · 기타 ─────────────────────────────────────
nl = "\n"
(DIST / "llms.txt").write_text(f"""# {name}

> 충북 제천 청풍호 옆 독채 펜션. 대지 {cfg['site_area']}, 집 {cfg['house_area']}를 하루 한 팀이 씁니다. 기준 {cap['base']}명, 최대 {cap['max']}명. 유리 식당(12인 식탁), 개별 바비큐, 불멍, 잔디 마당, 반려견 동반. 회갑·칠순·돌·동창회 모임.

## 기본 정보
- 상호: {name} (다른 표기: {', '.join(cfg['name_alt'])})
- 주소: {addr}
- 전화: {phone}
- 입실 {cfg['checkin']} · 퇴실 {cfg['checkout']}
- 인원: 기준 {cap['base']}명, 최대 {cap['max']}명 (초과 1명당 {cap['extra_fee']})

## 요금 (1박)
{nl.join(f"- {r}: {v or '문의'}" for r, v in cfg['rates'])}
- {cfg['rate_note']}
{nl.join(f"- {k}: {v}" for k, v in cfg['extras'])}

## 공간
{nl.join(f"- {t}: {d}" for t, d, _ in cfg['house_rooms'])}

## 모임
- {gath['lead']}
{nl.join(f"- {n}: {d}" for n, d in gath['seats'])}

## 반려견
{nl.join(f"- {k}: {v}" for k, v in pet['rules'])}

## 이용 규칙
{nl.join(f"- {k}: {v}" for k, v in cfg['rules'])}

## 가까운 곳 (차로)
{nl.join(f"- {n}: {d}, 약 {m}" for n, d, m in cfg['around'])}

## 자주 묻는 질문
{nl.join(f"- Q. {q}{nl}  A. {ans}" for q, ans in cfg['faq'])}

## 채널
{nl.join(f"- {c['name']}: {c['url']}" for c in filled)}

## 글 목록
{nl.join(f"- [{plain(x['title'], 120)}]({base}/posts/{x['id']}.html): {plain(x.get('summary') or x.get('content'), 140)}" for x in posts[:100])}
""", encoding="utf-8")
(DIST / "robots.txt").write_text("User-agent: *\nAllow: /\nDisallow: /admin.html\n" + (f"Sitemap: {domain}/sitemap.xml\n" if domain and not noindex else ""), encoding="utf-8")
# 사장님 관리 화면 — 비밀번호 하나로 config·posts.json을 고치면 Actions가 다시 빌드한다 (공통 지시서 11/8)
(DIST / "admin.html").write_text(fill((T / "admin.html").read_text(encoding="utf-8"), dict(
    name=escape(name), repo=cfg["repo"], branch=cfg["branch"], key=ADMIN_KEY, site=base, maker_phone="010-2468-5662")), encoding="utf-8")
if (ROOT / "admin-key.json").exists():  # 토큰을 비밀번호로 잠근 파일 — 관리 화면이 admin-key.json 으로 읽는다
    shutil.copy(ROOT / "admin-key.json", DIST / "admin-key.json")
if domain and not noindex:
    urls = [(f"{domain}/", today)] + [(f"{domain}/{p}", today) for p, _ in MENU] + [(f"{domain}/posts/{x['id']}.html", str(x['date'])[:10]) for x in posts]
    (DIST / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      + "".join(f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls) + "</urlset>\n", encoding="utf-8")
for k in ROOT.glob("*.txt"):
    if re.fullmatch(r"[0-9a-f]{32}", k.stem):
        shutil.copy(k, DIST / k.name)
for f in (ROOT / "static").iterdir():
    shutil.copy(f, DIST / f.name)
(DIST / ".nojekyll").write_text("", encoding="utf-8")

print(f"완성: {DIST} · 페이지 {len(MENU) + 2}개 · 글 {len(posts)}편")
if noindex:
    print("※ 검색 노출 막힘(noindex) — 도메인이 비었거나 임시 사진이라서. 둘 다 정리되면 자동으로 풀립니다.")
print(f"\n[확인 필요] {len(todo_list)}개")
for t in dict.fromkeys(todo_list):
    print(" -", t)
