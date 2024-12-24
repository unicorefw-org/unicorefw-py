# Wraps a function within another wrapper function.


def greet(name):
    return f"Hello, {name}!"


def excited_greet(greet_func, name):
    return f"{greet_func(name)} :)"


wrapped_greet = UniCoreFW.wrap(greet, excited_greet)
print(wrapped_greet("Alice"))  # Output: "Hello, Alice! :)"
