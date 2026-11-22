"""Testes do Padrão GoF: State (Ciclo de Vida do Pedido e Transições Válidas/Inválidas)."""

import unittest

from nexus.domain.entities import Order, OrderItem
from nexus.domain.exceptions import InvalidStateTransitionError
from nexus.domain.value_objects import Address, Money, OrderStatus


class TestGofState(unittest.TestCase):
    def setUp(self) -> None:
        address = Address("Rua Teste", "10", "Campinas", "SP", "13083852")
        items = [
            OrderItem("P1", "Item Teste", Money.from_float(50.00), quantity=1, weight_kg=0.5)
        ]
        self.base_order = Order(customer_email="teste@puc.br", delivery_address=address, items=items)

    def test_order_happy_path_transitions(self) -> None:
        # 1. Estado inicial
        self.assertEqual(self.base_order.status, OrderStatus.PENDING_PAYMENT)

        # 2. Pagar -> PAID
        self.base_order.pay(transaction_id="TX-123456")
        self.assertEqual(self.base_order.status, OrderStatus.PAID)
        self.assertEqual(self.base_order.transaction_id, "TX-123456")

        # 3. Despachar -> SHIPPED
        self.base_order.ship(tracking_code="TRACK-BR-001")
        self.assertEqual(self.base_order.status, OrderStatus.SHIPPED)
        self.assertEqual(self.base_order.tracking_code, "TRACK-BR-001")

    def test_order_cancel_from_pending(self) -> None:
        self.assertEqual(self.base_order.status, OrderStatus.PENDING_PAYMENT)
        self.base_order.cancel(reason="Cliente solicitou desistência antes do pagamento.")
        self.assertEqual(self.base_order.status, OrderStatus.CANCELLED)
        self.assertEqual(
            self.base_order.cancellation_reason,
            "Cliente solicitou desistência antes do pagamento.",
        )

    def test_order_cancel_from_paid(self) -> None:
        self.base_order.pay(transaction_id="TX-999")
        self.assertEqual(self.base_order.status, OrderStatus.PAID)

        self.base_order.cancel(reason="Estorno solicitado antes do envio.")
        self.assertEqual(self.base_order.status, OrderStatus.CANCELLED)

    def test_illegal_transition_ship_unpaid_order(self) -> None:
        self.assertEqual(self.base_order.status, OrderStatus.PENDING_PAYMENT)
        with self.assertRaises(InvalidStateTransitionError):
            self.base_order.ship(tracking_code="FAIL-TRACK")

    def test_illegal_transition_pay_twice(self) -> None:
        self.base_order.pay(transaction_id="TX-FIRST")
        with self.assertRaises(InvalidStateTransitionError):
            self.base_order.pay(transaction_id="TX-SECOND")

    def test_illegal_transition_cancel_shipped_order(self) -> None:
        self.base_order.pay(transaction_id="TX-OK")
        self.base_order.ship(tracking_code="TRACK-OK")

        with self.assertRaises(InvalidStateTransitionError):
            self.base_order.cancel(reason="Arrependimento tardio")

    def test_illegal_transition_operate_cancelled_order(self) -> None:
        self.base_order.cancel(reason="Cancelado")
        with self.assertRaises(InvalidStateTransitionError):
            self.base_order.pay(transaction_id="TX-NEVER")
        with self.assertRaises(InvalidStateTransitionError):
            self.base_order.ship(tracking_code="TRACK-NEVER")
        with self.assertRaises(InvalidStateTransitionError):
            self.base_order.cancel(reason="Cancelar novamente")


if __name__ == "__main__":
    unittest.main()
