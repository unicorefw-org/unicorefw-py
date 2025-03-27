"""
Template engine for UniCoreFW.

This module provides functionality for template processing with variable interpolation
and basic conditional logic.

Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info
"""

import re
from typing import Dict, Any, Match, List

from .security import SecurityError, sanitize_string

def template(template_str: str, context: Dict[str, Any]) -> str:
    """
    Process a template string with a context of variables.
    
    The template format supports variable interpolation with `<%= variable %>`
    and conditional statements with `<% if condition %>` and `<% endif %>`.
    
    Args:
        template_str: The template string to process
        context: Dictionary of variables to use in the template
        
    Returns:
        The processed template
        
    Raises:
        ValueError: If the template contains invalid syntax
        SecurityError: If potentially dangerous patterns are detected
    """
    # Validate inputs for security
    template_str = sanitize_string(template_str, max_length=10000)
    if not isinstance(context, dict):
        raise TypeError("Context must be a dictionary")
    
    # Validate context values
    for key, value in context.items():
        if not isinstance(key, str):
            raise TypeError(f"Context key '{key}' must be a string")
        if callable(value):
            from .security import validate_callable
            validate_callable(value, f"context['{key}']")
    
    # Check for dangerous patterns
    dangerous_patterns = r"<%=.*?.__(class|bases|subclasses|globals|dict|code|builtins|module)__.*?%>"
    if re.search(dangerous_patterns, template_str):
        raise SecurityError("Potentially dangerous template pattern detected")

    # Define the token pattern
    token_pattern = r"(<%=?[^%]*?%>)"

    # Tokenize the template
    def tokenize(template_text: str) -> List[str]:
        """Split template into tokens."""
        tokens = re.split(token_pattern, template_text)
        return tokens

    # Evaluate expressions in the template
    def evaluate_expression(expr: str, ctx: Dict[str, Any]) -> Any:
        """
        Evaluate a template expression.
        
        Args:
            expr: The expression to evaluate
            ctx: The context dictionary
            
        Returns:
            The result of the expression
            
        Raises:
            ValueError: If the expression is invalid
            NameError: If a variable is not defined
            AttributeError: If an attribute is not found
        """
        # Allow simple variable access and method calls with a strict pattern
        pattern = r"^([a-zA-Z_][a-zA-Z0-9_]*)(\.[a-zA-Z_][a-zA-Z0-9_]*(\(\))?)*$"
        if not re.match(pattern, expr):
            raise ValueError(f"Invalid expression: '{expr}'")

        parts = expr.split(".")
        value = ctx.get(parts[0], None)
        if value is None:
            raise NameError(f"Name '{parts[0]}' is not defined.")

        for part in parts[1:]:
            if part.endswith("()"):
                method_name = part[:-2]
                value = call_safe_method(value, method_name)
            else:
                if hasattr(value, part):
                    value = getattr(value, part, None)
                else:
                    raise AttributeError(f"Attribute '{part}' not found.")
        return value

    # Evaluate conditions in the template
    def evaluate_condition(condition: str, ctx: Dict[str, Any]) -> bool:
        """
        Evaluate a template condition.
        
        Args:
            condition: The condition to evaluate
            ctx: The context dictionary
            
        Returns:
            True if the condition is truthy, False otherwise
            
        Raises:
            ValueError: If the condition is invalid
        """
        # Allow simple variable truthiness checks
        pattern = r"^([a-zA-Z_][a-zA-Z0-9_]*)$"
        if not re.match(pattern, condition):
            raise ValueError(f"Invalid condition: '{condition}'")

        value = ctx.get(condition, None)
        return bool(value)

    # Call safe methods on objects
    def call_safe_method(obj: Any, method_name: str) -> Any:
        """
        Call a safe method on an object.
        
        Args:
            obj: The object to call the method on
            method_name: The name of the method to call
            
        Returns:
            The result of the method call
            
        Raises:
            ValueError: If the method is not allowed
        """
        # Only allow safe methods on strings
        safe_methods = {"upper", "lower", "title", "capitalize"}
        if isinstance(obj, str) and method_name in safe_methods:
            method = getattr(obj, method_name, None)
            return method()
        else:
            raise ValueError(
                f"Method '{method_name}' is not allowed on object of type '{type(obj).__name__}'."
            )

    # Process the template
    tokens = tokenize(template_str)
    output = ""
    skip_stack = []  # Track conditional blocks
    idx = 0

    while idx < len(tokens):
        token = tokens[idx]
        
        # Handle variable interpolation
        if token.startswith("<%=") and token.endswith("%>"):
            if not any(skip_stack):  # Only process if not in a skipped block
                expr = token[3:-2].strip()
                value = evaluate_expression(expr, context)
                output += str(value)
        
        # Handle control statements
        elif token.startswith("<%") and token.endswith("%>"):
            tag_content = token[2:-2].strip()
            
            # if statement
            if tag_content.startswith("if "):
                condition = tag_content[3:].rstrip(":").strip()
                result = evaluate_condition(condition, context)
                skip_stack.append(not result)
            
            # endif statement
            elif tag_content == "endif":
                if skip_stack:
                    skip_stack.pop()
                else:
                    raise ValueError("Unmatched 'endif' found.")
            
            # unknown tag
            else:
                raise ValueError(f"Unknown tag '{tag_content}'.")
        
        # Regular text
        else:
            if not any(skip_stack):  # Only add if not in a skipped block
                output += token
        
        idx += 1

    # Check for unclosed conditional blocks
    if skip_stack:
        raise ValueError("Unclosed 'if' statement detected.")
    
    return output