# Checks if an object has matching key-value pairs.

obj = {"name": "Alice", "age": 25}
result = UniCoreFW.is_match(obj, {"name": "Alice"})
print(result)  # Output: True

result = UniCoreFW.is_match(obj, {"name": "Bob"})
print(result)  # Output: False
