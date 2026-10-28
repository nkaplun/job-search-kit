#!/usr/bin/env python3
"""Job application tracker.

Single source of truth: applications.csv (opens fine in Excel / Google Sheets).
Per-application notes live in notes/<id>-<company>.md and are appended to, never
overwritten. Archived job descriptions live in postings/.

All three live in one data folder, `applications/` under the current directory by
default. Point somewhere else with --dir (before the command name).

Usage examples:
    python3 tracker.py add --company "Acme" --role "AI Engineer" \
        --link "https://..." --source "LinkedIn" --status applied
    python3 tracker.py update A003 --status interviewing --note "Recruiter screen went well"
    python3 tracker.py note A003 "Sent thank-you email to Dana"
    python3 tracker.py list --open
    python3 tracker.py report
    python3 tracker.py export --out Application_Log.md
    python3 tracker.py --dir ~/job-search/applications report
"""

import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta

# Set from --dir in main()
DATA_DIR = CSV_PATH = NOTES_DIR = POSTINGS_DIR = None

FIELDS = [
    "id",
    "company",
    "sector",
    "role",
    "location",
    "work_mode",       # onsite / hybrid / remote
    "link",
    "posting",         # archived copy of the job description (links expire)
    "source",          # LinkedIn, referral, careers page, recruiter, ...
    "date_applied",
    "status",
    "resume_used",
    "contact",         # recruiter / referral name + email
    "last_activity",   # auto-stamped on every update
    "next_action",
    "next_action_date",
    "compensation",
    "notes",           # one-line summary; long notes go in notes/<id>-*.md
]

STATUSES = [
    "saved",          # found it, not applied yet
    "applied",
    "oa",             # online assessment / take-home sent
    "screening",      # recruiter screen scheduled or done
    "interviewing",
    "offer",
    "accepted",
    "rejected",
    "withdrawn",
    "ghosted",        # no reply, written off
]

OPEN_STATUSES = {"saved", "applied", "oa", "screening", "interviewing", "offer"}
STALE_AFTER_DAYS = 10
TODAY = date.today()

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def set_data_dir(path):
    global DATA_DIR, CSV_PATH, NOTES_DIR, POSTINGS_DIR
    DATA_DIR = os.path.abspath(os.path.expanduser(path))
    CSV_PATH = os.path.join(DATA_DIR, "applications.csv")
    NOTES_DIR = os.path.join(DATA_DIR, "notes")
    POSTINGS_DIR = os.path.join(DATA_DIR, "postings")


def find_chrome():
    for name in ("google-chrome", "google-chrome-stable", "chromium",
                 "chromium-browser", "chrome", "msedge"):
        found = shutil.which(name)
        if found:
            return found
    for path in CHROME_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


# ---------- storage ----------

def load():
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return [dict(r) for r in csv.DictReader(f)]


def save(rows):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


def next_id(rows):
    nums = [int(r["id"][1:]) for r in rows if re.fullmatch(r"A\d+", r.get("id", ""))]
    return "A%03d" % ((max(nums) + 1) if nums else 1)


def find(rows, app_id):
    app_id = app_id.upper()
    for r in rows:
        if r["id"].upper() == app_id:
            return r
    sys.exit("No application with id %s. Run `list` to see ids." % app_id)


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "unknown"


def note_path(row):
    return os.path.join(NOTES_DIR, "%s-%s.md" % (row["id"], slug(row["company"])))


def append_note(row, text):
    os.makedirs(NOTES_DIR, exist_ok=True)
    path = note_path(row)
    new = not os.path.exists(path)
    with open(path, "a", encoding="utf-8") as f:
        if new:
            f.write("# %s - %s (%s)\n\n" % (row["company"], row["role"], row["id"]))
            if row.get("link"):
                f.write("Posting: %s\n\n" % row["link"])
        f.write("## %s\n%s\n\n" % (TODAY.isoformat(), text))
    return path


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def days_since(value):
    d = parse_date(value)
    return (TODAY - d).days if d else None


# ---------- commands ----------

def cmd_add(args):
    rows = load()
    if not args.allow_duplicate:
        for r in rows:
            if (r["company"].lower() == args.company.lower()
                    and r["role"].lower() == args.role.lower()):
                sys.exit("Already tracked as %s (status: %s). Use `update %s ...` "
                         "or pass --allow-duplicate." % (r["id"], r["status"], r["id"]))

    applied = args.date_applied or (TODAY.isoformat() if args.status != "saved" else "")
    row = {
        "id": next_id(rows),
        "company": args.company,
        "sector": args.sector or "",
        "role": args.role,
        "location": args.location or "",
        "work_mode": args.work_mode or "",
        "link": args.link or "",
        "posting": args.posting or "",
        "source": args.source or "",
        "date_applied": applied,
        "status": args.status,
        "resume_used": args.resume or "",
        "contact": args.contact or "",
        "last_activity": TODAY.isoformat(),
        "next_action": args.next_action or "",
        "next_action_date": args.next_action_date or "",
        "compensation": args.compensation or "",
        "notes": args.notes or "",
    }
    rows.append(row)
    save(rows)
    print("Added %s - %s, %s [%s]" % (row["id"], row["company"], row["role"], row["status"]))
    if args.notes:
        print("Notes file: %s" % append_note(row, args.notes))


def cmd_update(args):
    rows = load()
    row = find(rows, args.id)
    changes = []
    for field in ("status", "next_action", "next_action_date", "contact",
                  "compensation", "link", "posting", "source", "resume_used",
                  "location", "sector", "work_mode", "date_applied", "notes"):
        val = getattr(args, field, None)
        if val is not None:
            if row.get(field, "") != val:
                changes.append("%s: %s -> %s" % (field, row.get(field) or "(empty)", val))
            row[field] = val
    row["last_activity"] = args.date or TODAY.isoformat()
    save(rows)
    print("Updated %s - %s, %s" % (row["id"], row["company"], row["role"]))
    for c in changes:
        print("  " + c)
    if args.note:
        entry = args.note
        if changes:
            entry = "%s\n\n_(%s)_" % (args.note, "; ".join(changes))
        print("  note -> %s" % append_note(row, entry))
    elif changes:
        append_note(row, "; ".join(changes))


def cmd_note(args):
    rows = load()
    row = find(rows, args.id)
    row["last_activity"] = TODAY.isoformat()
    save(rows)
    print("Note added to %s" % append_note(row, args.text))


def cmd_posting(args):
    """Archive the job description. Posting links often disappear after a role closes."""
    rows = load()
    row = find(rows, args.id)
    os.makedirs(POSTINGS_DIR, exist_ok=True)
    base = "%s-%s" % (row["id"], slug(row["company"]))
    saved = [f for f in (row.get("posting") or "").split(",") if f]

    def record(filename):
        if filename not in saved:
            saved.append(filename)
        print("  saved postings/%s" % filename)

    if args.text_file:
        src = os.path.expanduser(args.text_file)
        if not os.path.exists(src):
            sys.exit("No such file: %s" % src)
        dest = base + ".md"
        with open(src, encoding="utf-8", errors="replace") as f:
            body = f.read()
        with open(os.path.join(POSTINGS_DIR, dest), "w", encoding="utf-8") as f:
            f.write("# %s - %s\n\nArchived %s\n" % (row["company"], row["role"],
                                                     TODAY.isoformat()))
            if row.get("link"):
                f.write("Original: %s\n" % row["link"])
            f.write("\n---\n\n" + body.rstrip() + "\n")
        record(dest)

    if args.pdf:
        src = os.path.expanduser(args.pdf)
        if not os.path.exists(src):
            sys.exit("No such file: %s" % src)
        dest = base + ".pdf"
        shutil.copy2(src, os.path.join(POSTINGS_DIR, dest))
        record(dest)

    if args.url is not None or args.print_page:
        url = args.url or row.get("link")
        if not url:
            sys.exit("No URL given and this application has no link on file.")
        chrome = find_chrome()
        if not chrome:
            sys.exit("No Chrome, Chromium, or Edge found. Save the posting as a PDF by "
                     "hand and pass it with --pdf.")
        dest = base + ".pdf"
        out = os.path.join(POSTINGS_DIR, dest)
        before = os.path.getsize(out) if os.path.exists(out) else -1
        profile = os.path.join(POSTINGS_DIR, ".chrome-profile")
        proc = subprocess.Popen(
            [chrome, "--headless=new", "--disable-gpu", "--no-first-run",
             "--user-data-dir=" + profile, "--virtual-time-budget=15000",
             "--no-pdf-header-footer", "--print-to-pdf=" + out, url],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            proc.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            proc.kill()          # Chrome often writes the PDF then fails to exit
            proc.wait()
        shutil.rmtree(profile, ignore_errors=True)
        size = os.path.getsize(out) if os.path.exists(out) else -1
        if size <= 0 or size == before:
            sys.exit("The browser produced no PDF for %s. Job boards often block headless "
                     "browsers. Open the posting, print to PDF yourself, then run "
                     "`posting %s --pdf <file>`." % (url, row["id"]))
        record(dest)
        if size < 12000:
            print("  WARNING: only %d bytes. That may be a login wall rather than the "
                  "posting. Open postings/%s and check." % (size, dest))

    if not saved:
        sys.exit("Nothing archived. Pass --url, --pdf, or --text-file.")
    row["posting"] = ",".join(saved)
    row["last_activity"] = TODAY.isoformat()
    save(rows)


def cmd_list(args):
    rows = load()
    if args.status:
        rows = [r for r in rows if r["status"] in args.status]
    if args.open:
        rows = [r for r in rows if r["status"] in OPEN_STATUSES]
    if args.company:
        rows = [r for r in rows if args.company.lower() in r["company"].lower()]
    if not rows:
        print("No applications match.")
        return
    rows.sort(key=lambda r: (r.get("date_applied") or "0000", r["id"]), reverse=True)
    width = max(len(r["company"]) for r in rows)
    for r in rows:
        stale = days_since(r.get("last_activity"))
        flag = " *stale*" if (r["status"] in OPEN_STATUSES and stale is not None
                              and stale >= STALE_AFTER_DAYS) else ""
        print("%s  %-*s  %-14s  %-11s  %s%s" % (
            r["id"], width, r["company"], r["status"],
            r.get("date_applied") or "not applied", r["role"], flag))
    print("\n%d application(s)." % len(rows))


def cmd_report(args):
    rows = load()
    if not rows:
        print("No applications tracked yet. Add one with `add`.")
        return
    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    applied_rows = [r for r in rows if parse_date(r.get("date_applied"))]
    last7 = [r for r in applied_rows if days_since(r["date_applied"]) <= 7]
    last30 = [r for r in applied_rows if days_since(r["date_applied"]) <= 30]

    print("JOB APPLICATION REPORT - %s" % TODAY.isoformat())
    print("=" * 46)
    print("Total tracked:        %d" % len(rows))
    print("Applied last 7 days:  %d" % len(last7))
    print("Applied last 30 days: %d" % len(last30))
    print("\nBy status")
    for s in STATUSES:
        if counts.get(s):
            print("  %-14s %d" % (s, counts[s]))

    submitted = [r for r in rows if r["status"] != "saved"]
    reached = [r for r in rows if r["status"] in
               {"oa", "screening", "interviewing", "offer", "accepted"}]
    if submitted:
        print("\nResponse rate: %d/%d (%.0f%%) reached a screen or beyond"
              % (len(reached), len(submitted), 100 * len(reached) / len(submitted)))

    due = [r for r in rows if parse_date(r.get("next_action_date"))
           and parse_date(r["next_action_date"]) <= TODAY + timedelta(days=args.horizon)]
    if due:
        print("\nNext actions due within %d days" % args.horizon)
        for r in sorted(due, key=lambda r: r["next_action_date"]):
            print("  %s  %s  %s - %s" % (r["next_action_date"], r["id"],
                                         r["company"], r["next_action"] or "(unspecified)"))

    unarchived = [r for r in rows if r["status"] != "saved" and not r.get("posting")]
    if unarchived:
        print("\nNo saved copy of the job description (links expire)")
        for r in unarchived:
            print("  %s  %s - %s" % (r["id"], r["company"], r["role"]))

    stale = [r for r in rows if r["status"] in OPEN_STATUSES
             and (days_since(r.get("last_activity")) or 0) >= args.stale_days]
    if stale:
        print("\nNo movement in %d+ days - consider a follow-up" % args.stale_days)
        for r in sorted(stale, key=lambda r: r.get("last_activity") or ""):
            print("  %s  %s - %s (%d days, %s)" % (
                r["id"], r["company"], r["role"],
                days_since(r["last_activity"]), r["status"]))


def cmd_export(args):
    rows = load()
    if not rows:
        sys.exit("Nothing to export.")
    rows.sort(key=lambda r: (r.get("date_applied") or "0000", r["id"]))
    cols = args.columns.split(",") if args.columns else [
        "date_applied", "company", "role", "location", "source", "status", "next_action"]
    headers = [c.replace("_", " ").title() for c in cols]
    title = "# Application Log" + (" - " + args.name if args.name else "")
    lines = [title,
             "",
             "Generated %s. %d applications." % (TODAY.isoformat(), len(rows)),
             "",
             "| " + " | ".join(headers) + " |",
             "|" + "|".join(["---"] * len(cols)) + "|"]
    for r in rows:
        lines.append("| " + " | ".join((r.get(c) or "-").replace("|", "\\|")
                                       for c in cols) + " |")
    out = "\n".join(lines) + "\n"
    if args.out:
        path = args.out if os.path.isabs(args.out) else os.path.join(DATA_DIR, args.out)
        with open(path, "w", encoding="utf-8") as f:
            f.write(out)
        print("Wrote %s" % path)
    else:
        print(out)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dir", default="applications",
                   help="data folder holding applications.csv, notes/, postings/ "
                        "(default: ./applications)")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="track a new application")
    a.add_argument("--company", required=True)
    a.add_argument("--role", required=True)
    a.add_argument("--sector")
    a.add_argument("--location")
    a.add_argument("--work-mode", dest="work_mode")
    a.add_argument("--link")
    a.add_argument("--posting", help="filename in postings/ (use the `posting` command instead)")
    a.add_argument("--source")
    a.add_argument("--date-applied", dest="date_applied")
    a.add_argument("--status", choices=STATUSES, default="applied")
    a.add_argument("--resume")
    a.add_argument("--contact")
    a.add_argument("--next-action", dest="next_action")
    a.add_argument("--next-action-date", dest="next_action_date")
    a.add_argument("--compensation")
    a.add_argument("--notes")
    a.add_argument("--allow-duplicate", action="store_true")
    a.set_defaults(func=cmd_add)

    u = sub.add_parser("update", help="change status or fields on an application")
    u.add_argument("id")
    u.add_argument("--status", choices=STATUSES)
    u.add_argument("--next-action", dest="next_action")
    u.add_argument("--next-action-date", dest="next_action_date")
    u.add_argument("--contact")
    u.add_argument("--compensation")
    u.add_argument("--link")
    u.add_argument("--posting")
    u.add_argument("--source")
    u.add_argument("--resume-used", dest="resume_used")
    u.add_argument("--location")
    u.add_argument("--sector")
    u.add_argument("--work-mode", dest="work_mode")
    u.add_argument("--date-applied", dest="date_applied")
    u.add_argument("--notes")
    u.add_argument("--note", help="append a dated entry to the notes file")
    u.add_argument("--date", help="override the last-activity date (YYYY-MM-DD)")
    u.set_defaults(func=cmd_update)

    n = sub.add_parser("note", help="append a dated note without changing status")
    n.add_argument("id")
    n.add_argument("text")
    n.set_defaults(func=cmd_note)

    pg = sub.add_parser("posting", help="archive the job description (PDF or text)")
    pg.add_argument("id")
    pg.add_argument("--url", nargs="?", const="", help="page to print; omit value to use the stored link")
    pg.add_argument("--print-page", action="store_true", help="print the stored link")
    pg.add_argument("--pdf", help="a PDF you already downloaded")
    pg.add_argument("--text-file", dest="text_file", help="posting text saved to a file")
    pg.add_argument("--timeout", type=int, default=75)
    pg.set_defaults(func=cmd_posting)

    l = sub.add_parser("list", help="show tracked applications")
    l.add_argument("--status", nargs="+", choices=STATUSES)
    l.add_argument("--open", action="store_true", help="only still-live applications")
    l.add_argument("--company")
    l.set_defaults(func=cmd_list)

    r = sub.add_parser("report", help="summary, follow-ups due, stale applications")
    r.add_argument("--horizon", type=int, default=7,
                   help="days ahead to include next actions (default 7)")
    r.add_argument("--stale-days", dest="stale_days", type=int, default=STALE_AFTER_DAYS,
                   help="flag open applications with no movement for this many days "
                        "(default %d)" % STALE_AFTER_DAYS)
    r.set_defaults(func=cmd_report)

    e = sub.add_parser("export", help="markdown table of applications")
    e.add_argument("--out", help="file to write, relative to the data folder (default: stdout)")
    e.add_argument("--columns", help="comma-separated csv column names")
    e.add_argument("--name", help="name to put in the title")
    e.set_defaults(func=cmd_export)

    args = p.parse_args()
    set_data_dir(args.dir)
    args.func(args)


if __name__ == "__main__":
    main()
