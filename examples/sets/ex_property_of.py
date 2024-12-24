# Returns a function that retrieves a property from a given object.

obj = {"name": "Alice", "age": 25}
get_property = UniCoreFW.property_of(obj)
print(get_property("age"))  # Output: 25
