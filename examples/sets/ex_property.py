# Returns a function that retrieves a specified property from an object.

get_name = UniCoreFW.property("name")
obj = {"name": "Alice", "age": 25}
print(get_name(obj))  # Output: "Alice"
