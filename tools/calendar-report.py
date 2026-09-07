#!/usr/bin/env python3
"""
Editorial calendar report for content/calendar.csv.

    python3 tools/calendar-report.py            # summary + what is in progress
    python3 tools/calendar-report.py P1         # every backlog row at that priority
    python3 tools/calendar-report.py refresh    # published pages past their refresh date
    python3 tools/calendar-report.py check      # rows whose page exists on disk but are not marked published, and vice versa

Columns: slug, path, cluster, priority, title, primary_keyword, status
(backlog | briefed | drafted | published | refresh), publish_date, refresh_due,
gsc_clicks_30d, gsc_clicks_90d, notes. Update the row when a page moves.
"""
import csv, datetime, pathlib, sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAL = ROOT / "content" / "calendar.csv"

def load():
    with CAL.open(newline="") as f:
        return list(csv.DictReader(f))

def main():
    rows = load()
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    today = datetime.date.today().isoformat()
    if arg.upper().startswith("P"):
        for r in rows:
            if r["priority"].upper() == arg.upper() and r["status"] == "backlog":
                print(f'{r["cluster"]:16} {r["path"]:60} {r["title"]}')
        return
    if arg == "refresh":
        for r in rows:
            if r["status"] == "published" and r["refresh_due"] and r["refresh_due"] <= today:
                print(f'{r["refresh_due"]}  {r["path"]}  {r["title"]}')
        return
    if arg == "check":
        for r in rows:
            exists = (ROOT / r["path"].strip("/") / "index.html").exists()
            if exists and r["status"] not in ("published", "drafted"):
                print(f'on disk but status={r["status"]}: {r["path"]}')
            if not exists and r["status"] in ("published", "drafted"):
                print(f'status={r["status"]} but missing on disk: {r["path"]}')
        return
    by_status = Counter(r["status"] for r in rows)
    by_prio = Counter((r["priority"], r["status"]) for r in rows)
    print(f"{len(rows)} rows. " + ", ".join(f"{k}: {v}" for k, v in sorted(by_status.items())))
    for p in ("P0", "P1", "P2", "P3"):
        line = ", ".join(f"{s} {n}" for (pp, s), n in sorted(by_prio.items()) if pp == p)
        if line: print(f"  {p}: {line}")
    active = [r for r in rows if r["status"] in ("briefed", "drafted")]
    if active:
        print("\nIn progress:")
        for r in active:
            print(f'  [{r["status"]}] {r["path"]}  {r["title"]}')
    due = [r for r in rows if r["status"] == "published" and r["refresh_due"] and r["refresh_due"] <= today]
    if due:
        print(f"\n{len(due)} page(s) due for refresh; run with 'refresh' to list them.")

if __name__ == "__main__":
    main()
