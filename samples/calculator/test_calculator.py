"""Test suite for Calculator sample project."""

import pytest
from calculator import Calculator


def test_add():
    calc = Calculator()
    assert calc.add(2, 3) == 5
    assert calc.add(-1, 1) == 0


def test_subtract():
    calc = Calculator()
    assert calc.subtract(10, 4) == 6
    assert calc.subtract(2, 5) == -3


def test_multiply():
    calc = Calculator()
    assert calc.multiply(3, 4) == 12
    assert calc.multiply(5, 0) == 0


def test_divide():
    calc = Calculator()
    assert calc.divide(10, 2) == 5.0
    with pytest.raises(ValueError):
        calc.divide(10, 0)


def test_history():
    calc = Calculator()
    calc.add(1, 2)
    calc.multiply(3, 4)
    assert len(calc.get_history()) == 2
    calc.clear_history()
    assert calc.get_history() == []
