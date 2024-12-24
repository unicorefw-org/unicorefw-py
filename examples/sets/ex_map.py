# Applies a function to each element, such as squaring numbers or formatting strings.

# Squaring numbers
array = [1, 2, 3, 4]
result = UniCoreFW.map(array, lambda x: x ** 2)
print(result)  # Output: [1, 4, 9, 16]

# Formatting strings
array = ["apple", "banana", "cherry"]
result = UniCoreFW.map(array, lambda x: x.upper())
print(result)  # Output: ['APPLE', 'BANANA', 'CHERRY']
