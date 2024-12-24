# Checks if an object is a tuple, which is the closest to the concept of arguments in Python.

result = UniCoreFW.is_arguments((1, 2, 3))
print(result)  # Output: True

result = UniCoreFW.is_arguments([1, 2, 3])
print(result)  # Output: False
