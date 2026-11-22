"""Testes do Padrão GoF: Factory Method (PaymentGatewayFactory)."""

import unittest

from nexus.adapters.gateways.factory import PaymentGatewayFactory
from nexus.domain.ports import PaymentGatewayPort, PaymentRequest
from nexus.domain.value_objects import Money, PaymentMethod
from nexus.resilience.resilient_gateway import ResilientPaymentGateway


class TestGofFactory(unittest.TestCase):
    def test_factory_creates_pix_gateway(self) -> None:
        factory = PaymentGatewayFactory(enable_resilience=False)
        gateway = factory.create(PaymentMethod.PIX)
        self.assertIsInstance(gateway, PaymentGatewayPort)
        self.assertEqual(gateway.gateway_name, "BacenPixGateway")

    def test_factory_creates_credit_card_gateway(self) -> None:
        factory = PaymentGatewayFactory(enable_resilience=False)
        gateway = factory.create(PaymentMethod.CREDIT_CARD)
        self.assertIsInstance(gateway, PaymentGatewayPort)
        self.assertEqual(gateway.gateway_name, "AdquirenteCardGateway")

    def test_factory_creates_boleto_gateway(self) -> None:
        factory = PaymentGatewayFactory(enable_resilience=False)
        gateway = factory.create(PaymentMethod.BOLETO)
        self.assertIsInstance(gateway, PaymentGatewayPort)
        self.assertEqual(gateway.gateway_name, "CIPBoletoRegistradoGateway")

    def test_factory_decorates_with_resilience_by_default(self) -> None:
        factory = PaymentGatewayFactory(enable_resilience=True)
        gateway = factory.create(PaymentMethod.PIX)
        self.assertIsInstance(gateway, ResilientPaymentGateway)
        self.assertIn("Resilient", gateway.gateway_name)

    def test_factory_created_gateway_processes_payment(self) -> None:
        factory = PaymentGatewayFactory(enable_resilience=True)
        gateway = factory.create(PaymentMethod.PIX)

        req = PaymentRequest(
            order_id="ORD-123",
            amount=Money.from_float(100.0),
            method=PaymentMethod.PIX,
            customer_email="aluno@puc.br",
        )
        result = gateway.process_payment(req)
        self.assertTrue(result.success)
        self.assertTrue(result.transaction_id.startswith("PIX-"))


if __name__ == "__main__":
    unittest.main()
