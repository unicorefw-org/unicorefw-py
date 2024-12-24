# Checks if an object is a regular expression.

import re

result = UniCoreFW.is_reg_exp(re.compile(r"\d+"))
print(result)  # Output: True

result = UniCoreFW.is_reg_exp("hello")
print(result)  # Output: False
