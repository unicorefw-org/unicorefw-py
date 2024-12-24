# Checks if an object is a function.

result = UniCoreFW.is_function(lambda x: x + 1)
print(result)  # Output: True

result = UniCoreFW.is_function(123)
print(result)  # Output: False
