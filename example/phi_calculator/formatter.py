"""
Output formatting for phi calculation results.
"""


from phi_calculator.calculator import phi_power
from phi_calculator.calculator import convergence_table


HEADER = "=" * 40


def format_result(phi: float, precision: int) -> str:
    """Format the main phi result as a readable string."""
    label = f"phi (precision={precision})"
    value = f"{phi:.{precision}f}"
    return f"{HEADER}\n  Golden Ratio\n  {label}: {value}\n{HEADER}"


def format_powers(max_power: int = 5) -> str:
    """Format a table of phi powers."""
    lines = [HEADER, "  phi powers", HEADER]
    for n in range(1, max_power + 1):
        val = phi_power(n)
        lines.append(f"  phi^{n} = {val}")
    lines.append(HEADER)
    return "\n".join(lines)


def format_convergence() -> str:
    """Format the Fibonacci convergence table."""
    rows = convergence_table()
    lines = [HEADER, "  Fibonacci convergence to phi", HEADER]
    for a, b, ratio in rows:
        lines.append(f"  {a:>5} / {b:>5} = {ratio}")
    lines.append(HEADER)
    return "\n".join(lines)


def full_report(phi: float, precision: int) -> str:
    """Combine all sections into one report."""
    parts = [
        format_result(phi, precision),
        format_powers(),
        format_convergence(),
    ]
    return "\n\n".join(parts)
