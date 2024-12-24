# Checks if an object is a dictionary (used as a map in Python).

result = UniCoreFW.is_map({"key": "value"})
print(result)  # Output: True

result = UniCoreFW.is_map([1, 2, 3])
print(result)  # Output: False
