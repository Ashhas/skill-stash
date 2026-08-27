# Lane template — derive a lane for any ecosystem

Use this when a selected module's ecosystem has no pre-written lane file (anything that isn't Maven or Node: Gradle, pip/Poetry/uv, Cargo, Go modules, Flutter/pub, Composer, RubyGems, NuGet, …). Fill in every section below for the ecosystem at hand **before running STEP 1**, and write the result down in your working notes for the run. The pre-written [maven-lane.md](maven-lane.md) and [node-lane.md](node-lane.md) show what a completed lane looks like — match their level of concreteness.

A derived lane is complete when it answers the four questions with **real commands you have verified exist**, not guesses. If you are unsure of a command, check the tool's help output first (`gradle help`, `pip index --help`, `cargo --list`, …).

---

## 1. Discovery — how do I list candidates? (plugs into STEP 1)

Answer all of these:

- **1a. Outdated report:** the read-only command that lists current → available versions. Examples of the shape you are looking for: `./gradlew dependencyUpdates` (versions plugin), `pip list --outdated`, `cargo outdated`, `go list -m -u all`, `flutter pub outdated`, `composer outdated`, `bundle outdated`. **Discovery must be read-only** — it must not mutate the manifest, the lockfile, or the installed packages.
- **1b. Security advisories:** the audit command, if the ecosystem has one (`cargo audit`, `pip-audit`, `osv-scanner`, `govulncheck`, `composer audit`, `bundler-audit`). A vulnerable dependency is a candidate regardless of bump type, tagged with severity.
- **1c. Scope buckets:** how this ecosystem categorises a dependency — the report's Scope column. Examples: Gradle `implementation`/`api`/plugin/version-catalog entry; Python runtime vs dev/extras group; Cargo `dependencies`/`dev-dependencies`/workspace-inherited; pub `dependencies`/`dev_dependencies`. Every candidate gets exactly one bucket.
- **1d. Version-pinning mechanism:** where versions actually live — manifest ranges, a lockfile, a version catalog (`gradle/libs.versions.toml`), a constraints file, a workspace root. You must know which file a bump edits before STEP 4.
- **1e. Pre-release filter:** the ecosystem's pre-release conventions (`-alpha`/`-rc`, `.dev`/`a1`/`b1`, `-beta.N`) and how to exclude them. Never bump a GA dependency to a pre-release.
- **1f. Drift checks:** pairs that must stay in lockstep in this ecosystem (compiler plugin ↔ runtime library, codegen tool ↔ generated output, `@types`-like shadow packages). Any mismatch found during discovery is pre-existing drift and joins the batch automatically.

## 2. Classification — what makes a bump risky here? (plugs into STEP 2 §2.3)

- **2a. Runtime compatibility:** where the module declares its runtime version (Java toolchain, `requires-python`, `rust-version`, `go` directive, Dart SDK constraint) and the check that a new dependency version still supports it. Requires a newer runtime than the module uses → BLOCKED.
- **2b. Coupling matrix:** the ecosystem's framework couplings — groups that must move together. Derive from the project's actual stack (its BOM/platform equivalents, plugin↔runtime pairs, generated-code tools). If unsure about a pairing, default to BLOCKED rather than RISKY.
- **2c. Usage scan:** the grep that finds direct usage of a package in source (import/use/require statements for this language), feeding the shared sparse-notes rule in SKILL.md §2.2.

## 3. Apply — how do I bump? (plugs into STEP 4.2)

- **3a. The bump command or edit** per scope bucket from 1c (edit the manifest, `cargo update -p <crate>`, `go get <mod>@<v>`, update the version catalog entry, …), and how the lockfile gets regenerated. Never hand-edit a lockfile.
- **3b. Coupled groups** move in one operation so they resolve together.
- **3c. Hardening rules:** if the project restricts installs (no lifecycle scripts, frozen/immutable lockfile, vendored deps, offline mirrors), respect that absolutely; a bump that needs an exception is BLOCKED pending the project's own review procedure.
- **3d. Generated code:** never hand-edit generated output; regenerate with the project's own script or revert and mark BLOCKED.

## 4. Verify — what proves the build still works? (plugs into STEP 4.4)

- **4a. Compile/build:** the cheapest command that proves the module still builds.
- **4b. Format/lint:** the project's own checks; if a formatter bump reformats, run the fix command and commit the diff.
- **4c. Tests:** the module's own test command — find it in the project's README, CI config, or standard tooling. Prefer the command CI runs.

---

## Boundaries for every derived lane

- Discovery is read-only; apply is the only sanctioned mutation.
- One commit per module; stage the manifest + lockfile + any audited source fixes together.
- The shared rules in [SKILL.md](../SKILL.md) — classification buckets (§2.1), release-notes-and-migration-guide discipline (§2.2), audit items (§4.3), report format (§2.4), and the PR confirmation gate (STEP 5) — apply unchanged to every derived lane.
