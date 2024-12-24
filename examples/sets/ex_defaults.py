# Assigns default properties to an object if they are missing.

obj = {"name": "Alice"}
defaults = {"name": "Unknown", "age": 25}
result = UniCoreFW.defaults(obj, defaults)
print(result)  # Output: {"name": "Alice", "age": 25}
