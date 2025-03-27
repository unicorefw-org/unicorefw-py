"""
Object manipulation functions for UniCoreFW.

This module contains functions for working with dictionaries and object-like structures.

Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info
"""

from typing import Dict, List, Callable, TypeVar, Union, Any, Optional, Tuple

K = TypeVar('K')
V = TypeVar('V')
T = TypeVar('T')
U = TypeVar('U')

def keys(obj: Dict[K, V]) -> List[K]:
    """
    Return the keys of a dictionary as a list.
    
    Args:
        obj: The dictionary to get keys from
        
    Returns:
        A list of keys
    """
    return list(obj.keys())

def values(obj: Dict[K, V]) -> List[V]:
    """
    Return the values of a dictionary as a list.
    
    Args:
        obj: The dictionary to get values from
        
    Returns:
        A list of values
    """
    return list(obj.values())

def extend(obj: Dict[K, V], *sources: Dict) -> Dict[K, V]:
    """
    Extend obj by copying properties from sources.
    
    Args:
        obj: The dictionary to extend
        *sources: Dictionaries to copy properties from
        
    Returns:
        The extended dictionary
    """
    for source in sources:
        obj.update(source)
    return obj

def clone(obj: Union[Dict, List]) -> Union[Dict, List]:
    """
    Create a shallow copy of an object (dictionary or list).
    
    Args:
        obj: The object to clone
        
    Returns:
        A shallow copy of the object
    """
    if isinstance(obj, dict):
        return obj.copy()
    elif isinstance(obj, list):
        return list(obj)
    else:
        return obj

def has(obj: Dict, key: K) -> bool:
    """
    Check if obj has a given property key.
    
    Args:
        obj: The dictionary to check
        key: The key to check for
        
    Returns:
        True if the key exists, False otherwise
    """
    return key in obj

def invert(obj: Dict[K, V]) -> Dict[V, K]:
    """
    Invert an object's keys and values.
    
    Args:
        obj: The dictionary to invert
        
    Returns:
        A new dictionary with keys and values swapped
    """
    return {v: k for k, v in obj.items()}

def defaults(obj: Dict[K, V], *defaults_dicts) -> Dict[K, V]:
    """
    Assign default properties to obj if they are missing.
    
    Args:
        obj: The original dictionary to update
        *defaults_dicts: One or more dictionaries containing default values
        
    Returns:
        A new dictionary with defaults applied
        
    Raises:
        TypeError: If obj or any default is not a dictionary
        ValueError: If keys in defaults are not strings
    """
    if not isinstance(obj, dict):
        raise TypeError("The 'obj' parameter must be a dictionary.")

    # Create a copy to avoid modifying the original object
    result = obj.copy()

    for default in defaults_dicts:
        if not isinstance(default, dict):
            raise TypeError("Each default must be a dictionary.")
        for key, value in default.items():
            if key not in obj:
                obj[key] = value
            if not isinstance(key, str):
                raise ValueError("Keys in defaults must be strings.")
            # Only set the default if the key is not already in 'result'
            if key not in result:
                result[key] = value
    return result

def create(proto: Dict) -> Dict:
    """
    Create an object that inherits from the given prototype (dictionary).
    
    Args:
        proto: The prototype dictionary
        
    Returns:
        A new dictionary with prototype properties
        
    Raises:
        TypeError: If proto is not a dictionary
    """
    if not isinstance(proto, dict):
        raise TypeError("Prototype must be a dictionary")

    class Obj(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.update(proto)

    return Obj()

def pairs(obj: Dict[K, V]) -> List[Tuple[K, V]]:
    """
    Convert an object into an array of [key, value] pairs.
    
    Args:
        obj: The dictionary to convert
        
    Returns:
        A list of key-value tuples
    """
    return list(obj.items())

def result(obj: Dict, property_name: str, *args) -> Any:
    """
    If the property is a function, invoke it with args; otherwise, return the property value.
    
    Args:
        obj: The dictionary to get the property from
        property_name: The property name to get
        *args: Arguments to pass if the property is a function
        
    Returns:
        The property value or function result
    """
    value = obj.get(property_name)

    if callable(value):
        # Directly call the function with args if it's callable
        return value(*args)

    return value

def size(obj: Union[Dict, List, Any]) -> int:
    """
    Return the number of values in obj (works for dicts, lists, etc.).
    
    Args:
        obj: The object to get the size of
        
    Returns:
        The number of elements/properties
    """
    if hasattr(obj, "__len__"):
        return len(obj)
    return sum(1 for _ in obj)

def to_array(obj: Union[Dict, List, Any]) -> List:
    """
    Convert obj into an array (list in Python).
    
    Args:
        obj: The object to convert
        
    Returns:
        A list representation of the object
    """
    if isinstance(obj, list):
        return obj
    elif isinstance(obj, (dict, set)):
        return list(obj.values()) if isinstance(obj, dict) else list(obj)
    elif hasattr(obj, "__iter__"):
        return list(obj)
    return [obj]

def where(obj_list: List[Dict], properties: Dict) -> List[Dict]:
    """
    Return an array of all objects in obj_list that match the key-value pairs in properties.
    
    Args:
        obj_list: The list of objects to filter
        properties: Key-value pairs to match
        
    Returns:
        A list of matching objects
    """
    return [
        obj
        for obj in obj_list
        if all(obj.get(k) == v for k, v in properties.items())
    ]

def object(keys: List[K], values: List[V]) -> Dict[K, V]:
    """
    Create an object (dictionary) from the given keys and values.
    
    Args:
        keys: The list of keys
        values: The list of values
        
    Returns:
        A dictionary with the given keys and values
        
    Raises:
        ValueError: If keys and values don't have the same length
    """
    if len(keys) != len(values):
        raise ValueError("Keys and values must have the same length")
    return {keys[i]: values[i] for i in range(len(keys))}

def map_object(obj: Dict[K, V], func: Callable[[V], U]) -> Dict[K, U]:
    """
    Apply func to each value in obj, returning a new object with the transformed values.
    
    Args:
        obj: The dictionary to transform
        func: A function to apply to each value
        
    Returns:
        A new dictionary with transformed values
    """
    return {k: func(v) for k, v in obj.items()}

def all_keys(obj: Dict) -> List:
    """
    Return all the keys of a dictionary, including inherited ones.
    
    Args:
        obj: The dictionary to get keys from
        
    Returns:
        A list of keys
        
    Raises:
        TypeError: If obj is not a dictionary
    """
    if isinstance(obj, dict):
        return list(obj.keys())
    else:
        raise TypeError("The input must be a dictionary.")

def is_match(obj: Dict, attrs: Dict) -> bool:
    """
    Check if obj has key-value pairs that match attrs.
    
    Args:
        obj: The dictionary to check
        attrs: The key-value pairs to match
        
    Returns:
        True if all key-value pairs match, False otherwise
    """
    return all(obj.get(k) == v for k, v in attrs.items())

def functions(obj: Dict) -> List[str]:
    """
    Return the names of all explicitly defined functions in an object (dictionary).
    
    Args:
        obj: The dictionary to check for functions
        
    Returns:
        A list of function names defined in the object
        
    Raises:
        TypeError: If obj is not a dictionary
    """
    if not isinstance(obj, dict):
        raise TypeError("Input must be a dictionary.")

    return [
        key
        for key, value in obj.items()
        if callable(value) and not key.startswith("__")
    ]

def deep_copy(obj: Any) -> Any:
    """
    Create a deep copy of the given object without using imports.
    
    Args:
        obj: The object to copy
        
    Returns:
        A deep copy of the object
    """
    if isinstance(obj, dict):
        return {k: deep_copy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [deep_copy(elem) for elem in obj]
    elif isinstance(obj, tuple):
        return tuple(deep_copy(elem) for elem in obj)
    elif isinstance(obj, str):
        # Strings are immutable, return as is
        return obj
    else:
        # For immutable objects like int, float, return as is
        return obj