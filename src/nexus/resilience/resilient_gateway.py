"""Adaptador Resiliente que envolve PaymentGatewayPort (Decorator / Proxy).

Combina Circuit Breaker e Retry com Exponential Backoff (Capítulo 18.4 do livro).
"""

from __future__ import annotations

from nexus.domain.ports import (
    PaymentGatewayPort,
    PaymentRequest,
    PaymentResult,
    RefundablePaymentPort,
    RefundResult,
)
from nexus.domain.value_objects import Money
from nexus.resilience.circuit_breaker import CircuitBreaker
from nexus.resilience.retry import execute_with_retry
from nexus.resilience.timeout import execute_with_timeout


class ResilientPaymentGateway(RefundablePaymentPort):
    """Envolve qualquer PaymentGatewayPort com resiliência a falhas de rede e timeouts."""

    def __init__(
        self,
        inner_gateway: PaymentGatewayPort,
        circuit_breaker: CircuitBreaker | None = None,
        max_attempts: int = 3,
        timeout_seconds: float = 5.0,
    ) -> None:
        self._inner_gateway = inner_gateway
        self._circuit_breaker = circuit_breaker or CircuitBreaker()
        self._max_attempts = max_attempts
        self._timeout_seconds = timeout_seconds

    @property
    def circuit_breaker(self) -> CircuitBreaker:
        return self._circuit_breaker

    @property
    def gateway_name(self) -> str:
        return f"Resilient({self._inner_gateway.gateway_name})"

    def process_payment(self, request: PaymentRequest) -> PaymentResult:
        # 1. Verifica estado do circuito (fail-fast imediato se estiver ABERTO)
        self._circuit_breaker.before_call()

        try:
            # 2. Cada tentativa tem timeout; falhas transitórias entram em retry com backoff
            result = execute_with_retry(
                action=lambda: execute_with_timeout(
                    lambda: self._inner_gateway.process_payment(request),
                    self._timeout_seconds,
                ),
                max_attempts=self._max_attempts,
                initial_delay_seconds=0.02,
                backoff_factor=1.5,
            )

            if result.success:
                self._circuit_breaker.record_success()
            else:
                self._circuit_breaker.record_failure()

            return result

        except Exception as exc:
            self._circuit_breaker.record_failure()
            raise exc

    def process_refund(self, transaction_id: str, amount: Money) -> RefundResult:
        self._circuit_breaker.before_call()

        if not isinstance(self._inner_gateway, RefundablePaymentPort):
            raise NotImplementedError(
                f"O gateway {self._inner_gateway.gateway_name} não suporta operações de estorno."
            )

        try:
            refund_result = execute_with_retry(
                action=lambda: execute_with_timeout(
                    lambda: self._inner_gateway.process_refund(transaction_id, amount),
                    self._timeout_seconds,
                ),
                max_attempts=self._max_attempts,
            )
            self._circuit_breaker.record_success()
            return refund_result
        except Exception as exc:
            self._circuit_breaker.record_failure()
            raise exc
