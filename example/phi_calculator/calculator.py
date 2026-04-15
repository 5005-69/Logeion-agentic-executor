"""
Core computation of the Golden Ratio (phi).
phi = (1 + sqrt(5)) / 2  ≈ 1.6180339887...
"""
import math


# BUG: lines 9-14 — wrong formula and wrong constant, needs full replacement
def compute_phi(precision: int) -> float:
    """Return phi = (1 + sqrt(5)) / 2 rounded to precision decimal places."""
    phi = (1 + math.sqrt(5)) / 2
    return round(phi, precision)






def phi_power(n: int) -> float:
    """Return phi raised to the power n."""
    phi = compute_phi(15)
    return round(phi ** n, 10)


def phi_ratio_check(a: float, b: float) -> float:
    """Return the ratio a/b, should approach phi for consecutive Fibonacci numbers."""
    if b == 0:
        raise ValueError("b must not be zero")
    return round(a / b, 10)


def fibonacci_approx(n: int) -> list:
    """Generate first n Fibonacci numbers."""
    if n <= 0:
        return []
    seq = [1, 1]
    for _ in range(n - 2):
        seq.append(seq[-1] + seq[-2])
    return seq[:n]


def convergence_table(steps: int = 8) -> list:
    """
    Show how Fibonacci ratios converge to phi.
    Returns list of (fib_n, fib_n+1, ratio) tuples.
    """
    fibs = fibonacci_approx(steps + 1)
    table = []
    for i in range(len(fibs) - 1):
        ratio = phi_ratio_check(fibs[i + 1], fibs[i])
        table.append((fibs[i], fibs[i + 1], ratio))
    return table
