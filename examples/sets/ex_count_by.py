# Counts instances in an array based on a key function's result.

array = ["apple", "banana", "avocado"]
result = UniCoreFW.count_by(array, lambda x: x[0])
print(result)  # Output: {"a": 2, "b": 1}
