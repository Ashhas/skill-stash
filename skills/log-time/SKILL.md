---
name: log-time
description: Reconstruct a day or a week of work from git, GitHub, Jira, the calendar and local session history, and hand back timesheet lines in the fixed format "Jira#<ticket>: <Jira title> - <what you did>" with an hour split per day. Use when the user says "log time", "log-time", "odoo", "uren boeken", "timesheet", "log my hours", "what did I work on last week", or asks what to write in Odoo.
---

# Log time

Reconstruct what the user worked on, then hand back lines they copy into Odoo. The hand-back is the whole job. Nothing gets written anywhere else.

## The commits are not the day

Git alone found 2.5 hours of a 32-hour week. The other 29 were meetings, a planning afternoon spent in Jira, an epic written in a session that produced no commit. So the evidence comes from four places, and a line is not written until all four have been read: git and GitHub, Jira edits made by the user, accepted and unanswered calendar events, and the agent's own session transcripts. Commands, queries and the caveats for each live in `references/gathering.md`. Read it first.

## Rules

- **The line is `Jira#<TICKET>: <Jira summary> - <what you did>`.** No space before `#`, a colon after the ticket, a spaced hyphen before the work. Hours go in the table, never in the line.
- **The title is the Jira summary, verbatim.** Whatever language Jira has it in. No Jira access means asking the user for the title, not guessing it.
- **Never invent.** Work without a ticket goes under "No ticket". Hours without evidence go under "Open". A batch edit across many tickets is one item, not one line per ticket: estimates on an epic's stories go on the epic's line, a sprint reshuffle goes under "No ticket".
- **Show what you skipped.** An unanswered invite, a session in a personal folder, a gap in the day: each is one open question. An unanswered invite is often a meeting that was attended; when a Jira ticket or commit names the user as present, book it and say in the question what proved it.
- **Write nothing.** No bookings, no files, no notes that outlive the run. A tool result the runtime parks in a temporary file is read there and left there.

## Gather

Do these in order and in silence. Nothing prints until the hand-back.

1. **Scope.** Today by default, a named day, or Monday to Friday of last week. Contracted hours per day come from the user; ask when they have not said. Step 5 sets a day to 0h when the calendar shows a recurring day-off or out-of-office event.
2. **Sources.** Check git and `gh`, the Jira tools, the calendar tools and the transcript folder once each. A missing source gets one clause on what will be blind because of it.
3. **Git and GitHub.** Every repository under the projects folder, not the current one. Commits, PRs authored, PRs reviewed. A burst of commits seconds apart is a restack, not work at that hour. The local UTC offset comes from the commits' own timestamps.
4. **Jira.** Issues the user changed in the range, with `updatedBy`, not issues that merely moved. Titles from `summary` only. Timestamps are UTC. Fetch `description` for one ticket only when it may prove attendance at an unanswered meeting.
5. **Calendar.** Three groups: confirmed, unconfirmed, skipped. Confirmed events are hours. Unconfirmed ones are open questions, unless other evidence proves attendance.
6. **Sessions.** `scripts/session-activity.py --from <date> --to <date>` prints per day which folder the agent worked in, when, and the first prompts. This is the best daytime evidence. Sessions outside the work folders are personal until the user says otherwise; never quote their prompts.
7. **Timeline.** Lay each day out in clock order in working memory, never in the chat. Meetings are intervals, sessions are spans, commits and Jira edits are points. A point inside a meeting interval is an open question, not a booking. This decides the hours and the open questions.

## What to hand back

One block: the scope line and the sources table, then per day the lines, the hour table and the open questions. No timeline, no per-step report, no narration, and no justification of the `Open` row beyond the questions.

```
Scope  Mon 21 Sep to Fri 25 Sep 2026 · 8h per day · Fri is a day off (calendar)

Sources
  git + GitHub      ok        48 repos under ~/Projects · gh authenticated
  Jira              ok        kabisa.atlassian.net
  Calendar          ok        primary calendar
  Session history   ok        ~/.claude/projects

Tue 22 Sep

Jira#MAHT-383: connect-backend upgraden naar Spring Boot 4 - worked through review comments on the PR stack, restacked onto main
Jira#MAHT-368: Controleer en valideer architectuurdiagram Hertek Connect - generated the current diagram, attached it and closed the ticket

No ticket
- Hertek Maintenance Sync 09:30-10:00
- Q4 planning with Joost and Sjoerd, MAHT backlog relabelled Q3 to Q4

| Item                          | Hours |
|-------------------------------|-------|
| MAHT-383                      | 2.25  |
| MAHT-368                      | 1.25  |
| Hertek Maintenance Sync       | 0.5   |
| Q4 planning (no ticket)       | 4.0   |
| Open                          | 0.0   |

Open questions
- Standup Gregg app 08:30 was never answered. Attended?
```

- **The work description** is one clause, past tense, in the language of the user's request, naming the outcome. Not "worked on the upgrade" but "restacked onto main, resolved the review threads". A bare rebase is not booked.
- **A long title** may lose its tail. Only when it runs past about 80 characters or ends in an advisory id or a parenthesised note, and only by dropping the tail. The reference has the example.
- **Hours** follow the clock. A meeting is its interval. A session is its span minus the meetings inside it, split over the tickets it touched, rounded to the quarter hour. Every minute counts once. What is left to the contracted day is the `Open` row.
- **Open questions** are one line each and ask one thing. A gap gets "09:45 to 13:30 has no trail. What was it?", not a list of what others did in that gap. The user answers them; the reply to that is a reprint of the changed days in the same shape, and that reprint ends the skill.

**Reply:** the block above, nothing before it and nothing after it.
