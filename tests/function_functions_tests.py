#!/usr/bin/env python3
##############################################################################
# /tests/function_functions_tests.py - Tests for Unicore functions           #
# Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.Info                #
#                                                                            #
# This file is part of UniCoreFW. You can redistribute it and/or modify      #
# it under the terms of the [BSD-3-Clause] as published by                   #
# the Free Software Foundation.                                              #
# You should have received a copy of the [BSD-3-Clause] license              #
# along with UniCoreFW. If not, see https://www.gnu.org/licenses/.           #
##############################################################################

import unittest
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from unicorefw import UniCoreFW  # Now you can import Unicore as usual

class TestUniCoreFWFunctions(unittest.TestCase):
    def test_after(self):
        calls = []

        def record_call():
            calls.append("called")

        after_func = UniCoreFW.after(3, record_call)
        after_func()
        after_func()
        after_func()
        self.assertEqual(len(calls), 1, "Should only run after the third call")

    def test_before(self):
        def adder(x, y):
            return x + y

        before_func = UniCoreFW.before(3, adder)
        self.assertEqual(before_func(1, 2), 3, "Before should allow execution")

    def test_bind_all(self):
        class MyClass:
            def __init__(self, value):
                self.value = value

            def get_value(self):
                return self.value

        obj = MyClass(10)
        UniCoreFW.bind_all(obj, "get_value")
        self.assertEqual(obj.get_value(), 10)

    def test_bind(self):
        def greet(greeting, name):
            return f"{greeting}, {name}!"

        bound_func = UniCoreFW.bind(greet, None, "Hello")
        self.assertEqual(
            bound_func("Alice"),
            "Hello, Alice!",
            "Should bind the first argument of the function",
        )

    def test_compose(self):
        def add1(x):
            return x + 1

        def times2(x):
            return x * 2

        composed = UniCoreFW.compose(add1, times2)
        self.assertEqual(
            composed(3), 7, "Compose should apply functions from right to left"
        )

    def test_debounce(self):
        import time

        calls = []

        def record_call():
            calls.append(time.time())

        debounced = UniCoreFW.debounce(record_call, 0.1)
        debounced()
        time.sleep(0.2)
        debounced()
        self.assertEqual(
            len(calls), 1, "Debounced function should only call after the wait time"
        )

    def test_defer(self):
        output = []

        def append_to_output():
            output.append("deferred")

        UniCoreFW.defer(append_to_output)
        # Give a small delay to allow defer to execute in background
        import time

        time.sleep(0.1)
        self.assertEqual(output, ["deferred"])

    # ------- Helpers and Miscellaneous ------- #

    def test_delay(self):
        import time

        calls = []

        def record_call():
            calls.append("called")

        UniCoreFW.delay(record_call, 0.1)
        time.sleep(0.2)
        self.assertEqual(
            calls, ["called"], "Should delay the execution of the function"
        )

    def test_memoize(self):
        def factorial(n):
            return n * factorial(n - 1) if n > 1 else 1

        memoized_factorial = UniCoreFW.memoize(factorial)
        self.assertEqual(memoized_factorial(5), 120)
        self.assertEqual(memoized_factorial(5), 120)  # Should hit the cache

    def test_negate(self):
        def is_even(x):
            return x % 2 == 0

        is_odd = UniCoreFW.negate(is_even)
        self.assertTrue(
            is_odd(3),
            "Negate should return the opposite of the original function result",
        )

    def test_once(self):
        func = UniCoreFW.once(lambda: "called")
        result = func()
        self.assertEqual(result, "called")
        self.assertIsNone(func())

    def test_partial(self):
        def multiply(x, y):
            return x * y

        partial_func = UniCoreFW.partial(multiply, 5)
        self.assertEqual(
            partial_func(2), 10, "Should partially apply the first argument"
        )

    def test_throttle(self):
        import time

        calls = []

        def record_call():
            calls.append(time.time())

        throttled = UniCoreFW.throttle(record_call, 0.1)
        throttled()
        throttled()
        self.assertEqual(
            len(calls),
            1,
            "Throttled function should be called only once within the threshold",
        )

    def test_wrap(self):
        def greet(name):
            return f"Hello, {name}!"

        wrapped_greet = UniCoreFW.wrap(greet, lambda f, name: f(name).upper())
        self.assertEqual(wrapped_greet("world"), "HELLO, WORLD!")


if __name__ == "__main__":
    unittest.main()
