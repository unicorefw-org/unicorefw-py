# Creates a shallow copy of an object or array.

obj = {"name": "Alice", "age": 25}
cloned_obj = UniCoreFW.clone(obj)
cloned_obj["name"] = "Bob"
print(obj)  # Output: {"name": "Alice", "age": 25}
print(cloned_obj)  # Output: {"name": "Bob", "age": 25}
