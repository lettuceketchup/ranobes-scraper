# Open question: what metadata survives Send to Kindle?

**Status: not investigated.** Written 2026-11-21 so a later session can pick it up. Nothing here has been
tested on a Kindle or through Amazon's Send to Kindle; the "what Amazon does" parts are forum reports.

## Why it matters

The user reads these epubs on a Kindle and sends them with Send to Kindle (not USB, not Calibre). Whatever
Amazon drops from the epub's metadata is invisible in the library, so the book has to carry the useful
information somewhere Amazon keeps.

## What our epub carries (read from `EPUB/content.opf`, built 2026-11-21)

| Field | Value (this novel) | Where it comes from |
|---|---|---|
| `dc:title` | the novel title (plus `, <volume label>` with `--volume-label`) | novel page |
| `dc:creator` (role `aut`) | Sinnoa | `.r-fullstory-spec` |
| `dc:contributor` (role `trl`) | WeTried Translations, Reaper Scans | `.r-fullstory-spec` |
| `dc:publisher` | J Plus Media | `.r-fullstory-spec` |
| `dc:subject` x14 | genres, Adventure ... Supernatural | `#mc-fs-genre` |
| `dc:date` | `2024` (year only; Calibre displays 2024-11-15, which is Calibre filling it in) | `.r-fullstory-spec` |
| `dc:description` | the site's synopsis | `.moreless__full` |
| `dc:language` | `en` (hard-coded) | |
| `dc:identifier` | `ranobes-<novel id>` | URL |
| `dc:source` | the ranobes novel URL | `--url` |
| cover | `cover.jpg` (re-encoded to JPEG), `properties="cover-image"` + a `cover.xhtml` page | `og:image` |
| series | only with `--volume-label`: EPUB3 `belongs-to-collection` + `calibre:series`/`calibre:series_index` | |

Not captured at all: the site's "Completed" status, chapter count, the "Events" tags (Weak to Strong, ...),
rating. The in-book intro page (`intro.xhtml`) repeats author, translators, publisher, year, genres and the
synopsis as plain text, so that information survives in the *content* whatever happens to the metadata.

## What is known (all second-hand)

- A MobileRead user lists the KFX-supported fields as title, author, language, publisher, publication date,
  description, cover and ASIN. Series is not on that list. Calibre's changelog says only the first author is
  shown on Kindle for KFX.
- Amazon has converted most Send to Kindle personal documents to KFX since about October 2023 (forum report).
- Titles: a 2022 Five Filters post says Amazon sometimes takes the EPUB title from the filename instead of the
  metadata. Our filename is `<novel title> - Chapters A-B.epub`, so either source reads sensibly.
- Series: users report it often does not arrive via Send to Kindle, and one suggests the device can't read
  series from EPUB3; the usual workaround is putting series name/number in the title.
- Nothing found on publisher, tags/subjects, contributors or `dc:source` for Send to Kindle specifically.

Sources: <https://fivefilters.org/?p=4199>, MobileRead threads
<https://www.mobileread.com/forums/showthread.php?p=4557228>,
<https://www.mobileread.com/forums/showthread.php?p=4220568>,
<https://www.mobileread.com/forums/showthread.php?p=4227426>,
<https://www.techwalla.com/13779370/how-to-convert-epub-to-kindle-format-send-to-kindle-vs-calibre>.

## Dead end already tried

Searching the Kindle Previewer 3 output (`-convert` gives a `.kpf`) for the author/publisher/tag strings found
nothing: `resources/book.kdf` is a SQLite database that won't open cleanly (it has a journal) and the `.kpf`
bundles the original `book.epub`, so it can't show what Amazon's converter kept. Don't repeat that.

## Suggested investigation

1. Build a small sample (e.g. `--start 1 --end 5`) and send it through Send to Kindle. Record what the library
   shows (title, author, cover, language) and what "About this book" shows (publisher, date, description).
2. Repeat with variations, one at a time: a full `dc:date` (`2024-11-15`) instead of the year; `--volume-label
   "Vol. 1"` to see whether the series appears; the same file renamed, to confirm title-from-filename vs metadata.
3. Fill a results table here (field, kept / dropped / where it shows) and, if something useful is dropped, move it
   into the title, the author field, or the intro page.
4. Only if Send to Kindle proves too lossy: build KFX/AZW3 with Calibre and sideload, but that is a different
   workflow from the one the user uses.
