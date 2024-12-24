# Checks if an object is None (since Python doesn’t have undefined).

result = UniCoreFW.is_undefined(None)
print(result)  # Output: True

result = UniCoreFW.is_undefined(123)
print(result)  # Output: False
