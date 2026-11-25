"""Testes unitários das entidades de domínio e value objects (SRP e Invariantes)."""

import unittest
from decimal import Decimal

from nexus.domain.entities import Order, OrderItem
from nexus.domain.exceptions import (
    CurrencyMismatchError,
    EmptyOrderError,
    InvalidAmountError,
)
from nexus.domain.value_objects import Address, Currency, Money, OrderStatus


class TestDomainEntities(unittest.TestCase):
    def setUp(self) -> None:
        self.sample_address = Address(
            street="Rua das Acácias",
            number="123",
            city="Campinas",
            state="SP",
            postal_code="13083852",
        )

    def test_money_arithmetic_and_invariants(self) -> None:
        m1 = Money.from_float(100.50)
        m2 = Money.from_float(49.50)

        total = m1.add(m2)
        self.assertEqual(total.amount, Decimal("150.00"))
        self.assertEqual(str(total), "BRL 150.00")

        diff = m1.subtract(m2)
        self.assertEqual(diff.amount, Decimal("51.00"))

        multiplied = m2.multiply(2)
        self.assertEqual(multiplied.amount, Decimal("99.00"))

    def test_money_negative_amount_raises_error(self) -> None:
        with self.assertRaises(InvalidAmountError):
            Money(amount=Decimal("-10.00"))

    def test_money_currency_mismatch_raises_error(self) -> None:
        brl = Money(amount=Decimal("10.00"), currency=Currency.BRL)
        usd = Money(amount=Decimal("10.00"), currency=Currency.USD)
        with self.assertRaises(CurrencyMismatchError):
            brl.add(usd)

    def test_order_item_calculations(self) -> None:
        item = OrderItem(
            product_id="P1",
            product_name="Teclado",
            unit_price=Money.from_float(150.00),
            quantity=3,
            weight_kg=0.5,
        )
        self.assertEqual(item.subtotal.amount, Decimal("450.00"))
        self.assertEqual(item.total_weight, 1.5)

    def test_order_cannot_be_empty(self) -> None:
        with self.assertRaises(EmptyOrderError):
            Order(
                customer_email="teste@puc.br",
                delivery_address=self.sample_address,
                items=[],
            )

    def test_order_financial_totals(self) -> None:
        items = [
            OrderItem(
                product_id="P1",
                product_name="Produto 1",
                unit_price=Money.from_float(100.00),
                quantity=2,
                weight_kg=1.0,
            ),
            OrderItem(
                product_id="P2",
                product_name="Produto 2",
                unit_price=Money.from_float(50.00),
                quantity=1,
                weight_kg=0.5,
            ),
        ]
        order = Order(
            customer_email="cliente@teste.com",
            delivery_address=self.sample_address,
            items=items,
            shipping_cost=Money.from_float(30.00),
            discount=Money.from_float(20.00),
        )

        self.assertEqual(order.items_subtotal.amount, Decimal("250.00"))
        self.assertEqual(order.total_weight_kg, 2.5)
        # (250 + 30) - 20 = 260
        self.assertEqual(order.final_total.amount, Decimal("260.00"))
        self.assertEqual(order.status, OrderStatus.PENDING_PAYMENT)


if __name__ == "__main__":
    unittest.main()
