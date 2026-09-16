# Changelog

All notable changes to UniCoreFW are recorded here. The project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Each implementation slice must record its behavior changes, compatibility
impact, and verification evidence in this file.

## [Unreleased]

### Security

- Added a version-bounded `crypto` extra that selects a patched `cryptography`
  line for Python 3.7, Python 3.8, and Python 3.9 or later.
- Added deterministic plaintext, ciphertext, key, and TTL validation at the
  Fernet boundary.
- Normalized invalid key and token failures without including key or token
  values in exception messages. Backend causes remain available through
  exception chaining.
- Added optional Fernet TTL enforcement for callers that require token expiry.
- Removed query text and driver exception text from `QueryError` messages while
  retaining the driver failure as the chained cause.
- Database shutdown attempts each owned resource even if an earlier close
  operation fails.
- SQLite SQL imports now run in an isolated snapshot and deny external database
  attachment and writable-schema pragmas before target replacement.
- Unexpected importer failures no longer expose file paths, SQL, or driver
  details in their public messages. The original error remains chained.
- Transaction contexts roll back `BaseException` paths. If rollback fails in
  the same path, `DatabaseError` retains the rollback failure as its cause
  without including SQL or driver text.
- Database instances reject cross-process and cross-thread use before
  touching their mutable cursor or connection. Process ownership cannot be
  disabled.
- Database constructor, root transaction, and connection-pool failures use
  redacted package exceptions. Driver diagnostics remain available through
  exception chaining.
- Local rate policies now require bounded positive call and window values, use
  monotonic time, and keep admissions in an incrementally expired `deque`.
- Added a fail-closed distributed rate-limit contract and an atomic Redis
  backend that uses Redis server time and keeps raw client identifiers out of
  Redis key names.
- Added `SECURITY.md` with supported versions, private reporting instructions,
  and explicit assets, attacker capabilities, trust boundaries, guarantees,
  and exclusions.
- Added offline tracked-file secret detection and Python CodeQL
  `security-extended` analysis. Unsuppressed CodeQL findings at security
  severity 4.0 or higher fail before release artifacts can build.
- Security suppressions now require exact scope, a review rationale, and a
  future expiry. Blanket, mismatched, duplicate, malformed, and expired
  exceptions fail CI.

### Added

- Added `--api NAME` filtering to the release and pydash benchmark scripts for
  focused single-API comparisons. The selector is validated against the
  registered compatible cases and is forwarded to isolated workers.
- Added `--verbose` to the release and pydash benchmark scripts. Inventory and
  summary sections are now suppressed from normal text output and remain
  available on request; JSON reports are unchanged.

- Added `scripts/benchmark_pydash.py`, a bounded, process-isolated comparison
  of 240 verified `UniCoreFW.<function>` and pydash calls. The report separates
  incompatible and package-specific APIs instead of assigning them timing
  ratios, validates exact case identities and worker schemas, and retains only
  bounded diagnostic tails in parent memory.
- Added a task-focused `docs/guide_<script>.md` guide for each of the ten
  executable repository scripts. The guides document requirements, bounded
  examples, exact options, output and exit contracts, safety controls, and
  troubleshooting from the implementations. A regression test rejects missing
  guides, incomplete sections, and orphaned script guides.

### Changed

- Resumed the coverage ratchet with boundary tests for run-length compression
  and decompression limits, empty and keyed extrema, and structural equality
  mismatches. The full suite now passes with 83.78% combined statement/branch
  coverage (1,928 passed, 15 skipped); ORM coverage remains deferred by plan.
- Established 95% combined statement/branch coverage as the interim baseline;
  the executable gate remains at the verified 83% ratchet until that baseline
  is reached. The ultimate target remains 100%.
- Added deterministic coverage for function argument transforms, spread/unary
  wrappers, map/filter/reduce helpers, predicate combinators, and invalid
  `after`/`before` argument forms.
- Added supporter coverage for escaped and bracketed path parsing, tuple and
  scalar path normalization, custom item iterators, attribute-backed objects,
  and empty inputs.
- Added object-helper coverage for collection conversion, path selection,
  iteration order, membership, keyed grouping, and validation of mismatched
  key/value lengths.
- Added object coverage for scalar/container conversions, inversion, callable
  selection, pick/omit predicates, safe application, boolean parsing, and
  numeric conversion failures.
- Added nested object coverage for method invocation, updater callbacks,
  deletion idempotence, and custom-container path creation.
- Added object coverage for namedtuple/sequence and attribute path checks, plus
  cyclic deep-copy preservation.
- Added object collection-algorithm coverage for ordering, left/right
  reductions, rolling reductions, transforms, bounded sampling, deep value
  mapping, and first/last key lookup.
- Added deep object coverage for custom cloning, recursive defaults, list-aware
  merging, and assignment customizers.
- Added direct module coverage for object path selection, truthy filtering,
  reverse lookup, and shallow/deep/depth-limited flat mapping primitives.
- Extended direct object coverage to forward/reverse iteration, membership,
  method dispatch, keyed grouping, and key-based mapping.
- Full branch-coverage verification now passes 1,935 tests with 15 skips and
  measures 85.29% combined coverage, up from 83.78%. The executable ratchet
  remains 83% while work continues toward the 95% interim baseline and 100%
  ultimate target.
- Added string boundary coverage for empty predecessor/successor inputs,
  invalid search positions, null replacements, index coercion, quote handling,
  and malformed JavaScript-style regular expressions.
- Full branch-coverage verification remains green with 1,936 tests passed and
  15 skips; combined coverage increased to 85.51%, and `string.py` reached
  95.82%.
- Added utility coverage for ignored non-callable mixins, deterministic memoize
  expiry, and decompression output-limit enforcement.
- Added a scoped XML-import failure test for `types.is_element`; the module
  now measures 98.68% in focused branch coverage, with one coverage.py loop
  attribution remaining.
- Full branch-coverage verification passes 1,938 tests with 15 skips and now
  measures 85.55% combined coverage; `types.py` measures 98.68% and `utils.py`
  97.39%.
- The larger object coverage batch is verified: 1,943 tests pass with 15
  skips, combined branch coverage reaches 86.39%, and `object.py` rises from
  68.39% to 72.79%.
- The follow-up object collection batch is verified: 1,944 tests pass with 15
  skips, combined branch coverage reaches 86.84%, and `object.py` rises to
  75.13%.
- Added object validation coverage for invalid prototypes/default sources,
  failed and empty invocation paths, iterator conversion, and scalar key/value
  fallbacks.
- Added deep-path coverage for attribute targets, missing/restricted keys,
  constant updates, conditional application, and caught exceptions.
- Added object coverage for mapping-protocol defaults/conversion and
  attribute-backed keys, values, pairs, and inversion.
- Added object assignment coverage for in-place assignment, key/value mapping,
  key renaming, and customizer-driven merging.
- Added object iteration coverage for early-break behavior, reverse traversal,
  and no-match last-key lookups.
- Added object coverage for radix parsing, deep and predicate-based selection,
  boolean pattern handling, and transform early termination.
- Added customized shallow-clone coverage and path-aware deep value mapping,
  including scalar customizer overrides.
- Full verification passes 1,956 tests with 15 skips; combined branch coverage
  reaches 88.89%, and `object.py` rises to 80.53%.
- Added supporter coverage for integer-string validation, callable and concrete
  customizer normalization, flexible customizer arity, and existing/new
  container creation.
- Full verification passes 1,957 tests with 15 skips; combined branch coverage
  reaches 88.94%, and `supporter.py` rises from 82.97% to 84.28%.
- Full verification passes 1,955 tests with 15 skips; combined branch coverage
  reaches 88.83%, and `object.py` rises to 80.23%.
- Full branch-coverage verification passes 1,946 tests with 15 skips; combined
  coverage reaches 87.30%, and `object.py` rises to 77.54%.
- Added object coverage for zero, multi-source, nullable, and iterable defaults,
  plus dictionary key coercion, list negative-index, and out-of-range `has`
  paths.
- Added direct function coverage for repeated `once` calls, missing method
  invocation, dictionary/scalar iteratees, empty flows, argument flipping, and
  callable validation.
- Cumulative verification passes 1,948 tests with 15 skips; combined branch
  coverage reaches 87.77%, with `function.py` at 85.77% and `object.py` at
  78.89%.
- Added bounded enhanced-debounce coverage for zero-delay execution,
  cancellation, pending-timer cleanup, and invalid callable input.
- Full branch-coverage verification passes 1,949 tests with 15 skips; combined
  coverage reaches 88.29%, and `function.py` rises to 94.74%.
- Added direct coverage for both debounce wrapper modes and the function-module
  `map_`/`filter_` helpers.
- Full branch-coverage verification passes 1,950 tests with 15 skips; combined
  coverage reaches 88.44%, and `function.py` rises to 97.27%.
- Added deterministic enhanced-debounce coverage for timer replacement,
  cancellation cleanup, and pending-timer budget failures.
- Fixed a timing-sensitive debounce test by waiting within a bounded deadline
  for cancelled timer reservations to be released. Clean full verification now
  passes 1,951 tests with 15 skips; combined coverage is 88.57% and
  `function.py` is 99.61%.
- Full verification after the object mapping batch passes 1,952 tests with 15
  skips; combined branch coverage reaches 88.66%, and `object.py` rises to
  79.35%.
- Full verification after the assignment/customizer batch passes 1,953 tests
  with 15 skips; combined branch coverage reaches 88.79%, `object.py` reaches
  80.06%, and `function.py` measures 99.42%.

- Verified all 68 Python files under `unicorefw/`, `tests/`, and `scripts/`
  with AST parsing, Ruff 0.16.3 fatal syntax/undefined-name rules (`E9`, `F63`,
  `F7`, and `F82`), and the CI-equivalent Flake8 rules; no findings remain.
  Full default Ruff linting remains a separate, unconfigured modernization
  effort because it reports 1,254 existing style and modernization findings.

- Began the array-vs-pydash performance campaign with semantics-preserving
  fast paths: hashable uniqueness now uses `dict.fromkeys()` where applicable;
  removal APIs use expected O(n) set membership; finite-depth flattening uses a
  direct O(n) traversal; key-based sorted insertion uses O(log n) binary search;
  `fill()` uses slice assignment; comparator sorting uses the standard
  `cmp_to_key`; and sorted-last lookup avoids reverse-copy scans.
- Focused `--api` confirmations showed UniCoreFW faster for `uniq`, `fill`,
  `intersperse`, `pull`, `pull_all`, `without`, `sorted_index_by`,
  `sorted_last_index_by`, `sorted_last_index_of`, `sorted_uniq`,
  `sorted_uniq_by`, and `flatten_depth` on the current local runner. Results
  are workload- and host-specific; remaining slower APIs are not represented as
  complete or universally faster.
- Continued the array campaign with expected O(n) hashable fast paths for
  `duplicates`, `uniq_by`, and `intersection_by`, and an O(n) equal-width path
  for `interleave`. These changes preserve equality fallbacks; focused timing
  remains runner-dependent and the APIs still require confirmation on the
  project's authoritative Python 3.10 environment.

- Crypto backend failures now use `CryptoUnavailableError`, invalid key material
  uses `InvalidKey`, and authentication failures use the package's
  `InvalidToken`.
- CI installs the project `crypto` and `orm` extras in test, coverage, and
  security jobs. The security job imports both backends and exercises their
  direct suites.
- Raised the combined statement/branch coverage ratchet from 77% to 77.5%.
- Added a bounded SQLAlchemy 2.0 `orm` extra and raised the coverage ratchet
  from 77.5% to 79.5%.
- Raised the combined statement/branch coverage ratchet from 79.5% to 81.5%.
- Raised the combined statement/branch coverage ratchet from 81.5% to 82%.
- Raised the combined statement/branch coverage ratchet from 82% to 82.5%.
- Raised the combined statement/branch coverage ratchet from 82.5% to 83%.
- Added canonical `DatabaseConnectionError` and `DatabaseImportError` names.
  The original `ConnectionError` and `ImportError` names remain aliases.
- Migration versions and scripts are validated before execution. Reusing an
  applied version with changed SQL now raises `DatabaseError` on checksum
  mismatch.
- Repeated `begin()` calls create generated savepoints. `commit()` and
  `rollback()` close one managed level while depth-zero calls retain direct
  driver behavior.
- Added a required PostgreSQL 17.10 and MySQL 8.4.10 integration job with
  digest-pinned service images, bounded current drivers, and dependency
  auditing.
- Added `LocalRateLimiter` as the explicit process-local name while retaining
  `RateLimiter` as an alias. Added `require_callable()` while retaining
  `validate_callable()` as a callability-only wrapper.
- Re-documented tag stripping as a text transformation rather than an HTML
  sanitizer and direct HTML callers to contextual escaping or a maintained
  allow-list sanitizer.
- The security integration job now exercises Redis admission, denial,
  concurrency, expiry, and identifier handling against a digest-pinned Redis
  service.
- Release builds now depend on the reusable CodeQL workflow in addition to the
  complete test, coverage, Bandit, dependency-audit, and secret-scanning gates.
- The package root now resolves declared compatibility exports lazily. A bare
  `import unicorefw` no longer imports core utilities, cryptography,
  SQLAlchemy, database drivers, pandas, or openpyxl.
- Database and ORM functions remain available through their submodules,
  package-root names, and compatible `UniCoreFW` static calls, but are no
  longer registered as collection-chain methods.
- Added dependency-free `core` and bounded `database` and `spreadsheet` extras.
  The existing crypto and ORM dependency sets remain separate.
- Added a required Linux import-budget job that enforces 100 ms median latency,
  10 MiB median incremental RSS, optional-dependency isolation, and detected
  import-side-effect checks.
- Replaced repeated collection membership scans with one stable hash-backed
  membership primitive across uniqueness, union, difference, intersection,
  symmetric-difference, keyed, duplicate, and value-removal operations.
  Unhashable values and derived keys retain equality semantics through a
  documented quadratic fallback.
- Replaced repeated front insertions in `take_right_while()` and `unshift()`
  with one reverse and one in-place slice update respectively.
- Added bounded representative collection benchmarks to the Ubuntu 24.04,
  Python 3.11.9 performance job.
- Replaced core module and package-factory reflection with a generated dispatch
  registry. `now()`, `noop()`, and `generate_key()` remain static calls but are
  no longer invalid collection-chain methods.
- Replaced the manual per-function export registry with build-time discovery.
  Module-owned top-level functions whose names do not begin with `_` now enter
  the generated package-root and dispatch declarations automatically. Runtime
  imports remain reflection-free; database, ORM, and supporter discovery parses
  source without importing those modules, and unreviewed name collisions fail
  generation.
- PEP 517 wheel and source-distribution builds now regenerate the public export,
  core dispatch, and API metadata artifacts before copying or archiving files.
  The build hook uses a fixed argument array, active interpreter, repository
  working directory, bounded execution, and sanitized fail-closed errors.
- Added supporter coverage for mapping and attribute path fallbacks, nested list
  growth and type errors, malformed path/regex parsing, empty and negative-depth
  flattening, safe import fallback, scheduler absence, and callable validation.
- Full branch-coverage verification passes 1,958 tests with 15 skips; combined
  coverage reaches 89.27%, while `supporter.py` rises to 90.61%.
- Added object-helper coverage for numeric/string path mismatches, indexed and
  mapped invocation fallbacks, swallowed callable failures, and callable
  ordering with default and partial order specifications.
- Full branch-coverage verification passes 1,960 tests with 15 skips; combined
  coverage reaches 89.44%, and `object.py` improves to 81.35%.
- Full branch-coverage verification passes 1,961 tests with 15 skips; combined
  coverage reaches 89.55%, and `object.py` improves to 81.94%.
- Extended `invoke()` coverage for explicit string/integer key coercion,
  missing intermediate segments, and `None` traversal termination.
- Full branch-coverage verification passes 1,961 tests with 15 skips; combined
  coverage reaches 89.57%, and `object.py` improves to 82.29%.
- Added supporter coverage for attribute container creation, immutable
  container classification, `None` path traversal, nested list mutation,
  root-container type errors, and trailing escape parsing.
- Full branch-coverage verification passes 1,962 tests with 15 skips; combined
  coverage reaches 89.84%, and `supporter.py` rises to 94.98%.
- Extended supporter coverage for nested list allocation and type failures,
  empty-path handling, negative-depth flattening, regex flag parsing, missing
  delimiters, and successful event-loop scheduling.
- Full branch-coverage verification passes 1,963 tests with 15 skips; combined
  coverage reaches 90.01%, and `supporter.py` rises to 98.47%.
- Added direct utility timestamp coverage and nested primitive mismatch coverage
  for structural equality in `types.py`.
- Full branch-coverage verification passes 1,963 tests with 15 skips; combined
  coverage reaches 90.03%, and `utils.py` improves to 97.83%.
- Added deterministic memoization-expiry and digit-only decompression coverage
  to exercise cache removal and no-character output paths.
- Full branch-coverage verification passes 1,964 tests with 15 skips; combined
  coverage remains 90.03%, and `utils.py` rises to 98.26%.
- Added string coverage for compiled-pattern replacement, invalid position
  coercion, invalid prune lengths, and `None` lower-case handling.
- Full branch-coverage verification passes 1,965 tests with 15 skips; combined
  coverage reaches 90.18%.
- Added object coverage for empty paths, generic sequence indexing, invalid
  key/function inputs, and dictionary/set-to-array conversion.
- Full branch-coverage verification passes 1,966 tests with 15 skips; combined
  coverage reaches 90.26%.
- Added array coverage for invalid `find` arguments, empty `first`/`last`
  requests, `reduce` without an initial accumulator, and unhashable exclusions.
- Full branch-coverage verification passes 1,967 tests with 15 skips; combined
  coverage reaches 90.36%.
- Added string coverage for `upper_case(None)`, negative truncation lengths,
  oversized omissions, invalid repeat counts, and empty/invalid regex patterns.
- Full branch-coverage verification passes 1,968 tests with 15 skips; combined
  coverage reaches 90.48%.
- Added object coverage for string/integer path coercion, sequence and
  attribute misses, and two-dictionary defaults assignment.
- Full branch-coverage verification passes 1,969 tests with 15 skips; combined
  coverage reaches 90.60%.
- Added namedtuple field/index/miss coverage and the duplicate-key branch for
  two-dictionary defaults.
- Full branch-coverage verification passes 1,969 tests with 15 skips; combined
  coverage reaches 90.78%, and `object.py` improves to 84.22%.
- Added mutable-mapping defaults coverage and verified the list identity fast
  path in `to_array()`.
- Full branch-coverage verification passes 1,970 tests with 15 skips; combined
  coverage reaches 90.98%, and `object.py` improves to 85.34%.
- Added object coverage for negative namedtuple indices, iterable defaults,
  malformed default sources, and invalid source iteration.
- Full branch-coverage verification passes 1,970 tests with 15 skips; combined
  coverage reaches 91.15%, and `object.py` improves to 86.22%.
- Added object collection-helper coverage for invalid indexed paths, scalar
  traversal misses, no-match `find_last`, and non-iterable `flat_map` results.
- Full branch-coverage verification passes 1,970 tests with 15 skips; combined
  coverage reaches 91.23%, and `object.py` improves to 86.63%.
- Added mutable-mapping `defaults(..., None)` no-op coverage.
- Full branch-coverage verification passes 1,970 tests with 15 skips; combined
  coverage reaches 91.26%.
- Added string coverage for separator-aware truncation, URL fragment merging,
  empty URL input, and empty start-case normalization.
- Full branch-coverage verification passes 1,971 tests with 15 skips; combined
  coverage reaches 91.30%.
- Extended string coverage for punctuation trimming, compiled regex replacement,
  URL path joining/trailing slashes, and additional separator branches.
- Full branch-coverage verification passes 1,971 tests with 15 skips; combined
  coverage reaches 91.34%.
- Added array boundary coverage for scalar and sized `last()` calls, empty and
  mismatched `unzip()`, empty `last_index_of()`, and non-positive `chunk()`.
- Full branch-coverage verification passes 1,972 tests with 15 skips; combined
  coverage reaches 91.50%.
- Added array coverage for zero/single-item sampling, callable indexing, and
  validation/exception paths in `count_by()` and `group_by()`.
- Full branch-coverage verification passes 1,973 tests with 15 skips; combined
  coverage reaches 91.71%.
- Added array extrema coverage for empty inputs, default comparisons, and
  key-function selection in `max_value()` and `min_value()`.
- Full branch-coverage verification passes 1,974 tests with 15 skips; combined
  coverage reaches 91.86%.
- Added adversarial sorted-array cases for both median binary-search partition
  adjustment directions.
- Full branch-coverage verification passes 1,975 tests with 15 skips; combined
  coverage reaches 91.89%.
- Added array coverage for fully consumed `drop_while`/`drop_right_while`,
  empty `fill`, and scalar `find_index`/`find_last_index` predicates.
- Full branch-coverage verification passes 1,976 tests with 15 skips; combined
  coverage reaches 92.02%, and `array.py` improves to 91.31%.
- Added direct string-module coverage for URL fragment/path edge branches and
  empty start-case normalization.
- Full branch-coverage verification passes 1,976 tests with 15 skips; combined
  coverage reaches 92.07%, and `string.py` improves to 99.76%.
- Added direct nested-equality coverage for the remaining `types.is_equal()`
  primitive continuation path.
- Full branch-coverage verification passes 1,976 tests with 15 skips; combined
  coverage measures 92.06% in this run.
- Added supporter coverage for numeric bracket parsing with leading zeroes and
  ignored JavaScript-style regex flags.
- Full branch-coverage verification passes 1,976 tests with 15 skips; combined
  coverage reaches 92.10%, and `supporter.py` improves to 99.13%.
- Added array coverage for zero-depth/null/scalar flattening, duplicate-aware
  intersection, singleton interspersion, and out-of-range `nth()`.
- Full branch-coverage verification passes 1,977 tests with 15 skips; combined
  coverage reaches 92.22%, and `array.py` improves to 92.08%.
- Added array coverage for empty `shift()`, fully consumed `take_while()`, and
  unhashable-key `uniq_by()` fallback behavior.
- Full branch-coverage verification passes 1,978 tests with 15 skips; combined
  coverage reaches 92.24%, and `array.py` improves to 92.31%.
- Added default-comparison coverage for non-empty `max_value()` and
  `min_value()` calls.
- Full branch-coverage verification passes 1,978 tests with 15 skips; combined
  coverage reaches 92.29%, and `array.py` improves to 92.62%.
- Added exclusion filtering coverage for unhashable array items with hashable
  exclusion values.
- Full branch-coverage verification passes 1,978 tests with 15 skips; combined
  coverage reaches 92.31%, and `array.py` improves to 92.77%.
- Added negative out-of-range `nth()` coverage.
- Full branch-coverage verification passes 1,978 tests with 15 skips; combined
  coverage reaches 92.32%.
- Added direct `_exclude_values()` coverage for unhashable items against a
  hashable exclusion set.
- Full branch-coverage verification passes 1,978 tests with 15 skips; combined
  coverage reaches 92.32%, and `array.py` improves to 92.85%.
- Added array coverage for nested zip construction/type errors, mixed
  intercalation, empty/negative-index `pop()`, and out-of-range `slice_()`.
- Full branch-coverage verification passes 1,979 tests with 15 skips; combined
  coverage reaches 92.43%.
- Added array coverage for large-index `pull_at`, initializer/empty `ft_reduce`,
  comparator-key conversion, and `sort()` validation/empty paths.
- Full branch-coverage verification passes 1,980 tests with 15 skips; combined
  coverage reaches 92.83%.
- Added array coverage for `unzip_with()` input/iteratee validation, empty
  inputs, callback errors, and the no-argument `zip_with()` path.
- Full branch-coverage verification passes 1,981 tests with 15 skips; combined
  coverage reaches 92.97%, and `array.py` improves to 97.31%.
- Added array coverage for comparator-key rich comparisons, tuple fallback in
  `uniq_by()`, nested indexed `zip_object_deep()`, and one-/two-/N-way
  `xor_with()` validation and comparator paths.
- Full branch-coverage verification passes 1,982 tests with 15 skips; combined
  coverage reaches 93.18%, and `array.py` improves to 98.77%.
- Extended array edge coverage for indexed `zip_object_deep()` overwrites,
  wrapped comparator failures in `sort()`, and remaining `xor_with()` input and
  comparator error paths.
- Full branch-coverage verification passes 1,982 tests with 15 skips; combined
  coverage reaches 93.28%, and `array.py` improves to 99.39%.
- Added object coverage for collection invocation/keying/nesting, callable key
  mapping, custom key/value readers, list-path unsetting, scalar cloning, and
  nested default replacement.
- Full branch-coverage verification passes 1,983 tests with 15 skips; combined
  coverage reaches 93.66%, and `object.py` improves to 88.68%.
- Added object coverage for nested `nest()` traversal, scalar conversion,
  cyclic `clone_deep()` memoization, missing/list/attribute `unset()` paths,
  ignored invalid defaults, and list-of-dicts default merging.
- Full branch-coverage verification passes 1,984 tests with 15 skips; combined
  coverage reaches 93.81%, and `object.py` improves to 89.50%.
- Added object coverage for flexible-arity `assign_with()` customizers,
  iterable/invalid sources, and callable/None execution paths in
  `apply_if_not_none()`.
- Full branch-coverage verification passes 1,985 tests with 15 skips; combined
  coverage reaches 93.95%, and `object.py` improves to 90.21%.
- Added object coverage for scalar/cyclic `map_values_deep()`, list/scalar
  `clone_with()`, generic sequence and namedtuple `get()` paths, and no-match
  `find_key()` behavior.
- Full branch-coverage verification passes 1,986 tests with 15 skips; combined
  coverage reaches 94.16%, and `object.py` improves to 91.32%.
- Added object coverage for `merge_with()`, `transform()`, numeric conversion,
  list-customized `set_with()`, `update_with()`, and modern/legacy apply helpers.
- Full branch-coverage verification passes 1,987 tests with 15 skips; combined
  coverage reaches 94.57%, and `object.py` improves to 93.43%.
- Added object coverage for list-root `merge_with()` folding and boolean,
  numeric, hexadecimal, and invalid `parse_int()` inputs.
- Full branch-coverage verification passes 1,988 tests with 15 skips; combined
  coverage reaches 94.72%, and `object.py` improves to 94.31%.
- Added object coverage for integer/string path coercion across mappings,
  lists, tuples, and ranges; cyclic `clone_deep_with()` memoization; and empty
  or nullable `merge()` inputs.
- Full branch-coverage verification passes 1,989 tests with 15 skips; combined
  coverage reaches 94.80%, and `object.py` improves to 94.72%.
- Added object coverage for deep/top-level selection, empty and indexed `set_`,
  pattern-driven `to_boolean()`, and remaining `pick_by()` modes.
- Full branch-coverage verification passes 1,990 tests with 15 skips; combined
  coverage reaches 94.85%, and `object.py` improves to 94.90%.
- Added equality coverage for differing nested scalar values and decompression
  output-limit coverage for limits exceeded after partial expansion.
- Full branch-coverage verification passes 1,990 tests with 15 skips; combined
  coverage reaches 94.84%.
- Added supporter flattening coverage for boolean depth compatibility and
  string normalization coverage for separator-only inputs.
- Full branch-coverage verification passes 1,991 tests with 15 skips; combined
  coverage remains 94.84%.
- Added `bind_all()` coverage for existing and missing method names.
- Full branch-coverage verification passes 1,991 tests with 15 skips; combined
  coverage reaches 94.86%, and `function.py` improves to 99.81%.
- Added object coverage for list/set/invalid exception specifications in
  `apply_catch()` and empty-ish `merge()` inputs.
- Full branch-coverage verification passes 1,991 tests with 15 skips; combined
  coverage reaches 94.96%, and `object.py` improves to 95.43%.
- Added deterministic enhanced-debounce coverage for cancelling the max timer
  when regular timer scheduling fails.
- Full branch-coverage verification passes 1,992 tests with 15 skips; combined
  coverage reaches 94.95%.
- Added direct integer-segment list-index coverage for `unset()` bounds checks.
- Full branch-coverage verification passes 1,992 tests with 15 skips; combined
  coverage remains 94.95%.
- Added object coverage for explicit `transform()` accumulators and empty-path
  `set_with()` handling.
- Full branch-coverage verification passes 1,992 tests with 15 skips; combined
  coverage reaches 94.98%, and `object.py` improves to 95.60%.
- Added object coverage for existing-key preservation in `defaults()` and
  integer-subclass conversion failures in `parse_int()`.
- Full branch-coverage verification passes 1,992 tests with 15 skips; combined
  coverage reaches 94.99%, and `object.py` improves to 95.72%.
- Added enhanced-debounce execution coverage verifying both active timers are
  cancelled when the deferred callback runs.
- Full branch-coverage verification passes 1,993 tests with 15 skips; combined
  coverage reaches 95.01%.

### Fixed

- Regenerated the stale `docs/api/core-exports.json` artifact. The core
  registry generator entry point and committed-artifact drift checks now pass;
  the focused registry generation suite passes all 29 tests.

- Corrected the immutable `pypa/gh-action-pypi-publish` v1.14.0 reference. The
  previous SHA had no matching GHCR image, so the publish job stopped before
  requesting a PyPI trusted-publishing token or uploading an artifact.
- Made `session_scope()` implement its documented async context-manager
  contract, including rollback when the caller body raises.
- Retained the MongoDB client until database shutdown, stopped forwarding the
  logical database name as a `MongoClient` option, and closed clients after
  database-selection failures.
- Ensured `Database.__exit__()` closes resources after commit or rollback
  failures.
- Replaced migration semicolon splitting with parser-aware SQLite statement
  boundaries, complete-script delegation to PostgreSQL, and quote-aware and
  comment-aware MySQL statement boundaries.
- Made SQLite migration DDL, migration records, automatic importer table
  creation, and inserted rows transactional.
- Prevented a failed SQLite SQL script import from retaining statements that
  completed before the failure.
- Prevented an inner transaction context from committing its outer
  transaction. Inner rollback now preserves outer work, and outer rollback
  discards changes from released inner savepoints.
- Closed partial relational-driver resources after cursor or configuration
  failures and made pool shutdown attempt every unique connection after a
  close failure.
- Database lifecycle contexts now begin a managed root transaction before
  yielding. PostgreSQL context-body failures therefore roll back instead of
  retaining writes made while the driver was in autocommit mode.
- Failed database context entry now closes partial resources, and context exit
  unwinds every managed savepoint before closing the connection.
- `xor()` and `xor_by()` now coalesce duplicate contributors as documented,
  matching the existing stable uniqueness contract.
- Completed the release benchmark registry for `require_callable()`,
  `html_template()`, `unsafe_raw_sql()`, and `unsafe_raw_css()`. Normal
  comparisons now benchmark these local APIs and report an API absent from an
  older installed release as `MISSING` without aborting the worker.

Release-workflow compatibility impact: None. The release job retains OIDC
authentication, provenance attestations, least-privilege permissions, and the
verified-artifact boundary.

Release-workflow verification:

- Confirmed the signed v1.14.0 release commit and its GHCR image tag. PyPA
  published the image as digest
  `sha256:72bce99a396e7ed0635f3fcc0f0a7052314a68c00c1999f5d0f9454b18cd2e40`.
- Added a regression assertion for the full 40-character release commit.
- Parsed the workflow YAML and passed the release-script suite.

### Optimization record

#### 2026-07-22: SEC-007 cryptography boundary

Status: Complete

- Preserved existing package-level and `UniCoreFW` crypto entry points.
- Preserved `encrypt_string(plaintext, key)` and
  `decrypt_string(ciphertext, key)` calls. `ttl` is an optional third argument,
  and its default retains the prior no-expiry behavior.
- Kept missing-backend errors compatible with `RuntimeError` and decryption
  failures compatible with `ValueError`. Exact exception classes and messages
  are now more specific.
- Documented key generation, external secret storage, rotation, creation-time
  exposure, and Fernet's full-message memory behavior.
- Added 22 direct tests for public entry points, missing dependencies, input
  types, invalid and wrong keys, corrupted and expired tokens, Unicode,
  non-UTF-8 content, and a 1 MiB payload.

Verification:

- Python 3.11.12 with cryptography 49.0.0: 1,457 tests passed in 28.79
  seconds. Combined statement/branch coverage reached 77.78%; statement
  coverage reached 80.81% and branch coverage reached 69.97%.
- `unicorefw/crypto.py` reached 100% statement and branch coverage.
- Python 3.8 resolver verification selected cryptography 46.0.7; all 22 crypto
  tests passed. The complete Python 3.8 suite passed 1,455 tests with 2 optional
  tests skipped.
- Bandit 1.9.4 reported no medium or high findings. The strict audit of the
  isolated Python 3.11 CI environment reported no known vulnerabilities.
- Fatal Flake8 checks, source compilation, `git diff --check`, clean sdist and
  wheel builds, `twine check`, wheel smoke verification, and wheel dependency
  metadata inspection passed.

Compatibility impact: Existing valid calls remain compatible. Code that
compares exact exception types or messages should use the documented package
exceptions instead.

#### 2026-07-22: STAB-002 ORM and database lifecycle

Status: Slice complete; service-backed drivers and nested transactions remain

- Added 33 tests for installed and missing SQLAlchemy, SQLAlchemy 1.4 fallback
  imports, sync SQLite sessions, async session success and rollback, legacy
  async iteration, database contexts, transactions, connection pools, resource
  shutdown, unavailable drivers, and unsupported operations.
- Repaired the documented `async with session_scope(...)` path and retained
  direct `async for` and `aclose()` compatibility.
- Validated database engine and connection-pool configuration before resource
  creation.
- Normalized closed database and invalid query failures with package exceptions
  and chained driver causes.
- Added MongoDB client ownership and cleanup for complete and partial
  initialization.

Verification:

- Python 3.11.12 with SQLAlchemy 2.0.51: 1,490 tests passed in 32.19
  seconds. Combined statement/branch coverage reached 79.83%; statement
  coverage reached 82.82% and branch coverage reached 72.57%.
- `unicorefw/orm.py` reached 100% statement and branch coverage.
  `unicorefw/db.py` rose from 69.37% to 75.49% combined coverage.
- Python 3.8 selected SQLAlchemy 2.0.51 and passed 1,488 tests with 2
  spreadsheet tests skipped.
- Bandit 1.9.4 reported no medium or high findings. The strict audit of the
  Python 3.11 CI environment reported no known vulnerabilities.
- Fatal Flake8 checks, clean sdist and wheel builds, `twine check`, wheel smoke
  verification, and wheel dependency metadata inspection passed.

Compatibility impact: Existing async iteration over `session_scope()` remains
available. `ConnectionError` and `ImportError` remain aliases, so existing
imports and exception handlers continue to work. Their canonical class names
now include the `Database` prefix. `QueryError` messages no longer include
driver text; callers can inspect `__cause__` for diagnostics without returning
it to clients.

#### 2026-07-23: STAB-002 migration and importer integrity

Status: Slice complete; nested transactions and service-backed drivers remain

- Preserved `Migration`, `DataImporter`, and database transaction public
  signatures and return values.
- Replaced lexical SQLite migration splitting with native parser-aware
  statement boundaries. Quoted semicolons and trigger bodies remain intact.
- Applied SQLite DDL, data changes, and migration tracking rows in one
  transaction. Failed migrations no longer retain their schema changes.
- Verified existing migration checksums before returning the prior `False`
  result. A changed script for the same version now fails explicitly.
- Moved JSON, CSV, Excel, and dictionary table creation into their insert
  transactions, so a later invalid row removes an auto-created table.
- Executed trusted SQLite SQL imports in an isolated snapshot and changed the
  target only after the script completed. External attachment and
  writable-schema pragmas remain blocked.
- Added redacted importer failure messages with chained parser, filesystem, and
  driver causes.
- Added 33 direct migration and import tests across JSON, CSV, Excel, SQL, and
  dictionary paths.

Verification:

- Python 3.11.12: 1,523 tests passed in 38.88 seconds. Combined
  statement/branch coverage reached 81.96%; statement coverage reached 84.69%
  and branch coverage reached 75.37%.
- `unicorefw/db.py` rose from 75.49% to 84.03% combined coverage.
- Python 3.8 passed 1,519 tests with 4 spreadsheet tests skipped.
- Bandit 1.9.4 reported no medium or high findings, and fatal Flake8 checks
  reported no errors.
- The strict dependency audit reported no known vulnerabilities. Source
  compilation, `git diff --check`, release verification, clean sdist and wheel
  builds, `twine check`, and wheel smoke verification passed.

Compatibility impact: Existing valid migration and importer calls retain their
signatures, return values, exception aliases, and supported formats. Unexpected
import failures now use a stable redacted message; protected diagnostics can
inspect `__cause__`. Reapplying an unchanged migration still returns `False`,
while checksum drift now raises `DatabaseError`.

#### 2026-07-24: STAB-002 nested transactions and savepoints

Status: Slice complete; service-backed drivers and thread ownership remain

- Preserved the `transaction()`, `begin()`, `commit()`, and `rollback()` public
  signatures.
- Added transaction depth tracking and generated savepoints for nested SQLite,
  PostgreSQL, and MySQL scopes.
- Limited nested commit and rollback calls to their current managed level.
- Unwound child levels opened inside a transaction context and preserved manual
  depth-zero commit and rollback behavior.
- Rolled back `BaseException` paths and retained chained diagnostics when
  rollback failed.
- Restored PostgreSQL autocommit after root commit, root rollback, and failed
  begin operations.
- Reset managed transaction state during close while the driver rolled back
  uncommitted work.
- Added 22 direct tests for SQLite data and DDL isolation, PostgreSQL
  autocommit, MySQL savepoint SQL, manual nesting, interrupts, commit failures,
  rollback failures, closed cursors, and driver compatibility.

Verification:

- Python 3.11.12: 1,545 tests passed in 30.41 seconds. Combined
  statement/branch coverage reached 82.40%; statement coverage reached 85.02%
  and branch coverage reached 76.02%.
- `unicorefw/db.py` rose from 84.03% to 85.61% combined coverage.
- Python 3.8 passed 1,541 tests with 4 spreadsheet tests skipped.
- Bandit 1.9.4 reported no medium or high findings. The strict dependency
  audit reported no known vulnerabilities.
- Fatal Flake8 checks, source compilation, `git diff --check`, release
  verification, clean sdist and wheel builds, `twine check`, and wheel smoke
  verification passed.

Compatibility impact: Existing single-level contexts keep their prior commit
and rollback behavior. Direct depth-zero `commit()` and `rollback()` calls
continue to invoke the driver. Repeated `begin()` calls create savepoints, and
nested commit or rollback calls close one level instead of ending the root
transaction. MySQL DDL can commit outside savepoint control; callers that need
transactional MySQL schema changes must use native migration tooling.

#### 2026-07-27: STAB-002 thread ownership and driver failures

Status: Slice complete; service-backed driver tests and the primary database
abstraction decision remain

- Bound each `Database` instance to its creating process and thread. Public
  operations reject ownership violations before accessing a driver resource.
- Added `unsafe_allow_cross_thread=True` for legacy callers that configure
  native driver support and serialize every operation. The option does not
  bypass process ownership or add locking.
- Added partial-initialization cleanup for SQLite, PostgreSQL, MySQL, and
  MongoDB. Cursor, connection, and client resources close in reverse creation
  order.
- Normalized unexpected constructor and connection-factory failures as
  `DatabaseConnectionError`.
- Normalized root begin, commit, rollback, and PostgreSQL transaction-mode
  restoration failures as `DatabaseError`.
- Removed connection parameters and driver text from these public error
  messages while retaining the original errors through `__cause__`.
- Made connection-pool shutdown clear its tracked state and attempt every
  unique connection after a driver close failure.
- Added 45 direct tests for process and thread ownership, the explicit opt-out,
  direct SQLite and MongoDB driver paths, partial constructors, pool failures,
  transaction failures, cleanup ordering, and control-flow exceptions.

Verification:

- Python 3.11.12: 1,590 tests passed in 32.40 seconds. Combined
  statement/branch coverage reached 82.96%; statement coverage reached 85.52%
  and branch coverage reached 76.68%.
- `unicorefw/db.py` reached 87.45% combined coverage.
- Python 3.8 passed 1,586 tests with 4 optional spreadsheet tests skipped in
  16.70 seconds.
- The coverage ratchet increased from 82% to 82.5%.
- Bandit 1.9.4 reported no medium or high findings. The strict dependency
  audit reported no known vulnerabilities.
- Fatal Flake8 checks, source compilation, `git diff --check`, release
  verification, clean sdist and wheel builds, `twine check`, and wheel smoke
  verification passed.

Compatibility impact: Existing valid constructor, transaction, CRUD, import,
export, and pool calls retain their signatures and return values. Cross-thread
use now fails by default because one instance owns one mutable cursor and
connection. Serialized legacy use can set `unsafe_allow_cross_thread=True`
with the required driver option. Failure paths raise stable package
exceptions instead of raw driver exceptions; exact raw diagnostics remain
available in `__cause__`.

#### 2026-07-28: STAB-002 PostgreSQL and MySQL integration boundary

Status: Repository implementation complete; first CI service execution pending

- Added an opt-in service suite for PostgreSQL and MySQL connection lifecycle,
  bound adversarial values, root commit and rollback, nested savepoint rollback,
  outer rollback after savepoint release, failed-query recovery, and resource
  closure.
- Made the service suite fail closed unless both targets use the dedicated
  `unicorefw_test` database, the `unicorefw` test user, expected ports, and
  loopback address `127.0.0.1`.
- Added one required Linux CI job using digest-pinned PostgreSQL 17.10 and MySQL
  8.4.10 images and isolated non-production credentials.
- Bounded the CI driver lines to psycopg2-binary 2.9.12 and PyMySQL 1.2, and
  audit the installed integration environment before tests run.
- Corrected `Database.__enter__()` to begin a managed root transaction. Context
  failure now has consistent rollback behavior when PostgreSQL starts in
  autocommit mode.
- Made context entry close resources after a begin failure and made context exit
  unwind nested managed levels before closing.

Verification:

- Focused database lifecycle, transaction, service-configuration, and release
  workflow suites: 94 passed and 10 service tests skipped because no local
  PostgreSQL or MySQL server was available.
- Full Python 3.10 suite: 1,598 passed and 14 skipped in 14.01 seconds.
- The local branch-coverage run measured 82.35% without pandas/openpyxl and
  therefore did not satisfy the 82.5% all-extras ratchet. The required coverage
  job installs those integrations; its execution and the new real-service job
  remain CI verification gates.
- Workflow YAML parsing, fatal Flake8 checks, source compilation, and
  `git diff --check` passed.

Compatibility impact: Successful relational database contexts retain their
commit-and-close behavior. A context now starts a managed transaction on entry,
so PostgreSQL body failures correctly roll back. Code that manually opens nested
levels inside a database lifecycle context has each level resolved on exit.
Direct calls to `__exit__()` without `__enter__()` retain their prior depth-zero
driver commit or rollback behavior.

#### 2026-07-28: SEC-006 security utility contracts

Status: Repository implementation complete; first CI Redis service execution pending

- Bounded `max_calls` to 1,000,000 and `time_window` to one year, rejecting
  booleans, non-numeric values, non-finite values, zero, and negative values.
- Replaced wall-clock/list cleanup with an injected monotonic clock, a
  thread-safe `deque`, exact-boundary expiry, and fail-closed clock validation.
- Exposed `LocalRateLimiter` without removing the compatible `RateLimiter`
  name.
- Added the structural `RateLimitBackend` contract,
  `DistributedRateLimiter`, and `RedisRateLimitBackend`.
- Made the distributed wrapper reject backend errors, non-boolean responses,
  and denials without copying backend diagnostics into public messages.
- Implemented Redis admission as one Lua evaluation using server time,
  sorted-set expiry/count/admission, unique members, and millisecond TTLs.
  Client identifiers are SHA-256 hashed before key construction; documentation
  states that deterministic hashing is not anonymization.
- Added a required real-service test using a digest-pinned Redis 8.8.1 image
  and a bounded redis-py 8 client. The test uses a unique namespace and database
  15, accepts only `127.0.0.1:6379`, and deletes only its exact keys.
- Added `require_callable()` with an explicit callability-only contract.
  `validate_callable()` remains compatible. Updated tag-stripping docs without
  changing their historical output.
- Added and packaged `SECURITY.md`; updated the README, long-form docs,
  master plan, and security CI suite.

Verification:

- Full Python 3.10 suite: 1,628 passed and 15 skipped in 14.48 seconds. The
  opt-in Redis service test accounts for one local skip.
- Combined statement/branch coverage reached 82.55% without pandas/openpyxl,
  satisfying the 82.5% ratchet. `unicorefw/security.py` reached 100% statement
  and branch coverage.
- Bandit 1.9.4 reported no medium or high findings. Fatal Flake8 checks,
  source compilation, workflow YAML parsing, release-script verification, and
  `git diff --check` passed.
- A clean PEP 517 sdist and wheel build passed. The sdist contains
  `SECURITY.md`; Twine 6.2.0 strict checks and isolated wheel smoke verification
  passed.
- The local environment does not contain `pip-audit` or a Redis server. The
  required security CI job installs the bounded audit/client dependencies,
  audits them before testing, and remains the gate for the first real Redis
  execution.

Compatibility impact: Existing valid `RateLimiter(max_calls, time_window)`
calls and context behavior remain compatible. Invalid or excessively large
policies now fail during construction. The optional `clock` is keyword-only.
Code that depends on the undocumented concrete list type of `limiter.calls`
now observes a `deque`. Callable and tag-stripping output behavior is
unchanged. Distributed rate-limiting APIs are additive.

#### 2026-07-28: SEC-008 static analysis and dependency policy

Status: Repository implementation complete; first CodeQL execution pending

- Added exact `detect-secrets` 1.5.0 scanning for every tracked or pending
  non-ignored file. Online verification is disabled so candidate values are
  not submitted to third-party endpoints.
- Added `scripts/verify_security_policy.py` to reject blanket, mismatched,
  reused, malformed, and expired inline suppressions. The current 18
  suppressions name an exact rule or fixture purpose, include a review
  rationale, and expire on 2027-07-28.
- Added a versioned CodeQL suppression registry keyed by tool, rule, and SARIF
  fingerprint. Exceptions require a rationale and future expiry.
- Added a reusable Python CodeQL 4.36.0 workflow, pinned to its full action
  commit, using `security-extended` queries. Unsuppressed results at security
  severity 4.0 or higher fail the job.
- Made release artifact construction depend on the CodeQL gate. Tag analysis
  is verified locally without uploading tag-scoped SARIF; branch and pull
  request results are uploaded after the repository severity gate.
- Confirmed that `CacheManager` uses a length-framed SHA-256 query-cache key.
  Added direct tests for the exact payload, determinism, boundary separation,
  parameter isolation, invalid input, and expired-entry pruning.
- Updated `SECURITY.md`, the README, long-form documentation, packaging
  manifests, and the master plan with the enforcement and exception policy.

Verification:

- Full Python 3.10 suite: 1,657 passed and 15 skipped in 22.71 seconds.
- Combined statement/branch coverage reached 82.58%, satisfying the 82.5%
  ratchet. The completion target remains 100% statement and branch coverage.
- Bandit 1.9.4 reported no medium or high findings. The suppression verifier
  accepted 18 scoped exceptions, and the exact detect-secrets CI command
  reported no candidate secrets.
- Fatal Flake8 checks, source compilation, workflow YAML parsing, release
  workflow regression tests, and `git diff --check` passed.
- A clean PEP 517 sdist and wheel build passed. The sdist contains the security
  policy verifier and suppression registry; Twine 6.2.0 strict checks and
  isolated wheel smoke verification passed.
- The local environment does not contain `pip-audit`, and this checkout cannot
  execute GitHub CodeQL actions. The required CI gates install and run the
  strict dependency audit and CodeQL analysis before release construction.

Compatibility impact: No runtime behavior or public API changed in this slice.
CI and release policy are stricter. Existing security suppressions must adopt
the documented exact scope, rationale, and future-expiry format.

#### 2026-07-28: PERF-001 lazy optional imports

Status: Repository implementation complete; first pinned CI benchmark
execution pending

- Replaced package-root wildcard imports with a dependency-free declarative
  export ownership map and module `__getattr__` resolution. Resolved exports
  are cached after first access.
- Made `UniCoreFW`, `UniCoreFWWrapper`, and `_` lazy package-root exports.
  Loading these core entry points imports the utility registry without loading
  crypto, database, ORM, or their third-party dependencies.
- Preserved lazy static and chain compatibility for the three crypto helpers.
  Preserved root and static compatibility for database and ORM helper
  functions while removing them from the collection-chain registry.
- Restored the Python module name to `unicorefw`; `DISPLAY_NAME` exposes the
  human-facing `UniCoreFW` name.
- Added bounded `core`, `database`, and `spreadsheet` extras. The spreadsheet
  set includes `defusedxml` for openpyxl XML parser hardening. Maintained
  database and spreadsheet dependencies require Python 3.9 or later.
- Added `scripts/benchmark_imports.py` with bounded process counts, worker
  timeouts, output limits, exact package-target validation, optional-module
  detection, and file-write/network/subprocess/thread/logging side-effect
  checks.
- Added a required pinned Linux budget job and isolated measurements for every
  public submodule and installed optional integration.
- Added direct and subprocess tests for dependency isolation, lazy crypto
  behavior, export-map integrity, compatible root/static/chain access,
  registry exclusion, malformed benchmark inputs, and import side effects.
- Updated the README, long-form documentation, packaging metadata, and master
  plan. ORM implementation internals were not changed.

Local performance evidence:

- The pre-change root import measured about 895 ms median and approximately
  38 MiB additional maximum RSS while loading cryptography and SQLAlchemy.
- The final five-process Python 3.10.12 measurement reached 38.04 ms median
  and 84 KiB median incremental RSS with no optional modules or detected
  side effects.
- A separate nine-process enforcement run reached 48.94 ms median and 48 KiB
  median incremental RSS, passing the 100 ms and 10 MiB budgets.
- Five-process medians for every public submodule are recorded in
  `docs/masterplan.md`. With database and spreadsheet extras installed,
  `unicorefw.db` measured 1,164.34 ms and 86,816 KiB because that explicit
  submodule currently imports every available integration.

Verification:

- Full Python 3.10 suite: 1,678 passed and 15 skipped in 26.61 seconds.
- Combined statement/branch coverage reached 82.78%, satisfying the 82.5%
  ratchet and advancing toward the 100% target. The new package root and export
  registry reached 100%; `unicorefw/core.py` reached 82.97%.
- Bandit 1.9.4 reported no medium or high findings. Secret scanning,
  suppression-policy verification, fatal Flake8 checks, source compilation,
  workflow YAML parsing, and `git diff --check` passed.
- The isolated Python 3.10 database/spreadsheet environment resolved every
  declared dependency, passed `pip check`, imported every integration, and
  reported no known vulnerabilities under strict `pip-audit` with the patched
  CI tooling bounds.
- A clean PEP 517 sdist and wheel build passed Twine 6.2.0 strict validation
  and isolated wheel smoke verification. The artifacts contain the declarative
  export registry and import benchmark, and the wheel exposes the intended
  `core`, `crypto`, `orm`, `database`, and `spreadsheet` extras.

Compatibility impact: Intended root utility functions, public classes,
submodules, `UniCoreFW` static calls, `_` static calls, and crypto chaining
remain available. Accidental root re-exports of implementation imports such as
`typing.Any`, standard-library modules, and undeclared driver internals are
removed. Code that compared `unicorefw.__name__` to the incorrect
`"UniCoreFW"` value must use `unicorefw.DISPLAY_NAME`. Database and ORM
functions are no longer collection-chain methods.

#### 2026-07-28: PERF-002 linear collection paths

Status: Repository implementation complete; first pinned CI collection
benchmark execution pending

- Added one private stable-membership primitive with an expected O(1)
  hashable path and an equality-preserving unhashable fallback.
- Applied the primitive to `uniq`, `union`, `difference`, `intersection`,
  `xor`, keyed variants, duplicate detection, sorted uniqueness, `without`,
  `pull`, and `pull_all` variants without introducing global caches or I/O.
- Made common hashable uniqueness paths O(n) and common two-input set-like
  paths O(n + m). Multi-input `xor` processes cumulative intermediate results.
- Kept comparator variants pairwise and documented their quadratic cost.
  Unhashable values and derived keys remain quadratic in the worst case to
  preserve equality behavior.
- Replaced repeated front insertions in `take_right_while()` with append plus
  one reverse, and in `unshift()` with one in-place prefix slice update.
- Added `scripts/benchmark_collections.py` with bounded runs and input sizes,
  deterministic result validation, representative hashability/equality
  scenarios, and machine-readable output.
- Added deterministic operation-count tests so the expected linear hashable
  behavior is enforced independently of runner timing. Tests also cover mixed
  and unhashable values, unhashable keys, NaN identity, stable ordering,
  duplicate handling, mutation identity, predicate order, invalid benchmark
  budgets, and fail-closed benchmark validation.
- Added the five-run collection benchmark to an Ubuntu 24.04 and Python 3.11.9
  CI job. Updated public API documentation and `docs/masterplan.md`.

Local Python 3.10.12 algorithm-scaling evidence at a 4,000-item base size:

These ratios apply only to the large, representative collection workloads
below. They are not general `UniCoreFW.<api>` latency claims: the release
comparison benchmark uses small fixed fixtures and also includes the public
static-dispatch path. Use `scripts/benchmark_collections.py` to reproduce
these algorithm-level measurements.

- all-unique `uniq`: 40.065 ms to 1.255 ms, 31.9x faster;
- hashable custom-equality `uniq`: 1,276.221 ms to 2.602 ms, 490.5x faster;
- 8,000-item all-unique `union`: 161.946 ms to 2.716 ms, 59.6x faster;
- 8,000-item overlapping `intersection`: 61.886 ms to 3.631 ms, 17.0x faster;
- 8,000-item overlapping `xor`: 117.278 ms to 7.629 ms, 15.4x faster;
- full-match `take_right_while`: 3.031 ms to 0.382 ms, 7.9x faster;
- 4,000-value `unshift`: 2.866 ms to 0.060 ms, 47.8x faster.

The 1,000-item unhashable fallback measured 6.463 ms before and 7.857 ms
after, a 21.6% slowdown. This fallback intentionally prioritizes exact
equality compatibility. Large workloads should supply hashable values or
hashable derived keys.

Verification:

- Full Python 3.10 suite: 1,707 passed and 15 skipped in 26.12 seconds.
- Combined statement/branch coverage increased from 82.78% to 82.87%.
  `unicorefw/array.py` increased from 85.94% to 86.60%; every line and branch
  in the new membership and stable-uniqueness primitives is covered. The
  repository continues toward the 100% statement and branch target.
- Existing array compatibility suites and exhaustive local comparisons
  against pydash 8.0.6 matched for all integer arrays through length three and
  representative unhashable arrays.
- Bandit reported no medium or high findings. Secret scanning, suppression
  policy validation, fatal Flake8 checks, source compilation, formatting,
  workflow YAML parsing, and `git diff --check` passed.
- A clean PEP 517 sdist and wheel build passed Twine 6.2.0 strict validation
  and isolated wheel smoke verification. The source artifact contains the
  collection benchmark, performance tests, master-plan evidence, and
  changelog record.

Compatibility impact: First-occurrence order, `difference()` source
duplicates, non-mutation behavior, and in-place `unshift()` identity are
preserved. The legacy `union(iteratee=...)` keyword remains non-transforming;
callers should use `union_by()`. `xor()` and `xor_by()` now coalesce duplicate
contributors as their documented uniqueness contract requires. Operations
that previously rejected unhashable values or derived keys now support them.
Comparator variants retain their behavior and pairwise cost. Hashable custom
classes must honor Python's requirement that equal values have equal,
stable hashes.

#### 2026-08-01: Release benchmark registry repair

Status: Complete

- Added explicit, side-effect-bounded benchmark cases for `require_callable()`,
  `html_template()`, `unsafe_raw_sql()`, and `unsafe_raw_css()`.
- Kept the completeness audit strict: every local public callable must have
  exactly one benchmark or intentional skip entry.
- Preserved normal comparison behavior for older releases: an unavailable
  release API is recorded as `MISSING`; strict comparison mode remains
  fail-closed.
- Limited normalized unsafe SQL and CSS results to wrapper type names so the
  release report does not reproduce trusted raw content.

Verification:

- The exact release comparison completed under the available `python3`
  interpreter with all 365 local APIs accounted for, 354 APIs benchmarked on
  both sides, 11 intentional skips, and no failures or result mismatches.
- A dedicated older-release simulation verified all four absent APIs are
  reported as `MISSING` without terminating the worker.
- The three focused registry regression tests passed. The full suite passed
  1,765 tests and skipped 15 service/driver tests, reaching 83.27% combined
  statement/branch coverage against the 83.0% ratchet.
- Scoped Black, Black-compatible isort, fatal Flake8, source compilation, and
  `git diff --check` passed.

Compatibility impact: None. Benchmark coverage and reporting changed; runtime
library behavior and ORM internals are unchanged.

#### 2026-08-03: Pydash comparison benchmark

Status: Complete

- Reused the release benchmark's fixtures, validators, normalizers, cleanup,
  and timing engine without changing `scripts/benchmark_release.py`.
- Fixed the comparison contract to the 240 APIs verified against pydash 8.0.6.
  The baseline contains 273 shared callables, 33 shared but incompatible APIs,
  and 92 APIs unique to each package.
- Required pydash 8.0.6 by default. Callers may declare another exact expected
  version, but an override cannot add an unreviewed API to the fixed allowlist.
- Isolated pydash and UniCoreFW imports in separate child processes. The
  pydash worker removes project paths before import, rejects project-local
  shadow modules, and checks module, distribution, and expected versions.
- Bounded iterations to 1 through 1,000,000, repeats to 1 through 100, and
  worker duration to 1 through 3,600 seconds. Worker failure diagnostics retain
  at most the final 4 KiB from each output stream while reader threads drain
  the streams without accumulating unbounded parent-process buffers. POSIX
  timeouts terminate the worker process group; all platforms bound reader
  shutdown to prevent inherited pipes from bypassing the timeout.
- Made missing APIs, call failures, skips, result mismatches, timeouts, unsafe
  imports, malformed timings or versions, unexpected case identities, and
  result/API-inventory contradictions return nonzero. Exact selected-case and
  complete accounting checks remain mandatory. JSON reports use sibling
  temporary files, `fsync()`, and atomic replacement.
- Kept pydash out of runtime dependency metadata. CI pins pydash 8.0.6 only
  where Python 3.9 or newer can install it; older supported interpreters run
  the dependency-independent tests and skip the three installed-pydash checks.

Verification:

- A complete one-iteration, one-repeat comparison benchmarked all 240 selected
  APIs on both sides. It reported no missing APIs, failures, skips, or
  normalized-result mismatches.
- All 136 focused tests passed. `scripts/benchmark_pydash.py` reached 100%
  statement and branch coverage across 455 statements and 174 branches.
- The combined benchmark and release-script suite passed 155 tests. The full
  suite passed 1,901 tests and skipped 15 service/driver tests, reaching 83.31%
  combined coverage against the 83.0% ratchet.
- Black, Black-compatible isort, fatal Flake8, source compilation, and
  `git diff --check` passed. Detect-secrets found no candidates. Bandit found
  no medium or high issues; its two low findings describe the required
  subprocess import and the fixed argument-array call with no shell.

Compatibility impact: None. The change adds development tooling and tests. It
does not change runtime dependencies, public APIs, release benchmarking,
database behavior, generated registries, or ORM internals.

#### 2026-08-05: Generated registry distribution build hook

Status: Complete

- Registered a dedicated setuptools `generate_core_registry` command and made
  both `build_py` and `sdist` run it before copying package modules or creating
  the source archive. Standard PEP 517 wheel and source builds therefore
  regenerate `_exports.py`, `_core_registry.py`, and API metadata automatically.
- Invoked the generator with the active interpreter in isolated mode, a fixed
  script path and working directory, `shell=False`, and a 120-second timeout.
  Nonzero exits, timeouts, and process-start failures stop the build with
  sanitized errors that do not reproduce command arguments or filesystem
  details.
- Kept metadata preparation lightweight: `setup.py` continues to read only
  `_metadata.py` with `run_path()`. Generation begins at the distribution
  command boundary, not during metadata queries or ordinary package imports.

Verification:

- All 6 build-hook tests passed and `setup.py` reached 100% statement/branch
  coverage across 36 statements. The 51-test packaging and registry suite
  passed.
- The complete suite passed 1,918 tests and skipped 15 service/driver tests,
  retaining 83.31% combined coverage against the 83.0% repository ratchet.
- An isolated `python -m build` visibly ran `generate_core_registry` before both
  `sdist` and `build_py`. Twine strict validation, isolated wheel smoke checks,
  and byte-for-byte comparison of both distributions' generated declarations
  passed.
- Generated-file drift, scoped Black, Black-compatible isort, fatal Flake8,
  source compilation, Python 3.7 grammar parsing, and `git diff --check` passed.
  Bandit's only findings were the two expected low-severity warnings for the
  fixed, isolated, no-shell subprocess invocation; no medium or high findings
  were reported.

Compatibility impact: None. Runtime dependencies, public APIs, generated API
ownership, import behavior, and ORM internals are unchanged. Distribution
builds now fail instead of packaging incomplete declarations when generation
cannot complete safely.

#### 2026-08-05: Repository script operational guides

Status: Complete

- Added one task-focused guide for each of the ten executable Python scripts
  in `scripts/`. Each guide documents purpose, requirements, safe commands,
  exact options and limits, output and exit behavior, operational safeguards,
  and failure diagnosis from the implementation.
- Documented permissive and strict benchmark behavior separately, including
  uncapped release-benchmark workloads, pydash worker bounds, isolated import
  controls, generated-registry write behavior, release artifact checks, and
  governed security suppressions.
- Added an inventory contract that derives required guide names from
  `scripts/*.py`, excludes only package infrastructure, and rejects missing,
  incomplete, or orphaned `docs/guide_<script>.md` files.
- Added the per-script guide requirement to the master plan. The existing
  documentation manifest includes every guide in source distributions.

Verification:

- The focused guide contract passed 2 tests. The combined release-script and
  guide suite passed 18 tests.
- A clean PEP 517 source-distribution build ran registry generation and the
  resulting archive contained all ten guide files.
- The complete suite passed 1,920 tests and skipped 15 service or optional
  integration tests in 45.01 seconds.
- Generated registry drift and `git diff --check` passed.

Compatibility impact: None. This slice adds documentation and its inventory
test. Runtime code, APIs, dependencies, generated ownership, benchmark
semantics, release behavior, and ORM internals are unchanged.

#### 2026-08-04: PERF-003 automatic public-function discovery

Status: Complete

- Replaced the 452-name manual export declaration with a generated package-root
  declaration. A module-owned top-level function or public alias is now
  discovered when its name does not begin with `_`; adding `reduce_top()` to
  `array.py`, for example, requires no edit to an export list.
- Moved the remaining build-time decisions to the dependency-free
  `unicorefw/_export_policy.py`: public module order, non-function and imported
  compatibility exports, `max`/`min` aliases, lazy-module classification, and
  exact approved name collisions.
- Kept runtime imports reflection-free. Trusted core namespaces are inspected
  only by the generator, while database, ORM, and supporter functions use
  conservative source-level final-binding analysis. Public aliases are kept,
  but rebinding, deletion, and ambiguous conditional bindings cannot leave a
  stale export; decorated public definitions fail generation because their
  runtime type cannot be proven without execution. The generated
  `unicorefw/_exports.py`, `unicorefw/_core_registry.py`, and API metadata use
  fixed paths and atomic drift-managed writes.
- Made collision changes fail closed. A new collision, changed owner tuple, or
  stale collision approval stops generation before root ownership can change
  silently.

Verification:

- Confirmed the generated 452 module exports, 444 unique root names and owners,
  350 eager core functions, and 365 static exports exactly match the previous
  compatibility surface.
- All 65 focused registry, dispatch, and import tests passed. The generator,
  policy, generated declarations, package root, and core dispatch reached 100%
  statement and branch coverage across 532 statements and 170 branches.
- The complete suite passed 1,912 tests and skipped 15 service/driver tests,
  reaching 83.31% combined statement/branch coverage against the 83.0%
  ratchet.
- Seven-run, 100,000-call local medians measured 114.482 ns for static dispatch,
  121.887 ns for factory-static dispatch, and 3,148.090 ns for the five-step
  chain. Nine isolated root imports measured a 42.203 ms and 304 KiB median,
  with no optional imports or detected side effects. These local values are
  regression evidence, not cross-host performance guarantees.
- Generated-file drift, scoped Black, Black-compatible isort, fatal Flake8,
  source compilation, Python 3.7 grammar parsing, and `git diff --check` passed.
  Bandit reported no findings in the changed executable files.

Compatibility impact: None for the current release: public names and owners are
unchanged. For future implementation changes, every module-owned top-level
function whose name does not begin with `_` is intentionally public. Internal
helpers must use an underscore-prefixed name. ORM implementation internals were
not changed.

#### 2026-07-29: PERF-003 generated dispatch registry

Status: Repository implementation and local release verification complete;
first pinned CI benchmark execution pending

- Added a deterministic generator for the compact runtime registry and a
  365-record build-time API metadata manifest. The generator uses fixed output
  paths, atomic replacement, cross-process-stable signature rendering, and a
  read-only drift mode. Source distributions now include the generated API
  metadata.
- Replaced `inspect.getmembers()` module scans with 350 declared core function
  records. Of those, 348 accept a wrapped positional input. Lazy
  `encrypt_string()` and `decrypt_string()` retain chain compatibility.
- Replaced package-factory `dir()` scanning with the generated static name
  declaration.
- Bound eager wrapper closures directly to their target callable and removed
  one `_apply_callable()` frame from each eager chain step.
- Preserved direct, `UniCoreFW`, and `_` factory-static callable identity,
  metadata, historical first-owner collisions, `max` and `min` aliases, and
  static database and ORM proxies.
- Made `now()`, `noop()`, and `generate_key()` static-only. Calling them as
  wrapper methods previously injected the wrapped value and raised
  `TypeError`; wrapper attribute access now raises `AttributeError`.
- Left ORM implementation internals unchanged.

Local Python 3.10.12 medians use seven runs of 100,000 calls, except the
nine-run cold import:

| Scenario | Before | After | Change |
|---|---:|---:|---:|
| Direct call | 164.116 ns | 185.963 ns | 13.31% slower |
| `UniCoreFW` static call | 152.526 ns | 186.908 ns | 22.54% slower |
| `_` factory-static call | 161.056 ns | 149.106 ns | 7.42% faster |
| Five-step chain | 4,930.602 ns | 4,150.976 ns | 15.81% faster |
| Cold `unicorefw.core` import | 206.092 ms | 314.536 ms | 52.62% slower |

The unchanged direct-call control also moved by more than 10%, showing
material host-frequency noise in these nanosecond samples. Cold-import
profiling was dominated by source-file operations and implementation-module
imports on the WSL checkout; generated registry construction was
approximately 6 ms. These regressions are recorded rather than discarded.
The five-step chain improved after removing one eager dispatch frame per
step. The separately enforced root import passed at a 55.139 ms and 328 KiB
median with no optional imports or side effects. The pinned Ubuntu
24.04/Python 3.11.9 job remains the authoritative stable-runner benchmark.

Verification evidence:

- 1,762 tests passed and 15 service/driver tests skipped. The complete suite
  reached 83.27% combined coverage, 85.75% statement coverage, and 77.11%
  branch coverage; the ratchet increased from 82.5% to 83.0%.
- The 74-test focused dispatch/generator/import suite reached 100% statement
  and branch coverage for `unicorefw/__init__.py`, `unicorefw/core.py`,
  `unicorefw/_core_registry.py`, `scripts/generate_core_registry.py`, and
  `scripts/benchmark_dispatch.py`.
- Bandit reported no medium or high findings, all 18 scoped suppressions
  validated, and the exact detect-secrets 1.5.0 scan found no candidate
  secrets.
- Generated-file drift, fatal Flake8, PERF-003-scoped Black and
  Black-compatible isort, source compilation, and `git diff --check` passed.
  Repository-wide default Black/isort checks still expose unrelated legacy
  formatting drift, including the intentionally deferred ORM module; this
  slice did not rewrite those files.
- A clean PEP 517 source distribution and wheel passed Twine 6.2.0 strict
  validation, wheel path/content inspection, isolated installation,
  dependency validation, and direct/static/chain/static-only API smoke
  checks.

Compatibility impact: Valid direct, static, factory-static, and collection
chain calls remain available. Code that tested for or invoked
`UniCoreFWWrapper.now`, `UniCoreFWWrapper.noop`, or
`UniCoreFWWrapper.generate_key` must use the static surface because those
functions accept no wrapped input.

## [1.1.5] - 2026-07-22

### Security

- Replaced unsafe SQL dump literals with SQLite-native quoting and staged restore.
- Added validated query construction and explicit trusted SQL/CSS escape hatches.
- Added HTML, spreadsheet, template, and structured audit-output protections.
- Added hard-capped resource budgets for decompression, templates, database
  imports, spreadsheet ZIP expansion, SQL scripts, and backup restore.
- Added bounded regex, nested-path, memoization, query-cache, debounce, and
  deferred-timer policies with hard safety ceilings.
- Replaced password-based release publication with gated PyPI trusted publishing.
- Pinned the audited Python 3.10+ CI and release toolchain to patched pip,
  pytest, and setuptools versions.

### Changed

- SQLite restore preserves populated targets unless destructive replacement is
  explicitly authorized.
- Database query export now requires either a validated table name or an
  `unsafe_raw_sql()` query.
- Resource exhaustion raises `ResourceLimitError`; invalid limit settings raise
  `InputValidationError`.
- Caller-supplied regular expressions now use a conservative structural policy;
  reviewed complex expressions require an explicit `unsafe_raw_regex()` marker.
- Memoization and query caches now use monotonic TTL expiry and LRU entry and
  estimated-weight limits.
- CI now measures branch coverage in one dedicated job and rejects regressions
  below the recorded ratchet. The completion target is 100% statement and branch
  coverage.

### Optimization record

Current stage: Phase 0 and Phase 1 in progress. The detailed roadmap lives in
[docs/masterplan.md](docs/masterplan.md).

#### 2026-07-18: Repository audit

Status: Complete

- Inventoried package, test, workflow, documentation, example, and packaging
  files.
- Confirmed a clean starting worktree on `main` at revision `63b650c`.
- Parsed all 143 tracked Python files.
- Ran the full local test suite: 1,321 tests passed in 15.18 seconds.
- Found that CI omitted the string and type suites and lacked direct database,
  ORM, and crypto coverage.
- Ran Bandit across `unicorefw`: 0 high, 1 medium, and 10 low findings.
- Ran the fatal Flake8 selection with 0 findings. Full Flake8 reported 1,555
  findings.
- Ran Black and isort checks. Black would reformat 26 files; isort reported
  import-order failures across package and test files.
- Ran `setup.py check --strict`; metadata passed with a setuptools
  license-classifier deprecation warning.
- Ran the Markdown doctest command and parsed the Python AST without an error.

#### 2026-07-18: Security and correctness review

Status: Complete

The review verified these release-blocking defects:

- SQL dump and backup functions did not escape stored values. A proof value
  produced an executable `DROP TABLE` statement in the dump.
- QueryBuilder accepted raw ordering and limit fragments, and `drop_table()`
  skipped identifier validation.
- HTML export did not escape headers or cells.
- CSV and Excel exports did not handle formula-leading cells.
- Template interpolation lacked an HTML auto-escaping mode.
- Audit logging permitted CR/LF log forging and lacked a hardened file sink.
- The release workflow could publish an artifact without the full suite or a
  clean-wheel test.

The review also verified these stability defects:

- `session_scope()` returned an async generator without the async
  context-manager interface shown in its documentation.
- Direct package exports and static/factory exports selected different
  functions for `invoke`, `now`, `map_`, and `max_value`.
- The package overwrote its `__name__` with `"UniCoreFW"`.
- Backup and restore paths could report success for unsupported combinations,
  and restore cleared existing SQLite tables by default.
- Database, ORM, and crypto modules lacked active direct tests.

#### 2026-07-18: Performance sampling

Status: Planning sample complete; formal benchmark baseline pending

Local Python 3.10.12 results:

| Sample | Result |
|---|---:|
| Cold `import unicorefw` | 0.94 to 0.99 seconds |
| Import maximum RSS delta | about 28,924 KiB |
| `uniq(range(10_000))` | 0.398 seconds |
| `union(range(10_000))` | 0.384 seconds |
| `intersection(range(5_000), range(5_000))` | 0.196 seconds |

The import loaded installed SQLAlchemy and cryptography stacks. The collection
samples confirmed quadratic membership paths. These one-shot samples guide
prioritization and do not set release thresholds.

#### 2026-07-18: Planning deliverables

Status: Complete

- Created `docs/masterplan.md` with prioritized findings, work packages,
  acceptance gates, release strategy, and the first implementation slice.
- Applied the decision order: Security, Performance, Stability, Scalability,
  Sustainability.
- Made no production-code, workflow, dependency, or packaging change during
  the planning slice.

#### 2026-07-18: SEC-001 remediation

Status: Complete

- Replaced hand-built SQL values with SQLite-native literal quoting in
  single-table export.
- Replaced full SQLite backup generation with a committed in-memory snapshot
  and `iterdump()`.
- Added atomic mode-0600 backup writes on POSIX.
- Added a versioned JSON backup envelope with lossless SQLite byte encoding.
- Changed restore to preserve populated targets by default.
- Required `clear_existing=True` and `allow_destructive=True` for target
  replacement.
- Added an isolated staging-database restore before target replacement.
- Denied SQLite file attachment and writable-schema pragmas during staged SQL
  restore.
- Added uncompressed byte and gzip expansion-ratio limits.
- Removed plaintext backup files after compressed output completed.
- Rejected unsupported formats and non-SQLite backup engines with explicit
  errors.
- Replaced semicolon splitting in SQLite SQL import with `executescript()` and
  a byte limit.
- Routed `drop_table()` through identifier validation and dialect-aware
  quoting.
- Added 15 database regression tests for adversarial values, binary data,
  compression limits, cleanup, destructive authorization, legacy JSON,
  unsupported operations, identifier injection, attachment denial, committed
  snapshots, and file permissions.

Compatibility changes:

- `BackupRestore.restore()` now defaults to `clear_existing=False`.
- A populated target requires explicit destructive authorization.
- Backup and SQL-script import reject non-SQLite engines until a native
  implementation exists.
- SQL backup and export reject uncommitted source state instead of producing an
  uncertain snapshot.
- Version 1 JSON backups preserve bytes through tagged base64 values and retain
  read compatibility with legacy JSON backups.

Verification:

- Focused database suite: 15 passed.
- Full suite: 1,336 passed in 15.29 seconds.
- Bandit: 0 high, 1 medium, and 10 low findings. The new backup code added no
  finding.
- Fatal Flake8 selection: 0 findings.
- Python AST parsing: 144 files parsed.

#### 2026-07-18: SEC-002 remediation

Status: Complete

- Replaced QueryBuilder raw structural concatenation with dialect-aware,
  validated quoting for fields, tables, joins, grouping, and ordering.
- Constrained ordinary WHERE and HAVING clauses to one simple predicate with
  bound parameters; reviewed complex expressions require `unsafe_raw_sql()`.
- Normalized SQLite and PostgreSQL/MySQL placeholders without interpolating
  values.
- Restricted join types and sort directions to allowlists.
- Enforced configurable upper bounds on LIMIT and OFFSET and rejected booleans,
  negative values, and SQL-shaped strings.
- Replaced exporter table/query guessing with validated table names or an
  explicit trusted-query wrapper.
- Added atomic owner-only writes to JSON, CSV, and HTML export paths.
- Replaced the query-cache MD5 digest with SHA-256, removing the remaining
  medium-severity Bandit finding.
- Added adversarial query-builder and exporter regression coverage for each
  identifier and structural input boundary.

Compatibility changes:

- Raw QueryBuilder fragments now fail closed. Callers must use structured
  fields and predicates or mark reviewed SQL with `unsafe_raw_sql()`.
- Exporter strings represent table names. Raw query strings no longer pass a
  whitespace heuristic.
- LIMIT and OFFSET default to a maximum of 1,000,000; callers can configure
  lower or higher positive bounds within the hard ceiling.

#### 2026-07-18: SEC-003 remediation

Status: Complete

- Escaped HTML export headers and cells with context-appropriate entity
  encoding.
- Required `unsafe_raw_css()` for reviewed custom stylesheets.
- Neutralized formula-leading CSV and Excel text by default, including leading
  whitespace and control-character cases. `spreadsheet_safe=False` preserves
  exact strings.
- Added `html_template()` for untrusted values in HTML text nodes and rejected
  interpolation inside tags, attributes, scripts, and styles.
- Kept `template()` as a plain-text renderer for compatibility.
- Replaced line-oriented audit strings with one structured JSON event per call.
- Added standard-library logging integration and a mode-0600 file sink that
  refuses symbolic links where `O_NOFOLLOW` exists.
- Added injection regression tests for HTML, CSS trust, CSV/Excel formulas,
  HTML-template contexts, audit-log forging, file permissions, and symlinks.

Local verification exercised each new output boundary except Excel. That test
skipped because pandas was absent. The required Linux CI integration job
installs pandas and openpyxl.

#### 2026-07-18: SEC-004 release hardening

Status: Repository implementation complete; external activation pending

- Made the cross-platform test workflow reusable by the release workflow and
  replaced fragmented coverage runs with one full-suite run.
- Added a required optional-output job for pandas/openpyxl, Bandit high/medium
  rejection, and dependency vulnerability auditing.
- Pinned each GitHub Action to a verified 40-character commit SHA and disabled
  checkout credential persistence.
- Split quality, build, and publish into separate least-privilege jobs.
- Replaced `setup.py` builds with isolated PEP 517 builds and removed package
  imports from build metadata evaluation.
- Added semantic tag, package-version, and changelog agreement checks.
- Added wheel path inspection, clean-venv installation, import smoke testing,
  `pip check`, strict Twine validation, SHA-256 checksums, a release manifest,
  and a CycloneDX SBOM.
- Replaced long-lived PyPI credentials with an environment-scoped OIDC publish
  job. The publishing action generates provenance attestations.
- Added structural tests that reject floating actions and password-based PyPI
  credentials in the release workflow.

Local artifact verification:

- An isolated PEP 517 build produced one wheel and one source distribution.
- The wheel passed path/content inspection, clean-venv installation, isolated
  import, behavioral smoke testing, and `pip check`.
- Twine 6.2.0 passed both artifacts in strict mode.
- The release manifest and CycloneDX JSON parsed and matched the built artifact
  hashes.

External work required before publication:

- Configure the protected `pypi` GitHub environment with maintainer approval.
- Register the workflow and environment as the `unicorefw` trusted publisher
  on PyPI.
- Run one non-production release-candidate rehearsal and verify its generated
  attestations before creating a production tag.

#### 2026-07-18: Consolidated verification

Status: Complete for SEC-001 through SEC-004

- Full local suite: 1,380 passed and 1 optional Excel test skipped in 12.72
  seconds.
- Bandit release gate: 0 high and 0 medium findings.
- Fatal Flake8 selection: 0 findings.
- Focused changed files passed Black and isort checks.
- `git diff --check` passed.

#### 2026-07-20: SEC-005A content-expansion and import budgets

Status: Complete

- Added `ResourceLimitError` with resource, limit, and observed-value fields.
- Added shared validation for positive integer and ratio settings with hard
  safety ceilings. Invalid and non-finite settings raise `InputValidationError`
  before work starts.
- Capped run-length decompression input, output, and expansion ratio. The count
  parser rejects oversized runs before allocating the repeated string.
- Added immutable `TemplateLimits` for source length, token count, conditional
  depth, output length, and context item count.
- Replaced repeated template string concatenation with bounded list assembly.
- Kept HTML interpolation context validation linear as token counts grow.
- Kept script and style contexts active until their matching closing tags when
  attacker-authored markup contains a different raw-text tag.
- Added byte, row, column, and batch limits to JSON and CSV imports.
- Made CSV byte counting part of the decoding stream and confirmed transaction
  rollback when a later row exceeded the budget.
- Added workbook byte, row, column, ZIP member, expanded-byte, and
  expansion-ratio limits to Excel import.
- Passed one bounded workbook snapshot to ZIP validation and pandas, preventing
  file replacement between validation and parsing.
- Added row and column limits to dictionary import.
- Added hard ceilings to SQL script input and backup restore expansion settings.
- Added the resource-limit suite to the required pandas/openpyxl CI job.

Compatibility changes:

- `decompress()` defaults to 1,000,000 output characters and a 100:1 ratio.
- Templates retain their 10,000-character source default and cap tokens,
  nesting, context items, and output.
- JSON, CSV, and Excel imports default to 64 MiB, 100,000 rows, and 1,000
  columns.
- Excel imports parse from an in-memory snapshot bounded by `max_bytes`.
- Callers can lower or raise defaults within hard ceilings. Request data must
  not control these settings.

Verification:

- Resource-limit suite: 18 passed and 1 Excel test skipped because pandas was
  absent.
- Full local suite: 1,400 passed and 2 optional Excel tests skipped in 10.30
  seconds.
- Existing database, template, output-security, and utility suites passed.
- Bandit reported 0 medium and 0 high findings. Fatal Flake8, compilation,
  Black, isort, and `git diff --check` gates passed.
- The wheel passed path inspection, clean-environment installation, isolated
  import, behavioral smoke testing, and `pip check`. Twine 6.2.0 accepted the
  wheel and source distribution in strict mode.

#### 2026-07-20: Coverage baseline and CI ratchet

Status: Baseline complete; 100% target in progress

- Confirmed pytest-cov 7.1.0 and coverage.py in the local environment.
- Ran all tests with statement and branch measurement: 1,400 passed and 2
  optional Excel tests skipped in 27.83 seconds.
- Measured 73.29% total coverage in branch mode. Statement coverage measured
  76.44%; branch coverage measured 65.81%.
- Recorded 1,240 uncovered statements and 759 uncovered branches.
- Added shared coverage.py settings to `pyproject.toml` with branch measurement,
  relative paths, missing-line output, and XML/JSON reports.
- Added one Linux/Python 3.11 coverage job with spreadsheet dependencies and a
  73% no-regression gate. The cross-platform matrix runs functional tests
  without duplicate coverage reports.
- Added a workflow regression test that requires branch mode, terminal, XML,
  and JSON reports, plus a coverage threshold from 73% through 100%.
- Re-ran the configured gate after adding its regression test: 1,401 passed, 2
  optional Excel tests skipped, and the 73% threshold passed at 73.29%.

Coverage policy:

- New and changed reachable code requires statement and branch tests.
- Each coverage slice raises the global ratchet to its verified result.
- Completion requires 100% statement and branch coverage across core and
  maintained optional integrations.
- A maintainer must document each exclusion. Exclusions may cover unreachable
  platform guards or defensive assertions, not untested behavior.

#### 2026-07-20: SEC-005B bounded state and execution policies

Status: Complete

- Replaced the unbounded `memoize()` dictionary with a thread-safe LRU bounded
  by entry count, estimated key/result weight, and monotonic TTL. Added cache
  inspection and clearing controls.
- Replaced the query cache's unbounded dictionary and wall-clock expiry with an
  isolated-copy LRU using monotonic TTL, entry, and estimated-weight budgets.
- Length-framed the query and parameter inputs before SHA-256 key generation so
  distinct input boundaries cannot produce the same byte stream.
- Added source-length, segment-depth, and auto-created-list budgets to nested
  paths. Mutating paths are checked before container allocation.
- Added per-wrapper debounce timer budgets and a process-wide deferred-timer
  budget. Reservations are released after callback completion, cancellation,
  or thread-start failure.
- Added `cancel()` and `pending_timer_count()` controls to debounced wrappers.
- Routed public caller-supplied regex helpers and custom boolean patterns through
  bounded input, pattern, group, quantifier, and repeat policies.
- Rejected backreferences, special groups, nested repetition, adjacent
  repetition, and repeated ambiguous groups by default. Added
  `unsafe_raw_regex()` as a visible trust boundary for reviewed patterns.
- Fixed query-cache clearing to use `OrderedDict.clear()`. Calling the base
  `dict.clear()` descriptor left the ordering links inconsistent and caused a
  later `KeyError`.

Compatibility changes:

- `memoize()` defaults to 256 entries, 16 MiB estimated weight, and a 300-second
  TTL. It still accepts positional arguments and returns the cached object by
  identity.
- `CacheManager` uses the same defaults and returns deep-copied cached values.
  Applications must call `clear()` after writes that invalidate a query.
- Nested paths default to 4,096 source characters, 64 segments, and 10,000
  auto-created list items. Large numeric segments in mutating paths now fail
  before mutation.
- Regex helpers default to 10,000 input characters and 512 pattern characters.
  Existing complex patterns may require simplification or an explicit trusted
  wrapper. The wrapper does not remove input and pattern length limits.
- Debounced wrappers default to eight pending timers. Saturation raises
  `ResourceLimitError`; primary `debounce()` callback exceptions remain
  suppressed for compatibility.

Verification:

- Resource and security coverage suites: 44 passed and 1 optional Excel test
  skipped.
- `security.py`, `template.py`, and `regex_policy.py` each reached 100% statement
  and branch coverage.
- Full coverage run: 1,427 passed and 2 optional Excel tests skipped in 31.13
  seconds. Combined statement-and-branch coverage reached 75.97%; statement
  coverage reached 78.79% and branch coverage reached 69.14%.
- The run recorded 1,209 uncovered statements and 727 uncovered branches. The
  CI no-regression threshold increased from 73% to 75%.
- Bandit reported no medium or high findings. Fatal Flake8, compilation,
  focused Black/isort, and `git diff --check` gates passed.

#### 2026-07-21: Release metadata Python compatibility

Status: Complete

- Replaced `Path.write_text(..., newline="\n")` in release metadata generation.
  Python 3.7 through 3.9 do not accept the `newline` argument on
  `Path.write_text()` even though the package declares support for those
  versions.
- Added one UTF-8 text writer based on `Path.open()`, whose newline interface is
  available across the declared Python range.
- Preserved deterministic LF output for `SHA256SUMS` on Windows and POSIX.
- Added a regression test that disables `Path.write_text()` during metadata
  generation and checks the checksum file's raw line endings.
- Added `scripts/__init__.py` so an installed third-party package named
  `scripts` cannot shadow the repository's release helpers on Python 3.8.
- Excluded the repository release-helper package from wheel discovery and made
  wheel inspection reject release tooling if packaging configuration regresses.

Verification:

- Release-script suite on Python 3.8: 9 passed.
- Full Python 3.8 suite: 1,428 passed and 2 optional Excel tests skipped in
  25.30 seconds. The Python 3.10 suite produced the same result in 21.52
  seconds.
- An isolated source and wheel build passed. Python 3.8 wheel inspection
  confirmed that the wheel excludes repository release tooling.
- Python 3.11 compiled the release metadata script. Fatal Flake8 passed for the
  changed script and test.

#### 2026-07-21: Bandit 1.9.4 SQL construction review

Status: Complete

- Reproduced all 11 B608 findings with Bandit 1.9.4.
- Verified that each reported query routes table and column identifiers through
  `_qtable()` or `_qident()`. Those functions enforce the identifier allowlist
  before dialect-specific quoting.
- Verified that insert, update, delete, and migration values remain DB-API bound
  parameters. SQL export obtains row literals from SQLite `quote()` rather than
  formatting caller values.
- Added a scoped `# nosec B608` to each reviewed construction site. Every
  suppression has an adjacent rationale, and a structural test rejects blanket
  or undocumented B608 suppressions.
- Added adversarial tests for table names, column names, update values, and
  delete predicates. The tests confirm that identifier attacks fail before
  execution and SQL-shaped values remain data.

Verification:

- Bandit 1.9.4 completed with 0 medium and 0 high findings. The report records
  11 reviewed B608 suppressions.
- Focused database security suite on Python 3.8 and 3.10: 45 passed on each
  interpreter.
- Full branch-coverage run: 1,431 passed and 2 optional Excel tests skipped in
  41.11 seconds. Combined coverage reached 76.36%; statement coverage reached
  79.15% and branch coverage reached 69.61%.
- The CI coverage threshold increased from 75% to 76%.

#### 2026-07-21: Patched CI and build toolchain

Status: Complete

- Raised Python 3.10+ test jobs from pytest 8.4.2 to pytest 9.0.3 or later,
  addressing PYSEC-2026-1845.
- Raised the Python 3.10+ build backend and security job to setuptools 83.0.0
  or later, addressing PYSEC-2026-3447.
- Added a pip 26.1.2 upgrade before dependency installation in every Python
  3.10+ test, lint, coverage, security, and release-build job. This also keeps
  the installer itself inside the strict dependency audit.
- Kept Python 3.8 and 3.9 on compatible pytest, pip, and setuptools lines by
  using Python-version markers. Package runtime support and public imports are
  unchanged.
- Directed every CI pytest invocation to a job-owned base temporary directory.
  This avoids the shared `/tmp/pytest-of-{user}` path in legacy pytest releases
  that cannot install the Python 3.10+ fix.
- Updated the coverage plugin to pytest-cov 7.x and raised the verified branch
  coverage ratchet from 76% to 77%.
- Added workflow regression coverage for the patched versions, compatibility
  markers, release-job installer upgrade, private pytest base directory, and
  strict audit command.

Compatibility boundary:

- pytest 9.0.3, setuptools 83.0.0, and pip 26.1.2 require Python 3.10 or later.
  Python 3.8 and 3.9 therefore retain their existing compatible tooling. Their
  CI runs use an isolated base temporary directory as a defense for the pytest
  issue; a fully patched legacy dependency set requires an upstream backport or
  removal of those interpreter jobs.

Verification:

- `python -m pip_audit --strict` against the exact Python 3.11 security-job
  environment reported no known vulnerabilities.
- Python 3.11 with pytest 9.1.1: 1,434 tests passed in 20.25 seconds.
- The exact pytest-cov 7.1.0 branch-coverage command passed 1,434 tests in 56.92
  seconds and measured 77.39% combined coverage.
- Python 3.8 with pytest 8.4.2: 1,432 tests passed and 2 optional tests skipped
  in 25.09 seconds.
- Bandit 1.9.4 reported no medium or high findings. Workflow YAML parsing,
  release-script tests, and `git diff --check` passed.

### Current optimization status

| Phase | Scope | Status | Exit evidence |
|---|---|---|---|
| 0 | Containment and reproducible baseline | In progress | Full CI suite, API manifest, coverage, benchmark, artifact baseline, publication gate |
| 1 | Security remediation | In progress | SEC-001 through SEC-003 and SEC-005 through SEC-008 repository-complete; SEC-004 external OIDC activation pending |
| 2 | Performance remediation | In progress | PERF-001 and PERF-002 repository-complete; wrapper dispatch, streaming/bulk paths, and hosted benchmark execution remain |
| 3 | Stability and API repair | In progress | Unified exports, database/ORM matrix, deterministic concurrency, type ratchet |
| 4 | Scalability | Pending | Bounded pools/caches, streaming backpressure, large-data tests |
| 5 | Sustainability and UX | Pending | Modern packaging, enforced quality gates, generated docs, governance files |

#### Audit limitations

- Local tests exercise PostgreSQL, MySQL, and Redis through opt-in suites, but
  this checkout had no local services. Required digest-pinned CI jobs supply
  all three engines. MongoDB still requires a service-backed integration job.
- Sync SQLite now exercises SQLAlchemy session configuration and lifecycle.
  Async and network-database engines still need service-backed integration.
- The initial repository audit used no network access. The patched Python 3.11
  CI environment later passed a live strict dependency audit; third-party
  action release verification remains a separate maintenance task.
- Import measurements now use isolated repeated processes; their first pinned
  hosted CI execution remains pending. Collection measurements now use bounded
  repeated workloads; other algorithm and database paths still require the
  same representative treatment.
- The repository contains no product or documentation-site UI source. The audit
  covered developer UX in code and Markdown.

#### Next action

- Run the new PostgreSQL, MySQL, Redis, CodeQL, and performance jobs, then
  begin PERF-003 without changing ORM internals. Preserve the 82.5% coverage
  ratchet while adding meaningful tests toward 100% statement and branch
  coverage.
- Keep publication paused until maintainers rehearse the protected PyPI OIDC
  and provenance path.

[Unreleased]: https://github.com/unicorefw-org/unicorefw-py/compare/v1.1.5...HEAD
[1.1.5]: https://github.com/unicorefw-org/unicorefw-py/compare/v1.1.4...v1.1.5
