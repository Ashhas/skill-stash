---
name: prep-commit
description: Run pre-commit preparation for the current project. Detect the stack, run its formatters and linters, fix issues, optionally update the CHANGELOG and version, then suggest a conventional commit message and optional PR description. Use before committing.
---

# Prep commit

## Step 1: Detect project type
Identify the project type by checking for:
- `pubspec.yaml` → Flutter/Dart
- `package.json` → JavaScript/TypeScript (check for framework: React, Vue, Angular, Node)
- `pom.xml` or `build.gradle` → Java/Kotlin
- `requirements.txt` or `pyproject.toml` → Python
- `Cargo.toml` → Rust
- `go.mod` → Go

## Step 2: Run stack-specific tools

**Flutter/Dart:**
- `dart run import_sorter:main`
- `dart format .`
- `flutter analyze` + `dart run custom_lint`

**JavaScript/TypeScript:**
- `npm run lint --fix` or `eslint --fix .`
- `npm run format` or `prettier --write .`

**Java:**
- `./mvnw spotless:apply` or `./gradlew spotlessApply`
- `./mvnw checkstyle:check` or `./gradlew check`

**Python:**
- `isort .` + `black .`
- `ruff check --fix .` or `flake8`

**Rust:**
- `cargo fmt`
- `cargo clippy --fix`

**Go:**
- `gofmt -w .` + `goimports -w .`
- `go vet ./...`

## Step 3: Fix any issues
If analysis tools report errors, fix them.

## Step 4: Ask about CHANGELOG
Ask the user: "Do you want to update the CHANGELOG?"

Options:
- **Yes**: update the changelog with new entries
- **No changes needed**: skip the changelog update entirely

If yes:
- Get the current version from the project's version file
- Find commits since the last changelog entry
- Categorize using conventional commit prefixes:
  - `feat:` → **Added**
  - `fix:` → **Fixed**
  - `chore:`, `refactor:`, `perf:` → **Changed**
  - `docs:` → **Documentation**
- Add entries under the current version

## Step 4b: Ask about version bump (only if CHANGELOG updated)
Ask the user: "Should the version be updated?"

Options:
- **Minor**: bump the minor version (e.g., 1.1.0 → 1.2.0), for new features
- **Patch**: bump the patch version (e.g., 1.1.0 → 1.1.1), for bug fixes
- **No version change**: keep the current version

If Minor or Patch:
- Update the version in `pubspec.yaml` (Flutter) or the equivalent version file
- Update the CHANGELOG header with the new version number and today's date
- Create a new version section and move the new entries there

If no version change:
- Keep entries under the current version

## Step 5: Generate commit message
Based on all staged and unstaged changes, generate a conventional commit.

Title constraints:
- Maximum 72 characters (including type and scope)
- If the description is too long, shorten it while preserving meaning

## Step 6: Show summary
Display:
- Files formatted
- Issues fixed
- Changelog entries added (if applicable)
- The suggested commit message in this format:

```
## Suggested Commit

**Title:** (max 72 chars)
<type>(<scope>): <short description>

**Description:**
- bullet point 1
- bullet point 2
```

Do NOT commit. Just prepare and show the suggested commit.

## Step 7: Ask about PR creation
Ask the user: "Will you open a Pull Request for this change?"

Options:
- **Yes**: generate a PR description
- **No**: skip the PR description

If yes, generate a PR description using this format:

```markdown
## What

<1-2 sentence summary of what changed. Be specific about versions, files, or features affected.>

## Why

<Explain the motivation. Include:>
- <The problem being solved or improvement being made>
- <Why this approach was chosen>
- <Any relevant context (CVEs for security patches, feature requirements, tech debt, etc.)>

<For security patches, include:>
- <Link to CVE/advisory>
- <What makes the current stack vulnerable>
- <Whether this is a breaking change>

**References:** (if applicable)
- <Links to advisories, documentation, or related PRs>

## JIRA Ticket

[TICKET-123](https://your-jira.atlassian.net/browse/TICKET-123)
```

Guidelines for PR descriptions:
- **What**: focus on the change itself, not the files (reviewers can see those)
- **Why**: explain motivation and context; this is the most valuable part
- **Keep it concise**: don't include verification steps or file lists unless they add value
- **Adapt to change type**:
  - Security patches: include CVE links and vulnerability details
  - Features: explain the user value and design decisions
  - Refactors: explain what prompted the refactor and any risks
  - Bug fixes: describe the bug and root cause

Do NOT create the PR. Just show the suggested description.
