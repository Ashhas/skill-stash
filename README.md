# skill-stash

My personal stash of agent skills. Reusable SKILL.md workflows for Claude Code, and Codex-ready. Public but curated: things go in when I actually use them, not before.

Skills here are applied per project. The projects that want a skill pull it in; nothing assumes a machine-wide install.

## Skills

| Skill | What it does |
|-------|--------------|
| [stash](skills/stash/SKILL.md) | Lists every installed skill-stash skill with a short explanation, read live from the skill files. |
| [prep-commit](skills/prep-commit/SKILL.md) | Detects the project's stack, runs its formatters and linters, optionally updates CHANGELOG and version, then suggests a conventional commit and PR description. |
| [unslop](skills/unslop/SKILL.md) | Cuts AI tells from any writing. Always applied. |
| [skillwright](skills/skillwright/SKILL.md) | Guides writing a new agent skill: naming, the description line, layout, formatting for agent readers, and a pre-publish checklist. |
| [dependency-updater](skills/dependency-updater/SKILL.md) | Discovers, classifies (SAFE/RISKY/BLOCKED), and batch-applies dependency updates for any stack, with a mandatory migration-guide audit before any risky bump. Ships Maven, Gradle, and Node lanes plus a template for deriving other ecosystems. |
| [odoo](skills/odoo/SKILL.md) | Writes Odoo timesheet lines for a day, one per Jira ticket in the fixed `Jira#<ticket>: <title> - <work>` format, with titles fetched from Jira and an hour split estimated from the day's commits and PRs. |

## Install

### Per project (the intended way)

Works for Claude Code, Codex, Cursor, and Copilot. Example:

```yaml
# apm.yml
dependencies:
  apm:
    - ashhas/skill-stash#v0.4.0
```

Run `apm install`. [APM](https://github.com/danielmeppiel/apm) resolves `owner/repo` against github.com directly:

1. Fetches this repo into `apm_modules/`.
2. Records the exact commit in `apm.lock.yaml`.
3. Copies the skills into the directories your tools read.

The directories differ per tool by design; the content is identical:

| Tool | Skills land in |
|------|----------------|
| Claude Code | `.claude/skills/` |
| Codex, Cursor, Copilot | `.agents/skills/` |

Older APM versions only write `.agents/skills/`. If Claude Code doesn't see the skills, run `apm update` first.

No APM? Copy the skill folder into `<project>/.claude/skills/`.

### Global (opt-in)

For when you want every skill on a machine:

```bash
git clone https://github.com/ashhas/skill-stash && cd skill-stash && ./install.sh
```

The script symlinks each skill into `~/.claude/skills/`. `git pull` updates them in place. `./install.sh --uninstall` removes the links.

### Always-on unslop

`unslop` should apply to all writing. Its description nudges auto-invocation; for a guarantee, add an `@` import to your `CLAUDE.md` (global or per-project; `AGENTS.md` for Codex), pointing at wherever the file lives for you:

```
@~/Projects/skill-stash/skills/unslop/SKILL.md   # from a clone
@.claude/skills/unslop/SKILL.md                  # from a project install
```

## Instructions

Convention files meant to be pulled into projects. Unlike skills, these are standing rules that should always be in context when matching code is edited, so they ship as APM instruction primitives instead of SKILL.md workflows.

- `.apm/instructions/flutter-coding-conventions.instructions.md` holds the generic Dart/Flutter rules: naming, one-widget-per-file, forbidden patterns, imports, comments, nullability, async, typed errors. Package-conditional sections cover bloc and go_router.
- `.apm/instructions/flutter-testing-conventions.instructions.md` covers what to test, test naming, arrange/act/assert, mocking with mocktail, and factories. Package-conditional sections cover bloc_test and Drift.
- `instructions/CLAUDE.md` is a versioned copy of my global Claude Code instructions. Reference material, not installed anywhere.

Both instruction files carry `applyTo: "**/*.dart"`, so they load only when Dart files are in play.

The same `apm install` that pulls the skills also places these per tool. For Claude Code they land in `.claude/rules/` with a `paths:` glob, and Claude Code auto-loads a rule whenever an edited file matches it. No `@`-import, no "read this first" link that the agent might skip.

For a throwaway sandbox without APM, an `@`-import from a clone still works (the frontmatter is harmless):

```
@~/Projects/skill-stash/.apm/instructions/flutter-coding-conventions.instructions.md
@~/Projects/skill-stash/.apm/instructions/flutter-testing-conventions.instructions.md
```

Project-level rules always win over these files on conflict.

## License

MIT, see [LICENSE](LICENSE). Adapted material keeps its original authors' MIT terms.
