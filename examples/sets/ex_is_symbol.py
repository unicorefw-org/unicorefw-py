# Checks if an object is a unique constant-like object (None, NotImplemented, Ellipsis).

result = UniCoreFW.is_symbol(None)
print(result)  # Output: True

result = UniCoreFW.is_symbol("hello")
print(result)  # Output: False
