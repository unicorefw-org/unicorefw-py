# Aggregates array values, like calculating the sum or finding the product.

# Summing values
array = [1, 2, 3, 4]
result = UniCoreFW.reduce(array, lambda acc, x: acc + x, 0)
print(result)  # Output: 10

# Calculating the product
result = UniCoreFW.reduce(array, lambda acc, x: acc * x, 1)
print(result)  # Output: 24
