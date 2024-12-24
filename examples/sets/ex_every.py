# Checks if every element in the array matches the predicate.

array = [2, 4, 6]
result = UniCoreFW.every(array, lambda x: x % 2 == 0)
print(result)  # Output: True
