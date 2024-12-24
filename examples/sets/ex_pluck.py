# Extracts a list of values for a given key from an array of dictionaries.
array = [
    {"name": "Alice", "age": 25},
    {"name": "Bob", "age": 30},
    {"name": "Charlie", "age": 35},
]
result = UniCoreFW.pluck(array, "name")
print(result)  # Output: ["Alice", "Bob", "Charlie"]
