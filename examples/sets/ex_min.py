# Returns the minimum value in an array, with an optional key function.

array = [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]
result = UniCoreFW.min(array, lambda x: x["age"])
print(result)  # Output: {"name": "Alice", "age": 25}
