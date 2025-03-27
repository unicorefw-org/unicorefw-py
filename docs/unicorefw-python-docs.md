# UniCoreFW Python Library Documentation

## Overview

UniCoreFW is a Universal Core Utility Library that provides a comprehensive suite of utility functions for Python applications. The library is designed with the principles of universality, security, and performance in mind, making it suitable for both small applications and enterprise-level systems.

## Key Features

- **Security-First Design**: Includes input validation, rate limiting, and audit logging
- **Comprehensive Utility Functions**: For arrays, objects, functions, and more
- **Functional Programming Support**: Map, reduce, filter, and other higher-order functions
- **Method Chaining with UniCoreFWWrapper**: Enables fluent, chainable API similar to libraries like Lodash/Underscore
- **Type Checking**: Various methods to check types and verify data structures

## Getting Started

### Installation

To use UniCoreFW in your project, simply import the module:

```python
from unicorefw import _, UniCoreFW, UniCoreFWWrapper
```

### Basic Usage

Create UniCoreFW instances in two different ways:

```python
# Use static methods directly
filtered = UniCoreFW.filter([1, 2, 3, 4, 5], lambda x: x % 2 == 0)
print(filtered)  # [2, 4]

# Create a UniCoreFWWrapper instance for chainable operations
uc = UniCoreFWWrapper([1, 2, 3, 4, 5])

# Use chainable methods
result = uc.map(lambda x: x * 2)
print(result.value())  # [2, 4, 6, 8, 10]
```

### Method Chaining

UniCoreFW supports method chaining for a more fluent API using UniCoreFWWrapper:

```python
result = (UniCoreFWWrapper([1, 2, 3, 4, 5])
          .filter(lambda x: x > 1)
          .map(lambda x: x * 2)
          .value())
print(result)  # [4, 6, 8, 10]
```

## Security Features

UniCoreFW includes several security-oriented features:

### Input Validation

```python
from unicorefw import validate_type, validate_callable

# Validate a parameter's type
value = validate_type("test", str, "string_param")

# Validate that a parameter is callable
def my_func():
    pass
validate_callable(my_func, "function_param")
```

### String Sanitization

```python
from unicorefw import sanitize_string

# Sanitize a string with length and character constraints
safe_string = sanitize_string("user input", max_length=50, allowed_chars="a-zA-Z0-9")
```

### Rate Limiting

```python
from unicorefw import RateLimiter

# Create a rate limiter allowing 100 calls per minute
limiter = RateLimiter(max_calls=100, time_window=60)

# Use the rate limiter as a context manager
with limiter:
    # Your rate-limited code here
    perform_operation()
```

### Audit Logging

```python
from unicorefw import AuditLogger

# Create an audit logger
logger = AuditLogger(log_file="app_audit.log")

# Log security events
logger.log("LOGIN", "User johndoe logged in successfully")
```

## Core API Reference

### Array Functions

#### Basic Array Operations

```python
# Get the first element(s)
first_elem = UniCoreFW.first([1, 2, 3, 4, 5])  # 1
first_three = UniCoreFW.first([1, 2, 3, 4, 5], n=3)  # [1, 2, 3]

# Get the last element(s)
last_elem = UniCoreFW.last([1, 2, 3, 4, 5])  # 5
last_two = UniCoreFW.last([1, 2, 3, 4, 5], n=2)  # [4, 5]

# Get all but the first n elements
rest_elems = UniCoreFW.rest([1, 2, 3, 4, 5], 2)  # [3, 4, 5]

# Get all but the last n elements
initial_elems = UniCoreFW.initial([1, 2, 3, 4, 5], 2)  # [1, 2, 3]

# Remove duplicates from an array
unique_values = UniCoreFW.uniq([1, 2, 2, 3, 4, 4, 5])  # [1, 2, 3, 4, 5]

# Compact an array (remove falsey values)
compacted = UniCoreFW.compact([0, 1, False, 2, '', 3, None])  # [1, 2, 3]

# Split array into chunks
chunks = UniCoreFW.chunk([1, 2, 3, 4, 5, 6], 2)  # [[1, 2], [3, 4], [5, 6]]
```

#### Functional Array Operations

```python
# Map: Apply a function to each element
doubled = UniCoreFW.map([1, 2, 3], lambda x: x * 2)  # [2, 4, 6]

# Reduce: Combine elements into a single value
sum_result = UniCoreFW.reduce([1, 2, 3, 4], lambda acc, x: acc + x, 0)  # 10

# Filter: Keep elements that pass a predicate
evens = UniCoreFW.filter([1, 2, 3, 4, 5], lambda x: x % 2 == 0)  # [2, 4]

# Reject: Opposite of filter
odds = UniCoreFW.reject([1, 2, 3, 4, 5], lambda x: x % 2 == 0)  # [1, 3, 5]

# Find: Get the first element that matches a predicate
found = UniCoreFW.find([1, 2, 3, 4, 5], lambda x: x > 3)  # 4

# Every: Check if all elements pass a predicate
all_positive = UniCoreFW.every([1, 2, 3], lambda x: x > 0)  # True

# Some: Check if any element passes a predicate
has_even = UniCoreFW.some([1, 3, 5, 6], lambda x: x % 2 == 0)  # True

# Sort by a key function
sorted_list = UniCoreFW.sort_by(["abc", "a", "ab"], lambda s: len(s))  # ["a", "ab", "abc"]

# Group by a key function
grouped = UniCoreFW.group_by([1, 2, 3, 4, 5], lambda x: x % 2 == 0)
# {True: [2, 4], False: [1, 3, 5]}

# Count by a key function
counts = UniCoreFW.count_by(["a", "b", "c", "a", "b"], lambda x: x)
# {"a": 2, "b": 2, "c": 1}

# Pluck a property from each object
users = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
names = UniCoreFW.pluck(users, "name")  # ["John", "Jane"]
```

#### Array Transformations

```python
# Flatten nested arrays
flattened = UniCoreFW.flatten([1, [2, 3], [4, [5]]])  # [1, 2, 3, 4, 5]

# Flatten with depth limit
flattened_depth1 = UniCoreFW.flatten([1, [2, 3], [4, [5]]], depth=1)  # [1, 2, 3, 4, [5]]

# Zip multiple arrays together
zipped = UniCoreFW.zip([1, 2, 3], ["a", "b", "c"])  # [(1, "a"), (2, "b"), (3, "c")]

# Unzip an array of tuples
unzipped = UniCoreFW.unzip([(1, "a"), (2, "b"), (3, "c")])  # [[1, 2, 3], ["a", "b", "c"]]

# Partition an array based on a predicate
partitioned = UniCoreFW.partition([1, 2, 3, 4, 5], lambda x: x % 2 == 0)
# [[2, 4], [1, 3, 5]]

# Remove values from an array
filtered = UniCoreFW.without([1, 2, 3, 4, 5], 2, 4)  # [1, 3, 5]

# Create a range of numbers
range_arr = UniCoreFW.range(1, 6)  # [1, 2, 3, 4, 5]
range_with_step = UniCoreFW.range(0, 10, 2)  # [0, 2, 4, 6, 8]

# Get the difference between arrays
diff = UniCoreFW.difference([1, 2, 3, 4], [2, 4], [1])  # [3]

# Get the intersection of arrays
intersect = UniCoreFW.intersection([1, 2, 3], [2, 3, 4], [2, 3, 5])  # [2, 3]

# Get the union of arrays
union = UniCoreFW.union([1, 2], [2, 3], [3, 4])  # [1, 2, 3, 4]

# Random sample from array
sample = UniCoreFW.sample([1, 2, 3, 4, 5], 2)  # e.g., [2, 4] (random)

# Shuffle an array
shuffled = UniCoreFW.shuffle([1, 2, 3, 4, 5])  # Random order
```

### Object Functions

```python
# Get object keys
keys = UniCoreFW.keys({"name": "John", "age": 30})  # ["name", "age"]

# Get object values
values = UniCoreFW.values({"name": "John", "age": 30})  # ["John", 30]

# Clone an object
original = {"name": "John", "age": 30}
cloned = UniCoreFW.clone(original)  # {"name": "John", "age": 30}

# Extend an object with other objects
base = {"name": "John"}
extended = UniCoreFW.extend(base, {"age": 30}, {"city": "New York"})
# {"name": "John", "age": 30, "city": "New York"}

# Check if an object has a property
has_name = UniCoreFW.has({"name": "John"}, "name")  # True

# Create an object from keys and values
obj = UniCoreFW.object(["name", "age"], ["John", 30])
# {"name": "John", "age": 30}

# Convert object to key-value pairs
pairs = UniCoreFW.pairs({"name": "John", "age": 30})
# [("name", "John"), ("age", 30)]

# Find objects matching criteria
users = [
    {"name": "John", "active": True},
    {"name": "Jane", "active": True},
    {"name": "Bob", "active": False}
]
active_users = UniCoreFW.where(users, {"active": True})
# [{"name": "John", "active": True}, {"name": "Jane", "active": True}]

# Set default values for an object
obj = {"name": "John"}
with_defaults = UniCoreFW.defaults(obj, {"age": 30, "city": "Unknown"})
# {"name": "John", "age": 30, "city": "Unknown"}

# Invert an object's keys and values
inverted = UniCoreFW.invert({"name": "John", "age": 30})
# {"John": "name", 30: "age"}
```

### Function Utilities

```python
# Create a partially applied function
def add(a, b):
    return a + b

add_five = UniCoreFW.partial(add, 5)
result = add_five(10)  # 15

# Throttle a function (limit execution rate)
def expensive_operation():
    print("Operation executed")

throttled = UniCoreFW.throttle(expensive_operation, 1000)  # Max once per second
throttled()  # Executes
throttled()  # Ignored if called within 1000ms

# Debounce a function (delay execution until pause)
def on_resize():
    print("Resize handler executed")

debounced = UniCoreFW.debounce(on_resize, 200)  # Wait for 200ms of inactivity
# Multiple rapid calls will only execute once after 200ms

# Create a function that only executes once
def initialize():
    print("Initialized")

init_once = UniCoreFW.once(initialize)
init_once()  # Prints "Initialized"
init_once()  # Does nothing, returns None

# Execute a function after n calls
def congratulate():
    print("Congratulations!")

after_three = UniCoreFW.after(3, congratulate)
after_three()  # Nothing happens
after_three()  # Nothing happens
after_three()  # Prints "Congratulations!"

# Execute a function up to n times
def limited_access():
    print("Access granted")

only_twice = UniCoreFW.before(2, limited_access)
only_twice()  # Prints "Access granted"
only_twice()  # Prints "Access granted"
only_twice()  # Does nothing, returns None

# Wrap a function with another function
def say_hello(name):
    return f"Hello, {name}!"

with_exclamation = UniCoreFW.wrap(say_hello, lambda f, name: f"{f(name)}!!")
result = with_exclamation("John")  # "Hello, John!!!"

# Negate a predicate function
is_even = lambda x: x % 2 == 0
is_odd = UniCoreFW.negate(is_even)
is_odd(3)  # True

# Compose multiple functions
add_one = lambda x: x + 1
multiply_by_two = lambda x: x * 2
composed = UniCoreFW.compose(add_one, multiply_by_two)  # multiply_by_two(add_one(x))
result = composed(5)  # (5 + 1) * 2 = 12

# Delay a function execution
def delayed_task():
    print("Executed after delay")

UniCoreFW.delay(delayed_task, 1000)  # Execute after 1000ms

# Defer a function execution
def deferred_task():
    print("Executed after current stack")

UniCoreFW.defer(deferred_task)  # Execute after current call stack clears
```

### Type Checking

```python
# Check if a value is a string
UniCoreFW.is_string("hello")  # True

# Check if a value is a number
UniCoreFW.is_number(42)  # True
UniCoreFW.is_number(3.14)  # True

# Check if a value is an array
UniCoreFW.is_array([1, 2, 3])  # True

# Check if a value is an object/dictionary
UniCoreFW.is_object({"name": "John"})  # True

# Check if a value is a function
UniCoreFW.is_function(lambda x: x)  # True

# Check if a value is a boolean
UniCoreFW.is_boolean(True)  # True

# Check if a value is None
UniCoreFW.is_null(None)  # True

# Check if a value is empty
UniCoreFW.is_empty("")  # True
UniCoreFW.is_empty([])  # True
UniCoreFW.is_empty({})  # True
```

### Utility Functions

```python
# Generate a unique ID
id1 = UniCoreFW.unique_id()  # "1"
id2 = UniCoreFW.unique_id("user_")  # "user_2"

# Get current timestamp
now = UniCoreFW.now()  # Current timestamp in milliseconds

# Identity function
same = UniCoreFW.identity("hello")  # "hello"

# Execute a function n times
results = UniCoreFW.times(3, lambda i: i * 2)  # [0, 2, 4]

# Escape HTML entities
escaped = UniCoreFW.escape("<script>alert('XSS')</script>")
# "<script>alert('XSS')</script>"

# Unescape HTML entities
unescaped = UniCoreFW.unescape("<div>")  # "<div>"

# Memoize a function (cache results)
@UniCoreFW.memoize
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(20)  # Fast computation due to memoization

# Template function
template_str = "Hello, <%= name %>! You are <%= age %> years old."
context = {"name": "John", "age": 30}
result = UniCoreFW.template(template_str, context)
# "Hello, John! You are 30 years old."

# Get maximum value
max_val = UniCoreFW.max([1, 5, 3, 2, 4])  # 5

# Get minimum value
min_val = UniCoreFW.min([1, 5, 3, 2, 4])  # 1

# Chain operations
chained = uc.UniCoreFWWrapper([1, 2, 3, 4, 5])
result = chained.filter(lambda x: x > 2).map(lambda x: x * 2).value()
# [6, 8, 10]
```

### Advanced Functions

#### find_median_sorted_arrays

This function efficiently finds the median of two sorted arrays.

```python
# Find median of two sorted arrays
nums1 = [1, 3, 5]
nums2 = [2, 4, 6]
median = UniCoreFW.find_median_sorted_arrays(nums1, nums2)  # 3.5
```

#### compress and decompress

Utilities for string compression and decompression.

```python
# Compress a string using run-length encoding
compressed = UniCoreFW.compress("aaabbc")  # "3a2b1c"

# Decompress a run-length encoded string
decompressed = UniCoreFW.decompress("3a2b3c")  # "aaabbccc"
```

#### deep_copy

Creates a deep copy of an object without using the copy module.

```python
# Deep copy a nested structure
original = {"a": 1, "b": [1, 2, {"c": 3}]}
copied = UniCoreFW.deep_copy(original)

# Modifying the copy doesn't affect the original
copied["b"][2]["c"] = 4
print(original["b"][2]["c"])  # Still 3
```

## Advanced Usage Examples

### Data Processing Pipeline

```python
import unicorefw as uc

# Sample data
data = [
    {"name": "John", "age": 30, "active": True},
    {"name": "Jane", "age": 25, "active": True},
    {"name": "Bob", "age": 40, "active": False},
    {"name": "Alice", "age": 35, "active": True},
    {"name": "Charlie", "age": 22, "active": False}
]

# Create processing pipeline
def process_users(users):
    return (uc.UniCoreFW(users)
            .filter(lambda user: user["active"])      # Only active users
            .sort_by(lambda user: user["age"])        # Sort by age
            .map(lambda user: {                       # Transform data
                "display_name": user["name"].upper(),
                "age_group": "Young" if user["age"] < 30 else "Adult"
            })
            .value())

result = process_users(data)
# [
#     {"display_name": "JANE", "age_group": "Young"},
#     {"display_name": "JOHN", "age_group": "Adult"},
#     {"display_name": "ALICE", "age_group": "Adult"}
# ]
```

### Event Handling with Debounce and Throttle

```python
import unicorefw as uc
import time

# Simulate frequent events (e.g., resize, scroll)
def handle_resize():
    print("Resizing UI components...")
    # Expensive UI operations

# Create throttled version (max once per 500ms)
throttled_resize = uc.UniCoreFW.throttle(handle_resize, 500)

# Create debounced version (execute 300ms after last call)
debounced_resize = uc.UniCoreFW.debounce(handle_resize, 300)

# Simulate rapid events
for _ in range(10):
    throttled_resize()  # Will execute about twice during the loop
    debounced_resize()  # Will execute once after the loop finishes
    time.sleep(0.1)

# Wait for debounced function to execute
time.sleep(0.5)
```

### Secure Data Processing

```python
import unicorefw as uc
from unicorefw import RateLimiter, AuditLogger, sanitize_string

# Setup security components
rate_limiter = RateLimiter(max_calls=100, time_window=60)
audit_logger = AuditLogger(log_file="data_processing.log")

def process_user_input(user_id, user_input):
    try:
        # Apply rate limiting
        with rate_limiter:
            # Sanitize input
            sanitized_input = sanitize_string(
                user_input, 
                max_length=1000,
                allowed_chars="a-zA-Z0-9 .,;:!?()-"
            )
      
            # Process the data
            result = perform_data_processing(sanitized_input)
      
            # Log success
            audit_logger.log("DATA_PROCESS", f"User {user_id} processed data successfully")
      
            return result
    except Exception as e:
        # Log failure
        audit_logger.log("ERROR", f"User {user_id} data processing failed: {str(e)}")
        raise

def perform_data_processing(data):
    # Apply function utilities for processing
    return (uc.UniCoreFWWrapper(data.split())
            .map(lambda word: word.lower())
            .filter(lambda word: len(word) > 3)
            .invoke("capitalize")
            .value())
```

### Memoized Recursive Function

```python
import unicorefw as uc
import time

# Define an expensive recursive function
def fibonacci_slow(n):
    if n <= 1:
        return n
    time.sleep(0.1)  # Simulate expensive computation
    return fibonacci_slow(n-1) + fibonacci_slow(n-2)

# Create a memoized version
fibonacci_fast = uc.UniCoreFW.memoize(fibonacci_slow)

# Measure performance
start = time.time()
result_slow = fibonacci_slow(10)
duration_slow = time.time() - start

start = time.time()
result_fast = fibonacci_fast(10)
duration_fast = time.time() - start

print(f"Slow: {duration_slow:.2f}s, Fast: {duration_fast:.2f}s")
# The memoized version should be significantly faster
```

### Template Rendering

```python
import unicorefw as uc

# Define a template
template = """
<% if user %>
<div>
    <h1>Hello, <%= user.name %>!</h1>
    <p>Your account is <%= user.status %>.</p>
    <% if user.notifications %>
    <p>You have <%= user.notifications %> unread messages.</p>
    <% endif %>
</div>
<% endif %>
"""

# Render with context
context = {
    "user": {
        "name": "John",
        "status": "active",
        "notifications": 3
    }
}

rendered = uc.UniCoreFW.template(template, context)
print(rendered)
```

## Security Best Practices

When using UniCoreFW, follow these security best practices:

1. **Always validate inputs**: Use the built-in validation functions for all user inputs

   ```python
   validate_type(user_input, str, "user_input")
   ```
2. **Sanitize string data**: Use sanitize_string for any user-provided text

   ```python
   sanitized = sanitize_string(user_input, max_length=100, allowed_chars="a-zA-Z0-9")
   ```
3. **Apply rate limiting**: Use RateLimiter for protection against DoS attacks

   ```python
   with RateLimiter(max_calls=100, time_window=60):
       process_request()
   ```
4. **Maintain audit logs**: Use AuditLogger to track security events

   ```python
   logger = AuditLogger()
   logger.log("ACCESS", f"User {user_id} accessed resource {resource_id}")
   ```
5. **Use secure random functions**: When randomness is needed, use the secure functions provided

   ```python
   # Use shuffle with secure randomness
   shuffled = UniCoreFW.shuffle(items)
   ```
6. **Be careful with dynamic evaluation**: The template function has safeguards, but be cautious with dynamic content

   ```python
   # Avoid user-provided templates when possible
   template = "<%= user.name %>"  # Safe
   # user_template = user_input  # Potentially unsafe
   ```

## Performance Considerations

For optimal performance when using UniCoreFW:

1. Use memoization for expensive functions

   ```python
   expensive_function = UniCoreFW.memoize(original_function)
   ```
2. Be mindful of deep copying large objects

   ```python
   # Consider whether you need a deep or shallow copy
   shallow_copy = UniCoreFW.clone(large_object)  # Faster
   deep_copy = UniCoreFW.deep_copy(large_object)  # More thorough but slower
   ```
3. Chain operations efficiently

   ```python
   # More efficient - processes data in a pipeline
   result = (UniCoreFW(data)
             .filter(criteria)
             .map(transform)
             .value())

   # Less efficient - creates intermediate arrays
   filtered = UniCoreFW.filter(data, criteria)
   result = UniCoreFW.map(filtered, transform)
   ```
4. Use the appropriate collection function for your needs

   ```python
   # If you only need one matching item, use find instead of filter
   first_match = UniCoreFW.find(items, predicate)  # Stops after finding a match
   ```

## Conclusion

UniCoreFW is a versatile utility library that combines functional programming concepts with robust security features. It provides a wide range of functions for array manipulation, object handling, function transformation, and type checking, along with advanced utilities like memoization, debouncing, and throttling.

The library's focus on security, with built-in input validation, rate limiting, and audit logging, makes it suitable for developing secure applications. Its chainable API enables expressive, readable code that follows functional programming principles.

Whether you're building a small utility application or an enterprise-level system, UniCoreFW offers the tools to write more concise, maintainable, and secure Python code.
