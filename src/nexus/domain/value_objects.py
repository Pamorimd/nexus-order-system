"""Objetos de Valor (Value Objects) do domínio Nexus.

Objetos imutáveis que evitam o code smell 'Primitive Obsession' (Refactoring Guru),
garantindo invariantes de negócio na própria instanciação.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from enum import Enum
import uuid

from nexus.domain.exceptions import CurrencyMismatchError, InvalidAmountError


class Currency(str, Enum):
    """Moedas suportadas pelo sistema."""

    BRL = "BRL"
    USD = "USD"


class PaymentMethod(str, Enum):
    """Métodos de pagamento disponíveis no checkout."""

    PIX = "PIX"
    CREDIT_CARD = "CREDIT_CARD"
    BOLETO = "BOLETO"


class OrderStatus(str, Enum):
    """Estados do ciclo de vida do pedido."""

    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class Money:
    """Objeto de valor monetário imutável com precisão decimal.

    Evita problemas de ponto flutuante em cálculos financeiros.
    """

    amount: Decimal
    currency: Currency = Currency.BRL

    def __post_init__(self) -> None:
        if self.amount < Decimal("0.00"):
            raise InvalidAmountError("O valor monetário não pode ser negativo.")
        # Garante quantização em 2 casas decimais
        quantized = self.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        object.__setattr__(self, "amount", quantized)

    @classmethod
    def zero(cls, currency: Currency = Currency.BRL) -> Money:
        return cls(amount=Decimal("0.00"), currency=currency)

    @classmethod
    def from_float(cls, value: float, currency: Currency = Currency.BRL) -> Money:
        return cls(amount=Decimal(str(value)), currency=currency)

    def add(self, other: Money) -> Money:
        self._ensure_same_currency(other)
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def subtract(self, other: Money) -> Money:
        self._ensure_same_currency(other)
        if other.amount > self.amount:
            raise InvalidAmountError("Resultado monetário negativo não é permitido.")
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def multiply(self, factor: Decimal | int | float) -> Money:
        factor_dec = Decimal(str(factor))
        if factor_dec < Decimal("0.00"):
            raise InvalidAmountError("Fator multiplicativo não pode ser negativo.")
        return Money(amount=self.amount * factor_dec, currency=self.currency)

    def _ensure_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise CurrencyMismatchError(
                f"Incompatibilidade de moedas: {self.currency} vs {other.currency}"
            )

    def __str__(self) -> str:
        return f"{self.currency.value} {self.amount:.2f}"


@dataclass(frozen=True)
class Address:
    """Endereço de entrega normalizado."""

    street: str
    number: str
    city: str
    state: str
    postal_code: str  # CEP normalizado (apenas 8 dígitos)


def generate_order_id() -> str:
    """Gera um identificador único para o pedido."""
    return f"ORD-{uuid.uuid4().hex[:8].upper()}"
