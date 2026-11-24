"""Testes dedicados à validação formal dos 5 Princípios SOLID no código do Nexus."""

from decimal import Decimal
import unittest

from nexus.adapters.gateways.boleto import BoletoPaymentGateway
from nexus.adapters.gateways.credit_card import CreditCardPaymentGateway
from nexus.adapters.gateways.pix import PixPaymentGateway
from nexus.adapters.persistence.memory_repo import InMemoryOrderRepository
from nexus.application.dtos import CreateOrderInputDTO, ItemInputDTO
from nexus.application.use_cases import CreateOrderUseCase
from nexus.domain.entities import Order, OrderItem
from nexus.domain.ports import (
    OrderRepositoryPort,
    PaymentGatewayPort,
    PaymentRequest,
    RefundablePaymentPort,
)
from nexus.domain.strategies import ShippingStrategy
from nexus.domain.value_objects import Address, Money, PaymentMethod


class TestSolidPrinciples(unittest.TestCase):
    def test_srp_single_responsibility(self) -> None:
        """SRP: Order calcula totais e protege estados; o repositório cuida da persistência."""
        address = Address("Rua 1", "10", "Campinas", "SP", "13083852")
        items = [OrderItem("P1", "Item", Money.from_float(100.0), 1, 1.0)]
        order = Order("user@puc.br", address, items)

        self.assertEqual(order.items_subtotal.amount, Decimal("100.00"))

        repo = InMemoryOrderRepository()
        repo.save(order)
        retrieved = repo.find_by_id(order.order_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.order_id, order.order_id)

    def test_ocp_open_closed_principle(self) -> None:
        """OCP: Nova estratégia de frete (Drone) é adicionada sem alterar nenhuma linha existente."""

        class DroneShippingStrategy(ShippingStrategy):
            @property
            def name(self) -> str:
                return "DRONE_SUPER_FAST"

            def calculate(self, origin_cep: str, destination_cep: str, total_weight_kg: float) -> Money:
                return Money.from_float(75.00)

            def estimated_delivery_days(self) -> int:
                return 0

        strategy = DroneShippingStrategy()
        cost = strategy.calculate("13083852", "13010000", total_weight_kg=1.0)
        self.assertEqual(cost.amount, Decimal("75.00"))
        self.assertEqual(strategy.estimated_delivery_days(), 0)

    def test_lsp_liskov_substitution_principle(self) -> None:
        """LSP: Qualquer implementação de PaymentGatewayPort pode ser substituída sem quebrar o cliente."""
        gateways: list[PaymentGatewayPort] = [
            PixPaymentGateway(),
            CreditCardPaymentGateway(),
            BoletoPaymentGateway(),
        ]

        req = PaymentRequest(
            order_id="ORD-LSP",
            amount=Money.from_float(50.0),
            method=PaymentMethod.PIX,
            customer_email="lsp@puc.br",
        )

        for gateway in gateways:
            result = gateway.process_payment(req)
            self.assertIsInstance(result.success, bool)
            self.assertTrue(result.success)
            self.assertTrue(len(result.transaction_id) > 0)

    def test_isp_interface_segregation_principle(self) -> None:
        """ISP: Boleto só implementa PaymentGatewayPort; Pix implementa também RefundablePaymentPort."""
        pix_gateway = PixPaymentGateway()
        boleto_gateway = BoletoPaymentGateway()

        self.assertIsInstance(pix_gateway, PaymentGatewayPort)
        self.assertIsInstance(pix_gateway, RefundablePaymentPort)

        self.assertIsInstance(boleto_gateway, PaymentGatewayPort)
        self.assertNotIsInstance(boleto_gateway, RefundablePaymentPort)

    def test_dip_dependency_inversion_principle(self) -> None:
        """DIP: Casos de uso dependem de abstrações (OrderRepositoryPort), não de classes concretas."""

        class MockRepository(OrderRepositoryPort):
            def __init__(self) -> None:
                self.saved_orders: list[Order] = []

            def save(self, order: Order) -> None:
                self.saved_orders.append(order)

            def find_by_id(self, order_id: str) -> Order | None:
                return self.saved_orders[0] if self.saved_orders else None

            def list_all(self) -> list[Order]:
                return self.saved_orders

        mock_repo = MockRepository()
        use_case = CreateOrderUseCase(order_repository=mock_repo)

        address = Address("Rua A", "1", "Campinas", "SP", "13083852")
        dto = CreateOrderInputDTO(
            customer_email="dip@puc.br",
            delivery_address=address,
            items=[ItemInputDTO("P1", "Produto", 50.0, 1, 0.5)],
        )

        output = use_case.execute(dto)
        self.assertEqual(len(mock_repo.saved_orders), 1)
        self.assertEqual(mock_repo.saved_orders[0].order_id, output.order_id)


if __name__ == "__main__":
    unittest.main()
