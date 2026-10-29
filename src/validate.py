#!/usr/bin/env python3
"""Validate one or more content JSON files against the site registry, FACTS and CONTENT_GUIDE rules.

Usage:  python3 src/validate.py src/content/path/to/page.json [more.json ...]
        python3 src/validate.py --all
Exit code 0 = all pass. Prints one line per issue:  path :: SEVERITY :: message
SEVERITY is ERROR (must fix) or WARN (should fix).
"""
import json, re, sys, os, glob

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = json.load(open(os.path.join(ROOT, "site.json")))
SLUGS = {p["slug"] for p in SITE["pages"]}
TYPES = {"service", "symptom", "hub", "info", "area", "article", "faq", "dictionary", "dentist", "custom"}
ICONS = set("tooth shield sparkle clock pin phone calendar implant aligner crown drop moon alert child senior xray heart smile gum star check family language card wallet book map chat sun hand pulse wave gear leaf braces bridge denture root shield-check repair emergency".split())
BLOCKS = {"prose", "steps", "list", "cards", "compare", "callout"}
TONES = {"urgent", "info", "note"}

BANNED = [
    "state-of-the-art", "cutting-edge", "cutting edge", "world-class", "top-rated", "best-in-class", "unparalleled",
    "utilize", "leverage", "passionate", "dedicated to excellence", "nestled", "seamless", "smile journey",
    "transform your smile", "dream smile", "we understand that", "look no further", "rest assured", "don't hesitate",
    "comprehensive solution", "holistic",
]
FORBIDDEN_FACTS = [
    (r"\$\s?\d", "dollar amount"),
    (r"\b(carecredit|care credit|lendingclub|sunbit|cherry financing|proceed finance)\b", "financing company"),
    (r"\b(itero|cerec|laser|lasers|primescan|trios|biolase|waterlase|solea)\b", "unlisted equipment/brand"),
    (r"\b(halcion|triazolam|valium|diazepam|iv sedation|intravenous)\b", "specific sedation drug/route"),
    (r"\b(testimonial|testimonials|our patients say|five-star|5-star|★|google reviews?)\b", "reviews/testimonials"),
    (r"\b(540-921-3323|pearisburg|tazewell|giles county)\b", "other office details"),
    (r"\b(membership plan|dental club|virginia dental club|membersy)\b", "membership plan"),
    (r"\b(24/7 emergency|24-hour emergency|emergency treatment 24/7|treatment any hour)\b", "24/7 treatment claim"),
    (r"\b(specialist in|our specialist|board-certified specialist)\b", "specialist claim"),
    (r"\b(pain-free guarantee|guaranteed results|guarantee)\b", "guarantee"),
    (r"\b(best dentist|#1 dentist|number one dentist)\b", "superlative claim"),
]
PHONE_OK = "703-263-8719"
WORD_TARGETS = {"service": (650, 1000), "symptom": (550, 950), "info": (600, 1000), "area": (450, 700), "hub": (400, 650), "article": (700, 1400), "dentist": (500, 900)}

link_re = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
html_re = re.compile(r"<[^>]+>")


def words(s):
    return len(re.findall(r"[A-Za-z0-9'’-]+", s))


def walk_strings(obj, path="$"):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_strings(v, f"{path}[{i}]")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(v, f"{path}.{k}")


def body_text(d):
    """Concatenate the text that counts toward the word target (sections, faqs, groups, terms, intro)."""
    parts = [d.get("intro", "")]
    for s in d.get("sections", []):
        for p, v in walk_strings(s):
            if not p.endswith(".type") and not p.endswith(".heading") and not p.endswith(".href") and not p.endswith(".tone") and not p.endswith(".label"):
                parts.append(v)
    for f in d.get("faqs", []):
        parts += [f.get("q", ""), f.get("a", "")]
    for g in d.get("groups", []):
        for f in g.get("items", []):
            parts += [f.get("q", ""), f.get("a", "")]
    for t in d.get("terms", []):
        parts += [t.get("definition", "")]
    return " ".join(parts)


def validate(path):
    issues = []
    E = lambda m: issues.append((path, "ERROR", m))
    W = lambda m: issues.append((path, "WARN", m))
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        return [(path, "ERROR", f"invalid JSON: {e}")]

    # expected slug from path
    rel = os.path.relpath(path, os.path.join(ROOT, "content")).replace(os.sep, "/")
    expected = "/" + rel[:-5] + "/" if rel != "index.json" else "/"
    if expected.endswith("/index/"):
        expected = expected[:-6]
    slug = d.get("slug")
    if slug != expected:
        E(f"slug {slug!r} does not match file location (expected {expected!r})")
    if slug not in SLUGS:
        E(f"slug {slug!r} is not in site.json registry")
    t = d.get("type")
    if t not in TYPES:
        E(f"type {t!r} invalid")
    reg = next((p for p in SITE["pages"] if p["slug"] == slug), None)
    if reg and reg.get("type") != t and reg.get("type") != "custom":
        E(f"type {t!r} does not match registry type {reg.get('type')!r}")

    for k in ["title", "meta_title", "meta_description", "h1", "intro", "cta"]:
        if not d.get(k):
            E(f"missing {k}")
    md = d.get("meta_description", "")
    if md and not (110 <= len(md) <= 165):
        W(f"meta_description length {len(md)} (want 140–160)")
    mt = d.get("meta_title", "")
    if mt and len(mt) > 70:
        W(f"meta_title length {len(mt)} (>70)")
    if d.get("icon") and d["icon"] not in ICONS:
        E(f"icon {d['icon']!r} not in icon set")
    if t in {"service", "symptom"} and not d.get("facts"):
        W("service/symptom page has no facts chips")
    for f in d.get("facts", []) or []:
        if words(f.get("value", "")) > 5:
            W(f"facts value too long: {f.get('value')!r}")

    secs = d.get("sections", [])
    if t not in {"faq", "dictionary"}:
        if not secs:
            E("no sections")
        kinds = [s.get("type") for s in secs]
        if not any(k in {"steps", "list"} for k in kinds):
            W("no steps/list section")
        if t in {"service", "symptom"} and not (5 <= len(secs) <= 9):
            W(f"{len(secs)} sections (want 5–9)")
        for i, s in enumerate(secs):
            k = s.get("type")
            if k not in BLOCKS:
                E(f"section[{i}] type {k!r} invalid")
                continue
            if not s.get("heading"):
                E(f"section[{i}] ({k}) missing heading")
            if k == "prose" and not isinstance(s.get("body"), list):
                E(f"section[{i}] prose body must be a list of paragraphs")
            if k in {"steps", "cards"}:
                for j, it in enumerate(s.get("items", [])):
                    if not it.get("title") or not it.get("body"):
                        E(f"section[{i}] item[{j}] needs title and body")
                    if it.get("href") and not (it["href"] in SLUGS or it["href"] in {"tel", "book", "forms"}):
                        E(f"section[{i}] item[{j}] href {it['href']!r} not in registry")
            if k == "list":
                if not isinstance(s.get("items"), list) or not all(isinstance(x, str) for x in s.get("items", [])):
                    E(f"section[{i}] list items must be strings")
                if s.get("style") and s["style"] not in {"check", "bullet", "warn"}:
                    E(f"section[{i}] list style {s['style']!r} invalid")
            if k == "compare":
                cols = s.get("columns", [])
                if len(cols) < 2:
                    E(f"section[{i}] compare needs >=2 columns")
                for r in s.get("rows", []):
                    if len(r) != len(cols) + 1:
                        E(f"section[{i}] compare row length {len(r)} != columns+1 ({len(cols)+1})")
            if k == "callout":
                if s.get("tone") not in TONES:
                    E(f"section[{i}] callout tone {s.get('tone')!r} invalid")
                if not s.get("body"):
                    E(f"section[{i}] callout missing body")
                c = s.get("cta")
                if c and not (c.get("href") in SLUGS or c.get("href") in {"tel", "book", "forms"}):
                    E(f"section[{i}] callout cta href {c.get('href')!r} not in registry")
        if t == "symptom":
            heads = " | ".join((s.get("heading") or "").lower() for s in secs)
            if "right now" not in heads and "do now" not in heads and "at home" not in heads:
                W("symptom page should have a 'What to do right now' section")

    faqs = d.get("faqs", [])
    if t in {"service", "symptom", "info", "area", "article"} and len(faqs) < 3:
        W(f"only {len(faqs)} faqs (want 3+)")
    for f in faqs:
        if not f.get("q") or not f.get("a"):
            E("faq missing q or a")
    if t == "faq":
        gs = d.get("groups", [])
        n = sum(len(g.get("items", [])) for g in gs)
        if len(gs) < 6 or n < 30:
            W(f"faq page has {len(gs)} groups / {n} questions (want 6+ / 30+)")
    if t == "dictionary":
        terms = d.get("terms", [])
        if len(terms) < 70:
            W(f"dictionary has {len(terms)} terms (want 70+)")
        names = [x.get("term", "") for x in terms]
        if names != sorted(names, key=lambda s: s.lower()):
            W("dictionary terms are not alphabetical")
        for x in terms:
            if x.get("href") and x["href"] not in SLUGS:
                E(f"dictionary term {x.get('term')!r} href {x['href']!r} not in registry")
    if t == "article":
        for k in ["date", "category", "read_time", "summary"]:
            if not d.get(k):
                E(f"article missing {k}")
        if d.get("date") and not re.match(r"^\d{4}-\d{2}-\d{2}$", d["date"]):
            E("article date must be YYYY-MM-DD")

    for r in d.get("related", []) or []:
        if r not in SLUGS:
            E(f"related slug {r!r} not in registry")
        if r == slug:
            W("related links to itself")
    if t == "hub" and d.get("related"):
        W("hub pages should omit related (children auto-listed)")
    cta = d.get("cta") or {}
    if isinstance(cta, dict) and (not cta.get("heading") or not cta.get("body")):
        E("cta needs heading and body")

    # string-level checks
    all_text = []
    for p, s in walk_strings(d):
        all_text.append(s)
        if html_re.search(s) and not p.endswith(".href"):
            E(f"raw HTML in {p}")
        for m in link_re.finditer(s):
            href = m.group(2)
            if href.startswith("http"):
                W(f"external link in {p}: {href} (prefer {{{{book}}}}/{{{{forms}}}} tokens)")
            elif href not in SLUGS:
                E(f"broken internal link in {p}: {href!r}")
        if "—" in s or "–" in s and p.endswith(".body"):
            pass
    joined = "\n".join(all_text)
    low = joined.lower()
    for b in BANNED:
        if b in low:
            E(f"banned phrase: {b!r}")
    for pat, label in FORBIDDEN_FACTS:
        m = re.search(pat, low)
        if m:
            E(f"forbidden content ({label}): {m.group(0)!r}")
    for ph in re.findall(r"\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}", joined):
        if ph.strip() != PHONE_OK:
            E(f"unexpected phone number {ph.strip()!r}")
    if "!" in joined:
        W("exclamation mark present")
    em = joined.count("—")
    if em > 2:
        W(f"{em} em dashes (prefer periods/commas)")
    hours_bad = re.findall(r"\b(9\s?am|9:00 am|5\s?pm|5:00 pm|6\s?pm|6:00 pm)\b.*?(monday|weekday|open)", low)
    if hours_bad:
        W("possible wrong hours mentioned; office hours are 7:00 AM–8:00 PM Mon–Fri, 8:00 AM–1:00 PM Sat–Sun")
    if "opening october 2026" not in low and "october 2026" in low and t != "info":
        pass

    wc = words(body_text(d))
    lo, hi = WORD_TARGETS.get(t, (0, 10**9))
    if wc < lo:
        E(f"word count {wc} below target {lo}")
    elif wc > hi + 200:
        W(f"word count {wc} above target {hi}")
    # location mention
    if t not in {"faq", "dictionary"} and "alexandria" not in low:
        W("no mention of Alexandria")
    return issues


def main(argv):
    if "--all" in argv:
        files = sorted(glob.glob(os.path.join(ROOT, "content", "**", "*.json"), recursive=True))
    else:
        files = [a for a in argv if a.endswith(".json")]
    if not files:
        print(__doc__)
        return 2
    total_err = 0
    for f in files:
        iss = validate(f)
        errs = [i for i in iss if i[1] == "ERROR"]
        total_err += len(errs)
        rel = os.path.relpath(f, ROOT)
        if not iss:
            print(f"{rel} :: OK")
        for p, sev, m in iss:
            print(f"{rel} :: {sev} :: {m}")
    print(f"\n{len(files)} files, {total_err} errors")
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
