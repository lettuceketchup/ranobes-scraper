# Ranobes Scraper

This Python script scrapes novels from [Ranobes](https://ranobes.net/) and saves them into .epub format.

### Features

- Regular updates
- No 'In preparation, Keguan...' for chapters
- 10,000+ novels to scrape
- Terminal based and simple to use
- Scraping progress can be monitored
- Optionally includes each chapter's reader comments (nested replies, quotes) in the epub
- Automatically hands off to a real browser window if the site's anti-flood/CAPTCHA protection kicks in, then resumes on its own once it's solved
- Remembers the browser's cookies between runs, so a solved CAPTCHA isn't asked for again straight away
- Works on an Android phone (Termux) too, with a virtual display you view in a VNC app
- Caches fetched pages on disk so re-running over the same chapters doesn't refetch them
- Configurable retries, delays, and timeouts; clear terminal logging for common failures (no internet, site down, timeouts)

### Getting Started

Install the latest version of [Python](https://www.python.org/). It may work with older versions but has not been tested.

### Prerequisites

This script depends on bs4, ebooklib, progress, and playwright. To install these navigate to the project folder and run

```
pip install -r requirements.txt
python -m playwright install chromium
```

The second command is a one-time download of the Chromium browser the script drives — the site can't be scraped with plain HTTP requests, since it fronts every page with a bot check that needs a real browser to clear.

You also need a graphical desktop (a screen the script can open a browser window on), because the site may ask you to solve a CAPTCHA by hand — see [Anti-flood / CAPTCHA handling](#anti-flood--captcha-handling). The final "Save As" dialog needs one too. No desktop (e.g. Termux on Android)? See [Solving CAPTCHAs on Android (Termux)](#solving-captchas-on-android-termux).

### Usage

Navigate to the project folder and run

```
python main.py
```
to start the script. It's fully interactive by default — it'll prompt you for the novel URL, then a starting/ending chapter number, then whether to include comments.

Now copy and paste the URL of the novel you wish to scrape from [Ranobes](https://ranobes.net/).

<img src = "images/Demo/novel_webpage.PNG" alt = "novel_webpage">


It will start extracting the chapter list.

<img src = "images/Demo/extract_index.PNG" alt = "extract_index">


After that, select the chapter range and it will start scraping the chapters.

<img src = "images/Demo/chapter_range.PNG" alt = "chapter_range">


Once done, a save dialog opens pre-filled with a sensible filename (novel title + chapter range) in the project folder — pick a different location if you'd like, or just hit Save.

<img src = "images/Demo/save_file.PNG" alt = "save_file">


Enjoy your read!

### Command-line options

Every prompt above can also be supplied as a flag, which skips that particular prompt — handy for scripting or resuming a specific range without retyping the URL:

```
python main.py --url <novel-url> --start 1 --end 20
python main.py --url <novel-url> --start 1 --end 20 --comments
python main.py --help
```

Run `python main.py --help` for the full list, including:

- `--comments` / `--no-comments` — include reader comments per chapter (off by default)
- `--retries`, `--retry-delay`, `--request-delay`, `--timeout`, `--wait` — tune how patiently the script retries a failing page and how much it paces itself between requests
- `--cache-dir`, `--no-cache` — where fetched pages are cached, or disable caching for a fully fresh run
- `--output-dir` — where the save dialog opens by default
- `--session-file`, `--fresh-session` — where cookies are kept between runs, or start one run without them
- `--captcha-timeout`, `--no-notify` — give up on an unsolved CAPTCHA after N minutes; turn off the phone notification
- `--log-level` — terminal verbosity

### Anti-flood / CAPTCHA handling

Ranobes' anti-bot protection can escalate to a real interactive CAPTCHA that no script can solve on its own. This usually happens under sustained request volume, but it can also happen on the very first page: in a November 2026 test from an Android phone (Termux), the site served its own image CAPTCHA ("click on the similar image") right away, and waiting didn't clear it. When that happens, the script automatically opens a visible browser window (the same session, so your cookies carry over) for you to solve it. It rings the terminal bell (and on Termux with Termux:API, sends a phone notification), then checks the page every few seconds and carries on by itself as soon as the check is cleared — multi-step challenges are fine, it keeps waiting until the last one is done. Press Enter to make it check right away, or type `abort` + Enter to give up.

It waits indefinitely by default; `--captcha-timeout MINUTES` makes it give up instead. If the CAPTCHA page fails to load (network trouble), use the window's reload button once the connection is back. Closing the window ends the run cleanly. Whichever way it stops, you're offered an epub of the chapters fetched so far.

Cookies are saved to `.browser_state.json` (after a CAPTCHA is solved and at the end of every run) and loaded at the next start, so you usually only solve a CAPTCHA once in a while. The file holds login-like cookies — keep it private. The site's clearance may be tied to your IP address, so switching networks can bring the CAPTCHA back.

If no window can be opened at all (for example over SSH, in a container, or in Termux without a display), the script stops with a message saying so instead of crashing.

### Solving CAPTCHAs on Android (Termux)

Termux has no screen of its own, so `display.sh` runs an invisible X screen with a built-in VNC server (TigerVNC's `Xvnc`), which you view in a VNC app on the same phone.

One-time setup:

1. Inside the Termux/proot Linux: `apt install tigervnc-standalone-server tmux openbox`
2. Install the [AVNC](https://play.google.com/store/apps/details?id=com.gaurav.avnc) app, add a server with address `127.0.0.1` and port `5901`, and set its gesture style to **Touchscreen**. Then, so dragging a puzzle piece actually drags it, go to AVNC's Settings → Input → Gestures → **One-finger swipe** and choose **Drag remote content** (by default a swipe only moves AVNC's own view; double-tap-and-swipe also drags).
3. Optional, for notifications: the Termux:API app and the `termux-api` package in Termux.

Each time:

```
./display.sh start     # once per Termux session; also: stop, status
python main.py ...     # finds the display by itself
```

When a CAPTCHA appears, open AVNC, solve it, and leave — the run continues on its own. Enable Termux's wake lock (from its notification) so Android doesn't kill it while you're in another app.

If a page keeps failing after several retries for another reason (bad connection, site hiccup, etc.), the script stops and asks whether to retry, skip that item, or abort — it never silently gives up on a chapter. If you abort or interrupt the run (Ctrl+C) partway through, it'll offer to save an epub with whatever chapters were already fetched, rather than losing that work.


### Lithium: EPUB Reader

Personally, I prefer the [Lithium: EPUB Reader](https://play.google.com/store/apps/details?id=com.faultexception.reader) due to its simplicity and ease of use to read .epub files.

<table>
    <tr>
        <td><img src = "images/Lithium/lithium_1.png" height = 400 width = 180 alt = "lithium_1"></td>
        <td><img src = "images/Lithium/lithium_2.png" height = 400 width = 180 alt = "lithium_2"></td>
        <td><img src = "images/Lithium/lithium_3.png" height = 400 width = 180 alt = "lithium_3"></td>
        <td><img src = "images/Lithium/lithium_4.png" height = 400 width = 180 alt = "lithium_4"></td>
    </tr>
</table>

### Finally

Feel free to open an issue if you face any bugs or have any suggestions.
