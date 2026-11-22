"""Adaptador do Gateway de Boleto Bancário Registrado.

Implementa estritamente PaymentGatewayPort (não implementa RefundablePaymentPort).
Demonstração prática do Princípio da Segregação de Interfaces (ISP do SOLID):
o boleto bancário é um título de cobrança que não suporta estorno programático síncrono.
"""

from __future__ import annotations

import uuid

from nexus.domain.ports import PaymentGatewayPort, PaymentRequest, PaymentResult


class BoletoPaymentGateway(PaymentGatewayPort):
    """Adaptador para emissão e registro de boletos bancários."""

    def __init__(self, simulate_network_failure: bool = False) -> None:
        self.simulate_network_failure = simulate_network_failure

    @property
    def gateway_name(self) -> str:
        return "CIPBoletoRegistradoGateway"

    def process_payment(self, request: PaymentRequest) -> PaymentResult:
        if self.simulate_network_failure:
            raise ConnectionError("Falha na CIP/Febraban ao registrar o título bancário.")

        tx_id = f"BOL-{uuid.uuid4().hex[:12].upper()}"
        linha_digitavel = f"34191.79001 01043.510047 91020.150008 1 {uuid.uuid4().int % 10000000000:010d}"

        return PaymentResult(
            success=True,
            transaction_id=tx_id,
            message=f"Boleto registrado com sucesso. Linha digitável: {linha_digitavel}",
            authorization_code=f"CIP-{tx_id[:8]}",
        )
