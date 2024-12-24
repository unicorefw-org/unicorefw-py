# Delays invoking the function by wait milliseconds.


def delayed_message():
    print("This message is delayed by 1 second")


UniCoreFW.delay(delayed_message, 1000)  # Waits 1 second before printing
