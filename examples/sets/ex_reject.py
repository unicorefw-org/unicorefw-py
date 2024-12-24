# Returns elements that do not match the predicate.

array = [1, 2, 3, 4]
result = UniCoreFW.reject(array, lambda x: x % 2 == 0)
print(result)  # Output: [1, 3]
