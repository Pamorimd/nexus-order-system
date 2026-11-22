"""Adaptador dos Correios (Empresa Brasileira de Correios e Telégrafos).

Implementa a porta ShippingCalculatorPort utilizando estratégias GoF.
"""

from __future__ import annotations

from nexus.domain.ports import ShippingCalculatorPort
from nexus.domain.strategies import PacShippingStrategy, SedexShippingStrategy, ShippingStrategy
from nexus.domain.value_objects import Money


class CorreiosShippingAdapter(ShippingCalculatorPort):
    """Adaptador de integração logística com a malha dos Correios."""

    def __init__(self, mode: str = "SEDEX") -> None:
        self.strategy: ShippingStrategy = (
            SedexShippingStrategy() if mode.upper() == "SEDEX" else PacShippingStrategy()
        )

    def calculate_shipping(
        self, origin_cep: str, destination_cep: str, weight_kg: float
    ) -> Money:
        return self.strategy.calculate(origin_cep, destination_cep, weight_kg)

    def estimate_days(self, origin_cep: str, destination_cep: str) -> int:
        return self.strategy.estimated_delivery_days()
