# EranMonitor Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the scraper's "?" bug, translate all Hebrew UI strings to English, shorten the poll interval to 2 minutes, and add a `watch` subcommand for live reporting in a second terminal.

**Architecture:** All changes are isolated to the existing 6 source files — no new modules. The scraper fix updates regex patterns to match actual page labels. The `watch` command is a new subparser entry in `main.py` that loops over `generate_report()` from `reporter.py`. A minimal `tests/` directory is introduced for testable logic.

**Tech Stack:** Python 3, Playwright (browser automation), SQLite, argparse, optionally matplotlib

---

## File Map

| File | Changes |
|---|---|
| `config.py` | Default interval 300 → 120 |
| `scraper.py` | Fix `calls` pattern (`שיחות` → `בשיחה`); warn on all-None result |
| `auth.py` | Hebrew → English strings |
| `collector.py` | Hebrew → English; add `--debug` flag support; updated startup message |
| `reporter.py` | Hebrew → English throughout (day names, headers, chart labels) |
| `main.py` | Hebrew → English; add `watch` subcommand + `cmd_watch()` |
| `tests/test_scraper.py` | Unit tests for `_extract_int` with actual page label format |
| `tests/test_reporter.py` | Unit tests for `_gap` calculation |

---

## Task 1: Fix scraper `calls` pattern (TDD)

**Files:**
- Modify: `scraper.py`
- Create: `tests/test_scraper.py`

- [ ] **Step 1: Create tests directory and write the failing test**

Create `tests/__init__.py` (empty) and `tests/test_scraper.py`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scraper import _extract_int, _FIELD_PATTERNS


def test_calls_extracted_from_bishia_label():
    """Page uses 'בשיחה' not 'שיחות' — must match correctly."""
    text = "שלוחה: none | בשיחה: 4 | בהמתנה: 2 | פנויים/ות: 0 | בהפסקה: 5 | מחוברים/ות: 10"
    assert _extract_int(text, _FIELD_PATTERNS["calls"]) == 4


def test_waiting_extracted():
    text = "בהמתנה: 2"
    assert _extract_int(text, _FIELD_PATTERNS["waiting"]) == 2


def test_connected_extracted_with_gender_suffix():
    """Page label is 'מחוברים/ות' — the slash must not break the pattern."""
    text = "מחוברים/ות: 10"
    assert _extract_int(text, _FIELD_PATTERNS["connected"]) == 10


def test_on_break_extracted():
    text = "בהפסקה: 5"
    assert _extract_int(text, _FIELD_PATTERNS["on_break"]) == 5


def test_returns_none_when_no_match():
    assert _extract_int("no relevant text here", _FIELD_PATTERNS["calls"]) is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/avi/Projects/EranMonitor
python3 -m pytest tests/test_scraper.py -v
```

Expected: `test_calls_extracted_from_bishia_label` FAILS — current pattern looks for `שיחות` not `בשיחה`.

- [ ] **Step 3: Fix `_FIELD_PATTERNS` in `scraper.py`**

Replace the `_FIELD_PATTERNS` dict (lines 19–24):

```python
_FIELD_PATTERNS = {
    "calls":     [r"בשיחה[^\d]*(\d+)", r"(\d+)[^\d]*בשיחה"],
    "waiting":   [r"בהמתנה[^\d]*(\d+)", r"ממתינ[^\d]*(\d+)", r"(\d+)[^\d]*בהמתנה"],
    "connected": [r"מחוברים[^\d]*(\d+)", r"מחוברות[^\d]*(\d+)", r"(\d+)[^\d]*מחובר"],
    "on_break":  [r"בהפסקה[^\d]*(\d+)", r"הפסקה[^\d]*(\d+)", r"(\d+)[^\d]*בהפסקה"],
}
```

- [ ] **Step 4: Add all-None warning at the end of `scrape_stats()` in `scraper.py`**

Replace the last 3 lines of `scrape_stats()` (currently `log.info` line and `return data`):

```python
    if all(v is None for v in data.values()):
        print("[!] Warning: all stats are None — page text may not match expected patterns.")
        log.debug("Raw page text (first 500 chars): %s", raw_text[:500])

    log.info("Scraped: %s", data)
    return data
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_scraper.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add scraper.py tests/__init__.py tests/test_scraper.py
git commit -m "fix: correct 'calls' scraper pattern from שיחות to בשיחה; warn on all-None"
```

---

## Task 2: Update default poll interval

**Files:**
- Modify: `config.py`

- [ ] **Step 1: Change default in `config.py`**

Replace line 15:

```python
POLL_INTERVAL_SECONDS = int(os.environ.get("ERAN_POLL_INTERVAL", "120"))
```

- [ ] **Step 2: Commit**

```bash
git add config.py
git commit -m "config: reduce default poll interval from 300s to 120s (2 min)"
```

---

## Task 3: Translate `auth.py` to English

**Files:**
- Modify: `auth.py`

- [ ] **Step 1: Replace `login_interactive()` print block**

Replace lines 29–36 in `auth.py`:

```python
    print("=" * 60)
    print("Opening browser for manual ERAN portal login...")
    print("  1. Check 'Login without extension'")
    print("  2. Check 'I am not a robot' (reCAPTCHA)")
    print("  3. Click Login — you will receive a code by SMS/email")
    print("  4. Enter the code in the browser")
    print("  5. Once you reach the call-centre page, return here and press Enter")
    print("=" * 60)
```

- [ ] **Step 2: Replace the two remaining Hebrew strings**

Replace line 57:

```python
        print("\nComplete login in the browser, then press Enter here...")
```

Replace lines 64–65:

```python
            print(f"[Warning] Current page URL: {current}")
            print("Login may not have completed. Saving cookies anyway.")
```

Replace line 68:

```python
        print(f"[✓] Session saved to: {SESSION_FILE}")
```

- [ ] **Step 3: Commit**

```bash
git add auth.py
git commit -m "i18n: translate auth.py login prompts to English"
```

---

## Task 4: Translate `collector.py` to English and add `--debug` support

**Files:**
- Modify: `collector.py`

- [ ] **Step 1: Translate `_handle_sigint` message (line 33)**

```python
    print("\n[!] Stop requested — shutting down cleanly.")
```

- [ ] **Step 2: Translate `run_collector()` messages**

Replace lines 39–43 (session file missing error):

```python
        print(
            f"[Error] Session file not found ({SESSION_FILE}).\n"
            "Run first:  python3 main.py login"
        )
```

Replace line 48–49 (startup banner):

```python
    print(f"[✓] Starting monitor — sampling every {POLL_INTERVAL_SECONDS}s ({POLL_INTERVAL_SECONDS // 60} min).")
    print("    Press Ctrl+C to stop.\n")
```

Replace line 73 (session expired):

```python
                print("[!] Session expired. Run 'login' again then restart collect.")
```

Replace line 81 (scrape warning):

```python
                log.warning("Failed to extract stats from page.")
```

Replace line 87 (monitor ended):

```python
    print("[✓] Monitor stopped.")
```

- [ ] **Step 3: Add `debug` parameter to `run_collector()` and wire up debug file dump**

Replace the function signature and the data extraction block. The full updated section from `run_collector` (replace lines 37–87):

```python
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
```

- [ ] **Step 4: Translate `_print_sample()` status line labels (lines 109–112)**

```python
    print(
        f"[{ts}]  Calls: {calls}  |  Waiting: {waiting}  |  "
        f"Connected: {connected}  |  On break: {on_break}"
    )
```

- [ ] **Step 5: Commit**

```bash
git add collector.py
git commit -m "i18n: translate collector.py to English; add --debug flag support"
```

---

## Task 5: Translate `reporter.py` to English

**Files:**
- Modify: `reporter.py`
- Create: `tests/test_reporter.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_reporter.py`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from reporter import _gap


def test_gap_shortage():
    """supply=5, demand=6 → gap=-1 (shortage)."""
    row = {"calls": 4, "waiting": 2, "connected": 10, "on_break": 5}
    assert _gap(row) == -1


def test_gap_surplus():
    """supply=8, demand=3 → gap=+5 (surplus)."""
    row = {"calls": 2, "waiting": 1, "connected": 10, "on_break": 2}
    assert _gap(row) == 5


def test_gap_handles_none_values():
    """None fields default to 0."""
    row = {"calls": None, "waiting": None, "connected": 5, "on_break": 0}
    assert _gap(row) == 5
```

- [ ] **Step 2: Run tests to verify they pass (logic is correct, only strings change)**

```bash
python3 -m pytest tests/test_reporter.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 3: Replace the full `reporter.py`**

```python
"""
Weekly analysis report.

Produces:
  1. A text summary printed to stdout
  2. A PNG chart saved to disk (requires matplotlib)

Key question: when are there staffing shortages vs. surpluses?

We define:
  demand   = calls + waiting          (how many callers need attention right now)
  supply   = connected - on_break     (volunteers actually available)
  gap      = supply - demand          (positive = surplus, negative = shortage)
"""
import datetime
import statistics
from collections import defaultdict

DAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _gap(row: dict) -> float | None:
    calls     = row.get("calls")     or 0
    waiting   = row.get("waiting")   or 0
    connected = row.get("connected") or 0
    on_break  = row.get("on_break")  or 0
    demand = calls + waiting
    supply = connected - on_break
    return supply - demand


def generate_report(rows: list, output_chart: str = "eran_report.png") -> None:
    if not rows:
        print("No data to report.")
        return

    print("\n" + "=" * 64)
    print("  ERAN Call Centre Monitor Report")
    print(f"  Period: {rows[0]['ts'][:16]}  to  {rows[-1]['ts'][:16]}")
    print(f"  Total samples: {len(rows)}")
    print("=" * 64)

    for field, label in [
        ("calls",     "Active calls (avg)          "),
        ("waiting",   "Waiting callers (avg)        "),
        ("connected", "Connected volunteers (avg)   "),
        ("on_break",  "Volunteers on break (avg)    "),
    ]:
        vals = [r[field] for r in rows if r.get(field) is not None]
        if vals:
            print(f"  {label}: {statistics.mean(vals):.1f}  (max {max(vals)}, min {min(vals)})")

    gaps = [g for r in rows if (g := _gap(r)) is not None]
    if gaps:
        print(f"\n  Average gap (supply minus demand): {statistics.mean(gaps):+.1f}")
        print(f"  Worst (shortage): {min(gaps):+.1f}")
        print(f"  Best  (surplus):  {max(gaps):+.1f}")

    print("\n  Breakdown by day of week:")
    by_day: dict[int, list] = defaultdict(list)
    for r in rows:
        g = _gap(r)
        if g is not None:
            by_day[r["day_of_week"]].append(g)

    for dow in range(7):
        if dow in by_day:
            vals = by_day[dow]
            avg = statistics.mean(vals)
            status = "✓ surplus" if avg > 0 else "✗ shortage"
            print(f"    {DAYS_EN[dow]:9s}: avg gap {avg:+.1f}  ({status})")

    print("\n  Hours with greatest shortage (top 10):")
    by_hour: dict[int, list] = defaultdict(list)
    for r in rows:
        g = _gap(r)
        if g is not None:
            by_hour[r["hour"]].append(g)

    hour_avgs = [(h, statistics.mean(v)) for h, v in by_hour.items()]
    hour_avgs.sort(key=lambda x: x[1])
    for h, avg in hour_avgs[:10]:
        bar = "█" * max(0, int(-avg))
        print(f"    {h:02d}:00  gap {avg:+.1f}  {bar}")

    print("\n  Hours with greatest surplus (top 5):")
    for h, avg in sorted(hour_avgs, key=lambda x: -x[1])[:5]:
        bar = "█" * max(0, int(avg))
        print(f"    {h:02d}:00  gap {avg:+.1f}  {bar}")

    print("=" * 64 + "\n")

    _try_plot(rows, by_hour, output_chart)


def _try_plot(rows: list, by_hour: dict, output_chart: str) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates

        timestamps = [datetime.datetime.fromisoformat(r["ts"]) for r in rows]
        gaps = [_gap(r) for r in rows]

        fig, axes = plt.subplots(2, 1, figsize=(14, 9))
        fig.suptitle("ERAN Call Centre Monitor", fontsize=14)

        ax = axes[0]
        ax.plot(timestamps, gaps, color="steelblue", linewidth=0.8, alpha=0.7)
        ax.axhline(0, color="red", linewidth=1, linestyle="--", label="Break-even")
        ax.fill_between(timestamps, gaps, 0,
                        where=[g < 0 for g in gaps],
                        alpha=0.3, color="red", label="shortage")
        ax.fill_between(timestamps, gaps, 0,
                        where=[g >= 0 for g in gaps],
                        alpha=0.3, color="green", label="surplus")
        ax.set_ylabel("Gap (supply minus demand)")
        ax.set_title("Gap over time")
        ax.legend()
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m %H:%M"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate()

        ax2 = axes[1]
        hours = sorted(by_hour.keys())
        avgs = [statistics.mean(by_hour[h]) for h in hours]
        colors = ["green" if a >= 0 else "red" for a in avgs]
        ax2.bar(hours, avgs, color=colors, alpha=0.7)
        ax2.axhline(0, color="black", linewidth=0.8)
        ax2.set_xlabel("Hour")
        ax2.set_ylabel("Average gap")
        ax2.set_title("Average gap by hour")
        ax2.set_xticks(range(0, 24))

        plt.tight_layout()
        plt.savefig(output_chart, dpi=120, bbox_inches="tight")
        print(f"[✓] Chart saved: {output_chart}")
    except ImportError:
        print("[!] matplotlib not installed — chart not generated.")
    except Exception as exc:
        print(f"[!] Error generating chart: {exc}")
```

- [ ] **Step 4: Run reporter tests to confirm nothing broke**

```bash
python3 -m pytest tests/test_reporter.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add reporter.py tests/test_reporter.py
git commit -m "i18n: translate reporter.py to English; update chart labels and day names"
```

---

## Task 6: Add `watch` subcommand + translate `main.py`

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Replace the full `main.py`**

```python
"""
Entry point for the ERAN call-centre monitor.

Commands
--------
login    – open a browser, let the user log in and save the session
collect  – start periodic data collection (runs until Ctrl+C)
report   – print a weekly summary and save a chart
export   – dump all rows to CSV
watch    – live-refresh report in a second terminal (reads from DB)

Examples
--------
    python3 main.py login
    python3 main.py collect
    python3 main.py collect --debug
    python3 main.py report
    python3 main.py report --days 3 --chart my_chart.png
    python3 main.py export --out data.csv
    python3 main.py watch
    python3 main.py watch --interval 60
"""
import argparse
import csv
import logging
import os
import signal
import sys
import time

try:
    from monitor.config import DB_PATH
    from monitor.storage import get_conn, fetch_recent_days, fetch_all
except ModuleNotFoundError:
    from config import DB_PATH
    from storage import get_conn, fetch_recent_days, fetch_all


def cmd_login(_args) -> None:
    try:
        from monitor.auth import login_interactive
    except ModuleNotFoundError:
        from auth import login_interactive
    login_interactive()


def cmd_collect(args) -> None:
    try:
        from monitor.collector import run_collector
    except ModuleNotFoundError:
        from collector import run_collector
    run_collector(args.db, debug=getattr(args, "debug", False))


def cmd_report(args) -> None:
    try:
        from monitor.reporter import generate_report
    except ModuleNotFoundError:
        from reporter import generate_report
    conn = get_conn(args.db)
    rows = fetch_recent_days(conn, days=args.days)
    if not rows:
        print(f"[!] No data in the last {args.days} days.")
        sys.exit(0)
    generate_report(rows, output_chart=args.chart)


def cmd_export(args) -> None:
    conn = get_conn(args.db)
    rows = fetch_all(conn)
    if not rows:
        print("[!] No data to export.")
        sys.exit(0)
    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"[✓] Exported {len(rows)} rows to: {args.out}")


def cmd_watch(args) -> None:
    try:
        from monitor.reporter import generate_report
        from monitor.storage import get_conn, fetch_recent_days
    except ModuleNotFoundError:
        from reporter import generate_report
        from storage import get_conn, fetch_recent_days

    running = True

    def _stop(sig, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, _stop)
    conn = get_conn(args.db)

    while running:
        os.system("clear")
        rows = fetch_recent_days(conn, days=1)
        if rows:
            generate_report(rows)
        else:
            print("No data collected yet. Is 'collect' running?")

        print(f"[Refreshing every {args.interval}s — Ctrl+C to stop]")

        for _ in range(args.interval):
            if not running:
                break
            time.sleep(1)


def main() -> None:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="ERAN call-centre monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--db", default=DB_PATH, help="Path to SQLite file (default: %(default)s)")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("login", help="Interactive browser login (saves session)")

    collect_p = sub.add_parser("collect", help="Start continuous monitoring")
    collect_p.add_argument("--debug", action="store_true",
                           help="Write raw page text to scrape_debug.txt each cycle")
    collect_p.set_defaults(func=cmd_collect)

    report_p = sub.add_parser("report", help="Generate weekly report")
    report_p.add_argument("--days", type=int, default=7, help="Days to include (default: 7)")
    report_p.add_argument("--chart", default="eran_report.png", help="Chart output filename")
    report_p.set_defaults(func=cmd_report)

    export_p = sub.add_parser("export", help="Export data to CSV")
    export_p.add_argument("--out", default="eran_data.csv", help="Output filename")
    export_p.set_defaults(func=cmd_export)

    watch_p = sub.add_parser("watch", help="Live-refresh report in terminal (reads from DB)")
    watch_p.add_argument("--interval", type=int, default=120,
                         help="Refresh interval in seconds (default: 120)")
    watch_p.set_defaults(func=cmd_watch)

    for name, func in [("login", cmd_login), ("collect", cmd_collect)]:
        sub.choices[name].set_defaults(func=func)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke-test the CLI**

```bash
cd /home/avi/Projects/EranMonitor
python3 main.py --help
python3 main.py watch --help
python3 main.py collect --help
```

Expected: help text prints in English with `watch` and `--debug` listed, no import errors.

- [ ] **Step 3: Run all tests**

```bash
python3 -m pytest tests/ -v
```

Expected: all 8 tests PASS.

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "feat: add watch subcommand; translate main.py to English; wire --debug to collect"
```

---

## Done — verification checklist

- [ ] `python3 main.py login` → English instructions in terminal
- [ ] `python3 main.py collect` → English status lines (`Calls: 4 | Waiting: 2 | ...`)
- [ ] `python3 main.py watch` → clears terminal, prints English report, refreshes every 120s
- [ ] `python3 main.py watch --interval 30` → refreshes every 30s
- [ ] `python3 main.py collect --debug` → writes `scrape_debug.txt` each cycle
- [ ] `python3 -m pytest tests/ -v` → all tests pass
