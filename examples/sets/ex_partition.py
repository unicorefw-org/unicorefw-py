# Splits an array into two arrays: one for elements that match the predicate and one for elements that don't.
array = [1, 2, 3, 4, 5]
result = UniCoreFW.partition(array, lambda x: x % 2 == 0)
print(result)  # Output: ([2, 4], [1, 3, 5])
