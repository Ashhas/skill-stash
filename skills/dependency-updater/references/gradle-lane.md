# Gradle lane: JVM and Android modules built with Gradle

Lane-specific content for Gradle-built modules, including Android. The shared workflow, classification buckets, audit discipline, and report format live in [SKILL.md](../SKILL.md); this file plugs into its STEPs 1, 2 (§2.3), 4.2, and 4.4.

> **Provenance:** unlike the Maven and Node lanes, which encode rules learned from real project history, this lane is assembled from the ecosystem's published compatibility rules. The rules are stable and well documented, but verify the version matrices against the official pages on each run, and refine this file when a real project teaches you something it missed.

Always use the module's wrapper (`./gradlew`), never a globally installed Gradle. The wrapper version in `gradle/wrapper/gradle-wrapper.properties` is itself a dependency this lane manages.

---

## STEP 1: Discovery

### 1.1: Outdated packages (the primary signal)

Gradle has no built-in outdated report. The standard tool is the versions plugin (`com.github.ben-manes.versions`), whose `dependencyUpdates` task is read-only:

```bash
cd <module-dir>
./gradlew dependencyUpdates -Drevision=release > /tmp/gradle-updates-<module>.log 2>&1
```

If the project doesn't apply the plugin, do not edit its build files for discovery. Inject it with an init script instead:

```bash
cat > /tmp/versions-init.gradle <<'EOG'
initscript {
  repositories { gradlePluginPortal() }
  dependencies { classpath 'com.github.ben-manes:gradle-versions-plugin:0.51.0' }
}
allprojects {
  apply plugin: com.github.benmanes.gradle.versions.VersionsPlugin
}
EOG
./gradlew --init-script /tmp/versions-init.gradle dependencyUpdates -Drevision=release
```

**Pre-release filter:** `-Drevision=release` helps, but Gradle-ecosystem pre-releases still slip through as "release" on some repositories. Drop suggestions matching `-alpha`, `-beta`, `-rc`, `-M[0-9]`, `-dev`, `-eap`, and `-SNAPSHOT`. Never bump a GA dependency to a pre-release. Android artifacts in particular publish long alpha/beta trains; the newest stable is what you want, and the report's "milestone" section is not it.

### 1.2: Where versions live (the sweep)

The report tells you *what* is outdated; you must find *where* each version is declared. Sweep all of these, and give each candidate the matching scope:

| Scope | Location | How to find it |
|-------|----------|----------------|
| `catalog` | `gradle/libs.versions.toml` (`[versions]`, `[libraries]`, `[plugins]`, `[bundles]`) | The modern default. Most bumps are one line in `[versions]`. |
| `plugin` | `plugins { }` blocks in `build.gradle(.kts)` and `settings.gradle(.kts)` `pluginManagement` | Plugin versions may also live in the catalog's `[plugins]`. |
| `inline` | hardcoded string coordinates in any `build.gradle(.kts)`, plus `buildSrc/` and `ext` properties | `grep -rnE '["'\'']([a-zA-Z0-9.-]+):([a-zA-Z0-9.-]+):[0-9]' --include='build.gradle*' --include='*.kts' .` |
| `wrapper` | `gradle/wrapper/gradle-wrapper.properties` | The Gradle version itself. |

### 1.3: Security advisories

Gradle has no first-party audit command. In order of preference:

- If the project uses dependency locking, scan the lockfiles: `osv-scanner --lockfile gradle.lockfile` (and `--lockfile gradle/verification-metadata.xml` where present).
- If the project applies the OWASP `dependency-check` plugin, run its task.
- Otherwise rely on the repo's GitHub Dependabot alerts and note in the report that no local audit ran.

### 1.4: Lockstep drift (Gradle/Android pairs)

Any mismatch found here is **pre-existing drift** and joins the batch automatically:

| Pair | Check | Why |
|------|-------|-----|
| `Kotlin` ↔ `KSP` | The KSP version must start with the exact Kotlin version (e.g. Kotlin `2.0.21` ↔ KSP `2.0.21-1.0.28`) | KSP is compiler-coupled; a prefix mismatch fails the build or, worse, mis-generates |
| `Kotlin` ↔ `kotlinx-serialization` plugin | The serialization plugin version equals the Kotlin version | Compiler plugin |
| `Compose BOM` ↔ individual `androidx.compose.*` versions | Compose artifacts should have no explicit version next to a BOM import | An explicit version silently overrides the BOM |
| `Hilt` Gradle plugin ↔ `Hilt` runtime/compiler artifacts | Same version everywhere | Codegen/runtime ABI |
| Same library in catalog AND inline | Compare the sweep results from §1.2 | The inline one wins or conflicts; note it as drift, consolidate to the catalog |

---

## STEP 2 (§2.3): Lane-specific classification rules

Apply after the shared bump-type rule (SKILL.md §2.1) and alongside the shared release-notes discipline (SKILL.md §2.2).

### 2.a: Runtime and toolchain compatibility

- **Gradle ↔ JDK:** each Gradle version supports a bounded JDK range. Check the module's toolchain block (`jvmToolchain(N)`) or `java.sourceCompatibility` against the Gradle compatibility matrix.
- **AGP ↔ JDK:** AGP 8+ requires JDK 17.
- A bump that requires a newer JDK, Gradle, or `compileSdk` than the module uses → BLOCKED unless that prerequisite bump is in the same batch.

### 2.b: Coupling matrix (the Android core)

These couplings are published, not optional. Verify current bounds against the official pages (AGP release notes carry the AGP ↔ Gradle table; the Kotlin and KSP release pages carry theirs):

| Candidate | Couples to | Rule |
|-----------|-----------|------|
| `AGP` (com.android.tools.build) | Gradle wrapper | Each AGP requires a minimum Gradle. AGP bump without a satisfying wrapper → BLOCKED until the wrapper joins the batch. An AGP **major** is never a routine batch item: mark it BLOCKED and, when Google's official AGP upgrade skill is installed (e.g. `agp-9-upgrade` from [android/skills](https://github.com/android/skills)), name that skill as the migration path in the BLOCKED appendix. It carries the compatibility tables and per-version recipes this lane won't duplicate. |
| `AGP` | Android Studio | Each Studio release supports a bounded AGP range. Bumping AGP above the team's installed Studio breaks everyone's IDE sync. Coordination concern: confirm before batching. |
| `AGP` | `compileSdk` | New `compileSdk` levels need a minimum AGP. Check the release notes. |
| `Kotlin` | `KSP`, serialization plugin, Compose compiler plugin | All are compiler-coupled and move in the same operation as Kotlin. Kotlin 2.0+ uses the `org.jetbrains.kotlin.plugin.compose` plugin at the exact Kotlin version. |
| `Compose BOM` | all `androidx.compose.*` | Bump the BOM, never individual artifacts (§1.4). |
| `Hilt`/`Dagger`, `Room`, `Moshi`, other codegen | `KSP` (or `kapt`) | Codegen libraries publish KSP compatibility; check their release notes when KSP or Kotlin moves. |
| Gradle wrapper major | every plugin | Gradle majors remove deprecated APIs that plugins depend on. RISKY at least; surface deprecations first (§4.4). |

If unsure about a pairing, default to BLOCKED rather than RISKY.

### 2.c: Generic major-bump usage scan

```bash
grep -rn "import <package-prefix>" <module-dir>/src/ --include="*.java" --include="*.kt" -l
```

Feeds the SKILL.md §2.2 audit items list and its sparse-notes rule, same as the other lanes. Config surfaces to grep for Android: `AndroidManifest.xml`, `proguard-rules.pro`/consumer rules, `gradle.properties`.

---

## STEP 4.2: Apply version bumps

- **Catalog:** edit the `[versions]` entry in `gradle/libs.versions.toml`. One line, and every module using the catalog follows.
- **Plugin:** edit the `plugins { }` block or the catalog `[plugins]` entry, wherever §1.2 found it.
- **Inline:** edit the string coordinate. Note it as a candidate for catalog consolidation, but don't refactor in this batch.
- **Wrapper:** `./gradlew wrapper --gradle-version <v>`, then commit the changed `gradle-wrapper.properties`, scripts, and jar together. Never hand-edit or hand-download `gradle-wrapper.jar`.
- **Coupled sets** (Kotlin + KSP + compiler plugins, AGP + wrapper) move in one edit round so a single sync sees them together.
- **Dependency locking:** if the project has `gradle.lockfile`s, regenerate them after the edits: `./gradlew dependencies --write-locks` (or the project's own relock task). Never hand-edit a lockfile.

### Audit grep examples (for SKILL.md §4.3)

```bash
# AGP major: removed/renamed DSL blocks
grep -rn "<removed-dsl-block>" --include='build.gradle*' --include='*.kts' .

# Kotlin major: removed compiler flags
grep -rn "freeCompilerArgs" --include='*.kts' --include='build.gradle*' .

# Library major: renamed APIs in source
grep -rn "<removed-symbol>" <module-dir>/src/ --include="*.kt" --include="*.java"
```

---

## STEP 4.4: Verify compile, lint, tests

```bash
cd <module-dir>
./gradlew assembleDebug        # Android; plain JVM modules: ./gradlew assemble
./gradlew lint                 # Android lint, if configured
./gradlew test                 # unit tests
```

- After a Gradle or AGP bump, also run once with `--warning-mode all` and read the deprecation output; that is tomorrow's breakage.
- `connectedAndroidTest` needs a device or emulator; run it when instrumentation tests exist and CI normally runs them, otherwise say so in the report.
- Prefer whatever command the project's CI runs; check the workflow files when unsure.

---

## Boundaries

- **Never hand-edit `gradle-wrapper.jar` or a lockfile.** Use the wrapper task and `--write-locks`.
- **Don't disable build features to get green.** No turning off the configuration cache, lint, or warnings-as-errors to make a bump pass; a bump that needs that is RISKY audit work or BLOCKED.
- **Don't refactor inline versions into the catalog in this batch.** Note them as drift candidates.
- **AGP moves are team moves.** The Android Studio coupling (§2.b) means an AGP bump lands on every teammate's IDE; confirm before including one.

## Error handling

| Situation | Resolution |
|-----------|------------|
| `dependencyUpdates` task not found | The versions plugin isn't applied; use the init-script injection from §1.1. |
| `Could not resolve` during the report | Repository or proxy issue, not an update signal. Check `repositories { }` and any corporate mirror before classifying anything. |
| AGP bump demands a newer Gradle | Add the wrapper bump to the same batch, or mark the AGP bump BLOCKED. |
| IDE sync breaks after AGP bump | Android Studio is older than the AGP range. Revert, mark BLOCKED, coordinate the Studio upgrade first. |
| Configuration-cache failure after a plugin bump | Re-run with `--no-configuration-cache` to isolate. If the plugin is incompatible, that's a RISKY finding for the report, not a reason to disable the cache permanently. |
| KSP "was compiled with an incompatible version of Kotlin" | The §1.4 lockstep was missed. Move Kotlin and KSP together. |

## Lane checklist

- [ ] Versions plugin report run (§1.1), pre-releases filtered out
- [ ] Full sweep done (§1.2): catalog, plugins, inline strings, buildSrc/ext, wrapper
- [ ] Security scan run or its absence noted (§1.3)
- [ ] Lockstep drift surfaced (§1.4): Kotlin ↔ KSP, Compose BOM overrides, Hilt pair, catalog-vs-inline duplicates
- [ ] AGP ↔ Gradle ↔ Studio ↔ compileSdk matrix checked (§2.b) for every AGP, Gradle, or Kotlin move
- [ ] Coupled sets applied together (§4.2); lockfiles regenerated if the project locks
- [ ] `--warning-mode all` deprecation pass done after any Gradle or AGP bump
