"""Adaptador do Gateway de Pagamento Instantâneo Pix.

Implementa RefundablePaymentPort (permite cobrança e estorno imediato via Banco Central).
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


class PixPaymentGateway(RefundablePaymentPort):
    """Adaptador de liquidação instantânea via Arranjo Pix."""

    def __init__(self, simulate_network_failure: bool = False) -> None:
        self.simulate_network_failure = simulate_network_failure

    @property
    def gateway_name(self) -> str:
        return "BacenPixGateway"

    def process_payment(self, request: PaymentRequest) -> PaymentResult:
        if self.simulate_network_failure:
            raise ConnectionError("Timeout de conexão na rede SPI (Banco Central).")

        tx_id = f"PIX-{uuid.uuid4().hex[:12].upper()}"
        return PaymentResult(
            success=True,
            transaction_id=tx_id,
            message="Pagamento Pix compensado instantaneamente com sucesso.",
            authorization_code=f"AUTH-{tx_id[:6]}",
        )

    def process_refund(self, transaction_id: str, amount: Money) -> RefundResult:
        if self.simulate_network_failure:
            raise ConnectionError("Falha na comunicação de estorno com o Bacen.")

        refund_id = f"REF-PIX-{uuid.uuid4().hex[:8].upper()}"
        return RefundResult(
            success=True,
            refund_id=refund_id,
            amount_refunded=amount,
            message="Estorno via Pix creditado na conta de origem.",
        )
