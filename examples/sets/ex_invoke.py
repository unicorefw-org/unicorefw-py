# Calls a specified method on each item in an array.


class Item:
    def __init__(self, value):
        self.value = value

    def double(self):
        return self.value * 2


array = [Item(2), Item(3), Item(4)]
result = UniCoreFW.invoke(array, "double")
print(result)  # Output: [4, 6, 8]
