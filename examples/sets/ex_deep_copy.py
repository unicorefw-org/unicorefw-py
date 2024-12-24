# Creates a deep copy of an object, including nested objects.

original = {"a": 1, "b": {"c": 2}}
copy = UniCoreFW.deep_copy(original)
copy["b"]["c"] = 3
print(original)  # Output: {"a": 1, "b": {"c": 2}}
print(copy)  # Output: {"a": 1, "b": {"c": 3}}
