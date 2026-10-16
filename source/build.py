#!/usr/bin/env python3
# Copyright (c) 2026 Michael Manning — The World Then Noncommercial ShareAlike License 1.0 (see LICENSE.md)
"""
Build The World Then from one source template into two outputs:

  index.html                  - multi-file version, fetches data/ + vendor/ at
                                runtime (for GitHub Pages; needs a web server to
                                test locally because browsers block fetch() over
                                file://)
  the-world-then.html         - single self-contained file with everything
                                inlined (open directly via file://, no server)

Source of truth (paths relative to the handoff bundle root, one level up):
  source/app.html
  source/about.html          (About/methodology page -> copied to about.html)
  data/countries-50m.json    (drawn land layer since (171); the bake's NE-2024
                              keyframe source stays data/countries-110m.json)
  data/civs-app.json         (BAKED map model — tools/bake/payload.mjs)
  data/enrichment.json       (BAKED panel data: rulers/events/people/cities/wars)
  data/hydro.json            (rivers/lakes overlay — Natural Earth, public domain)
  vendor/flubber.min.js

Run:  python3 source/build.py   (from the bundle root)
  or: cd source && python3 build.py

RELEASE ((213), 2026-10-16): every deployed build names its release so a
downloaded standalone can be matched to the exact published source (the
license's matching-source route). Bump RELEASE for every deploy; after the
push, tag the public commit release-<RELEASE>. The export validator refuses
to stage a release whose tag already exists with different bytes.
"""
import base64
import gzip
import hashlib
import io
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# ---- indexing policy ((211), 2026-10-16): the site is reachable but shared
# privately while bugs are fixed. Every built page carries a robots NOINDEX
# meta by default (the 404 has its own, permanent one). robots.txt ALLOWS
# crawling on purpose: a Disallow would stop crawlers from ever reading the
# noindex, and a disallowed-but-known URL can still be listed. THE LAUNCH
# SWITCH IS EXPLICIT: `python3 source/build.py --launch` lifts the meta from
# index / about / the standalone; nothing else changes at launch. The export
# validator (tools/export-public.mjs) refuses a mismatch either way.
LAUNCH = "--launch" in sys.argv[1:]
RELEASE = "213"
RELEASE_TOKEN = "@@RELEASE@@"
def release(page, name, expect):
    assert page.count(RELEASE_TOKEN) == expect, f"{name}: expected {expect} release token(s), found {page.count(RELEASE_TOKEN)}"
    return page.replace(RELEASE_TOKEN, RELEASE)
VIEWPORT = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
NOINDEX  = '<meta name="robots" content="noindex">'
def policy(page, name):
    assert page.count(VIEWPORT) == 1, f"viewport meta not unique in {name}"
    assert NOINDEX not in page, f"{name} already carries a robots meta — the build owns it"
    return page if LAUNCH else page.replace(VIEWPORT, VIEWPORT + "\n" + NOINDEX)
print("LAUNCH BUILD — pages carry no robots meta (indexable)" if LAUNCH else
      "PREVIEW BUILD — every page carries <meta name=\"robots\" content=\"noindex\">; `--launch` lifts it")
SRC  = release((ROOT/"source/app.html").read_text(), "app.html", 4)
TOPO = (ROOT/"data/countries-50m.json").read_text()
CIVS = (ROOT/"data/civs-app.json").read_text()
ENRI = (ROOT/"data/enrichment.json").read_text()
HYDR = (ROOT/"data/hydro.json").read_text()
FLUB = (ROOT/"vendor/flubber.min.js").read_text()
D3   = (ROOT/"vendor/d3.min.js").read_text()
TOPJ = (ROOT/"vendor/topojson.min.js").read_text()

# ---- cache-busting (H round, 2026-08-03): stamp fetched/linked assets with a
# content-hash query string so a fresh index.html always pulls matching assets
# through GitHub Pages' 10-minute cache (and any longer-lived proxy). The hash
# changes exactly when the file does, so unchanged deploys still diff clean.
def _v(text): return hashlib.md5(text.encode()).hexdigest()[:8]
def stamp(page, ref, content):
    versioned = f"{ref}?v={_v(content)}"
    assert page.count(ref) >= 1, f"cache-bust target missing: {ref}"
    return page.replace(f'"{ref}"', f'"{versioned}"')

FONTCSS = (ROOT/"fonts/fonts.css").read_text()

# ---- about.html: self-contained (no JS, no data deps) — fonts link stamped ----
ABOUT = release((ROOT/"source/about.html").read_text(), "about.html", 2)
ABOUT = stamp(ABOUT, "fonts/fonts.css", FONTCSS)
ABOUT = policy(ABOUT, "about.html")
(ROOT/"about.html").write_text(ABOUT)
print(f"about.html                  {len(ABOUT)//1024:>4} KB  (About/methodology page, self-contained)")

# ---- multi-file index.html: fetch data + vendor at runtime ----
# source/app.html already contains the bootData() fetch logic and <script src="vendor/...">
INDEX = SRC
for ref, content in [("data/countries-50m.json", TOPO), ("data/civs-app.json", CIVS),
                     ("data/hydro.json", HYDR), ("data/enrichment.json", ENRI),
                     ("vendor/d3.min.js", D3), ("vendor/topojson.min.js", TOPJ),
                     ("vendor/flubber.min.js", FLUB), ("fonts/fonts.css", FONTCSS)]:
    INDEX = stamp(INDEX, ref, content)
INDEX = policy(INDEX, "index.html")
(ROOT/"index.html").write_text(INDEX)
print(f"index.html                  {len(INDEX)//1024:>4} KB  (multi-file, fetches data/ + vendor/)")

# ---- standalone: inline flubber + ALL data as ONE gzip blob (encoding round,
# 2026-07-14). base64(gzip(json)) is ~1/4 the raw JSON; the app's bootData
# inflates it natively via DecompressionStream (window.__PACKED branch in
# source/app.html) — byte-identical data, no custom format to drift.
# mtime=0 keeps the gzip DETERMINISTIC so rebuilt-without-changes diffs clean.
combined = '{"topo":'+TOPO+',"tl":'+CIVS+',"hydro":'+HYDR+',"enr":'+ENRI+'}'
buf = io.BytesIO()
with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=9, mtime=0) as gz:
    gz.write(combined.encode("utf-8"))
packed = base64.b64encode(buf.getvalue()).decode("ascii")
# the standalone is truly self-contained since the H round (2026-08-03): d3 +
# topojson are inlined alongside flubber (before, they still loaded from cdnjs —
# the "no server needed" file quietly required a network for its two core libs).
# Fonts are the one deliberate exception: a lone file has no fonts/ directory, so
# the local stylesheet is swapped back to the Google Fonts CDN; offline it falls
# to the (7-15) system fallback stacks, exactly as before.
GOOGLE_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600&family=Cinzel:wght@700&display=swap">'
)
assert SRC.count('<link rel="stylesheet" href="fonts/fonts.css">') == 1
assert SRC.count('<script src="vendor/d3.min.js"></script>') == 1
standalone = SRC.replace('<link rel="stylesheet" href="fonts/fonts.css">', GOOGLE_FONTS)
# Relative about-links are DEAD over file:// (the standalone travels alone —
# there is no about.html beside it). Same swap-to-absolute rule as the fonts:
# online they land on the real page, offline the browser just says so ((137)).
assert standalone.count('href="about.html"') == 2
standalone = standalone.replace('href="about.html"', 'href="https://theworldthen.com/about.html"')
standalone = standalone.replace('<script src="vendor/d3.min.js"></script>', '<script>'+D3+'</script>')
standalone = standalone.replace('<script src="vendor/topojson.min.js"></script>', '<script>'+TOPJ+'</script>')
standalone = standalone.replace(
    '<script src="vendor/flubber.min.js"></script>',
    '<script>'+FLUB+'</script>\n<script>window.__PACKED="'+packed+'";</script>'
)
standalone = policy(standalone, "the-world-then.html")
(ROOT/"the-world-then.html").write_text(standalone)
print(f"  packed data blob: {len(combined)//1024} KB json -> {len(packed)//1024} KB base64-gzip")
print(f"the-world-then.html         {len(standalone)//1024:>4} KB  (single file, open via file://)")
print(f"release {RELEASE} (tag the public commit release-{RELEASE} after the push)")
print("done.")
