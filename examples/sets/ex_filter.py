# Filters an array of objects, returning only those that match the given key-value pairs.

# Filters elements in an array based on a predicate function.
array = [1, 2, 3, 4]
result = UniCoreFW.filter(array, lambda x: x % 2 == 0)
print(result)  # Output: [2, 4]
