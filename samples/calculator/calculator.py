"""Reference implementation for the Calculator sample project."""

from typing import List, Union

Number = Union[int, float]


class Calculator:
    """Basic arithmetic calculator with operation history tracking."""

    def __init__(self) -> None:
        self.history: List[str] = []

    def add(self, a: Number, b: Number) -> Number:
        res = a + b
        self.history.append(f"{a} + {b} = {res}")
        return res

    def subtract(self, a: Number, b: Number) -> Number:
        res = a - b
        self.history.append(f"{a} - {b} = {res}")
        return res

    def multiply(self, a: Number, b: Number) -> Number:
        res = a * b
        self.history.append(f"{a} * {b} = {res}")
        return res

    def divide(self, a: Number, b: Number) -> float:
        if b == 0:
            raise ValueError("Cannot divide by zero")
        res = a / b
        self.history.append(f"{a} / {b} = {res}")
        return res

    def get_history(self) -> List[str]:
        return list(self.history)

    def clear_history(self) -> None:
        self.history.clear()
