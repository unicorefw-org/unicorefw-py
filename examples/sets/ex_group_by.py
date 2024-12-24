# Groups elements in an array based on a function's result.

array = ["apple", "banana", "apricot", "blueberry"]
result = UniCoreFW.group_by(array, lambda x: x[0])
print(result)  # Output: {"a": ["apple", "apricot"], "b": ["banana", "blueberry"]}
