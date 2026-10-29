#!/usr/bin/env python3
"""Build the West Alexandria Dental Care static site.

    python3 src/build.py            # writes ../site/
    python3 src/build.py --check    # build + report broken internal links

Everything about the practice (name, phone, hours, nav, page registry) lives in site.json.
Every content page lives in content/<slug>.json. This script renders them with one shared layout.
"""
import json, os, re, sys, shutil, glob, html, datetime
from collections import OrderedDict

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(ROOT), "site")
SITE = json.load(open(os.path.join(ROOT, "site.json"), encoding="utf-8"))
PAGES = OrderedDict((p["slug"], p) for p in SITE["pages"])
CONTENT = {}
for f in glob.glob(os.path.join(ROOT, "content", "**", "*.json"), recursive=True):
    try:
        d = json.load(open(f, encoding="utf-8"))
        CONTENT[d["slug"]] = d
    except Exception as e:
        print(f"WARN cannot load {f}: {e}")

PHONE = SITE["phone"]; TEL = SITE["phone_tel"]; BOOK = SITE["book_url"]; FORMS = SITE["forms_url"]
ADDR = SITE["address"]; HOURS = SITE["hours"]; NAME = SITE["name"]; DOMAIN = SITE["domain"].rstrip("/")
DENTIST_PHOTOS = {"/dentists/dr-sameer-atrash/": "dr-sameer-atrash.jpg", "/dentists/dr-fadi-alhrashi/": "dr-fadi-alhrashi.webp"}
HUB_ICONS = {"/general-dentistry/": "tooth", "/restorative-dentistry/": "repair", "/cosmetic-dentistry/": "sparkle", "/dental-implants/": "implant", "/clear-aligners/": "aligner", "/emergency-dentistry/": "emergency", "/sedation-dentistry/": "moon", "/symptoms/": "pulse", "/new-patients/": "calendar", "/areas/": "map"}
HUB_ORDER = ["/general-dentistry/", "/restorative-dentistry/", "/cosmetic-dentistry/", "/dental-implants/", "/clear-aligners/", "/emergency-dentistry/", "/sedation-dentistry/"]
BROKEN = []

# --------------------------------------------------------------------------- photos
# photos.json maps a named slot to a file in assets/img/photos/. Swap the file to replace a placeholder.
PHOTOS_PATH = os.path.join(ROOT, "photos.json")
PHOTOS = json.load(open(PHOTOS_PATH, encoding="utf-8")) if os.path.exists(PHOTOS_PATH) else {}
SLOT_BY_PREFIX = [
    ("/general-dentistry/childrens-dentistry/", "cat-children"), ("/general-dentistry/dental-care-for-seniors/", "cat-seniors"),
    ("/general-dentistry/family-dentistry/", "cat-family"), ("/clear-aligners/for-teens/", "cat-teens"),
    ("/general-dentistry/", "cat-general"), ("/restorative-dentistry/", "cat-restorative"), ("/cosmetic-dentistry/", "cat-cosmetic"),
    ("/dental-implants/", "cat-implants"), ("/clear-aligners/", "cat-aligners"), ("/emergency-dentistry/", "cat-emergency"),
    ("/sedation-dentistry/", "cat-sedation"), ("/symptoms/", "cat-symptoms"), ("/new-patients/", "cat-new-patients"),
    ("/areas/", "cat-areas"), ("/about/", "cat-about"), ("/blog/what-counts-as-a-dental-emergency/", "cat-emergency"),
    ("/blog/how-often-dental-cleanings/", "cat-general"), ("/blog/dental-anxiety-comfort-options/", "cat-sedation"),
    ("/blog/evening-and-weekend-dentist-alexandria/", "home-hours"), ("/blog/dental-care-for-the-whole-family-one-office/", "cat-family"),
    ("/blog/what-to-expect-first-visit-new-dentist/", "cat-new-patients"), ("/blog/", "cat-blog"), ("/faq/", "cat-new-patients"),
    ("/dental-dictionary/", "cat-blog"), ("/services/", "home-approach"), ("/book-online/", "cat-new-patients"), ("/contact/", "contact-exterior"),
]

def photo(slot):
    p = PHOTOS.get(slot)
    if not p or not os.path.exists(os.path.join(ROOT, "assets", "img", "photos", p["file"])):
        return None
    return p

def photo_img(slot, cls="", loading="lazy", sizes="(max-width: 900px) 100vw, 50vw"):
    p = photo(slot)
    if not p: return ""
    base = "/assets/img/photos/"
    srcset = ""
    if p.get("file_sm"):
        srcset = f' srcset="{base}{p["file_sm"]} {p.get("width_sm", 900)}w, {base}{p["file"]} {p.get("width", 1600)}w" sizes="{sizes}"'
    dims = f' width="{p["width"]}" height="{p["height"]}"' if p.get("width") and p.get("height") else ""
    fp = ' fetchpriority="high"' if loading == "eager" else ""
    return (f'<img class="{cls}" src="{base}{p["file"]}"{srcset}{dims} alt="{esc(p.get("alt", ""))}" loading="{loading}"{fp}'
            f' style="object-position:{esc(p.get("position", "50% 50%"))}">')

def slot_for(slug):
    for pre, s in SLOT_BY_PREFIX:
        if slug and slug.startswith(pre): return s
    return None

def hero_media(slug):
    s = slot_for(slug)
    if not s or not photo(s): return ""
    return f'<div class="page-hero__media hero__media"><div class="arch arch--photo">{photo_img(s, loading="eager")}</div></div>'

# --------------------------------------------------------------------------- helpers

def esc(s):
    return html.escape(str(s), quote=True)

def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "section"

_link_re = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_bold_re = re.compile(r"\*\*(.+?)\*\*")

def href_for(h):
    if h == "tel": return f"tel:{TEL}"
    if h == "book": return BOOK
    if h == "forms": return FORMS
    return h

def inline(s):
    """Escape then apply the tiny inline markup allowed in content strings."""
    if s is None: return ""
    t = esc(s)
    t = t.replace("{{phone}}", f'<a href="tel:{TEL}">{PHONE}</a>')
    t = t.replace("{{book}}", f'<a href="{BOOK}" target="_blank" rel="noopener">book online</a>')
    t = t.replace("{{forms}}", f'<a href="{FORMS}" target="_blank" rel="noopener">patient registration page</a>')
    def rep(m):
        text, href = m.group(1), m.group(2)
        if href.startswith("/") and href not in PAGES:
            BROKEN.append(href)
        ext = href.startswith("http")
        attrs = ' target="_blank" rel="noopener"' if ext else ""
        return f'<a href="{esc(href_for(href))}"{attrs}>{text}</a>'
    t = _link_re.sub(rep, t)
    t = _bold_re.sub(r"<strong>\1</strong>", t)
    return t

def icon(name, cls="icon"):
    return f'<svg class="{cls}" aria-hidden="true"><use href="/assets/img/icons.svg#i-{name}"></use></svg>'

def btn(label, href, style="primary", ico=None, extra=""):
    h = href_for(href)
    ext = h.startswith("http")
    attrs = ' target="_blank" rel="noopener"' if ext else ""
    i = icon(ico) if ico else ""
    return f'<a class="btn btn--{style}{(" " + extra) if extra else ""}" href="{esc(h)}"{attrs}>{i}<span>{esc(label)}</span></a>'

def title_of(slug):
    p = PAGES.get(slug); c = CONTENT.get(slug)
    return (c or p or {}).get("title", slug)

def children_of(slug):
    return [p for p in SITE["pages"] if p.get("parent") == slug]

def first_sentence(s, n=150):
    s = (s or "").strip()
    parts = re.findall(r".+?[.!?](?=\s|$)", s)
    out = parts[0] if parts else s
    if len(out) < 60 and len(parts) > 1:
        out = out + " " + parts[1].strip()
    if len(out) > n:
        out = out[:n].rsplit(" ", 1)[0] + "…"
    return out

def plain(s):
    """Strip the inline markup (links, bold, tokens) for use in attributes and card blurbs."""
    s = _link_re.sub(r"\1", s or "")
    s = _bold_re.sub(r"\1", s)
    return s.replace("{{phone}}", PHONE).replace("{{book}}", "book online").replace("{{forms}}", "patient registration page")

def blurb(slug):
    c = CONTENT.get(slug)
    if not c: return ""
    return first_sentence(plain(c.get("intro") or c.get("meta_description") or ""))

def page_icon(slug, default="tooth"):
    c = CONTENT.get(slug)
    return (c or {}).get("icon") or HUB_ICONS.get(slug) or default

def status_pill(cls="status"):
    return f'<span class="{cls}" data-status><span class="status__dot"></span><span data-status-text>Open seven days a week</span></span>'

def hours_table(light=False):
    rows = "".join(f'<tr><td>{h["day"]}</td><td>{h["open"]} – {h["close"]}</td></tr>' for h in HOURS)
    return f'<table class="hours-table{" hours-table--light" if light else ""}" data-hours-table><tbody>{rows}</tbody></table>'

def address_block():
    return f'{esc(ADDR["building"])}<br>{esc(ADDR["street"])}<br>{esc(ADDR["city"])}, {esc(ADDR["state"])} {esc(ADDR["zip"])}'

# --------------------------------------------------------------------------- chrome

def more_cls(label):
    return ' class="is-more"' if label.endswith("→") else ""

def cur_cls(flag):
    return ' class="is-current"' if flag else ""

def nav_panel_column(col):
    out = []
    def group(heading, href, links):
        lis = "".join(f'<li><a href="{esc(l[1])}"{more_cls(l[0])}>{esc(l[0])}</a></li>' for l in links)
        return f'<div><div class="panel__heading"><a href="{esc(href)}">{esc(heading)}</a></div><ul class="panel__list">{lis}</ul></div>'
    def links_for(c):
        if c.get("links"): return c["links"]
        kids = children_of(c["children"])
        return [[k["title"], k["slug"]] for k in kids]
    out.append(group(col["heading"], col["href"], links_for(col)))
    if col.get("then"):
        t = col["then"]
        out.append(group(t["heading"], t["href"], links_for(t)))
    return f'<div class="mega__col">{"".join(out)}</div>'

def header_html(current):
    items = []
    for n in SITE["nav"]:
        if n.get("mega"):
            cols = "".join(nav_panel_column(c) for c in n["columns"])
            feature = (f'<div class="mega__feature"><h4>Not sure where to start?</h4><p>Tell us what is happening and we will help you find the right place to begin. You do not need to know the dental term.</p>'
                       f'{btn("Browse by symptom", "/symptoms/", "light", "arrow-right", "btn--sm")}'
                       f'<div class="mega__emg">{icon("alert")}<span>Something hurts? <a href="tel:{TEL}">Call {PHONE}</a></span></div></div>')
            items.append(f'<li class="nav__item nav__item--has-panel"><button class="nav__link" type="button" aria-expanded="false" aria-haspopup="true">{esc(n["label"])}{icon("chevron-down")}</button>'
                         f'<div class="panel panel--mega">{feature}<div class="mega__cols">{cols}</div></div></li>')
        elif n.get("dropdown"):
            groups = "".join(f'<div class="panel__group"><div class="panel__heading">{esc(g["heading"])}</div><ul class="panel__list">' + "".join(f'<li><a href="{esc(l[1])}">{esc(l[0])}</a></li>' for l in g["links"]) + "</ul></div>" for g in n["groups"])
            items.append(f'<li class="nav__item nav__item--has-panel"><button class="nav__link" type="button" aria-expanded="false" aria-haspopup="true">{esc(n["label"])}{icon("chevron-down")}</button><div class="panel panel--drop">{groups}</div></li>')
        else:
            cur = ' is-current' if current == n["href"] else ""
            items.append(f'<li class="nav__item"><a class="nav__link{cur}" href="{esc(n["href"])}">{esc(n["label"])}</a></li>')
    brand = (f'<a class="brand" href="/" aria-label="{esc(NAME)} home"><img class="brand__mark" src="/assets/img/logo-mark.svg" alt="" width="46" height="46">'
             f'<span class="brand__text"><span class="brand__name">West Alexandria</span><span class="brand__sub">Dental Care</span></span></a>')
    topbar = (f'<div class="topbar"><div class="container"><div class="topbar__left"><span class="dot"></span><span>{esc(SITE["announcement"])}</span></div>'
              f'<div class="topbar__right">{status_pill()}<a class="hide-sm" href="{esc(FORMS)}" target="_blank" rel="noopener">Patient forms</a><a href="tel:{TEL}">Call {PHONE}</a></div></div></div>')
    header = (f'<header class="header"><div class="container header__inner">{brand}<nav class="nav" aria-label="Primary"><ul class="nav__list">{"".join(items)}</ul></nav>'
              f'<div class="header__cta"><a class="header__phone" href="tel:{TEL}">{icon("phone")}<span>{PHONE}</span></a>{btn("Book online", "book", "primary", None, "btn--sm")}'
              f'<button class="burger" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="drawer">{icon("menu")}</button></div></div></header>')
    return topbar + header

def drawer_html():
    groups = []
    for n in SITE["nav"]:
        if n.get("mega"):
            subs = []
            for c in n["columns"]:
                for cc in [c] + ([c["then"]] if c.get("then") else []):
                    links = cc.get("links") or [[k["title"], k["slug"]] for k in children_of(cc["children"])]
                    subs.append(f'<div><div class="panel__heading"><a href="{esc(cc["href"])}">{esc(cc["heading"])}</a></div><ul class="panel__list">' + "".join(f'<li><a href="{esc(l[1])}">{esc(l[0])}</a></li>' for l in links) + "</ul></div>")
            groups.append(f'<details class="drawer__group"><summary>{esc(n["label"])}{icon("chevron-down")}</summary><div class="drawer__sub">{"".join(subs)}</div></details>')
        elif n.get("dropdown"):
            subs = "".join(f'<div><div class="panel__heading">{esc(g["heading"])}</div><ul class="panel__list">' + "".join(f'<li><a href="{esc(l[1])}">{esc(l[0])}</a></li>' for l in g["links"]) + "</ul></div>" for g in n["groups"])
            groups.append(f'<details class="drawer__group"><summary>{esc(n["label"])}{icon("chevron-down")}</summary><div class="drawer__sub">{subs}</div></details>')
        else:
            groups.append(f'<a class="drawer__link" href="{esc(n["href"])}">{esc(n["label"])}{icon("chevron-right")}</a>')
    return (f'<div class="drawer" id="drawer" aria-hidden="true"><div class="drawer__scrim" data-drawer-close></div><div class="drawer__panel" role="dialog" aria-modal="true" aria-label="Menu">'
            f'<div class="drawer__head"><span class="brand__name">Menu</span><button class="drawer__close" type="button" aria-label="Close menu" data-drawer-close>{icon("x")}</button></div>'
            f'<div class="drawer__body"><a class="drawer__link" href="/">Home{icon("chevron-right")}</a>{"".join(groups)}<a class="drawer__link" href="{esc(FORMS)}" target="_blank" rel="noopener">Patient forms{icon("arrow-up-right")}</a></div>'
            f'<div class="drawer__foot">{btn("Book online", "book", "primary", "calendar", "btn--block")}{btn("Call " + PHONE, "tel", "ghost", "phone", "btn--block")}<div class="drawer__hours">Mon–Fri 7 AM–8 PM · Sat–Sun 8 AM–1 PM</div></div></div></div>')

def footer_html():
    cols = "".join(f'<div><h4>{esc(c["heading"])}</h4><ul>' + "".join(f'<li><a href="{esc(l[1])}">{esc(l[0])}</a></li>' for l in c["links"]) + "</ul></div>" for c in SITE["footer"])
    brand = (f'<a class="brand" href="/"><img class="brand__mark" src="/assets/img/logo-mark.svg" alt="" width="46" height="46"><span class="brand__text"><span class="brand__name">West Alexandria</span><span class="brand__sub">Dental Care</span></span></a>')
    contact = (f'<div class="footer__contact"><div>{icon("pin")}<span>{address_block()}</span></div><div>{icon("phone")}<a href="tel:{TEL}">{PHONE}</a></div>'
               f'<div>{icon("directions")}<a href="{esc(ADDR["directions"])}" target="_blank" rel="noopener">Get directions</a></div><div>{icon("calendar")}<a href="{esc(BOOK)}" target="_blank" rel="noopener">Book online, any hour</a></div></div>')
    year = datetime.date.today().year
    return (f'<footer class="footer"><div class="container"><div class="footer__grid">'
            f'<div>{brand}<p class="footer__about">Comprehensive family, restorative and cosmetic dentistry in the Bradlee Office Building, led by Dr. Sameer Atrash and Dr. Fadi Alhrashi. Open seven days a week.</p><div style="margin-top:18px">{status_pill()}</div></div>'
            f'{cols}<div><h4>Hours</h4><table class="hours-table footer__hours" data-hours-table><tbody>' + "".join(f'<tr><td>{h["day"][:3]}</td><td>{h["open"]} – {h["close"]}</td></tr>' for h in HOURS) + f'</tbody></table><div style="margin-top:18px">{contact}</div></div></div>'
            f'<div class="footer__bottom"><div>© {year} {esc(NAME)} · {esc(SITE["legal"])}</div><nav><a href="/privacy/">Privacy</a><a href="/accessibility/">Accessibility</a><a href="/contact/">Contact</a></nav></div></div></footer>')

def sticky_cta():
    return f'<div class="sticky-cta">{btn("Call now", "tel", "ghost", "phone")}{btn("Book online", "book", "primary", "calendar")}</div>'

def jsonld_org():
    return {
        "@context": "https://schema.org", "@type": "Dentist", "@id": DOMAIN + "/#dentist",
        "name": NAME, "legalName": SITE["legal"], "url": DOMAIN + "/", "telephone": "+1-" + PHONE, "email": SITE.get("email", ""),
        "image": DOMAIN + "/assets/img/og.jpg", "logo": DOMAIN + "/assets/img/icon-512.png",
        "address": {"@type": "PostalAddress", "streetAddress": ADDR["street"], "addressLocality": ADDR["city"], "addressRegion": ADDR["state"], "postalCode": ADDR["zip"], "addressCountry": "US"},
        "geo": {"@type": "GeoCoordinates", "latitude": ADDR["lat"], "longitude": ADDR["lng"]},
        "openingHoursSpecification": [
            {"@type": "OpeningHoursSpecification", "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], "opens": "07:00", "closes": "20:00"},
            {"@type": "OpeningHoursSpecification", "dayOfWeek": ["Saturday", "Sunday"], "opens": "08:00", "closes": "13:00"}],
        "areaServed": SITE["neighborhoods"], "availableLanguage": SITE["languages"],
        "employee": [{"@type": "Person", "name": "Dr. Sameer Atrash", "jobTitle": "Owner and general dentist", "url": DOMAIN + "/dentists/dr-sameer-atrash/"},
                      {"@type": "Person", "name": "Dr. Fadi Alhrashi", "jobTitle": "General dentist", "url": DOMAIN + "/dentists/dr-fadi-alhrashi/"}],
        "potentialAction": {"@type": "ReserveAction", "target": BOOK, "name": "Book online"},
    }

def jsonld_crumbs(trail):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": t, "item": DOMAIN + s} for i, (t, s) in enumerate(trail)]}

def jsonld_faq(faqs):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", inline(f["a"]))}} for f in faqs]}

def layout(slug, title, description, body, jsonld=None, og_image=None, og_type="website"):
    canonical = DOMAIN + slug
    ld = [jsonld_org()] + (jsonld or [])
    ld_html = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)
    hours_js = json.dumps([{"o": h["o"], "c": h["c"]} for h in HOURS])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{esc(NAME)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(og_image or DOMAIN + '/assets/img/og.jpg')}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#17343e">
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/assets/img/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400;1,6..72,500&display=swap">
<link rel="stylesheet" href="/assets/css/main.css">
<script>window.WADC={{hours:{hours_js}}};</script>
{ld_html}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{header_html(slug)}
{drawer_html()}
<main id="main">
{body}
</main>
{footer_html()}
{sticky_cta()}
<script src="/assets/js/main.js" defer></script>
</body>
</html>
"""

# --------------------------------------------------------------------------- content blocks

def render_block(b, idx):
    t = b.get("type"); h = b.get("heading", ""); hid = slugify(h) or f"section-{idx}"
    head = f'<h2 id="{hid}">{inline(h)}</h2>' if h else ""
    intro = f'<p class="block__intro">{inline(b["intro"])}</p>' if b.get("intro") else ""
    if t == "prose":
        return f'<section class="block prose" id="s-{hid}">{head}' + "".join(f"<p>{inline(p)}</p>" for p in b.get("body", [])) + "</section>"
    if t == "steps":
        lis = "".join(f'<li><h3>{inline(i["title"])}</h3><p>{inline(i["body"])}</p></li>' for i in b.get("items", []))
        return f'<section class="block" id="s-{hid}">{head}{intro}<ol class="steps-v">{lis}</ol></section>'
    if t == "list":
        style = b.get("style", "bullet"); ic = {"check": "check", "warn": "alert", "bullet": "dot"}.get(style, "dot")
        lis = "".join(f"<li>{icon(ic)}<span>{inline(i)}</span></li>" for i in b.get("items", []))
        return f'<section class="block" id="s-{hid}">{head}{intro}<ul class="list list--{style}">{lis}</ul></section>'
    if t == "cards":
        cards = []
        for i in b.get("items", []):
            href = i.get("href")
            if href and href.startswith("/") and href not in PAGES: BROKEN.append(href)
            inner = f'<h3>{inline(i["title"])}</h3><p>{inline(i["body"])}</p>'
            if href:
                cards.append(f'<a class="card card--link" href="{esc(href_for(href))}">{inner}<span class="card__arrow">Learn more {icon("arrow-right")}</span></a>')
            else:
                cards.append(f'<div class="card">{inner}</div>')
        return f'<section class="block" id="s-{hid}">{head}{intro}<div class="cards-2">{"".join(cards)}</div></section>'
    if t == "compare":
        cols = b.get("columns", []); rows = b.get("rows", [])
        thead = "<tr><th></th>" + "".join(f"<th>{inline(c)}</th>" for c in cols) + "</tr>"
        tbody = "".join("<tr><th scope=\"row\">" + inline(r[0]) + "</th>" + "".join(f"<td>{inline(c)}</td>" for c in r[1:]) + "</tr>" for r in rows)
        return f'<section class="block" id="s-{hid}">{head}{intro}<div class="table-wrap"><table class="compare"><thead>{thead}</thead><tbody>{tbody}</tbody></table></div></section>'
    if t == "callout":
        tone = b.get("tone", "info"); cta = b.get("cta")
        ic = icon("alert") if tone == "urgent" else ""
        c = btn(cta["label"], cta["href"], "primary", None, "btn--sm") if cta else ""
        if cta and cta["href"].startswith("/") and cta["href"] not in PAGES: BROKEN.append(cta["href"])
        return f'<section class="block" id="s-{hid}"><div class="callout callout--{tone}"><h2 id="{hid}">{ic}{inline(h)}</h2><p>{inline(b.get("body", ""))}</p>{c}</div></section>'
    return ""

def render_faqs(faqs, heading="Straight answers"):
    if not faqs: return ""
    items = "".join(f'<details class="faq__item"><summary class="faq__q"><span>{inline(f["q"])}</span><span class="plus">{icon("plus")}</span></summary><div class="faq__a"><p>{inline(f["a"])}</p></div></details>' for f in faqs)
    return f'<section class="block" id="s-questions"><h2 id="questions">{esc(heading)}</h2><div class="faq">{items}</div></section>'

def related_cards(slugs, heading="Related reading"):
    slugs = [s for s in slugs if s in PAGES]
    if not slugs: return ""
    cards = "".join(f'<a class="card card--link card--sm" href="{esc(s)}"><span class="card__icon">{icon(page_icon(s))}</span><h3>{esc(title_of(s))}</h3><p>{esc(blurb(s))}</p><span class="card__arrow">Read {icon("arrow-right")}</span></a>' for s in slugs)
    return f'<section class="section section--tight"><div class="container"><div class="section__head"><span class="eyebrow">Keep reading</span><h2>{esc(heading)}</h2></div><div class="related reveal-stagger">{cards}</div></div></section>'

def cta_band(cta, slug=""):
    heading = (cta or {}).get("heading") or "Ready when you are."
    body = (cta or {}).get("body") or "Whether you are due for a cleaning, dealing with pain or thinking about your smile, the first step is simply a conversation."
    return (f'<section class="section section--tight"><div class="container"><div class="cta-band reveal"><div><span class="eyebrow eyebrow--plain" style="color:var(--sky)">Your new dental home</span><h2>{inline(heading)}</h2><p>{inline(body)}</p>'
            f'<div class="btn-row">{btn("Book online", "book", "light", "calendar")}{btn("Call " + PHONE, "tel", "outline-light", "phone")}</div></div>'
            f'<div class="cta-band__aside"><div><strong>Hours</strong>{status_pill()}<div class="small" style="color:#b9cbd2;margin-top:6px">Mon–Fri 7:00 AM–8:00 PM<br>Sat–Sun 8:00 AM–1:00 PM</div></div>'
            f'<div><strong>Visit</strong>{address_block()}<br><a href="{esc(ADDR["directions"])}" target="_blank" rel="noopener">Get directions ↗</a></div>'
            f'<div><strong>Before you come</strong><a href="{esc(FORMS)}" target="_blank" rel="noopener">Complete patient paperwork ↗</a></div></div></div></div></section>')

def crumbs(trail):
    parts = [f'<a href="/">Home</a>']
    for i, (t, s) in enumerate(trail):
        parts.append(icon("chevron-right"))
        if i == len(trail) - 1: parts.append(f'<span aria-current="page">{esc(t)}</span>')
        else: parts.append(f'<a href="{esc(s)}">{esc(t)}</a>')
    return f'<nav class="crumbs container" aria-label="Breadcrumb">{"".join(parts)}</nav>'

def trail_for(slug):
    trail = []; s = slug
    while s and s in PAGES:
        p = PAGES[s]; trail.append((title_of(s), s)); s = p.get("parent")
    return list(reversed(trail))

def book_card(urgent=False):
    return (f'<div class="aside__card aside__card--navy"><h4>Book a visit</h4>{status_pill()}<div class="small">Mon–Fri 7 AM–8 PM<br>Sat–Sun 8 AM–1 PM</div>'
            f'<div class="btn-row">{btn("Book online", "book", "light", "calendar", "btn--sm")}{btn("Call " + PHONE, "tel", "outline-light", "phone", "btn--sm")}</div></div>')

def emergency_card():
    return (f'<div class="aside__card aside__card--rose"><h4>Something hurts now?</h4><p>Call us first and we will plan the visit with you. We keep room in the schedule for urgent problems, seven days a week.</p>'
            f'<div style="margin-top:12px">{btn("Call " + PHONE, "tel", "primary", "phone", "btn--sm")}</div></div>')

def toc(sections, faqs):
    heads = [(slugify(s["heading"]), s["heading"]) for s in sections if s.get("heading")]
    if faqs: heads.append(("questions", "Straight answers"))
    if len(heads) < 3: return ""
    return '<div class="aside__card toc"><h4>On this page</h4><ol>' + "".join(f'<li><a href="#{h}">{esc(t)}</a></li>' for h, t in heads) + "</ol></div>"

def siblings_card(slug):
    p = PAGES.get(slug, {}); parent = p.get("parent")
    if not parent: return ""
    kids = children_of(parent)
    if len(kids) < 2: return ""
    lis = "".join(f'<li><a href="{esc(k["slug"])}"{cur_cls(k["slug"] == slug)}>{esc(k["title"])}</a></li>' for k in kids)
    return f'<div class="aside__card siblings"><h4><a href="{esc(parent)}">{esc(title_of(parent))}</a></h4><ul>{lis}</ul></div>'

def facts_html(facts):
    if not facts: return ""
    return '<div class="facts">' + "".join(f'<div class="fact"><div class="fact__label">{esc(f["label"])}</div><div class="fact__value">{esc(f["value"])}</div></div>' for f in facts) + "</div>"

# --------------------------------------------------------------------------- page types

def page_hero(c, media_html=None, show_icon=True, extra=""):
    if media_html is None:
        media_html = hero_media(c.get("slug", ""))
    single = "" if media_html else " page-hero__grid--single"
    ic = f'<div class="page-hero__icon">{icon(c.get("icon") or "tooth")}</div>' if show_icon and c.get("icon") else ""
    return (f'<section class="page-hero"><div class="blobs"><div class="blob blob--sky blob--a" style="width:520px;height:520px;right:-140px;top:-200px"></div><div class="blob blob--gold blob--b" style="width:380px;height:380px;left:-160px;bottom:-200px"></div></div>'
            f'<div class="container"><div class="page-hero__grid{single}"><div class="hero-in">{ic}<span class="eyebrow">{esc(c.get("eyebrow", ""))}</span><h1>{inline(c["h1"])}</h1><p class="lede">{inline(c["intro"])}</p>'
            f'<div class="btn-row">{btn("Book online", "book", "primary", "calendar")}{btn("Call " + PHONE, "tel", "ghost", "phone")}</div>{extra}{facts_html(c.get("facts"))}</div>{media_html}</div></div></section>')

def render_standard(c):
    slug = c["slug"]; t = c["type"]
    media = None
    if t == "dentist" and slug in DENTIST_PHOTOS:
        media = f'<div class="page-hero__media hero__media"><div class="arch arch--ring"><img src="/assets/img/{DENTIST_PHOTOS[slug]}" alt="{esc(c["title"])}" width="707" height="800" loading="eager" fetchpriority="high"></div></div>'
    blocks = "".join(render_block(b, i) for i, b in enumerate(c.get("sections", [])))
    faqs = render_faqs(c.get("faqs", []))
    aside_parts = [toc(c.get("sections", []), c.get("faqs")), book_card()]
    if t == "symptom" or slug.startswith("/emergency-dentistry/"): aside_parts.insert(1, emergency_card())
    aside_parts.append(siblings_card(slug))
    body = (crumbs(trail_for(slug)) + page_hero(c, media) +
            f'<section class="section section--tight section--paper"><div class="container"><div class="layout"><article class="main">{blocks}{faqs}</article><aside class="aside">{"".join(aside_parts)}</aside></div></div></section>' +
            related_cards(c.get("related", [])) + cta_band(c.get("cta"), slug))
    ld = [jsonld_crumbs([("Home", "/")] + trail_for(slug))]
    if c.get("faqs"): ld.append(jsonld_faq(c["faqs"]))
    if t == "dentist":
        ld.append({"@context": "https://schema.org", "@type": "Person", "name": c["title"], "jobTitle": "General dentist", "worksFor": {"@id": DOMAIN + "/#dentist"}, "url": DOMAIN + slug, "image": DOMAIN + "/assets/img/" + DENTIST_PHOTOS.get(slug, "og.jpg")})
    return layout(slug, c["meta_title"], c["meta_description"], body, ld)

def render_hub(c):
    slug = c["slug"]
    kids = children_of(slug)
    cards = "".join(f'<a class="card card--link card--sm" href="{esc(k["slug"])}"><span class="card__icon">{icon(page_icon(k["slug"]))}</span><h3>{esc(k["title"])}</h3><p>{esc(blurb(k["slug"]))}</p><span class="card__arrow">Read more {icon("arrow-right")}</span></a>' for k in kids)
    blocks = "".join(render_block(b, i) for i, b in enumerate(c.get("sections", [])))
    faqs = render_faqs(c.get("faqs", []))
    extra_kids = ""
    if slug == "/symptoms/":
        em = [k for k in children_of("/emergency-dentistry/") if k["slug"] != "/emergency-dentistry/after-hours/"]
        extra_kids = (f'<div class="section__head" style="margin-top:48px"><span class="eyebrow">Urgent</span><h2>Emergency guides</h2></div><div class="children reveal-stagger">' +
                      "".join(f'<a class="card card--link card--sm" href="{esc(k["slug"])}"><span class="card__icon" style="background:var(--rose-soft);color:var(--rose)">{icon("alert")}</span><h3>{esc(k["title"])}</h3><p>{esc(blurb(k["slug"]))}</p><span class="card__arrow">Read more {icon("arrow-right")}</span></a>' for k in em) + "</div>")
    body = (crumbs(trail_for(slug)) + page_hero(c) +
            f'<section class="section section--tight section--paper"><div class="container"><div class="section__head"><span class="eyebrow">In this section</span><h2>{esc(c["title"])}, page by page</h2></div><div class="children reveal-stagger">{cards}</div>{extra_kids}</div></section>' +
            f'<section class="section section--tight"><div class="container"><div class="layout"><article class="main">{blocks}{faqs}</article><aside class="aside">{toc(c.get("sections", []), c.get("faqs"))}{book_card()}{emergency_card() if slug in ("/emergency-dentistry/", "/symptoms/") else ""}</aside></div></div></section>' +
            cta_band(c.get("cta"), slug))
    ld = [jsonld_crumbs([("Home", "/")] + trail_for(slug))]
    if c.get("faqs"): ld.append(jsonld_faq(c["faqs"]))
    return layout(slug, c["meta_title"], c["meta_description"], body, ld)

def fmt_date(iso):
    try: return datetime.date.fromisoformat(iso).strftime("%B %-d, %Y")
    except Exception: return iso

def articles_sorted():
    arts = [c for c in CONTENT.values() if c.get("type") == "article"]
    return sorted(arts, key=lambda a: a.get("date", ""), reverse=True)

def post_card(a, feature=False, num=None):
    n = f'<span class="card__num">{num:02d}</span>' if num else ""
    return (f'<a class="post{" post--feature" if feature else ""}" href="{esc(a["slug"])}"><div class="post__meta">{n}<span>{esc(a.get("category", ""))}</span></div><h3>{esc(a["title"])}</h3><p>{esc(plain(a.get("summary") or first_sentence(a.get("intro", ""), 180)))}</p>'
            f'<div class="post__foot"><span>{esc(fmt_date(a.get("date", "")))}</span><span>{esc(a.get("read_time", ""))}</span></div></a>')

def render_article(c):
    slug = c["slug"]
    blocks = "".join(render_block(b, i) for i, b in enumerate(c.get("sections", [])))
    faqs = render_faqs(c.get("faqs", []), "Quick answers")
    others = [a for a in articles_sorted() if a["slug"] != slug][:3]
    more = "".join(post_card(a) for a in others)
    hero = (f'<section class="page-hero"><div class="blobs"><div class="blob blob--sky blob--a" style="width:520px;height:520px;right:-140px;top:-200px"></div></div><div class="container"><div class="article hero-in"><span class="eyebrow">{esc(c.get("category", "Dental blog"))}</span><h1>{inline(c["h1"])}</h1><p class="lede">{inline(c["intro"])}</p>'
            f'<div class="article__meta"><span>{esc(fmt_date(c.get("date", "")))}</span><span>·</span><span>{esc(c.get("read_time", ""))}</span><span>·</span><span>Reviewed for patient education</span></div></div></div></section>')
    bslot = slot_for(slug)
    banner = f'<div class="container"><figure class="article__banner">{photo_img(bslot, sizes="(max-width: 900px) 100vw, 760px")}</figure></div>' if bslot and photo(bslot) else ""
    body = (crumbs(trail_for(slug)) + hero + banner +
            f'<section class="section section--tight section--paper"><div class="container"><article class="article">{blocks}{faqs}</article></div></section>' +
            f'<section class="section section--tight"><div class="container"><div class="section__head section__head--row"><div><span class="eyebrow">From the dental blog</span><h2>More clear answers</h2></div>{btn("All articles", "/blog/", "ghost", "arrow-right", "btn--sm")}</div><div class="grid grid--3 reveal-stagger">{more}</div></div></section>' +
            cta_band(c.get("cta"), slug))
    ld = [jsonld_crumbs([("Home", "/")] + trail_for(slug)),
          {"@context": "https://schema.org", "@type": "BlogPosting", "headline": c["title"], "datePublished": c.get("date"), "dateModified": c.get("date"), "author": {"@type": "Organization", "name": NAME}, "publisher": {"@id": DOMAIN + "/#dentist"}, "mainEntityOfPage": DOMAIN + slug, "description": c["meta_description"], "image": DOMAIN + "/assets/img/og.jpg"}]
    if c.get("faqs"): ld.append(jsonld_faq(c["faqs"]))
    return layout(slug, c["meta_title"], c["meta_description"], body, ld, og_type="article")

def render_faq_page(c):
    slug = c["slug"]; groups = c.get("groups", [])
    nav = '<div class="faq-nav">' + "".join(f'<a href="#{slugify(g["heading"])}">{esc(g["heading"])}</a>' for g in groups) + "</div>"
    gs = ""
    for g in groups:
        items = "".join(f'<details class="faq__item"><summary class="faq__q"><span>{inline(f["q"])}</span><span class="plus">{icon("plus")}</span></summary><div class="faq__a"><p>{inline(f["a"])}</p></div></details>' for f in g.get("items", []))
        gs += f'<div class="faq-group" id="{slugify(g["heading"])}"><h2>{esc(g["heading"])}</h2><div class="faq">{items}</div></div>'
    body = (crumbs(trail_for(slug)) + page_hero(c) +
            f'<section class="section section--tight section--paper"><div class="container"><div class="layout"><div class="main">{nav}{gs}</div><aside class="aside">{book_card()}{emergency_card()}</aside></div></div></section>' + cta_band(c.get("cta"), slug))
    allq = [f for g in groups for f in g.get("items", [])]
    return layout(slug, c["meta_title"], c["meta_description"], body, [jsonld_crumbs([("Home", "/"), (c["title"], slug)]), jsonld_faq(allq)])

def render_dictionary(c):
    slug = c["slug"]; terms = sorted(c.get("terms", []), key=lambda t: t["term"].lower())
    letters = sorted({t["term"][0].upper() for t in terms})
    az = '<div class="az">' + "".join((f'<a href="#letter-{L}">{L}</a>' if L in letters else f"<span>{L}</span>") for L in "ABCDEFGHIJKLMNOPQRSTUVWXYZ") + "</div>"
    out = ""
    for L in letters:
        dl = ""
        for t in [x for x in terms if x["term"][0].upper() == L]:
            if t.get("href") and t["href"] not in PAGES: BROKEN.append(t["href"])
            link = f' <a href="{esc(t["href"])}">Read more →</a>' if t.get("href") else ""
            dl += f'<dt>{esc(t["term"])}</dt><dd>{inline(t["definition"])}{link}</dd>'
        out += f'<div class="dict-letter" id="letter-{L}"><h2>{L}</h2><dl class="dict">{dl}</dl></div>'
    body = (crumbs(trail_for(slug)) + page_hero(c) +
            f'<section class="section section--tight section--paper"><div class="container"><div class="layout"><div class="main">{az}{out}</div><aside class="aside">{book_card()}</aside></div></div></section>' + cta_band(c.get("cta"), slug))
    return layout(slug, c["meta_title"], c["meta_description"], body, [jsonld_crumbs([("Home", "/"), (c["title"], slug)])])

# --------------------------------------------------------------------------- custom pages

HOME_FAQ = [
    {"q": "Are you accepting new patients?", "a": "Yes. West Alexandria Dental Care is welcoming new patients for our October 2026 opening. Book online at any hour, or call 703-263-8719 and the team will find a time that fits, including evenings and weekends."},
    {"q": "Do you see both adults and children?", "a": "Yes. This is a comprehensive family office for every stage of life, from a child's first visit to implants and dentures for grandparents, with records in one place so care stays joined up."},
    {"q": "Which insurance plans do you accept?", "a": "Aetna, Ameritas, Delta Dental, Humana, Cigna, MetLife and Virginia Medicaid. Participation and benefits vary by employer and plan, so send us your card through the registration page or bring it along and we will check your benefits before anything starts."},
    {"q": "What if I feel anxious about dental care?", "a": "Tell us when you book. We plan a slower, step-by-step visit, agree a signal to pause, and offer nitrous oxide and other sedation options after an individual health review. A first visit can be just a conversation."},
    {"q": "What languages does your team speak?", "a": "English, Arabic, Spanish and Portuguese. Mention your preferred language when you request an appointment so we can schedule the right team member for you."},
    {"q": "Do you place dental implants?", "a": "Yes. We plan complete tooth replacement here, including bridges, dentures and implant-supported options when they are the right fit. Dr. Fadi Alhrashi completed a dental implant fellowship at Tufts and is a Diplomate of the American Board of Oral Implantology."},
    {"q": "Where is the office and is there parking?", "a": "We are in the Bradlee Office Building at 3543 W. Braddock Road, Suite E1, Alexandria, VA 22302, steps from Bradlee Shopping Center and just off I-395 at the King Street exit. Free surface parking surrounds the building."},
]

def render_home():
    arts = articles_sorted()[:3]
    posts = "".join(post_card(a, num=i + 1) for i, a in enumerate(arts))
    chips = "".join(f'<span class="chip">{icon(i)}{esc(t)}</span>' for i, t in [("clock", "Open 7 days"), ("sun", "7 AM–8 PM weekdays"), ("language", "4 languages"), ("shield-check", "PPO + Medicaid")])
    hero_img = photo_img("hero-office", cls="hero__img", loading="eager", sizes="100vw")
    hero = f"""
<section class="hero hero--photo">
  <div class="hero__bg">{hero_img}<div class="hero__shade"></div></div>
  <div class="container hero__content">
    <div class="hero__copy hero-in">
      <span class="eyebrow eyebrow--light">Now welcoming new patients in West Alexandria</span>
      <h1 class="hero__title">Complete care.<br><span class="display-italic display-italic--gold">One dental home.</span></h1>
      <p class="lede hero__lede">Cleanings, urgent visits, restorative care, clear aligners, cosmetic dentistry and thoughtful tooth replacement, all with the clarity and personal attention of a neighborhood practice. Open seven days a week in the Bradlee Office Building.</p>
      <div class="btn-row">{btn("Book online", "book", "gold", "arrow-right", "btn--lg")}{btn("Explore services", "/services/", "outline-light", None, "btn--lg")}</div>
      <div class="hero__status">{status_pill()}</div>
    </div>
    <ul class="hero__stats reveal-stagger">
      <li><strong>7 days</strong><span>Open every week</span></li>
      <li><strong>7 AM–8 PM</strong><span>Weekday hours</span></li>
      <li><strong>4</strong><span>Languages spoken</span></li>
      <li><strong>Same-day</strong><span>Urgent care</span></li>
    </ul>
  </div>
</section>"""
    starters = [
        ("Routine care", "I'm due for a checkup", "Exams, cleanings and practical prevention for adults, teens and children.", "/general-dentistry/cleanings-and-exams/", "tooth"),
        ("Urgent care", "Something hurts", "Same-day evaluation for tooth pain, swelling, a broken tooth or another urgent concern.", "/emergency-dentistry/", "alert"),
        ("Restorative care", "I need to fix a tooth", "Fillings, crowns, bridges and tooth-saving treatment, with clear options first.", "/restorative-dentistry/", "repair"),
        ("Smile goals", "I want to smile confidently", "Whitening, bonding, clear aligners and cosmetic planning shaped around a healthy result.", "/cosmetic-dentistry/", "sparkle"),
    ]
    starter_html = "".join(f'<a class="starter__card" href="{esc(h)}"><span class="starter__kicker"><span class="card__num">0{i+1}</span>{esc(k)}</span><h3>{esc(t)}</h3><p>{esc(b)}</p><span class="card__arrow">Start here {icon("arrow-right")}</span></a>' for i, (k, t, b, h, ic) in enumerate(starters))
    starter = f"""
<section class="section section--tight">
  <div class="container">
    <div class="section__head section__head--center reveal"><span class="eyebrow">Start with what you need today</span><h2>You don't need to know the dental term.</h2><p class="lede" style="margin-inline:auto">Tell us what is happening. We will help you find the right place to start.</p></div>
    <div class="starter reveal-stagger">{starter_html}</div>
  </div>
</section>"""
    def svc(slug, span, extra_cls="", links=None):
        kids = children_of(slug)[:4] if links is None else links
        subs = "".join(f'<li><a href="{esc(k["slug"])}">{esc(k["title"])}</a></li>' for k in kids)
        return (f'<div class="card card--link card--stretch {extra_cls} span-{span}"><span class="card__icon">{icon(HUB_ICONS[slug])}</span><h3><a class="stretch" href="{esc(slug)}">{esc(title_of(slug))}</a></h3><p>{esc(blurb(slug))}</p>'
                f'<ul class="sublinks">{subs}</ul><a class="card__arrow" href="{esc(slug)}">{esc(title_of(slug))} {icon("arrow-right")}</a></div>')
    bento = (svc("/general-dentistry/", 6) + svc("/emergency-dentistry/", 6, "card--navy") +
             svc("/restorative-dentistry/", 3) + svc("/cosmetic-dentistry/", 3) + svc("/dental-implants/", 3) + svc("/clear-aligners/", 3) +
             svc("/sedation-dentistry/", 4) +
             f'<a class="card card--link card--gold span-4" href="/symptoms/"><span class="card__icon">{icon("pulse")}</span><h3>Symptom guides</h3><p>Sensitivity, bleeding gums, jaw pain, a loose tooth. Start with what you feel and find out what is usually behind it and what to do now.</p><span class="card__arrow">Browse symptoms {icon("arrow-right")}</span></a>' +
             f'<a class="card card--link card--sky span-4" href="/services/"><span class="card__icon">{icon("book")}</span><h3>Every service, on one page</h3><p>From sealants and fluoride to crowns, dentures, TMJ care and sleep apnea appliances, with a plain-English page on each.</p><span class="card__arrow">All services {icon("arrow-right")}</span></a>')
    services = f"""
<section class="section section--paper">
  <div class="container">
    <div class="section__head section__head--row reveal"><div><span class="eyebrow">Care for every stage of your smile</span><h2>Everyday dentistry, and the bigger jobs too.</h2><p class="lede">This is the office you return to year after year, for cleanings, a sudden toothache, a stronger bite or a more confident smile. We plan the care around the person, not the procedure.</p></div>{btn("See every service", "/services/", "ghost", "arrow-right")}</div>
    <div class="bento reveal-stagger">{bento}</div>
  </div>
</section>"""
    hours = f"""
<section class="section section--navy">
  <div class="container hours-band">
    <div class="reveal">
      <span class="eyebrow">Hours that fit real schedules</span>
      <h2>Open seven days a week. Early, late and weekends.</h2>
      <p class="lede">A 7 AM appointment before the commute, a 7 PM one after it, or a Saturday morning with the kids. Scheduling is online around the clock, and the same two dentists see you at every hour.</p>
      <ul class="access-list">
        <li>{icon("pin")}<div><strong>Bradlee Office Building</strong><span>3543 W. Braddock Road, Suite E1, Alexandria, VA 22302, steps from Bradlee Shopping Center.</span></div></li>
        <li>{icon("car")}<div><strong>Just off I-395</strong><span>Take the King Street exit. Minutes from Seminary Hill, Fairlington, Shirlington and Parkfairfax.</span></div></li>
        <li>{icon("parking")}<div><strong>Free surface parking</strong><span>Around the building, right at the door. No garage, no validation.</span></div></li>
      </ul>
      <div class="btn-row" style="margin-top:28px">{btn("Get directions", ADDR["directions"], "light", "directions")}{btn("Evening & weekend appointments", "/new-patients/evening-and-weekend-appointments/", "outline-light", "arrow-right")}</div>
    </div>
    <div class="hours-card reveal"><div class="hours-card__photo">{photo_img("home-hours")}</div><div class="hours-card__status" data-status><span class="status__dot"></span><span data-status-text>Open seven days a week</span></div>{hours_table()}<p class="small" style="margin-top:16px;color:#b9cbd2">These are the hours patients are seen. Online booking never closes.</p></div>
  </div>
</section>"""
    dentists = f"""
<section class="section">
  <div class="container dentists">
    <div class="portraits reveal-stagger">
      <a class="portrait" href="/dentists/dr-sameer-atrash/"><img src="/assets/img/dr-sameer-atrash.jpg" alt="Dr. Sameer Atrash" width="707" height="1000" loading="lazy"><div class="portrait__tag"><strong>Dr. Sameer Atrash, DMD</strong><span>Owner &amp; general dentist</span></div></a>
      <a class="portrait portrait--offset" href="/dentists/dr-fadi-alhrashi/"><img src="/assets/img/dr-fadi-alhrashi.webp" alt="Dr. Fadi Alhrashi" width="1122" height="1402" loading="lazy"><div class="portrait__tag"><strong>Dr. Fadi Alhrashi, DDS</strong><span>General dentist</span></div></a>
    </div>
    <div class="reveal">
      <span class="eyebrow">Meet the dentists</span>
      <h2>Two perspectives. One thoughtful standard of care.</h2>
      <p class="lede" style="margin-top:14px;margin-bottom:26px">Dr. Sameer Atrash and Dr. Fadi Alhrashi bring complementary experience to an office built for everyday family care and the more involved treatment life sometimes requires.</p>
      <div class="profile"><span class="profile__role">Owner &amp; general dentist</span><h3>Sameer Atrash, DMD</h3><p>Fairfax-raised and Tufts-trained, Dr. Sam pairs a conservative clinical philosophy with a modern, transparent approach: understand the person first, explain the diagnosis clearly, decide together.</p><div class="chip-row"><span class="chip chip--sky">{icon("star")}DMD, Tufts 2021</span><span class="chip chip--sky">{icon("aligner")}Clear aligners &amp; implants</span></div><a class="link-arrow" href="/dentists/dr-sameer-atrash/">Meet Dr. Sam {icon("arrow-right")}</a></div>
      <div class="profile"><span class="profile__role">General dentist</span><h3>Fadi Alhrashi, DDS</h3><p>Nearly two decades of advanced training in restorative, surgical and implant dentistry, with a calm, patient-centered approach to everyday and complex care. Speaks English and Arabic.</p><div class="chip-row"><span class="chip chip--sky">{icon("implant")}Implant fellowship, Tufts</span><span class="chip chip--sky">{icon("shield-check")}ABOI/ID Diplomate · AAID Fellow</span></div><a class="link-arrow" href="/dentists/dr-fadi-alhrashi/">Meet Dr. Fadi {icon("arrow-right")}</a></div>
    </div>
  </div>
</section>"""
    approach = f"""
<section class="section section--cream2">
  <div class="container">
    <div class="section__head reveal"><span class="eyebrow">Why choose West Alexandria Dental Care</span><h2>Modern tools. Clear decisions. No assembly-line dentistry.</h2><p class="lede">Technology matters when it helps us see more clearly and treat more precisely. The relationship matters every time. Our job is to explain what we see, make priorities understandable and help you choose wisely.</p></div>
    <div class="approach">
    <div class="approach__media reveal"><div class="frame">{photo_img("home-approach")}</div></div>
    <div class="approach__cards reveal-stagger">
      <a class="card card--link" href="/about/our-approach/"><span class="card__icon">{icon("heart")}</span><h3>Complete care, one home</h3><p>Preventive, restorative, cosmetic and urgent needs handled by the same two dentists, with your history in one place.</p><span class="card__arrow">How we work {icon("arrow-right")}</span></a>
      <a class="card card--link" href="/sedation-dentistry/"><span class="card__icon">{icon("moon")}</span><h3>Comfort, planned in</h3><p>It is okay to be nervous. We pace the visit, explain each step, and offer nitrous oxide and sedation options after an individual review.</p><span class="card__arrow">Comfort options {icon("arrow-right")}</span></a>
      <a class="card card--link" href="/about/technology/"><span class="card__icon">{icon("xray")}</span><h3>Advanced diagnostics</h3><p>3D imaging, magnification and digital X-rays shown on the screen beside you, used when they meaningfully improve care.</p><span class="card__arrow">Our technology {icon("arrow-right")}</span></a>
    </div>
    </div>
  </div>
</section>"""
    plans = "".join(f'<div class="plan{" plan--hl" if p == "Virginia Medicaid" else ""}">{icon("check")}<span>{esc(p)}{"<small>Accepted here</small>" if p == "Virginia Medicaid" else ""}</span></div>' for p in SITE["insurance"])
    insurance = f"""
<section class="section section--paper">
  <div class="container">
    <div class="section__head section__head--row reveal"><div><span class="eyebrow">Insurance &amp; new patients</span><h2>Yes, we accept insurance. We also help you understand it.</h2><p class="lede">Dental benefits should make care easier, not more confusing. Complete your registration online, upload a photo of your card, and our team will verify your benefits and explain the next step before your visit.</p></div>{btn("Complete patient paperwork", "forms", "primary", "arrow-up-right")}</div>
    <div class="plans reveal-stagger">{plans}<a class="plan" href="/new-patients/insurance/" style="justify-content:space-between">Don't see your plan? {icon("arrow-right")}</a></div>
    <p class="small muted" style="margin-top:18px">Network participation and benefits vary by employer and plan. <a href="/new-patients/understanding-dental-insurance/">How dental insurance actually works →</a> · <a href="/new-patients/no-insurance/">No insurance?</a></p>
  </div>
</section>"""
    first = f"""
<section class="section">
  <div class="container">
    <div class="section__head section__head--center reveal"><span class="eyebrow">A clearer first visit</span><h2>No pressure. No mystery. No rushed decision.</h2></div>
    <div class="steps reveal-stagger">
      <div class="step"><span class="step__num">1</span><h3>Tell us what matters</h3><p>We start with your concern, your goals and what would make the visit feel successful. If you are nervous, say so. It changes how we plan.</p></div>
      <div class="step"><span class="step__num">2</span><h3>See the full picture</h3><p>Your exam and images come up on the screen beside you, and we explain what we see in plain language, including what can wait.</p></div>
      <div class="step"><span class="step__num">3</span><h3>Choose the right plan</h3><p>You leave knowing your options, the priorities, and the cost in writing. Then you decide, without anyone leaning on you.</p></div>
    </div>
    <div style="text-align:center;margin-top:40px" class="reveal">{btn("What a first visit involves", "/new-patients/first-visit/", "ghost", "arrow-right")}</div>
  </div>
</section>"""
    langs = f"""
<section class="section section--tight section--cream2">
  <div class="container" style="text-align:center">
    <span class="eyebrow eyebrow--plain reveal">Feel understood</span>
    <div class="langs reveal-stagger" style="margin:18px 0 34px"><span data-lang="English">Welcome</span><span data-lang="Arabic" class="ar" lang="ar" dir="rtl">أهلاً وسهلاً</span><span data-lang="Spanish" lang="es">Bienvenidos</span><span data-lang="Portuguese" lang="pt">Bem-vindos</span></div>
    <p class="lede reveal" style="margin:22px auto 0">Care in English, Arabic, Spanish and Portuguese. Tell us your preferred language when you book. <a href="/new-patients/languages/">Languages we speak →</a></p>
  </div>
</section>"""
    faq_items = "".join(f'<details class="faq__item"><summary class="faq__q"><span>{esc(f["q"])}</span><span class="plus">{icon("plus")}</span></summary><div class="faq__a"><p>{esc(f["a"])}</p></div></details>' for f in HOME_FAQ)
    faq = f"""
<section class="section section--paper">
  <div class="container"><div class="layout" style="grid-template-columns:minmax(0,380px) minmax(0,1fr)">
    <div class="reveal"><span class="eyebrow">Frequently asked</span><h2>Good questions deserve clear answers.</h2><p class="lede" style="margin-top:14px">Still unsure? Call us at <a href="tel:{TEL}">{PHONE}</a> or browse <a href="/faq/">all questions and answers</a>.</p></div>
    <div class="faq reveal">{faq_items}</div>
  </div></div>
</section>"""
    blog = f"""
<section class="section">
  <div class="container">
    <div class="section__head section__head--row reveal"><div><span class="eyebrow">From the dental journal</span><h2>Clear answers before your next visit.</h2><p class="lede">Practical, responsible guidance for the questions patients ask most, from urgent symptoms to prevention and dental anxiety.</p></div>{btn("Visit the dental blog", "/blog/", "ghost", "arrow-right")}</div>
    <div class="grid grid--3 reveal-stagger">{posts}</div>
  </div>
</section>"""
    body = hero + starter + services + hours + dentists + approach + insurance + first + langs + faq + blog + cta_band({"heading": "Ready when you are.", "body": "Whether you are due for a cleaning, dealing with pain or thinking about your smile, the first step is simply a conversation. New patients are welcome, and so is a second opinion."})
    return layout("/", "West Alexandria Dental Care | Family Dentist in Alexandria, VA, Open 7 Days", "Comprehensive family, restorative and cosmetic dentistry in the Bradlee Office Building, Alexandria, VA. Open 7 AM–8 PM weekdays and weekend mornings. PPO plans and Virginia Medicaid accepted. Care in four languages.", body, [jsonld_faq(HOME_FAQ)])

def render_services():
    groups = ""
    for hub in HUB_ORDER:
        kids = children_of(hub)
        links = "".join(f'<a href="{esc(k["slug"])}"><span>{esc(k["title"])}</span>{icon("arrow-right")}</a>' for k in kids)
        groups += (f'<div class="svc-group"><div class="svc-group__head reveal"><div><span class="card__icon">{icon(HUB_ICONS[hub])}</span><h2><a href="{esc(hub)}" style="color:inherit">{esc(title_of(hub))}</a></h2><p>{esc(blurb(hub))}</p><a class="link-arrow" href="{esc(hub)}" style="margin-top:10px">About {esc(title_of(hub).lower())} {icon("arrow-right")}</a></div>'
                   f'<div class="svc-list">{links}</div></div></div>')
    sym = children_of("/symptoms/")
    sym_links = "".join(f'<a href="{esc(k["slug"])}"><span>{esc(k["title"])}</span>{icon("arrow-right")}</a>' for k in sym)
    groups += f'<div class="svc-group"><div class="svc-group__head reveal"><div><span class="card__icon" style="background:var(--gold-soft);color:var(--gold-deep)">{icon("pulse")}</span><h2><a href="/symptoms/" style="color:inherit">Symptom guides</a></h2><p>Start with what you feel, not the dental term. Each guide covers what is usually behind it, what to do now, and when to be seen today.</p></div><div class="svc-list">{sym_links}</div></div></div>'
    c = {"slug": "/services/", "eyebrow": "All services", "h1": "Every service, on one page", "intro": "From cleanings and sealants to crowns, implants, clear aligners and sleep apnea appliances, with a plain-English page on each. Most treatment happens in this building, with the same two dentists, so a crown or an implant does not mean a referral across town.", "icon": "book"}
    body = crumbs([("All Services", "/services/")]) + page_hero(c) + f'<section class="section section--tight section--paper"><div class="container">{groups}</div></section>' + cta_band({"heading": "Not sure which service fits?", "body": "Tell us what is happening and we will help you find the right place to start. Evenings and weekends included."})
    return layout("/services/", "All Dental Services in Alexandria, VA | West Alexandria Dental Care", "Every service at West Alexandria Dental Care on one page: general, restorative, cosmetic, implants, clear aligners, emergency and sedation dentistry, with symptom guides.", body, [jsonld_crumbs([("Home", "/"), ("All Services", "/services/")])])

def render_dentists_index():
    def card(slug, img, role, name, blurb_, chips):
        ch = "".join(f'<span class="chip chip--sky">{icon(i)}{esc(t)}</span>' for i, t in chips)
        return (f'<div class="card" style="display:grid;grid-template-columns:200px 1fr;gap:28px;align-items:start;padding:32px"><a class="portrait" href="{esc(slug)}" style="aspect-ratio:3/4"><img src="/assets/img/{img}" alt="{esc(name)}" loading="lazy"></a>'
                f'<div><span class="profile__role">{esc(role)}</span><h2 style="font-size:2rem;margin:6px 0 12px">{esc(name)}</h2><p class="lede" style="font-size:1.05rem">{esc(blurb_)}</p><div class="chip-row" style="margin:16px 0 20px">{ch}</div>{btn("Meet " + name.split(",")[0].split()[-1] if False else "Full profile", slug, "primary", "arrow-right", "btn--sm")}</div></div>')
    c = {"slug": "/dentists/", "eyebrow": "Meet the dentists", "h1": "Two dentists. One promise: care that makes sense.", "intro": "A healthy smile rarely comes from a single procedure. It comes from listening, seeing the full picture and choosing the right care at the right time. That is the standard Dr. Sam and Dr. Fadi share, whichever of them you see.", "icon": "family"}
    sam = card("/dentists/dr-sameer-atrash/", "dr-sameer-atrash.jpg", "Owner & general dentist", "Dr. Sameer Atrash, DMD", "Born in Washington, D.C. and raised in Fairfax, Dr. Sam found dentistry in high school through Fairfax County's Dental Careers Program. VCU, then Tufts University School of Dental Medicine. Conservative first: prevent what can be prevented, preserve what can be preserved.", [("star", "DMD, Tufts 2021"), ("book", "BS Biology · MPI, VCU"), ("aligner", "Clear aligners, implants, digital dentistry")])
    fadi = card("/dentists/dr-fadi-alhrashi/", "dr-fadi-alhrashi.webp", "General dentist", "Dr. Fadi Alhrashi, DDS", "Nearly two decades of advanced training and clinical experience: an Advanced General Dentistry residency at the Eastman Institute for Oral Health and a Dental Implant Fellowship at Tufts. Calm, thorough, and fluent in English and Arabic.", [("implant", "Implant fellowship, Tufts"), ("shield-check", "ABOI/ID Diplomate · AAID Fellow"), ("star", "Handelman Award of Excellence")])
    expect = "".join(f'<div class="card card--sm"><span class="card__num">0{i+1}</span><h3>{esc(t)}</h3><p>{esc(b)}</p></div>' for i, (t, b) in enumerate([
        ("Clear explanations", "See what we see, understand what it means and know which decisions can wait."),
        ("Personal options", "Treatment plans shaped around your health, goals, comfort and priorities, with the cost in writing."),
        ("Comprehensive thinking", "Everyday prevention and complex care viewed as parts of the same long-term plan."),
        ("Calm, respectful care", "No lectures and no judgment, whatever the gap since your last visit. Just a team ready to help you move forward.")]))
    body = (crumbs([("Meet the Dentists", "/dentists/")]) + page_hero(c) +
            f'<section class="section section--tight section--paper"><div class="container"><div class="grid reveal-stagger" style="gap:24px">{sam}{fadi}</div></div></section>' +
            f'<section class="section section--tight"><div class="container"><div class="section__head reveal"><span class="eyebrow">What you can expect</span><h2>Expertise matters. How you are treated matters just as much.</h2></div><div class="grid grid--4 reveal-stagger">{expect}</div></div></section>' +
            related_cards(["/about/our-approach/", "/about/technology/", "/new-patients/first-visit/"], "More about the practice") +
            cta_band({"heading": "A healthier smile can start with one conversation.", "body": "New patients are welcome. If you would like to see a particular dentist, mention it when you book and we will tell you what is available."}))
    return layout("/dentists/", "Meet the Dentists | Dr. Sameer Atrash & Dr. Fadi Alhrashi | Alexandria, VA", "Meet Dr. Sameer Atrash, DMD and Dr. Fadi Alhrashi, DDS, the general dentists behind West Alexandria Dental Care in the Bradlee Office Building, Alexandria, VA.", body, [jsonld_crumbs([("Home", "/"), ("Meet the Dentists", "/dentists/")])])

def render_contact():
    c = {"slug": "/contact/", "eyebrow": "Contact West Alexandria Dental Care", "h1": "Let's find the right first visit.", "intro": "Due for a cleaning? Dealing with pain? Looking for a second opinion? Choose a time online at any hour, or call us directly for an urgent dental concern. Someone in the office will help you plan the next step.", "icon": "chat"}
    cards = (f'<a class="card card--link" href="tel:{TEL}"><span class="card__icon">{icon("phone")}</span><h3>Call</h3><p style="font-size:1.3rem;font-weight:600;color:var(--navy)">{PHONE}</p><p>Best for urgent dental concerns and same-day questions.</p></a>'
             f'<a class="card card--link" href="{esc(BOOK)}" target="_blank" rel="noopener"><span class="card__icon">{icon("calendar")}</span><h3>Book online</h3><p>Real-time availability, 24 hours a day, including early mornings, evenings and weekends.</p><span class="card__arrow">Choose a time {icon("arrow-up-right")}</span></a>'
             f'<a class="card card--link" href="{esc(ADDR["directions"])}" target="_blank" rel="noopener"><span class="card__icon">{icon("pin")}</span><h3>Visit</h3><p>{address_block()}</p><span class="card__arrow">Directions {icon("arrow-up-right")}</span></a>')
    form = f"""
<form class="form" data-inquiry-form data-to="{esc(SITE.get('email', ''))}" action="mailto:{esc(SITE.get('email', ''))}" method="post" enctype="text/plain">
  <div class="form__row"><div class="field"><label for="f-name">Full name</label><input id="f-name" name="name" required autocomplete="name"></div><div class="field"><label for="f-phone">Phone number</label><input id="f-phone" name="phone" type="tel" required autocomplete="tel"></div></div>
  <div class="form__row"><div class="field"><label for="f-email">Email address</label><input id="f-email" name="email" type="email" autocomplete="email"></div><div class="field"><label for="f-reason">Reason for contacting us</label><select id="f-reason" name="reason"><option>New-patient exam and cleaning</option><option>Tooth pain or urgent concern</option><option>Restorative or cosmetic consultation</option><option>Comfort or sedation question</option><option>Insurance question</option><option>Something else</option></select></div></div>
  <div class="field"><label for="f-msg">How can we help?</label><textarea id="f-msg" name="message" required></textarea></div>
  <div class="btn-row">{btn("Prepare email inquiry", "#", "primary", "mail").replace('<a ', '<button type="submit" ').replace('href="#" ', '').replace('</a>', '</button>')}</div>
  <p class="form__note" data-form-note>Please do not include private health information. This form prepares an email to the office; for real-time appointment availability use Book online, and for an urgent concern please call.</p>
</form>"""
    body = (crumbs([("Contact & Directions", "/contact/")]) + page_hero(c) +
            f'<section class="section section--tight section--paper"><div class="container"><div class="contact-grid reveal-stagger">{cards}</div></div></section>' +
            f'<section class="section section--tight"><div class="container"><div class="layout"><div class="main"><div class="section__head"><span class="eyebrow">Questions before booking?</span><h2>Send our team an inquiry.</h2><p class="lede">For a question about care, insurance or your first visit. The office replies during business hours.</p></div>{form}</div>'
            f'<aside class="aside"><div class="aside__card"><h4>Opening schedule</h4>{hours_table(light=True)}<p class="small muted" style="margin-top:12px">{esc(SITE["announcement"])}.</p></div>{book_card()}<div class="aside__card"><h4>Before your visit</h4><p class="small">Complete your forms and upload your insurance card through our secure registration page.</p><div style="margin-top:12px">{btn("Patient paperwork", "forms", "ghost", "arrow-up-right", "btn--sm")}</div></div></aside></div></div></section>' +
            f'<section class="section section--tight section--paper"><div class="container"><div class="section__head reveal"><span class="eyebrow">Our West Alexandria location</span><h2>Near Bradlee Shopping Center. Close to home.</h2><p class="lede">Located in the Bradlee Office Building, just off I-395 at the King Street exit, for families across West Alexandria, Seminary Hill, Fairlington, Shirlington and nearby communities.</p></div>'
            f'<div class="map reveal"><iframe title="Map to West Alexandria Dental Care" src="{esc(ADDR["map_embed"])}" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe></div>'
            f'<div class="grid grid--3 reveal-stagger" style="margin-top:24px"><div class="card card--sm"><span class="card__icon">{icon("parking")}</span><h3>Free parking</h3><p>Surface parking around the building, right at the door.</p></div><div class="card card--sm"><span class="card__icon">{icon("car")}</span><h3>Convenient access</h3><p>Just off I-395 at the King Street exit, and minutes from Quaker Lane and Seminary Road.</p></div><div class="card card--sm"><span class="card__icon">{icon("pin")}</span><h3>Nearby landmarks</h3><p>Steps from Bradlee Shopping Center, in the Bradlee Office Building, Suite E1.</p></div></div>'
            f'<div style="margin-top:24px" class="reveal">{btn("Areas we serve", "/areas/", "ghost", "arrow-right")}</div></div></section>' +
            cta_band({"heading": "Prefer to talk?", "body": "We are happy to start with a phone call. For an urgent dental concern, please call rather than using the form so we can help direct your next step."}))
    ld = [jsonld_crumbs([("Home", "/"), ("Contact & Directions", "/contact/")])]
    return layout("/contact/", "Contact & Directions | West Alexandria Dental Care, Alexandria, VA", "Call 703-263-8719, book online 24/7, or visit West Alexandria Dental Care in the Bradlee Office Building, 3543 W. Braddock Road, Suite E1, Alexandria, VA 22302. Free parking.", body, ld)

def render_book():
    c = {"slug": "/book-online/", "eyebrow": "Book online", "h1": "Choose a time that fits. Any hour, any day.", "intro": "Online scheduling shows real availability, including 7 AM starts, evenings until 8 PM and weekend mornings. Pick a time, tell us what brings you in, and the office confirms the details. New patients are welcome.", "icon": "calendar"}
    steps = "".join(f'<li><h3>{esc(t)}</h3><p>{esc(b)}</p></li>' for t, b in [
        ("Pick a time online", "The booking page lists open appointments for both dentists. Choose what fits; the office follows up if anything needs adjusting."),
        ("Complete your paperwork", "Use the secure registration page to enter your medical history and insurance before you arrive. You can upload a photo of your card."),
        ("Come in and talk first", "A first visit starts with a conversation, then the exam. You leave with a written plan and no pressure to decide on the spot.")])
    body = (crumbs([("Book Online", "/book-online/")]) + page_hero(c, extra=f'<div style="margin-top:22px">{btn("Open online booking", "book", "sky", "arrow-up-right", "btn--lg")}</div>') +
            f'<section class="section section--tight section--paper"><div class="container"><div class="layout"><div class="main"><section class="block"><h2>How it works</h2><ol class="steps-v">{steps}</ol></section>'
            f'<section class="block"><div class="callout callout--info"><h2>Something hurts right now?</h2><p>Please call {PHONE} instead of booking online so we can plan the visit and get you in sooner.</p>{btn("Call " + PHONE, "tel", "primary", "phone", "btn--sm")}</div></section>'
            f'<section class="block"><h2>Good to have ready</h2><ul class="list list--check"><li>{icon("check")}<span>Your insurance card, or a photo of it (we accept Aetna, Ameritas, Delta Dental, Humana, Cigna, MetLife and Virginia Medicaid).</span></li><li>{icon("check")}<span>A list of medications you take, including ones that seem unrelated to teeth.</span></li><li>{icon("check")}<span>Your preferred language, if it is Arabic, Spanish or Portuguese, so we schedule the right team member.</span></li><li>{icon("check")}<span>A note about anything that makes dental visits hard for you. It changes how we plan the appointment.</span></li></ul></section></div>'
            f'<aside class="aside">{book_card()}<div class="aside__card"><h4>Paperwork first</h4><p class="small">Registration takes about ten minutes on a phone or computer.</p><div style="margin-top:12px">{btn("Complete patient paperwork", "forms", "ghost", "arrow-up-right", "btn--sm")}</div></div><div class="aside__card"><h4>Hours</h4>{hours_table(light=True)}</div></aside></div></div></section>' +
            related_cards(["/new-patients/first-visit/", "/new-patients/evening-and-weekend-appointments/", "/new-patients/insurance/"], "Before your first visit") +
            cta_band({"heading": "Rather talk to a person?", "body": f"Call {PHONE} and someone at the office will find a time with you."}))
    return layout("/book-online/", "Book Online | West Alexandria Dental Care, Alexandria, VA", "Book a dental appointment online, any hour. Early mornings, evenings until 8 PM and weekend mornings at West Alexandria Dental Care in Alexandria, VA. New patients welcome.", body, [jsonld_crumbs([("Home", "/"), ("Book Online", "/book-online/")])])

def render_blog_index():
    arts = articles_sorted()
    if not arts:
        cards = "<p>Articles are on the way.</p>"
    else:
        cards = post_card(arts[0], feature=True) + "".join(post_card(a) for a in arts[1:])
    c = {"slug": "/blog/", "eyebrow": "Dental blog", "h1": "Practical answers for healthier smiles.", "intro": "Clear, responsible guidance for the questions patients ask most, from urgent symptoms to prevention, comfort and what to expect at a new office. Written to be useful, not to sell.", "icon": "book"}
    body = (crumbs([("Dental Blog", "/blog/")]) + page_hero(c) +
            f'<section class="section section--tight section--paper"><div class="container"><div class="grid grid--3 reveal-stagger">{cards}</div></div></section>' +
            related_cards(["/symptoms/", "/faq/", "/dental-dictionary/"], "More resources") + cta_band(None))
    return layout("/blog/", "Dental Blog | West Alexandria Dental Care", "Plain-English articles from West Alexandria Dental Care on dental emergencies, cleanings, dental anxiety, first visits and family care in Alexandria, VA.", body, [jsonld_crumbs([("Home", "/"), ("Dental Blog", "/blog/")])])

def render_404():
    links = "".join(f'<a class="card card--link card--sm" href="{esc(s)}"><h3>{esc(t)}</h3></a>' for t, s in [("All services", "/services/"), ("Symptom guides", "/symptoms/"), ("New patients", "/new-patients/"), ("Meet the dentists", "/dentists/"), ("Contact & directions", "/contact/"), ("Book online", "/book-online/")])
    body = f'<section class="section"><div class="container not-found"><div class="num">404</div><h1>That page is not here.</h1><p class="lede" style="margin:18px auto 32px">It may have moved. Everything below is where it lives now, or just call us and whoever answers can point you to it faster than this page can.</p><div class="btn-row" style="justify-content:center">{btn("Call " + PHONE, "tel", "primary", "phone")}{btn("Home", "/", "ghost")}</div><div class="grid grid--3" style="margin-top:48px;text-align:left">{links}</div></div></section>'
    return layout("/404.html", "Page not found | West Alexandria Dental Care", "That page is not here.", body)

# --------------------------------------------------------------------------- output

def write(slug, html_):
    if slug.endswith(".html"):
        path = os.path.join(OUT, slug.lstrip("/"))
    else:
        path = os.path.join(OUT, slug.strip("/"), "index.html") if slug != "/" else os.path.join(OUT, "index.html")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(html_)

def main():
    check = "--check" in sys.argv
    if os.path.isdir(OUT):
        for item in os.listdir(OUT):
            p = os.path.join(OUT, item)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(OUT, exist_ok=True)
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(OUT, "assets"))
    for f in glob.glob(os.path.join(OUT, "assets", "img", "_*")): os.remove(f)
    built = []; missing = []
    custom = {"/": render_home, "/services/": render_services, "/contact/": render_contact, "/book-online/": render_book, "/dentists/": render_dentists_index, "/blog/": render_blog_index}
    for slug, p in PAGES.items():
        if slug in custom:
            write(slug, custom[slug]()); built.append(slug); continue
        c = CONTENT.get(slug)
        if not c:
            missing.append(slug); continue
        t = c.get("type")
        if t == "hub": h = render_hub(c)
        elif t == "article": h = render_article(c)
        elif t == "faq": h = render_faq_page(c)
        elif t == "dictionary": h = render_dictionary(c)
        else: h = render_standard(c)
        write(slug, h); built.append(slug)
    write("/404.html", render_404())
    # sitemap, robots, manifest
    today = datetime.date.today().isoformat()
    urls = "".join(f"<url><loc>{DOMAIN}{s}</loc><lastmod>{today}</lastmod><changefreq>{'weekly' if s == '/' else 'monthly'}</changefreq><priority>{'1.0' if s == '/' else ('0.8' if s.count('/') == 2 else '0.6')}</priority></url>" for s in built)
    open(os.path.join(OUT, "sitemap.xml"), "w").write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
    open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n")
    json.dump({"name": NAME, "short_name": "WA Dental", "start_url": "/", "display": "browser", "background_color": "#f7f2ea", "theme_color": "#17343e", "icons": [{"src": "/assets/img/icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "/assets/img/icon-512.png", "sizes": "512x512", "type": "image/png"}]}, open(os.path.join(OUT, "site.webmanifest"), "w"))
    # netlify/vercel friendly redirects + headers
    open(os.path.join(OUT, "_redirects"), "w").write("/index.html / 301\n/* /404.html 404\n")
    host = DOMAIN.split("//", 1)[1]
    open(os.path.join(OUT, ".htaccess"), "w").write(f"""# {NAME} - Apache/LiteSpeed rules (Hostinger shared hosting)
Options -Indexes
DirectoryIndex index.html
ErrorDocument 404 /404.html

<IfModule mod_rewrite.c>
RewriteEngine On
# Force HTTPS and the canonical host ({host})
RewriteCond %{{HTTPS}} off [OR]
RewriteCond %{{HTTP_HOST}} !^{host.replace('.', chr(92) + '.')}$ [NC]
RewriteRule ^ https://{host}%{{REQUEST_URI}} [L,R=301]
# Clean URLs: /services -> /services/
RewriteCond %{{REQUEST_FILENAME}} -d
RewriteCond %{{REQUEST_URI}} !/$
RewriteRule ^(.*)$ /$1/ [L,R=301]
</IfModule>

<IfModule mod_headers.c>
<FilesMatch "\\.(css|js|svg|png|jpg|jpeg|webp|woff2|webmanifest)$">
Header set Cache-Control "public, max-age=2592000"
</FilesMatch>
<FilesMatch "\\.html$">
Header set Cache-Control "public, max-age=600"
</FilesMatch>
Header set X-Content-Type-Options "nosniff"
Header set Referrer-Policy "strict-origin-when-cross-origin"
</IfModule>

<IfModule mod_deflate.c>
AddOutputFilterByType DEFLATE text/html text/css text/javascript application/javascript application/json image/svg+xml
</IfModule>
""")
    print(f"built {len(built)} pages → {OUT}")
    if missing: print(f"missing content for {len(missing)} registry pages: " + ", ".join(missing))
    if BROKEN:
        bad = sorted(set(BROKEN)); print(f"BROKEN internal links ({len(bad)}): " + ", ".join(bad))
    if check:
        # verify every href="/..." in output resolves to a built page or asset
        outbad = set()
        for f in glob.glob(os.path.join(OUT, "**", "*.html"), recursive=True):
            for h in re.findall(r'href="(/[^"#?]*)', open(f, encoding="utf-8").read()):
                if h.startswith("/assets/") or h in ("/sitemap.xml", "/robots.txt", "/site.webmanifest", "/404.html"):
                    if not os.path.exists(os.path.join(OUT, h.lstrip("/"))): outbad.add(h)
                    continue
                target = os.path.join(OUT, h.strip("/"), "index.html") if h != "/" else os.path.join(OUT, "index.html")
                if not os.path.exists(target): outbad.add(h)
        print("link check: " + ("OK, all internal links resolve" if not outbad else f"{len(outbad)} unresolved: " + ", ".join(sorted(outbad))))
        return 1 if (outbad or BROKEN) else 0
    return 0

if __name__ == "__main__":
    sys.exit(main())
