![alt text](https://raw.githubusercontent.com/unicorefw-org/unicorefw-py/refs/heads/main/logo.svg)
# UniCoreFW-py - Unicore Framework in Python
|               |       Arrays | Objects |  Functions | Utilities | 
| :------------ | ------------:| -------:| ----------:| ---------:|
| **Test Status**         |            ✓ |       ✓ |         ✓ |         ✓ |
| **Build Status**         |            ✓ |       ✓ |         ✓ |         ✓ |

* * *
Overview
--------
UniCoreFW-PY, a part of UnicoreFW.org is a Python-based framework based on UnderscoreJS, designed to offer a comprehensive set of utilities and functional programming tools. This framework is equipped with command-line capabilities that allow users to execute example scripts, parse custom command-line arguments, and integrate powerful utility methods for various use cases. The goal of UnicoreFW is to provide security, performance, and ease of use for developers looking to build and maintain Python applications.


Features
--------
    
*   **Flexible Test Execution**: Run example scripts through the command line for rapid prototyping and testing.
*   **Utility Functions**: Includes a robust set of utility methods for functional programming, string manipulation, and more.
*   **Secure Execution**: Built-in security measures to safely execute code and handle user inputs.


Installation from Pypi using PIP
------------
    pip install unicorefw

Installation from source
------------

1.  Clone the repository:
    
        git clone https://github.com/unicorefw-org/unicorefw-py.git
        cd unicore-py
    
2.  Ensure Python 3.x is installed on your system.



Directory Structure
-------------------

    project_root_dir/
    ├── src/
    │   └── unicorefw.py
    ├── examples/
    │   └── sets/            # list of examples
    │   └── functions.py     # show examples of function usage
    │   └── task_manager.py  # Sample implementations of UniCoreFW functions
    │   └── underscore.py    # examples on how to use UniCoreFW as _
    └── README.md


Quick Start Guide
-----------------

    from unicorefw import UniCoreFW, UniCoreFWWrapper

    def _(collection):
        return UniCoreFWWrapper(collection)

    # Attach functions from 'Unicore' directly to '_'
    for func_name in dir(UniCoreFW):
        if callable(getattr(UniCoreFW, func_name)) and not func_name.startswith("_"):
            setattr(_, func_name, getattr(UniCoreFW, func_name))

    # Example usage:
    result = _([1, 2, 3, 4, 5]).map(lambda x: x * 2).filter(lambda x: x > 5).value()
    print(result)  # Expected output: [6, 8, 10]

    # Using a static function call
    template = "Name: <%= name %>, Age: <%= age %>"
    context = {"name": "Alice", "age": 25}
    result = _.template(template, context)
    print(result)  # Expected output: "Name: Alice, Age: 25"

Documention
------------
 Please see `docs/guide.md` for more information.

**PYTHON IMPLEMENTATION**
* * *
This class, `UniCoreFW`, provides a wide range of utility functions for working with arrays, objects, and strings. Here's a summary of what each method does:

**Array Functions**
- `_.map` – Transforms an array's elements based on a function.
- `_.reduce` – Reduces an array to a single value using a function.
- `_.reduce_right` – Like - `_.reduce, but starts from the right.
- `_.find` – Returns the first value that matches a predicate.
- `_.filter` – Returns an array of values that match a predicate.
- `_.where` – Filters an array of objects, matching a set of key-value pairs.
- `_.find_where` – Like - `_.where, but returns only the first match.
- `_.reject` – Returns an array of values that fail a predicate.
- `_.every` – Tests whether all values pass a predicate.
- `_.some` – Tests whether any values pass a predicate.
- `_.contains` – Checks if a value exists in an array.
- `_.invoke` – Invokes a method on every item in a collection.
- `_.pluck` – Extracts a list of values from an array of objects.
- `_.max` – Returns the maximum value based on a function.
- `_.min` – Returns the minimum value based on a function.
- `_.sort_by` – Sorts an array by a function's result.
- `_.group_by` – Groups an array by the result of a function.
- `_.index_by` – Indexes an array by a property value or function result.
- `_.count_by` – Counts instances of values by a function's result.
- `_.shuffle` – Shuffles the values in an array.
- `_.sample` – Selects random values from an array.
- `_.to_array` – Converts an iterable into an array.
- `_.size` – Returns the size of a collection.
- `_.partition` – Splits a collection into two arrays based on a predicate.
- `_.first` – Returns the first elements of an array.
- `_.initial` – Returns everything but the last element of an array.
- `_.last` – Returns the last elements of an array.
- `_.rest` – Returns everything but the first element of an array.
- `_.compact` – Removes falsey values from an array.
- `_.flatten` – Flattens a nested array.
- `_.without` – Returns an array with specified values removed.
- `_.uniq` – Removes duplicate values from an array.
- `_.union` – Combines arrays, removing duplicates.
- `_.intersection` – Returns values common to all arrays.
- `_.difference` – Returns values from the first array not present in others.
- `_.zip` – Merges arrays based on their index.
- `_.unzip` – Reverses the process of - `_.zip.
- `_.object` – Converts an array of pairs into an object.
- `_.range` – Creates an array of numbers in a range.
- `_.chunk` – Splits an array into chunks of a specified size.

**Object Functions**
- `_.keys` – Returns an array of an object's keys.
- `_.all_keys` – Returns an array of an object's keys, including inherited ones.
- `_.values` – Returns an array of an object's values.
- `_.map_object` – Applies a function to each value of an object.
- `_.pairs` – Converts an object into an array of [key, value] pairs.
- `_.invert` – Inverts an object's keys and values.
- `_.functions` – Returns an array of all function property names in an object.
- `_.extend` – Extends an object with the properties of other objects.
- `_.extend_own` – Like - `_.extend, but only copies own properties.
- `_.defaults` – Assigns default properties to an object.
- `_.create` – Creates an object with a specified prototype.
- `_.clone` – Creates a shallow copy of an object.
- `_.tap` – Invokes a function with an object and returns the object.
- `_.has` – Checks if an object contains a given property.
- `_.property` – Returns a function that retrieves a property value.
- `_.property_of` – Returns a function that retrieves a property value from a given object.
- `_.matcher (or - `_.matches)` – Creates a function that checks for matching key-value pairs.
- `_.is_equal` – Performs a deep comparison between objects.
- `_.is_match` – Checks if an object matches key-value pairs.
- `_.is_empty` – Checks if an object is empty.
- `_.is_element` – Checks if an object is a DOM element.
- `_.is_array` – Checks if a value is an array.
- `_.is_object` – Checks if a value is an object.
- `_.is_arguments` – Checks if a value is an arguments object.
- `_.is_function` – Checks if a value is a function.
- `_.is_string` – Checks if a value is a string.
- `_.is_number` – Checks if a value is a number.
- `_.is_finite` – Checks if a value is a finite number.
- `_.is_boolean` – Checks if a value is a boolean.
- `_.is_date` – Checks if a value is a date.
- `_.is_regExp` – Checks if a value is a regular expression.
- `_.is_error` – Checks if a value is an error.
- `_.is_symbol` – Checks if a value is a symbol.
- `_.is_map` – Checks if a value is a map.
- `_.is_weak_map` – Checks if a value is a weak map.
- `_.is_set` – Checks if a value is a set.
- `_.is_weak_set` – Checks if a value is a weak set.
- `_.is_null` – Checks if a value is null.
- `_.is_undefined` – Checks if a value is undefined.
- `_.is_nan` – Checks if a value is NaN.
- `_.is_typed_array` – Checks if a value is a typed array.
- `_.is_array_buffer` – Checks if a value is an array buffer.
- `_.is_data_view` – Checks if a value is a data view.

**Utility Functions**
- `_.identity` – Returns the same value that is passed.
- `_.constant` – Returns a function that returns the given value.
- `_.noop` – A function that does nothing.
- `_.times` – Invokes a function a specified number of times.
- `_.random` – Returns a random number between a min and max.
- `_.mixin` – Adds functions to the Underscore object.
- `_.iteratee` – Returns a function that can be applied to each element in a collection.
- `_.unique_id` – Generates a unique identifier.
- `_.escape` – Escapes a string for inclusion in HTML.
- `_.unescape` – Unescapes a string from HTML.
- `_.result` – Resolves the value of a property, potentially invoking it as a function.
- `_.now` – Returns the current timestamp.
- `_.template` – Compiles a template to a function.
- `_.chain` – Returns a wrapped object to allow chaining of functions.
- `_.value` – Extracts the result from a chained object.

**Function Functions**
- `_.bind` – Binds a function to an object.
- `_.partial` – Partially applies a function by pre-filling some arguments.
- `_.bind_all` – Binds methods of an object to the object itself.
- `_.memoize` – Caches the result of a function call.
- `_.delay` – Delays a function for a specified number of milliseconds.
- `_.defer` – Defers a function to be executed after the current call stack clears.
- `_.throttle` – Creates a throttled version of a function.
- `_.debounce` – Creates a debounced version of a function.
- `_.once` – Ensures a function is only called once.
- `_.after` – Returns a function that will only run after it has been called N times.
- `_.before` – Returns a function that will run until it has been called N times.
- `_.wrap` – Wraps a function inside another function.
- `_.negate` – Returns the negation of a predicate function.
- `_.compose` – Composes functions together to run in sequence.

**Chaining Functions**
- `_.chain` – Starts a chain.
- `_.value` – Extracts the value at the end of a chain.


Security Considerations
-----------------------

*   **Safe Execution**: The framework ensures that code execution is sandboxed and limited in scope to avoid unwanted side effects.
*   **Input Validation**: Command-line inputs are validated to prevent invalid or malicious commands.
    

Contributing
------------

We welcome contributions to UnicoreFW! Please follow these steps:

1.  Follow principles in CODE_OF_CONDUCT.md
2.  Fork the repository.
3.  Create a feature branch.
4.  Submit a pull request with a detailed description of your changes.
    
