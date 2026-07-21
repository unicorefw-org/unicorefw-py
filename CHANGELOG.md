# Changelog

All notable changes to UniCoreFW are recorded here. The project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Each implementation slice must record its behavior changes, compatibility
impact, and verification evidence in this file.

## [Unreleased]

### Security

- Replaced unsafe SQL dump literals with SQLite-native quoting and staged restore.
- Added validated query construction and explicit trusted SQL/CSS escape hatches.
- Added HTML, spreadsheet, template, and structured audit-output protections.
- Added hard-capped resource budgets for decompression, templates, database
  imports, spreadsheet ZIP expansion, SQL scripts, and backup restore.
- Added bounded regex, nested-path, memoization, query-cache, debounce, and
  deferred-timer policies with hard safety ceilings.
- Replaced password-based release publication with gated PyPI trusted publishing.

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

### Current optimization status

| Phase | Scope | Status | Exit evidence |
|---|---|---|---|
| 0 | Containment and reproducible baseline | In progress | Full CI suite, API manifest, coverage, benchmark, artifact baseline, publication gate |
| 1 | Security remediation | In progress | SEC-001 through SEC-003 and SEC-005 complete; SEC-004 external OIDC activation pending |
| 2 | Performance remediation | Pending | Lazy core import, complexity targets, streaming/bulk paths, benchmark gates |
| 3 | Stability and API repair | Pending | Unified exports, database/ORM matrix, deterministic concurrency, type ratchet |
| 4 | Scalability | Pending | Bounded pools/caches, streaming backpressure, large-data tests |
| 5 | Sustainability and UX | Pending | Modern packaging, enforced quality gates, generated docs, governance files |

#### Audit limitations

- Local tests did not exercise PostgreSQL, MySQL, MongoDB, Redis, pandas, or
  openpyxl. The required CI output-integration job installs pandas and openpyxl;
  service-backed database jobs remain pending.
- Installed SQLAlchemy and cryptography packages allowed import-boundary and
  ORM-shape inspection without service-backed integration testing.
- The audit used no network access, so it did not query live vulnerability
  databases or verify current third-party action releases.
- Import and algorithm measurements used local one-shot samples. Phase 0 must
  replace them with isolated, repeated benchmarks.
- The repository contains no product or documentation-site UI source. The audit
  covered developer UX in code and Markdown.

#### Next action

- Continue the coverage campaign from the 75% ratchet, prioritizing crypto,
  database error paths, and maintained optional integrations.
- Keep publication paused until maintainers rehearse the protected PyPI OIDC
  and provenance path.

[Unreleased]: https://github.com/unicorefw-org/unicorefw-py/compare/v1.1.4...HEAD
