# Design notes

How the site looks, why it looks that way, and the two or three files that decide it.

The short version: the page is meant to read as a modern data story — one clear heading, one
picture, one band of big numbers, then the charts and the raw rows. The honesty rules did not move
to make room for it, and the decorations are kept strictly away from the evidence.

## Where the look lives

| What decides the look | File | Change it and… |
| --- | --- | --- |
| Colour, gradients, shadows, corner radii, type stacks | `src/theme.json` | every page, the charts and the drawings follow |
| The rules that use them | `src/site.css.tpl` | rebuild writes `assets/site.css` |
| The drawn pictures and icons | `tools/art.py` | the hero, the target ring, the pipeline diagram |
| The chart drawing | `tools/charts.py` | all three charts |
| Which component appears on which page | `tools/build.py` | the page markup |
| Every word | `src/content.en.json`, `src/content.bn.json` | both languages, one key at a time |

**Never edit the generated files** (`assets/site.css`, `*.html`, `bn/*.html`). Edit the source and
run `py tools/build.py`. The build stops if the stylesheet template still contains a `{{…}}` token,
which is what stops a renamed token in `theme.json` from silently becoming an undefined CSS
variable — that exact mistake is failure 2 in `docs/ai-use-log.md`.

## Colour, and the gate it has to pass

Every colour is a named token in `src/theme.json`; adding a key there creates a CSS variable
automatically, so a whole palette change is a handful of lines. Nothing else in the repository
writes a colour: the charts, the icons and the illustrations all carry classes, and the stylesheet
decides what those classes look like.

`tools/check.py` recomputes the contrast ratio of every pair listed in `contrast_pairs` and refuses
to publish below **4.5:1** for text and **3:1** for chart series, in both light and dark mode. That
is why an inaccessible palette cannot ship, and why the pair list is part of the theme rather than
a comment. A test also asserts that every accent and every series colour has a pair of its own, so
adding a sixth series colour without checking it now fails the suite.

The pair list never contains `header_bg`, which holds an `rgba()` value: the checker computes ratios
from plain hex pairs, and an rgba value there would crash it.

## The drawings

* Every picture is inline SVG written by `tools/art.py`. There are no image files to download, so
  a page stays a few tens of kilobytes, nothing can show a broken-image icon, and the site works
  with JavaScript switched off.
* The colour of a drawing comes from the stylesheet, not from the drawing: the SVG carries classes
  and the CSS carries the colours, so the same file is correct in light mode, dark mode and print.
* **The decorations are decoration.** The hero scene, the camera drawing, the brand mark and every
  icon are marked `aria-hidden="true"` and contain no text at all — no numbers and no labels. That
  is deliberate: a drawing of four people waiting and a clock must never be read out as a measured
  figure, and it must never be mistaken for a photograph of the real place. A test enforces it
  (`DesignTests.test_the_decorations_are_hidden_and_carry_no_figures`).
* Only two drawings carry words or figures: the **target ring** and the **pipeline diagram**. Both
  receive their content from the build, which takes it from `data/stats.json` or the content files.
  The ring's accessible name is the same sentence printed beside it, built from the same two
  numbers, so the picture cannot claim a different total from the text.

The pipeline diagram is the only picture on the site that explains something: `data/*.csv` is drawn
as the first step, the generated `data/stats.json` as the second, and these pages as the third. It
is the honesty rule as a picture.

## The hero picture

* **By default** the hero shows the drawn illustration: a queue at a counter, with the waiting time
  drawn as a track that fills up towards the front.
* **Your own photograph replaces it** when: the file is in `data/photos/`, it has a row in
  `data/photos.csv` with a caption, alt text, place, date and `consent_ok: yes`, and its file name
  is written into `hero_photo_file` in `src/site.json`. Rebuild and the illustration steps aside.
* **A name that matches nothing is ignored.** The build keeps the illustration and
  `py tools/check.py` reports the file name. That is the point: the only picture that can reach the
  front of the site is one you took, for which somebody consented, with a caption you wrote. No
  stock image and no generated image can arrive there by accident.

## The charts

Charts carry facts, so they are treated differently from the drawings: they are announced
(`role="img"` with a title and a description), their labels come from the content files in the
reader's language, and the rows behind every chart are printed underneath it in a table that stacks
into labelled rows on a phone.

The visual language is deliberately plain and repetitive: a dashed gridline, a gradient bar with
rounded corners, the value written as a small chip, the median as a dashed line with a chip of its
own, and a track behind each bar so an empty stretch is still readable. An empty chart is drawn as
an empty panel with a sentence saying why it is empty — never as a bar chart with invented bars.

## Phones, print and motion

* **360 px.** One column throughout, tables stack into labelled rows, and the page never scrolls
  sideways (checked as `scrollWidth == clientWidth` in the browser, at 360 px specifically). The
  header keeps two rows — the mark and the language switch, then a scrollable strip of tabs —
  because a wrapped six-item navigation plus a wordmark and a language button took a third of the
  screen. The wordmark stays in the document and is only moved out of sight, so a screen reader
  still announces the link.
* **Print.** The header, the footer and the decorations are dropped, the cards and figures are kept
  together across page breaks, and the one-page summary is laid out for A4.
* **Motion** is CSS only: a hover lift on cards, colour and border transitions, the target ring
  filling. Nothing on the page moves on its own, no content depends on animation, and
  `prefers-reduced-motion: reduce` turns all of it off.

## What I would change next

* The hero illustration is generic on purpose, because it must not imply anything about the real
  place. Once the places have coordinates, a second illustration could be drawn as a plan of the
  actual queue area, next to the bubbles on the places page.
* Real photographs will change the page weight more than anything else here; the per-page check is
  what keeps that visible, and it should stay switched on.
* The data tables are wide by nature. A print-only layout that flips them onto their side would
  read better than the current sideways-scrolling box on paper.
