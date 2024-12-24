# Wraps an object in a chainable class, allowing method chaining.

result = (
    UniCoreFW.chain([1, 2, 3, 4]).map(lambda x: x * 2).filter(lambda x: x > 4).value()
)
print(result)  # Output: [6, 8]


# Example 1: Using chain with a string
result = UniCoreFW.chain("hello").map(lambda c: c.upper()).reverse().value()

print(result)  # Output: "OLLEH"

# Example 2: Sorting a string
result = UniCoreFW.chain("banana").sort_by().value()

print(result)  # Output: "aaabnn"

# Example 3: Getting the first character(s) of a string
result = UniCoreFW.chain("world").first(3).value()

print(result)  # Output: "wor"

# Example 4: Combining methods
result = UniCoreFW.chain("apple").map(lambda c: c.upper()).sort_by().first(3).value()

print(result)  # Output: "AEL"

# Example 5: Original list remains unchanged
original_list = [3, 1, 4, 1, 5]
result = UniCoreFW.chain(original_list).sort_by().reverse().value()

print(result)  # Output: [5, 4, 3, 1, 1]
print(original_list)  # Output: [3, 1, 4, 1, 5]
