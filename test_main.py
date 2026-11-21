"""Self-check for main.py's chapter cleaning, footnotes, comment cap and epub output.

Run:  python test_main.py
Plain asserts, no test framework. The cache sweep and epub build use the pages
in .page_cache/ and are skipped if it is empty. Set TEST_OUT_DIR to keep the
generated epub (and its Calibre conversion) instead of using a temp folder.
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

from bs4 import BeautifulSoup
from ebooklib import epub
from lxml import etree

import main
from main import CommentNode

TITLE = "I\u2019m an Infinite Regressor, But I\u2019ve Got Stories to Tell"
NS = 'xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"'
HERE = os.path.dirname(os.path.abspath(__file__))


def page(box_html, heading="Chapter 299<br/>" + TITLE):
    return BeautifulSoup(
        f'<h1 class="h4 title">{heading}</h1><div id="arrticle">{box_html}</div>', "html.parser")


def build(box_html, **kw):
    return main.build_chapter_content(page(box_html, **kw), TITLE, "Chapter ?")


def assert_xhtml(fragment):
    etree.fromstring(f"<div {NS}>{fragment}</div>")


def check_cleaning():
    ch = build(
        "<p>Discord: https://dsc.gg/reapercomics</p>"
        f"<p><strong>\u25c8 {TITLE}</strong></p>"
        "<p>\u2500\u2500\u2500\u2500\u2500\u2500</p>"
        "<p>Translator: ZERO_SUGAR</p><p>Editor: echo</p><p>WeTried Translations</p>"
        "<p>Chapter 299</p><p></p><p>&nbsp;</p>"
        "<p>The <em>quiet</em> room &amp; <strong>more</strong><br/>line two.</p>"
        "<p>* * *</p><hr/><p>\u201c...\u201d</p>"
        "<p>Mentioned the discord in passing [1].</p>"
        "<p>Footnotes:</p><p>[1] Some note.</p>"
        "<p>Join our discord at</p><p>https://dsc.gg/reapercomics</p>")
    html = ch.html
    assert ch.label == "Chapter 299", ch.label
    assert "dsc.gg" not in html and "\u25c8" not in html and "Join our discord" not in html
    for kept in ("Translator: ZERO_SUGAR", "Editor: echo", "WeTried Translations",
                 "<em>quiet</em>", "<strong>more</strong>", "&amp;", "<br/>",
                 "Mentioned the discord in passing", "\u201c...\u201d"):
        assert kept in html, f"lost: {kept}"
    assert html.count("Chapter 299") == 1, "the site's own 'Chapter N' echo should go"
    assert html.count('class="scene"') == 1, "scene breaks should collapse to one"
    assert '<p></p>' not in html
    assert 'epub:type="noteref" href="#fn1" id="fnref1">[1]</a>' in html
    assert '<aside epub:type="footnote" id="fn1"><p><a href="#fnref1">[1]</a> Some note.</p></aside>' in html
    assert ch.removed == 5, ch.removed  # discord, banner, echo, "join", url
    assert_xhtml(html)

    # Header shaped like chapter 383: credits, echo, divider, part title.
    ch = build("<p>WeTried Translations</p><p>Translator: ZERO_SUGAR</p><p>Chapter 383</p>"
               "<p>\u2500\u2500\u2500\u2500\u2500\u2500</p><p>The Suicidal I</p><p>Text.</p>",
               heading="Chapter 383")
    assert ch.html.count("Chapter 383") == 1
    assert ch.html.count('class="scene"') == 1 and "The Suicidal I" in ch.html

    # Non-chapter pages keep only the part before the "|".
    ch = build("<p>Hello.</p>", heading="Announcement | " + TITLE)
    assert ch.label == "Announcement" and "<h2>Announcement</h2>" in ch.html

    # A real translator's note that mentions the discord must survive (ch 485).
    note = ("I've never seen a community be as involved theory-making, props to "
            "everyone in \u2060the discord for that.")
    assert note in build(f"<p>{note}</p>").html

    # An unmatched [2] is left alone; no footnotes -> no footnote block.
    ch = build("<p>A system message [2] appears.</p>")
    assert "[2]" in ch.html and "noteref" not in ch.html and "footnotes" not in ch.html

    # The site's template leaves an empty "Footnotes:" heading, or a stub
    # "[1]" with no text, on chapters that have no footnotes: both are dropped.
    ch = build("<p>The end.</p><p></p><hr/><p>Footnotes:</p><p>Join our discord at </p><p>\n</p>")
    assert "Footnotes" not in ch.html and "footnotes" not in ch.html and 'scene' not in ch.html
    ch = build("<p>The end.</p><p>Footnotes:</p><p>[1]</p>")
    assert "footnote" not in ch.html.lower() and "[1]" not in ch.html and "The end." in ch.html
    ch = build("<p>A [1] and [2].</p><p>Footnotes:</p><p>[1]</p><p>[2] Real note.</p>")
    assert ch.html.count("<aside") == 1 and "Real note." in ch.html

    # The closing line that merely contains the title is not the banner.
    end = f"<p>-{TITLE}. END.</p>"
    assert "END." in build(end).html
    print("ok  cleaning, formatting, footnotes, scene breaks")


def comment(n, up=0, down=0, replies=()):
    return CommentNode(author=f"u{n}", timestamp="", reply_to="", upvotes=str(up),
                       downvotes=str(down), body_html=f"c{n}", replies=list(replies))


def check_comment_cap():
    threads = [comment(i, up=i, replies=[comment(1000 + i)]) for i in range(100)]
    kept, hidden = main.limit_comments(threads, 20)
    count = sum(main._comment_count(c) for c in kept)
    assert count == 20 and hidden == 200 - 20, (count, hidden)
    ids = [int(c.author[1:]) for c in kept]
    assert ids == sorted(ids), "original order must be kept"
    assert 99 in ids and 0 not in ids, "best-voted threads win"
    assert main.limit_comments(threads, 0) == (threads, 0), "0 means no cap"
    small = threads[:5]
    assert main.limit_comments(small, 20) == (small, 0)

    big = comment(1, up=50, replies=[comment(100 + i) for i in range(50)])
    kept, hidden = main.limit_comments([big, comment(2)], 20)
    assert sum(main._comment_count(c) for c in kept) == 20 and hidden == 52 - 20
    assert kept[0].author == "u1" and len(kept[0].replies) == 19

    html = main.build_comments_section(kept, hidden)
    assert "32 more comments not shown." in html
    assert_xhtml(html)
    print("ok  comment cap")


def check_interrupt():
    # First Ctrl+C = stop at the next safe point; second = quit immediately.
    # (The signal itself can't be injected portably, so call the handler.)
    import time
    main._stop_requested = False
    main.check_stop()  # no flag: no-op
    main.stoppable_sleep(0.05)
    real_exit, calls = os._exit, []
    os._exit = calls.append
    try:
        main._on_sigint(2, None)
        assert main._stop_requested and calls == [], "first press only sets the flag"
        for stop in (main.check_stop, lambda: main.stoppable_sleep(5)):
            started = time.monotonic()
            try:
                stop()
            except KeyboardInterrupt:
                assert time.monotonic() - started < 1
            else:
                raise AssertionError("a pending stop must raise at the next check")
        main._on_sigint(2, None)
        assert calls == [130], "second press quits immediately"
    finally:
        os._exit = real_exit
        main._stop_requested = False
    print("ok  Ctrl+C: stop at a safe point, second press quits")


def check_direct_save():
    # No dialog by default: the epub goes straight into --output-dir, and a
    # second build of the same range gets " (2)" instead of overwriting.
    out = tempfile.mkdtemp(prefix="ranobes-save-")

    def make():
        book = epub.EpubBook()
        book.set_identifier("ranobes-save-test")
        book.set_title("Save Test")
        book.set_language("en")
        item = epub.EpubHtml(title="Chapter 1", file_name="ch1.xhtml")
        item.content = ('<h2>Chapter 1</h2><p>Hello <a epub:type="noteref" href="#fn1" id="fnref1">[1]</a>.</p>'
                        '<aside epub:type="footnote" id="fn1"><p>[1] A note.</p></aside>')
        book.add_item(item)
        return book, [item]

    for _ in range(2):
        book, items = make()
        main.finalize_and_save(book, items, out)
    assert sorted(os.listdir(out)) == ["Save Test - Chapter 1 (2).epub",
                                       "Save Test - Chapter 1.epub"], os.listdir(out)
    # Footnote ids must not become a hidden page-list of fake page numbers.
    with zipfile.ZipFile(os.path.join(out, "Save Test - Chapter 1.epub")) as z:
        assert b"page-list" not in z.read("EPUB/nav.xhtml")
    print("ok  direct save without a dialog, no overwrite, no fake page-list")


def cached_chapters():
    paths = sorted(glob.glob(os.path.join(HERE, ".page_cache", "*.html")))
    for path in paths:
        with open(path, encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
        if soup.find("h1", class_="h4 title") is not None:
            yield soup


def check_cache_sweep():
    chapters = list(cached_chapters())
    if not chapters:
        print("skip cache sweep (no cached chapters)")
        return None
    raw_words = kept_words = removed = with_notes = linked = 0
    for soup in chapters:
        container = soup.find("div", id="dle-comments-list")
        if container is not None:
            container.decompose()
        box = soup.find(id="arrticle")
        raw_words += sum(len(p.get_text(" ", strip=True).split()) for p in box.find_all("p"))
        ch = main.build_chapter_content(soup, TITLE, "Chapter ?")
        assert ch.label and "|" not in ch.label, ch.label
        assert "dsc.gg" not in ch.html, ch.label
        assert "\u25c8" not in ch.html, ch.label
        assert_xhtml(ch.html)
        kept_words += ch.words
        removed += ch.removed
        if 'class="footnotes"' in ch.html:
            with_notes += 1
            linked += ch.html.count('epub:type="noteref"')
    ratio = kept_words / raw_words
    assert ratio > 0.9, f"suspiciously much text dropped: {ratio:.3f}"
    print(f"ok  cache sweep: {len(chapters)} chapters, {kept_words:,}/{raw_words:,} words "
          f"kept ({ratio:.1%}), {removed} lines removed, {with_notes} with footnotes "
          f"({linked} note links)")
    return chapters


def find_calibre(name):
    for candidate in (shutil.which(name), rf"C:\Program Files\Calibre2\{name}.exe"):
        if candidate and os.path.exists(candidate):
            return candidate
    return None


def check_epub_build(out_dir):
    pages = list(cached_chapters())
    if not pages:
        print("skip epub build (no cached chapters)")
        return
    with_notes = [p for p in pages
                  if any(t.get_text(strip=True) == "Footnotes:" for t in p.find_all("p"))]
    chosen = pages[:8] + [p for p in with_notes if p not in pages[:8]][:4]

    book = epub.EpubBook()
    book.set_identifier("ranobes-test")
    book.set_title(TITLE)
    book.set_language("en")
    book.add_author("Sinnoa")
    css = epub.EpubItem(uid="style_book", file_name=main.BOOK_CSS_PATH,
                        media_type="text/css", content=main.BOOK_CSS)
    book.add_item(css)

    intro = epub.EpubHtml(title="Introduction", file_name="intro.xhtml", lang="en")
    intro.content = main.build_intro_html(main.NovelMetadata(
        title=TITLE, authors=["Sinnoa"], translators=["ZERO_SUGAR"], publishers=[],
        genres=["Fantasy"], year="2024", description="A test synopsis.",
        description_paragraphs=["A test synopsis."], cover_url=""))
    intro.add_item(css)
    book.add_item(intro)

    items, shown_comments = [], 0
    for n, soup in enumerate(chosen, start=1):
        comments, hidden = main.limit_comments(main.extract_comments(soup), 3)
        shown_comments += sum(main._comment_count(c) for c in comments)
        container = soup.find("div", id="dle-comments-list")
        if container is not None:
            container.decompose()
        ch = main.build_chapter_content(soup, TITLE, f"Chapter {n}")
        item = epub.EpubHtml(title=ch.label, file_name=f"ch{n}.xhtml")
        item.content = ch.html + main.build_comments_section(comments, hidden)
        item.add_item(css)
        book.add_item(item)
        items.append(item)
    book.toc = (epub.Link("intro.xhtml", "Introduction", "intro"),
                (epub.Section("Chapters"), tuple(items)))
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = [intro] + items

    path = os.path.join(out_dir, "test-book.epub")
    epub.write_epub(path, book, {"epub3_pages": False})

    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        assert "EPUB/style/book.css" in names, names
        for item in items:
            data = z.read(f"EPUB/{item.file_name}")
            root = etree.fromstring(data)  # must be well-formed XML
            assert b"style/book.css" in data, item.file_name
            assert b"fonts.googleapis" not in data and b"font-family" not in data
            assert root.nsmap.get("epub") == "http://www.idpf.org/2007/ops", root.nsmap
    print(f"ok  epub written: {path} ({len(chosen)} chapters, {shown_comments} comments shown)")

    meta, convert = find_calibre("ebook-meta"), find_calibre("ebook-convert")
    if meta:
        out = subprocess.run([meta, path], capture_output=True, text=True, encoding="utf-8")
        assert "Sinnoa" in out.stdout, out.stdout + out.stderr
        print("ok  calibre reads the metadata")
    if convert:
        target = os.path.join(out_dir, "test-book.azw3")
        out = subprocess.run([convert, path, target], capture_output=True, text=True,
                             encoding="utf-8", errors="replace")
        assert out.returncode == 0 and os.path.getsize(target) > 0, out.stdout[-800:] + out.stderr[-800:]
        print(f"ok  calibre converted it to AZW3: {target}")
    else:
        print("skip calibre conversion (ebook-convert not found)")


if __name__ == "__main__":
    out_dir = os.environ.get("TEST_OUT_DIR") or tempfile.mkdtemp(prefix="ranobes-test-")
    os.makedirs(out_dir, exist_ok=True)
    check_cleaning()
    check_comment_cap()
    check_direct_save()
    check_interrupt()
    check_cache_sweep()
    check_epub_build(out_dir)
    print("all checks passed")
