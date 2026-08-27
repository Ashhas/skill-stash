#!/usr/bin/env bash
# Symlink skill-stash skills into the global skill directories.
# Usage: ./install.sh [--uninstall]
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIRS=("$HOME/.claude/skills")
# Add "$HOME/.codex/skills" here when Codex enters the picture.

# Skills that are project-scoped by design — never linked globally.
# Pull these into a project via APM (or copy the folder into <project>/.claude/skills/).
PROJECT_ONLY=("dependency-updater")

uninstall=false
[[ "${1:-}" == "--uninstall" ]] && uninstall=true

for target_dir in "${SKILL_DIRS[@]}"; do
  mkdir -p "$target_dir"
  for skill in "$REPO_DIR"/skills/*/; do
    name="$(basename "$skill")"
    link="$target_dir/$name"
    if ! $uninstall; then
      for p in "${PROJECT_ONLY[@]}"; do
        [[ "$name" == "$p" ]] && { echo "skipped  $name (project-scoped — install via APM per project)"; continue 2; }
      done
    fi
    if $uninstall; then
      if [[ -L "$link" && "$(readlink "$link")" == "$REPO_DIR"* ]]; then
        rm "$link" && echo "removed  $link"
      fi
      continue
    fi
    if [[ -L "$link" ]]; then
      ln -sfn "${skill%/}" "$link" && echo "updated  $link"
    elif [[ -e "$link" ]]; then
      echo "SKIPPED  $link exists and is not a symlink — resolve manually" >&2
    else
      ln -s "${skill%/}" "$link" && echo "linked   $link"
    fi
  done
done
