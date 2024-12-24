# Adds properties of obj as functions on Unicore itself.

custom_methods = {"triple": lambda x: x * 3, "quadruple": lambda x: x * 4}

UniCoreFW.mixin(custom_methods)
print(UniCoreFW.triple(3))  # Output: 9
print(UniCoreFW.quadruple(2))  # Output: 8
