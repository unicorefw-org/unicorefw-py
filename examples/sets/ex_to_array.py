# Converts an object to an array, handling lists, sets, dictionaries, and iterables.

# Converting dictionary values to an array
obj = {"a": 1, "b": 2, "c": 3}
result = UniCoreFW.to_array(obj)
print(result)  # Output: [1, 2, 3]

# Converting a set to an array
obj = {1, 2, 3, 4}
result = UniCoreFW.to_array(obj)
print(result)  # Output: [1, 2, 3, 4]
