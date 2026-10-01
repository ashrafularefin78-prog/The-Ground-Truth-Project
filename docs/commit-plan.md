# Commit plan

The assignment asks for **at least 15 meaningful commits spread over at least 3 different days**.
This plan has **28**, in a day-by-day order that matches how the work was actually done, each one a
coherent slice with a message worth reading. The first seven are already in the history (day 1); the
rest are the order to follow.

## Three rules before you start

1. **Never backdate a commit.** `GIT_COMMITTER_DATE` and `git commit --date` can fake the graph, and
   an examiner can see it in one command (`git log --format='%ad %s'`). Work the days, or show the
   honest gaps.
2. **Rebuild and check before every commit.** The repository root *is* the published site, so a
   source change is only real once `py tools/build.py` has rewritten the pages:

   ```bash
   py tools/build.py
   py tools/check.py          # must print 0 errors before you commit
   ```

3. **Stage exactly what the row lists, never `git add -A`.** The tree on disk already holds the
   finished files, so this plan is a *review order*: each commit stages one coherent part of them.
   No file appears in two commits, except the generated output in the two "regenerate" commits,
   which is regenerated on purpose. That keeps every commit real: nothing is staged twice, and
   nothing is dressed up as an edit that never happened.

Once, at the start:

```bash
cd <this folder>
git init
git branch -M main
```

Every commit follows this shape:

```bash
py tools/build.py
py tools/check.py
git add <exactly the files in the row>
git commit -m "<the message>"
```

---

## Day 1 — the data contract and the engine

| # | Message | Files |
| --- | --- | --- |
| 1 | `chore: ignore python caches and keep raw originals out of git` | `.gitignore`, `raw/README.md` |
| 2 | `feat(data): define the observation, place and photo schemas` | `data/observations.csv`, `data/places.csv`, `data/photos.csv` |
| 3 | `feat(data): add the interview note format with a consent field` | `data/interview.md` |
| 4 | `feat(config): add the site identity, the palette and the checked contrast pairs` | `src/site.json`, `src/theme.json`, `src/bn-status.json`, `src/number-allowlist.json` |
| 5 | `feat(engine): read the raw csvs and type every field` | `tools/common.py`, `tools/dataset.py` |
| 6 | `feat(engine): compute every figure with the rows it came from` | `tools/stats.py` |
| 7 | `chore: license the code under mit and the written study under cc by` | `LICENSE`, `LICENSE-CC-BY-4.0` |

Commit 6 is the one to be able to explain: `tools/stats.py` is where a blank cell stays blank, where
the median and the buckets come from, and where the headline finding is chosen by a rule.

Commit 7 is the licence, and it is split for a reason: MIT for the software, CC BY 4.0 for the
study, so the code can be reused freely and the study can be reused by anybody who credits it. The
full legal code is committed rather than linked, so the repository still says what it is if the
link rots. The copyright line reads "the author of this repository" until you put your own name into
both files — do that before your first push, while the history is still only yours to read.

**End of day 1 — stop here and commit nothing else.** Tomorrow's commits must land on a real
tomorrow.

## Day 2 — the site itself

| # | Message | Files |
| --- | --- | --- |
| 8 | `feat(art): draw the hero, the icons and the pipeline diagram as inline svg` | `tools/art.py` |
| 9 | `feat(charts): draw the charts as inline svg with gradients and value chips` | `tools/charts.py` |
| 10 | `feat(content): write the english and bangla wording using data tokens only` | `src/content.en.json`, `src/content.bn.json` |
| 11 | `feat(style): add the design system stylesheet and the enhancement script` | `src/site.css.tpl`, `src/app.js` |
| 12 | `feat(build): generate every page, with the hero and the metric band on top` | `tools/build.py` |
| 13 | `feat(check): verify page weight, contrast, alt text and freshness` | `tools/validate.py`, `tools/check.py` |
| 14 | `feat(dev): serve the built site locally for phone-width testing` | `tools/serve.py` |

Commit 10 deliberately does not mark the Bangla as reviewed: that switch stays off until you have read
`docs/bangla-review.md` line by line, which is why `src/bn-status.json` is committed on day 1 with
`reviewed_all: false` and signed off later.

## Day 3 — verification, fixes and the write-up

| # | Message | Files |
| --- | --- | --- |
| 15 | `test(engine): prove the charts follow the csv and the drawings stay decoration` | `tools/tests/run_tests.py` |
| 16 | `docs: add the method note and the ai use log, including five real ai failures` | `docs/method-note.md`, `docs/ai-use-log.md` |
| 17 | `docs: write down the design system and the hero picture rule` | `docs/design-notes.md` |
| 18 | `docs: add the change request runbook and the viva preparation` | `docs/change-request-runbook.md`, `docs/viva-prep.md` |
| 19 | `docs: add the readme, the licence section and this commit plan` | `README.md`, `docs/commit-plan.md` |
| 20 | `chore(build): publish the generated pages for the first time` | `*.html`, `bn/*.html`, `assets/site.css`, `assets/app.js`, `data/stats.json`, `docs/bangla-review.md`, `robots.txt`, `.nojekyll` |

Two drawing bugs were found here by looking at the pages rather than by the tests: a CSS sibling
selector reached across the whole pipeline diagram and painted two of its three nodes in the page
colour, and the reconstructed histogram drew its two axis titles on the same baseline. Because
`tools/art.py`, `tools/charts.py` and `src/site.css.tpl` are each committed once, that work sits
inside commits 8, 9 and 11 instead of in a separate fix commit — and both failures are written up
with what I did about them in `docs/ai-use-log.md` (failures 4 and 5), which is where the debugging
history is worth reading anyway.

## The days that are genuinely yours — the field data

| # | Message | Files |
| --- | --- | --- |
| 21 | `feat(data): add the first field observations` | `data/observations.csv`, `data/places.csv` |
| 22 | `feat(data): add the photo evidence with captions and alt text` | `data/photos.csv`, `data/photos/*` |
| 23 | `feat(data): add the interview with consent recorded` | `data/interview.md` |
| 24 | `docs: sign off the bangla wording after reading every line` | `src/bn-status.json`, `docs/bangla-review.md` |
| 25 | `feat(site): set the identity, the public url and the hero picture` | `src/site.json` |
| 26 | `chore(build): regenerate every page from the real data` | `*.html`, `bn/*.html`, `assets/site.css`, `data/stats.json`, `docs/bangla-review.md`, `sitemap.xml` |

After commit 26, run the submission gate for the first time:

```bash
py tools/check.py --publish
```

## Deadline day — the change request

| # | Message | Files |
| --- | --- | --- |
| 27 | `feat: answer the change request` | whatever the request touches |
| 28 | `chore: regenerate and publish the change request version` | the regenerated output |

Follow `docs/change-request-runbook.md`, and commit the request and the fix (27) separately from the
regenerated output (28), so the history shows the request landing and the site following it.

## Publishing, once

```bash
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

Then on GitHub: **Settings → Pages → Source: Deploy from a branch → `main` / `root`**. From then on,
every push is a deploy, and running `py tools/check.py` before the push is what keeps a broken page
off the live site.

## Checking the history at the end

```bash
git log --format='%ad %s' --date=short      # the days, with no faked dates
git log --stat | grep -c '^ '               # roughly how much changed per commit
git log --oneline | wc -l                    # the count the assignment asks about
```
