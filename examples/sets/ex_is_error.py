# Checks if an object is an exception.

result = UniCoreFW.is_error(ValueError("An error occurred"))
print(result)  # Output: True

result = UniCoreFW.is_error("error")
print(result)  # Output: False
