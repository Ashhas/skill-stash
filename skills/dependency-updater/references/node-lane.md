# Node lane — JavaScript/TypeScript workspaces (npm / Yarn)

Lane-specific content for Node workspaces. The shared workflow, classification buckets, audit discipline, and report format live in [SKILL.md](../SKILL.md) — this file plugs into its STEPs 1, 2 (§2.3), 4.2, and 4.4.

Determine the package manager first — it decides the apply commands and the lockfile:

```bash
[ -f yarn.lock ] && echo yarn; [ -f package-lock.json ] && echo npm; [ -f pnpm-lock.yaml ] && echo pnpm
grep '"packageManager"' package.json   # authoritative when present
```

This lane covers npm and Yarn (classic and Berry); pnpm follows the same shape with `pnpm outdated` / `pnpm audit` / `pnpm up`. **If the project hardens its installs** (Yarn Berry `enableScripts: false`, `enableImmutableInstalls: true`, an allowlist policy), respect that hardening absolutely — never loosen it to make an install succeed; a bump that needs a lifecycle script or git dependency is BLOCKED pending the project's own security-review procedure.

There is no BOM in this ecosystem; version constraints live in `package.json` (`dependencies`, `devDependencies`, `resolutions`) and are locked in the lockfile.

---

## STEP 1: Discovery

All discovery here is **read-only** — it must not run an install, mutate the lockfile, or touch `node_modules`. Use `--immutable` (Yarn) or `--no-save` guards if any step could install.

### 1.1 — Outdated packages (the primary signal)

`yarn outdated` is **not** built into Yarn Berry. Use `npm outdated`, which is read-only, queries the registry directly, and produces a clean `Current / Wanted / Latest` table:

```bash
cd <module-dir>
npm outdated || true    # exits non-zero when anything is outdated — that's expected, not an error
```

Read the three columns — they map directly to classification:

- **Current** — installed version (from the lockfile).
- **Wanted** — highest version satisfying the `package.json` range. `Current → Wanted` is an **in-range** bump (a `yarn up` / `npm update` picks it up without editing `package.json`). These are the SAFE candidates.
- **Latest** — newest published. When `Latest > Wanted`, the semver range must be widened in `package.json` — usually a **major** bump. These are the RISKY/BLOCKED candidates.

### 1.2 — Security advisories

```bash
cd <module-dir>
yarn npm audit --all --recursive --json > /tmp/node-audit.json 2>&1   # Yarn Berry
# npm: npm audit --json > /tmp/node-audit.json 2>&1
```

Cover dependencies + devDependencies and walk transitives. Each advisory has a severity, vulnerable range, and dependents. A vulnerable dependency is a candidate **regardless of bump type** — flag it in classification with its severity even when it's only reachable transitively (the fix may be a `resolutions`/`overrides` entry rather than a direct bump).

### 1.3 — Categorise every candidate

Unlike Maven's BOM/property/inline split, Node candidates fall into these buckets — the classification treats each differently, and the bucket is the report's Scope column:

| Category | How to spot it | Notes |
|----------|---------------|-------|
| Runtime dependency | key in `dependencies` | Ships to the browser/server bundle — highest blast radius. |
| Dev/tooling dependency | key in `devDependencies` | Build, lint, test tooling. Lower runtime risk but can break CI. |
| `@types/*` package | `@types/` prefix | Must track its runtime library's major (e.g. `@types/react` major ↔ `react` major). Bumping types ahead of the lib surfaces phantom type errors. |
| `resolutions` / `overrides` entry | key in `resolutions` (Yarn) or `overrides` (npm) | A pin that overrides transitive versions. Bumping the direct dep does nothing if a resolution pins it lower — see §1.4. |

### 1.4 — Framework coupling and resolution drift (Node lockstep)

The JS equivalent of the Maven ecosystem matrix. Bumping one side of a coupled pair without the other breaks the build or types. Examples — verify against the project's actual stack and extend as needed:

| Coupled group | Rule |
|---------------|------|
| `next` ↔ `react` / `react-dom` | Each Next major pins a supported React major. Do not bump `react`/`react-dom` across a major without confirming the `next` version supports it (and vice-versa). Keep `react` and `react-dom` on the **same** version always. |
| `@types/react` ↔ `react`, `@types/node` ↔ Node | Types major must match the runtime major. |
| `eslint` ↔ shareable configs/plugins | An ESLint major (flat-config era) requires plugin majors that support it. Bump the set together. |
| `vitest` ↔ `@vitest/*` / coverage provider | Keep all `vitest` and `@vitest/*` packages on the same minor. |
| `@playwright/test` ↔ a `playwright` `resolutions` pin | If `resolutions.playwright` pins a version, bumping `@playwright/test` alone leaves the browser binaries pinned — bump both together. |
| Code generators (`orval`, `openapi-generator`, `graphql-codegen`) ↔ generated output | Regenerating may change the client surface. Never hand-edit generated directories — regenerate with the project's own script and commit the result as-is. See the STEP 4 guardrail. |

**Resolution drift** — the Node analog of Maven lockstep drift, and included in the batch automatically like any Maven drift. Compare each `resolutions`/`overrides` entry against the same package's `dependencies`/`devDependencies` range:

```bash
cd <module-dir>
node -e "const p=require('./package.json'); const dd={...p.dependencies,...p.devDependencies}; Object.entries(p.resolutions||p.overrides||{}).forEach(([k,v])=>{const decl=dd[k]; if(decl&&decl!==v) console.log('DRIFT '+k+': declared '+decl+' vs resolution '+v)});"
```

Any `DRIFT` line is pre-existing drift — a resolution silently overriding a declared range (e.g. `typescript` declared `^6.x` while a resolution pins `^5.x`). Surface it and fix it in this batch regardless of which updates the user picks.

---

## STEP 2 (§2.3): Lane-specific classification rules

Apply after the shared bump-type rule (SKILL.md §2.1) and alongside the shared release-notes discipline (SKILL.md §2.2).

### 2.a — In-range vs out-of-range (from §1.1)

- `Current → Wanted` (in-range) bump, patch or minor → **SAFE**. It's covered by the existing `package.json` range; `yarn up` / `npm update` adopts it without editing the range.
- `Latest > Wanted` (range must widen), i.e. a **major** → **RISKY or BLOCKED** — continue below. Widening a `^` range across a major is a deliberate change, never routine.

### 2.b — Framework coupling (from §1.4)

For any candidate in a coupled group, the whole group must move together or the bump is BLOCKED until the batch includes the rest:

| Candidate | Rule |
|-----------|------|
| `react` / `react-dom` major | BLOCKED unless the `next` version in the batch supports that React major, and both `react` and `react-dom` move to the same version. |
| `next` major | RISKY — read the Next.js upgrade guide; check for `next.config`, App-Router, and middleware API changes. Confirm the pinned React major is still supported. |
| `@types/*` ahead of its runtime lib major | BLOCKED — bump the runtime lib first (or together). |
| `eslint` major | RISKY — flat-config and plugin-major coupling; bump the plugin/config set together or BLOCKED. |
| `typescript` major | RISKY — new TS majors add stricter checks; a `resolutions` pin (see §1.4) may need updating in lockstep. |
| A `resolutions` pin on a coupled package (e.g. `playwright` pinned while bumping `@playwright/test`) | Bump both together or treat the single-side bump as BLOCKED. |
| Code generator major | RISKY — regenerating output may change the client surface; verify per the STEP 4 guardrail. |

### 2.c — Security advisories (from §1.2)

An advisory raises priority but does not change the bucket by itself:

- Fixable by an in-range bump → **SAFE**, tagged with severity.
- Fixable only by a major or a new `resolutions`/`overrides` entry → classify by the bump rules above (RISKY/BLOCKED), tagged with severity so the user can weigh urgency.
- Transitive-only with no direct-dep fix → propose a `resolutions`/`overrides` entry; classify RISKY (a forced transitive version can break other consumers) and note it needs a clean install + test pass to confirm.

### 2.d — Node audit-item sources (for SKILL.md §2.2)

The shared release-notes discipline applies unchanged: direct usage + no migration guide → BLOCKED; transitive-only → RISKY with a flag. Node-specific grep targets for the audit items: `import` sites in `src/`, `next.config.*`, `eslint.config.*`/`.eslintrc*`, `tsconfig*.json`, `vitest.config.*`, and `playwright.config.*`.

---

## STEP 4.2: Apply version bumps

All commands run from the module directory. Use the project's pinned package manager (`corepack`, `.yarn/releases/`, or the `packageManager` field) when present.

**Immutable-install override (Yarn Berry):** if the project sets `enableImmutableInstalls: true`, any lockfile-mutating command fails by design. Applying updates is the one sanctioned mutation — scope the override to the single command with the env var, never edit `.yarnrc.yml`:

```bash
YARN_ENABLE_IMMUTABLE_INSTALLS=false yarn up <package>@<version>
```

- **In-range (SAFE):** bump within the existing range with `yarn up` (with the override above when applicable) or `npm update <package>`, which updates the lockfile and the `package.json` range as needed.
- **Range widening (major):** edit the `package.json` range to the new `^X.0.0` (or the version the migration guide requires), then relock (`yarn install` with the override, or `npm install`). Do not hand-edit the lockfile.
- **Coupled groups (§1.4 / §2.b):** bump the whole group in one invocation so they resolve together, e.g. `yarn up react@<v> react-dom@<v>` or the full `vitest @vitest/*` set.
- **`@types/*`:** move in the same step as its runtime library, never ahead of it.
- **`resolutions` / `overrides`:** to fix a transitive advisory or correct resolution drift (§1.4), edit the entry in `package.json`, then relock. Keep any pin in lockstep with the declared range unless the pin is deliberately narrower.
- **Respect any supply-chain hardening:** never loosen `.yarnrc.yml` (`enableScripts`, `approvedGitRepositories`, `enableImmutableInstalls`) or equivalent policies to make an install succeed. If a bumped package now needs a lifecycle script or a `github:` source, stop and mark it BLOCKED — the sanctioned escape hatches (per-package `dependenciesMeta.<pkg>.built: true`, or an explicit allowlist entry) require the project's own security review, and most native deps ship prebuilt binaries and don't actually need their postinstall.

After applying, confirm the lockfile is consistent and no unintended installs happened:

```bash
yarn install --immutable   # Yarn: must pass with no lockfile changes
# npm: npm ci --dry-run
```

### 🚫 Generated-code guardrail

If the project has CI- or script-generated code (OpenAPI clients, GraphQL types), **never hand-edit it.** If a codegen-related bump changes generated output, regenerate it with the project's own script and commit the regenerated result as-is. If regeneration produces a diff you can't explain or that breaks types, revert the bump and mark it BLOCKED — do not patch generated files by hand.

### Audit grep examples (for SKILL.md §4.3)

```bash
# API/import renames → source
grep -rn "<removed-symbol>" <module-dir>/src/ --include="*.ts" --include="*.tsx"
# config-key or option changes → config files
grep -rnE "<pattern>" <module-dir>/next.config.* <module-dir>/eslint.config.* <module-dir>/tsconfig*.json <module-dir>/vitest.config.* <module-dir>/playwright.config.*
```

For a Next.js major, run its codemod as an audit aid, then review the diff — do not accept it blind:

```bash
npx @next/codemod@latest upgrade
```

---

## STEP 4.4: Verify typecheck, lint, format, tests

Run the project's own scripts from `package.json` — typically lint, format-check, typecheck, and the unit test suite. Then the heavier suites relevant to what was bumped:

| What was bumped | Also run |
|-----------------|----------|
| Code generator / generated client | The project's regenerate script (see guardrail), then unit tests |
| `vitest` / `@vitest/*` / test utils | The coverage suite |
| `@playwright/test` / `playwright` | The integration/e2e suite (needs the app + browsers) |
| `next` / `react` / build tooling | `build` (a green build is the real proof for a framework bump) |
| MSW / mock tooling | The integration suite |

If reverting one bump at a time to isolate a failure: `git checkout package.json <lockfile>`, then re-apply the rest.

---

## Boundaries

- **Never hand-edit generated directories** — regenerate with the project's own script; never patch generated output.
- **Never loosen supply-chain hardening** to make an install succeed — no re-enabling `enableScripts`, no `approvedGitRepositories` widening, no `enableImmutableInstalls` removal. A bump that needs a lifecycle script or `github:` source is a BLOCKED item; per-package escape hatches require the project's own security review.
- **Never hand-edit the lockfile** — let the package manager maintain it.
- **Do not bump deps in isolation from framework couplings** (§1.4) — React/React-DOM/Next, `@types`↔runtime, the `vitest` set, and any `resolutions` pins on coupled packages all move together.

## Error handling

| Situation | Resolution |
|-----------|------------|
| `npm outdated` errors (no network / private registry) | It queries the configured registry; if that's blocked, fall back to `yarn upgrade-interactive` (TUI) to eyeball candidates, or `yarn npm info <pkg> version` per package. |
| `yarn up` / `yarn install` fails with "lockfile would have been modified" | That's `enableImmutableInstalls: true` doing its job. For a deliberate update, prefix the single command with `YARN_ENABLE_IMMUTABLE_INSTALLS=false` — never edit `.yarnrc.yml`. |
| Typecheck breaks after a `@types/*` or `typescript` bump | Confirm the types major matches the runtime lib major (§1.4). If it's a genuine new strictness check, treat as RISKY audit work, not a routine bump. |
| Regeneration produces an unexplained diff | Revert the codegen-related bump and mark BLOCKED (see guardrail). |
| Formatting check fails after a prettier/eslint bump | Run the project's format-fix / lint-fix script, commit the formatting diff (analogous to `spotless:apply`). |
| A bumped package now demands a lifecycle script or `github:` source | Do NOT loosen the hardening. Mark BLOCKED; the per-package escape hatch needs the project's own security review. |

## Lane checklist

- [ ] `npm outdated` run (§1.1) — Current/Wanted/Latest read; in-range vs range-widening split
- [ ] Audit run (§1.2) — advisories tagged with severity, transitive fixes considered
- [ ] Candidates categorised (§1.3) — dependency / devDependency / `@types` / resolution
- [ ] Framework couplings checked (§1.4 / §2.b) — Next↔React, `@types`↔runtime, `vitest` set, `resolutions` pins on coupled packages
- [ ] Resolution drift surfaced (§1.4) and included in the batch
- [ ] Generated code left untouched or regenerated via the project's own script — never hand-edited
- [ ] Any supply-chain hardening intact — no `enableScripts`/`approvedGitRepositories` loosening
- [ ] Lockfile consistency confirmed after apply (`yarn install --immutable` / `npm ci --dry-run`)
