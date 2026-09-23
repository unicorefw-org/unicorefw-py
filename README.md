<p align="center">
  <img src="https://unicorefw.org/static/assets/images/icon.png?v=1.1.3" alt="UniCoreFW logo" />
</p>

[![Publish to PyPi](https://github.com/unicorefw-org/unicorefw-py/actions/workflows/release.yml/badge.svg)](https://pypistats.org/packages/unicorefw)
[![Unit Tests](https://github.com/unicorefw-org/unicorefw-py/actions/workflows/tests.yml/badge.svg)](https://github.com/unicorefw-org/unicorefw-py/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/unicorefw-org/unicorefw-py/branch/main/graph/badge.svg)](https://codecov.io/gh/unicorefw-org/unicorefw-py)
[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/downloads/)

# UniCoreFW

**Universal Core Utility Library (Python)**

UniCoreFW is a compact, batteries-included utility library that provides chainable and static helper functions across arrays (lists), objects (dicts / nested structures), functions, strings, security utilities, templates, and optional cryptography helpers.

> **Current version:** `1.1.5`

---

## Key Capabilities

- **Two usage styles**
  - **Static:** `UniCoreFW.map([...], fn)` / `_.map([...], fn)`
  - **Chainable:** `_(...).map(...).filter(...).value()`
- **Module-spanning API**
  - Core functions are registered as static and chain methods. Optional crypto
    compatibility methods load only when called; database and ORM functions
    are intentionally not collection-chain methods.
- **Security utilities**
  - Input validation, bounded local and distributed rate limiting, and audit logging.
- **Template engine**
  - `<%= var %>` interpolation and simple `<% if cond %> ... <% endif %>` with defensive checks.
- **Optional cryptography utilities**
  - Fernet symmetric encryption if `cryptography` is installed.

---

## Installation

### From PyPI

```bash
pip install unicorefw
```

### Optional dependency: crypto

Install the bounded optional dependency set for `unicorefw.crypto`:

```bash
pip install "unicorefw[crypto]"
```

### Optional dependency: ORM

Install the maintained SQLAlchemy policy layer without selecting a database
driver:

```bash
pip install "unicorefw[orm]"
```

Install the DBAPI driver for your database as another dependency. Async SQLite
requires `aiosqlite`, while PostgreSQL applications may choose `asyncpg`,
psycopg, or another SQLAlchemy-supported driver.

### Optional dependencies: database and spreadsheets

Python 3.9 or later can install the bounded relational, MongoDB, and Redis
driver set used by `unicorefw.db`:

```bash
pip install "unicorefw[database]"
```

Excel import and export support uses a separate bounded dependency set:

```bash
pip install "unicorefw[spreadsheet]"
```

The spreadsheet extra includes `defusedxml` because upstream openpyxl does not
enable XML entity-expansion defenses by itself. The base package and
`unicorefw[core]` install no third-party runtime dependency.

---

## Project Layout

```text
project_root_dir/
├── unicorefw/
│   ├── __init__.py
│   ├── _exports.py        # explicit lazy-export ownership
│   ├── core.py
│   ├── array.py
│   ├── object.py
│   ├── string.py
│   ├── function.py
│   ├── utils.py
│   ├── types.py
│   ├── security.py
│   ├── template.py
│   ├── crypto.py
│   ├── orm.py
│   ├── supporter.py
│   └── db.py              # present (import directly as unicorefw.db)
├── examples/
│   ├── sets/
│   ├── functions.py
│   ├── task_manager.py
│   └── underscore.py
└── README.md
```

---

## Quick Start

```python
from unicorefw import _, UniCoreFW

# Chainable usage
result = (
    _([1, 2, 3, 4, 5])
    .map(lambda x: x * 2)
    .filter(lambda x: x > 5)
    .value()
)
print(result)  # [6, 8, 10]

# Static usage (either UniCoreFW.* or _.*)
print(UniCoreFW.chunk([1, 2, 3, 4, 5, 6], 2))  # [[1, 2], [3, 4], [5, 6]]
print(_.chunk([1, 2, 3, 4, 5, 6], 2))          # [[1, 2], [3, 4], [5, 6]]
```

---

## How the API Works

UniCoreFW exposes two main entry points:

- `UniCoreFW`: the primary class providing **static methods** like `UniCoreFW.method_name(...)`.
- `_`: a convenience factory that returns a **UniCoreFWWrapper** for chaining:
  - `_(collection).map(...).filter(...).value()`
  - Additionally, `_.method_name(...)` is available as a static shortcut.

Chaining works by applying functions across UniCoreFW’s modules in a defined order; if a function name exists in a module, it becomes both:

- a chain method on `UniCoreFWWrapper`, and
- a static method on `UniCoreFW` (without overriding earlier modules’ functions when names collide).

Database and ORM helpers remain available from their submodules, the package
root, and compatible `UniCoreFW` static calls, but are excluded from collection
chaining. Importing `unicorefw` alone does not import `core`, `crypto`, `db`,
`orm`, SQLAlchemy, database drivers, pandas, or openpyxl. Compatibility names
are resolved from an explicit allowlist and cached on first access.

---

## Core Modules (What They Provide)

### Arrays (`unicorefw.array`)

List/array utilities: map/reduce/filter/find, chunking, flattening, set-like ops, ordering, etc.

```python
mapped = _.map([1, 2, 3], lambda x: x * 2)                 # [2, 4, 6]
flattened = _.flatten([1, [2, [3, 4]]])                    # [1, 2, 3, 4]
chunked = _.chunk([1, 2, 3, 4, 5, 6], 2)                   # [[1,2],[3,4],[5,6]]
median = _.find_median_sorted_arrays([1, 3, 5], [2, 4, 6]) # 3.5
```

Stable `uniq`, `union`, `intersection`, `difference`, and `xor` paths use
hash-backed membership and preserve first-occurrence order. Their common
hashable paths are O(n), or O(n + m) for two-input operations. Unhashable
values and unhashable derived keys retain equality semantics through a
quadratic worst-case fallback. Explicit comparator variants such as
`uniq_with` and `intersection_with` remain pairwise and therefore quadratic.

### Objects (`unicorefw.object`)

Dictionary and nested-structure helpers (including safe path operations), mapping, selection, and iteration.

```python
extended = _.extend({"a": 1}, {"b": 2}, {"c": 3})  # {"a":1,"b":2,"c":3}
print(_.has({"a": {"b": [10]}}, "a.b.0"))          # True
```

### Strings (`unicorefw.string`)

String transformation and inspection utilities (case transforms, regex helpers, whitespace normalization, etc.).

```python
from unicorefw import humanize, pascal_case, normalize_whitespace
print(humanize("hello_world_example"))          # "Hello world example"
print(pascal_case("hello world"))               # "HelloWorld"
print(normalize_whitespace("  a   b\nc\t"))     # "a b c"
```

### Functions (`unicorefw.function`)

Function helpers such as debounce, once, composition/flow utilities, partial/curry variants, etc.

```python
from unicorefw import once, debounce

only_once = once(lambda: "called")
print(only_once())  # "called"
print(only_once())  # None
```

### Utilities (`unicorefw.utils`)

General helpers: `unique_id`, `now`, `memoize`, `compress/decompress`, etc.

```python
print(_.unique_id("req-"))      # e.g. "req-1"
print(_.compress("aaabbc"))     # "3a2b1c"
print(_.decompress("3a2b1c"))   # "aaabbc"
```

### Types (`unicorefw.types`)

Type predicates and helpers like `is_string`, `is_number`, `is_empty`, deep equality, etc.

```python
from unicorefw import is_string, is_empty
print(is_string("x"))  # True
print(is_empty({}))    # True
```

### Security (`unicorefw.security`)

Input validation, bounded rate limiting, and audit logging primitives.

```python
from unicorefw.security import (
    AuditLogger,
    LocalRateLimiter,
    sanitize_string,
    validate_type,
)

validate_type("test", str, "param")
constrained = sanitize_string("  abc  ", max_length=10, allowed_chars="a-zA-Z0-9")
print(constrained)  # "abc"

with LocalRateLimiter(max_calls=100, time_window=60):
    pass

with AuditLogger(log_file="security.jsonl") as logger:
    logger.log("LOGIN", {"user_id": "42", "result": "success"})
```

Audit files are UTF-8 JSON Lines, owner-only on POSIX, and refuse symbolic-link
destinations where the operating system supports `O_NOFOLLOW`. Do not put
credentials, tokens, or other secrets in audit details.

`LocalRateLimiter` (also available under the compatible `RateLimiter` name)
shares state only between threads using the same object in one process. A
multi-process or multi-host service must use an atomic shared backend:

```python
from redis import Redis  # application dependency
from unicorefw.security import DistributedRateLimiter, RedisRateLimitBackend

backend = RedisRateLimitBackend(Redis.from_url(redis_url))
with DistributedRateLimiter(
    backend,
    key=authenticated_client_id,
    max_calls=100,
    time_window=60,
):
    process_request()
```

The Redis backend deterministically hashes the supplied identifier before using
it in a Redis key, uses Redis server time, and admits each request through one
atomic script. Hashing keeps the raw identifier out of the key name but is not
anonymization. Backend failures deny the request. Use stable authenticated
identifiers and configure Redis authentication, encryption, isolation,
availability, and key eviction for the application's threat model.

`sanitize_string()` constrains text by length and an allowed-character regular
expression; it is not contextual output encoding. Likewise,
`strip_html_tags()`/`strip_tags()` only remove tag-shaped text. Use
`html.escape()` for untrusted HTML text or a maintained allow-list sanitizer
when limited markup must be accepted. Callable validation establishes only
that Python can call an object, so callable inputs must come from a trusted
source.

See the project [security policy](https://github.com/unicorefw-org/unicorefw-py/blob/main/SECURITY.md)
for supported versions, private vulnerability reporting, and the threat model.

### Templates (`unicorefw.template`)

A small text-template processor plus an HTML text-node renderer:

```python
from unicorefw.template import html_template, template

print(template("Hello, <%= name %>!", {"name": "Alice"}))  # "Hello, Alice!"
print(html_template("<p><%= value %></p>", {"value": "<b>Alice</b>"}))
# <p><b>Alice</b></p>
```

`template()` produces plain text and does not HTML-escape values. `html_template()`
accepts untrusted values only in HTML text nodes; it rejects expressions inside
attributes, tags, scripts, and styles. Template source must always be trusted.

Caller-controlled expansion uses fixed budgets:

```python
from unicorefw.security import ResourceLimitError
from unicorefw.template import TemplateLimits, html_template
from unicorefw.utils import decompress

limits = TemplateLimits(
    max_tokens=200,
    max_nesting_depth=8,
    max_output_length=100_000,
)
rendered = html_template("<p><%= value %></p>", context, limits=limits)

try:
    text = decompress(
        encoded_text,
        max_output_length=250_000,
        max_compression_ratio=20,
    )
except ResourceLimitError:
    reject_input()
```

`ResourceLimitError` reports an exhausted runtime budget. Invalid settings raise
`InputValidationError`, including values above the library hard ceilings.

Other process-local helpers are bounded by default:

```python
from unicorefw.function import debounce
from unicorefw.object import set_
from unicorefw.regex_policy import RegexLimits
from unicorefw.string import regex_test
from unicorefw.supporter import PathLimits
from unicorefw.utils import memoize

cached_lookup = memoize(
    lookup,
    max_entries=256,
    max_weight_bytes=16 * 1024 * 1024,
    ttl_seconds=300,
)
search_changed = debounce(run_search, 250, max_pending_timers=8)
set_(record, "items[9].name", "safe", limits=PathLimits(max_list_length=100))
matched = regex_test(
    user_text,
    r"[A-Za-z0-9_-]+",
    limits=RegexLimits(max_input_length=2_000),
)
```

The standard-library regex engine has no portable timeout. Caller-supplied
patterns therefore use a conservative default policy that rejects
backreferences, special groups, and nested or adjacent repetition. Use
`unsafe_raw_regex()` only for reviewed, developer-controlled patterns; input
length remains capped when the trusted wrapper is used.

### Crypto (`unicorefw.crypto`) *(optional)*

Fernet authenticated encryption utilities require the `crypto` extra:

```python
from unicorefw.crypto import (
    InvalidToken,
    decrypt_string,
    encrypt_string,
    generate_key,
)

key = generate_key()
token = encrypt_string("secret", key)

try:
    # Reject tokens older than five minutes.
    plaintext = decrypt_string(token, key, ttl=300)
except InvalidToken:
    plaintext = None
```

Generate keys with `generate_key()` or Fernet, then store them in a dedicated
secret manager. Do not commit, log, or place keys in exception messages. Plan
rotation before deployment; applications that need overlapping old and new
keys can use `cryptography.fernet.MultiFernet` at their key-management boundary.
Fernet tokens expose their creation time in plaintext and buffer the complete
message in memory, so this helper is not suitable for large-file streaming.
Treat `InvalidToken` as one authentication failure; do not reveal whether a
token was malformed, expired, or encrypted under another valid key.

### ORM policy layer (`unicorefw.orm`) *(optional)*

The ORM module re-exports SQLAlchemy primitives and centralizes session
configuration. `session_scope()` supports `async with` and rolls back when the
request body raises:

```python
from unicorefw.orm import create_async_engine_from_url, create_async_sessionmaker
from unicorefw.orm import session_scope

engine = create_async_engine_from_url("sqlite+aiosqlite:///application.db")
AsyncSessionLocal = create_async_sessionmaker(engine)

async def load_record(record_id):
    async with session_scope(AsyncSessionLocal) as session:
        return await session.get(Record, record_id)
```

Keep credentials outside source code and pass them to SQLAlchemy through your
deployment secret boundary. Call `await engine.dispose()` during application
shutdown. The `orm` extra supplies SQLAlchemy and asyncio support; install the
selected DBAPI driver as another dependency.

### Database utilities (`unicorefw.db`) *(module present; import directly)*

The repository includes a `unicorefw.db` module for database helpers (multi-engine, pooling, migrations, import/export). Import it explicitly:

```python
from unicorefw.db import CacheManager, Database
db = Database(engine="sqlite", database=":memory:")
cache = CacheManager(db, max_entries=256, max_weight_bytes=16 * 1024 * 1024)
```

`CacheManager` uses monotonic TTL expiry, LRU entry and estimated-weight limits,
and isolated copies of cached query results. Call `cache.clear()` after writes
that may invalidate a cached query; cache invalidation is not automatic.

Build dynamic queries from validated identifiers and bound values. Complex SQL
requires an explicit trust marker:

```python
from unicorefw.db import QueryBuilder, unsafe_raw_sql

rows = (
    QueryBuilder(db)
    .select("id", "name")
    .from_table("users")
    .where("active = ?", True)
    .order_by("id", "DESC")
    .limit(100)
    .execute()
)

# Only reviewed, developer-controlled SQL belongs in this wrapper.
trusted_report = unsafe_raw_sql(
    "SELECT department, COUNT(*) AS total FROM users GROUP BY department"
)
```

Exporter source strings represent table names. Pass a reviewed query through
`unsafe_raw_sql()`. CSV and Excel exports neutralize formula-looking text by
default; `spreadsheet_safe=False` opts out and preserves exact strings. HTML
export escapes headers and cells. Custom CSS requires `unsafe_raw_css()`.

Importers cap bytes, rows, and columns. Excel import also caps ZIP expansion and
member count. JSON defaults to 64 MiB, 100,000 rows, and 1,000 columns:

```python
from unicorefw.db import DataImporter

inserted = DataImporter(db).from_json(
    "users.json",
    "users",
    max_bytes=8 * 1024 * 1024,
    max_rows=25_000,
    max_columns=100,
)
```

CSV import counts bytes while reading and rolls its transaction back when a row
limit expires. JSON, CSV, Excel, and dictionary imports create a requested table
inside the same transaction as their inserts, so a failed row does not leave an
empty table behind. Unexpected parser and driver failures raise
`DatabaseImportError` without copying file paths, SQL, or driver text into the
public message. The original error remains available through `__cause__`.
Configure limits from trusted application policy, not request parameters.

`Database.transaction()` uses a root transaction for the first context and a
generated savepoint for each nested context. An inner failure rolls back its
savepoint and leaves the outer transaction active. An outer failure rolls back
changes from inner contexts that released their savepoints. Direct
`begin()`, `commit()`, and `rollback()` calls retain their signatures;
`commit()` and `rollback()` close one managed level at a time. Calls made with
no managed level reach the driver as before, which preserves existing explicit
commit and rollback code.

Using `Database` itself as a context manager owns both the connection and a
managed root transaction. Entry begins the transaction; normal exit resolves
all managed levels and commits, while exceptional exit rolls them back. Every
exit closes the cursor and connection. This explicit root transaction is
important for PostgreSQL, whose direct helper connection otherwise uses
autocommit outside `transaction()`.

Each `Database` instance is bound to its creating process and thread because it
owns one mutable cursor and connection. Calls from another thread fail with
`DatabaseError` before driver access. Create one instance per thread.

Legacy code that already serializes every operation may disable the thread
check explicitly:

```python
db = Database(
    engine="sqlite",
    database="app.db",
    check_same_thread=False,
    unsafe_allow_cross_thread=True,
)
```

This option does not add locking, make a cursor safe for concurrent use, or
permit use after `fork()`. The caller must enable the driver's cross-thread
mode and provide synchronization. Process ownership cannot be disabled.

Unexpected constructor and connection-pool failures raise
`DatabaseConnectionError`. Root transaction failures raise `DatabaseError`.
Public messages exclude driver details and connection parameters; protected
diagnostics can inspect `__cause__`. Partial driver initialization and pool
shutdown attempt to close every acquired resource.

MySQL can commit DDL outside savepoint control, so use a native migration tool
for MySQL schema changes that need transactional guarantees.

The required service test job validates PostgreSQL 17.10 and MySQL 8.4.10 with
digest-pinned images. Its tests refuse remote hosts, privileged database users,
unexpected ports, and database names other than `unicorefw_test`; local runs
skip unless the integration environment is enabled explicitly.

`Migration` validates versions and scripts, verifies the checksum of an
already-applied version, and applies SQLite DDL and tracking records in one
transaction. SQLite statement boundaries use the native parser, so semicolons
inside strings and trigger bodies remain intact. PostgreSQL receives the
complete script through its DB-API driver. MySQL scripts use quote-aware and
comment-aware statement boundaries because PyMySQL does not enable
multi-statement execution by default. MySQL scripts that depend on client-side
`DELIMITER` directives require a native migration tool.

`DataImporter.from_sql()` accepts trusted SQLite scripts only. It executes the
script against an isolated snapshot, denies external database attachment and
writable-schema pragmas, and replaces the target only after the complete script
succeeds.

SQLite backup and restore use atomic owner-only files on POSIX. Restore builds an
isolated in-memory database before it changes the target.

```python
from unicorefw.db import BackupRestore, Database

source = Database(engine="sqlite", database="app.db")
backup_path = BackupRestore(source).backup(
    "app-backup.sql", format="sql", compress=True
)
source.close()

# The safe default requires an empty target database.
target = Database(engine="sqlite", database="restored.db")
BackupRestore(target).restore(backup_path, format="sql")
target.close()
```

Replacing a populated target requires both flags:

```python
target = Database(engine="sqlite", database="existing.db")
BackupRestore(target).restore(
    backup_path,
    format="sql",
    clear_existing=True,
    allow_destructive=True,
)
target.close()
```

Treat SQL backups as trusted executable schema artifacts. Restore denies SQLite
file attachment and writable-schema pragmas, but restored triggers and views can
still contain executable database logic. The default restore limits are 512 MiB
after decompression and a 200:1 gzip expansion ratio. PostgreSQL, MySQL, MongoDB,
and Redis backups require their native backup tools.

---

## Changelog Notes

Older changelog entries may not include newer internal changes. Prefer GitHub releases/tags for authoritative history.

---

## License

BSD 3-Clause License. See [LICENSE](LICENSE).

## Contributing

PRs are welcome. Please include tests where appropriate and keep changes consistent with the library’s defensive, security-oriented design.

Run the branch-coverage gate before submitting changes:

```bash
python -m pytest tests --cov=unicorefw --cov-branch \
  --cov-report=term-missing --cov-report=xml --cov-report=json \
  --cov-fail-under=83
```

CI rejects regressions below the current verified 83% ratchet. The interim
coverage baseline is 95% statement and branch coverage, and the ultimate
project target is 100%; maintainers raise the executable ratchet as each
baseline is reached.

Before submitting a security-sensitive change, also run:

```bash
python scripts/verify_security_policy.py suppressions --root .
bandit -r unicorefw -ll
git ls-files --cached --others --exclude-standard -z |
  xargs -0 detect-secrets-hook --no-verify
```

The CI environment pins `detect-secrets==1.5.0` and audits its installed
dependency graph. Inline Bandit or secret-scanner exceptions require exact
scope, a review rationale, and a future expiry date. CodeQL exceptions use the
same policy through `security/suppressions.json`. See
[SECURITY.md](https://github.com/unicorefw-org/unicorefw-py/blob/main/SECURITY.md)
before recording or renewing an exception.
