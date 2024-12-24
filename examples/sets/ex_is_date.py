# Checks if an object is a date.

from datetime import date

result = UniCoreFW.is_date(date.today())
print(result)  # Output: True

result = UniCoreFW.is_date("2023-01-01")
print(result)  # Output: False
