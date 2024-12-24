# Returns a function that checks if an object has specific key-value pairs.

check_age_25 = UniCoreFW.matches({"age": 25})
print(check_age_25({"name": "Alice", "age": 25}))  # Output: True
print(check_age_25({"name": "Bob", "age": 30}))  # Output: False
