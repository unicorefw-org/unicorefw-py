# Returns a function that negates a predicate function’s result.

is_even = lambda x: x % 2 == 0
is_odd = UniCoreFW.negate(is_even)
print(is_odd(3))  # Output: True
