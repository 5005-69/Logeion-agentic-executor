"""
Golden Ratio Calculator — main entry point
"""
from phi_calculator.calculator import compute_phi
from phi_calculator.formatter import format_result
from phi_calculator.validator import is_valid_precision


def run(precision: int = 10):
    if not is_valid_precision(precision):
        print(f"Invalid precision: {precision}")
        return

    phi = compute_phi(precision)
    output = format_result(phi, precision)
    print(output)


if __name__ == "__main__":
    run(precision=12)
