#!/usr/bin/env python3
"""Build the published pages from index.html.

index.html is the source (Shevi & Rupesh). Each page differs only in the
PAGE config line and the <title>. Writes:
  couple.html                     standalone copy for Shevi & Apurva
  <out>/junk-facts.html           artifact body (no doctype/head) for each page
Usage: python3 tools/build.py [OUT_DIR]
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = {
    "junk-facts.html": {"title": "Junk Facts", "config": None},
    "junk-facts-couple.html": {
        "title": "Junk Facts Together",
        "config": 'const PAGE = {names:["Shevi","Apurva"], relation:"partner", pair:"a couple", url:"https://claude.ai/artifact/PsnkUKxs1JenvSvrZGz5Ta"};',
        "standalone": "couple.html",
    },
}

def body(src):
    head = src.split("<!-- APP:START -->", 1)[1].split("<!-- APP:HEAD-END -->", 1)[0]
    main = src.split("<!-- APP:BODY-START -->", 1)[1].split("<!-- APP:END -->", 1)[0]
    return head.strip("\n") + "\n" + main.strip("\n") + "\n"

def variant(src, page):
    out = src
    if page["config"]:
        out, n = re.subn(r"^const PAGE = \{.*\};$", page["config"], out, count=1, flags=re.M)
        assert n == 1, "PAGE config line not found"
    out = out.replace("<title>Junk Facts</title>", "<title>%s</title>" % page["title"], 1)
    return out

def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "dist")
    os.makedirs(out_dir, exist_ok=True)
    src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    couple_url = os.environ.get("COUPLE_URL", "")
    for name, page in PAGES.items():
        v = variant(src, page)
        if couple_url:
            v = v.replace("https://claude.ai/artifact/COUPLE_URL", couple_url)
        open(os.path.join(out_dir, name), "w", encoding="utf-8").write(body(v))
        if page.get("standalone"):
            open(os.path.join(ROOT, page["standalone"]), "w", encoding="utf-8").write(v)
        print("wrote", name)

if __name__ == "__main__":
    main()
