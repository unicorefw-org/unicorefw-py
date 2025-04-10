#!/usr/bin/env python3
#############################################################################################
# /tests/array_functions_tests.py - Tests for Unicore arrays and conditional functions      #
# Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.Info                               #
#                                                                                           #
# This file is part of UniCoreFW. You can redistribute it and/or modify                     #
# it under the terms of the [BSD-3-Clause] as published by                                  #
# the Free Software Foundation.                                                             #
# You should have received a copy of the [BSD-3-Clause] license                             #
# along with UniCoreFW. If not, see https://www.gnu.org/licenses/.                          #
#############################################################################################
import unittest
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from unicorefw import UniCoreFW  # Now you can import Unicore as usual


class TestUnicoreArrays(unittest.TestCase):
    # ------- Array and Collection Functions ------- #
    def test_chunk(self):
        result = UniCoreFW.chunk([1, 2, 3, 4, 5], 2)
        self.assertEqual(result, [[1, 2], [3, 4], [5]])

    def test_compact(self):
        arr = [0, 1, False, 2, "", 3]
        self.assertEqual(
            UniCoreFW.compact(arr), [1, 2, 3], "Should remove falsy values from array"
        )

    def test_contains(self):
        self.assertTrue(UniCoreFW.contains([1, 2, 3], 2))
        self.assertFalse(UniCoreFW.contains([1, 2, 3], 4))

    def test_count_by(self):
        arr = [1, 2, 3, 4, 5]
        result = UniCoreFW.count_by(arr, lambda x: x % 2 == 0)
        self.assertEqual(
            result, {False: 3, True: 2}, "Should count elements by the given condition"
        )

    def test_difference(self):
        result = UniCoreFW.difference([1, 2, 3, 4], [2, 4])
        self.assertEqual(result, [1, 3])

    def test_every(self):
        arr = [2, 4, 6]
        self.assertTrue(
            UniCoreFW.every(arr, lambda x: x % 2 == 0),
            "Should return True when all elements satisfy the condition",
        )
        arr = [2, 3, 6]
        self.assertFalse(
            UniCoreFW.every(arr, lambda x: x % 2 == 0),
            "Should return False when not all elements satisfy the condition",
        )

    def test_filter(self):
        result = UniCoreFW.filter([1, 2, 3, 4], lambda x: x % 2 == 0)
        self.assertEqual(result, [2, 4])

    def test_find_median_sorted_arrays(self):
        self.assertEqual(
            UniCoreFW.find_median_sorted_arrays([1, 3], [2]),
            2.0,
            "Should return the median of the merged sorted arrays",
        )
        self.assertEqual(
            UniCoreFW.find_median_sorted_arrays([1, 2], [3, 4]),
            2.5,
            "Should return the median of the merged sorted arrays",
        )

    def test_first(self):
        self.assertEqual(
            UniCoreFW.first([1, 2, 3]), 1, "can pull out the first element of an array"
        )
        self.assertEqual(
            UniCoreFW.first([1, 2, 3]), 1, 'can perform OO-style "first()"'
        )
        self.assertEqual(
            UniCoreFW.first([1, 2, 3], 0),
            [],
            "returns an empty array when n <= 0 (0 case)",
        )
        self.assertEqual(
            UniCoreFW.first([1, 2, 3], -1),
            [],
            "returns an empty array when n <= 0 (negative case)",
        )
        self.assertEqual(
            UniCoreFW.first([1, 2, 3], 2), [1, 2], "can fetch the first n elements"
        )
        self.assertEqual(
            UniCoreFW.first([1, 2, 3], 5),
            [1, 2, 3],
            "returns the whole array if n > length",
        )
        result = (lambda: UniCoreFW.first(4, 3, 2, 1))()
        self.assertEqual(result, 4, "works on an arguments object")
        result = UniCoreFW.map([[1, 2, 3], [], [1, 2, 3]], lambda x: UniCoreFW.first(x))
        self.assertEqual(list(result), [1, None, 1], "works well with UniCoreFW.map")
        self.assertEqual(
            UniCoreFW.first(None), None, "returns undefined when called on null"
        )
        self.assertEqual(
            UniCoreFW.first([], 10),
            [],
            "returns an empty array when called with an explicit number of elements to return",
        )
        self.assertEqual(
            UniCoreFW.first([], 1),
            [],
            "returns an empty array when called with an explicit number of elements to return",
        )
        self.assertEqual(
            UniCoreFW.first(None, 5),
            [],
            "returns an empty array when called with an explicit number of elements to return",
        )
        self.assertEqual(
            UniCoreFW.first([]), None, "return undefined when called on a empty array"
        )

    def test_find(self):
        arr = [1, 2, 3, 4]
        # Should find the first element matching x > 2
        found = UniCoreFW.find(arr, lambda x: x > 2)
        self.assertEqual(found, 3)

        # Should return None if no match
        not_found = UniCoreFW.find(arr, lambda x: x > 10)
        self.assertIsNone(not_found)

        # Test exception-safety (func that might raise)
        def raiser(x):
            if x == 3:
                raise ValueError("Test error")
            return False

        # Should skip elements that cause exceptions
        found_exception = UniCoreFW.find(arr, raiser)
        self.assertIsNone(found_exception)

    def test_last(self):
        # Single list argument
        self.assertEqual(UniCoreFW.last([1, 2, 3]), 3, "Should return the last element")

        # last n elements
        self.assertEqual(UniCoreFW.last([1, 2, 3, 4], n=2), [3, 4])

        # Edge cases
        self.assertIsNone(UniCoreFW.last([]), "Empty list => None")
        self.assertEqual(
            UniCoreFW.last([], n=3), [], "Empty list => empty list when n specified"
        )

        # Multiple args scenario
        self.assertEqual(
            UniCoreFW.last(5, 6, 7),
            7,
            "If called like last(5,6,7) => returns the last argument",
        )

    def test_uniq(self):
        arr = [1, 2, 2, 3, 1, 4]
        uniq_arr = UniCoreFW.uniq(arr)
        # Because set-based deduplication is not guaranteed to preserve order,
        # the function returns a list but order may vary. Let's check content:
        self.assertEqual(set(uniq_arr), {1, 2, 3, 4})
        self.assertEqual(len(uniq_arr), 4, "Should remove duplicates")

        # Edge case: empty array
        self.assertEqual(UniCoreFW.uniq([]), [])

    def test_flatten(self):
        result = UniCoreFW.flatten([1, [2, [3, 4]], 5], 2)
        self.assertEqual(result, [1, 2, 3, 4, 5])
        self.assertEqual(UniCoreFW.flatten([[], [[]], []]), [], "supports empty arrays")
        self.assertEqual(
            UniCoreFW.flatten([[], [[]], []], True),
            [[]],
            "can shallowly flatten empty arrays",
        )
        list_ = [1, [2], [3, [[[4]]]]]
        self.assertEqual(
            UniCoreFW.flatten(list_), [1, 2, 3, 4], "can flatten nested arrays"
        )
        self.assertEqual(
            UniCoreFW.flatten(list_, True),
            [1, 2, 3, [[[4]]]],
            "can shallowly flatten nested arrays",
        )
        list_ = [[1], [2], [3], [[4]]]
        self.assertEqual(
            UniCoreFW.flatten(list_, True),
            [1, 2, 3, [4]],
            "can shallowly flatten arrays containing only other arrays",
        )
        list_ = [1, [2], [[3]], [[[4]]]]
        self.assertEqual(
            UniCoreFW.flatten(list_, 2),
            [1, 2, 3, [4]],
            "can flatten arrays to a given depth",
        )
        self.assertEqual(
            UniCoreFW.flatten(list_, 0), list_, "can flatten arrays to depth of 0"
        )
        # self.assertEqual(UniCoreFW.flatten(list_, False), [1, 2, 3, 4], 'false means deep')
        # result = (lambda: UniCoreFW.flatten(1, [2], [3, [[[4]]]]))()
        # self.assertEqual(result, [1, 2, 3, 4], 'works on an arguments object')
        # self.assertEqual(UniCoreFW.flatten(None), [], 'supports null')
        # self.assertEqual(UniCoreFW.flatten(None), [], 'supports undefined')
        # self.assertEqual(UniCoreFW.flatten(list_, -1), list_, 'can flatten arrays to depth of -1')
        # self.assertEqual(len(UniCoreFW.flatten([range(10), range(10), 5, 1, 3], True)), 23, 'can flatten medium length arrays')
        # self.assertEqual(len(UniCoreFW.flatten([range(10), range(10), 5, 1, 3])), 23, 'can shallowly flatten medium length arrays')
        # self.assertEqual(len(UniCoreFW.flatten([[None] * 1000000, range(56000), 5, 1, 3])), 1056003, 'can handle massive arrays')
        # self.assertEqual(len(UniCoreFW.flatten([[None] * 1000000, range(56000), 5, 1, 3], True)), 1056003, 'can handle massive arrays in shallow mode')
        x = range(100000)
        for i in range(1000):
            x = [x]
        # self.assertEqual(UniCoreFW.flatten(x), range(100000), 'can handle very deep arrays')
        self.assertEqual(
            UniCoreFW.flatten(x, True),
            x[0],
            "can handle very deep arrays in shallow mode",
        )

    def test_group_by(self):
        arr = [1, 2, 3, 4]
        result = UniCoreFW.group_by(arr, lambda x: x % 2)
        self.assertEqual(
            result,
            {1: [1, 3], 0: [2, 4]},
            "Should group elements by the given condition",
        )

    def test_index_by(self):
        arr = [{"id": 1, "value": "a"}, {"id": 2, "value": "b"}]
        result = UniCoreFW.index_by(arr, "id")
        self.assertEqual(
            result,
            {1: {"id": 1, "value": "a"}, 2: {"id": 2, "value": "b"}},
            "Should index elements by the given key",
        )

    def test_initial(self):
        self.assertEqual(
            UniCoreFW.initial([1, 2, 3, 4, 5]),
            [1, 2, 3, 4],
            "returns all but the last element",
        )
        self.assertEqual(
            UniCoreFW.initial([1, 2, 3, 4], 2),
            [1, 2],
            "returns all but the last n elements",
        )
        self.assertEqual(
            UniCoreFW.initial([1, 2, 3, 4], 6),
            [],
            "returns an empty array when n > length",
        )
        # result = (lambda: UniCoreFW.initial(1, 2, 3, 4))()
        # self.assertEqual(result, [1, 2, 3], 'works on an arguments object')
        # result = map(lambda x: UniCoreFW.initial(x), [[1, 2, 3], [1, 2, 3]])
        # self.assertEqual(list(UniCoreFW.flatten(result)), [1, 2, 1, 2], 'works well with UniCoreFW.map')

    def test_intersection(self):
        result = UniCoreFW.intersection([1, 2, 3], [2, 3, 4])
        self.assertEqual(result, [2, 3])

    def test_invoke(self):
        class TestClass:
            def double(self):
                return self.value * 2

        obj = TestClass()
        obj.value = 5
        result = UniCoreFW.invoke([obj], "double")
        self.assertEqual(
            result, [10], "Should invoke the method on each object in the array"
        )

    def test_last_index_of(self):
        arr = [1, 2, 3, 2, 1]
        self.assertEqual(
            UniCoreFW.last_index_of(arr, 2),
            3,
            "Should return the last index of the given value",
        )

    def test_map_object(self):
        result = UniCoreFW.map_object({"a": 1, "b": 2}, lambda x: x * 2)
        self.assertEqual(result, {"a": 2, "b": 4})

    def test_max(self):
        arr = [1, 3, 2, 5, 4]
        self.assertEqual(UniCoreFW.max(arr), 5, "Should return the maximum value")

    def test_min(self):
        arr = [1, 3, 2, 5, 4]
        self.assertEqual(UniCoreFW.min(arr), 1, "Should return the minimum value")

    def test_object(self):
        keys = ["a", "b", "c"]
        values = [1, 2, 3]
        self.assertEqual(
            UniCoreFW.object(keys, values),
            {"a": 1, "b": 2, "c": 3},
            "Should create an object from keys and values",
        )

    def test_partition(self):
        arr = [1, 2, 3, 4, 5]
        result = UniCoreFW.partition(arr, lambda x: x % 2 == 0)
        self.assertEqual(
            result, [[2, 4], [1, 3, 5]], "Should partition array based on predicate"
        )

    def test_pluck(self):
        result = UniCoreFW.pluck([{"a": 1}, {"a": 2}], "a")
        self.assertEqual(result, [1, 2])

    def test_range(self):
        self.assertEqual(UniCoreFW.range(5), [0, 1, 2, 3, 4])
        self.assertEqual(UniCoreFW.range(1, 5), [1, 2, 3, 4])
        self.assertEqual(UniCoreFW.range(1, 10, 2), [1, 3, 5, 7, 9])

    def test_reduce(self):
        result = UniCoreFW.reduce([1, 2, 3, 4], lambda acc, x: acc + x, 0)
        self.assertEqual(result, 10)

    def test_reject(self):
        arr = [1, 2, 3, 4]
        result = UniCoreFW.reject(arr, lambda x: x % 2 == 0)
        self.assertEqual(result, [1, 3], "Should reject elements based on predicate")

    def test_rest(self):
        result = UniCoreFW.rest([1, 2, 3, 4], 2)
        self.assertEqual(result, [3, 4])
        numbers = [1, 2, 3, 4]
        self.assertEqual(
            UniCoreFW.rest(numbers), [2, 3, 4], "fetches all but the first element"
        )
        self.assertEqual(
            UniCoreFW.rest(numbers, 0),
            [1, 2, 3, 4],
            "returns the whole array when index is 0",
        )
        self.assertEqual(
            UniCoreFW.rest(numbers, 2),
            [3, 4],
            "returns elements starting at the given index",
        )
        # result = (lambda: UniCoreFW.rest(1, 2, 3, 4))()
        # self.assertEqual(result, [2, 3, 4], 'works on an arguments object')
        # result = map(lambda x: UniCoreFW.rest(x), [[1, 2, 3], [1, 2, 3]])
        # self.assertEqual(list(UniCoreFW.flatten(result)), [2, 3, 2, 3], 'works well with _.map')

    def test_sample(self):
        array = [1, 2, 3, 4, 5]
        sample = UniCoreFW.sample(array, 2)
        self.assertEqual(len(sample), 2)
        for item in sample:
            self.assertIn(item, array)

    def test_shuffle(self):
        array = [1, 2, 3, 4, 5]
        shuffled = UniCoreFW.shuffle(array)
        self.assertCountEqual(shuffled, array)  # Same elements, different order

    def test_size(self):
        self.assertEqual(UniCoreFW.size([1, 2, 3]), 3)
        self.assertEqual(UniCoreFW.size({"a": 1, "b": 2}), 2)

    def test_some(self):
        arr = [1, 2, 3, 4]
        self.assertTrue(
            UniCoreFW.some(arr, lambda x: x > 3),
            "Should return True if some elements match the condition",
        )
        self.assertFalse(
            UniCoreFW.some(arr, lambda x: x > 4),
            "Should return False if no elements match the condition",
        )

    def test_sort_by(self):
        arr = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        result = UniCoreFW.sort_by(arr, lambda x: x["age"])
        self.assertEqual(
            result,
            [{"name": "Bob", "age": 25}, {"name": "Alice", "age": 30}],
            "Should sort array by specified key function",
        )

    def test_to_array(self):
        self.assertEqual(UniCoreFW.to_array((1, 2, 3)), [1, 2, 3])
        self.assertEqual(UniCoreFW.to_array({"a": 1, "b": 2}), [1, 2])

    def test_union(self):
        result = UniCoreFW.union([1, 2], [2, 3])
        self.assertEqual(result, [1, 2, 3])

    def test_unzip(self):
        arr = [(1, "a"), (2, "b"), (3, "c")]
        self.assertEqual(
            UniCoreFW.unzip(arr),
            [[1, 2, 3], ["a", "b", "c"]],
            "Should unzip array of tuples",
        )

    def test_where(self):
        result = UniCoreFW.where([{"a": 1}, {"a": 2}, {"a": 1}], {"a": 1})
        self.assertEqual(result, [{"a": 1}, {"a": 1}])

    def test_without(self):
        arr = [1, 2, 3, 4]
        self.assertEqual(
            UniCoreFW.without(arr, 2, 4),
            [1, 3],
            "Should return array without specified values",
        )

    def test_zip(self):
        arr1 = [1, 2, 3]
        arr2 = ["a", "b", "c"]
        self.assertEqual(
            UniCoreFW.zip(arr1, arr2),
            [(1, "a"), (2, "b"), (3, "c")],
            "Should zip arrays into tuples",
        )
