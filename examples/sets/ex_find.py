# Finds the first element that meets a condition, like finding the first even number.

array = [1, 3, 5, 6, 7]
result = UniCoreFW.find(array, lambda x: x % 2 == 0)
print(result)  # Output: 6 (first even number)

# Finding the first number greater than 10
array = [4, 6, 9, 12]
result = UniCoreFW.find(array, lambda x: x > 10)
print(result)  # Output: 12
