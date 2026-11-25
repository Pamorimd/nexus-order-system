"""Adaptador do Gateway de Cartão de Crédito.

Implementa RefundablePaymentPort (permite cobrança síncrona com operadora e chargeback/estorno).
"""

from __future__ import annotations

import uuid

from nexus.domain.ports import (
    PaymentRequest,
    PaymentResult,
    RefundablePaymentPort,
    RefundResult,
)
from nexus.domain.value_objects import Money


class CreditCardPaymentGateway(RefundablePaymentPort):
    """Adaptador de adquirente de cartão de crédito (ex: Cielo, Stone, Stripe)."""

    def __init__(self, simulate_network_failure: bool = False) -> None:
        self.simulate_network_failure = simulate_network_failure

    @property
    def gateway_name(self) -> str:
        return "AdquirenteCardGateway"

    def process_payment(self, request: PaymentRequest) -> PaymentResult:
        if self.simulate_network_failure:
            raise ConnectionError(
                "Falha de comunicação com a bandeira do cartão de crédito."
            )

        tx_id = f"CC-{uuid.uuid4().hex[:12].upper()}"
        return PaymentResult(
            success=True,
            transaction_id=tx_id,
            message="Transação de crédito autorizada e capturada pela adquirente.",
            authorization_code=f"AUTH-CC-{uuid.uuid4().hex[:6].upper()}",
        )

    def process_refund(self, transaction_id: str, amount: Money) -> RefundResult:
        if self.simulate_network_failure:
            raise ConnectionError("Falha ao comunicar cancelamento na adquirente.")

        refund_id = f"REF-CC-{uuid.uuid4().hex[:8].upper()}"
        return RefundResult(
            success=True,
            refund_id=refund_id,
            amount_refunded=amount,
            message="Valor estornado na fatura do titular do cartão.",
        )
