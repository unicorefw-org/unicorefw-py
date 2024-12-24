# Filters an array of objects, returning only those that match the given key-value pairs.
obj_list = [
    {"name": "Alice", "age": 25},
    {"name": "Bob", "age": 30},
    {"name": "Charlie", "age": 25},
]
result = UniCoreFW.where(obj_list, {"age": 25})
print(result)  # Output: [{"name": "Alice", "age": 25}, {"name": "Charlie", "age": 25}]
