#!/usr/bin/env python3
##############################################################################
# examples/functions.py - Show examples for Unicore functions                #
# Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.Info                #
#                                                                            #
# This file is part of UniCoreFW. You can redistribute it and/or modify      #
# it under the terms of the [BSD-3-Clause] as published by                   #
# the Free Software Foundation.                                              #
# You should have received a copy of the [BSD-3-Clause] license              #
# along with UniCoreFW. If not, see https://www.gnu.org/licenses/.           #
##############################################################################

import os
import glob
import argparse
import sys
import re

# Set the base directory path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Ensure the 'src' directory is in sys.path for Unicore imports
sys.path.insert(0, os.path.join(BASE_DIR, "../src"))

from unicorefw import UniCoreFW


def _show_function(args):
    """
    Runs example files based on the provided argument.
    If '_all_' is provided, runs all example files.
    """
    if not args:
        print("Usage: examples/functions.py --show=function <function_name>")
        return

    arg = UniCoreFW.first(args)
    examples_path = os.path.join(BASE_DIR, "../examples/sets")

    if UniCoreFW.is_string(arg):
        if arg == "_all_":
            # Run all example files matching the pattern
            for file_path in glob.glob(os.path.join(examples_path, "ex_*.py")):
                print(f"\nExecuting {file_path}")
                run_example(file_path, True)
        else:
            file_path = os.path.join(examples_path, f"ex_{arg}.py")
            if os.path.exists(file_path):
                print(f"Executing {file_path}")
                run_example(file_path, True)
            else:
                print(f"Error: Example file '{file_path}' not found.")
    else:
        print("Error: Invalid argument. Expected a string.")


def run_example(file_path, show_source=False):
    """
    Safely executes a Python example file by importing it as a module.
    """
    src = ""
    line = ""
    try:
        with open(file_path, "r") as f:
            line = f.read()
            if show_source:
                src += line

            exec(line)
        print(
            "\n^ Output was produced by the following code: \n===========================================\n\n"
            + src
        )
    except Exception as e:
        print(f"Error executing {file_path}: {e}")



def parse_args():
    """
    Parses command-line arguments with `--name=value` format and additional positional arguments.

    Returns:
        tuple: A dictionary containing key-value pairs from `--name=value` arguments
               and a list of positional arguments.
    """
    parser = argparse.ArgumentParser(
        description="Parse --name=value command-line arguments and additional positional arguments.",
        allow_abbrev=False,
        add_help=False,
    )

    known_args, unknown_args = parser.parse_known_args()

    # Process key-value arguments with `--name=value` format
    def process_arg(arg):
        if arg.startswith("--") and "=" in arg[2:]:
            key, value = arg[2:].split("=", 1)
            if key:
                return key, value
            else:
                parser.error(f"Invalid argument format: '{arg}'. Key cannot be empty.")
        else:
            return arg

    # Parse each argument: store key-value pairs and positional arguments separately
    key_value_dict = {}
    positional_args = []

    for arg in unknown_args:
        processed = process_arg(arg)
        if isinstance(processed, tuple):
            key, value = processed
            key_value_dict.setdefault(key, []).append(value)
        else:
            positional_args.append(processed)

    # Finalize dictionary by collapsing single-item lists
    final_key_value_dict = UniCoreFW.map_object(
        key_value_dict, lambda v: v[0] if len(v) == 1 else v
    )

    return final_key_value_dict, positional_args


def main():
    """
    Unicore Command-Line Utilities for maintaining UniCoreFW.
    """
    try:
        actions, args = parse_args()
    except SystemExit as e:
        # argparse uses sys.exit(), which raises SystemExit
        raise e

    if not actions:
        print("No arguments were provided.")
        return

    for action, action_invoker in actions.items():
        # Sanitize action and action_invoker to prevent unintended execution
        function_name = f"_{re.sub(r'[^a-zA-Z0-9]', '', action)}_{re.sub(r'[^a-zA-Z0-9]', '_', action_invoker)}"
        function = globals().get(function_name)

        if function:
            print(f"Invoking function {function_name}")
            function(args)
            break
        else:
            print(f"Error: Command '{action}={action_invoker}' not found.")


if __name__ == "__main__":
    main()
