<p align="center"><img src="https://unicorefw.org/logo.png?v=1.0.2" /></p>
 
|                                                                                                           | Arrays | Objects | Functions | Utilities |
| :---------------------------------------------------------------------------------------------------------- | -------: | --------: | ----------: | ----------: |
| **Test Status**                                                                                           |     ✓ |      ✓ |        ✓ |        ✓ |
| **Build Status**                                                                                          |      ✓ |      ✓ |        ✓ |        ✓ |
| ![Publish to PyPi](https://github.com/unicorefw-org/unicorefw-py/actions/workflows/release.yml/badge.svg) |        |         |           |           |
# UniCoreFW

[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)](https://www.python.org/downloads/)

**Universal Core Utility Library**

UniCoreFW is a comprehensive utility library that provides a wide range of functions for arrays, objects, functions, and more, all with a focus on universality, security, and performance.

## Features

- **Security-First Design**: Built-in input validation, rate limiting, and audit logging
- **Functional Programming**: Map, reduce, filter, and other higher-order functions
- **Chainable API**: Similar to libraries like Lodash/Underscore
- **Comprehensive Toolset**: 100+ utility functions organized into logical categories
- **Type Checking**: Extensive type checking and validation utilities

## Installation

```bash
pip install unicorefw
```

## Quick Start

```python
import unicorefw as uc

# Create a new instance
_ = uc.UniCoreFW([1, 2, 3, 4, 5])

# Functional methods
doubled = _.map(lambda x: x * 2).value()  # [2, 4, 6, 8, 10]

# Chainable API
result = (uc.UniCoreFW([1, 2, 3, 4, 5])
          .filter(lambda x: x > 2)
          .map(lambda x: x * 2)
          .value())  # [6, 8, 10]

# Use static methods directly
filtered = uc.UniCoreFW.filter([1, 2, 3, 4, 5], lambda x: x % 2 == 0)  # [2, 4]
```

## Core Modules

### Array Functions

```python
# Map, filter, reduce
mapped = uc.UniCoreFW.map([1, 2, 3], lambda x: x * 2)  # [2, 4, 6]
filtered = uc.UniCoreFW.filter([1, 2, 3, 4], lambda x: x % 2 == 0)  # [2, 4]
reduced = uc.UniCoreFW.reduce([1, 2, 3, 4], lambda a, b: a + b, 0)  # 10

# Array manipulation
first = uc.UniCoreFW.first([1, 2, 3], n=2)  # [1, 2]
last = uc.UniCoreFW.last([1, 2, 3], n=2)  # [2, 3]
flattened = uc.UniCoreFW.flatten([1, [2, [3, 4]]])  # [1, 2, 3, 4]
chunked = uc.UniCoreFW.chunk([1, 2, 3, 4, 5, 6], 2)  # [[1, 2], [3, 4], [5, 6]]
```

### Object Functions

```python
# Object manipulation
keys = uc.UniCoreFW.keys({"a": 1, "b": 2})  # ["a", "b"]
values = uc.UniCoreFW.values({"a": 1, "b": 2})  # [1, 2]
extended = uc.UniCoreFW.extend({"a": 1}, {"b": 2}, {"c": 3})  # {"a": 1, "b": 2, "c": 3}

# Object creation
obj = uc.UniCoreFW.object(["a", "b"], [1, 2])  # {"a": 1, "b": 2}
```

### Function Utilities

```python
# Function transformation
def add(a, b):
    return a + b

add_5 = uc.UniCoreFW.partial(add, 5)  # Creates a new function that adds 5
result = add_5(10)  # 15

# Execution control
throttled = uc.UniCoreFW.throttle(expensive_function, 1000)  # Max once per second
debounced = uc.UniCoreFW.debounce(on_input_change, 300)  # Wait for 300ms of inactivity
memoized = uc.UniCoreFW.memoize(fibonacci)  # Cache results for repeated calls
```

### Security Utilities

```python
from unicorefw import validate_type, validate_callable, sanitize_string

# Input validation
validate_type("test", str, "string_param")
validate_callable(lambda x: x, "function_param")

# String sanitization
safe_input = sanitize_string(user_input, max_length=100, allowed_chars="a-zA-Z0-9")

# Rate limiting
with uc.RateLimiter(max_calls=100, time_window=60):
    perform_api_request()

# Audit logging
logger = uc.AuditLogger(log_file="security.log")
logger.log("LOGIN", "User authenticated successfully")
```

### Special Algorithms

```python
# Find median of two sorted arrays
median = uc.UniCoreFW.find_median_sorted_arrays([1, 3, 5], [2, 4, 6])  # 3.5

# String compression
compressed = uc.UniCoreFW.compress("aaabbc")  # "3a2b1c"
decompressed = uc.UniCoreFW.decompress("3a2b3c")  # "aaabbccc"
```

## Advanced Examples

### Data Processing Pipeline

```python
def process_data(items):
    return (uc.UniCoreFW(items)
            .filter(lambda x: x["active"])
            .sort_by(lambda x: x["priority"])
            .map(lambda x: {
                "id": x["id"],
                "status": "High" if x["priority"] > 5 else "Low"
            })
            .value())

result = process_data([
    {"id": 1, "active": True, "priority": 7},
    {"id": 2, "active": False, "priority": 3},
    {"id": 3, "active": True, "priority": 4}
])
# [{"id": 3, "status": "Low"}, {"id": 1, "status": "High"}]
```

### Secure Template Rendering

```python
template = "Hello, <%= name %>! Your role is: <%= role %>."
context = {"name": "John", "role": "Admin"}

rendered = uc.UniCoreFW.template(template, context)
# "Hello, John! Your role is: Admin."
```

## Why UniCoreFW?

### Universality

UniCoreFW provides consistent APIs across different environments and use cases, allowing you to write cleaner, more maintainable code.

### Security

Every function is designed with security in mind, including input validation, rate limiting, and audit logging capabilities.

### Performance

Functions are optimized for minimal overhead, suitable for both small applications and enterprise-level systems.

## License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Authors

- **Kenny Ngo** - *Initial work* - [UniCoreFW.Org](https://unicorefw.org) / [IIPTech.info](https://iiptech.info)


