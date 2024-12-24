# Passes value into func and returns value.


def logger(x):
    print(f"Logging value: {x}")


result = UniCoreFW.tap(5, logger)
# Output: Logging value: 5
print(result)  # Output: 5
