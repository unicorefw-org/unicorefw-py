# Creates a function that can be called up to n times. After n calls, it always returns the last result.


def greet():
    print("Hello!")


limited_greet = UniCoreFW.before(3, greet)
limited_greet()  # Output: "Hello!"
limited_greet()  # Output: "Hello!"
limited_greet()  # Output: "Hello!"
limited_greet()  # No output, limit reached
