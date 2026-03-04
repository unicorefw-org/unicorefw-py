<p align="center">
  <img src="https://unicorefw.org/img/logo.png?v=1.1.2" alt="UniCoreFW logo" />
</p>

[![Publish to PyPi](https://github.com/unicorefw-org/unicorefw-py/actions/workflows/release.yml/badge.svg)](https://pypistats.org/packages/unicorefw)
[![Unit Tests](https://github.com/unicorefw-org/unicorefw-py/actions/workflows/tests.yml/badge.svg)](https://github.com/unicorefw-org/unicorefw-py/actions/workflows/tests.yml)
[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)](https://www.python.org/downloads/)

# UniCoreFW

**Universal Core Utility Library (Python)**

UniCoreFW is a compact, batteries-included utility library that provides chainable and static helper functions across arrays (lists), objects (dicts / nested structures), functions, strings, security utilities, templates, and optional cryptography helpers.

> **Current version:** `1.1.2`

---

## Key Capabilities

- **Two usage styles**
  - **Static:** `UniCoreFW.map([...], fn)` / `_.map([...], fn)`
  - **Chainable:** `_(...).map(...).filter(...).value()`
- **Module-spanning API**
  - Functions from `array`, `object`, `string`, `function`, `utils`, `types`, `security`, `template`, and `crypto` are attached dynamically as static methods and as chain methods.
- **Security utilities**
  - Input validation helpers, string sanitization, rate limiting, and audit logging.
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

### Optional dependency (Crypto module)

The `unicorefw.crypto` module requires `cryptography`:

```bash
pip install cryptography
```

---

## Project Layout

```text
project_root_dir/
├── unicorefw/
│   ├── __init__.py
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
Input validation, sanitization, rate limiting, and audit logging primitives.

```python
from unicorefw.security import RateLimiter, AuditLogger, validate_type, sanitize_string

validate_type("test", str, "param")
safe = sanitize_string("  abc  ", max_length=10, allowed_chars="a-zA-Z0-9")
print(safe)  # "abc"

with RateLimiter(max_calls=100, time_window=60):
    pass

logger = AuditLogger(log_file="security.log")
logger.log("LOGIN", "User authenticated successfully")
```

### Templates (`unicorefw.template`)
A small, defensive template processor:

```python
from unicorefw import template
print(template("Hello, <%= name %>!", {"name": "Alice"}))  # "Hello, Alice!"
```

### Crypto (`unicorefw.crypto`) *(optional)*
Fernet symmetric encryption utilities (requires `cryptography`):

```python
from unicorefw.crypto import generate_key, encrypt_string, decrypt_string

key = generate_key()
token = encrypt_string("secret", key)
print(decrypt_string(token, key))  # "secret"
```

### Database utilities (`unicorefw.db`) *(module present; import directly)*
The repository includes a `unicorefw.db` module for database helpers (multi-engine, pooling, migrations, import/export). Import it explicitly:

```python
from unicorefw.db import Database
db = Database(engine="sqlite", database=":memory:")
```

---

## Changelog Notes

Older changelog entries may not include newer internal changes. Prefer GitHub releases/tags for authoritative history.

---

## License

BSD 3-Clause License. See [LICENSE](LICENSE).

## Contributing

PRs are welcome. Please include tests where appropriate and keep changes consistent with the library’s defensive, security-oriented design.
