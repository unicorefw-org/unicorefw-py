# Indexes an array by a function’s result for each element.

array = [{"name": "Alice"}, {"name": "Bob"}]
result = UniCoreFW.index_by(array, lambda x: x["name"])
print(result)  # Output: {"Alice": {"name": "Alice"}, "Bob": {"name": "Bob"}}
