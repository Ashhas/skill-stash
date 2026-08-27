# Git commits

Never add a `Co-Authored-By: Claude ...` trailer (or any other AI/assistant attribution) to commit messages. Author commits as me only.

# Git push and remote publication

Never run `git push` (or `gh pr create`, `gh pr merge`, `gh pr review --approve`, or any other command that publishes to a remote) without explicit confirmation in the current turn. A prior turn's authorization to commit does not imply authorization to push. After a commit lands locally, stop and ask before publishing anything.

Confirmation must be unambiguous — "yes", "push it", "open the PR", etc. Treat anything ambiguous as "do not push yet" and ask.

# Pull request descriptions

Always structure PR descriptions using **What / Why** format. This applies to anything PR-description-shaped — GitHub/GitLab PRs, MR descriptions, change summaries, release notes when I ask for one, etc.

- **What** — the concrete changes (behaviour, scope, key version bumps). The reader should be able to skim this and know what's in the diff at a high level. Do **not** enumerate every changed file — the diff already shows that. Only call out specific files, versions, or lines when they really need to be highlighted (e.g. a sensitive config change, a notable version bump, a non-obvious touchpoint). Nested bullets and inline labels (e.g. a "Changes:" sub-block) are fine when they aid scannability, but keep them lean.
- **Why** — the motivation: the problem being solved, the ticket/CVE/incident, the constraint or decision that drove the change. For security fixes, include a realistic **Risk Assessment** (as a labelled paragraph or sub-block within Why) covering actual exposure vs. theoretical CVSS — e.g. "client-side only, cannot reach metadata endpoints".

Optional trailing section:

- **References** — standalone trailing block for links: CVE/advisory URLs, release notes, Jira/Linear tickets, related PRs. Use this whenever there are 2+ links worth citing; for a single link, inlining it in Why is also fine.

Do **not** add a Test plan section unless I explicitly ask for one. Do **not** add a Rationale line — the Why section already covers motivation.

Style notes:

- Keep What before Why. Always.
- Do not use other top-level section layouts (Summary/Context/Notes, Background/Changes, Overview/Details, etc.) unless I ask for them.
- The format does not have to match a prior example to the letter — match the *style*: What/Why first, scannable bullets, Risk Assessment for security work, References as a trailing block.

# Writing style

@~/Projects/skill-stash/skills/unslop/SKILL.md
