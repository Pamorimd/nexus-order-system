"""Testes do Padrão GoF: Strategy (Cálculo de Frete e Descontos)."""

from decimal import Decimal
import unittest

from nexus.domain.strategies import (
    ExpressTransportadoraShippingStrategy,
    NoDiscountStrategy,
    PacShippingStrategy,
    PercentageDiscountStrategy,
    PixCashbackDiscountStrategy,
    SedexShippingStrategy,
)
from nexus.domain.value_objects import Money


class TestGofStrategy(unittest.TestCase):
    def test_sedex_shipping_strategy(self) -> None:
        strategy = SedexShippingStrategy()
        self.assertEqual(strategy.name, "CORREIOS_SEDEX")
        self.assertEqual(strategy.estimated_delivery_days(), 2)

        # Mesmo estado (início do CEP igual): 25 + (2 * 6.5) = 38.00
        cost_same_state = strategy.calculate("13083852", "13010000", total_weight_kg=2.0)
        self.assertEqual(cost_same_state.amount, Decimal("38.00"))

        # Estados distintos (primeiro dígito diferente): 25 + (2 * 6.5) + 10 = 48.00
        cost_interstate = strategy.calculate("13083852", "01000000", total_weight_kg=2.0)
        self.assertEqual(cost_interstate.amount, Decimal("48.00"))

    def test_pac_shipping_strategy(self) -> None:
        strategy = PacShippingStrategy()
        self.assertEqual(strategy.name, "CORREIOS_PAC")
        self.assertEqual(strategy.estimated_delivery_days(), 6)

        cost = strategy.calculate("13083852", "13010000", total_weight_kg=3.0)
        # 14 + (3 * 3.0) = 23.00
        self.assertEqual(cost.amount, Decimal("23.00"))

    def test_express_transportadora_shipping_strategy(self) -> None:
        strategy = ExpressTransportadoraShippingStrategy()
        self.assertEqual(strategy.name, "TRANSPORTADORA_EXPRESS")
        self.assertEqual(strategy.estimated_delivery_days(), 1)

        cost = strategy.calculate("13083852", "80000000", total_weight_kg=2.5)
        # 38 + (2.5 * 4.0) = 48.00
        self.assertEqual(cost.amount, Decimal("48.00"))

    def test_discount_strategies(self) -> None:
        subtotal = Money.from_float(200.00)

        no_discount = NoDiscountStrategy().apply_discount(subtotal)
        self.assertEqual(no_discount.amount, Decimal("0.00"))

        pct_discount = PercentageDiscountStrategy(Decimal("15.0")).apply_discount(subtotal)
        self.assertEqual(pct_discount.amount, Decimal("30.00"))

        pix_cashback = PixCashbackDiscountStrategy().apply_discount(subtotal)
        self.assertEqual(pix_cashback.amount, Decimal("10.00"))


if __name__ == "__main__":
    unittest.main()
