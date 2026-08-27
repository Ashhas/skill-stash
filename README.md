# skill-stash

My personal stash of agent skills — reusable SKILL.md workflows I use daily with Claude Code (and Codex-ready). Public but curated: things go in when I actually use them, not before.

## Skills

| Skill | What it does |
|-------|--------------|
| [prep-commit](skills/prep-commit/SKILL.md) | Detect the project's stack, run its formatters/linters, optionally update CHANGELOG and version, suggest a conventional commit and PR description. |
| [unslop](skills/unslop/SKILL.md) | Cut AI tells from any writing. Always applied. |
| [dependency-updater](skills/dependency-updater/SKILL.md) | Discover, classify (SAFE/RISKY/BLOCKED), and batch-apply dependency updates for Maven and Node projects, with a mandatory migration-guide audit before any risky bump. |

## Install

**Personal (global, all projects):**

```bash
git clone https://github.com/ashhas/skill-stash && cd skill-stash && ./install.sh
```

Symlinks each skill into `~/.claude/skills/`. `git pull` updates them in place. `./install.sh --uninstall` removes the links.

**Per project (via APM, works for Codex/Cursor/Copilot too):**

```yaml
# apm.yml
dependencies:
  apm:
    - ashhas/skill-stash
```

Then `apm install`.

**Always-on skills:** `unslop` is meant to apply to all writing. Its description nudges auto-invocation, but for a guarantee add this line to your global `CLAUDE.md` (or reference it from `AGENTS.md` for Codex):

```
@~/.claude/skills/unslop/SKILL.md
```

## Instructions

`instructions/CLAUDE.md` is a versioned copy of my global Claude Code instructions — reference material, not auto-installed.

## Attribution

- `unslop` is adapted from [pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan (poteto), MIT licensed.
- Skills adapted from elsewhere always carry an attribution line. Nothing here is copied from unlicensed sources.
- Also worth installing, not vendored here: [Google's Android skills](https://github.com/android/skills), [mattpocock/skills](https://github.com/mattpocock/skills).

## License

MIT — see [LICENSE](LICENSE). Adapted portions remain © their original authors under their original MIT terms.
