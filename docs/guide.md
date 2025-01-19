UniCoreFW Framework Documentation
===============================

Table of Contents
-----------------

1.  [Introduction](#introduction)
2.  [Installation](#installation)
3.  [Quick Start Guide](#quick-start-guide)
4.  [Core Features](#core-features)
    *   [Dynamic Method Chaining](#dynamic-method-chaining)
    *   [Static Method Usage](#static-method-usage)
5.  [Detailed API Reference](#detailed-api-reference)
    *   [Array Functions](#array-functions)
    *   [Object Functions](#object-functions)
    *   [Utility Functions](#utility-functions)
    *   [Type Checking Functions](#type-checking-functions)
6.  [Examples](#examples)
7.  [Contributing](#contributing)
8.  [License](#license)

1\. Introduction<a name="introduction"></a>
----------------

**UniCoreFW** is a Python library inspired by the popular JavaScript library **Underscore.js**. It provides a set of utility functions for working with arrays, objects, and functions in a more convenient way, supporting method chaining for streamlined and expressive code.

2\. Installation<a name="installation"></a>
----------------

To install the UniCoreFW framework, run:

    pip install unicorefw

3\. Quick Start Guide<a name="quick-start-guide"></a>
---------------------
    from unicorefw import UniCoreFW, UniCoreFWWrapper

    def _(collection):
        return UniCoreFWWrapper(collection)

    # Attach functions from 'UniCoreFW' directly to '_'
    for func_name in dir(UniCoreFW):
        if callable(getattr(UniCoreFW, func_name)) and not func_name.startswith('_'):
            setattr(_, func_name, getattr(UniCoreFW, func_name))

    # Example usage
    result = (
        _([1, 2, 3, 4, 5])
        .map(lambda x: x * 2)
        .filter(lambda x: x > 5)
        .value()
        )
      print(result)  # Output: [6, 8, 10]
      
      # Static function usage
      template = "Name: <%= name %>, Age: <%= age %>"
      context = {"name": "Alice", "age": 25}
      print(_.template(template, context))  # Output: "Name: Alice, Age: 25"

4\. Core Features<a name="core-features"></a>
-----------------

### Dynamic Method Chaining <a name="dynamic-method-chaining"></a>

The `UniCoreFWWrapper` class enables method chaining, allowing you to chain multiple operations on a collection:

    from unicorefw import UniCoreFW, UniCoreFWWrapper

    def _(collection):
        return UniCoreFWWrapper(collection)

    for func_name in dir(UniCoreFW):
        if callable(getattr(UniCoreFW, func_name)) and not func_name.startswith('_'):
            setattr(_, func_name, getattr(UniCoreFW, func_name))

    result = _([1, 2, 3, 4, 5]).map(lambda x: x + 1).filter(lambda x: x % 2 == 0).value()

### Static Method Usage <a name="static-method-usage"></a>

Use static methods directly for one-off utility operations:

    from unicorefw import UniCoreFW
      
      result = _.difference([1, 2, 3], [2, 4])
      print(result)  # Output: [1, 3]

5\. Detailed API Reference<a name="detailed-api-reference"></a>
--------------------------

### Array Functions <a name='array-functions'>

#### 1\. `map(collection, func)`

*   **Description**: Transforms a collection by applying the given function `func` to each element.
*   **Parameters**:
    *   `collection` (list/tuple): The collection to be transformed.
    *   `func` (function): The function to apply to each element.
*   **Returns**: A new collection with the transformed elements.
*   **Example**:
    
        result = _.map([1, 2, 3], lambda x: x * 2)
        print(result)  # Output: [2, 4, 6]
    

#### 2\. `filter(collection, predicate)`

*   **Description**: Filters the elements of the collection that satisfy the given predicate function.
*   **Parameters**:
    *   `collection` (list/tuple): The collection to filter.
    *   `predicate` (function): A function that returns `True` for elements to include.
*   **Returns**: A collection with elements that passed the predicate.
*   **Example**:
    
        result = _.filter([1, 2, 3, 4], lambda x: x % 2 == 0)
        print(result)  # Output: [2, 4]
    

#### 3\. `reduce(collection, func, initial=None)`

*   **Description**: Reduces the collection to a single value by iteratively applying the given function `func`.
*   **Parameters**:
    *   `collection` (list/tuple): The collection to reduce.
    *   `func` (function): A function that takes two arguments, an accumulator and the current value.
    *   `initial` (optional): The initial value for the accumulator.
*   **Returns**: The reduced single value.
*   **Example**:
    
        result = _.reduce([1, 2, 3, 4], lambda acc, x: acc + x, 0)
        print(result)  # Output: 10
    

#### 4\. `find(collection, predicate)`

*   **Description**: Returns the first element in the collection that satisfies the predicate function.
*   **Parameters**:
    *   `collection` (list/tuple): The collection to search through.
    *   `predicate` (function): A function that returns `True` for the desired element.
*   **Returns**: The first element that matches the condition, or `None` if not found.
*   **Example**:
    
        result = _.find([1, 2, 3, 4], lambda x: x > 2)
        print(result)  # Output: 3
    

#### 5\. `uniq(collection)`

*   **Description**: Removes duplicate values from the collection.
*   **Parameters**:
    *   `collection` (list/tuple): The collection to deduplicate.
*   **Returns**: A collection with unique elements.
*   **Example**:
    
        result = _.uniq([1, 2, 2, 3, 4, 4, 5])
        print(result)  # Output: [1, 2, 3, 4, 5]
    

#### 6\. `flatten(collection, depth=None)`

*   **Description**: Flattens nested lists up to the specified depth.
*   **Parameters**:
    *   `collection` (list): The collection to flatten.
    *   `depth` (int, optional): The number of levels to flatten. Defaults to infinite if not specified.
*   **Returns**: A flattened collection.
*   **Example**:
    
        result = _.flatten([1, [2, [3, 4], 5]], depth=2)
        print(result)  # Output: [1, 2, 3, 4, 5]
    

### Object Functions <a name='object-functions'>

#### 7\. `keys(obj)`

*   **Description**: Retrieves all the keys of the given object.
*   **Parameters**:
    *   `obj` (dict/object): The object to get the keys from.
*   **Returns**: A list of keys.
*   **Example**:
    
        result = _.keys({"a": 1, "b": 2, "c": 3})
        print(result)  # Output: ['a', 'b', 'c']
    

#### 8\. `values(obj)`

*   **Description**: Retrieves all the values of the given object.
*   **Parameters**:
    *   `obj` (dict/object): The object to get the values from.
*   **Returns**: A list of values.
*   **Example**:
    
        result = _.values({"a": 1, "b": 2, "c": 3})
        print(result)  # Output: [1, 2, 3]
    

#### 9\. `extend(target, *sources)`

*   **Description**: Copies properties from source objects to the target object.
*   **Parameters**:
    *   `target` (dict): The object to extend.
    *   `*sources` (dict): The source objects to copy properties from.
*   **Returns**: The extended target object.
*   **Example**:
    
        target = {"a": 1}
          result = _.extend(target, {"b": 2}, {"c": 3})
        print(result)  # Output: {'a': 1, 'b': 2, 'c': 3}
    

#### 10\. `invert(obj)`

*   **Description**: Inverts the keys and values of an object.
*   **Parameters**:
    *   `obj` (dict): The object to invert.
*   **Returns**: An object with inverted keys and values.
*   **Example**:
    
        result = _.invert({"a": 1, "b": 2, "c": 3})
        print(result)  # Output: {1: 'a', 2: 'b', 3: 'c'}
    

#### 11\. `unique_id(prefix='')`

*   **Description**: Generates a unique ID with an optional prefix.
*   **Parameters**:
    *   `prefix` (str, optional): A string to prepend to the unique ID.
*   **Returns**: A string representing the unique ID.
*   **Example**:
    
        id1 = _.unique_id('user_')
        print(id1)  # Output: 'user_1'
    

#### 12\. `now()`

*   **Description**: Returns the current timestamp in milliseconds.
*   **Returns**: Integer representing the current timestamp.
*   **Example**:
    
        timestamp = _.now()
        print(timestamp)  # Output: 1633029330000
    

#### 13\. `times(n, func)`

*   **Description**: Invokes the given function `func` `n` times.
*   **Parameters**:
    *   `n` (int): The number of times to invoke the function.
    *   `func` (function): The function to invoke.
*   **Returns**: A list containing the results of each function call.
*   **Example**:
    
        result = _.times(3, lambda i: i * 2)
        print(result)  # Output: [0, 2, 4]
    

#### 14\. `memoize(func)`

*   **Description**: Creates a function that memoizes the results of `func`.
*   **Parameters**:
    *   `func` (function): The function to memoize.
*   **Returns**: The memoized function.
*   **Example**:
    
        square = _.memoize(lambda x: x * x)
        print(square(4))  # Output: 16
    

#### 15\. `delay(func, wait, *args, **kwargs)`

*   **Description**: Invokes `func` after `wait` milliseconds.
*   **Parameters**:
    *   `func` (function): The function to delay.
    *   `wait` (int): The number of milliseconds to wait.
    *   `*args`, `**kwargs`: Arguments and keyword arguments to pass to `func`.
*   **Example**:
    
        _.delay(print, 1000, 'Hello, world!')
    

#### 16\. `debounce(func, wait)`

*   **Description**: Creates a debounced version of `func` that delays invoking until after `wait` milliseconds.
*   **Parameters**:
    *   `func` (function): The function to debounce.
    *   `wait` (int): The number of milliseconds to wait.
*   **Returns**: The debounced function.
*   **Example**:
    
        debounced_func = _.debounce(lambda: print('Called!'), 300)
    

#### 17\. `throttle(func, wait)`

*   **Description**: Creates a throttled version of `func` that only invokes once per `wait` milliseconds.
*   **Parameters**:
    *   `func` (function): The function to throttle.
    *   `wait` (int): The number of milliseconds to wait.
*   **Returns**: The throttled function.
*   **Example**:
    
        throttled_func = _.throttle(lambda: print('Called!'), 300)
    

### Type Checking Functions <a name='type-checking-functions'>

#### 18\. `is_string(obj)`

*   **Description**: Checks if `obj` is a string.
*   **Parameters**:
    *   `obj`: The object to check.
*   **Returns**: `True` if `obj` is a string, otherwise `False`.
*   **Example**:
    
        print(_.is_string("hello"))  # Output: True
    

#### 19\. `is_number(obj)`

*   **Description**: Checks if `obj` is a number.
*   **Parameters**:
    *   `obj`: The object to check.
*   **Returns**: `True` if `obj` is a number, otherwise `False`.
*   **Example**:
    
        print(_.is_number(42))  # Output: True
    

#### 20\. `is_array(obj)`

*   **Description**: Checks if `obj` is an array (list).
*   **Parameters**:
    *   `obj`: The object to check.
*   **Returns**: `True` if `obj` is a list, otherwise `False`.
*   **Example**:
    
        print(_.is_array([1, 2, 3]))  # Output: True
    

#### 21\. `is_object(obj)`

*   **Description**: Checks if `obj` is an object.
*   **Parameters**:
    *   `obj`: The object to check.
*   **Returns**: `True` if `obj` is an object, otherwise `False`.
*   **Example**:
    
        print(_.is_object({"a": 1}))  # Output: True
    

#### 22\. `is_function(obj)`

*   **Description**: Checks if `obj` is a function.
*   **Parameters**:
    *   `obj`: The object to check.
*   **Returns**: `True` if `obj` is a function, otherwise `False`.
*   **Example**:
    
        print(_.is_function(lambda x: x))  # Output: True
    

#### 23\. `is_boolean(obj)`

*   **Description**: Checks if `obj` is a boolean.
*   **Parameters**:
    *   `obj`: The object to check.
*   **Returns**: `True` if `obj` is a boolean, otherwise `False`.
*   **Example**:
    
        print(_.is_boolean(True))  # Output: True
    

#### 24\. `is_date(obj)`

*   **Description**: Checks if `obj` is a `datetime.date` instance.
*   **Parameters**:
    *   `obj`: The object to check.
*   **Returns**: `True` if `obj` is a date, otherwise `False`.
*   **Example**:
    
        from datetime import date
        print(_.is_date(date.today()))  # Output: True
    

#### 25\. `is_null(obj)`

*   **Description**: Checks if `obj` is `None`.
*   **Parameters**:
    *   `obj`: The object to check.
*   **Returns**: `True` if `obj` is `None`, otherwise `False`.
*   **Example**:
    
        print(_.is_null(None))  # Output: True
    

### Utility Functions <a name='utility-functions'>

#### 26\. `noop()`

*   **Description**: A function that does nothing and returns `None`. Useful as a placeholder.
*   **Example**:
    
        result = _.noop()
        print(result)  # Output: None
    

#### 27\. `constant(value)`

*   **Description**: Returns a function that always returns the provided `value`.
*   **Parameters**:
    *   `value`: The value to return.
*   **Returns**: A function.
*   **Example**:
    
        const_func = _.constant(42)
        print(const_func())  # Output: 42
    

#### 28\. `wrap(func, wrapper)`

*   **Description**: Creates a function that wraps `func` within the `wrapper` function.
*   **Parameters**:
    *   `func` (function): The function to wrap.
    *   `wrapper` (function): The wrapper function.
*   **Returns**: A wrapped function.
*   **Example**:
    
        wrapped = _.wrap(lambda x: x * 2, lambda func, x: func(x) + 1)
        print(wrapped(5))  # Output: 11
    

#### 29\. `tap(collection, interceptor)`

*   **Description**: Invokes the `interceptor` function with the `collection` and then returns `collection`. Used to perform side effects.
*   **Parameters**:
    *   `collection`: The collection to tap.
    *   `interceptor` (function): The function to invoke.
*   **Returns**: The original `collection`.
*   **Example**:
    
        result = _.tap([1, 2, 3], lambda x: print("Array: ", x))
          # Output: Array: [1, 2, 3]
        print(result)  # Output: [1, 2, 3]
    

#### 30\. `clone(obj)`

*   **Description**: Creates a shallow copy of `obj`.
*   **Parameters**:
    *   `obj`: The object to clone.
*   **Returns**: A new object that is a shallow copy of `obj`.
*   **Example**:
    
        obj = {"a": 1, "b": 2}
          cloned = _.clone(obj)
        print(cloned)  # Output: {'a': 1, 'b': 2}
    

### Array and Object Manipulation Functions

#### 31\. `compact(array)`

*   **Description**: Removes falsey values (e.g., `None`, `False`, `0`, `""`) from the array.
*   **Parameters**:
    *   `array` (list): The array to compact.
*   **Returns**: A new array without falsey values.
*   **Example**:
    
        result = _.compact([0, 1, False, 2, '', 3])
        print(result)  # Output: [1, 2, 3]
    

#### 32\. `difference(array, *others)`

*   **Description**: Returns the difference between `array` and other arrays.
*   **Parameters**:
    *   `array` (list): The main array.
    *   `*others` (list): Other arrays to exclude elements from.
*   **Returns**: A new array with unique elements from `array` not present in `others`.
*   **Example**:
    
        result = _.difference([1, 2, 3, 4], [2, 4])
        print(result)  # Output: [1, 3]
    

#### 33\. `group_by(collection, key_func)`

*   **Description**: Groups the collection by a key generated by `key_func`.
*   **Parameters**:
    *   `collection` (list/tuple): The collection to group.
    *   `key_func` (function): The function that returns the key for grouping.
*   **Returns**: A dictionary with keys generated by `key_func` and lists of elements as values.
*   **Example**:
    
        result = _.group_by([1.2, 1.4, 2.1, 2.4], lambda x: int(x))
        print(result)  # Output: {1: [1.2, 1.4], 2: [2.1, 2.4]}
    

#### 34\. `partition(array, predicate)`

*   **Description**: Splits `array` into two lists: one with elements that pass `predicate`, and one with elements that fail.
*   **Parameters**:
    *   `array` (list): The array to partition.
    *   `predicate` (function): The function to evaluate.
*   **Returns**: A tuple of two lists.
*   **Example**:
    
        result = _.partition([1, 2, 3, 4], lambda x: x % 2 == 0)
        print(result)  # Output: ([2, 4], [1, 3])
    

#### 35\. `zip(*arrays)`

*   **Description**: Merges multiple arrays by combining corresponding elements into tuples.
*   **Parameters**:
    *   `*arrays`: Arrays to zip.
*   **Returns**: A list of tuples.
*   **Example**:
    
        result = _.zip([1, 2, 3], ['a', 'b', 'c'])
        print(result)  # Output: [(1, 'a'), (2, 'b'), (3, 'c')]
    

#### 36\. `unzip(array_of_tuples)`

*   **Description**: The reverse of `zip`; separates tuples into individual arrays.
*   **Parameters**:
    *   `array_of_tuples` (list of tuples): The collection to unzip.
*   **Returns**: A list of lists.
*   **Example**:
    
        result = _.unzip([(1, 'a'), (2, 'b'), (3, 'c')])
        print(result)  # Output: [[1, 2, 3], ['a', 'b', 'c']]
    

#### 37\. `pairs(obj)`

*   **Description**: Converts an object into a list of `[key, value]` pairs.
*   **Parameters**:
    *   `obj` (dict): The object to convert.
*   **Returns**: A list of `[key, value]` pairs.
*   **Example**:
    
        result = _.pairs({"a": 1, "b": 2})
        print(result)  # Output: [['a', 1], ['b', 2]]
    

#### 38\. `without(array, *values)`

*   **Description**: Returns a copy of `array` with all instances of the provided `values` removed.
*   **Parameters**:
    *   `array` (list): The array to process.
    *   `*values`: Values to exclude.
*   **Returns**: A new array without the specified values.
*   **Example**:
    
        result = _.without([1, 2, 3, 1, 4], 1, 4)
        print(result)  # Output: [2, 3]
    

#### 39\. `invoke(array, method_name, *args)`

*   **Description**: Invokes the method named `method_name` on each item in the array.
*   **Parameters**:
    *   `array` (list): The array of objects.
    *   `method_name` (str): The name of the method to invoke.
    *   `*args`: Additional arguments to pass to the method.
*   **Returns**: A list of results.
*   **Example**:
    
        result = _.invoke([[3, 2, 1], [5, 4]], 'sort')
        print(result)  # Output: [[1, 2, 3], [4, 5]]
    

#### 40\. `pluck(array, key)`

*   **Description**: Extracts a list of property values from an array of objects.
*   **Parameters**:
    *   `array` (list): The array of objects.
    *   `key` (str): The property key to pluck.
*   **Returns**: A list of property values.
*   **Example**:
    
        data = [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]
          result = _.pluck(data, 'age')
        print(result)  # Output: [25, 30]
    

#### 41\. `shuffle(array)`

*   **Description**: Randomly shuffles the elements of the array.
*   **Parameters**:
    *   `array` (list): The array to shuffle.
*   **Returns**: A new array with the elements shuffled.
*   **Example**:
    
        result = _.shuffle([1, 2, 3, 4, 5])
        print(result)  # Output: [3, 1, 5, 2, 4] (order may vary)
    

#### 42\. `sample(array, n=1)`

*   **Description**: Returns a random sample of `n` elements from the array.
*   **Parameters**:
    *   `array` (list): The array to sample from.
    *   `n` (int, optional): The number of elements to sample. Defaults to 1.
*   **Returns**: A list of sampled elements.
*   **Example**:
    
        result = _.sample([1, 2, 3, 4, 5], 2)
        print(result)  # Output: [2, 5] (sample may vary)
    

#### 43\. `sort_by(array, key_func)`

*   **Description**: Sorts the array by the results of `key_func` applied to each element.
*   **Parameters**:
    *   `array` (list): The array to sort.
    *   `key_func` (function): The function that returns the sort key for each element.
*   **Returns**: A new sorted array.
*   **Example**:
    
        result = _.sort_by([{'age': 30}, {'age': 20}, {'age': 25}], lambda x: x['age'])
        print(result)  # Output: [{'age': 20}, {'age': 25}, {'age': 30}]
    

#### 44\. `count_by(collection, key_func)`

*   **Description**: Counts the elements in the collection based on the result of `key_func`.
*   **Parameters**:
    *   `collection` (list/tuple): The collection to count.
    *   `key_func` (function): The function that returns the key for counting.
*   **Returns**: A dictionary with keys generated by `key_func` and counts as values.
*   **Example**:
    
        result = _.count_by(['apple', 'banana', 'apple', 'cherry'], lambda x: len(x))
        print(result)  # Output: {5: 3, 6: 1}
    

#### 45\. `max(collection, key_func=None)`

*   **Description**: Returns the maximum value in the collection, optionally using `key_func` for comparisons.
*   **Parameters**:
    *   `collection` (list/tuple): The collection to search.
    *   `key_func` (function, optional): The function to determine the key for comparison.
*   **Returns**: The maximum value.
*   **Example**:
    
        result = _.max([1, 2, 3, 4], key_func=lambda x: -x)
        print(result)  # Output: 1
    

#### 46\. `min(collection, key_func=None)`

*   **Description**: Returns the minimum value in the collection, optionally using `key_func` for comparisons.
*   **Parameters**:
    *   `collection` (list/tuple): The collection to search.
    *   `key_func` (function, optional): The function to determine the key for comparison.
*   **Returns**: The minimum value.
*   **Example**:
    
        result = _.min([1, 2, 3, 4], key_func=lambda x: -x)
        print(result)  # Output: 4
    

#### 47\. `every(collection, predicate)`

*   **Description**: Checks if all elements in the collection satisfy the `predicate` function.
*   **Parameters**:
    *   `collection` (list/tuple): The collection to evaluate.
    *   `predicate` (function): The function that returns `True` or `False`.
*   **Returns**: `True` if all elements pass the test, `False` otherwise.
*   **Example**:
    
        result = _.every([2, 4, 6], lambda x: x % 2 == 0)
        print(result)  # Output: True
    

#### 48\. `some(collection, predicate)`

*   **Description**: Checks if any elements in the collection satisfy the `predicate` function.
*   **Parameters**:
    *   `collection` (list/tuple): The collection to evaluate.
    *   `predicate` (function): The function that returns `True` or `False`.
*   **Returns**: `True` if any elements pass the test, `False` otherwise.
*   **Example**:
    
        result = _.some([1, 2, 3], lambda x: x > 2)
        print(result)  # Output: True
    

#### 49\. `is_equal(obj1, obj2)`

*   **Description**: Performs a deep comparison between two objects to determine if they are equivalent.
*   **Parameters**:
    *   `obj1`: The first object.
    *   `obj2`: The second object.
*   **Returns**: `True` if the objects are equivalent, `False` otherwise.
*   **Example**:
    
        result = _.is_equal({'a': 1, 'b': {'c': 2}}, {'a': 1, 'b': {'c': 2}})
        print(result)  # Output: True
    

#### 50\. `matches(attrs)`

*   **Description**: Creates a function that checks if an object contains the key-value pairs in `attrs`.
*   **Parameters**:
    *   `attrs` (dict): The key-value pairs to match.
*   **Returns**: A function that checks for matching attributes.
*   **Example**:
    
        matcher = _.matches({'a': 1, 'b': 2})
          result = matcher({'a': 1, 'b': 2, 'c': 3})
        print(result)  # Output: True
    

#### 51\. `iteratee(value)`

*   **Description**: Converts a value into a function suitable for use as an iteratee.
*   **Parameters**:
    *   `value`: The value to convert (e.g., function, key string).
*   **Returns**: A function.
*   **Example**:
    
        iteratee_func = _.iteratee('age')
          result = iteratee_func({'name': 'John', 'age': 30})
        print(result)  # Output: 30
    

#### 52\. `has(obj, key)`

*   **Description**: Checks if `obj` contains the specified `key`.
*   **Parameters**:
    *   `obj` (dict): The object to check.
    *   `key` (str): The key to look for.
*   **Returns**: `True` if `key` is present, `False` otherwise.
*   **Example**:
    
        result = _.has({'a': 1, 'b': 2}, 'b')
        print(result)  # Output: True
    

#### 53\. `invert(obj)`

*   **Description**: Creates an object composed of the inverted keys and values of `obj`.
*   **Parameters**:
    *   `obj` (dict): The object to invert.
*   **Returns**: A new dictionary with inverted keys and values.
*   **Example**:
    
        result = _.invert({'a': 1, 'b': 2})
        print(result)  # Output: {1: 'a', 2: 'b'}
    

#### 54\. `find_index(array, predicate)`

*   **Description**: Returns the index of the first element in `array` that satisfies the `predicate` function.
*   **Parameters**:
    *   `array` (list): The array to search.
    *   `predicate` (function): The function invoked per iteration.
*   **Returns**: The index of the found element, or `-1` if not found.
*   **Example**:
    
        result = _.find_index([1, 2, 3, 4], lambda x: x == 3)
        print(result)  # Output: 2
    

#### 55\. `find_last_index(array, predicate)`

*   **Description**: Returns the index of the last element in `array` that satisfies the `predicate` function.
*   **Parameters**:
    *   `array` (list): The array to search.
    *   `predicate` (function): The function invoked per iteration.
*   **Returns**: The index of the found element, or `-1` if not found.
*   **Example**:
    
        result = _.find_last_index([1, 2, 3, 4, 3], lambda x: x == 3)
        print(result)  # Output: 4
    

#### 56\. `is_arguments(obj)`

*   **Description**: Checks if `obj` is an `arguments` object.
*   **Parameters**:
    *   `obj`: The object to check.
*   **Returns**: `True` if `obj` is an `arguments` object, `False` otherwise.
*   **Example**:
    
        result = _.is_arguments(['arg1', 'arg2'])
        print(result)  # Output: False
    

#### 57\. `is_array_buffer(obj)`

*   **Description**: Checks if `obj` is an `ArrayBuffer`.
*   **Parameters**:
    *   `obj`: The object to check.
*   **Returns**: `True` if `obj` is an `ArrayBuffer`, `False` otherwise.
*   **Example**:
    
        result = _.is_array_buffer(memoryview(b'example'))
        print(result)  # Output: True
    

#### 58\. `is_data_view(obj)`

*   **Description**: Checks if `obj` is a `DataView`.
*   **Parameters**:
    *   `obj`: The object to check.
*   **Returns**: `True` if `obj` is a `DataView`, `False` otherwise.
*   **Example**:
    
        result = _.is_data_view(memoryview(b'example'))
        print(result)  # Output: False
    

#### 59\. `is_element(obj)`

*   **Description**: Checks if `obj` is a DOM element.
*   **Parameters**:
    *   `obj`: The object to check.
*   **Returns**: `True` if `obj` is an element, `False` otherwise.

#### 60\. `is_match(obj, attrs)`

*   **Description**: Checks if `obj` matches the key-value pairs in `attrs`.
*   **Parameters**:
    *   `obj` (dict): The object to check.
    *   `attrs` (dict): The key-value pairs to match.
*   **Returns**: `True` if `obj` matches `attrs`, `False` otherwise.
*   **Example**:
    
        result = _.is_match({'a': 1, 'b': 2}, {'b': 2})
        print(result)  # Output: True
    

#### 61\. `is_symbol(obj)`

*   **Description**: Checks if `obj` is a `Symbol`.
*   **Parameters**:
    *   `obj`: The object to check.
*   **Returns**: `True` if `obj` is a `Symbol`, `False` otherwise.
*   **Example**:
    
        result = _.is_symbol('example')
        print(result)  # Output: False
    

#### 62\. `is_typed_array(obj)`

*   **Description**: Checks if `obj` is a typed array.
*   **Parameters**:
    *   `obj`: The object to check.
*   **Returns**: `True` if `obj` is a typed array, `False` otherwise.
*   **Example**:
    
        result = _.is_typed_array(bytearray([1, 2, 3]))
        print(result)  # Output: True
    

#### 63\. `is_weak_map(obj)`

*   **Description**: Checks if `obj` is a `WeakMap`.
*   **Parameters**:
    *   `obj`: The object to check.
*   **Returns**: `True` if `obj` is a `WeakMap`, `False` otherwise.
*   **Example**:
    
        result = _.is_weak_map({})
        print(result)  # Output: False
    

#### 64\. `is_weak_set(obj)`

*   **Description**: Checks if `obj` is a `WeakSet`.
*   **Parameters**:
    *   `obj`: The object to check.
*   **Returns**: `True` if `obj` is a `WeakSet`, `False` otherwise.
*   **Example**:
    
        result = _.is_weak_set(set([1, 2, 3]))
        print(result)  # Output: False
    

#### 65\. `mixin(obj)`

*   **Description**: Adds functions from `obj` to the UniCoreFW framework, making them available as methods.
*   **Parameters**:
    *   `obj` (dict): A dictionary of functions to add.
*   **Example**:
    
        _.mixin({'triple': lambda x: x * 3})
        print(_.triple(4))  # Output: 12
    

#### 66\. `random(min, max)`

*   **Description**: Returns a random integer between `min` and `max`, inclusive.
*   **Parameters**:
    *   `min` (int): The minimum value.
    *   `max` (int): The maximum value.
*   **Returns**: A random integer.
*   **Example**:
    
        result = _.random(1, 10)
        print(result)  # Output: 7 (value may vary)
    

#### 67\. `size(collection)`

*   **Description**: Returns the size of the collection.
*   **Parameters**:
    *   `collection` (list/tuple/dict): The collection to evaluate.
*   **Returns**: The number of elements in the collection.
*   **Example**:
    
        result = _.size([1, 2, 3])
        print(result)  # Output: 3
    

#### 68\. `sort_by(array, key_func)`

*   **Description**: Sorts the array by the results of `key_func` applied to each element.
*   **Parameters**:
    *   `array` (list): The array to sort.
    *   `key_func` (function): The function that returns the sort key for each element.
*   **Returns**: A new sorted array.
*   **Example**:
    
        result = _.sort_by([{'age': 30}, {'age': 20}, {'age': 25}], lambda x: x['age'])
        print(result)  # Output: [{'age': 20}, {'age': 25}, {'age': 30}]
    

#### 69\. `to_array(collection)`

*   **Description**: Converts a collection to an array.
*   **Parameters**:
    *   `collection` (iterable): The collection to convert.
*   **Returns**: An array representation of the collection.
*   **Example**:
    
        result = _.to_array({1, 2, 3})
        print(result)  # Output: [1, 2, 3]
    

#### 70\. `wrap(func, wrapper)`

*   **Description**: Creates a function that wraps `func` within the `wrapper` function.
*   **Parameters**:
    *   `func` (function): The function to wrap.
    *   `wrapper` (function): The wrapper function.
*   **Returns**: A wrapped function.
*   **Example**:
    
        wrapped = _.wrap(lambda x: x * 2, lambda func, x: func(x) + 1)
        print(wrapped(5))  # Output: 11
    

#### 71\. `invoke_map(collection, path, *args)`

*   **Description**: Invokes the method at `path` for each element in `collection`.
*   **Parameters**:
    *   `collection` (list): The collection to iterate over.
    *   `path` (str): The method name or path.
    *   `*args`: Additional arguments to invoke the method with.
*   **Returns**: A list of results.
*   **Example**:
    
        result = _.invoke_map([[5, 1, 7], [3, 2]], 'sort')
        print(result)  # Output: [[1, 5, 7], [2, 3]]
    

#### 72\. `defer(func, *args)`

*   **Description**: Defers the execution of `func` until the current call stack has cleared.
*   **Parameters**:
    *   `func` (function): The function to defer.
    *   `*args`: Arguments to pass to the function.
*   **Example**:
    
        _.defer(print, "This will be printed after the current call stack is clear")
    

#### 73\. `delay(func, wait, *args)`

*   **Description**: Invokes `func` after `wait` milliseconds.
*   **Parameters**:
    *   `func` (function): The function to delay.
    *   `wait` (int): The number of milliseconds to wait.
    *   `*args`: Arguments to pass to the function.
*   **Example**:
    
        _.delay(print, 1000, "Printed after 1 second")
    

#### 74\. `before(n, func)`

*   **Description**: Creates a function that is invoked at most `n` times. Subsequent calls to the function return the result of the last invocation.
*   **Parameters**:
    *   `n` (int): The number of calls at which `func` stops being invoked.
    *   `func` (function): The function to restrict.
*   **Returns**: A new restricted function.
*   **Example**:
    
        limitedFunc = _.before(3, lambda: print("Called"))
          limitedFunc()  # Output: "Called"
          limitedFunc()  # Output: "Called"
          limitedFunc()  # No output
    

#### 75\. `after(n, func)`

*   **Description**: Creates a function that is invoked once `n` or more times have been called.
*   **Parameters**:
    *   `n` (int): The number of calls before `func` is invoked.
    *   `func` (function): The function to delay.
*   **Returns**: A new function.
*   **Example**:
    
        callAfter = _.after(3, lambda: print("Executed"))
          callAfter()  # No output
          callAfter()  # No output
          callAfter()  # Output: "Executed"
    

#### 76\. `negate(predicate)`

*   **Description**: Creates a function that negates the result of the `predicate` function.
*   **Parameters**:
    *   `predicate` (function): The function whose result to negate.
*   **Returns**: A new function.
*   **Example**:
    
        isOdd = lambda x: x % 2 != 0
          isEven = _.negate(isOdd)
        print(isEven(4))  # Output: True
    

#### 77\. `constant(value)`

*   **Description**: Returns a function that always returns `value`.
*   **Parameters**:
    *   `value`: The value to return.
*   **Returns**: A function.
*   **Example**:
    
        always42 = _.constant(42)
        print(always42())  # Output: 42
    

#### 78\. `times(n, func)`

*   **Description**: Invokes `func` `n` times, returning an array of the results of each invocation.
*   **Parameters**:
    *   `n` (int): The number of times to invoke `func`.
    *   `func` (function): The function to invoke.
*   **Returns**: A list of results.
*   **Example**:
    
        result = _.times(3, lambda: "Hello")
        print(result)  # Output: ["Hello", "Hello", "Hello"]
    

#### 79\. `identity(value)`

*   **Description**: Returns `value` as it is.
*   **Parameters**:
    *   `value`: Any value.
*   **Returns**: The same `value`.
*   **Example**:
    
        result = _.identity(5)
        print(result)  # Output: 5
    

#### 80\. `unique_id(prefix="")`

*   **Description**: Generates a unique ID with an optional `prefix`.
*   **Parameters**:
    *   `prefix` (str, optional): The prefix for the ID.
*   **Returns**: A unique ID as a string.
*   **Example**:
    
        id1 = _.unique_id("user_")
        print(id1)  # Output: "user_1"
    

#### 81\. `escape(string)`

*   **Description**: Escapes a string for insertion into HTML, replacing `<`, `>`, `&`, `"`, and `'`.
*   **Parameters**:
    *   `string` (str): The string to escape.
*   **Returns**: The escaped string.
*   **Example**:
    
        result = _.escape("
    
    Sample
    
        ")
        print(result)  # Output: "<div>Sample</div>"
    

#### 82\. `unescape(string)`

*   **Description**: Unescapes an HTML-escaped string.
*   **Parameters**:
    *   `string` (str): The string to unescape.
*   **Returns**: The unescaped string.
*   **Example**:
    
        result = _.unescape("<div>Sample</div>")
        print(result)  # Output: "
    
    Sample
    
        "
    

#### 83\. `result(obj, path, *args)`

*   **Description**: Returns the value at `path` of `obj`. If the value is a function, it is invoked with `args`.
*   **Parameters**:
    *   `obj` (dict): The object to query.
    *   `path` (str): The path of the property.
    *   `*args`: Arguments to invoke the function with if it is a callable.
*   **Returns**: The value or result of the invoked function.
*   **Example**:
    
        obj = {"name": "Alice", "greet": lambda greeting: f"{greeting}, Alice!"}
          result = _.result(obj, "greet", "Hello")
        print(result)  # Output: "Hello, Alice!"
    

#### 84\. `noop()`

*   **Description**: A function that does nothing and returns `None`. Useful as a placeholder.
*   **Example**:
    
        result = _.noop()
        print(result)  # Output: None
    

#### 85\. `deep_copy(obj)`

*   **Description**: Creates a deep copy of `obj`.
*   **Parameters**:
    *   `obj`: The object to deep copy.
*   **Returns**: A new deep-copied object.
*   **Example**:
    
        original = {"a": 1, "b": {"c": 2}}
          copied = _.deep_copy(original)
        print(copied)  # Output: {'a': 1, 'b': {'c': 2}}
    

#### 86\. `map_object(obj, iteratee)`

*   **Description**: Applies the iteratee function to each value of `obj` and returns a new object.
*   **Parameters**:
    *   `obj` (dict): The object to iterate over.
    *   `iteratee` (function): The function applied to each value.
*   **Returns**: A new object with modified values.
*   **Example**:
    
        result = _.map_object({"a": 1, "b": 2}, lambda x: x * 2)
        print(result)  # Output: {"a": 2, "b": 4}
    

#### 87\. `pairs(obj)`

*   **Description**: Converts `obj` into a list of `[key, value]` pairs.
*   **Parameters**:
    *   `obj` (dict): The object to convert.
*   **Returns**: A list of `[key, value]` pairs.
*   **Example**:
    
        result = _.pairs({"a": 1, "b": 2})
        print(result)  # Output: [["a", 1], ["b", 2]]
    

#### 88\. `object(list)`

*   **Description**: Converts a list of `[key, value]` pairs into an object.
*   **Parameters**:
    *   `list` (list): A list of `[key, value]` pairs.
*   **Returns**: A new object.
*   **Example**:
    
        result = _.object([["a", 1], ["b", 2]])
        print(result)  # Output: {"a": 1, "b": 2}
    

#### 89\. `reject(array, predicate)`

*   **Description**: Returns the elements of `array` for which `predicate` returns `False`.
*   **Parameters**:
    *   `array` (list): The array to filter.
    *   `predicate` (function): The function invoked per element.
*   **Returns**: A list of elements.
*   **Example**:
    
        result = _.reject([1, 2, 3, 4], lambda x: x % 2 == 0)
        print(result)  # Output: [1, 3]
    

#### 90\. `partition(array, predicate)`

*   **Description**: Splits `array` into two arrays: one with elements `predicate` returns truthy for, and one with elements it returns falsey for.
*   **Parameters**:
    *   `array` (list): The array to partition.
    *   `predicate` (function): The function invoked per element.
*   **Returns**: A tuple containing two lists.
*   **Example**:
    
        result = _.partition([1, 2, 3, 4], lambda x: x % 2 == 0)
        print(result)  # Output: ([2, 4], [1, 3])
    

#### 91\. `tap(obj, interceptor)`

*   **Description**: Invokes `interceptor` with `obj`, returning `obj`. Useful for debugging.
*   **Parameters**:
    *   `obj`: The object to pass.
    *   `interceptor` (function): The function to invoke.
*   **Returns**: The original `obj`.
*   **Example**:
    
        result = _.tap([1, 2, 3], lambda x: print("Tapped array:", x))
        print(result)  # Output: [1, 2, 3]
    

#### 92\. `sort_by_all(array, *iteratees)`

*   **Description**: Sorts `array` by multiple iteratees in the order they are provided.
*   **Parameters**:
    *   `array` (list): The array to sort.
    *   `*iteratees` (functions): The iteratees used for sorting.
*   **Returns**: A sorted list.
*   **Example**:
    
        result = _.sort_by_all([{ "name": "John", "age": 25 }, { "name": "Jane", "age": 20 }], lambda x: x["age"], lambda x: x["name"])
        print(result)  # Output: [{'name': 'Jane', 'age': 20}, {'name': 'John', 'age': 25}]
    

#### 93\. `zip(*arrays)`

*   **Description**: Combines multiple arrays into a single array of grouped elements.
*   **Parameters**:
    *   `*arrays` (lists): The arrays to combine.
*   **Returns**: A single array of grouped elements.
*   **Example**:
    
        result = _.zip(["a", "b"], [1, 2], [True, False])
        print(result)  # Output: [["a", 1, True], ["b", 2, False]]
    

#### 94\. `unzip(array)`

*   **Description**: The opposite of `zip`; splits an array of grouped elements into separate arrays.
*   **Parameters**:
    *   `array` (list): The array to split.
*   **Returns**: A list of arrays.
*   **Example**:
    
        result = _.unzip([["a", 1, True], ["b", 2, False]])
        print(result)  # Output: [["a", "b"], [1, 2], [True, False]]
    

#### 95\. `without(array, *values)`

*   **Description**: Returns an array excluding all given `values`.
*   **Parameters**:
    *   `array` (list): The array to filter.
    *   `*values`: The values to exclude.
*   **Returns**: A new filtered array.
*   **Example**:
    
        result = _.without([1, 2, 3, 4], 2, 4)
        print(result)  # Output: [1, 3]
    

#### 96\. `some(array, predicate)`

*   **Description**: Checks if `predicate` returns `True` for any element of `array`.
*   **Parameters**:
    *   `array` (list): The array to check.
    *   `predicate` (function): The function invoked per element.
*   **Returns**: `True` if any element passes the check, `False` otherwise.
*   **Example**:
    
        result = _.some([1, 2, 3], lambda x: x > 2)
        print(result)  # Output: True
    

#### 97\. `every(array, predicate)`

*   **Description**: Checks if `predicate` returns `True` for all elements of `array`.
*   **Parameters**:
    *   `array` (list): The array to check.
    *   `predicate` (function): The function invoked per element.
*   **Returns**: `True` if all elements pass the check, `False` otherwise.
*   **Example**:
    
        result = _.every([1, 2, 3], lambda x: x > 0)
        print(result)  # Output: True
    

#### 98\. `min(array)`

*   **Description**: Returns the minimum value in `array`.
*   **Parameters**:
    *   `array` (list): The array to check.
*   **Returns**: The minimum value.
*   **Example**:
    
        result = _.min([3, 1, 4, 2])
        print(result)  # Output: 1
    

#### 99\. `max(array)`

*   **Description**: Returns the maximum value in `array`.
*   **Parameters**:
    *   `array` (list): The array to check.
*   **Returns**: The maximum value.
*   **Example**:
    
        result = _.max([3, 1, 4, 2])
        print(result)  # Output: 4
    

#### 100\. `invoke(array, method, *args)`

*   **Description**: Invokes the `method` on each item in the `array`, passing `*args` as arguments.
*   **Parameters**:
    *   `array` (list): The array to process.
    *   `method` (str): The method name to invoke.
    *   `*args`: Arguments to pass to the method.
*   **Returns**: A list of results from invoking the method.
*   **Example**:
    
        result = _.invoke([[5, 1, 7], [3, 2]], 'sort')
        print(result)  # Output: [[1, 5, 7], [2, 3]]
    

#### 101\. `matches(attrs)`

*   **Description**: Creates a function that checks if an object contains the key-value pairs in `attrs`.
*   **Parameters**:
    *   `attrs` (dict): The key-value pairs to match.
*   **Returns**: A function that returns `True` or `False`.
*   **Example**:
    
        matcher = _.matches({"name": "John"})
        print(matcher({"name": "John", "age": 30}))  # Output: True
    

#### 102\. `property(key)`

*   **Description**: Returns a function that retrieves the property `key` from an object.
*   **Parameters**:
    *   `key` (str): The property key to retrieve.
*   **Returns**: A function.
*   **Example**:
    
        getName = _.property("name")
        print(getName({"name": "Alice"}))  # Output: "Alice"
    

#### 103\. `property_of(obj)`

*   **Description**: Returns a function that retrieves a value for a given key from `obj`.
*   **Parameters**:
    *   `obj` (dict): The object to query.
*   **Returns**: A function.
*   **Example**:
    
        getValue = _.property_of({"a": 1, "b": 2})
        print(getValue("b"))  # Output: 2
    

#### 104\. `pluck(array, key)`

*   **Description**: Extracts a list of property values from `array`.
*   **Parameters**:
    *   `array` (list): The array to iterate over.
    *   `key` (str): The property key to pluck.
*   **Returns**: A list of values.
*   **Example**:
    
        result = _.pluck([{ "name": "Alice" }, { "name": "Bob" }], "name")
        print(result)  # Output: ["Alice", "Bob"]
    

#### 105\. `reduce_right(array, iteratee, initial=None)`

*   **Description**: Reduces `array` from right to left using the `iteratee` function.
*   **Parameters**:
    *   `array` (list): The array to reduce.
    *   `iteratee` (function): The function to apply.
    *   `initial` (optional): The initial value.
*   **Returns**: The reduced value.
*   **Example**:
    
        result = _.reduce_right([1, 2, 3, 4], lambda acc, x: acc - x, 0)
        print(result)  # Output: -2
    

#### 106\. `shuffle(array)`

*   **Description**: Returns a shuffled copy of `array`.
*   **Parameters**:
    *   `array` (list): The array to shuffle.
*   **Returns**: A new shuffled array.
*   **Example**:
    
        result = _.shuffle([1, 2, 3, 4, 5])
        print(result)  # Output: [3, 5, 1, 4, 2] (order may vary)
    

#### 107\. `sort_by(array, iteratee)`

*   **Description**: Sorts `array` based on the result of `iteratee` applied to each element.
*   **Parameters**:
    *   `array` (list): The array to sort.
    *   `iteratee` (function): The function invoked per element.
*   **Returns**: A new sorted array.
*   **Example**:
    
        result = _.sort_by([{ "name": "Alice", "age": 30 }, { "name": "Bob", "age": 25 }], lambda x: x["age"])
        print(result)  # Output: [{"name": "Bob", "age": 25}, {"name": "Alice", "age": 30}]
    

#### 108\. `where_(array, properties)`

*   **Description**: Returns an array of all elements that match the given `properties`.
*   **Parameters**:
    *   `array` (list): The array to search.
    *   `properties` (dict): The properties to match.
*   **Returns**: A list of matched elements.
*   **Example**:
    
        result = _.where_([{ "name": "Alice", "age": 30 }, { "name": "Bob", "age": 25 }], { "age": 30 })
        print(result)  # Output: [{"name": "Alice", "age": 30}]
    

#### 109\. `zip(keys, values)`

*   **Description**: Creates an object from `keys` and `values` arrays.
*   **Parameters**:
    *   `keys` (list): The array of keys.
    *   `values` (list): The array of values.
*   **Returns**: A new object.
*   **Example**:
    
        result = _.zip(["a", "b", "c"], [1, 2, 3])
        print(result)  # Output: {"a": 1, "b": 2, "c": 3}
    

#### 110\. `range(start, stop, step=1)`

*   **Description**: Creates an array of numbers (positive and/or negative) progressing from `start` up to, but not including, `stop`.
*   **Parameters**:
    *   `start` (int): The start value.
    *   `stop` (int): The end value.
    *   `step` (int, optional): The increment or decrement value.
*   **Returns**: A list of numbers.
*   **Example**:
    
        result = _.range(0, 5)
        print(result)  # Output: [0, 1, 2, 3, 4]
    

#### 111\. `union(*arrays)`

*   **Description**: Returns a new array of unique values from all given arrays.
*   **Parameters**:
    *   `*arrays` (lists): The arrays to process.
*   **Returns**: A combined array of unique values.
*   **Example**:
    
        result = _.union([1, 2], [2, 3], [3, 4])
        print(result)  # Output: [1, 2, 3, 4]
    

### 112\. `intersection(*arrays)`

*   **Description**: Returns an array of shared values present in all the provided `arrays`.
*   **Parameters**:
    *   `*arrays` (lists): The arrays to inspect for common values.
*   **Returns**: A new array containing elements common to all arrays.  
    **Example**:
    
        result = _.intersection([1, 2, 3], [2, 3, 4], [3, 4, 5]) 
        print(result) # Output: [3]
    

### 113\. `difference(array, *others)`

*   **Description**: Returns a new array with elements from `array` that are not present in any of the `others` arrays.
*   **Parameters**:
    *   `array` (list): The array to inspect.
    *   `*others` (lists): The arrays to compare against.
*   **Returns**: A new array with filtered values.
*   **Example**:
    
        result = _.difference([1, 2, 3, 4], [2, 4], [3])
        print(result) # Output: [1]
    

### 114\. `xor(*arrays)`

*   **Description**: Creates an array of unique values that is the symmetric difference of the provided arrays.
*   **Parameters**:
    *   `*arrays` (lists): The arrays to process.
*   **Returns**: A new array with unique values.
*   **Example**:  
    
        result = _.xor([2, 1], [2, 3])
        print(result) # Output: [1, 3]
    

6\. Examples<a name="examples"></a>
------------

### Example 1: Chaining Array Operations

    result = _([1, 2, 3, 4, 5])\
          .map(lambda x: x * 2)\
          .filter(lambda x: x > 5)\
          .value()
    print(result)  # Output: [6, 8, 10]

### Example 2: Using Static Methods

    from unicorefw import _
      
      result = _.difference([1, 2, 3], [2, 3])
      print(result)  # Output: [1]

7\. Contributing<a name="contributing"></a>
----------------

Contributions are welcome! Please see `CONTRIBUTING.md` for guidelines.

8\. License<a name="license"></a>
-----------

This project is licensed under the BSD-3-Clause License. See `LICENSE` for details.
