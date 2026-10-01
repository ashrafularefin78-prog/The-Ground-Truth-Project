# AI use log

Required by the assignment: prompts, edits, rejections, and five places where the AI was wrong.
This log is written as the work happens, not after it, and it records failures even when they were
my own fault for accepting the output without checking.

**Tools used:** an AI coding assistant (Codebuff / Buffy) inside the editor, plus the AI features
of the editor itself. No image generation, no invented survey data, no text-generating shortcut for
the Bangla (see the review list in `docs/bangla-review.md`, which is generated from the real
`src/content.bn.json` and read by hand).

**Standing instruction I gave the assistant:** every number on the site must be computed from
`data/observations.csv` at build time, and no sentence may contain a typed-in number. That was
enforced in code rather than trusted, and it is the reason `py tools/check.py` fails when a digit
appears in a sentence without a `{{stat:…}}` token.

## What the AI did, and what I did with it

| Prompt (short) | What the AI produced | My change or decision |
| --- | --- | --- |
| "Read this assignment PDF and tell me what it is actually asking for" | a summary of the requirements and a list of the four likely surprise change requests | kept; I checked it against the PDF myself |
| "Plan the site so charts update when the CSV changes, with no Node installed" | a plan using a Python-stdlib generator that bakes charts into static SVG | accepted after I rejected the first idea of drawing charts in the browser, because the likely change request "make it work with no JavaScript" would break it |
| "Write the build so a page cannot print a number that is not in the CSV" | `{{stat:…}}` tokens, `data/stats.json` with row ids, and a checker that fails on a typed-in digit | accepted; this is the part I understand best and the part I would explain first in the viva |
| "Generate the Bangla pages" | a first draft of every Bangla string | **not accepted as final**: listed in `docs/bangla-review.md`, read through line by line, and `src/bn-status.json` only flips to `reviewed_all` when I have done that |
| "Draw the three charts as SVG with no library" | `tools/charts.py` | accepted, then changed by hand: font sizes raised and tick labels thinned after I measured them at 360 px |
| "Add a limitations page" | a template with fixed sentences | rejected as too generic; replaced with findings computed from an audit of the CSV (blank cells, parts of the day not covered, estimates, places with too few observations) |
| "Write the method note" | the structure and the rules the code actually follows | kept for the factual parts; every section marked *in my own words* is mine |

## Five AI failures

These are the five that actually happened, with what I did about them. Every one was caught by
checking the output against the real thing rather than by trusting the answer.

### 1. It could not read the assignment PDF, and its first attempt failed silently

The first attempt to extract the text of the assignment used `python`, which is not on the PATH on
this machine, and a text-scraping shortcut that returned nothing at all. It looked like the PDF was
empty. I only noticed because the output was blank instead of being an error.

**Fix:** read the PDF's compressed streams directly (`zlib` + ASCII85) with the `py` launcher that
is actually installed, and print the text page by page to confirm all four pages came out.

**Lesson:** an assistant that says "done" with no output is worse than one that fails loudly. Every
tool in `tools/` now prints what it did, and fails rather than passing quietly.

### 2. It shipped a chart colour bug that no test caught

The generated CSS referred to `--series_1` while the generator emitted `--series-1`. CSS does not
complain about an undefined custom property: it silently fell back to black, so every bar in every
chart was black, and the running-total line lost its colour too. The tests passed, because the
tests check numbers and structure, not colour.

**Fix:** found by actually opening the site on the phone width and looking at it, then aligning the
names. `tools/check.py` now recomputes every contrast ratio in `src/theme.json` so the palette is
checked as arithmetic rather than by eye.

**Lesson:** colour and layout have to be looked at, not asserted. A green test suite is not a
screenshot.

### 3. It designed for a desktop and called the page responsive

The first version of the pages put a four-column summary table and a six-column data table on the
page with `white-space: nowrap`. At 360 px the page itself did not scroll sideways, so by a literal
reading nothing was broken — but the tables needed sideways scrolling inside their own box, which
is exactly what the assignment says not to do on a phone. A long chart footnote was also printed
inside a fixed-width SVG and simply got cut off mid-word.

**Fix:** the summary became a stacked list, and under 34 rem every data table row now becomes a
small labelled block using the column name written into `data-label` by the build; the footnote moved
out of the chart and into the figure caption.

**Lesson:** measure at the real width instead of trusting the word "responsive". I now check
`scrollWidth` at 360 px in the browser for every page.

### 4. It wrote a CSS selector that quietly reached across the whole drawing

While modernising the look, the assistant drew the pipeline diagram (`data/*.csv` → `stats.json` →
the pages) as one SVG with three nodes, and coloured the text inside the accent node with a CSS
*sibling* selector (`.flow-node-accent ~ .flow-sub`). Every node has the same parent — the `<svg>` —
so that selector also matched the labels in the other two nodes and painted them the **page**
colour: dark text on a dark panel, invisible in dark mode, and nothing in the test output changed.

**Fix:** each step is now wrapped in its own `<g class="flow-node-group">` and the CSS uses
descendant selectors, so a node's colours stay inside that node. The regression is now guarded by a
test that checks the diagram's text in both languages.

**Lesson:** "it looked right in one theme" is not a check. I looked at the dark mode first, and the
text was black on black. Grepping the generated CSS for a selector is faster than arguing with it.

### 5. It left two axis labels drawn on top of each other

The first version of the reconstructed histogram put "observations" and "minutes" on the same
baseline at the bottom, sitting 4 px apart — readable in the code, visibly wrong on the page. The
running-total chart also printed its last value inside the plot area, where it could collide with
the gridline.

**Fix:** the y-axis title is now written up the left edge (rotated), and the running total is drawn
in a chip that is clamped inside the panel. The lesson is the same as failure 2, one level down: a
chart is a picture, and a picture has to be looked at.

## A limit of AI that is not a bug

The assignment requires at least 15 meaningful commits spread over at least 3 days. AI can help
write the code in one sitting, but the history is the evidence that the work happened over days,
and backdating commits would be a lie that is trivially visible in the commit graph. So no commit
in this repository is backdated: the commit plan in `docs/commit-plan.md` is followed on real days,
and if a day is skipped the history shows it.

The same applies to the field data, the photos and the interview. They are collected by hand, from
places I physically stood in, and no tool in this repository will generate them: the build fails
rather than filling a gap.

There is a second, smaller version of the same problem in the look of the site. The assistant could
draw the queue illustration, the icons and the charts, but it cannot know what the real queue looks
like, or which photograph matters. So the drawn pictures are kept as decoration — hidden from
screen readers, carrying no figures — and the one picture that shows something real is still a
photograph I have to take.
