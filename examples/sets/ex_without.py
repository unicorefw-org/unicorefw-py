# Removes specified values from the array, with examples for various data types.

# Removing numbers from an array
array = [1, 2, 3, 4, 5]
result = UniCoreFW.without(array, 2, 4)
print(result)  # Output: [1, 3, 5]

# Removing strings from an array
array = ["apple", "banana", "cherry"]
result = UniCoreFW.without(array, "banana")
print(result)  # Output: ["apple", "cherry"]
