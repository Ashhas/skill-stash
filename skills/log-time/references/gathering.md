# Gathering evidence

Commands and rules behind the Gather steps of `log-time`. A rule marked *(seen)* comes from a real reconstruction where the plain approach missed hours.

## §1 Sources

| Source | Check | Blind spot when missing |
|---|---|---|
| git + GitHub | the repository scan below, counting the repositories it visits, and `gh auth status` | PRs and reviews; commits still work |
| Jira | a Jira search tool is listed (Claude Code: tool search for `searchJiraIssuesUsingJql`) | titles must come from the user; ticketless afternoons stay dark |
| Calendar | a calendar list tool is listed (Claude Code: tool search for `list_events`) | meetings vanish, ask the user for them |
| Session history | `ls ~/.claude/projects/*/*.jsonl` | daytime evidence falls back to commits and Jira |

A missing calendar costs the most *(seen: a week with no git activity in office hours held six hours of meetings)*.

## §2 Git and GitHub

Every repository, not the current one *(seen: a review in a repo nobody had configured was the only trace of a morning)*. Paths may contain spaces, so read them NUL-separated. Match the author on a name substring, case-insensitive, because git and Jira often carry different email addresses for the same person.

```bash
cd ~/Projects
find . -maxdepth 3 -name .git -not -path "*/node_modules/*" -print0 | sort -z | while IFS= read -r -d '' g; do
  r="${g%/.git}"
  out=$(git -C "$r" log --all --author="<name substring>" -i \
        --since="<from> 00:00" --until="<to> 23:59" --format='%ci %h %s' | sort)
  [ -n "$out" ] && { echo "=== $r"; echo "$out"; }
done
```

Pull requests, one call each across all repositories:

```bash
gh search prs --author=@me      --updated=<from>..<to> --json repository,number,title,updatedAt,state
gh search prs --reviewed-by=@me --updated=<from>..<to> --json repository,number,title,updatedAt
```

Checkouts and rebases the log does not show, in the repositories the scan above found commits in:

```bash
git -C <repo> reflog --date=iso | grep -E "<yyyy-mm-dd>"
```

- Commits with committer dates seconds apart are a rebase. The work happened earlier; the burst marks the restack *(seen: 27 commits between 18:57 and 19:02, 5 of them new)*. Count the new ones by comparing subjects against the previous day.
- `gh` prints UTC. The local offset is in every git commit date (`+0200`); add it.
- `--reviewed-by=@me` means "ever reviewed by me" and `--updated` means "anything happened in range", so a hit can be the user's own PR that a colleague reviewed that day *(seen)*. Check who acted with `gh api repos/<owner>/<repo>/pulls/<n>/reviews`. A colleague's action is not booked.
- A push writes nothing to the local reflog. A branch pushed without new commits shows only in the PR's `updatedAt` and in the session history *(seen: "Push it" at 09:29, PR updated 09:29, no reflog entry)*.

## §3 Jira

Get the account id once from the Atlassian user-info tool. `updatedBy` refuses `currentUser()`:

```
issuekey in updatedBy("<accountId>", "<from>", "<to>") ORDER BY updated ASC
```

`<from>` is inclusive, `<to>` exclusive, both in the user's Jira timezone, so pass the day after the last day. Request only `summary`, `updated`, `created`. Fifty per page; follow `nextPageToken`.

Tickets that moved but were not changed by the user, for context only:

```
assignee = currentUser() AND updated >= "<from>" AND updated < "<to>" AND NOT issuekey in updatedBy("<accountId>", "<from>", "<to>")
```

- Assignment and mentions move `updated`. Such a ticket is not work *(seen: a security ticket a bot created at 09:10 looked like the start of a workday)*.
- Timestamps end in `+0000`. Convert to local time.
- Edits across many tickets within minutes are a batch: a reshuffle, estimates, labels. One item in the output *(seen: 7 tickets moved between sprints in five minutes, 13 stories given an estimate in three)*. Estimates on an epic's stories go on the epic's line; a reshuffle goes under "No ticket".
- A Jira edit inside a confirmed meeting interval follows the commit rule in §6: open question, not a booking.
- Tickets created or changed by someone else are evidence at most, never a line. Fetch `description` for one such ticket only when it may prove attendance at an unanswered meeting; when it does, book the meeting and cite the proof in the open question *(seen: "from the meeting of 24-09 with Joost, Aschwin and Egon")*.

A long summary may lose its tail, nothing else:

| Jira summary | Timesheet title |
|---|---|
| `connect-backend upgraden naar Spring Boot 4` | unchanged |
| `HIGH Security: Amazon Web Services Advanced JDBC Wrapper: Privilege Escalation in Aurora PostgreSQL instance (GHSA-7xw4-g7mm-r4hh)` | `HIGH Security: Amazon Web Services Advanced JDBC Wrapper: Privilege Escalation` |

## §4 Calendar

List the primary calendar for the range with event types `DEFAULT`, `OUT_OF_OFFICE`, `FOCUS_TIME` and `WORKING_LOCATION`. Read start, end, title, type, the user's response status and the organizer.

| Group | Rule |
|---|---|
| Confirmed | `accepted`, or organised by the user with attendees |
| Unconfirmed | `needsAction`, or organised by the user with no attendees and a real title |
| Skipped | `declined` · `WORKING_LOCATION` · `OUT_OF_OFFICE` · all-day entries and timed events from 00:00 to 00:00 · descriptions that say "this is not a meeting" · own focus blocks such as `>>>>>>` |

- Unconfirmed events are open questions; the user decides them, not the response status. The exception is proof elsewhere: a ticket or commit naming the user as present books the meeting, with the proof cited in the question *(seen: an unanswered 13:30 meeting, the resulting epic named the attendees)*.
- A recurring day-off event or a weekly out-of-office sets that day to 0h. An empty day off is not a gap.
- A focus block says what the day was for. It is never hours by itself.
- Working-location events say where the day was spent. An office day with no laptop trail is normal; say so.

A week can exceed the tool's output limit. When the runtime parks the result in a temporary file, read it there with Python and leave it:

```python
import json
d = json.load(open("<saved file>"))
for e in d["events"]:
    s = e["start"].get("dateTime") or e["start"].get("date")
    me = [a for a in e.get("attendees", []) if a.get("self")]
    status = me[0]["responseStatus"] if me else "organizer"
    print(s[:16], e.get("eventType", "DEFAULT"), status, e.get("summary"))
```

## §5 Session history

Claude Code keeps one JSONL transcript per session under `~/.claude/projects/<encoded cwd>/`. Each line carries a `timestamp`; user turns carry the prompt. The folder name says which project the session ran in.

```bash
python3 <skill dir>/scripts/session-activity.py --from <from> --to <to> --prompts 6
```

- A session's span is the working span for that project. A session with 1,700 messages from 09:00 to 19:50 is a full day on that repository even when every commit is after 18:00 *(seen)*.
- The first prompts say what the work was about. Quote them when the commits do not.
- Sessions outside the work folders are personal by default. One open question naming the folder and the span; never the prompts.
- The script drops prompts from the automated review hook, skill injections and pasted screenshots.
- Other runtimes keep transcripts elsewhere or not at all. Mark the source missing.

## §6 Timeline

- Meetings are intervals, sessions and commit runs are spans, Jira edits and PR events are points.
- Every minute counts once. A meeting inside a session takes its minutes; the session keeps the rest *(seen: a 51-minute session over three standups double-counted 0.75h)*.
- A commit or Jira edit inside a meeting interval means a laptop was open or the meeting was skipped. Open question, not a decision; the meeting keeps its minutes until the user says otherwise.
- The residual to the contracted day is the `Open` row. It is never assigned to the largest block or to an internal bucket *(seen: named the gap, the user filled it from memory in one message)*.
