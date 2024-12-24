# Checks if an object is a DataView equivalent (memoryview in Python).

buffer = bytearray([1, 2, 3])
view = memoryview(buffer)
result = UniCoreFW.is_data_view(view)
print(result)  # Output: True

result = UniCoreFW.is_data_view(buffer)
print(result)  # Output: False
