# Partially applies arguments to a function.
def add(x, y):
    return x + y


add_five = UniCoreFW.partial(add, 5)
print(add_five(10))  # Output: 15
