# Method note

**To complete before submitting** (five lines, then one paragraph each in the sections marked *in
my own words*):

- Author: <!-- your name, course, institution -->
- Places studied: <!-- the names that also sit in data/places.csv -->
- Dates of collection: <!-- first and last day you stood there -->
- Roughly how many hours I spent collecting: <!-- e.g. about six hours across three days -->
- Instrument: <!-- e.g. a phone stopwatch, plus a notebook -->

Everything else in this note is already true of the site: the collection rules below are the rules
the files and the build actually follow.

---

## 1. What counts as one observation

One row in `data/observations.csv` is one waiting episode that I personally stood in or watched
from the moment a person joined the queue until the moment they were served. Rows were logged
while standing there, not reconstructed from memory afterwards. The row records the place, the
date, the clock time I started watching, the queue length, how many people were ahead, how long
the person waited, how that time was obtained, and one line of what I saw.

A row is kept even when a field is blank, and `data/observations.csv` says at the top what each
column means. Blanks are never filled in later with an estimate: the limitations page counts every
blank cell by column and shows the count on the site, which is the honest way round.

## 2. How the waiting time was obtained

Every row states how its time was measured, in the `timing_method` column:

- `stopwatch` — I started a timer when the person joined the queue and stopped it when they were
  served;
- `estimate` — I counted from memory or from the clock face, which is less accurate and is
  reported as such;
- `self_report` — the person told me how long they had been waiting.

The data page prints how many rows fall into each of those three groups, as a percentage of the
collection. A median computed mostly from estimates is a weaker median, and the site says so
instead of averaging the difference away.

## 3. Sampling, and what I did not do

The times were **not** chosen at random. I stood at these places when I was free and when I
expected a queue, so quiet hours and quiet days are certainly under-represented. Nothing here is a
random sample of all waiting times, and the limitations page states this in the same words every
time the site is rebuilt.

I collected on the days listed above, at the places listed above, and nowhere else. The rows
therefore describe these places at those hours and nothing more.

## 4. Photos

Photos in `data/photos/` were taken by me on <!-- device -->. Faces and number plates are blurred
before a photo is added to the repository, no photo is published without `consent_ok: yes` in
`data/photos.csv`, and each photo is resized to at most 1200 px on its longest edge and kept under
250 kB so that a page stays well inside the 1 MB limit. Every photo has a caption and alt text
written by hand — the build refuses to complete without them.

One photo can also be used as the picture at the top of the home page. That is switched on by
naming the file in `hero_photo_file` in `src/site.json`; until then the home page shows a drawn
illustration instead, which is unmistakably a drawing and carries no numbers, so it cannot be
mistaken for evidence. Only a photo that already has a caption, alt text and `consent_ok: yes` in
`data/photos.csv` can take that place, and naming a file that is not in the CSV is ignored and
reported by `py tools/check.py`.

## 5. The interview

One interview is recorded in `data/interview.md`. The person is described by a role, not a name.
I explained what the answers would be used for before asking anything, and `consent_ok: yes` in
that file is what allows the answers to appear on the site at all: with consent unconfirmed the
build publishes a short note saying an interview exists but is not shown.

*In my own words* — who I asked, why that person, and anything they said that changed how I
understood the queue:

<!-- three or four sentences, in your own writing -->

## 6. What went wrong

*In my own words* — this is the section an examiner reads first. Name the specific problems: a
counter that closed while you were timing, a day when you were refused permission, a photo that
had to be thrown away, a queue that was too fast to time properly, an estimate you later wished you
had timed.

<!-- three or four sentences -->

## 7. How the site is generated from the data

```
data/observations.csv ─┐
data/places.csv        ├─► py tools/build.py ─► stats.json ─► charts, sentences, tables, summary
data/photos.csv        │                       └─► every page carries a hash of these files
data/interview.md    ──┘
```

No figure is typed into a page. Each one is a `{{stat:…}}` token resolved from `data/stats.json`,
which also records the row ids behind it; the charts print those ids underneath, so any number on
the site can be checked against the CSV by hand. If the CSV changes and the site is not rebuilt,
`py tools/check.py` fails and names the page that is out of date.

## 8. Ethics and privacy

Nobody identifiable appears in a photo without having agreed. The interview is anonymised, no phone
numbers or addresses are stored in this repository, and the only personal detail that appears on
the site at all is my own name as the collector. Nothing typed into the report form is stored by
the site: the form hands the text to the visitor's own email program, and the site has no server.

## 9. What I would change next time

*In my own words* — one paragraph. The honest answer is usually about the sampling: more days, and
the same hours repeated across days so the comparison holds the day of the week still.

<!-- three or four sentences -->
