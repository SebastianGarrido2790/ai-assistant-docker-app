"""
Diagnostic script to verify the safety and functionality of the calculate_tool.

This script ensures that the transition from `eval()` to `simple_eval()` correctly
supports standard math operations and constants while successfully blocking
malicious injection payloads (e.g., attribute access, MRO escapes).

Usage:
    uv run python scripts/test_calculator_safety.py
"""

import math
import os
import sys

# Add root to path to allow 'import src'
sys.path.append(os.getcwd())

from src.tools.tools import calculate_tool


def test_calculator():
    """
    Execute a suite of functional and security tests on the calculator tool.

    Tests cover:
    1. Basic arithmetic (addition).
    2. Trigonometric and math functions (sin, sqrt, pow).
    3. Mathematical constants (pi).
    4. Safety boundaries (blocking __class__ and __mro__ access).
    """
    print("Testing basic addition...")
    assert calculate_tool.invoke({"expression": "2 + 2"}) == "4"

    print("Testing math functions (sin)...")
    result = calculate_tool.invoke({"expression": "sin(0)"})
    assert float(result) == 0.0

    print("Testing constants (pi)...")
    result = calculate_tool.invoke({"expression": "pi"})
    assert float(result) == math.pi

    print("Testing nested expression...")
    result = calculate_tool.invoke({"expression": "sqrt(16) + pow(2, 3)"})
    assert float(result) == 12.0

    print("Testing safety (eval attack)...")
    # This should fail or be blocked by simpleeval
    # Attempting to access __class__ or similar
    result = calculate_tool.invoke({"expression": "''.__class__.__mro__"})
    assert "Error" in result or "not allowed" in result or "Undefined" in result

    print("All tests passed!")


if __name__ == "__main__":
    try:
        test_calculator()
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
