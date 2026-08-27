---
description: Generic Dart/Flutter coding conventions -- naming, one-widget-per-file, forbidden patterns, imports, comments, nullability, async, typed errors. Package-conditional sections for bloc and go_router.
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

## Widgets

One widget class per file. A file that defines a widget defines that widget only, plus the framework-required pair (`State<T>` for a `StatefulWidget`). Do not accumulate multiple `StatelessWidget` / `StatefulWidget` subclasses in the same file just because they're only used from the top widget. Extract them.

The rule targets a specific smell: a screen or component file that grows a tail of `_HeaderThing`, `_FooterThing`, `_SomeTile` private widget classes at the bottom. The problem isn't the underscore. It's that widgets get buried in files where nothing else in the codebase can find or reuse them.

Where extracted widgets live (adapt folder names to the project's layout):

- Feature-local widgets go in the feature's own `widgets/` folder (e.g. `ui/features/<feature>/widgets/<widget_name>.dart`). Sub-divide with further folders if the feature grows.
- App-wide reusable widgets go in a shared folder grouped by kind (e.g. `ui/common/buttons/`, `cards/`, `inputs/`, `layout/`, `states/`). Add a new category folder rather than dumping into a flat `common/`.

Naming:

- The extracted widget class becomes public, so drop the leading underscore.
- No mandatory scope prefix. The folder path already scopes it. Use a prefix only if it genuinely improves readability at the call site (`HomeHeader` is clearer than a bare `Header` when several screens have a header).

Escape hatch, private composed sub-widgets: keeping `_FooChild` co-located inside a parent widget's file is permitted only when the child is a deliberately encapsulated composition detail. It exists solely to be composed by exactly one parent, extracting it would leak private state or make the parent's contract harder to read, and no other file could sensibly use it. When you use this escape hatch, add a one-line `// Private: <why>` comment above the private widget class stating the specific reason it can't be extracted. Absence of that comment means the widget should have been extracted.

Not covered by this rule (still allowed, never the smell):

- `State<T>` classes paired with a `StatefulWidget`. The framework requires them; they're not a "second widget."
- Private helper methods on a widget class, including `Widget _buildFoo(BuildContext context)` helpers. Methods aren't widget classes.
- Private classes from `package:flutter` or any other package. This rule only governs widgets you author.

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

## Layering

- Feature UI code lives with its feature; data access lives in repositories. State-management classes do not touch the database or HTTP client directly.
- Domain logic (algorithms, coordinators, model classes) lives in `domain/`, free of Flutter imports.

## If the project uses bloc / flutter_bloc

- Bloc events: `<Subject><PastTenseVerb>` (`ScanRequested`, `MeasurementCompleted`)
- Cubit / Bloc state classes: `<Feature>State` with named-constructor sub-states (`ScanOverviewState.loaded`, `ScanOverviewState.error`)
- All state classes are `@immutable` with `Equatable`. Use `copyWith`, never field assignment.
- Blocs/Cubits that listen to streams store the `StreamSubscription` and cancel it in an overridden `close()`.

## If the project uses go_router with shell branches

Back navigation across `StatefulShellBranch`es must use an explicit target, not `Navigator.maybePop()`. A screen reached with `context.go(...)` into a *different* branch has no navigator stack to pop, so `maybePop()` silently does nothing. Give such screens an explicit back handler (`onBack: () => context.go(Routes.home)`). `maybePop()` is only correct for genuinely nested routes within the same branch. This was a shipped bug once; treat it as a hard rule.
