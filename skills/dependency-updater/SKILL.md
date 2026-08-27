---
name: dependency-updater
description: Discover, classify, and batch-apply dependency and plugin updates for any project, whatever the stack. Maven, Gradle, npm/Yarn/pnpm, pip/Poetry, Cargo, Go, Flutter/pub, and others. Use when the user says "update dependencies", "check for updates", "bump versions", or "dependency audit".
---

# Dependency updater

Discover all available dependency and plugin updates for a project's modules, classify them by risk and effort, apply approved updates, verify the build, and prepare a PR. Also fits periodic dependency hygiene and security-advisory checks.

The pipeline is the same for every module: STEP 0 (selection) → 1 (discovery) → 2 (classification) → 3 (confirmation) → 4 (apply) → 5 (PR). Only the lane-specific steps depend on the ecosystem. A **lane** answers four questions for one ecosystem: how to discover candidates, how to classify them, how to apply bumps, and how to verify. Lanes plug into STEPs 1, 2 (§2.3), 4.2, and 4.4:

| Lane | Covers | Where |
|------|--------|-------|
| Maven | Java/Kotlin modules built with Maven: `versions-maven-plugin`, BOMs, `pom.xml` | [references/maven-lane.md](references/maven-lane.md) |
| Gradle | JVM and Android modules: versions plugin, version catalogs, AGP/Kotlin/KSP couplings | [references/gradle-lane.md](references/gradle-lane.md) |
| Node | JavaScript/TypeScript workspaces on npm or Yarn: `package.json` plus the lockfile | [references/node-lane.md](references/node-lane.md) |
| Derived | Any other ecosystem (pip/Poetry/uv, Cargo, Go modules, Flutter/pub, Composer, RubyGems, …) | Fill in [references/lane-template.md](references/lane-template.md) before STEP 1; write the derived lane in your working notes so later steps can point back to it |

## Non-negotiables

These hold at every step:

1. **Lane first.** Read (or derive) the selected lane before STEP 1. Never run a lane from memory. Never mix lanes within one module's run.
2. **Drift always ships.** Pre-existing drift found in discovery is fixed in this batch, whatever scope the user picks.
3. **Audit every RISKY and major bump** (§2.2 gathers the evidence, §4.3 resolves it). Compile and test success are not a substitute: they only prove the named APIs you call still exist, and miss renamed config properties, flipped defaults, and behaviour changes.
4. **Never bump a GA dependency to a pre-release.**
5. **Unsure about an ecosystem coupling → BLOCKED**, not RISKY.
6. **One commit per module.** Never push or open a PR without the user's explicit confirmation (STEP 5).
7. **Lane coupling matrices are examples.** On first use in a repo, verify them against that project's actual stack.

**Report formatting:** wrap library, dependency, plugin, and coordinate names in backticks (`` `Flyway` ``, `` `flyway-database-postgresql` ``, `` `${spotless.version}` ``), in reports and prose alike. Build tools (Maven, Gradle, Yarn) and umbrella categories ("AWS SDK") get none.

---

## STEP 0: Module discovery and selection

Discover the project's modules and ecosystems. Do not assume a layout:

```bash
find . -maxdepth 3 \( -name pom.xml -o -name 'build.gradle*' -o -name package.json -o -name pubspec.yaml -o -name pyproject.toml -o -name requirements.txt -o -name Cargo.toml -o -name go.mod -o -name composer.json -o -name Gemfile \) -not -path '*/target/*' -not -path '*/node_modules/*' -not -path '*/build/*' -not -path '*/.git/*'
```

Map each hit to a lane: `pom.xml` → Maven; `build.gradle*` → Gradle; `package.json` → Node; anything else → derived. Present the discovered modules as a numbered menu with their ecosystem, plus an "All modules" option. Wait for the user's selection, then read or derive the selected lanes (non-negotiable 1).

"All modules": run STEPs 1–2 per module, each in its own lane; present one combined classification report grouped by module; one commit per module in STEP 4 for clean bisectability.

---

## STEP 1: Discovery (lane-specific)

Follow the lane's **STEP 1**. Output, identical for every lane:

- A candidate update list: each entry has current version, available version, and scope.
- Any pre-existing drift found along the way (non-negotiable 2).

---

## STEP 2: Classification

Classify every candidate from STEP 1 as SAFE, RISKY, or BLOCKED.

### 2.1: Classify the bump (all lanes)

| Bump type | Default classification |
|-----------|------------------------|
| Patch (x.y.Z) | SAFE |
| Minor (x.Y.z) | SAFE unless release notes mention breaking changes |
| Major (X.y.z) | RISKY or BLOCKED (continue below) |
| Skips multiple majors (e.g. 1.x → 3.x) | BLOCKED. Never include in a batch. |

Beta → newer beta is RISKY (API may change between betas). Beta → GA is SAFE.

### 2.2: Fetch release notes AND migration guide (all lanes; every RISKY and major bump)

A classification with no evidence is a guess. Fetch both documents where they exist:

- **Release notes / changelog**: what changed. The surface area.
- **Migration guide** (upgrade guide, "breaking changes" page): what to change in your code. Always look for this second document; skipping it is the most common cause of silent post-upgrade bugs.

To find them: search `<library> migration guide <version>` (the word "migration", not "release notes") and check the project's GitHub releases page. For majors the two usually live at separate URLs.

Extract, in this order:

1. **Required runtime version** (Java, Node, Python, Rust, Go, Dart, whatever the lane's runtime is) → cross-check the lane's compatibility rules.
2. **Required parent/BOM or coupled-framework version** → cross-check the lane's coupling rules.
3. **Removed APIs and renamed classes/methods** → grep patterns for §4.3.
4. **Renamed or removed configuration properties** → config-file grep patterns for §4.3.
5. **Behavioural changes** (default-value flips, new validation, changed serialisation) → describe each.
6. **Multi-version jumps** (v6 → v8): read every intermediate major's notes. The jump itself is BLOCKED per §2.1; these notes feed its migration appendix.

Minor bumps with no migration guide: the changelog is enough; still extract items 3 and 4 if mentioned.

**Output per RISKY/major bump, the input to §4.3:**

```
**`<coordinate or package>` A.B.C → X.Y.Z**
- Audit item: <pattern to grep for + what to do if found>
- Audit item: <…>
```

**Sparse or paywalled notes**: decide by usage (run the lane's usage scan):

- **Direct usage** in `src/` → BLOCKED. Record "Notes unavailable, audit cannot be completed without a dedicated spike" and revert the bump if already applied.
- **Transitive only** → RISKY, flagged: "Notes sparse; transitive only. Verified by smoke test and the module's verification suite. No source-level audit possible."

**Every BLOCKED item gets a concrete action list** sourced from the notes. Good: "Replace `@MockBean` with `@MockitoBean` across test classes". Bad: "Major bump, needs review". With sparse notes write "Notes unavailable, needs dedicated spike"; never fabricate actions.

### 2.3: Lane-specific classification rules

Apply the lane's **STEP 2** section: runtime checks, coupling matrices, usage scans, reclassification rules. Non-negotiable 5 applies.

### 2.4: Produce the classification report (all lanes)

One Markdown table per bucket, one-line cells. BLOCKED rows additionally get a "Migration details" appendix below the tables.

**Pre-existing drift** (omit if empty):

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

**Migration details** appendix, one section per BLOCKED row:

```
**`<coordinate or package>` A.B.C → X.Y.Z**
- <concrete action 1>
- <concrete action 2>
```

Rules:

- Cells fit on one line; the migration headline is one short summary, full bullets live in the appendix.
- Every BLOCKED row has an appendix section. If notes were unavailable: headline "Notes unavailable, needs spike" plus one matching bullet.
- **Scope column by lane:** Maven `property` / `inline` / `parent`; Gradle `catalog` / `plugin` / `inline` / `wrapper`; Node `dependency` / `devDependency` / `@types` / `resolution`; derived lanes use the buckets from lane-template step 1c.
- Tag security-relevant rows with their advisory severity in Notes.

### 2.5: Recommended next action

End the report with exactly one bold line:

- `**Recommended next action:** Apply Drifts + SAFE (N changes). Skip RISKY and BLOCKED for now.`
- `**Recommended next action:** Apply Drifts + RISKY (M changes, with care). No SAFE updates this round.`
- `**Recommended next action:** Apply Drifts only. No SAFE or RISKY updates available.`
- `**Recommended next action:** No actionable updates. All available versions are pre-releases or BLOCKED.`

Pick by:

- SAFE non-empty → "Drifts + SAFE".
- SAFE empty, RISKY non-empty → "Drifts + RISKY (with care)".
- Only BLOCKED items, drift present → "Drifts only".
- Only BLOCKED or pre-release items, no drift → "No actionable updates".
- Include RISKY in the recommendation only for 1–2 self-contained items the user could accept in the same PR; for 3+, recommend separate PRs.

The recommendation is your opinionated call; the user can override it in STEP 3.

---

## STEP 3: User confirmation

Present the STEP 2 report. Ask: **"Apply the recommended action, or specify a different scope?"**

- No → exit without changes.
- Yes, or approves a subset → use only those updates.
- Drift goes in regardless (non-negotiable 2).

---

## STEP 4: Apply

### 4.1: Branch (all lanes)

```bash
git checkout <default-branch> && git pull
git checkout -b chore/dependency-updates-<module>-<YYYYMMDD>
```

Use the repo's default branch and its branch-naming convention if it has one; otherwise the pattern above.

### 4.2: Apply version bumps (lane-specific)

Follow the lane's **apply** section.

### 4.3: Resolve audit items (all lanes; mandatory for every RISKY and major bump)

The step most likely to be skipped; don't skip it (non-negotiable 3). Run every audit item from §2.2 as an explicit grep. Exactly three valid outcomes per item:

1. **Not applicable**: zero matches. Record it; move on.
2. **Applicable, fixed**: matches found; apply the change the migration guide calls for; commit it alongside the version bump.
3. **Applicable, blocked**: matches that can't be fixed cheaply. Revert that single bump; reclassify BLOCKED with a concrete migration-work entry.

Record every outcome before §4.4:

```
=== RISKY audit: <package> X → Y ===
- <audit item 1> → 23 matches → FIXED (<what was changed>)
- <audit item 2> → 0 matches → not applicable
- <audit item 3> → 2 matches → FIXED
```

SAFE bumps need no audit; for a minor bump of a directly imported library, a 30-second changelog scan is good hygiene. Patch bumps need nothing.

### 4.4: Verify (lane-specific)

Follow the lane's **verify** section. On failure: isolate the offending bump (revert one at a time if needed), fix if straightforward, otherwise revert that single bump and move it to BLOCKED.

### 4.5: Commit (all lanes)

Stage the lane's manifest files plus any changed sources:

```bash
# Maven lane
git add <module-dir>/pom.xml [<nested-pom>] [<changed-sources>]

# Gradle lane
git add gradle/libs.versions.toml [<build.gradle files>] [gradle/wrapper/] [<changed-sources>]

# Node lane
git add <module-dir>/package.json <module-dir>/<lockfile> [<changed-sources>]

git commit -m "chore(<module>): bump dependencies

- <package>: <old> → <new>
- ..."
```

No bump count in the subject (it rots); the body holds the detail. One commit per module; `<module>` is the module name.

---

## STEP 5: PR

Assemble the PR content, then gate the push. Follow the repo's own PR conventions (template, title format) if it has any.

### 5.1: Assemble and present

Build a What/Why-structured draft:

- **What**: the bump list (`<package>: <old> → <new>`, one line each) and drift fixed (omit if none).
- **Why**: dependency hygiene and/or the triggering advisory; audit items resolved, one bullet per RISKY/major item with its outcome from §4.3.
- **Excluded (needs dedicated work)**: the BLOCKED table from §2.4 verbatim; link a follow-up ticket instead of the long appendix if preferred.

Present the draft. **Do not push and do not create a PR yet.** Ask: **"Push the branch and open this PR? Reply 'push' / 'open the PR' to confirm, or tell me what to change."**

### 5.2: Push and open (only on explicit confirmation)

Only after an unambiguous confirmation, push the branch and create the PR (e.g. `gh pr create`) with the assembled content. If the user wants edits, regenerate and re-present; never publish a draft they haven't seen.

---

## Verification checklist (all lanes)

Run the lane's own checklist too.

- [ ] Selected lane read (or derived) before STEP 1
- [ ] Release notes AND migration guide fetched (§2.2) for every RISKY and major-bump candidate; both URLs attached
- [ ] Audit items list produced (§2.2) for every RISKY and major-bump candidate
- [ ] Every audit item resolved (§4.3): explicitly grepped, outcome recorded as "not applicable" / "FIXED" / "BLOCKED"
- [ ] Every BLOCKED row has a concrete migration appendix, or an honest "needs spike" when notes were unavailable
- [ ] Report ends with a single-line **Recommended next action**
- [ ] PR opened only after explicit confirmation, with the assembled What/Why content
