# Checks if an object is a WeakSet.

from weakref import WeakSet

result = UniCoreFW.is_weak_set(WeakSet())
print(result)  # Output: True

result = UniCoreFW.is_weak_set({1, 2, 3})
print(result)  # Output: False
