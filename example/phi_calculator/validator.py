"""
Input validation for phi calculator.
"""


# BUG: lines 7-13 — wrong bounds and wrong return type, needs full replacement
def is_valid_precision(precision) -> bool:
    """Accept only int in range 1–50."""
    if not isinstance(precision, int):
        return False
    return 1 <= precision <= 50






def is_valid_power(n) -> bool:
    """Return True if n is a valid exponent (positive integer, max 100)."""
    if not isinstance(n, int):
        return False
    return 1 <= n <= 100


def is_positive_float(value) -> bool:
    """Return True if value is a positive float or int."""
    if not isinstance(value, (int, float)):
        return False
    return value > 0


def validate_ratio_inputs(a, b) -> tuple[bool, str]:
    """
    Validate inputs for ratio computation.
    Returns (is_valid, error_message).
    """
    if not is_positive_float(a):
        return False, f"a must be a positive number, got {a!r}"
    if not is_positive_float(b):
        return False, f"b must be a positive number, got {b!r}"
    return True, ""


def validate_fibonacci_n(n) -> tuple[bool, str]:
    """Validate n for fibonacci sequence generation."""
    if not isinstance(n, int):
        return False, f"n must be an integer, got {type(n).__name__}"
    if n < 1:
        return False, f"n must be at least 1, got {n}"
    if n > 1000:
        return False, f"n is too large (max 1000), got {n}"
    return True, ""
