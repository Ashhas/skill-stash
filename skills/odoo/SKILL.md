---
name: odoo
description: Write Odoo timesheet lines for a day of work, one per Jira ticket, in the fixed format "Jira#<ticket>: <Jira title> - <what you did>", with an hour split estimated from the day's commits and PRs. Use when the user says "odoo", "uren boeken", "timesheet", "log my hours", or asks what to write in Odoo.
---

# Odoo timesheet lines

Collect the day's tickets, fetch each Jira title verbatim, describe the work in one clause, estimate hours from timestamps, print the lines.

## Non-negotiables

1. **The line format is exact:** `Jira#<TICKET>: <Jira summary> - <what you did>`. No space between `Jira` and `#`. A colon after the ticket, a spaced hyphen before the work.
2. **The title is the Jira summary, copied verbatim**, in whatever language Jira has it. Never translate it and never guess it. If no Jira access is available, ask the user for the title. One exception: a very long summary may be shortened, see step 2.
3. **Hours are booked separately in Odoo.** They never go in the line. Present the split next to the lines, as a suggestion.
4. **One line per ticket per day.** Two pieces of work on the same ticket merge into one line.

## Step 1: Find the day's tickets

Default to today. Take the date from the user when they name one.

```bash
git log --all --author="$(git config user.name)" --since="<date> 00:00" --until="<date> 23:59" --format='%ci %h %s'
gh pr list --author @me --state all --limit 30 --json number,title,createdAt,headRefName
```

Ticket ids come from commit subjects (`[MAHT-383]`), branch names (`feature/MAHT-383-...`) and PR titles. Add tickets the user worked on without commits (reviews, analysis, meetings) from the conversation or by asking.

Work with no ticket, such as a `chore/dependency-updates-*` branch, gets no invented ticket. Ask which ticket the user books it on and hold the line until they answer.

## Step 2: Fetch the titles

Use the Jira integration available in the session (an Atlassian tool, `acli`, or the REST API) and read only the `summary` field. Kabisa tickets (`MAHT`, `KSHT`, `HSHCD`, ...) live on `kabisa.atlassian.net`; try that site first, then list accessible sites.

Keep the summary as it is. Only when it is very long, roughly more than 80 characters or with a trailing advisory id or parenthesised note, may it be cut down. Keep the words Jira uses, drop the tail, never reword what stays. There is no fixed length rule; when in doubt, keep it whole.

| Jira summary | Timesheet title |
|---|---|
| `connect-backend upgraden naar Spring Boot 4` | unchanged |
| `HIGH Security: Amazon Web Services Advanced JDBC Wrapper: Privilege Escalation in Aurora PostgreSQL instance (GHSA-7xw4-g7mm-r4hh)` | `HIGH Security: Amazon Web Services Advanced JDBC Wrapper: Privilege Escalation` |

## Step 3: Describe the work

One clause per ticket, past tense, in the user's language (Dutch unless they write English), naming outcomes rather than activity: "Redis-factory-regressie gefixt, branch gesplitst in zes gestapelde PRs", not "gewerkt aan de upgrade". Drop trivia the user would not book, such as a bare rebase, unless they ask for it.

## Step 4: Estimate the hours

Spread the span between the first and last timestamp of the day over the tickets in proportion to their commits and PR activity, rounded to the half hour. Say when the start of the day is not visible in git, so the user knows the total is a floor.

## Step 5: Print

```
Jira#MAHT-383: connect-backend upgraden naar Spring Boot 4 - stack gereviewd, Redis-factory-regressie gefixt, branch gesplitst in zes gestapelde PRs
Jira#KSHT-761: Update Android Target API Level naar 36 (Deadline: 31 aug 2026) - cordova-android 15 upgrade afgerond en PR gerebased
```

Follow the block with the hour split as a short table (ticket, hours) and one line per open question (a ticketless piece of work, a title that could not be fetched).

## Verification

- [ ] Every line starts with `Jira#` and has `: ` after the ticket and ` - ` before the work
- [ ] Every title was fetched from Jira, not written from memory; a shortened one only drops a tail of a very long summary
- [ ] No hours inside a line
- [ ] No line for work the user would not book; no invented ticket for ticketless work
- [ ] Hour split adds up to the visible span and is marked as an estimate
