# Checks if an object has a specified property.

obj = {"name": "Alice", "age": 25}
result = UniCoreFW.has(obj, "age")
print(result)  # Output: True

result = UniCoreFW.has(obj, "city")
print(result)  # Output: False
