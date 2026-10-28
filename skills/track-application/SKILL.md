---
name: track-application
description: Log, update, and report on job applications in a CSV tracker. Use whenever the user mentions applying to a job, pastes a job posting or URL they applied to, reports a recruiter reply, interview, offer, or rejection, asks what they applied to, asks what to follow up on, or wants an application log.
---

# Application tracking

## Where things live

All data lives in `applications/` inside the job-search folder (the folder that holds
`job-search-profile.md`):
- `applications/applications.csv`: one row per application. Opens in Excel or
  Google Sheets.
- `applications/notes/<id>-<company>.md`: dated notes per application (recruiter
  emails, interview debriefs).
- `applications/postings/`: saved copies of job descriptions, because posting links
  expire.

**Never edit the CSV by hand.** Always go through `scripts/tracker.py`, which ships
in this skill's folder. It assigns ids, validates statuses, and stamps dates. It creates
the `applications/` folder on first use.

Run it from the job-search folder, using the full path to the script:

```
python3 "<this skill's folder>/scripts/tracker.py" --help
```

If the current folder has no `job-search-profile.md`, ask the user where their
job-search folder is, or offer to run **job-search-setup**. To use a data folder
elsewhere, pass `--dir <path>` before the command name.

The examples below write `tracker.py` for short. Always use the full path.

## Logging a new application

When the user gives a job (a URL, a pasted description, or just "applied to X for Y"):

1. If they gave a URL, fetch it and pull out company, role, location, work mode
   (onsite, hybrid, remote), sector, and pay if listed. Don't ask for anything the
   posting already says.
2. Fill in what you can infer; leave the rest blank rather than guessing.
   - `source`: where they found it (LinkedIn, referral, careers page, recruiter).
   - `resume`: the file they sent. If `resume/tailored/` has a version for this
     company, that's probably it; otherwise `master.pdf`. Confirm if unsure.
   - `status`: `applied` if they already submitted, `saved` if it's a lead they
     haven't sent yet.
3. Run `add`. Then, if the profile says to save job descriptions (the default), archive
   the posting in the same turn (next section).
4. Show them the new row and ask only about fields that matter and that you couldn't
   determine.

```
python3 tracker.py add \
  --company "Acme" --role "AI Engineer" \
  --sector "Developer tools" --location "San Francisco, CA" --work-mode hybrid \
  --link "https://..." --source "LinkedIn" \
  --resume "Doe_AI_Engineer_Resume_Acme.pdf" \
  --status applied \
  --next-action "follow up if no reply" --next-action-date 2026-01-15
```

`add` refuses a company and role it already has. If it's really a second application
to the same role, pass `--allow-duplicate`; otherwise use `update`.

## Saving the posting

Options, best first:

1. **Text you already have.** If you fetched the URL or they pasted the description,
   write it to a temporary file and run:
   `python3 tracker.py posting A004 --text-file <file>`
2. **A PDF they saved.** Browser, then Print, then Save as PDF, then:
   `python3 tracker.py posting A004 --pdf ~/Downloads/posting.pdf`
3. **Automatic PDF:** `python3 tracker.py posting A004 --url` (no value uses the
   stored link). This uses Chrome, Chromium, or Edge in the background. It works on plain
   careers pages, but LinkedIn, Workday, and Greenhouse often show a login wall instead.
   If it warns about a small file, check the result and fall back to option 2.

Don't try option 3 more than once. If it fails, ask them to print the page to PDF.

## Updating

Any news (recruiter email, screen scheduled, interview done, rejection, offer):

```
python3 tracker.py update A004 --status interviewing \
  --note "Tech screen Jan 12 with Priya, focus on Python and system design" \
  --next-action "prep system design" --next-action-date 2026-01-10
```

Statuses, roughly in order: `saved`, `applied`, `oa` (online assessment or
take-home), `screening` (recruiter call), `interviewing`, `offer`, `accepted`,
`rejected`, `withdrawn`, `ghosted`.

For a note with no status change: `python3 tracker.py note A004 "text"`.

## Reporting

- `python3 tracker.py report`: counts by status, applications in the last 7 and 30
  days, response rate, follow-ups due, applications missing a saved posting, and
  anything with no movement in 10+ days. Pass `--stale-days N` to match the profile's
  follow-up setting.
- `python3 tracker.py list --open`: everything still live.
- `python3 tracker.py export --name "<their name>" --out Application_Log.md`: a
  markdown table, written into `applications/`. Use `--columns` to choose columns.

When they ask "where do things stand?" or "what should I follow up on?", run `report`
and summarize it in plain language. Lead with what needs action this week, then the
counts. Don't paste the raw output.

## When an interview comes up

When an application reaches `screening` or `interviewing`, offer to help them prepare:
research the company and role, and draft likely questions with answers drawn from their
real experience in `resume/master.tex`. Save it under `interview-prep/<Company>/`.
