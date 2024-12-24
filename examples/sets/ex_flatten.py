# Flattens nested arrays into a single array up to a specified depth.

array = [1, [2, [3, [4]]]]
result = UniCoreFW.flatten(array, 2)
print(result)  # Output: [1, 2, 3, [4]]
