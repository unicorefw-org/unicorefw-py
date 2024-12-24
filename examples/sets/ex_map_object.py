# Applies a function to each value in an object, returning a new object with the transformed values.

obj = {"a": 1, "b": 2, "c": 3}
result = UniCoreFW.map_object(obj, lambda x: x * 2)
print(result)  # Output: {"a": 2, "b": 4, "c": 6}
