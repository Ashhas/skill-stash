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

## Install

Per project, the intended way. Works for Claude Code, Codex, Cursor, and Copilot. Example:

```yaml
# apm.yml
dependencies:
  apm:
    - ashhas/skill-stash#v0.2.0
```

Then `apm install`. [APM](https://github.com/danielmeppiel/apm) resolves `owner/repo` against github.com directly: it fetches this repo into `apm_modules/`, records the exact commit in `apm.lock.yaml`, and copies the skills into the directories your tools read. Those directories differ per tool by design; the content is identical. Current APM writes `.claude/skills/` for Claude Code and `.agents/skills/` for Codex, Cursor, and Copilot (older APM versions only write `.agents/skills/`; upgrade with `apm update` if Claude Code doesn't see the skills).

No APM? Copy the skill folder into `<project>/.claude/skills/`.

Global install is opt-in, for when you want every skill on a machine:

```bash
git clone https://github.com/ashhas/skill-stash && cd skill-stash && ./install.sh
```

This symlinks each skill into `~/.claude/skills/`. `git pull` updates them in place, and `./install.sh --uninstall` removes the links.

`unslop` is meant to apply to all writing. Its description nudges auto-invocation, but for a guarantee add an `@` import to your `CLAUDE.md` (global or per-project; use `AGENTS.md` for Codex), pointing at wherever the file lives for you:

```
@~/Projects/skill-stash/skills/unslop/SKILL.md   # from a clone
@.claude/skills/unslop/SKILL.md                  # from a project install
```

## Instructions

`instructions/CLAUDE.md` is a versioned copy of my global Claude Code instructions. Reference material, not auto-installed.

## License

MIT, see [LICENSE](LICENSE). Adapted material keeps its original authors' MIT terms.
