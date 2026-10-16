# Building The World Then from source

This folder is the corresponding source of the deployed site. The software in
it (the markup, styles, scripts, and the build script) is published under The
World Then Noncommercial ShareAlike License 1.0 (../LICENSE-TWT-NC-SA-1.0.txt).
The About page's prose and the project's other original creative content are
CC BY-NC-SA 4.0, and third-party material keeps its own licenses; ../LICENSE.md
lists the components. Each deployed release is tagged `release-<n>`
in this repository; the About page of every build names the release it was
built from, so a downloaded `the-world-then.html` can be matched to its exact
source here.

## What is here

- `app.html` — the atlas page: markup, styles, and scripts, unminified. The
  deployed `index.html` is this file with `?v=` content-hash stamps on its
  data and asset links and the preview `noindex` meta inserted by the build.
- `about.html` — the About page source; the built `about.html` differs only by
  the stamped fonts link, the release label, and the same meta.
- `build.py` — the build. It writes `index.html`, `about.html`, and the
  self-contained `the-world-then.html` (data, libraries, and fonts link
  inlined) into the repository root.

Everything the build reads is in this repository: `data/` (the baked dataset
and basemap), `vendor/` (d3, topojson-client, flubber), and `fonts/`. The
bake pipeline that produced `data/` from Wikidata, Wikipedia, and the
historical-basemaps sheets is not part of the software offered here; the
data keeps the licenses listed in `LICENSE.md` and on the About page.

## Build

Requires Python 3 (standard library only).

    python3 source/build.py            # preview build: pages carry a robots noindex meta
    python3 source/build.py --launch   # launch build: no robots meta

Run it from the repository root. The build is deterministic: the same inputs
produce byte-identical pages, and the deploy tooling checks that before
publishing.

## Run

`the-world-then.html` opens directly in a browser (file:// works; fonts load
from Google Fonts when online). `index.html` fetches `data/` and `vendor/` at
runtime, so serve the folder over HTTP, for example:

    python3 -m http.server 8000

and open http://localhost:8000/.
