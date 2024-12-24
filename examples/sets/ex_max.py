# Returns the maximum value in an array, with an optional key function.

array = [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]
result = UniCoreFW.max(array, lambda x: x["age"])
print(result)  # Output: {"name": "Bob", "age": 30}
