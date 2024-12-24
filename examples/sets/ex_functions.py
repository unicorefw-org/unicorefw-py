# Returns a list of all function names on an object.


class MathOps:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b


result = UniCoreFW.functions(MathOps)
print(result)  # Output: ["add", "subtract"]
