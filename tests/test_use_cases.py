"""Testes dos casos de uso da camada de aplicação do Nexus."""

import unittest

from nexus.adapters.gateways.factory import PaymentGatewayFactory
from nexus.adapters.persistence.memory_repo import InMemoryOrderRepository
from nexus.application.dtos import (
    CreateOrderInputDTO,
    ItemInputDTO,
    ProcessPaymentInputDTO,
)
from nexus.application.use_cases import (
    CancelOrderUseCase,
    CreateOrderUseCase,
    ProcessPaymentUseCase,
    ShipOrderUseCase,
)
from nexus.domain.exceptions import OrderNotFoundError
from nexus.domain.value_objects import Address, OrderStatus, PaymentMethod


class TestUseCases(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = InMemoryOrderRepository()
        self.factory = PaymentGatewayFactory(enable_resilience=True)
        address = Address("Rua das Rosas", "50", "Campinas", "SP", "13083852")
        self.sample_create_dto = CreateOrderInputDTO(
            customer_email="aluno@puc-campinas.edu.br",
            delivery_address=address,
            items=[
                ItemInputDTO("P1", "Item A", unit_price=100.0, quantity=2, weight_kg=1.0)
            ],
            shipping_strategy_name="CORREIOS_SEDEX",
            origin_cep="13083852",
            discount_percentage=5.0,
        )

    def test_create_order_use_case(self) -> None:
        uc = CreateOrderUseCase(order_repository=self.repo)
        output = uc.execute(self.sample_create_dto)

        self.assertTrue(output.order_id.startswith("ORD-"))
        self.assertEqual(output.status, OrderStatus.PENDING_PAYMENT)
        self.assertEqual(output.items_subtotal, "BRL 200.00")
        self.assertEqual(output.discount, "BRL 10.00")
        self.assertIsNotNone(self.repo.find_by_id(output.order_id))

    def test_process_payment_use_case(self) -> None:
        create_uc = CreateOrderUseCase(order_repository=self.repo)
        order_output = create_uc.execute(self.sample_create_dto)

        pay_uc = ProcessPaymentUseCase(order_repository=self.repo, gateway_factory=self.factory)
        pay_dto = ProcessPaymentInputDTO(
            order_id=order_output.order_id,
            payment_method=PaymentMethod.PIX,
            customer_email=self.sample_create_dto.customer_email,
        )
        pay_output = pay_uc.execute(pay_dto)

        self.assertTrue(pay_output.success)
        self.assertEqual(pay_output.new_status, OrderStatus.PAID)
        self.assertTrue(pay_output.transaction_id.startswith("PIX-"))

        saved = self.repo.find_by_id(order_output.order_id)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.status, OrderStatus.PAID)

    def test_ship_order_use_case(self) -> None:
        create_uc = CreateOrderUseCase(order_repository=self.repo)
        order = create_uc.execute(self.sample_create_dto)

        pay_uc = ProcessPaymentUseCase(order_repository=self.repo, gateway_factory=self.factory)
        pay_uc.execute(
            ProcessPaymentInputDTO(order.order_id, PaymentMethod.PIX, "a@b.com")
        )

        ship_uc = ShipOrderUseCase(order_repository=self.repo)
        shipped = ship_uc.execute(order.order_id, tracking_code="SEDEX-12345")

        self.assertEqual(shipped.status, OrderStatus.SHIPPED)
        self.assertEqual(shipped.tracking_code, "SEDEX-12345")

    def test_cancel_order_use_case(self) -> None:
        create_uc = CreateOrderUseCase(order_repository=self.repo)
        order = create_uc.execute(self.sample_create_dto)

        cancel_uc = CancelOrderUseCase(order_repository=self.repo)
        cancelled = cancel_uc.execute(order.order_id, reason="Cancelamento solicitado pelo usuário")

        self.assertEqual(cancelled.status, OrderStatus.CANCELLED)
        self.assertEqual(cancelled.cancellation_reason, "Cancelamento solicitado pelo usuário")

    def test_process_payment_order_not_found(self) -> None:
        pay_uc = ProcessPaymentUseCase(order_repository=self.repo, gateway_factory=self.factory)
        with self.assertRaises(OrderNotFoundError):
            pay_uc.execute(
                ProcessPaymentInputDTO("ORD-INEXISTENTE", PaymentMethod.PIX, "a@b.com")
            )


if __name__ == "__main__":
    unittest.main()
