---
name: dependency-updater
description: Discover, classify, and batch-apply dependency and plugin updates for any project, whatever the stack — Maven, Gradle, npm/Yarn/pnpm, pip/Poetry, Cargo, Go, Flutter/pub, and others. Use when the user says "update dependencies", "check for updates", "bump versions", or "dependency audit".
---

# Dependency Updater

Discover all available dependency and plugin updates for a project's modules, classify them by risk and effort, apply approved updates, verify the build, and prepare a PR.

The workflow is the same for every module — STEP 0 (selection) → 1 (discovery) → 2 (classification) → 3 (confirmation) → 4 (apply) → 5 (PR). The workflow is **stack-agnostic**; only the content of the lane-specific steps depends on the module's ecosystem. A **lane** is the ecosystem-specific answer to four questions: how to discover candidates, how to classify them, how to apply bumps, and how to verify. Two lanes ship pre-written; every other ecosystem gets a derived lane:

- **Maven lane** — Java/Kotlin modules built with Maven. Uses the `versions-maven-plugin`, BOMs, and `pom.xml`. Details: [references/maven-lane.md](references/maven-lane.md)
- **Node lane** — JavaScript/TypeScript workspaces using npm or Yarn. Uses `package.json` + the lockfile. Details: [references/node-lane.md](references/node-lane.md)
- **Any other ecosystem** (Gradle, pip/Poetry/uv, Cargo, Go modules, Flutter/pub, Composer, RubyGems, …) — derive a lane by filling in [references/lane-template.md](references/lane-template.md) for that ecosystem before STEP 1. Write the derived lane down (in your working notes for the run) so every later step can point back to it.

This file holds the shared workflow and the rules that apply to all lanes. The lane files hold the ecosystem-specific content for the lane-specific steps. **After STEP 0, read (or derive) the lane for every selected module before starting STEP 1 — do not run a lane from memory.** Do not mix lanes within a single module's run.

> **Scope:** The lane files carry generic ecosystem rules plus *examples* of coupling matrices. On first use in a repo, verify the couplings against that project's actual stack.

> **Formatting rule:** Always wrap library, dependency, plugin, and Maven coordinate names in backticks — both in reports and in the skill's own prose. Examples: `` `Flyway` ``, `` `Lombok` ``, `` `Vert.x` ``, `` `Spring Boot` ``, `` `flyway-database-postgresql` ``, `` `${spotless.version}` ``. This keeps the reader's eye locked on identifiers vs. surrounding prose. Build tools (Maven, Gradle, Yarn) and umbrella categories ("AWS SDK", "your project") do NOT get backticks — only the specific libraries being managed.

## When to use

- User asks to check/update dependencies (backend or frontend)
- Periodic dependency hygiene
- Security advisory requires checking dependency versions

---

## STEP 0: Module discovery and selection

Discover the project's modules and their ecosystems — do not assume a layout:

```bash
find . -maxdepth 3 \( -name pom.xml -o -name 'build.gradle*' -o -name package.json -o -name pubspec.yaml -o -name pyproject.toml -o -name requirements.txt -o -name Cargo.toml -o -name go.mod -o -name composer.json -o -name Gemfile \) -not -path '*/target/*' -not -path '*/node_modules/*' -not -path '*/build/*' -not -path '*/.git/*'
```

Map each hit to a lane: `pom.xml` → Maven lane; `package.json` → Node lane; anything else → a derived lane for that ecosystem (see the lane list above). Present the discovered modules as a numbered menu with their ecosystem (plus an "All modules" option) and ask the user which to check. Wait for the selection before proceeding. **Read the selected lane's reference file — or derive the lane from [references/lane-template.md](references/lane-template.md) — now**, before STEP 1.

If "All modules" is selected, run STEPs 1–2 for each module independently — each in its own lane — present a combined classification report grouped by module, and produce **one commit per module** in STEP 4 for clean bisectability.

---

## STEP 1: Discovery (lane-specific)

Follow the **STEP 1** section of the selected lane file. The output is the same for both lanes: a candidate update list (each with current version, available version, and scope) plus any **pre-existing drift** found along the way. Drift found in discovery must be fixed in this batch regardless of which updates the user picks.

---

## STEP 2: Classification

Classify every candidate update from STEP 1 as SAFE, RISKY, or BLOCKED.

### 2.1 — Classify the bump (both lanes)

| Bump type | Default classification |
|-----------|------------------------|
| Patch (x.y.Z) | SAFE |
| Minor (x.Y.z) | SAFE unless release notes mention breaking changes |
| Major (X.y.z) | RISKY or BLOCKED (continue below) |
| Skips multiple majors (e.g. 1.x → 3.x) | BLOCKED — never include in a batch |

Beta → newer beta is RISKY (API may change between betas). Beta → GA is SAFE.

### 2.2 — Fetch release notes AND migration guide (both lanes; for RISKY and all majors)

A classification with no evidence is a guess. For every RISKY and major-bump candidate, fetch **both** of these where they exist — they answer different questions:

- **Release notes** (or changelog) — *what changed* in the new version. Tells you the surface area.
- **Migration guide** (or upgrade guide / "breaking changes" page) — *what to change in your code* to adopt the new version. Tells you the work. **Always look for this second document.** A library that publishes a migration guide considers it required reading; skipping it is the most common cause of silent post-upgrade bugs.

Both documents may live at different URLs; many projects publish them together, but for major bumps the migration guide is usually a separate, more detailed page. To find them: search `<library> migration guide <version>` (note: search for "migration", not just "release notes"), and check the project's GitHub releases page for the changelog.

**Extract from each document, in this order:**

1. **Required runtime version** (Java, Node, Python, Rust, Go, Dart — whatever the lane's runtime is) — cross-check with the lane's compatibility rules
2. **Required parent/BOM or coupled-framework version** — cross-check with the lane's coupling rules
3. **Removed APIs and renamed classes/methods** — these become grep patterns for §4.3
4. **Renamed or removed configuration properties** — these become config-file grep patterns for §4.3
5. **Behavioural changes** (default-value flips, new validation, changed serialisation) — describe each
6. **For multi-version jumps** (v6 → v8): read every intermediate major's notes, not just the target

For minor bumps where no migration guide exists, the release notes / changelog is enough — extract the same items 3 and 4 if mentioned.

**Output: an Audit items list per RISKY/major bump.** This is the input to §4.3. Format:

```
**`<coordinate or package>` A.B.C → X.Y.Z**
- Audit item: <pattern to grep for + what to do if found>
- Audit item: <…>
```

If the notes are paywalled or sparse, the classification depends on how the library is used (cross-reference with the lane's usage scan):

- **Direct usage** in the codebase (any import of the package in `src/`) → reclassify as **BLOCKED**. Without a migration guide and with code that calls the API directly, the risk of silent behavioural breakage is too high for a routine batch. Write "Notes unavailable — audit cannot be completed without a dedicated spike" and revert the bump if it was already applied.
- **Transitive only** (no direct imports) → keep as **RISKY** but flag explicitly: "Notes sparse; transitive only — verified by smoke test and the module's verification suite. No source-level audit possible." The verification suite is the safety net here.

**For BLOCKED items, produce a concrete bullet list of migration actions** sourced from the notes. Good: "Replace `@MockBean` with `@MockitoBean` across test classes". Bad: "Major bump, needs review". If the notes are paywalled or sparse, write "Notes unavailable — needs dedicated spike" rather than fabricating actions.

### 2.3 — Lane-specific classification rules

Apply the **STEP 2** section of the selected lane file: runtime/compatibility checks, ecosystem coupling matrices, usage scans, and any lane-specific reclassification rules. If unsure about a coupling, default to BLOCKED rather than RISKY.

### 2.4 — Produce the classification report (both lanes)

Use a Markdown table for every bucket with one-line cells. BLOCKED items get a "Migration details" appendix immediately below the table — each BLOCKED row gets a bolded heading and a normal bullet list there. This keeps the four tables visually consistent for scanning while still surfacing the full action lists.

**Pre-existing drift** (omit section if empty):

```markdown
| # | Drift | Detail | Fix |
|---|-------|--------|-----|
| D1 | <name> | <what's wrong> | <how to fix> |
```

**SAFE:**

```markdown
| Dependency | Current → Available | Scope | Reason | Notes |
|------------|--------------------|-------|--------|-------|
```

**RISKY:**

```markdown
| Dependency | Current → Available | Scope | What needs fixing | Notes |
|------------|--------------------|-------|-------------------|-------|
```

**BLOCKED:**

```markdown
| Dependency | Current → Available | Blocker | Migration headline | Notes |
|------------|--------------------|---------|--------------------|-------|
```

Followed by a "Migration details" subsection, with one section per BLOCKED row:

```
**`<coordinate or package>` A.B.C → X.Y.Z**
- <concrete action 1>
- <concrete action 2>
```

Rules:

- Table cells must fit on one line. The migration headline is one short summary; full bullets live in the appendix.
- Every BLOCKED row in the table must have a corresponding section in the appendix.
- If release notes were unavailable, write "Notes unavailable — needs spike" as the headline and a single matching bullet in the appendix.
- **Scope column by lane:** Maven uses `property` / `inline` / `parent`. Node uses `dependency` / `devDependency` / `@types` / `resolution`. A derived lane uses the scope buckets defined when deriving it (lane-template step 1c). Tag security-relevant rows with their advisory severity in the Notes column.

Pre-existing drift items are included in the batch **automatically** — they are not optional.

### 2.5 — Recommended next action

End the report with a single bold line telling the user what to do. Pick from these patterns:

- `**Recommended next action:** Apply Drifts + SAFE (N changes). Skip RISKY and BLOCKED for now.`
- `**Recommended next action:** Apply Drifts + RISKY (M changes, with care). No SAFE updates this round.`
- `**Recommended next action:** Apply Drifts only — no SAFE or RISKY updates available.`
- `**Recommended next action:** No actionable updates. All available versions are pre-releases or BLOCKED.`

Selection rules:

- SAFE non-empty → "Drifts + SAFE".
- SAFE empty, RISKY non-empty → "Drifts + RISKY (with care)".
- Only BLOCKED items → "Drifts only".
- Include RISKY in the recommendation only if there are 1–2 self-contained items the user could reasonably accept in the same PR. For 3+ RISKY items, recommend leaving them for separate PRs.

The recommendation is your opinionated call. The user can override it in STEP 3.

---

## STEP 3: User confirmation

Present the STEP 2 report. Ask: **"Apply the recommended action, or specify a different scope?"**

- No → exit without changes.
- Yes / approves a subset → use only those updates.
- Pre-existing drifts always go in, regardless of the chosen scope.

---

## STEP 4: Apply

### 4.1 — Branch (both lanes)

```bash
git checkout <default-branch> && git pull
git checkout -b chore/dependency-updates-<module>-<YYYYMMDD>
```

Use the repo's default branch. Keep the project's branch-naming convention if it has one; otherwise use the pattern above.

### 4.2 — Apply version bumps (lane-specific)

Follow the **apply** section of the selected lane file.

### 4.3 — Resolve audit items (both lanes; mandatory for every RISKY and major bump)

This is the step most likely to be skipped. Don't skip it. Compile success does NOT prove a bump is safe — it only proves the *named* APIs you used haven't been removed. Compile success says nothing about renamed config properties, flipped defaults, deprecated-but-still-working APIs, or behaviour changes.

For every RISKY/major bump applied in §4.2, walk through its **Audit items list** from §2.2 and resolve each one. There are exactly three valid outcomes per item:

1. **Not applicable** — grep returns no matches in the codebase. Record this; move on.
2. **Applicable, fixed** — grep finds matches; apply the change the migration guide calls for; commit the fix alongside the version bump.
3. **Applicable, blocked** — grep finds matches that can't be fixed cheaply. Revert that single version bump and reclassify it as BLOCKED with a concrete migration-work entry.

Run each audit item as an explicit grep before claiming the bump is done — the lane files show lane-specific grep surfaces and examples.

**Write down each audit item and its outcome before moving to §4.4.** A typical format:

```
=== RISKY audit: <package> X → Y ===
- <audit item 1> → 23 matches → FIXED (<what was changed>)
- <audit item 2> → 0 matches → not applicable
- <audit item 3> → 2 matches → FIXED
```

If you skip this step, you're shipping a guess. The compile + tests verifications in §4.4 will not catch silent behavioural changes; they exist to catch *additional* breakage, not to substitute for the audit.

**For SAFE bumps** the audit is *not required* — but for any minor bump on a library the codebase imports directly, a 30-second scan of the changelog is good hygiene. Patch bumps need no audit.

### 4.4 — Verify (lane-specific)

Follow the **verify** section of the selected lane file. If anything fails: identify the offending bump (revert one at a time if needed), fix if straightforward, otherwise revert that single bump and move it to BLOCKED.

### 4.5 — Commit (both lanes)

Stage the lane's manifest files plus any changed sources:

```bash
# Maven lane
git add <module-dir>/pom.xml [<nested-pom>] [<changed-sources>]

# Node lane
git add <module-dir>/package.json <module-dir>/<lockfile> [<changed-sources>]

git commit -m "chore(<module>): bump dependencies

- <package>: <old> → <new>
- ..."
```

Do **not** include the bump count in the commit subject — the count rots as fast as the list of bumps itself. Keep the subject stable; the body holds the detail.

For multi-module runs, one commit per module. `<module>` in the scope is the module name.

---

## STEP 5: PR

This step assembles the PR content and gates the push. Follow the repo's own PR conventions (template, title format) if it has any.

### 5.1 — Assemble and present the PR content

Immediately after STEP 4 commits, assemble a What/Why-structured draft:

- **What** — the bump list (`<package>: <old> → <new>`, one line each) and pre-existing drift fixed (omit if none)
- **Why** — dependency hygiene and/or the advisory that triggered the run; audit items resolved (one bullet per RISKY/major item with its outcome, from §4.3)
- **Excluded (needs dedicated work)** — the BLOCKED table from §2.4 verbatim; link a follow-up ticket instead of the long appendix if preferred

Present this draft to the user. **Do not push and do not create a PR yet.** Ask: **"Push the branch and open this PR? Reply 'push' / 'open the PR' to confirm, or tell me what to change."**

### 5.2 — Push and open the PR (only on explicit confirmation)

Only after the user has unambiguously confirmed in 5.1, push the branch and create the PR (e.g. `gh pr create`) with the assembled content. If the user wants edits, regenerate and re-present — never publish a draft they haven't seen.

---

## Verification checklist (both lanes)

The lane files carry their own lane-specific checklists — run those too.

- [ ] The selected lane's reference file was read before STEP 1
- [ ] Release notes AND migration guide fetched (§2.2) for every RISKY and major-bump candidate; both URLs attached
- [ ] Audit items list produced (§2.2) for every RISKY and major-bump candidate
- [ ] Every audit item resolved (§4.3) — explicitly grepped, outcome recorded as "not applicable" / "FIXED" / "BLOCKED"
- [ ] Every BLOCKED row has a concrete migration appendix (or honest "needs spike" if notes unavailable)
- [ ] Report ends with a single-line **Recommended next action**
- [ ] PR opened only after explicit confirmation, with the assembled What/Why content
