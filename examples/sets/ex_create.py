# Creates an object with a specified prototype and optional properties.
class Proto:
    greeting = "Hello"


instance = UniCoreFW.create(Proto(), {"name": "Alice"})
print(instance.greeting)  # Output: "Hello"
print(instance.name)  # Output: "Alice"
