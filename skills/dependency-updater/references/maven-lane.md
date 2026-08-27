# Maven lane: Java/Kotlin modules built with Maven

Lane-specific content for Maven-built modules. The shared workflow, classification buckets, audit discipline, and report format live in [SKILL.md](../SKILL.md); this file plugs into its STEPs 1, 2 (§2.3), 4.2, and 4.4.

Determine the Maven command first. Prefer the module's wrapper:

```bash
if [ -f <module-dir>/mvnw ]; then MVN="<module-dir>/mvnw"
elif [ -f ./mvnw ]; then MVN="./mvnw"
else MVN="mvn"
fi
```

---

## STEP 1: Discovery

Run all of §1.1 through §1.5 for each selected module.

### 1.1: Versioned dependencies (BOM-aware)

```bash
cd <module-dir>
$MVN versions:display-dependency-updates -DprocessDependencyManagement=true -DallowSnapshots=false > /tmp/dep-updates.log 2>&1
grep '\->' /tmp/dep-updates.log | grep -v '\-alpha\|\-beta\|\-RC\|\-M[0-9]\|\-SNAPSHOT\|\-cr\.\|\.Beta\|\.Alpha\|\.CR'
```

**Expect hundreds to thousands of lines for any module that imports a BOM.** Most of that is BOM-managed transitive noise, collapsed by the de-duplication rule below. The actionable signal comes from §§1.2 and 1.3.

**De-duplication rule:** if a dependency's version is governed by a BOM (the `Spring Boot` parent, `spring-cloud-aws-dependencies`, the AWS SDK BOM, the `Jackson` BOM, etc.), do NOT list it as an individual update; bump the BOM property instead. Only list a BOM-governed artifact individually if it's been explicitly overridden in this module's `pom.xml`.

**Pre-release filter:** the grep above drops common pre-release suffixes. Manually verify any remaining suggestion is GA. Azure SDKs use `-beta.N`, Spring uses `-M1`/`-RC1`, Jakarta uses `-M1`. Never bump a GA dependency to a pre-release.

**Avoid `-q`** with `versions:*` goals; it suppresses the `->` lines you need.

### 1.2: Property updates

```bash
cd <module-dir>
$MVN versions:display-property-updates -DallowSnapshots=false > /tmp/prop-updates.log 2>&1
grep '\->' /tmp/prop-updates.log | grep -v '\-alpha\|\-beta\|\-RC\|\-M[0-9]\|\-SNAPSHOT\|\-cr\.\|\.Beta\|\.Alpha\|\.CR'
```

Properties map directly to the change you'll make (edit one line). This is the most actionable output of the discovery phase.

### 1.3: Inline-version sweep

`display-property-updates` only finds versions declared via a `<property>`. Hardcoded inline `<version>` tags are invisible to it. A typical Spring Boot module has tens of these (drivers, native libs, plugins inside `<annotationProcessorPaths>`, multi-artifact libraries without a shared property).

```bash
cd <module-dir>
grep -nE '<version>[0-9]' pom.xml | grep -v '\${' | grep -v '<!--'
```

For each inline version, cross-reference `/tmp/dep-updates.log` from §1.1. If there's a `->` line for that artifact, add it to the candidate update list with scope `inline`.

### 1.4: Plugins and parent POM

```bash
cd <module-dir>
$MVN versions:display-plugin-updates 2>&1 | grep '\->' | grep -v '\-alpha\|\-beta\|\-RC\|\-M[0-9]\|\-SNAPSHOT'
$MVN versions:display-parent-updates 2>&1 | grep '\->'
```

Plugin output often shows "current → older" lines for `pluginManagement` *minimum-required* constraints. Those are not upgrades; ignore them.

### 1.5: Sub-modules and lockstep drift

Discover nested Maven modules and run §§1.1–1.3 inside each one:

```bash
find <module-dir> -mindepth 2 -maxdepth 3 -name pom.xml -not -path '*/target/*'
```

If a property exists in both parent and sub-module (e.g. `${lombok.version}`), they must stay in lockstep; flag any divergence. **When bumping a property shared between parent and sub-module, both poms must be updated together.**

While scanning, run the lockstep checks as a discovery action. Any mismatch found here is **pre-existing drift** that must be fixed in this batch regardless of which updates the user picks:

| Library group | Check | Why |
|---------------|-------|-----|
| `Flyway` | `grep -nE 'flyway-(core\|database-postgresql)' pom.xml`; versions must match | `flyway-database-postgresql` loads via SPI; version skew against `flyway-core` causes runtime failures |
| `Lombok` | `grep -nE 'lombok' pom.xml`; the `<dependency>` version must match the `<annotationProcessorPaths>` version | Mismatch causes silent stale generated code |
| `Jackson` | `grep -nE 'jackson-' pom.xml`; when declared inline (no BOM), versions must match | Cross-artifact ABI breaks |
| `Kotlin` | `kotlin-stdlib` and `kotlin-maven-plugin` versions must match (usually via `${kotlin.version}`) | Compiler/runtime ABI |

For shared libraries used across multiple modules in the same repo, bumping one module in isolation creates cross-service version skew. Flag this as a coordination concern, not a hard block.

---

## STEP 2 (§2.3): Lane-specific classification rules

Apply after the shared bump-type rule (SKILL.md §2.1) and alongside the shared release-notes discipline (SKILL.md §2.2).

### 2.a: Java version compatibility

```bash
grep -E '<java.version>|<maven.compiler.source>' <module-dir>/pom.xml
```

If the new version requires a higher Java version than the module uses → BLOCKED.

### 2.b: Ecosystem compatibility matrix

Some dependencies are coupled to the framework parent and cannot be bumped alone. Before classifying a major BOM bump as RISKY, verify compatibility with the current parent. If a parent bump is required and isn't in this batch → BLOCKED.

Examples of framework couplings. Verify against the project's actual stack and extend as needed:

| Dependency | Couples to | Rule |
|------------|-----------|------|
| `spring-cloud-aws-dependencies` | `Spring Boot` parent | 3.x → `Spring Boot` 3.x; 4.x → `Spring Boot` 4.x. Major bump without matching `Spring Boot` major → BLOCKED. |
| `spring-modulith` | `Spring Boot` parent | 1.x → `Spring Boot` 3.x; 2.x → `Spring Boot` 4.x. Same rule. |
| `spring-cloud-*` | `Spring Boot` parent | Release trains pin to specific `Spring Boot` ranges. Check release notes. |

If unsure about a pairing, default to BLOCKED rather than RISKY.

### 2.c: Generic major-bump usage scan

For any major bump, scan source for direct API usage:

```bash
grep -rn "import <package-prefix>" <module-dir>/src/ --include="*.java" --include="*.kt" -l
```

The result feeds into the SKILL.md §2.2 audit items list and its sparse-notes rule:

- **Direct usage** → migration-guide items become §4.3 grep patterns; if notes are sparse → BLOCKED per SKILL.md §2.2
- **Transitive only** → the audit can be lighter (smoke test plus `mvn verify` is the safety net); if notes are sparse → keep as RISKY per SKILL.md §2.2 but flag it

Config-property changes (e.g. `application.yaml`) always need to be grepped, regardless of direct vs transitive usage.

### 2.d: Tightly-coupled ecosystems

Some dependency groups must move together; bumping one in isolation breaks the others:

- **Hadoop / Parquet / Avro**: bump together. `hadoop-aws` must stay compatible with the AWS SDK major used in the same module → RISKY for any version change.

---

## STEP 4.2: Apply version bumps

- **Property:** change the property value.
- **Inline:** change the `<version>` tag.
- **Parent:** change `<parent><version>`.
- **Lombok:** update BOTH `<dependency>` and `<annotationProcessorPaths>`.
- **Sub-modules:** if a property is shared with a nested pom (e.g. `${lombok.version}` shared with a nested `e2e/pom.xml`), update both. When bumping a `Spring Boot` parent or shared BOM, every nested pom that re-declares those versions must follow.

### Audit grep examples (for SKILL.md §4.3)

Example for a `Spring Boot` 3 → 4 bump:

```bash
# Audit item: Replace @MockBean with @MockitoBean
grep -rn "@MockBean\|@SpyBean" <module-dir>/src/ --include="*.java" --include="*.kt"

# Audit item: spring.session.redis.* → spring.session.data.redis.*
grep -rn "spring\.session\.redis\." <module-dir>/src/ <module-dir>/src/*/resources/

# Audit item: @PropertyMapping moved package
grep -rn "import.*\.test\.web\.servlet\.client\.PropertyMapping" <module-dir>/src/
```

---

## STEP 4.4: Verify compile, format, tests

```bash
cd <module-dir>
$MVN compile -DskipTests
$MVN spotless:check    # if spotless was bumped, run spotless:apply and commit the diff
```

Then run the module's own test command: `$MVN verify` when integration tests or TestContainers exist (needs Docker), otherwise `$MVN test`. Check the module's README or CI config when unsure.

---

## Boundaries

- **Legacy and tightly-coupled modules are conservative.** When a module's dependency ecosystem is tightly coupled (e.g. Hadoop/Parquet/Avro with an old AWS SDK), prefer security-only updates.
- **Property-based versions are preferred.** If you find an inline version that could be a property, note it but don't refactor in this batch.

## Error handling

| Situation | Resolution |
|-----------|------------|
| Compile failure after bump | Read the error, check the migration guide. Fix if straightforward; otherwise revert that single bump and mark BLOCKED. |
| Test failure after bump | Identify the offending bump (revert one at a time). Fix if possible; otherwise revert and mark BLOCKED. |
| `versions:*` plugin not available | Use the fully qualified coordinate: `mvn org.codehaus.mojo:versions-maven-plugin:2.18.0:display-dependency-updates` |
| Spotless `check` fails after bump | Run `$MVN spotless:apply`, commit the formatting diff |

## Lane checklist

- [ ] Inline-version sweep run (§1.3): non-property `<version>` tags cross-referenced
- [ ] Sub-module sweep run (§1.5): every nested `pom.xml` processed
- [ ] Lockstep drift surfaced (§1.5): `Flyway`, `Lombok`, `Jackson`, `Kotlin`, plus any other paired artifacts
- [ ] Pre-release versions filtered out and verified GA where suggested
- [ ] BOM-managed transitive deps de-duplicated (bump the BOM, not the individual artifact)
- [ ] Ecosystem compatibility matrix checked (§2.b) for every major BOM bump
- [ ] Sub-module poms synced when shared properties or the parent version changed
