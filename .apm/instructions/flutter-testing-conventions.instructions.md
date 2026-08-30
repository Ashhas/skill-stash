---
description: Generic Flutter testing conventions -- what to test, test naming, arrange/act/assert, mocking with mocktail, factories. Package-conditional sections for bloc_test and Drift.
applyTo: "**/*.dart"
---

# Flutter testing conventions

Generic testing rules for any Flutter project. The last sections are package-specific and only apply when the project uses that package. Project-level instructions override anything here.

## What to test

- **Every new or changed public API** needs a test.
- **Every bug fix** ships with a regression test written *before* the fix and watched failing on the old code -- then the fix makes it pass. A test that never failed proves nothing.
- **Every domain algorithm** (score calculations, parsers, merge logic) has a unit test with edge cases at boundaries.
- **Every repository** has a test against a mocked data source, verifying the interface contract.
- **When code reproduces a specific numeric behaviour from a legacy system or spec** (rounding mode, bucket boundary, exclusion rule), pin it with a boundary test at the exact tie/edge value. A spec that says "rounded to 1 decimal" is ambiguous (banker's vs away-from-zero); the test locks the decision, e.g. assert `7.25 → 7.2` for round-half-to-even.

Do not test framework internals. Do not test that `flutter_bloc` emits states; trust the framework. Test your own logic.

## Structure

`test/` mirrors `lib/`, folder for folder, concept subfolders included: a
test file lives at the same relative path as the code it covers
(`lib/orders/pricing/price_calculator.dart` →
`test/orders/pricing/price_calculator_test.dart`). Shared helpers,
factories, and fixtures live in `test/support/`. Do not sort tests into
kind layers (`unit/`, `bloc/`, `widget/`); the mirrored path already says
what a test is, and it keeps every file findable from its subject.

## Naming

Test names describe **what is being asserted**, not how. Use `<verbActingOnSubject>WhenCondition` shape:

- ✅ `emitsErrorWhenScanTimesOut`
- ✅ `computesScoreOfTenWhenMaxResultantBelowFifteen`
- ✅ `excludesDevicesWithScoreZeroFromAggregate`
- ❌ `testScoreCalculation`
- ❌ `testScanFlow`

## Structure per test

Arrange / act / assert, in that order, with a blank line between sections. No mysterious setup in the wrong section.

```dart
test('computesTotalWhenCartHasMultipleItems', () {
  // arrange
  final cart = Cart(items: [
    Item(price: 250),
    Item(price: 175),
  ]);

  // act
  final total = cart.total;

  // assert
  expect(total, 425);
});
```

## Mocking

Prefer `mocktail` over `mockito`. It needs no code generation and sets up cleaner in test files.

- **Mock direct collaborators only.** If the class under test depends on a `ScanRepository`, mock the repository. Do not mock the database, HTTP client, or platform plugins underneath it.
- **Never mock the thing under test.** If you're tempted to, the design is wrong.
- **Prefer fakes over mocks for stateful collaborators.** A `FakeScanRepository` that stores in a `Map` is often clearer than a `when(...).thenAnswer(...)` chain.

## Test data

- Model factories live in `test/support/factories/`. One factory per domain type. Deterministic defaults; overrideable named parameters.
- Binary or wire-format fixtures live in `test/support/fixtures/` with a `.md` file next to them explaining what each captures.

## What not to test

- Auto-generated code (ORM models, `.arb`-generated `AppLocalizations`, JSON serializers)
- Framework code (`flutter_bloc`, `go_router` internals)
- Pure UI aesthetics (widget test the state → widget mapping, not the color of a padding)
- Coverage-chasing tests that assert framework behavior. Coverage from meaningful tests only.

## If the project uses bloc / flutter_bloc

Every Bloc / Cubit has a `bloc_test` covering its state transitions. The state machine is the contract; tests are how we know the contract holds. One `blocTest` per state transition path. Cover:

- Happy path: the state machine reaches the terminal state under expected inputs
- Error paths: every failure mode emits the corresponding error state
- Edge cases: empty inputs, concurrent events, cancellation
- Reset / cleanup: Blocs release resources on close

Do not manually build state instances by hand-typing every field. Use a factory or the actual code paths; this catches state-shape drift.

## If the project uses Drift

- **Every new DAO query method** has a *direct* DAO-level test against an in-memory Drift DB, not just transitive coverage through a repository. The join / group-by / ordering logic lives in the DAO; test it there so it survives a repository refactor. A repository test on top is still expected; it does not replace the DAO test.
- **Every schema migration** exercises the actual upgrade path, not just the version constant. `expect(db.schemaVersion, N)` does **not** test the migration: every `forTesting(NativeDatabase.memory())` DB takes the `onCreate` path and never runs `onUpgrade`. Open a DB at the previous schema (drift's `SchemaVerifier` with exported schema JSON, or a hand-built prior-version table) and assert the upgrade produces the new column/table with the correct default for pre-existing rows. A broken `onUpgrade` corrupts real installs and no other test will catch it.
