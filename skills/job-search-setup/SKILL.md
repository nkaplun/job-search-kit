---
name: job-search-setup
description: One-time setup for the job search kit. Creates the job-search folder, the profile with search filters, and a LaTeX master resume converted from the user's existing resume. Use when the user asks to set up their job search, when they first install this kit, or when find-jobs, tailor-resume, or track-application can't find job-search-profile.md.
---

# Job search setup

This kit has three working skills: **find-jobs** (search the web for postings),
**tailor-resume** (make a one-page LaTeX resume for one posting), and
**track-application** (log applications and follow-ups). All three read the same
folder, which this skill creates.

## The job-search folder

```
<job-search folder>/
  job-search-profile.md      search filters, resume rules, facts the user confirmed
  resume/
    master.tex               the master resume every tailored version starts from
    master.pdf
    tailored/                one .tex and .pdf per posting, plus gap notes
  leads/                     results of each find-jobs run (.csv and .json)
  applications/              tracker data: applications.csv, notes/, postings/
```

Files that ship with this skill, in this skill's folder:
- `templates/profile_template.md`: the blank profile
- `templates/resume_template.tex`: the resume format, with placeholder content

## Steps

Do these in order. Ask questions in small batches, not all at once.

### 1. Pick the folder

If the current working directory already has `job-search-profile.md`, setup has been done.
Ask what they want to change instead of starting over.

Otherwise, suggest using the current working directory if it's empty or clearly meant for
the job search. If it's somewhere unrelated (a code project, the home folder), suggest
creating `~/job-search` and tell them to start Claude Code from there in the future, so
the other skills find the profile.

Create the subfolders shown above.

### 2. Fill in the profile

Copy `templates/profile_template.md` to `job-search-profile.md` in the folder. Then ask
for the values, a few at a time:

1. Name, current role, and in one line what they're looking for.
2. Target roles, locations (and whether remote counts), level, any pay floor.
3. Companies or industries to skip or to prefer. "None" is a fine answer.
4. Any writing rules they want followed on their resume.

Fill in sensible defaults for anything they skip, and show them the finished profile.

### 3. Build the master resume

Ask for their current resume. Any format works: a PDF or Word file path, a pasted copy, or
a LinkedIn profile export. If they already have a `.tex` resume in this exact format, copy
it to `resume/master.tex` and skip to step 4.

Otherwise:
1. Read their resume. For a `.docx`, try `textutil -convert txt` (macOS) or `pandoc`;
   if neither works, ask them to paste the text.
2. Copy `templates/resume_template.tex` to `resume/master.tex` and replace every
   placeholder with their real content. Keep the preamble and macros exactly as they are;
   the format is the point.
   - Header: name, city, phone, email, and whichever links they have. Drop any
     link they don't have, along with its `$|$` separator.
   - Summary: 3 or 4 sentences built from their actual strongest results.
   - Technical Knowledge: rename the row labels to fit their field. 4 to 6 rows.
   - Experience: one `\tworow` pair and bullet block per job, most recent first,
     `\entrygap` between jobs. Bullets lead with the result and bold the number.
   - Education, then Certifications & Awards (delete this section if empty).
3. **Never invent anything.** Rewording their bullets into the result-first pattern is
   fine. Adding a number, skill, or claim they didn't give you is not. If a bullet has no
   number and one would help, ask them for it.
4. Escape LaTeX special characters in their text: `%` `$` `&` `#` `_`.

### 4. Compile and check

Find a LaTeX compiler, in this order: `tectonic`, `latexmk`, `pdflatex`.

- **None installed:** offer to install Tectonic (small, downloads its own packages on
  first run). macOS: `brew install tectonic`. Linux and Windows: see
  https://tectonic-typesetting.github.io. If they'd rather not install anything, tell them
  they can upload `master.tex` to https://www.overleaf.com and compile it there, and that
  tailor-resume will hand them `.tex` files to upload the same way.
- Compile from inside `resume/`: `tectonic master.tex` (or `pdflatex master.tex`).
  Tectonic's first run takes a minute while it downloads packages.
- Check the page count with `pdfinfo master.pdf` if available. If it's over one page,
  first shrink the four spacing numbers near the top of the file, then ask the user what
  to cut. Don't cut content on your own.
- Ask them to open `master.pdf` and confirm everything is right. Fix what they flag.

### 5. Finish

Tell them, in a few lines, what they can now say:
- "Find me jobs" runs **find-jobs**.
- "Tailor my resume for <link>" runs **tailor-resume**.
- "I applied to <link>" or "where do things stand?" runs **track-application**.

And remind them to start Claude Code from the job-search folder each time.
