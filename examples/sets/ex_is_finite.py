# Checks if a number is finite (not infinite or NaN).

result = UniCoreFW.is_finite(123)
print(result)  # Output: True

result = UniCoreFW.is_finite(float("inf"))
print(result)  # Output: False
