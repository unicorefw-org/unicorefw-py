# Removes duplicates, whether the data is simple integers or complex objects.

# Removing duplicates from numbers
array = [1, 2, 2, 3, 4, 4, 5]
result = UniCoreFW.uniq(array)
print(result)  # Output: [1, 2, 3, 4, 5]

# Removing duplicates from strings
array = ["apple", "banana", "apple", "cherry"]
result = UniCoreFW.uniq(array)
print(result)  # Output: ["apple", "banana", "cherry"]
