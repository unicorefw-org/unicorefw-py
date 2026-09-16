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
import os
import sys
import unittest

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

from unicorefw import _  # Now you can import Unicore as usual
from unicorefw.array import _exclude_values


class TestUnicoreArrays(unittest.TestCase):
    # ------- Array and Collection Functions ------- #
    def test_chunk(self):
        result = _.chunk([1, 2, 3, 4, 5], 2)
        self.assertEqual(result, [[1, 2], [3, 4], [5]])

    def test_compact(self):
        arr = [0, 1, False, 2, "", 3]
        self.assertEqual(
            _.compact(arr), [1, 2, 3], "Should remove falsy values from array"
        )

    def test_contains(self):
        self.assertTrue(_.contains([1, 2, 3], 2))
        self.assertFalse(_.contains([1, 2, 3], 4))

    def test_count_by(self):
        arr = [1, 2, 3, 4, 5]
        result = _.count_by(arr, lambda x: x % 2 == 0)
        self.assertEqual(
            result, {False: 3, True: 2}, "Should count elements by the given condition"
        )

    def test_difference(self):
        result = _.difference([1, 2, 3, 4], [2, 4])
        self.assertEqual(result, [1, 3])

    def test_every(self):
        arr = [2, 4, 6]
        self.assertTrue(
            _.every(arr, lambda x: x % 2 == 0),
            "Should return True when all elements satisfy the condition",
        )
        arr = [2, 3, 6]
        self.assertFalse(
            _.every(arr, lambda x: x % 2 == 0),
            "Should return False when not all elements satisfy the condition",
        )

    def test_filter(self):
        result = _.filter([1, 2, 3, 4], lambda x: x % 2 == 0)
        self.assertEqual(result, [2, 4])

    def test_find_median_sorted_arrays(self):
        self.assertEqual(
            _.find_median_sorted_arrays([1, 3], [2]),
            2.0,
            "Should return the median of the merged sorted arrays",
        )
        self.assertEqual(
            _.find_median_sorted_arrays([1, 2], [3, 4]),
            2.5,
            "Should return the median of the merged sorted arrays",
        )

    def test_first(self):
        self.assertEqual(
            _.first([1, 2, 3]), 1, "can pull out the first element of an array"
        )
        self.assertEqual(
            _.first([1, 2, 3]), 1, 'can perform OO-style "first()"'
        )
        self.assertEqual(
            _.first([1, 2, 3], 0),
            [],
            "returns an empty array when n <= 0 (0 case)",
        )
        self.assertEqual(
            _.first([1, 2, 3], -1),
            [],
            "returns an empty array when n <= 0 (negative case)",
        )
        self.assertEqual(
            _.first([1, 2, 3], 2), [1, 2], "can fetch the first n elements"
        )
        self.assertEqual(
            _.first([1, 2, 3], 5),
            [1, 2, 3],
            "returns the whole array if n > length",
        )
        result = (lambda: _.first(4, 3, 2, 1))()
        self.assertEqual(result, 4, "works on an arguments object")
        result = _.map([[1, 2, 3], [], [1, 2, 3]], lambda x: _.first(x))
        self.assertEqual(list(result), [1, None, 1], "works well with _.map")
        self.assertEqual(
            _.first(None), None, "returns undefined when called on null"
        )
        self.assertEqual(
            _.first([], 10),
            [],
            "returns an empty array when called with an explicit number of elements to return",
        )
        self.assertEqual(
            _.first([], 1),
            [],
            "returns an empty array when called with an explicit number of elements to return",
        )
        self.assertEqual(
            _.first(None, 5),
            [],
            "returns an empty array when called with an explicit number of elements to return",
        )
        self.assertEqual(
            _.first([]), None, "return undefined when called on a empty array"
        )

    def test_find(self):
        arr = [1, 2, 3, 4]
        # Should find the first element matching x > 2
        found = _.find(arr, lambda x: x > 2)
        self.assertEqual(found, 3)

        # Should return None if no match
        not_found = _.find(arr, lambda x: x > 10)
        self.assertIsNone(not_found)

        # Test exception-safety (func that might raise)
        def raiser(x):
            if x == 3:
                raise ValueError("Test error")
            return False

        # Should skip elements that cause exceptions
        found_exception = _.find(arr, raiser)
        self.assertIsNone(found_exception)

    def test_find_first_last_reduce_and_without_edge_paths(self):
        with self.assertRaises(TypeError):
            _.find(1, lambda value: True)
        with self.assertRaises(TypeError):
            _.find([1], None)
        self.assertEqual(_.first(n=2), [])
        self.assertEqual(_.last(n=2), [])
        self.assertEqual(_.reduce([1, 2], lambda left, right: left + right, None), 3)
        self.assertEqual(_.without([[1], [2]], [1]), [[2]])

    def test_last(self):
        # Single list argument
        self.assertEqual(_.last([1, 2, 3]), 3, "Should return the last element")

        # last n elements
        self.assertEqual(_.last([1, 2, 3, 4], n=2), [3, 4])

        # Edge cases
        self.assertIsNone(_.last([]), "Empty list => None")
        self.assertEqual(
            _.last([], n=3), [], "Empty list => empty list when n specified"
        )

        # Multiple args scenario
        self.assertEqual(
            _.last(5, 6, 7),
            7,
            "If called like last(5,6,7) => returns the last argument",
        )
        self.assertEqual(_.last(5), 5)
        self.assertEqual(_.last([1, 2], 1), [2])
        self.assertEqual(_.last([1, 2], 0), [])

    def test_unzip_last_index_and_chunk_boundaries(self):
        self.assertEqual(_.unzip([]), [])
        with self.assertRaises(ValueError):
            _.unzip([(1,), (2, 3)])
        self.assertEqual(_.last_index_of([], 1), -1)
        self.assertEqual(_.chunk([1, 2], 0), [])

    def test_sampling_indexing_and_grouping_validation_edges(self):
        self.assertEqual(_.sample([1, 2], 0), [])
        self.assertIn(_.sample([1, 2], 1), [1, 2])
        rows = [{"id": 1}, {"id": 2}]
        self.assertEqual(_.index_by(rows, lambda row: row["id"]), {1: rows[0], 2: rows[1]})
        with self.assertRaises(TypeError):
            _.count_by(1, lambda value: value)
        with self.assertRaises(TypeError):
            _.count_by([1], None)
        self.assertEqual(_.count_by([1, 2, 3], lambda value: 1 / (value - 2)), {-1.0: 1, 1.0: 1})
        with self.assertRaises(TypeError):
            _.group_by(1, lambda value: value)
        with self.assertRaises(TypeError):
            _.group_by([1], None)
        self.assertEqual(_.group_by([1, 2, 3], lambda value: 1 / (value - 2)), {-1.0: [1], 1.0: [3]})

    def test_array_extrema_empty_and_key_paths(self):
        self.assertIsNone(_.max_value([]))
        self.assertIsNone(_.min_value([]))
        self.assertEqual(_.max_value([1, 3, 2]), 3)
        self.assertEqual(_.min_value([1, 3, 2]), 1)
        rows = [{"score": 2}, {"score": 5}]
        self.assertEqual(_.max_value(rows, key_func=lambda row: row["score"]), rows[1])
        self.assertEqual(_.min_value(rows, key_func=lambda row: row["score"]), rows[0])

    def test_median_partition_adjustment_paths(self):
        self.assertEqual(_.find_median_sorted_arrays([10, 11], [1, 2, 3, 4, 5, 6]), 4.5)
        self.assertEqual(_.find_median_sorted_arrays([1, 2, 3, 4], [10]), 3.0)

    def test_drop_fill_and_index_scalar_boundaries(self):
        self.assertEqual(_.drop_while([1, 2], lambda value: True), [])
        self.assertEqual(_.drop_right_while([1, 2], lambda value: True), [])
        values = []
        self.assertIs(_.fill(values, 1), values)
        self.assertEqual(_.find_index([1, 2, 3], 2), 1)
        self.assertEqual(_.find_last_index([1, 2, 1], 1), 2)

    def test_flatten_intersection_intersperse_and_nth_edges(self):
        self.assertEqual(_.flatten_depth([[1], [2]], 0), [[1], [2]])
        self.assertEqual(_.flatten_depth(None), [])
        self.assertEqual(_.flatten_depth(3), [3])
        self.assertEqual(_.intersection_with([1, 1, 2], [1, 2]), [1, 2])
        self.assertEqual(_.intersperse([1], 0), [1])
        self.assertIsNone(_.nth([1, 2], 9))
        self.assertIsNone(_.nth([1, 2], -9))

    def test_shift_take_while_and_unhashable_uniq_by_edges(self):
        values = []
        self.assertIsNone(_.shift(values))
        self.assertEqual(_.take_while([1, 2], lambda value: True), [1, 2])
        self.assertEqual(_.uniq_by([[1], [1], [2]], lambda value: value), [[1], [2]])
        self.assertEqual(_.without([[1]], 1), [[1]])
        self.assertEqual(_exclude_values([[1], [2]], (1,)), [[1], [2]])

    def test_nested_zip_intercalate_pop_and_slice_edges(self):
        self.assertEqual(_.zip_object_deep(["a.b", "a.c"], [1, 2]), {"a": {"b": 1, "c": 2}})
        with self.assertRaises(TypeError):
            _.zip_object_deep(["0"], [1])
        self.assertEqual(_.intercalate([1, [2]], [0]), [1, 0, 2])
        with self.assertRaises(IndexError):
            _.pop([])
        values = [1, 2, 3]
        self.assertEqual(_.pop(values, -1), 3)
        self.assertEqual(_.slice_("abc", 9), [])

    def test_pull_at_reduce_comparator_and_sort_validation_edges(self):
        values = list(range(12))
        self.assertEqual(_.pull_at(values, list(range(9))), [9, 10, 11])
        self.assertEqual(_.ft_reduce(lambda left, right: left + right, [1, 2, 3]), 6)
        self.assertEqual(_.ft_reduce(lambda left, right: left + right, [], 4), 4)
        with self.assertRaises(TypeError):
            _.ft_reduce(lambda left, right: left + right, [])
        key = _.ft_cmp_to_key(lambda left, right: left - right)
        self.assertEqual(sorted([3, 1, 2], key=key), [1, 2, 3])
        with self.assertRaises(TypeError):
            _.sort(tuple([2, 1]))
        with self.assertRaises(TypeError):
            _.sort([2, 1], comparator=1)
        with self.assertRaises(TypeError):
            _.sort([2, 1], key=1)
        self.assertEqual(_.sort([]), [])

    def test_unzip_with_and_zip_with_validation_edges(self):
        self.assertEqual(_.unzip_with([]), [])
        self.assertEqual(_.unzip_with([[1, 2], [3, 4]], lambda left, right: left + right), [4, 6])
        with self.assertRaises(TypeError):
            _.unzip_with("bad")
        with self.assertRaises(TypeError):
            _.unzip_with([[1], 2])
        self.assertEqual(_.unzip_with([[], [1]]), [])
        with self.assertRaises(TypeError):
            _.unzip_with([[1]], 1)
        with self.assertRaises(TypeError):
            _.unzip_with([[1]], lambda value: value + "x")
        self.assertEqual(_.zip_with(), [])

    def test_array_remaining_validation_and_comparator_paths(self):
        # Exercise every rich-comparison operator exposed by the comparator key.
        key_type = _.ft_cmp_to_key(lambda left, right: left - right)
        left, right = key_type(1), key_type(2)
        self.assertTrue(left < right)
        self.assertTrue(right > left)
        self.assertTrue(left <= right)
        self.assertTrue(right >= left)
        self.assertTrue(left != right)
        self.assertTrue(left == key_type(1))

        self.assertEqual(_.uniq_by((1, 2, 1), lambda value: value), [1, 2])
        self.assertEqual(
            _.zip_object_deep(["items[0].name", "items[1].name"], ["a", "b"]),
            {"items": [{"name": "a"}, {"name": "b"}]},
        )
        self.assertEqual(
            _.zip_object_deep([["items[0].name", "a"], ["items[1].name", "b"]]),
            {"items": [{"name": "a"}, {"name": "b"}]},
        )
        self.assertEqual(_.zip_object_deep(["items[0]"], ["a"]), {"items": ["a"]})
        self.assertEqual(
            _.zip_object_deep(["items[0]", "items[0].name"], ["old", "new"]),
            {"items": [{"name": "new"}]},
        )
        with self.assertRaises(TypeError):
            _.sort([1, 2], comparator=lambda left, right: left + "x")
        self.assertEqual(_.xor_with([1, 2], lambda left, right: left == right), [1, 2])
        self.assertEqual(_.xor_with([1, 2], [2, 3], lambda left, right: left == right), [1, 3])
        self.assertEqual(
            _.xor_with([1, 2], [2, 3], [3, 4], lambda left, right: left == right),
            [1, 4],
        )
        with self.assertRaises(ValueError):
            _.xor_with([1])
        with self.assertRaises(TypeError):
            _.xor_with([1], 1)
        with self.assertRaises(TypeError):
            _.xor_with([1], "bad", lambda left, right: left == right)
        with self.assertRaises(TypeError):
            _.xor_with([1], [2], lambda left, right: left + "x")
        with self.assertRaises(TypeError):
            _.xor_with([1], [2], lambda left, right: right + "x")

    def test_uniq(self):
        arr = [1, 2, 2, 3, 1, 4]
        uniq_arr = _.uniq(arr)
        # Because set-based deduplication is not guaranteed to preserve order,
        # the function returns a list but order may vary. Let's check content:
        self.assertEqual(set(uniq_arr), {1, 2, 3, 4})
        self.assertEqual(len(uniq_arr), 4, "Should remove duplicates")

        # Edge case: empty array
        self.assertEqual(_.uniq([]), [])

    def test_flatten(self):
        result = _.flatten([1, [2, [3, 4]], 5], 2)
        self.assertEqual(result, [1, 2, 3, 4, 5])
        self.assertEqual(_.flatten([[], [[]], []]), [], "supports empty arrays")
        self.assertEqual(
            _.flatten([[], [[]], []], True),
            [[]],
            "can shallowly flatten empty arrays",
        )
        list_ = [1, [2], [3, [[[4]]]]]
        self.assertEqual(
            _.flatten(list_), [1, 2, 3, 4], "can flatten nested arrays"
        )
        self.assertEqual(
            _.flatten(list_, True),
            [1, 2, 3, [[[4]]]],
            "can shallowly flatten nested arrays",
        )
        list_ = [[1], [2], [3], [[4]]]
        self.assertEqual(
            _.flatten(list_, True),
            [1, 2, 3, [4]],
            "can shallowly flatten arrays containing only other arrays",
        )
        list_ = [1, [2], [[3]], [[[4]]]]
        self.assertEqual(
            _.flatten(list_, 2),
            [1, 2, 3, [4]],
            "can flatten arrays to a given depth",
        )
        self.assertEqual(
            _.flatten(list_, 0), list_, "can flatten arrays to depth of 0"
        )
        # self.assertEqual(_.flatten(list_, False), [1, 2, 3, 4], 'false means deep')
        # result = (lambda: _.flatten(1, [2], [3, [[[4]]]]))()
        # self.assertEqual(result, [1, 2, 3, 4], 'works on an arguments object')
        # self.assertEqual(_.flatten(None), [], 'supports null')
        # self.assertEqual(_.flatten(None), [], 'supports undefined')
        # self.assertEqual(_.flatten(list_, -1), list_, 'can flatten arrays to depth of -1')
        # self.assertEqual(len(_.flatten([range(10), range(10), 5, 1, 3], True)), 23, 'can flatten medium length arrays')
        # self.assertEqual(len(_.flatten([range(10), range(10), 5, 1, 3])), 23, 'can shallowly flatten medium length arrays')
        # self.assertEqual(len(_.flatten([[None] * 1000000, range(56000), 5, 1, 3])), 1056003, 'can handle massive arrays')
        # self.assertEqual(len(_.flatten([[None] * 1000000, range(56000), 5, 1, 3], True)), 1056003, 'can handle massive arrays in shallow mode')
        x = range(100000)
        for i in range(1000):
            x = [x]
        # self.assertEqual(_.flatten(x), range(100000), 'can handle very deep arrays')
        self.assertEqual(
            _.flatten(x, True),
            x[0],
            "can handle very deep arrays in shallow mode",
        )

    def test_group_by(self):
        arr = [1, 2, 3, 4]
        result = _.group_by(arr, lambda x: x % 2)
        self.assertEqual(
            result,
            {1: [1, 3], 0: [2, 4]},
            "Should group elements by the given condition",
        )

    def test_index_by(self):
        arr = [{"id": 1, "value": "a"}, {"id": 2, "value": "b"}]
        result = _.index_by(arr, "id")
        self.assertEqual(
            result,
            {1: {"id": 1, "value": "a"}, 2: {"id": 2, "value": "b"}},
            "Should index elements by the given key",
        )

    def test_initial(self):
        self.assertEqual(
            _.initial([1, 2, 3, 4, 5]),
            [1, 2, 3, 4],
            "returns all but the last element",
        )
        self.assertEqual(
            _.initial([1, 2, 3, 4], 2),
            [1, 2],
            "returns all but the last n elements",
        )
        self.assertEqual(
            _.initial([1, 2, 3, 4], 6),
            [],
            "returns an empty array when n > length",
        )
        # result = (lambda: _.initial(1, 2, 3, 4))()
        # self.assertEqual(result, [1, 2, 3], 'works on an arguments object')
        # result = map(lambda x: _.initial(x), [[1, 2, 3], [1, 2, 3]])
        # self.assertEqual(list(_.flatten(result)), [1, 2, 1, 2], 'works well with _.map')

    def test_intersection(self):
        result = _.intersection([1, 2, 3], [2, 3, 4])
        self.assertEqual(result, [2, 3])

    def test_invoke(self):
        class TestClass:
            def double(self):
                return self.value * 2 # type: ignore

        obj = TestClass()
        obj.value = 5 # type: ignore
        result = _.invoke([obj], "double")
        self.assertEqual(
            result, [10], "Should invoke the method on each object in the array"
        )

    def test_last_index_of(self):
        arr = [1, 2, 3, 2, 1]
        self.assertEqual(
            _.last_index_of(arr, 2),
            3,
            "Should return the last index of the given value",
        )

    def test_map_object(self):
        result = _.map_object({"a": 1, "b": 2}, lambda x: x * 2)
        self.assertEqual(result, {"a": 2, "b": 4})

    def test_max(self):
        arr = [1, 3, 2, 5, 4]
        self.assertEqual(_.max(arr), 5, "Should return the maximum value")

    def test_min(self):
        arr = [1, 3, 2, 5, 4]
        self.assertEqual(_.min(arr), 1, "Should return the minimum value")

    def test_object(self):
        keys = ["a", "b", "c"]
        values = [1, 2, 3]
        self.assertEqual(
            _.object(keys, values),
            {"a": 1, "b": 2, "c": 3},
            "Should create an object from keys and values",
        )

    def test_partition(self):
        arr = [1, 2, 3, 4, 5]
        result = _.partition(arr, lambda x: x % 2 == 0)
        self.assertEqual(
            result, [[2, 4], [1, 3, 5]], "Should partition array based on predicate"
        )

    def test_pluck(self):
        result = _.pluck([{"a": 1}, {"a": 2}], "a")
        self.assertEqual(result, [1, 2])

    def test_range(self):
        self.assertEqual(_.range(5), [0, 1, 2, 3, 4])
        self.assertEqual(_.range(1, 5), [1, 2, 3, 4])
        self.assertEqual(_.range(1, 10, 2), [1, 3, 5, 7, 9])

    def test_reduce(self):
        result = _.reduce([1, 2, 3, 4], lambda acc, x: acc + x, 0)
        self.assertEqual(result, 10)

    def test_reject(self):
        arr = [1, 2, 3, 4]
        result = _.reject(arr, lambda x: x % 2 == 0)
        self.assertEqual(result, [1, 3], "Should reject elements based on predicate")

    def test_rest(self):
        result = _.rest([1, 2, 3, 4], 2)
        self.assertEqual(result, [3, 4])
        numbers = [1, 2, 3, 4]
        self.assertEqual(
            _.rest(numbers), [2, 3, 4], "fetches all but the first element"
        )
        self.assertEqual(
            _.rest(numbers, 0),
            [1, 2, 3, 4],
            "returns the whole array when index is 0",
        )
        self.assertEqual(
            _.rest(numbers, 2),
            [3, 4],
            "returns elements starting at the given index",
        )
        # result = (lambda: _.rest(1, 2, 3, 4))()
        # self.assertEqual(result, [2, 3, 4], 'works on an arguments object')
        # result = map(lambda x: _.rest(x), [[1, 2, 3], [1, 2, 3]])
        # self.assertEqual(list(_.flatten(result)), [2, 3, 2, 3], 'works well with _.map')

    def test_sample(self):
        array = [1, 2, 3, 4, 5]
        sample = _.sample(array, 2)
        self.assertEqual(len(sample), 2)
        for item in sample:
            self.assertIn(item, array)

    def test_shuffle(self):
        array = [1, 2, 3, 4, 5]
        shuffled = _.shuffle(array)
        self.assertCountEqual(shuffled, array)  # Same elements, different order

    def test_size(self):
        self.assertEqual(_.size([1, 2, 3]), 3)
        self.assertEqual(_.size({"a": 1, "b": 2}), 2)

    def test_some(self):
        arr = [1, 2, 3, 4]
        self.assertTrue(
            _.some(arr, lambda x: x > 3),
            "Should return True if some elements match the condition",
        )
        self.assertFalse(
            _.some(arr, lambda x: x > 4),
            "Should return False if no elements match the condition",
        )

    def test_sort_by(self):
        arr = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        result = _.sort_by(arr, lambda x: x["age"])
        self.assertEqual(
            result,
            [{"name": "Bob", "age": 25}, {"name": "Alice", "age": 30}],
            "Should sort array by specified key function",
        )

    def test_to_array(self):
        self.assertEqual(_.to_array((1, 2, 3)), [1, 2, 3])
        self.assertEqual(_.to_array({"a": 1, "b": 2}), [1, 2])

    def test_union(self):
        result = _.union([1, 2], [2, 3])
        self.assertEqual(result, [1, 2, 3])

    def test_unzip(self):
        arr = [(1, "a"), (2, "b"), (3, "c")]
        self.assertEqual(
            _.unzip(arr),
            [[1, 2, 3], ["a", "b", "c"]],
            "Should unzip array of tuples",
        )

    def test_where(self):
        result = _.where([{"a": 1}, {"a": 2}, {"a": 1}], {"a": 1})
        self.assertEqual(result, [{"a": 1}, {"a": 1}])

    def test_without(self):
        arr = [1, 2, 3, 4]
        self.assertEqual(
            _.without(arr, 2, 4),
            [1, 3],
            "Should return array without specified values",
        )

    def test_zip(self):
        arr1 = [1, 2, 3]
        arr2 = ["a", "b", "c"]
        self.assertEqual(
            _.zip(arr1, arr2),
            [(1, "a"), (2, "b"), (3, "c")],
            "Should zip arrays into tuples",
        )
