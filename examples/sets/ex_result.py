# If the property is a function, it invokes it with optional arguments; otherwise, it returns the property value.

# Test object setup
obj = {
    "name": "Alice",
    "greet": lambda greeting, name="Alice": f"{greeting}, {name}!",  # Use a parameter to avoid obj reference
}

# Running the tests
result = UniCoreFW.result(obj, "name")
print(result)  # Expected output: "Alice"

result = UniCoreFW.result(obj, "greet", "Hello")
print(result)  # Expected output: "Hello, Alice!"
