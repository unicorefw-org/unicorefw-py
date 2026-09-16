#!/usr/bin/env python3
##############################################################################
# /tests/test_function.py - Tests for Unicore functions                     #
# Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.Info                #
#                                                                            #
# This file is part of UniCoreFW. You can redistribute it and/or modify      #
# it under the terms of the [BSD-3-Clause] as published by                   #
# the Free Software Foundation.                                              #
# You should have received a copy of the [BSD-3-Clause] license              #
# along with UniCoreFW. If not, see https://www.gnu.org/licenses/.           #
##############################################################################

import os
import sys
import unittest
from importlib import import_module
from unittest.mock import patch

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

from unicorefw import _
from unicorefw.function import reduce_ as reduce_impl
from unicorefw.security import ResourceLimitError

function_impl = import_module("unicorefw.function")

class TestUniCoreFWFunctions(unittest.TestCase):
    def test_matches(self):
        # matches(attrs) returns a function that checks if an object has those attrs
        checker = _.matches({"a": 1, "b": 2})
        self.assertTrue(checker({"a": 1, "b": 2, "c": 3}))
        self.assertFalse(checker({"a": 1, "b": 9}))
        self.assertFalse(checker({"a": 1}))

    def test_property_func(self):
        # property_func("someKey") => returns a function that fetches obj["someKey"] or obj.someKey
        get_name = _.property_func("name")
        self.assertEqual(get_name({"name": "Alice"}), "Alice")

        # Non-dict fallback
        class Person:
            def __init__(self, name):
                self.name = name

        bob = Person("Bob")
        self.assertEqual(get_name(bob), "Bob")

        # Missing property => None
        self.assertIsNone(get_name({}))

    def test_after(self):
        calls = []

        def record_call():
            calls.append("called")

        after_func = _.after(3, record_call)
        after_func()
        after_func()
        after_func()
        self.assertEqual(len(calls), 1, "Should only run after the third call")

    def test_before(self):
        def adder(x, y):
            return x + y

        before_func = _.before(3, adder)
        self.assertEqual(before_func(1, 2), 3, "Before should allow execution")

    def test_bind_all(self):
        class MyClass:
            def __init__(self, value):
                self.value = value

            def get_value(self):
                return self.value

        obj = MyClass(10)
        _.bind_all(obj, "get_value")
        self.assertEqual(obj.get_value(), 10)

    def test_bind(self):
        def greet(greeting, name):
            return f"{greeting}, {name}!"

        bound_func = _.bind(greet, None, "Hello")
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

        composed = _.compose(add1, times2)
        self.assertEqual(
            composed(3), 7, "Compose should apply functions from right to left"
        )

    def test_debounce(self):
        import time

        calls = []

        def record_call():
            calls.append(time.time())

        debounced = _.debounce(record_call, 0.1)
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

        _.defer(append_to_output)
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

        _.delay(record_call, 0.1)
        time.sleep(0.2)
        self.assertEqual(
            calls, ["called"], "Should delay the execution of the function"
        )

    def test_memoize(self):
        def factorial(n):
            return n * factorial(n - 1) if n > 1 else 1

        memoized_factorial = _.memoize(factorial)
        self.assertEqual(memoized_factorial(5), 120)
        self.assertEqual(memoized_factorial(5), 120)  # Should hit the cache

    def test_negate(self):
        def is_even(x):
            return x % 2 == 0

        is_odd = _.negate(is_even)
        self.assertTrue(
            is_odd(3),
            "Negate should return the opposite of the original function result",
        )

    def test_once(self):
        func = _.once(lambda: "called")
        result = func()
        self.assertEqual(result, "called")
        self.assertIsNone(func())

    def test_function_fallback_and_validation_branches(self):
        self.assertEqual(function_impl.invoke(["abc", object()], "upper"), ["ABC", None])
        self.assertTrue(function_impl.iteratee({"a": 1})({"a": 1, "b": 2}))
        self.assertTrue(function_impl.iteratee(2)(2))
        self.assertEqual(function_impl.flow()(5), 5)
        self.assertEqual(function_impl.flow_right()(5), 5)
        self.assertEqual(function_impl.flip(lambda a, b: a - b)(2, 5), 3)
        with self.assertRaises(TypeError):
            function_impl.flip(None)

        class Plain:
            def existing(self):
                return 1

        instance = Plain()
        self.assertIsNone(function_impl.bind_all(instance, "existing", "missing"))

    def test_enhanced_debounce_cancels_max_timer_when_regular_schedule_fails(self):
        class FakeTimer:
            def __init__(self):
                self.cancelled = False

            def cancel(self):
                self.cancelled = True

        timer = FakeTimer()
        calls = [0]

        def schedule(self, delay, callback):
            calls[0] += 1
            if calls[0] == 1:
                return timer
            raise RuntimeError("schedule failed")

        with patch.object(function_impl._TimerBudget, "schedule", schedule):
            debounced = function_impl.enhanced_debounce(lambda value: value, 1, max_wait=2)
            with self.assertRaises(RuntimeError):
                debounced("value")
        self.assertTrue(timer.cancelled)

    def test_enhanced_debounce_execute_cancels_both_timers(self):
        callbacks = []

        class FakeTimer:
            def __init__(self):
                self.cancelled = False

            def cancel(self):
                self.cancelled = True

        timers = []

        def schedule(self, delay, callback):
            timer = FakeTimer()
            timers.append(timer)
            callbacks.append(callback)
            return timer

        with patch.object(function_impl._TimerBudget, "schedule", schedule):
            debounced = function_impl.enhanced_debounce(lambda value: value, 1, max_wait=2)
            self.assertEqual(debounced("value"), "value")
            callbacks[-1]()
        self.assertTrue(all(timer.cancelled for timer in timers))

    def test_enhanced_debounce_zero_delay_and_cancel(self):
        import threading

        called = threading.Event()
        values = []

        def record(value):
            values.append(value)
            called.set()
            return value

        debounced = function_impl.enhanced_debounce(record, 0, max_wait=1_000)
        self.assertEqual(debounced("first"), "first")
        self.assertTrue(called.wait(timeout=2))
        debounced.cancel()
        import time

        deadline = time.monotonic() + 2.5
        while debounced.pending_timer_count() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertEqual(debounced.pending_timer_count(), 0)

        with self.assertRaises(TypeError):
            function_impl.enhanced_debounce(None, 0)

    def test_debounce_wrapper_and_direct_map_filter_helpers(self):
        wrapped = function_impl.debounce_(lambda value: value + 1, 0)
        self.assertEqual(wrapped(1), 2)
        wrapped.cancel()
        wrapped_with_max = function_impl.debounce_(lambda value: value * 2, 0, max_wait=1_000)
        self.assertEqual(wrapped_with_max(2), 4)
        wrapped_with_max.cancel()
        self.assertEqual(function_impl.map_([1, 2], lambda value: value + 1), [2, 3])
        self.assertEqual(function_impl.filter_([1, 2, 3], lambda value: value > 1), [2, 3])

    def test_enhanced_debounce_replaces_timers_and_handles_budget_failure(self):
        debounced = function_impl.enhanced_debounce(lambda value: value, 1_000, max_wait=2_000)
        self.assertEqual(debounced("first"), "first")
        self.assertEqual(debounced("second"), "first")
        debounced.cancel()
        import time

        deadline = time.monotonic() + 2.5
        while debounced.pending_timer_count() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertEqual(debounced.pending_timer_count(), 0)

        limited = function_impl.enhanced_debounce(
            lambda value: value,
            1_000,
            max_wait=2_000,
            max_pending_timers=1,
        )
        with self.assertRaises(ResourceLimitError):
            limited("value")
        limited.cancel()

    def test_partial(self):
        def multiply(x, y):
            return x * y

        partial_func = _.partial(multiply, 5)
        self.assertEqual(
            partial_func(2), 10, "Should partially apply the first argument"
        )

    def test_throttle(self):
        import time

        calls = []

        def record_call():
            calls.append(time.time())

        throttled = _.throttle(record_call, 0.1)
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

        wrapped_greet = _.wrap(greet, lambda f, name: f(name).upper())
        self.assertEqual(wrapped_greet("world"), "HELLO, WORLD!")

    def test_argument_and_collection_helpers(self):
        transformed = _.over_args(lambda a, b, c: (a, b, c), [lambda x: x + 1, str])
        self.assertEqual(transformed(1, 2, 3), (2, "2", 3))

        spread = _.spread(lambda a, b: a + b)
        self.assertEqual(spread([2, 3]), 5)
        self.assertEqual(_.unary(lambda value, extra=0: value + extra)(4, 9), 4)

        self.assertEqual(_.map_([1, 2], lambda value: value * 2), [2, 4])
        self.assertEqual(_.filter_([1, 2, 3], lambda value: value % 2), [1, 3])
        self.assertEqual(reduce_impl([1, 2, 3], lambda left, right: left + right), 6)
        self.assertEqual(reduce_impl([1, 2], lambda left, right: left * right, 3), 6)
        with self.assertRaises(TypeError):
            reduce_impl([], lambda left, right: left + right)

    def test_predicate_combinators_and_argument_order(self):
        self.assertTrue(_.allany(lambda value: value > 0)([1, 2, 3]))
        self.assertFalse(_.allany(lambda value: value % 2 == 0)([2, 3]))
        self.assertTrue(_.anyof(lambda value: value < 0, lambda value: value == 2)(2))
        self.assertFalse(_.anyof(lambda value: value < 0)(2))

        with self.assertRaises(TypeError):
            _.after("bad", 2)
        with self.assertRaises(TypeError):
            _.before("bad", 2)


if __name__ == "__main__":
    unittest.main()
