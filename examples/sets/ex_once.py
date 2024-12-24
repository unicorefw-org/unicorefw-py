# Creates a function that can only be called once. Subsequent calls return the result of the first call.


def initialize():
    print("Initializing...")


initialize_once = UniCoreFW.once(initialize)
initialize_once()  # Output: "Initializing..."
initialize_once()  # No output, function only runs once
