# EranMonitor Improvements — Design Spec
**Date:** 2026-03-31

## Overview

Three improvements to the ERAN call-centre monitor:
1. Translate all Hebrew user-facing strings to English
2. Fix the scraper returning `?` for all collected values
3. Shorten the collection interval to 2 minutes and add a live `watch` command

---

## 1. Hebrew → English Translation

All user-facing strings (print statements, argparse help text, terminal output) are translated to English. Code-internal Hebrew (SQL column names, inline comments in scraper.py) is left unchanged.

**Files affected:**

| File | What changes |
|---|---|
| `main.py` | argparse descriptions, help strings, error messages |
| `collector.py` | startup banner, Ctrl+C message, status line labels (`שיחות:` → `Calls:`, etc.), error messages |
| `reporter.py` | all report section headers, stat labels, day names, chart titles/labels |
| `auth.py` | login step instructions printed to terminal |

---

## 2. Scraper Fix

**Root cause:** `scraper.py` maps `calls` to the Hebrew word "שיחות" but the actual portal page uses "בשיחה". Additionally, when all scraped values come back `None`, the failure is silent — the terminal just shows `?` with no explanation.

**Changes to `scraper.py`:**

1. Fix `calls` pattern: replace `"שיחות"` with `"בשיחה"` to match the actual page label
2. Add a warning message to the terminal when all 4 values are `None` (silent failure is now visible)
3. Add a `--debug` flag to the `collect` subcommand that writes raw scraped page text to `scrape_debug.txt` for future diagnosis

**Page fields (actual):**
- שלוחה → extension (ignored)
- בשיחה → `calls`
- בהמתנה → `waiting`
- פנויים/ות → available volunteers (logged but not persisted for now)
- בהפסקה → `on_break`
- מחוברים/ות → `connected`

**No schema changes** — DB columns stay as `calls`, `waiting`, `connected`, `on_break`.

---

## 3. Collection Interval + `watch` Command

### Interval

- `config.py`: default `POLL_INTERVAL_SECONDS` 300 → 120
- `collector.py`: startup message updated to reflect 2-minute interval

### `watch` Subcommand

**Usage:** `python3 main.py watch [--interval 120] [--db eran_monitor.db]`

**Behavior:**
1. Clear terminal
2. Print compact report summary (last 1 day of data by default) using the existing `generate_report()` function from `reporter.py`
3. Show "Next refresh in Xs" at the bottom
4. Sleep `--interval` seconds (default: 120)
5. Repeat until Ctrl+C

**Design decisions:**
- Reuses `generate_report()` — no new report logic
- Default window: last 1 day (keeps terminal output concise)
- `--interval` defaults to 120 to match the collect interval
- Runs independently in a second terminal alongside `collect`

**Files changed:**
- `config.py` — default interval 300 → 120
- `collector.py` — update startup message
- `main.py` — add `watch` subcommand + `cmd_watch()` function
- `reporter.py` — Hebrew → English only (no structural changes)

---

## Summary of File Changes

| File | Changes |
|---|---|
| `config.py` | Default interval 300 → 120 |
| `main.py` | Hebrew → English; add `watch` subcommand |
| `collector.py` | Hebrew → English; `--debug` flag; updated startup message |
| `scraper.py` | Fix `calls` pattern (`שיחות` → `בשיחה`); add silent-failure warning |
| `reporter.py` | Hebrew → English throughout |
| `auth.py` | Hebrew → English |
