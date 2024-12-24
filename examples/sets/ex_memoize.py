# Caches the results of a function call to improve performance for repeated calls.


def slow_square(x):
    print(f"Calculating square of {x}")
    return x * x


memoized_square = UniCoreFW.memoize(slow_square)
print(memoized_square(4))  # Calculates and outputs 16
print(memoized_square(4))  # Outputs 16 without recalculating
