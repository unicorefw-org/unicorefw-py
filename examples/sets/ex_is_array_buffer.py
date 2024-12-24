# Checks if an object is an ArrayBuffer equivalent (bytearray or memoryview in Python).

result = UniCoreFW.is_array_buffer(bytearray([1, 2, 3]))
print(result)  # Output: True

result = UniCoreFW.is_array_buffer("hello")
print(result)  # Output: False
