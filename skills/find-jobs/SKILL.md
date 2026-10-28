---
name: find-jobs
description: Search the web for open job postings that match the user's filters in job-search-profile.md, check that each one is still open, score fit against their master resume, and save a ranked list. Use when the user asks to find jobs, look for openings, search for roles, or refresh their job leads.
---

# Find jobs

## Before you start

1. Find `job-search-profile.md` in the current working directory. If it isn't there,
   stop and run the **job-search-setup** skill first.
2. Read the profile (filters, how many jobs per run) and `resume/master.tex` (what the
   user can actually claim). Use the filters as written; don't re-ask for them. If the
   user adds a one-off filter in their request ("only remote this time"), apply it to
   this run without editing the profile.
3. If `applications/applications.csv` exists, read it so you don't return jobs they
   already applied to or saved.
4. Read the most recent file in `leads/`, if any, so this run favors new postings. A job
   from an earlier run can repeat only if it's still open and a strong fit; mark it as
   seen before.

## Searching

Run many searches. One per target role per location is a reasonable start, plus variants
of the title (for example "forward deployed engineer" and "FDE"). Send them in parallel.

**Search results are mostly dead links.** Search engines keep job pages indexed for months
after a role closes, so most individual posting links from a search return 404 or redirect
to a careers page. Use search to find **companies** that hire for these roles, then pull
each company's live list of openings straight from its job board. These public endpoints
return current openings as JSON, with no login (replace `<company>` with the board name
from any of that company's job links):

| Board | Live list of openings |
|---|---|
| Greenhouse | `curl -s https://boards-api.greenhouse.io/v1/boards/<company>/jobs` (add `?content=true` for descriptions) |
| Ashby | `curl -s "https://api.ashbyhq.com/posting-api/job-board/<company>?includeCompensation=true"` (includes `descriptionPlain`) |
| Lever | `curl -s "https://api.lever.co/v0/postings/<company>?mode=json"` |

Filter the results by title and location with a short Python script, then check only the
matches. A job that's on the live list is open. Ashby posting pages show almost no text to a
plain fetch, so read Ashby descriptions from the list instead.

Where to find companies:
1. `site:` searches on the job boards, for example
   `site:job-boards.greenhouse.io "analytics engineer" remote`. Use the company name
   from each result, not the link.
2. Aggregators (LinkedIn, Indeed, Wellfound, Built In) and "companies hiring <role>"
   lists. Aggregator links often need a login or are expired.
3. Companies the user names, and well-known employers for the role in their area.

For companies on Workday or their own careers site, fetch the careers page and look for the
role there.

If the user wants a large run (40+ jobs) and subagents are available, it's fine to split
the searching across a few parallel agents by role or region. Give each agent the filters
and the list of companies to skip, and merge their results yourself.

## Checking each posting

Fetch every posting before including it (or read it from the board's list). Drop it if:
- it's closed, removed, or redirects to a generic careers page
- the level is wrong for the profile (watch for "senior", "staff", "lead", "principal",
  and required years of experience above the profile's level)
- the location doesn't match (check for "must be in office 5 days" on remote-looking jobs)
- the company or industry is on the skip list

From each posting that passes, pull out: company, role, location, work mode (onsite,
hybrid, remote), link, date posted if shown, pay if listed, and the 4 to 6 requirements
that matter most.

## Scoring fit

Compare each posting's requirements to the master resume and the profile's list of true
facts. Score 1 to 5:
- **5**: most must-haves are clearly on the resume
- **4**: a strong match with one or two gaps that are nice-to-haves
- **3**: a reasonable stretch; worth applying with a tailored resume
- **2 or 1**: leave it out unless the run is short on results

For each job write one sentence on why it fits, citing something real from the resume,
and one sentence on the gaps. Be honest about gaps; the user relies on them to decide
where to spend time.

## Saving the results

Write two files to `leads/`, named with today's date:

- `Job_Leads_<YYYY-MM-DD>.json`: a list of objects with these keys:
  `company, role, location, work_mode, link, posted, pay, fit, why, gaps,
  key_requirements` (a list), `seen_before` (true or false).
- `Job_Leads_<YYYY-MM-DD>.csv`: the same rows with `key_requirements` joined by
  `; `, sorted by fit (highest first), then by date posted (newest first). Write it
  with Python's `csv` module so commas inside fields are quoted correctly. It opens
  directly in Excel or Google Sheets.

## Reporting back

Keep it short:
1. How many postings you checked and how many made the list.
2. A table of the top 10: company, role, location, fit, one-line why.
3. Any pattern worth knowing, for example "most remote AI engineer roles want
   TypeScript, which isn't on your resume."
4. Offer two next steps:
   - tailor resumes for the top N (the profile's "resumes to tailor per run"), using
     the **tailor-resume** skill
   - log any of them in the tracker as `saved` leads, using **track-application**

Don't apply to anything on the user's behalf.
