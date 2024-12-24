# Throttles a function to only be called once in a specified time period (milliseconds).
import time

throttled_func = UniCoreFW.throttle(lambda: print("Called"), 1000)
throttled_func()  # Prints "Called"
time.sleep(0.5)
throttled_func()  # Does nothing
time.sleep(1)
throttled_func()  # Prints "Called" after 1 second
