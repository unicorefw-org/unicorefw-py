"""
UniCoreFW - Universal Core Utility Library
==========================================

A comprehensive suite of utility functions for Python applications.

Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info
"""

__version__ = "1.0.3"
__author__ = "Kenny Ngo"

# Import the main classes
from .core import UniCoreFW, UniCoreFWWrapper

# Import all functions from submodules to make them available at package level
from .array import *
from .object import *
from .function import *
from .utils import *
from .types import *
from .security import *
from .template import *

# Create a convenience factory function for UniCoreFWWrapper
def _(collection):
    """
    Factory function to create a UniCoreFWWrapper instance.
    This provides a shorthand similar to the Underscore.js _ function.
    
    Args:
        collection: The collection to wrap
        
    Returns:
        UniCoreFWWrapper: A wrapped collection
    """
    return UniCoreFWWrapper(collection)

# Attach static methods
for func_name in dir(UniCoreFW):
    if callable(getattr(UniCoreFW, func_name)) and not func_name.startswith("_"):
        setattr(_, func_name, getattr(UniCoreFW, func_name))

# Define what's available for import
__all__ = ['UniCoreFW', 'UniCoreFWWrapper', '_']