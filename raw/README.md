# What goes in `raw/`

Your untouched evidence. Two folders are ignored by git on purpose, so that nothing here is
published by accident:

```
raw/
  originals/          the full-resolution photos exactly as they came off the phone or camera
  interview-notes/    the audio recording, the written note, the permission note
```

**Why they are not committed.** The repository is served as the public website, so anything
committed here is on the open internet. Full-resolution photos of a street or a queue can carry
recognisable faces, number plates, and the exact location metadata in the file. Keep the originals
in this folder locally, hand them in through your own submission folder, and commit only the
web-sized copies that the site actually uses.

## The rule for anything that leaves this folder

| Before it goes into `data/photos/` | Why |
| --- | --- |
| Blur every readable face and number plate | Consent is not implied by standing in a queue |
| Strip the location metadata (`exiftool -all= photo.jpg`) | The site already states the place in the caption; the file does not need to carry it |
| Resize to at most 1200 px on the longest edge, under 250 kB | The assignment caps a page at 1 MB, and eight photos add up fast |
| Write the caption and the alt text yourself | The build fails if either is missing or says something useless like "image of queue" |

## The interview note

`data/interview.md` is the copy that gets published, and it must be anonymised before it goes
there: use a role label ("Counter staff", "Student in the 10am queue") rather than a name. The
recording and any notes with a real name, a phone number or an address stay in
`raw/interview-notes/`, which is ignored by git.

If somebody asks you to remove their answers, delete them from `data/interview.md`, rebuild with
`py tools/build.py`, and write in `docs/method-note.md` that the answers were withdrawn. That
sentence is worth more in the viva than the answers would have been.
