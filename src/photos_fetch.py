#!/usr/bin/env python3
"""Download and size the placeholder photos listed in photos.json.

    python3 src/photos_fetch.py            # fetch any slot whose file is missing
    python3 src/photos_fetch.py --force    # re-fetch everything

Each slot in photos.json has an Unsplash photo id in "source". This script downloads it from the Unsplash
image CDN at the sizes the site uses, writes the files into assets/img/photos/, fills in width/height,
and rewrites CREDITS.md. When the office has real photos, drop them in with the same file names (or edit
the "file" field) and this script is no longer needed.
"""
import json, os, sys, subprocess, struct

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "assets", "img", "photos")
MANIFEST = os.path.join(ROOT, "photos.json")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
SIZES = {"hero-office": (2400, 1200)}      # slot: (large width, small width); default below
DEFAULT = (1600, 900)


def jpeg_size(path):
    """Return (w, h) of a JPEG without PIL."""
    with open(path, "rb") as f:
        data = f.read()
    i = 2
    while i < len(data):
        if data[i] != 0xFF: i += 1; continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", data[i + 5:i + 9]); return w, h
        seg = struct.unpack(">H", data[i + 2:i + 4])[0]; i += 2 + seg
    return None, None


def fetch(pid, width, dest):
    url = f"https://images.unsplash.com/{pid}?w={width}&q=80&auto=format&fit=max&fm=jpg"
    r = subprocess.run(["curl", "-sL", "--max-time", "90", "-A", UA, url, "-o", dest], capture_output=True)
    ok = r.returncode == 0 and os.path.exists(dest) and os.path.getsize(dest) > 10000
    if not ok and os.path.exists(dest): os.remove(dest)
    return ok


def main():
    force = "--force" in sys.argv
    os.makedirs(OUT, exist_ok=True)
    m = json.load(open(MANIFEST, encoding="utf-8"))
    credits = ["# Placeholder photo credits", "", "Free-to-use photos from Unsplash (https://unsplash.com/license), used as placeholders until the office's own photography is ready.", ""]
    for slot, p in m.items():
        pid = p.get("source")
        big, small = SIZES.get(slot, DEFAULT)
        f_big = p.get("file") or f"{slot}.jpg"; f_small = p.get("file_sm") or f"{slot}-sm.jpg"
        p["file"], p["file_sm"] = f_big, f_small
        for fname, w in ((f_big, big), (f_small, small)):
            dest = os.path.join(OUT, fname)
            if force or not os.path.exists(dest):
                if not pid: print(f"{slot}: no source and no file, skipping"); continue
                print(f"{slot}: fetching {fname} ({w}px)")
                if not fetch(pid, w, dest): print(f"  FAILED {fname}")
        if os.path.exists(os.path.join(OUT, f_big)):
            p["width"], p["height"] = jpeg_size(os.path.join(OUT, f_big))
        if os.path.exists(os.path.join(OUT, f_small)):
            p["width_sm"], _ = jpeg_size(os.path.join(OUT, f_small))
        if pid:
            credits.append(f"- `{f_big}` ({slot}): https://unsplash.com/photos/{pid.replace('photo-', '')} — {p.get('credit', 'Unsplash')}")
    json.dump(m, open(MANIFEST, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    open(os.path.join(OUT, "CREDITS.md"), "w").write("\n".join(credits) + "\n")
    print("done:", len(m), "slots")


if __name__ == "__main__":
    main()
