<p align="center"><img src="https://unicorefw.org/img/logo.png?v=1.0.2" /></p>

|                        | Arrays | Objects | Functions | Utilities |
| :--------------------- | -----: | ------: | --------: | --------: |
| **Test Status**  |     ✓ |      ✓ |        ✓ |        ✓ |
| **Build Status** |     ✓ |      ✓ |        ✓ |        ✓ |
![Publish to PyPi](https://github.com/unicorefw-org/unicorefw-py/actions/workflows/release.yml/badge.svg) ![Unit Tests](https://github.com/unicorefw-org/unicorefw-py/actions/workflows/tests.yml/badge.svg)
# UniCoreFW

[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](LICENSE) [![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)](https://www.python.org/downloads/)

**Universal Core Utility Library**

UniCoreFW is a comprehensive utility library that provides a wide range of functions for arrays, objects, functions, and more, all with a focus on universality, security, and performance.

## Features

- **Security-First Design**: Built-in input validation, rate limiting, and audit logging
- **Functional Programming**: Map, reduce, filter, and other higher-order functions
- **Chainable API**: Similar to libraries like Lodash/Underscore
- **Comprehensive Toolset**: 100+ utility functions organized into logical categories
- **Type Checking**: Extensive type checking and validation utilities

Changelogs
----------

## Version 1.0.3

* **Restructured:** unicorefw.py
* **Updated:** flatten()  to improve performance

## Version 1.0.2

* **Removed:** `import random`
* **Added:** `import secrets`
* **Added:** `from functools import lru_cache`
* **Added:** `lock = threading.Lock()`
* **Added:** `counter = 0`

#### New Features:

* Implemented a robust security foundation with new exception classes:
  * `SecurityError`: Base exception for security-related errors.
  * `InputValidationError`: Raised when input validation fails.
  * `AuthorizationError`: Raised when authorization checks fail.
  * `SanitizationError`: Raised when data sanitization fails.

#### New Class:

* **RateLimiter** :
  * Implements rate limiting to prevent DoS attacks.
  * Supports `max_calls` and `time_window` configuration.

## Installation from Pypi using PIP

```bash
pip install unicorefw
```

Installation from source
------------------------

1. Clone the repository:

   git clone https://github.com/unicorefw-org/unicorefw-py.git
   cd unicorefw-py
2. Ensure Python 3.x is installed on your system.
3. Directory Structure

```
project_root_dir/
├── unicorefw/
│   └── __init__
│   └── array.py
│   └── core.py
│   └── function.py
│   └── object.py
│   └── security.py
│   └── template.py
│   └── types.py
│   └── utils.py
├── examples/
│   └── sets/            # List of examples
│   └── functions.py     # Show examples of function usage
│   └── task_manager.py  # Sample implementations using UniCoreFW functions
│   └── underscore.py    # Examples on how to use UniCoreFW as _
└── README.md
```

## Quick Start

```python
from unicorefw import _, UniCoreFW, UniCoreFWWrapper

# Chaining example
result = (_([1, 2, 3, 4, 5])
            .map(lambda x: x * 2)
            .filter(lambda x: x > 5)
            .value())
          
print(f"Chained result: {result}")  # Output: [6, 8, 10]

# Static method example
template = "Name: <%= name %>, Age: <%= age %>"
context = {"name": "Alice", "age": 25}
print(f"Template result: {_.template(template, context)}")  
# Output: "Name: Alice, Age: 25"

# Multiple operations example
data = [
    {"name": "Alice", "age": 25, "active": True},
    {"name": "Bob", "age": 30, "active": False},
    {"name": "Charlie", "age": 35, "active": True}
]

active_names = (_(data)
                .filter(lambda x: x.get("active", False))
                .pluck("name")
                .value())
print(f"Active users: {active_names}")  # Output: ['Alice', 'Charlie']

# Demonstrate static vs chained methods
array = [1, 2, 3, 4, 5]
print(f"Static map: {_.map(array, lambda x: x * 3)}")
print(f"Chained map: {_(array).map(lambda x: x * 3).value()}")
```

## Core Modules

### Array Functions

```python
# Map, filter, reduce
mapped = UniCoreFW.map([1, 2, 3], lambda x: x * 2)  # [2, 4, 6]
filtered = UniCoreFW.filter([1, 2, 3, 4], lambda x: x % 2 == 0)  # [2, 4]
reduced = UniCoreFW.reduce([1, 2, 3, 4], lambda a, b: a + b, 0)  # 10

# Array manipulation
first = UniCoreFW.first([1, 2, 3], n=2)  # [1, 2]
last = UniCoreFW.last([1, 2, 3], n=2)  # [2, 3]
flattened = UniCoreFW.flatten([1, [2, [3, 4]]])  # [1, 2, 3, 4]
chunked = UniCoreFW.chunk([1, 2, 3, 4, 5, 6], 2)  # [[1, 2], [3, 4], [5, 6]]
```

### Object Functions

```python
# Object manipulation
keys = UniCoreFW.keys({"a": 1, "b": 2})  # ["a", "b"]
values = UniCoreFW.values({"a": 1, "b": 2})  # [1, 2]
extended = UniCoreFW.extend({"a": 1}, {"b": 2}, {"c": 3})  # {"a": 1, "b": 2, "c": 3}

# Object creation
obj = UniCoreFW.object(["a", "b"], [1, 2])  # {"a": 1, "b": 2}
```

### Function Utilities

```python
# Function transformation
def add(a, b):
    return a + b

add_5 = UniCoreFW.partial(add, 5)  # Creates a new function that adds 5
result = add_5(10)  # 15

# Execution control
throttled = UniCoreFW.throttle(expensive_function, 1000)  # Max once per second
debounced = UniCoreFW.debounce(on_input_change, 300)  # Wait for 300ms of inactivity
memoized = UniCoreFW.memoize(fibonacci)  # Cache results for repeated calls
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
with RateLimiter(max_calls=100, time_window=60):
    perform_api_request()

# Audit logging
logger = AuditLogger(log_file="security.log")
logger.log("LOGIN", "User authenticated successfully")
```

### Special Algorithms

```python
# Find median of two sorted arrays
median = UniCoreFW.find_median_sorted_arrays([1, 3, 5], [2, 4, 6])  # 3.5

# String compression
compressed = UniCoreFW.compress("aaabbc")  # "3a2b1c"
decompressed = UniCoreFW.decompress("3a2b3c")  # "aaabbccc"
```

## Advanced Examples

### Data Processing Pipeline

```python
def process_data(items):
    return (_(items)
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

rendered = UniCoreFW.template(template, context)
# "Hello, John! Your role is: Admin."
```

**PYTHON IMPLEMENTATION**
---------------------

# Architecture

**UniCoreFW**	 is Primary class that providing static utility methods	like UniCoreFW.method_name(arguments)

**UniCoreFWWrapper** is Wrapper class that enables method chaining like UniCoreFWWrapper(collection).method1().method2().value()

This class, `UniCoreFW`, provides a wide range of utility functions for working with arrays, objects, and strings. Here's a summary of what each method does:

**Array Functions**

- `_.map` – Transforms an array's elements based on a function.
- `_.reduce` – Reduces an array to a single value using a function.
- `_.reduce_right` – Like - `_.reduce, but starts from the right.
- `_.find` – Returns the first value that matches a predicate.
- `_.filter` – Returns an array of values that match a predicate.
- `_.where` – Filters an array of objects, matching a set of key-value pairs.
- `_.find_where` – Like - `_.where, but returns only the first match.
- `_.reject` – Returns an array of values that fail a predicate.
- `_.every` – Tests whether all values pass a predicate.
- `_.some` – Tests whether any values pass a predicate.
- `_.contains` – Checks if a value exists in an array.
- `_.invoke` – Invokes a method on every item in a collection.
- `_.pluck` – Extracts a list of values from an array of objects.
- `_.max` – Returns the maximum value based on a function.
- `_.min` – Returns the minimum value based on a function.
- `_.sort_by` – Sorts an array by a function's result.
- `_.group_by` – Groups an array by the result of a function.
- `_.index_by` – Indexes an array by a property value or function result.
- `_.count_by` – Counts instances of values by a function's result.
- `_.shuffle` – Shuffles the values in an array.
- `_.sample` – Selects random values from an array.
- `_.to_array` – Converts an iterable into an array.
- `_.size` – Returns the size of a collection.
- `_.partition` – Splits a collection into two arrays based on a predicate.
- `_.first` – Returns the first elements of an array.
- `_.initial` – Returns everything but the last element of an array.
- `_.last` – Returns the last elements of an array.
- `_.rest` – Returns everything but the first element of an array.
- `_.compact` – Removes falsey values from an array.
- `_.flatten` – Flattens a nested array.
- `_.without` – Returns an array with specified values removed.
- `_.uniq` – Removes duplicate values from an array.
- `_.union` – Combines arrays, removing duplicates.
- `_.intersection` – Returns values common to all arrays.
- `_.difference` – Returns values from the first array not present in others.
- `_.zip` – Merges arrays based on their index.
- `_.unzip` – Reverses the process of - `_.zip.
- `_.object` – Converts an array of pairs into an object.
- `_.range` – Creates an array of numbers in a range.
- `_.chunk` – Splits an array into chunks of a specified size.

**Object Functions**

- `_.keys` – Returns an array of an object's keys.
- `_.all_keys` – Returns an array of an object's keys, including inherited ones.
- `_.values` – Returns an array of an object's values.
- `_.map_object` – Applies a function to each value of an object.
- `_.pairs` – Converts an object into an array of [key, value] pairs.
- `_.invert` – Inverts an object's keys and values.
- `_.functions` – Returns an array of all function property names in an object.
- `_.extend` – Extends an object with the properties of other objects.
- `_.extend_own` – Like - `_.extend, but only copies own properties.
- `_.defaults` – Assigns default properties to an object.
- `_.create` – Creates an object with a specified prototype.
- `_.clone` – Creates a shallow copy of an object.
- `_.tap` – Invokes a function with an object and returns the object.
- `_.has` – Checks if an object contains a given property.
- `_.property` – Returns a function that retrieves a property value.
- `_.property_of` – Returns a function that retrieves a property value from a given object.
- `_.matcher (or - `_.matches)` – Creates a function that checks for matching key-value pairs.
- `_.is_equal` – Performs a deep comparison between objects.
- `_.is_match` – Checks if an object matches key-value pairs.
- `_.is_empty` – Checks if an object is empty.
- `_.is_element` – Checks if an object is a DOM element.
- `_.is_array` – Checks if a value is an array.
- `_.is_object` – Checks if a value is an object.
- `_.is_arguments` – Checks if a value is an arguments object.
- `_.is_function` – Checks if a value is a function.
- `_.is_string` – Checks if a value is a string.
- `_.is_number` – Checks if a value is a number.
- `_.is_finite` – Checks if a value is a finite number.
- `_.is_boolean` – Checks if a value is a boolean.
- `_.is_date` – Checks if a value is a date.
- `_.is_reg_exp` – Checks if a value is a regular expression.
- `_.is_error` – Checks if a value is an error.
- `_.is_symbol` – Checks if a value is a symbol.
- `_.is_map` – Checks if a value is a map.
- `_.is_weak_map` – Checks if a value is a weak map.
- `_.is_set` – Checks if a value is a set.
- `_.is_weak_set` – Checks if a value is a weak set.
- `_.is_null` – Checks if a value is null.
- `_.is_undefined` – Checks if a value is undefined.
- `_.is_nan` – Checks if a value is NaN.
- `_.is_typed_array` – Checks if a value is a typed array.
- `_.is_array_buffer` – Checks if a value is an array buffer.
- `_.is_data_view` – Checks if a value is a data view.

**Utility Functions**

- `_.identity` – Returns the same value that is passed.
- `_.constant` – Returns a function that returns the given value.
- `_.noop` – A function that does nothing.
- `_.times` – Invokes a function a specified number of times.
- `_.random` – Returns a random number between a min and max.
- `_.mixin` – Adds functions to the Underscore object.
- `_.iteratee` – Returns a function that can be applied to each element in a collection.
- `_.unique_id` – Generates a unique identifier.
- `_.escape` – Escapes a string for inclusion in HTML.
- `_.unescape` – Unescapes a string from HTML.
- `_.result` – Resolves the value of a property, potentially invoking it as a function.
- `_.now` – Returns the current timestamp.
- `_.template` – Compiles a template to a function.
- `_.chain` – Returns a wrapped object to allow chaining of functions.
- `_.value` – Extracts the result from a chained object.

**Function Functions**

- `_.bind` – Binds a function to an object.
- `_.partial` – Partially applies a function by pre-filling some arguments.
- `_.bind_all` – Binds methods of an object to the object itself.
- `_.memoize` – Caches the result of a function call.
- `_.delay` – Delays a function for a specified number of milliseconds.
- `_.defer` – Defers a function to be executed after the current call stack clears.
- `_.throttle` – Creates a throttled version of a function.
- `_.debounce` – Creates a debounced version of a function.
- `_.once` – Ensures a function is only called once.
- `_.after` – Returns a function that will only run after it has been called N times.
- `_.before` – Returns a function that will run until it has been called N times.
- `_.wrap` – Wraps a function inside another function.
- `_.negate` – Returns the negation of a predicate function.
- `_.compose` – Composes functions together to run in sequence.

**Chaining Functions**

- `_.chain` – Starts a chain.
- `_.value` – Extracts the value at the end of a chain.

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
