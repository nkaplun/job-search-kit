---
name: tailor-resume
description: Make a one-page tailored version of the user's LaTeX master resume for a specific job posting, by reordering and rewording what's already true, then compile it to PDF and list what the posting wants that the resume can't claim. Use when the user asks to tailor, customize, or adapt their resume for a job, link, or posting, or to tailor resumes for jobs found by find-jobs.
---

# Tailor resume

## Before you start

1. Find `job-search-profile.md` in the current working directory. If it isn't there,
   stop and run the **job-search-setup** skill first.
2. Read the profile: the master resume path (default `resume/master.tex`), the
   one-page rule, the writing style rules, and the list of things that are true about
   the user but not on the master.
3. Read the master resume.
4. Get the posting:
   - a link: fetch it
   - pasted text: use it
   - "the top 5 from my leads": take them from the newest file in `leads/`
   - a link that won't load (login wall): ask the user to paste the description

## The one hard rule

**Never invent anything.** Everything in the tailored resume must come from the master
resume or from the profile's list of true facts. That means:
- no new skills, tools, numbers, titles, dates, or employers
- no inflating a number, a scope ("led" when the master says "contributed to"), or a
  level of experience
- if the posting wants something the user doesn't have, it goes in the gap notes, not on
  the resume

If you think the user probably has a skill the posting wants (it would be odd for their
job not to involve it), ask them. If they say yes, add it to the profile's list of true
facts so you don't have to ask again.

## What you can change

1. **Summary**: rewrite it to lead with what this posting cares about most, using
   the user's real results. Use the posting's words for things the user really did
   (if the posting says "LLM evaluation" and the master says "testing model output",
   use "LLM evaluation").
2. **Technical Knowledge**: reorder rows and items so the posting's must-haves come
   first. Drop items that are irrelevant to this job if it saves space.
3. **Bullets**: reorder bullets within each job so the most relevant come first. Reword
   for emphasis. Cut the least relevant bullets if space is tight. Don't move bullets
   between jobs.
4. **Section order**: leave it alone unless the user asks.

Keep the preamble, macros, and header exactly as they are in the master.

## Files and names

- Short role name: drop words like "Senior" and the team name, then remove spaces.
  "Forward Deployed Engineer, Enterprise" becomes `FDE`; "AI Engineer" becomes
  `AI_Engineer`.
- Write `resume/tailored/<LastName>_<RoleShort>_Resume_<Company>.tex`, using the
  last name from the profile. If that file exists, add `_2`, `_3`, and so on rather
  than overwriting it.

## Compile and check

From `resume/tailored/`, compile with whichever is installed, in this order:
`tectonic <file>.tex`, `latexmk -pdf <file>.tex`, `pdflatex <file>.tex`. If none
are installed, give the user the `.tex` file and tell them to upload it to Overleaf
(https://www.overleaf.com), or offer to install Tectonic (`brew install tectonic` on
macOS).

If it fails to compile, the cause is almost always an unescaped `%`, `$`, `&`, `#`,
or `_` in text you wrote. Fix it and compile again.

Check the page count with `pdfinfo <file>.pdf` (look at `Pages:`). If `pdfinfo`
isn't available:
`python3 -c "import re,sys;print(len(re.findall(rb'/Type\s*/Page[^s]', open(sys.argv[1],'rb').read())))" <file>.pdf`

If it's over one page and the profile says one page: cut the least relevant bullet,
then tighten the summary, then shrink the four spacing numbers near the top of the file.
Compile again and repeat until it fits.

Delete any `.aux`, `.log`, or `.out` files the compile leaves behind (Tectonic
usually leaves none).

## Gap notes

For every posting, note what it asks for that the resume doesn't claim. These are the
things the user will likely be asked about in an interview.

- One posting: put the list in your reply.
- Several postings in one run: write
  `resume/tailored/Gaps_<YYYY-MM-DD>.md` with one table, columns `Company`,
  `Role`, `Left off`, and mention it in your reply.

## Reporting back

For each resume, keep it to a few lines:
- the PDF path
- the 2 or 3 main changes (for example "led the summary with the evaluation work; moved
  the Slack integration bullet to the top")
- the gaps

If `applications/applications.csv` exists and this posting is already tracked, offer to
set its `resume_used` with **track-application**. If it isn't tracked, offer to log it
as a `saved` lead.

## Batches

When tailoring for many postings (for example the top 20 from find-jobs), work through
them one at a time in the same way, compiling and checking each. If subagents are
available it's fine to split the list across a few of them; give each one this whole
skill file, the profile, and the master resume. Check a sample of their output before
reporting.
