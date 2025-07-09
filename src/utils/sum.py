"""Module for some functions to test like building a python module.

The we then include in Jupyter Notebook, iPython or scripts.
We also validate linting with these functions.
"""


def my_sum(a: float, b: float) -> float:
    """This is my_sum."""
    return a + b


def my_sum_three(a: int, b: int, c: int) -> int:
    """This is my_sum_three."""
    return a + b + c


def a(c: int, d: int) -> int:
    """a."""
    return c + d + 10 + 4


def sum_even_numbers(numbers: list[int]) -> int:
    """Sum all even numbers in the given list.

    Args:
        numbers: List of integers to sum
    """
    return sum(num for num in numbers if num % 2 == 0)
