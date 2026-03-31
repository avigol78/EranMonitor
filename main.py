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
