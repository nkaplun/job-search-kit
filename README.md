# Job Search Kit for Claude Code

Three skills that cover the repetitive part of a job search:

| Say this to Claude | What happens |
|---|---|
| "Find me jobs" | Searches the web for open postings that match your filters, checks each one is still live, scores how well it fits your resume, and saves a ranked spreadsheet. |
| "Tailor my resume for <link>" | Makes a one-page version of your resume for that posting by reordering and rewording what's already true, then turns it into a PDF and lists what the posting wants that you can't claim. It never adds experience you don't have. |
| "I applied to <link>" / "Where do things stand?" | Logs the application in a spreadsheet, saves a copy of the posting, and tells you what to follow up on. |

A fourth skill, setup, runs once to get you started.

## What you need

- [Claude Code](https://claude.com/claude-code)
- Python 3 (already on macOS and most Linux machines)
- A LaTeX compiler to make PDFs. Setup offers to install
  [Tectonic](https://tectonic-typesetting.github.io) for you (`brew install tectonic` on a
  Mac). If you'd rather not install anything, you can upload the `.tex` files to
  [Overleaf](https://www.overleaf.com) instead.

## Install

Pick one.

**A. As a plugin (recommended).** In Claude Code, run:

```
/plugin marketplace add nkaplun/job-search-kit
/plugin install job-search-kit@job-search-kit
```

Restart Claude Code afterward.

**B. As plain skills.** Clone this repo and copy the four folders inside `skills/` into
`~/.claude/skills/`:

```
git clone https://github.com/nkaplun/job-search-kit.git
mkdir -p ~/.claude/skills && cp -R job-search-kit/skills/* ~/.claude/skills/
```

## First run

1. Make a folder for your job search, for example `~/job-search`, and start Claude Code
   inside it.
2. Say **"set up my job search"**. Claude will ask for your target roles, locations, and
   level, then ask for your current resume (PDF, Word, or pasted text) and convert it into
   this kit's resume format.
3. Check the PDF it makes. Then say "find me jobs."

Always start Claude Code from your job-search folder. That's how the skills find your
settings.

## Your folder after setup

```
job-search/
  job-search-profile.md   your filters and resume rules (edit any time)
  resume/master.tex       your master resume
  resume/tailored/        one tailored resume per job
  leads/                  each search's results, as a spreadsheet
  applications/           your application tracker
```
