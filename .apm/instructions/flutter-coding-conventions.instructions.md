---
description: Generic Dart/Flutter coding conventions -- naming, one-widget-per-file, file/folder layout, modeling, forbidden patterns, imports, comments, nullability, async, typed errors. Package-conditional sections for bloc and go_router.
applyTo: "**/*.dart"
---

# Flutter coding conventions

Generic Dart and Flutter rules for any Flutter project. The last sections are package-specific and only apply when the project uses that package. Project-level instructions override anything here.

## Analyzer

If an analyzer rule fires, fix the code, not the rule. Disabling a lint to make CI green is a code smell; if a rule genuinely doesn't fit the project, record why before turning it off.

## Formatting

- `dart format` is the source of truth. Line length is Dart's default (80 chars).
- Turn on `require_trailing_commas`. Add trailing commas everywhere `dart format` puts them.
- Prefer single quotes for strings unless the string contains a single quote.

## Naming

- Files: `snake_case.dart`
- Classes / enums / typedefs: `UpperCamelCase`
- Members, locals, parameters: `lowerCamelCase`
- Constants: `lowerCamelCase` (Dart convention); `SCREAMING_CASE` only for compile-time env constants (`kApiBaseUrl`)
- Private members: leading underscore (`_privateField`, `_privateMethod`)
- Destructured variables: full descriptive names, never single letters. Applies wherever a pattern binds multiple values of different types: record destructuring (`final (weight, measuredAt) = ...`), if-case patterns, and switch patterns. `final (a, b) = ...` forces the reader to look up which position holds what; the names must carry that information.
- Methods are actions: anything called with parentheses gets a verb name (`computeScore()`, `getReading()`, `resolveConflict()`). Traits that do no work stay getters and may be noun-shaped (`isOnline`, `displayName`). Pick the shortest verb that keeps the action and its meaning: `get` for lookups, `compute` for calculations, never a verb that overclaims (a lookup is `getEntry`, not `computeEntry`).
- Named constructors are exempt from the verb rule: `Report.fromJson(...)` is idiomatic because the class-name position already says "construct".
- Name the concept, never the technology. No implementation infixes: the bloc's event type is `ScanEvent`, not `ScanBlocEvent`.
- No singular/plural type pairs unless one is genuinely the element type of the other. `Setting`/`Settings` promises "a Settings is a collection of Setting"; if that is false, rename one side. Avoid near-anagram pairs (`StageStat` next to `StatStages`) for the same reason: the reader cannot tell them apart at a glance.
- Names must be unambiguous out of context: a folder called `stages/` could hold pipeline stages, animation stages, or stat stages. Name the domain concept it actually holds.
- A literal that encodes a domain rule gets a named constant stating that rule: a `?? 1.0` fallback meaning "unlisted entries count as neutral" becomes `neutralFactor`. Plain mathematical identities (a product starting at 1, a sum at 0) stay literals.

## Widgets

One widget class per file. A file that defines a widget defines that widget only, plus the framework-required pair (`State<T>` for a `StatefulWidget`). Do not accumulate multiple `StatelessWidget` / `StatefulWidget` subclasses in the same file just because they're only used from the top widget. Extract them.

The rule targets a specific smell: a screen or component file that grows a tail of `_HeaderThing`, `_FooterThing`, `_SomeTile` private widget classes at the bottom. The problem isn't the underscore. It's that widgets get buried in files where nothing else in the codebase can find or reuse them.

Where extracted widgets live (adapt folder names to the project's layout):

- Presentation folders mirror the widget composition tree: the screen and its top-level layouts at the feature root, one folder per visual cluster, sub-clusters nested (`checkout/summary/`, `checkout/line_items/`). No flat `widgets/` dump where a screen-level layout sits next to a three-line helper.
- Widgets whose parents live in *different* clusters go to a shared folder (`common/`, grouped further by kind when it grows: `buttons/`, `cards/`). Everything with a single home stays in its cluster.

Naming:

- The extracted widget class becomes public, so drop the leading underscore.
- No mandatory scope prefix. The folder path already scopes it. Use a prefix only if it genuinely improves readability at the call site (`HomeHeader` is clearer than a bare `Header` when several screens have a header).

Escape hatch, private composed sub-widgets: keeping `_FooChild` co-located inside a parent widget's file is permitted only when the child is a deliberately encapsulated composition detail. It exists solely to be composed by exactly one parent, extracting it would leak private state or make the parent's contract harder to read, and no other file could sensibly use it. When you use this escape hatch, add a one-line `// Private: <why>` comment above the private widget class stating the specific reason it can't be extracted. Absence of that comment means the widget should have been extracted.

Not covered by this rule (still allowed, never the smell):

- `State<T>` classes paired with a `StatefulWidget`. The framework requires them; they're not a "second widget."
- Private helper methods on a widget class, including `Widget _buildFoo(BuildContext context)` helpers. Methods aren't widget classes.
- Private classes from `package:flutter` or any other package. This rule only governs widgets you author.

## Files and folders

One concept per file, where a concept is exactly one of:

- a single public class (its private helpers may live alongside it);
- a single enum plus its extensions -- an enum never shares a file with a class;
- a sealed hierarchy: a folder named after the base type holding the library file and one part file per subtype (`scan_event/scan_event.dart` + `scan_started.dart`, `scan_failed.dart`, ...).

Folder layout inside a layer:

- Domain folders first (`orders/`, `scanning/`), and the concept a folder is named after sits at its root, never buried in a subfolder: `orders/order.dart`, not `orders/models/order.dart`.
- Prefer named concept subfolders whenever 2+ files share a concept (`orders/pricing/`, `scanning/calibration/`). `models/` and `enums/` are the fallback for leftovers with no richer shared concept, never the default destination.
- Vocabulary shared by two domains gets its own neutral folder so folder dependencies stay one-way: if `scans/` and `alarms/` both need `Severity`, it lives in neither. A domain never imports a domain that imports it back.

## Forbidden patterns

- **Empty `catch` blocks.** Every caught exception either flows to a user-visible error state, gets logged with context, or is re-thrown with a specific reason.
- **Busy-wait loops.** No `while (true) await Future.delayed(...)`. If you're waiting for a stream event, listen for the event. If you're retrying, use the `retry` package with exponential backoff.
- **Recursive fallback methods** without a depth limit. Explicit state machine or bounded retry only.
- **Hardcoded user-visible strings** in localized apps. Use `.arb` keys via generated `AppLocalizations`. Debug messages (log lines, error contexts) may be inline English.
- **Hardcoded config values** that differ between environments. Route through a config class populated from `--dart-define`.
- **`Future.delayed` in production code as retry mechanism.** Use the `retry` package.
- **`print()` in production code.** Use a proper logger. `debugPrint` is acceptable in Flutter debug-only branches guarded by `kDebugMode`.
- **Direct edits to generated files** (`*.g.dart`, `flutter_gen/`, deployed agent-tool targets like `.claude/`, `.cursor/`).
- **Multiple widget classes per file.** See the Widgets section.

## Imports

- Order: `dart:` → `package:` → `package:<app>/` (project) → relative
- No relative imports across `lib/`; always use `package:<app>/...`
- Single blank line between the groups
- The `directives_ordering` lint enforces this

## Comments

Default to writing no comments. Add one only when the *why* is non-obvious:

- Hidden constraint ("backend hard-caps this at 100; do not increase")
- Subtle invariant ("guarantees `hasData == true` in every emitted state")
- Workaround for a specific bug ("workaround for `flutter_blue_plus` #1234, remove when fixed upstream")

Do not write comments that:

- Restate what the code obviously does
- Reference the current task or PR ("added for TICKET-42")
- Describe callers ("called from `ScanOverviewScreen`")

Never write dartdoc to satisfy a lint (keep `public_member_api_docs` off). Concretely: no constructor echoes (`/// Creates a [Foo].`), no field docs that restate the name and type (`/// The icon to display.`), no narration of the next statement. If a doc would only repeat the signature, write nothing.

Public-API dartdoc (`///`) is welcome where it adds contract the signature can't show: units, ranges, null-meaning, provenance (spec or firmware references). Typically on domain models, repository interfaces, and protocol constants. Skip dartdoc on obvious getters, one-line utilities, and framework overrides.

Comment forms required elsewhere in these conventions are unaffected: `// Private: <why>` on co-located private widgets, `// arrange / act / assert` in tests, and fire-and-forget notes.

## Nullability

- Nullable types (`T?`) are the exception, not the default. Model a field as non-nullable unless you have a concrete reason for it to be missing.
- Use `late final` for fields set once during construction/initialization.
- Prefer `firstOrNull` over `firstWhere((_) => true, orElse: () => null)`.
- Never use `!` (null-force) on a value you didn't just null-check. If the type says "maybe null," treat it as maybe null.

## Async

- `async` functions return `Future<T>`. Never `Future<void>` unless the caller intentionally fires-and-forgets.
- `await` every `Future` you create unless you deliberately fire-and-forget (and note it in a comment).
- Store `StreamSubscription`s somewhere with a lifecycle and cancel them there (a Bloc/Cubit `close()` override, a `State.dispose()`). No dangling subscriptions.

## Errors

- Domain errors are typed. Throw `AppException` subclasses (`TimeoutException`-style names specific to the domain), never bare `Exception('message')`.
- Cross-boundary errors (network, storage) are wrapped into domain exceptions at the repository layer. UI never sees a transport exception (like a `DioException`) directly.
- State-management code catches domain exceptions and emits error states with a machine-readable code plus the localized message key.

## Modeling and code shape

- States that are mutually exclusive share one enum field; states that can coexist get separate fields. If "burned" and "confused" can both be true at once, they cannot live in the same enum.
- Separate state by lifetime. Scope-bound values (per session, per match, per request) live in their own type that gets *replaced* when the scope ends, not in fields on the long-lived entity that a cleanup method must remember to reset. Clearing by construction beats clearing by convention.
- An invariant spanning two values gets exactly one write path: one helper that always writes the pair (a status with its counter, an emitted event with its state transition). Two call sites hand-pairing them is a desync waiting to happen.
- Setup and factory classes never decide their own inputs: the caller generates and passes. `freshGame(teams)` with the caller drawing random teams first, not `freshGame(random)` deciding inside.
- Dispatch over sealed types with an exhaustive `switch`, never `is`-checks plus `as`-casts: a new subtype must fail compilation at every dispatch site instead of throwing at runtime.
- Multi-value returns use records, not sentinels or nullable dances: `({Item item, int? slot})` with a null slot beats returning `-1`.
- A formula lives in exactly one place. A call site that needs a variant extracts a shared helper; it never copies the expression.
- Order methods in a class the way the process runs, so the file reads top-down as its lifecycle, and let an orchestrating method *be* the sequence of named steps rather than narrating phases with comments.

## Layering

- Feature UI code lives with its feature; data access lives in repositories. State-management classes do not touch the database or HTTP client directly.
- State-management classes live beside the UI they drive (`presentation/<feature>/state/`; plain `presentation/state/` in a single-feature app), not in a top-level `bloc/` folder.
- Domain logic (algorithms, coordinators, model classes) lives in `domain/`, free of Flutter imports.

## If the project uses bloc / flutter_bloc

- Bloc events: `<Subject><PastTenseVerb>` (`ScanRequested`, `MeasurementCompleted`)
- Cubit / Bloc state classes: `<Feature>State` with named-constructor sub-states (`ScanOverviewState.loaded`, `ScanOverviewState.error`)
- When `<Feature>State` would collide with a domain type the bloc wraps, the domain type keeps the plain name and the bloc state takes a distinguishing one (`<Feature>ViewState`)
- All state classes are `@immutable` with `Equatable`. Use `copyWith`, never field assignment.
- Blocs/Cubits that listen to streams store the `StreamSubscription` and cancel it in an overridden `close()`.

## If the project uses go_router with shell branches

Back navigation across `StatefulShellBranch`es must use an explicit target, not `Navigator.maybePop()`. A screen reached with `context.go(...)` into a *different* branch has no navigator stack to pop, so `maybePop()` silently does nothing. Give such screens an explicit back handler (`onBack: () => context.go(Routes.home)`). `maybePop()` is only correct for genuinely nested routes within the same branch. This was a shipped bug once; treat it as a hard rule.
