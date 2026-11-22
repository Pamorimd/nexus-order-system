"""Adaptador de Transportadora Expressa Privada.

Implementa a porta ShippingCalculatorPort utilizando estratégia GoF.
"""

from __future__ import annotations

from nexus.domain.ports import ShippingCalculatorPort
from nexus.domain.strategies import ExpressTransportadoraShippingStrategy
from nexus.domain.value_objects import Money


class ExpressTransportadoraShippingAdapter(ShippingCalculatorPort):
    """Adaptador de integração logística com malha rodoviária e aérea privada."""

    def __init__(self) -> None:
        self.strategy = ExpressTransportadoraShippingStrategy()

    def calculate_shipping(
        self, origin_cep: str, destination_cep: str, weight_kg: float
    ) -> Money:
        return self.strategy.calculate(origin_cep, destination_cep, weight_kg)

    def estimate_days(self, origin_cep: str, destination_cep: str) -> int:
        return self.strategy.estimated_delivery_days()
