# Debounces a function so it only runs after waiting a specified period.

debounced_func = UniCoreFW.debounce(lambda: print("Called"), 1000)
debounced_func()  # Waits 1 second to call
debounced_func()  # Resets the timer
