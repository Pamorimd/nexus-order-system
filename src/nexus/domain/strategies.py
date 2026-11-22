"""Padrão GoF Comportamental: Strategy (Refactoring Guru).

Permite a definição de uma família de algoritmos de tarifação de frete e
concessão de descontos, tornando-os intercambiáveis em tempo de execução.
Atende diretamente ao Princípio Aberto/Fechado (OCP).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from nexus.domain.value_objects import Money


class ShippingStrategy(ABC):
    """Interface comum para todas as estratégias de cálculo de frete."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nome identificador da modalidade de envio."""

    @abstractmethod
    def calculate(
        self, origin_cep: str, destination_cep: str, total_weight_kg: float
    ) -> Money:
        """Calcula o valor do frete."""

    @abstractmethod
    def estimated_delivery_days(self) -> int:
        """Retorna o prazo estimado em dias úteis."""


class SedexShippingStrategy(ShippingStrategy):
    """Estratégia de envio expresso estatal (Correios Sedex)."""

    @property
    def name(self) -> str:
        return "CORREIOS_SEDEX"

    def calculate(
        self, origin_cep: str, destination_cep: str, total_weight_kg: float
    ) -> Money:
        # Tarifa base expressa + R$ 6.50 por kg
        base_rate = Decimal("25.00")
        weight_rate = Decimal(str(total_weight_kg)) * Decimal("6.50")
        # Adicional interestadual se os primeiros dígitos do CEP diferirem
        interstate_fee = Decimal("10.00") if origin_cep[0] != destination_cep[0] else Decimal("0.00")
        return Money(amount=base_rate + weight_rate + interstate_fee)

    def estimated_delivery_days(self) -> int:
        return 2


class PacShippingStrategy(ShippingStrategy):
    """Estratégia de envio econômico estatal (Correios PAC)."""

    @property
    def name(self) -> str:
        return "CORREIOS_PAC"

    def calculate(
        self, origin_cep: str, destination_cep: str, total_weight_kg: float
    ) -> Money:
        # Tarifa base econômica + R$ 3.00 por kg
        base_rate = Decimal("14.00")
        weight_rate = Decimal(str(total_weight_kg)) * Decimal("3.00")
        interstate_fee = Decimal("5.00") if origin_cep[0] != destination_cep[0] else Decimal("0.00")
        return Money(amount=base_rate + weight_rate + interstate_fee)

    def estimated_delivery_days(self) -> int:
        return 6


class ExpressTransportadoraShippingStrategy(ShippingStrategy):
    """Estratégia de frete corporativo ultra-rápido privado."""

    @property
    def name(self) -> str:
        return "TRANSPORTADORA_EXPRESS"

    def calculate(
        self, origin_cep: str, destination_cep: str, total_weight_kg: float
    ) -> Money:
        # Tarifa fixa premium com desconto para cargas leves
        base_rate = Decimal("38.00")
        weight_rate = Decimal(str(total_weight_kg)) * Decimal("4.00")
        return Money(amount=base_rate + weight_rate)

    def estimated_delivery_days(self) -> int:
        return 1


class DiscountStrategy(ABC):
    """Estratégia para concessão de descontos sobre o subtotal do pedido."""

    @abstractmethod
    def apply_discount(self, subtotal: Money) -> Money:
        """Calcula o valor nominal do desconto a ser abatido."""


class NoDiscountStrategy(DiscountStrategy):
    """Estratégia padrão nula (Null Object Pattern)."""

    def apply_discount(self, subtotal: Money) -> Money:
        return Money.zero(currency=subtotal.currency)


class PercentageDiscountStrategy(DiscountStrategy):
    """Aplica uma porcentagem fixa de desconto."""

    def __init__(self, percentage: Decimal) -> None:
        self.percentage = percentage

    def apply_discount(self, subtotal: Money) -> Money:
        factor = self.percentage / Decimal("100.00")
        return subtotal.multiply(factor)


class PixCashbackDiscountStrategy(DiscountStrategy):
    """Desconto promocional fixo de 5% para pagamentos instantâneos via Pix."""

    def apply_discount(self, subtotal: Money) -> Money:
        return subtotal.multiply(Decimal("0.05"))
