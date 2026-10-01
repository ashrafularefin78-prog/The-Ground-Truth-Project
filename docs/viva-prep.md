# Viva preparation

The viva tests whether you understand the code you handed in. Everything below is the shortest
honest route to being able to answer that, file by file, plus four drills to rehearse.

## The two meanings of "ground truth" in your answer

Say this early, in one sentence: *the site is not a description of a problem, it is a record of
measurements, and the measurements are the file.* Every claim on every page is generated from
`data/observations.csv`, so the first thing to open in the viva is not the website but the CSV.

## Numbers you should be able to say from memory

Open `data/stats.json` and learn three: how many observations, the median wait, and the longest
wait. If asked "what does the site claim?", you answer with those three and then point at the page
where each appears.

## "Explain any two lines or functions"

`tools/` is roughly 2,000 lines and most of it is error messages. These are the parts worth being
able to read cold.

| Where | What to say |
| --- | --- |
| `tools/common.py` → `read_csv` | Reads the file, skips lines starting with `#` so the raw CSV can document its own columns, then hands the rest to `csv.DictReader`. It never invents a value: a blank cell stays empty. |
| `tools/common.py` → `fmt_num` | Prints `7` for 7.0 and `7.5` for 7.5, so a whole number never gains a decimal point it did not earn. |
| `tools/common.py` → `data_fingerprint` | Hashes the raw files (sha256). The short hash is stamped into every page as `<meta name="data-snapshot">`, which is how the checker proves a page was not built from an older CSV. |
| `tools/dataset.py` → `derive_day_part` | Turns a clock time into morning/afternoon/evening/night at the boundaries documented in the CSV comment, so the part of the day is derived rather than guessed. |
| `tools/dataset.py` → `parse_interview` | Reads the note format: `key: value` header lines, then `Q/B/A/C` blocks separated by `---`. Answers are published only when `consent_ok` is yes. |
| `tools/stats.py` → `_buckets` | Fixed-width buckets on the wait axis. The last bucket is labelled `45+` **only** when a value actually reaches its upper edge, so the axis never claims more than the data. |
| `tools/stats.py` → `_headline` | Picks the finding by a rule, in order: the place with the highest median among places with at least *n* timed waits; otherwise the share of waits over the threshold; otherwise the single longest wait; otherwise it says there is nothing to show. The rule that fired is printed under the headline. |
| `tools/stats.py` → `_audit` | Builds the limitations page from the data: blank cells, uncovered parts of the day, estimated waits, places with too few rows, rows without photos. |
| `tools/charts.py` → `histogram` | The bars and the median line share one linear value axis (0 to the last bucket's edge), which is what makes it honest to draw a continuous median line across discrete bars. |
| `tools/content.py` → `t` | Replaces every `{{namespace:key}}` token with a value from `stats.json`, escapes anything that came from the CSV, and refuses to print when the value is `None` rather than printing a dash. |
| `tools/content.py` → `find_bare_numbers` | Finds a digit in a sentence outside a token. That is the check that stops a number being typed into the wording by hand. |
| `tools/build.py` → `table` | Writes each column name into `data-label` on every cell, which is what lets the stylesheet turn a wide table into stacked labelled rows on a phone with no JavaScript. |
| `tools/check.py` → `_luminance` / `contrast_ratio` | The WCAG contrast formula, applied to the pairs listed in `src/theme.json`. Accessibility is checked as arithmetic rather than by eye. |
| `tools/check.py` → `strip_comments` | The no-JavaScript lint ignores comments before looking for `innerHTML` and friends, so the rule can be explained in the file without tripping itself. |
| `tools/art.py` → `hero_scene` | The hero drawing. Decorative: `aria-hidden`, no text, no numbers — so a drawing can never be read out as a measured figure. Its colours come from CSS classes, including the gradient. |
| `tools/art.py` → `wait_meter` | The only drawing that states a figure. The percentage is passed in by the build, and the accessible name is the same sentence that is printed beside the ring, so the two cannot disagree. |
| `tools/build.py` → `hero_media` | Chooses the author's photograph or the drawn illustration. A file name only wins if it matches a consented row of `data/photos.csv`, so no image can stand in for evidence. |

If you are asked about a line you do not recognise, the honest answer is "I would need to open it",
then open it and read it out. The repo is organised so that is a reasonable answer:
`grep -rn "the words you saw" tools/`.

## "Make a small live edit"

Four drills, in increasing difficulty. Rehearse at least the first two.

**1. Change a chart colour rule (2 minutes).**
Open `src/theme.json`, change `light.series_1` from `#4338e0` to `#0d7a44`, run `py tools/build.py`.
Every bar and every node in the map moves to the second colour, because the drawings carry classes
and only the stylesheet holds colours. Now run `py tools/check.py`: it recomputes the contrast ratio
for `chart series 1 on page` and will complain if the new colour is too light. Put it back.

**2. Change a chart's data rule (3 minutes).**
Open `src/site.json`, change `bucket_width_minutes` from 5 to 10, rebuild. The histogram collapses
from 5-minute to 10-minute buckets and the caption changes with it. This is the cleanest possible
answer to "show me that the charts come from your data".

**3. Add a sentence that quotes the data (5 minutes).**
In `src/content.en.json`, add to the `home` group:
`"extra_note": "The slowest wait recorded was {{stat:wait.max}} minutes."`
Then render it in `tools/build.py` inside `home()`:
`parts.append(f'<p>{self.t(lang, "home.extra_note")}</p>')`
and the same key in `src/content.bn.json` (both languages are required — the checker fails if one
is missing). Rebuild. If you had typed `25` instead of the token, `py tools/check.py` would refuse
the build; show that happening, it is the best demonstration in the whole repository.

**4. Break it and fix it (10 minutes).**
In `tools/charts.py`, inside `histogram`, change the median line to
`x = left + (median / peak) * plot_w` (using the *count* scale instead of the *value* scale). The
dashed line now sits in the wrong place — usually far to the right. Explain why: the horizontal axis
is minutes, the vertical is counts, and the line must use the same scale as the bars. Revert it.

## The examiner's four questions

**"Why did you choose this problem?"**
*In your own words* — the honest answer is about something you personally stood in and found
absurd, and it should name the place. Two or three sentences.

**"Where exactly was this photo taken?"**
Answer with the place from `data/places.csv` and the date from `data/photos.csv`, then open the
photo and point at the landmark in it. The captions and alt texts are in the manifest so the answer
is checkable.

**"What did this survey question miss?"**
Pick one and be specific: the survey never asked how many people *left* the queue before being
served (only whether anyone did), it never asked people to compare this queue with another, and it
did not record whether the counter was short-staffed or simply slow. The `walked_away` column is the
one to point at: it is a yes/no, so it can support "people gave up" but not "one in five gave up".

**"Name one conclusion your data does not support."**
Have two ready:

1. *That this counter is slower than the counter next door.* The two places have different numbers
   of observations and different hours, and the median comparison is only indicative where a place
   has fewer than three timed waits — the site says so on the chart.
2. *That the queue is caused by under-staffing.* The data shows how long people waited, never why.
   The limitation is generated on the limitations page in the sentence about the bottleneck.

## If you get stuck

* **"How do I know this number is right?"** Open the chart on `data.html`, expand *Show the raw rows
  behind this chart*, and read the row ids. Then open `data/observations.csv` and find those ids.
* **"Is this number typed in anywhere?"** Run `py tools/check.py`. If a digit exists outside a
  token, it fails and names the key.
* **"Is this page up to date?"** The footer prints the data snapshot hash and the build date, and
  `py tools/check.py` fails when a page's stamped hash differs from the current CSV.
* **"What happens if the CSV is missing a value?"** The row still counts towards coverage, the blank
  is counted on the limitations page, and the median uses only the rows that have a wait — so the
  page can never average a blank as zero.
