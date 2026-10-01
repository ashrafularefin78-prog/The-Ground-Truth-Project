# Change request runbook

The assignment says the instructor sends one change request about 24 hours before the deadline, and
that it must be finished and published by the same deadline. The four examples in the brief are
already handled by the way this site is built, so any of them is a short job rather than a rewrite.
Below is exactly what to do for each, plus a generic procedure for a request that is none of them.

**Before the deadline**, do this once so the commands are already in your fingers:

```bash
py tools/build.py         # rebuild
py tools/check.py         # is anything broken or stale?
py tools/serve.py         # look at it at 360 px in the browser
```

Publishing a change is always the same three steps: rebuild, look, commit and push.

---

## 1. "The principal wants a printable one-page summary of your findings. Add it."

**Already built.** `summary.html` and `bn/summary.html` are a print-laid-out A4 page: the headline
finding, the key numbers, one chart, the places measured, what the study does not prove, and the
ask. The print stylesheet hides the navigation and the footer, sets A4 margins, keeps figures from
splitting across pages and adds the URL next to external links.

What is left, if you want it to look sharp:

1. Fill in `src/site.json` (`student_name`, `institution`) and `src/content.en.json` /
   `src/content.bn.json` for the ask (`summary.ask_points`) so the demands are the ones you would
   actually make.
2. `py tools/build.py`, open `summary.html`, press **Print this page**, and choose "Save as PDF" at
   A4 to check it lands on one page. If it spills, remove one item from `summary.ask_points` or turn
   off the places list in `tools/build.py` (the `summary_place_items` call) — but say so in the
   method note.
3. Email the PDF to the person who asked for it, and add a sentence to `docs/method-note.md` that
   it was produced on request.

**Time: 15 minutes.**

## 2. "A new set of 5 observations arrived. Add them and update every chart and sentence that is now wrong."

This is the case the whole design exists for. Nothing needs rewriting, because every chart and every
sentence reads its numbers from the CSV at build time.

1. Append five rows to `data/observations.csv`, continuing the numbering (`OBS-021` …) and giving
   each row its place from `data/places.csv`.
2. `py tools/build.py`
3. Read the rebuild output: it prints how many observations exist, how many have a timed wait, and
   any warnings (for example a row whose `wait_minutes` is blank).
4. `py tools/check.py` — this fails if the pages were not rebuilt, if a chart cites a row that is
   not in the CSV, or if the CSV no longer matches the hash stamped on the pages.
5. Look at `index.html` and `data.html` at 360 px. Three things will have moved on their own: the
   headline finding (the rule that picks it is printed under it), the median and the totals, and the
   limitations page, which recounts its own gaps.
6. Only hand-edit prose if a sentence is now *wrong in kind* rather than in number — for example if
   the new rows change the headline from "the slowest place" to "the share of long waits", in which
   case the sentence changes by itself too. Numbers never need editing by hand, and typing one in is
   blocked by the checker.

**Time: 15 minutes, most of it typing the rows.**

## 3. "Make the site work with no JavaScript for the main content."

**Already true.** Every sentence, number, chart, table, link and form label is in the HTML that
`py tools/build.py` writes. `assets/app.js` only adds three optional conveniences: a copy button,
a print button, and the handoff that opens your email program. With JavaScript disabled you still
get the whole study; the action page tells the reader to select and copy the prepared message
themselves.

To prove it and to record the proof:

1. `py tools/check.py` — it lints `assets/app.js` and fails if it ever creates or rewrites page
   text (`innerHTML`, `textContent =`, `document.write`). That is the automated half of the
   argument.
2. Open the site with JavaScript disabled (Chrome: DevTools → Settings → Debugger → "Disable
   JavaScript"), or from the command line: `py tools/serve.py` and check the pages in a text
   browser. Every page must show its full content.
3. Write the result in `docs/method-note.md` and add the screenshot to your submission folder.

If the request instead insists on *removing* JavaScript, delete the `<script>` tag from
`tools/build.py` and rebuild; nothing else changes, because nothing depends on it.

**Time: 10 minutes.**

## 4. "Your chosen finding is disputed. Add a 'Limitations' section that honestly shows what your data cannot prove."

**Already built, and generated rather than written.** `limitations.html` and `bn/limitations.html`
are produced from an audit of your own CSV at build time, so they cannot flatter the study. The page
has four parts:

- **what the gaps are** — how many rows are still missing against the target, which places have too
  few timed waits to compare, how many waits were estimated rather than timed, which parts of the day
  have no rows at all, how many rows have no photo;
- **what the data cannot prove** — no cause, no baseline, one observer watching one queue at a time,
  self-selected times, weather and term dates uncontrolled, and no claim about anywhere else;
- **cells left blank** — every column with blanks, counted;
- **what would make it stronger** — the honest next steps.

If the examiners want the disputed finding itself addressed by name:

1. Put the counter-argument in `src/content.en.json` (and the Bangla in `src/content.bn.json`) under
   `limitations`, or add a new `finding_…` sentence, then rebuild.
2. Add the numbers that settle it as `{{stat:…}}` tokens rather than prose, so the section cannot
   drift from the data.
3. Say in `docs/method-note.md` what was disputed and what you changed.

**Time: 20 minutes.**

## Anything else

1. **Read the request twice.** Write down, in one line, what it wants the reader to be able to do
   that they cannot do now.
2. **Decide which file owns it:** wording → `src/content.en.json` and `src/content.bn.json`; a new
   column or a new kind of evidence → `data/*.csv` plus the loaders in `tools/dataset.py`; a new
   figure → `tools/stats.py` plus a chart in `tools/charts.py`; a new page → a `…_page` method in
   `tools/build.py` and its name in the `PAGES` list.
3. **Change the smallest thing that satisfies the request**, then `py tools/build.py`.
4. `py tools/check.py` — and if it complains, fix the complaint rather than disabling the check.
   Every failing check is one of the assignment's requirements.
5. Look at the affected pages at 360 px, in both languages.
6. Commit with a message that names the change request, push, and open the live URL to confirm the
   new version is up.
7. Write two lines in `docs/ai-use-log.md`: what you asked the assistant for, and what you had to
   correct. That log entry is worth marks, and it is only honest if it is written while you remember
   the details.

**Rehearse this section before the deadline**, on a throwaway change (for example: add a sentence
to the home page that quotes the median). The whole point of the surprise request is that it tests
whether you know your own repository, and a rehearsal is the cheapest way to find that you do not.
