"""Padrão GoF de Criação: Factory Method (Refactoring Guru).

Responsável por instanciar a família de gateways de pagamento e aplicar
as camadas de resiliência (Circuit Breaker / Retry) de forma transparente.
Desacopla a camada de aplicação da instanciação concreta dos adaptadores.
"""

from __future__ import annotations

from nexus.adapters.gateways.boleto import BoletoPaymentGateway
from nexus.adapters.gateways.credit_card import CreditCardPaymentGateway
from nexus.adapters.gateways.pix import PixPaymentGateway
from nexus.domain.ports import PaymentGatewayPort
from nexus.domain.value_objects import PaymentMethod
from nexus.resilience.circuit_breaker import CircuitBreaker
from nexus.resilience.resilient_gateway import ResilientPaymentGateway


class PaymentGatewayFactory:
    """Fábrica de adaptadores de pagamento com suporte a resiliência configurável."""

    def __init__(
        self,
        enable_resilience: bool = True,
        shared_circuit_breaker: CircuitBreaker | None = None,
    ) -> None:
        self.enable_resilience = enable_resilience
        self.shared_circuit_breaker = shared_circuit_breaker

    def create(
        self,
        method: PaymentMethod,
        simulate_network_failure: bool = False,
    ) -> PaymentGatewayPort:
        """Factory Method para criação e enriquecimento do gateway correspondente."""
        raw_gateway: PaymentGatewayPort

        if method == PaymentMethod.PIX:
            raw_gateway = PixPaymentGateway(simulate_network_failure=simulate_network_failure)
        elif method == PaymentMethod.CREDIT_CARD:
            raw_gateway = CreditCardPaymentGateway(simulate_network_failure=simulate_network_failure)
        elif method == PaymentMethod.BOLETO:
            raw_gateway = BoletoPaymentGateway(simulate_network_failure=simulate_network_failure)
        else:
            raise ValueError(f"Método de pagamento não suportado pela fábrica: {method}")

        if self.enable_resilience:
            return ResilientPaymentGateway(
                inner_gateway=raw_gateway,
                circuit_breaker=self.shared_circuit_breaker or CircuitBreaker(),
            )

        return raw_gateway
