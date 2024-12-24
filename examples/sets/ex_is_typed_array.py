# Checks if an object is an array.array type.

from array import array

result = UniCoreFW.is_typed_array(array("i", [1, 2, 3]))
print(result)  # Output: True

result = UniCoreFW.is_typed_array([1, 2, 3])
print(result)  # Output: False
