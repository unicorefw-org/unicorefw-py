# Predicate function that might raise an exception
def safe_divide(x):
    return 10 / x == 2  # Will raise ZeroDivisionError if x == 0


array = [0, 1, 2, 5]

result = UniCoreFW.find(array, safe_divide)
print(result)  # Output: 5
