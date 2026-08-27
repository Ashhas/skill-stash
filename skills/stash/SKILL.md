---
name: stash
description: Show what's in the skill-stash — list every installed skill-stash skill with a short explanation of each. Use when the user asks what skills are available, what skill-stash contains, or invokes /stash.
---

# Stash

List the skill-stash skills available in the current setup, with a one-line explanation of each. Always read the actual skill files — never answer from memory, the stash changes.

## Steps

1. **Locate the stash.** Find the directory this skill lives in and treat its parent as the skills root. Depending on how skill-stash was installed, that is one of:
   - `<project>/.claude/skills/` or `<project>/.agents/skills/` (per-project install)
   - `~/.claude/skills/` (global symlinks)
   - `<clone>/skills/` (reading straight from a clone)

2. **Enumerate the skills.** List every sibling directory containing a `SKILL.md`. When the install location mixes skill-stash skills with unrelated ones (a global or project dir with other skills), include only the skill-stash ones — they resolve (via symlink) or trace back to the skill-stash repo; when in doubt, check for the repo's attribution or read the clone's `skills/` directory directly.

3. **Read each frontmatter.** Take `name` and `description` from each `SKILL.md`. Do not read the full bodies — the frontmatter is the summary.

4. **Present the list** as a table:

   | Skill | What it does |
   |-------|--------------|
   | `<name>` | <description, trimmed of trigger phrasing — keep the part that says what it does> |

   After the table, add one line noting where the skills were found (the path from step 1) and, if any skill directory had no readable `SKILL.md`, name it as broken rather than omitting it silently.
