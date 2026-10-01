# Ground Truth Project — waiting times at a service point

A hand-collected field study of how long people actually wait, published as a bilingual static
website where **every number on every page is computed from the raw CSV rows** when the site is
built. Nothing is typed into a page by hand, and nothing is invented: change a row in
`data/observations.csv`, rebuild, and the charts, the sentences and the summary change with it.

This repository is the website *and* the source code *and* the raw data, so the file an examiner
checks in the viva is the same file the live site was generated from.

---

## The short version

```bash
py tools/build.py        # regenerate every page from data/
py tools/check.py        # weight, contrast, alt text, links, honesty, freshness
py tools/check.py --publish   # the submission gate: real data, photos, interview, Bangla review
py tools/serve.py        # look at it on http://127.0.0.1:8000/
py tools/tests/run_tests.py   # 34 tests over the engine, the charts and the drawings
```

No Node, no npm, no build tool, no internet connection, no account. Python 3.10+ standard library
only. The site is plain HTML, one CSS file and one optional JavaScript file.

## What is already built

| Piece | Where | Notes |
| --- | --- | --- |
| Home page | `index.html` | the problem in plain words, then the strongest finding, chosen by a stated rule |
| Data page | `data.html` | three charts drawn as inline SVG, each with the source rows printed underneath |
| Places page | `map.html` | labelled plan of the queue area, bubble = number of observations |
| Action page | `action.html` | prepared message, a report form that opens your own email app, print handoff |
| One-page summary | `summary.html` | laid out for A4, ready for the principal or the counter manager |
| Limitations | `limitations.html` | generated from a real audit of the CSV, not written from memory |
| Bangla site | `bn/…` | every page mirrored, wording listed for your review in `docs/bangla-review.md` |
| Raw data | `data/*.csv` | downloadable from the data page, so any figure can be checked |

The engine lives in `tools/`: `build.py` writes the pages, `stats.py` computes every figure,
`charts.py` draws the charts, `art.py` draws the hero, the icons and the pipeline diagram,
`validate.py` and `check.py` refuse to let a broken or dishonest site through, and
`tests/run_tests.py` proves it reacts to data correctly.

## How it looks

The site is built from one palette, one stylesheet template and drawings written as inline SVG, so
it needs no image files, no web fonts and no framework. The look is documented in
`docs/design-notes.md`; the short version is that the colours live in `src/theme.json`, every one of
them is contrast-checked before the site can publish, and the drawn pictures are decoration that
carry no figures at all.

The picture at the top of the home page is a drawing until you give it a photograph: put one in
`data/photos/`, record it in `data/photos.csv` with a caption, alt text and consent, name it in
`hero_photo_file` in `src/site.json` and rebuild. A name that does not match a consented row is
ignored and reported, so nothing can stand in for your own evidence.

## What you still have to supply

Everything here is real, and none of it can be invented by a tool:

1. **20 or more observations** in `data/observations.csv` — one row per wait you stood in or
   watched. The file documents every column at the top; a row with a blank `wait_minutes` is
   still counted, and the site says so instead of guessing.
2. **2 or more places** in `data/places.csv`, with where each sits in the queue area (`diagram_x`,
   `diagram_y`, 0–100).
3. **8 or more photos** in `data/photos/`, listed in `data/photos.csv` with a caption, alt text,
   place and date. The build *fails* if any of those is missing.
4. **One interview** in `data/interview.md`. The answers stay off the site until `consent_ok: yes`.
5. **Your details** in `src/site.json`: name, course, institution, the problem title in both
   languages, the public URL, the repository URL and a contact address for the action page.
6. **A read-through of the Bangla** in `docs/bangla-review.md`, then `reviewer` and
   `reviewed_all: true` in `src/bn-status.json`.

Until those exist, the site deliberately shows an honest "collection in progress" state and no
figures at all. That is not a placeholder: it is the site refusing to print a number it cannot
trace to a row.

## Publishing (GitHub Pages)

```bash
git add .
git commit -m "Add the site"
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

Then on GitHub: **Settings → Pages → Source: Deploy from a branch → Branch: `main` / `root`**.
The generated HTML is committed to the repository, so Pages serves it directly with no build step
of its own. After that, publishing a change is `py tools/build.py && git commit && git push`.

Put the live URL and the repository URL into `src/site.json` (`site_url`, `repo_url`) and rebuild:
the pages then carry correct canonical links, `hreflang` alternates and a `sitemap.xml`.

## How the honesty checks work

* **No typed-in numbers.** Any digit in `src/content.*.json` outside a `{{stat:…}}` token is an
  error. Definitions like "the slowest 10%" are the only exceptions, and they are listed openly in
  `src/number-allowlist.json`.
* **Every figure is traceable.** `data/stats.json` records the row ids behind every statistic, the
  charts print them under each figure, and `check.py` fails if a chart cites a row that is not in
  the CSV.
* **Freshness.** Every page carries `<meta name="data-snapshot">` with a hash of the raw files. Edit
  a CSV without rebuilding and `check.py` fails, naming the page and the hash. The site cannot
  quietly show stale numbers.
* **The tests use synthetic data only.** `tools/tests/run_tests.py` builds throwaway sites in
  temporary folders to prove the maths (including that changing one number changes the chart). None
  of that data can reach `data/` or the published pages.

## Repository map

```
index.html data.html map.html action.html summary.html limitations.html 404.html   generated
bn/                     generated Bangla mirror of every page
assets/                 site.css and app.js (generated), photos/ (copied from data/photos/)
data/                   the raw field data — yours — plus stats.json (generated)
raw/                    your untouched originals; not published (see raw/README.md)
src/                    the source of truth: site.json, theme.json, content.en.json, content.bn.json
tools/                  the build engine, the checks, the local server, the tests
docs/                   method note, AI use log, design notes, Bangla review list, runbook, viva notes
```

**Do not edit the generated files** (`*.html`, `bn/`, `assets/site.css`, `assets/app.js`,
`data/stats.json`, `docs/bangla-review.md`). Edit `src/` or `data/` and run
`py tools/build.py`. The generated CSS and JS say so at the top of the file.

## Licence

Two licences, because the repository holds two different kinds of thing:

| What | Licence | File |
| --- | --- | --- |
| The code — `tools/`, `src/app.js`, `src/site.css.tpl` | MIT | `LICENSE` |
| The study — `data/`, the photographs, `data/interview.md`, the wording in `src/content.*.json`, `docs/`, `README.md` | Creative Commons Attribution 4.0 | `LICENSE-CC-BY-4.0` |

So the software can be reused freely, and the study can be reused by anybody who credits you and
links back — the newspaper, the student union, the counter manager. That is the point of publishing
it. The full CC BY 4.0 legal code is in the repository rather than behind a link.

Two limits worth knowing. The people in the photographs did not licence their own image: they
agreed to appear in *this* study, so keep every face and number plate blurred and never republish a
photo whose recorded consent does not cover the use. And if anybody withdraws consent, delete the
photo from `data/photos/`, drop its row from `data/photos.csv` and rebuild: the page loses the
picture and `py tools/check.py` stays green.

Once `repo_url` is set in `src/site.json`, the footer of every page links to `LICENSE`.
