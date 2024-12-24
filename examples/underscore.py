#!/usr/bin/env python3
##############################################################################
# examples/underscore.py - Example of using underscore to wrap functions     #
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

# Set the base directory path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Ensure the 'src' directory is in sys.path for Unicore imports
sys.path.insert(0, os.path.join(BASE_DIR, "../src"))

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
