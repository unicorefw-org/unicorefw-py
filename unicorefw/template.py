"""
File: unicorefw/template.py
Template engine for UniCoreFW.

This module provides functionality for template processing with variable interpolation
and basic conditional logic.

Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info

This file is part of UniCoreFW. You can redistribute it and/or modify
it under the terms of the [BSD-3-Clause] as published by
the Free Software Foundation.
You should have received a copy of the [BSD-3-Clause] license
along with UniCoreFW. If not, see https://www.gnu.org/licenses/.
"""

import html
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .security import (
    ResourceLimitError,
    SecurityError,
    _validate_resource_limit,
    sanitize_string,
)

_HARD_MAX_TEMPLATE_LENGTH = 1_000_000
_HARD_MAX_TEMPLATE_TOKENS = 100_000
_HARD_MAX_TEMPLATE_NESTING_DEPTH = 256
_HARD_MAX_TEMPLATE_OUTPUT_LENGTH = 16_000_000
_HARD_MAX_TEMPLATE_CONTEXT_ITEMS = 100_000

_TEMPLATE_TOKEN_RE = re.compile(r"<%=?[^%]*?%>")
_RAW_HTML_TAG_RE = re.compile(
    r"</?(?P<tag>script|style)\b[^>]*>",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class TemplateLimits:
    """Resource budgets for one template rendering operation."""

    max_template_length: int = 10_000
    max_tokens: int = 1_000
    max_nesting_depth: int = 32
    max_output_length: int = 1_000_000
    max_context_items: int = 1_000

    def __post_init__(self) -> None:
        _validate_resource_limit(
            self.max_template_length,
            "max_template_length",
            _HARD_MAX_TEMPLATE_LENGTH,
        )
        _validate_resource_limit(
            self.max_tokens,
            "max_tokens",
            _HARD_MAX_TEMPLATE_TOKENS,
        )
        _validate_resource_limit(
            self.max_nesting_depth,
            "max_nesting_depth",
            _HARD_MAX_TEMPLATE_NESTING_DEPTH,
        )
        _validate_resource_limit(
            self.max_output_length,
            "max_output_length",
            _HARD_MAX_TEMPLATE_OUTPUT_LENGTH,
        )
        _validate_resource_limit(
            self.max_context_items,
            "max_context_items",
            _HARD_MAX_TEMPLATE_CONTEXT_ITEMS,
        )


def _resolve_limits(limits: Optional[TemplateLimits]) -> TemplateLimits:
    if limits is None:
        return TemplateLimits()
    if not isinstance(limits, TemplateLimits):
        raise TypeError("limits must be a TemplateLimits instance")
    return limits


def _validate_template_source(template_str: str, limits: TemplateLimits) -> None:
    if not isinstance(template_str, str):
        raise TypeError("template_str must be a string")
    if len(template_str) > limits.max_template_length:
        raise ResourceLimitError(
            "template source length",
            limits.max_template_length,
            len(template_str),
        )


def _validate_html_interpolation_contexts(template_str: str) -> None:
    """Allow dynamic values only in HTML text nodes."""
    raw_tag: Any = None
    raw_matches = iter(_RAW_HTML_TAG_RE.finditer(template_str))
    next_raw_match = next(raw_matches, None)
    last_open = -1
    last_close = -1
    scan_start = 0

    for token_match in _TEMPLATE_TOKEN_RE.finditer(template_str):
        token_start = token_match.start()

        while next_raw_match is not None and next_raw_match.start() < token_start:
            tag_text = next_raw_match.group(0)
            matched_tag = next_raw_match.group("tag").lower()
            if raw_tag is None and not tag_text.startswith("</"):
                raw_tag = matched_tag
            elif tag_text.startswith("</") and matched_tag == raw_tag:
                raw_tag = None
            next_raw_match = next(raw_matches, None)

        segment_open = template_str.rfind("<", scan_start, token_start)
        segment_close = template_str.rfind(">", scan_start, token_start)
        if segment_open >= 0:
            last_open = segment_open
        if segment_close >= 0:
            last_close = segment_close
        if last_open > last_close:
            raise SecurityError(
                "HTML template expressions are allowed only in text nodes, "
                "not inside tags or attributes"
            )
        if raw_tag is not None:
            raise SecurityError(
                f"HTML template expressions are not allowed in {raw_tag} blocks"
            )
        scan_start = token_match.end()


def _render_template(
    template_str: str,
    context: Dict[str, Any],
    *,
    autoescape: bool,
    limits: TemplateLimits,
) -> str:
    """
    Process a template string with a context of variables.

    The template format supports variable interpolation with `<%= variable %>`
    and conditional statements with `<% if condition %>` and `<% endif %>`.

    Args:
        template_str: The template string to process
        context: Dictionary of variables to use in the template
        autoescape: Whether to HTML-escape interpolated values
        limits: Resource budgets for this render

    Returns:
        The processed template

    Raises:
        ValueError: If the template contains invalid syntax
        SecurityError: If potentially dangerous patterns are detected

    Examples:
        >>> template("Hello, <%= name %>!", {"name": "John"})
        "Hello, John!"
    """
    _validate_template_source(template_str, limits)
    template_str = sanitize_string(
        template_str,
        max_length=limits.max_template_length,
    )
    if not isinstance(context, dict):
        raise TypeError("Context must be a dictionary")
    if len(context) > limits.max_context_items:
        raise ResourceLimitError(
            "template context items",
            limits.max_context_items,
            len(context),
        )
    # Validate context values
    for key, value in context.items():
        if not isinstance(key, str):
            raise TypeError(f"Context key '{key}' must be a string")
        if callable(value):
            from .security import validate_callable

            validate_callable(value, f"context['{key}']")

    # Check for dangerous patterns
    dangerous_patterns = (
        r"<%=.*?.__(class|bases|subclasses|globals|dict|code|builtins|module)__.*?%>"
    )
    if re.search(dangerous_patterns, template_str):
        raise SecurityError("Potentially dangerous template pattern detected")

    token_matches = list(_TEMPLATE_TOKEN_RE.finditer(template_str))
    if len(token_matches) > limits.max_tokens:
        raise ResourceLimitError(
            "template token count",
            limits.max_tokens,
            len(token_matches),
        )

    tokens: List[str] = []
    cursor = 0
    for token_match in token_matches:
        tokens.append(template_str[cursor : token_match.start()])
        tokens.append(token_match.group(0))
        cursor = token_match.end()
    tokens.append(template_str[cursor:])

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
            if method is not None:
                return method()
        else:
            raise ValueError(
                f"Method '{method_name}' is not allowed on object of type '{type(obj).__name__}'."
            )

    # Process the template
    output: List[str] = []
    output_length = 0
    skip_stack = []  # Track conditional blocks
    idx = 0

    def append_output(value: str) -> None:
        nonlocal output_length
        prospective_length = output_length + len(value)
        if prospective_length > limits.max_output_length:
            raise ResourceLimitError(
                "template output length",
                limits.max_output_length,
                prospective_length,
            )
        output.append(value)
        output_length = prospective_length

    while idx < len(tokens):
        token = tokens[idx]

        # Handle variable interpolation
        if token.startswith("<%=") and token.endswith("%>"):
            if not any(skip_stack):  # Only process if not in a skipped block
                expr = token[3:-2].strip()
                value = evaluate_expression(expr, context)
                rendered_value = str(value)
                if autoescape:
                    rendered_value = html.escape(rendered_value, quote=True)
                append_output(rendered_value)

        # Handle control statements
        elif token.startswith("<%") and token.endswith("%>"):
            tag_content = token[2:-2].strip()

            # if statement
            if tag_content.startswith("if "):
                if len(skip_stack) >= limits.max_nesting_depth:
                    raise ResourceLimitError(
                        "template nesting depth",
                        limits.max_nesting_depth,
                        len(skip_stack) + 1,
                    )
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
                append_output(token)

        idx += 1

    # Check for unclosed conditional blocks
    if skip_stack:
        raise ValueError("Unclosed 'if' statement detected.")

    return "".join(output)


def template(
    template_str: str,
    context: Dict[str, Any],
    *,
    limits: Optional[TemplateLimits] = None,
) -> str:
    """Render a trusted plain-text template under fixed resource budgets.

    Args:
        template_str: Trusted template source
        context: Values available to expressions
        limits: Optional per-render resource budgets

    Raises:
        ResourceLimitError: If rendering exhausts a budget
        InputValidationError: If a limit setting is invalid
    """
    resolved_limits = _resolve_limits(limits)
    return _render_template(
        template_str,
        context,
        autoescape=False,
        limits=resolved_limits,
    )


def html_template(
    template_str: str,
    context: Dict[str, Any],
    *,
    limits: Optional[TemplateLimits] = None,
) -> str:
    """Render untrusted values into HTML text nodes with escaping enabled.

    The template source itself must be trusted. Dynamic expressions inside
    tags, attributes, script blocks, or style blocks are rejected because HTML
    escaping alone is not sufficient for those contexts.

    Args:
        template_str: Trusted HTML template source
        context: Values available to text-node expressions
        limits: Optional per-render resource budgets

    Raises:
        ResourceLimitError: If rendering exhausts a budget
        InputValidationError: If a limit setting is invalid
        SecurityError: If an expression appears outside an HTML text node
    """
    resolved_limits = _resolve_limits(limits)
    _validate_template_source(template_str, resolved_limits)
    _validate_html_interpolation_contexts(template_str)
    return _render_template(
        template_str,
        context,
        autoescape=True,
        limits=resolved_limits,
    )
