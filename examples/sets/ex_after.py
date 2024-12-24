# Creates a function that will only run after it has been called a specified number of times.


def show_message():
    print("This message shows after 3 calls!")


after_three = UniCoreFW.after(3, show_message)
after_three()  # No output
after_three()  # No output
after_three()  # Output: "This message shows after 3 calls!"
after_three()  # Output: "This message shows after 3 calls!" (every time after)
