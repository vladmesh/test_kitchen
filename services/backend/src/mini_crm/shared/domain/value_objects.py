from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Money:
    """Value object representing money with amount and currency."""

    amount: Decimal
    currency: str = "USD"

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if not self.currency:
            raise ValueError("Currency cannot be empty")

    def __add__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            raise TypeError("Can only add Money to Money")
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} to {other.currency}")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __sub__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            raise TypeError("Can only subtract Money from Money")
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {other.currency} from {self.currency}")
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def __mul__(self, multiplier: Decimal | int | float) -> Money:
        if not isinstance(multiplier, (Decimal, int, float)):
            raise TypeError("Multiplier must be a number")
        return Money(amount=self.amount * Decimal(str(multiplier)), currency=self.currency)

    def __truediv__(self, divisor: Decimal | int | float) -> Money:
        if not isinstance(divisor, (Decimal, int, float)):
            raise TypeError("Divisor must be a number")
        if divisor == 0:
            raise ValueError("Cannot divide by zero")
        return Money(amount=self.amount / Decimal(str(divisor)), currency=self.currency)

    def __lt__(self, other: Money) -> bool:
        if not isinstance(other, Money):
            raise TypeError("Can only compare Money with Money")
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare {self.currency} with {other.currency}")
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        return self < other or self == other

    def __gt__(self, other: Money) -> bool:
        if not isinstance(other, Money):
            raise TypeError("Can only compare Money with Money")
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare {self.currency} with {other.currency}")
        return self.amount > other.amount

    def __ge__(self, other: Money) -> bool:
        return self > other or self == other

    def is_positive(self) -> bool:
        """Check if amount is positive."""
        return self.amount > 0

    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self.amount == 0

    def is_negative(self) -> bool:
        """Check if amount is negative."""
        return self.amount < 0
