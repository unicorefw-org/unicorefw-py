# Filters out falsy values from an array with different types of falsy values.
array = [0, "apple", False, None, "banana", "", 7]
result = UniCoreFW.compact(array)
print(result)  # Output: ["apple", "banana", 7]
