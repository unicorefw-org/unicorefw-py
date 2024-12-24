# Composes multiple functions so that the result of each function is passed to the next from right to left.


def add_two(x):
    return x + 2


def multiply_by_three(x):
    return x * 3


# First adds 2, then multiplies the result by 3
composed_func = UniCoreFW.compose(multiply_by_three, add_two)
print(composed_func(4))  # Output: 18 (4 + 2 = 6, 6 * 3 = 18)
