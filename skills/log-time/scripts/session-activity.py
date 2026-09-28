#!/usr/bin/env python3
"""Per day: which project folders the local agent worked in, when, and on what.

Reads Claude Code transcripts (~/.claude/projects/<encoded cwd>/*.jsonl). Prints one
block per day with the project folder, first and last timestamp, message count and
the first user prompts. Timestamps are converted to local time.

Usage:
  session-activity.py --from 2026-09-21 --to 2026-09-25 [--prompts 6] [--root ~/.claude/projects]
"""
import argparse
import datetime as dt
import glob
import json
import os
from collections import defaultdict

DROP_PREFIXES = (
    "Review this change for security vulnerabilities",  # automated review hook
    "Base directory for this skill",                     # skill injection, not a prompt
    "[Image",                                            # pasted screenshot placeholder
    "<",                                                 # system reminders and tool results
)


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--from", dest="start", required=True, help="first day, YYYY-MM-DD")
    p.add_argument("--to", dest="end", required=True, help="last day, YYYY-MM-DD (inclusive)")
    p.add_argument("--prompts", type=int, default=6, help="user prompts to show per session")
    p.add_argument("--root", default=os.path.expanduser("~/.claude/projects"))
    return p.parse_args()


def local(ts):
    return dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().replace(tzinfo=None)


def prompt_text(msg):
    content = msg.get("content")
    if isinstance(content, list):
        content = " ".join(x.get("text", "") for x in content if isinstance(x, dict) and x.get("type") == "text")
    if not isinstance(content, str):
        return None
    text = content.strip().replace("\n", " ")
    if not text or text.startswith(DROP_PREFIXES):
        return None
    return text


def main():
    args = parse_args()
    lo = dt.datetime.fromisoformat(args.start)
    hi = dt.datetime.fromisoformat(args.end) + dt.timedelta(days=1)
    home_prefix = os.path.expanduser("~").replace("/", "-")

    # day -> project -> list of sessions {first, last, count, prompts}
    days = defaultdict(lambda: defaultdict(list))
    for path in glob.glob(os.path.join(args.root, "*", "*.jsonl")):
        if dt.datetime.fromtimestamp(os.path.getmtime(path)) < lo - dt.timedelta(days=1):
            continue
        project = os.path.basename(os.path.dirname(path)).replace(home_prefix, "~")
        per_day = defaultdict(lambda: {"first": None, "last": None, "count": 0, "prompts": []})
        with open(path, errors="ignore") as fh:
            for line in fh:
                if '"timestamp"' not in line:
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                ts = obj.get("timestamp")
                if not ts:
                    continue
                t = local(ts)
                if not (lo <= t < hi):
                    continue
                day = per_day[t.date()]
                day["count"] += 1
                day["first"] = min(day["first"] or t, t)
                day["last"] = max(day["last"] or t, t)
                if obj.get("type") == "user":
                    text = prompt_text(obj.get("message", {}))
                    if text:
                        day["prompts"].append((t, text))
        for date, s in per_day.items():
            if s["prompts"]:
                days[date][project].append(s)

    for date in sorted(days):
        print(f"## {date:%a %d %b}")
        rows = []
        for project, sessions in days[date].items():
            for s in sessions:
                rows.append((s["first"], s["last"], s["count"], project, s["prompts"]))
        for first, last, count, project, prompts in sorted(rows):
            print(f"   {first:%H:%M}-{last:%H:%M}  {count:5} msgs  {project}")
            for t, text in prompts[: args.prompts]:
                print(f"      {t:%H:%M} {text[:150]}")
        print()


if __name__ == "__main__":
    main()
