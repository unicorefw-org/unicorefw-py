# Checks if an object is a WeakKeyDictionary.

from weakref import WeakKeyDictionary

result = UniCoreFW.is_weak_map(WeakKeyDictionary())
print(result)  # Output: True

result = UniCoreFW.is_weak_map({})
print(result)  # Output: False
