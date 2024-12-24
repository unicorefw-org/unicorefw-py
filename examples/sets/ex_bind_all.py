# Binds specified methods to an object so that this always refers to the object.
class Person:
    def __init__(self, name):
        self.name = name

    def greet(self):
        return f"Hello, {self.name}"


person = Person("Alice")
UniCoreFW.bind_all(person, "greet")
print(person.greet())  # Output: "Hello, Alice"
