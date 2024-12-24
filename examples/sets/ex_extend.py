# Copies properties from source objects to obj.

obj = {"name": "Alice"}
source1 = {"age": 25}
source2 = {"city": "Paris"}
result = UniCoreFW.extend(obj, source1, source2)
print(result)  # Output: {"name": "Alice", "age": 25, "city": "Paris"}
