import re
import sys
import os
from datetime import date
from array import array
from weakref import WeakKeyDictionary, WeakSet
from xml.etree.ElementTree import Element
import unittest

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

from unicorefw import UniCoreFW  # Now you can import Unicore as usual

class TestTemplateEdgeCases(unittest.TestCase):
    def test_is_string(self):
        assert UniCoreFW.is_string("test")
        assert not UniCoreFW.is_string(123)

    def test_is_number(self):
        assert UniCoreFW.is_number(10)
        assert UniCoreFW.is_number(3.14)
        assert not UniCoreFW.is_number("3.14")

    def test_is_array_and_object(self):
        assert UniCoreFW.is_array([1,2,3])
        assert not UniCoreFW.is_array((1,2,3))
        assert UniCoreFW.is_object({"a":1})
        assert not UniCoreFW.is_object([("a",1)])

    def test_is_function_and_boolean(self):
        assert UniCoreFW.is_function(lambda x: x)
        def foo(): pass
        assert UniCoreFW.is_function(foo)
        assert UniCoreFW.is_boolean(True)
        assert UniCoreFW.is_boolean(False)
        assert not UniCoreFW.is_boolean(0)

    def test_is_date_and_reg_exp(self):
        assert UniCoreFW.is_date(date.today())
        assert not UniCoreFW.is_date("2025-06-30")
        patt = re.compile(r"\d+")
        assert UniCoreFW.is_reg_exp(patt)
        assert not UniCoreFW.is_reg_exp("123")

    def test_is_error_null_undefined(self):
        assert UniCoreFW.is_error(ValueError("error"))
        assert not UniCoreFW.is_error("error")
        assert UniCoreFW.is_null(None)
        assert not UniCoreFW.is_null(0)
        assert UniCoreFW.is_undefined(None)
        assert not UniCoreFW.is_undefined(False)

    def test_is_finite_and_nan(self):
        assert UniCoreFW.is_finite(0)
        assert UniCoreFW.is_finite(1.5)
        assert not UniCoreFW.is_finite(float("inf"))
        assert UniCoreFW.is_nan(float("nan"))
        assert not UniCoreFW.is_nan(123)

    def test_is_map_set_and_arguments(self):
        assert UniCoreFW.is_map({"a":1})
        assert not UniCoreFW.is_map([1,2])
        assert UniCoreFW.is_set({1,2})
        assert not UniCoreFW.is_set([1,2])
        assert UniCoreFW.is_arguments((1,2))
        assert not UniCoreFW.is_arguments([1,2])

    def test_is_array_buffer_and_data_view_and_typed_array(self):
        arr = array('i', [1,2,3])
        assert UniCoreFW.is_array_buffer(arr)
        mv = memoryview(b"abc")
        assert UniCoreFW.is_data_view(mv)
        assert UniCoreFW.is_typed_array(arr)

    def test_is_weak_map_and_weak_set_and_element(self):
        wk = WeakKeyDictionary()
        assert UniCoreFW.is_weak_map(wk)
        assert not UniCoreFW.is_weak_map({})
        ws = WeakSet()
        assert UniCoreFW.is_weak_set(ws)
        assert not UniCoreFW.is_weak_set(set())
        el = Element("tag")
        assert UniCoreFW.is_element(el)
        assert not UniCoreFW.is_element({"tag": None})

    def test_is_empty(self):
        assert UniCoreFW.is_empty(None)
        assert UniCoreFW.is_empty([])
        assert UniCoreFW.is_empty({})
        assert UniCoreFW.is_empty("")
        assert not UniCoreFW.is_empty([0])
        # Test non-len iterable
        def gen(): yield 1
        assert not UniCoreFW.is_empty(gen())
        assert UniCoreFW.is_empty(iter([]))

    def test_is_symbol(self):
        import types as _builtin_types
        assert UniCoreFW.is_symbol(_builtin_types.ModuleType)
        assert UniCoreFW.is_symbol(_builtin_types.FunctionType)
        assert UniCoreFW.is_symbol(UniCoreFW.is_symbol)
        assert not UniCoreFW.is_symbol(123)

    def test_is_equal(self):
        assert UniCoreFW.is_equal(1,1)
        assert not UniCoreFW.is_equal(1,2)
        assert UniCoreFW.is_equal([1,2],[1,2])
        assert not UniCoreFW.is_equal([1,2],[2,1])
        assert UniCoreFW.is_equal({"a":1,"b":[2,3]},{"b":[2,3],"a":1})
        # cyclic
        a = []; a.append(a)
        b = []; b.append(b)
        assert UniCoreFW.is_equal(a,b)
        # different cycle
        c = []; c.append(c); c.append(1)
        d = []; d.append(d); d.append(2)
        assert not UniCoreFW.is_equal(c,d)
