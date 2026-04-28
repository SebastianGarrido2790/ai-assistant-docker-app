"""
Security utilities for the agentic workflow.

This module provides defenses against prompt injection attacks and ensures
tool inputs conform to safety boundaries (length capping).
"""

import re

from loguru import logger

# Patterns that attempt to override agent instructions or escape context
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore (all )?(previous|prior|above) instructions?", re.IGNORECASE),
    re.compile(r"you are now", re.IGNORECASE),
    re.compile(r"disregard (your )?(system )?prompt", re.IGNORECASE),
    re.compile(r"<\s*(system|SYSTEM)\s*>"),  # Escaped system-tag injection
    re.compile(r"\[INST\]|\[\/INST\]"),  # Llama-style instruction tags
]

_MAX_INPUT_LENGTH: int = 2_000  # Hard cap; tune per tool's context budget


def sanitize_tool_input(text: str) -> str:
    """Sanitize free-text tool input against prompt injection attacks.

    Applies a length cap and pattern-based rejection of known injection
    vectors before the value is embedded in any agent prompt or query.

    Args:
        text: The raw user-supplied string.

    Returns:
        The sanitized string, safe for downstream prompt inclusion.

    Raises:
        ValueError: If the input matches a known injection pattern.
    """
    if not text:
        return ""

    if len(text) > _MAX_INPUT_LENGTH:
        logger.warning(
            f"Input length {len(text)} exceeds cap. Truncating to {_MAX_INPUT_LENGTH}."
        )
        text = text[:_MAX_INPUT_LENGTH]

    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            logger.error(f"Potential prompt injection detected: {pattern.pattern}")
            raise ValueError(
                "Input rejected: potential prompt injection detected. "
                "Pattern matches restricted security policy."
            )

    return text.strip()
