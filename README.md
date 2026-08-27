# skill-stash

My personal stash of agent skills — reusable SKILL.md workflows for Claude Code (and Codex-ready). Public but curated: things go in when I actually use them, not before.

Skills here are applied **per project**: the projects that want a skill pull it in; nothing assumes a machine-wide install.

## Skills

| Skill | What it does |
|-------|--------------|
| [stash](skills/stash/SKILL.md) | Show what's in the stash — lists every installed skill-stash skill with a short explanation, read live from the skill files. |
| [prep-commit](skills/prep-commit/SKILL.md) | Detect the project's stack, run its formatters/linters, optionally update CHANGELOG and version, suggest a conventional commit and PR description. |
| [unslop](skills/unslop/SKILL.md) | Cut AI tells from any writing. Always applied. |
| [dependency-updater](skills/dependency-updater/SKILL.md) | Discover, classify (SAFE/RISKY/BLOCKED), and batch-apply dependency updates for any stack — pre-written lanes for Maven and Node, a lane template for everything else — with a mandatory migration-guide audit before any risky bump. |

## Install

**Per project (the intended way — via APM, works for Claude Code, Codex, Cursor, and Copilot):**

```yaml
# apm.yml
dependencies:
  apm:
    - ashhas/skill-stash
```

Then `apm install`. No APM? Copy the skill folder into `<project>/.claude/skills/` instead.

**Global (opt-in, if you want every skill on a machine):**

```bash
git clone https://github.com/ashhas/skill-stash && cd skill-stash && ./install.sh
```

Symlinks each skill into `~/.claude/skills/`. `git pull` updates them in place. `./install.sh --uninstall` removes the links.

**Always-on skills:** `unslop` is meant to apply to all writing. Its description nudges auto-invocation, but for a guarantee add an `@`-import to your `CLAUDE.md` (global or per-project; reference it from `AGENTS.md` for Codex), pointing at wherever the file lives for you:

```
@~/Projects/skill-stash/skills/unslop/SKILL.md   # from a clone
@.claude/skills/unslop/SKILL.md                  # from a project install
```

## Instructions

`instructions/CLAUDE.md` is a versioned copy of my global Claude Code instructions — reference material, not auto-installed.

## Attribution

- `unslop` is adapted from [pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan (poteto), MIT licensed.
- Skills adapted from elsewhere always carry an attribution line. Nothing here is copied from unlicensed sources.
- Also worth installing, not vendored here: [Google's Android skills](https://github.com/android/skills), [mattpocock/skills](https://github.com/mattpocock/skills).

## License

MIT — see [LICENSE](LICENSE). Adapted portions remain © their original authors under their original MIT terms.
