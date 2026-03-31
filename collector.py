"""
Periodic data-collection loop.

Usage:
    python -m monitor.main collect
"""
import logging
import time
import signal
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

try:
    from monitor.config import PORTAL_URL, SESSION_FILE, POLL_INTERVAL_SECONDS
    from monitor.auth import is_session_valid
    from monitor.scraper import scrape_stats
    from monitor.storage import get_conn, insert_sample
except ModuleNotFoundError:
    from config import PORTAL_URL, SESSION_FILE, POLL_INTERVAL_SECONDS
    from auth import is_session_valid
    from scraper import scrape_stats
    from storage import get_conn, insert_sample

log = logging.getLogger(__name__)

_running = True


def _handle_sigint(sig, frame):
    global _running
    print("\n[!] Stop requested — shutting down cleanly.")
    _running = False


def run_collector(db_path: str, debug: bool = False) -> None:
    if not Path(SESSION_FILE).exists():
        print(
            f"[Error] Session file not found ({SESSION_FILE}).\n"
            "Run first:  python3 main.py login"
        )
        sys.exit(1)

    signal.signal(signal.SIGINT, _handle_sigint)
    conn = get_conn(db_path)

    print(f"[✓] Starting monitor — sampling every {POLL_INTERVAL_SECONDS}s ({POLL_INTERVAL_SECONDS // 60} min).")
    print("    Press Ctrl+C to stop.\n")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(storage_state=SESSION_FILE)
        page = context.new_page()

        # Initial load
        _load_portal(page)

        while _running:
            try:
                page.reload(wait_until="networkidle", timeout=30_000)
            except PWTimeout:
                log.warning("Reload timed out, retrying once…")
                try:
                    _load_portal(page)
                except Exception as exc:
                    log.error("Could not reload portal: %s", exc)
                    _sleep_interruptible(30)
                    continue

            # Check we weren't redirected to login
            if not is_session_valid(page):
                print("[!] Session expired. Run 'login' again then restart collect.")
                break

            if debug:
                try:
                    raw = page.inner_text("body")
                    with open("scrape_debug.txt", "w", encoding="utf-8") as f:
                        f.write(raw)
                    print("[debug] Raw page text written to scrape_debug.txt")
                except Exception as exc:
                    log.warning("Could not write debug file: %s", exc)

            data = scrape_stats(page)
            if data:
                insert_sample(conn, data)
                _print_sample(data)
            else:
                log.warning("Failed to extract stats from page.")

            _sleep_interruptible(POLL_INTERVAL_SECONDS)

        browser.close()

    print("[✓] Monitor stopped.")


def _load_portal(page) -> None:
    page.goto(PORTAL_URL, wait_until="networkidle", timeout=60_000)


def _sleep_interruptible(seconds: int) -> None:
    """Sleep in 1-second chunks so Ctrl+C is responsive."""
    for _ in range(seconds):
        if not _running:
            break
        time.sleep(1)


def _print_sample(data: dict) -> None:
    import datetime
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    calls     = _fmt(data.get("calls"))
    waiting   = _fmt(data.get("waiting"))
    connected = _fmt(data.get("connected"))
    on_break  = _fmt(data.get("on_break"))
    print(
        f"[{ts}]  Calls: {calls}  |  Waiting: {waiting}  |  "
        f"Connected: {connected}  |  On break: {on_break}"
    )


def _fmt(v) -> str:
    return str(v) if v is not None else "?"
