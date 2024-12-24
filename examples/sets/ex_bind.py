# Binds a function to a specified context with optional arguments.


class MyClass:
    def __init__(self, name):
        self.name = name

    def greet(self, greeting):
        return f"{greeting}, {self.name}!"


obj = MyClass("Alice")
bound_greet = UniCoreFW.bind(obj.greet, obj, "Hello")
print(bound_greet())  # Expected output: "Hello, Alice!"
