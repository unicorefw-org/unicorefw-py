# Generates a unique ID, optionally prefixed.

result = UniCoreFW.unique_id("user_")
print(result)  # Output: "user_1" (ID will increment with each call)

result = UniCoreFW.unique_id("order_")
print(result)  # Output: "order_2"
