"""Testes do Padrão Transversal de Resiliência: Circuit Breaker e Retries."""

import time
import unittest

from nexus.adapters.gateways.pix import PixPaymentGateway
from nexus.domain.exceptions import CircuitBreakerOpenError
from nexus.domain.ports import PaymentRequest
from nexus.domain.value_objects import Money, PaymentMethod
from nexus.resilience.circuit_breaker import CircuitBreaker, CircuitState
from nexus.resilience.resilient_gateway import ResilientPaymentGateway
from nexus.resilience.retry import execute_with_retry


class TestResilienceCircuitBreaker(unittest.TestCase):
    def test_circuit_breaker_transitions(self) -> None:
        cb = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout_seconds=0.2,
            half_open_success_threshold=1,
        )

        # 1. Inicia CLOSED
        self.assertEqual(cb.state, CircuitState.CLOSED)
        cb.before_call()

        # 2. Primeira falha
        cb.record_failure()
        self.assertEqual(cb.state, CircuitState.CLOSED)

        # 3. Segunda falha atinge threshold -> OPEN
        cb.record_failure()
        self.assertEqual(cb.state, CircuitState.OPEN)

        # 4. Chamada com circuito OPEN é barrada com fail-fast
        with self.assertRaises(CircuitBreakerOpenError):
            cb.before_call()

        # 5. Aguarda recuperação de 0.2s
        time.sleep(0.25)
        self.assertEqual(cb.state, CircuitState.HALF_OPEN)

        # 6. Sucesso em HALF_OPEN restaura para CLOSED
        cb.record_success()
        self.assertEqual(cb.state, CircuitState.CLOSED)

    def test_circuit_breaker_reopens_on_half_open_failure(self) -> None:
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout_seconds=0.1)
        cb.record_failure()
        self.assertEqual(cb.state, CircuitState.OPEN)

        time.sleep(0.15)
        self.assertEqual(cb.state, CircuitState.HALF_OPEN)

        # Falha durante teste reabre o circuito imediatamente
        cb.record_failure()
        self.assertEqual(cb.state, CircuitState.OPEN)

    def test_retry_mechanism_eventual_success(self) -> None:
        attempts = 0

        def flaky_operation() -> str:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ConnectionError("Falha de rede temporária")
            return "SUCESSO"

        result = execute_with_retry(
            action=flaky_operation,
            max_attempts=3,
            initial_delay_seconds=0.01,
            backoff_factor=1.5,
        )
        self.assertEqual(result, "SUCESSO")
        self.assertEqual(attempts, 3)

    def test_retry_exhaustion_raises_exception(self) -> None:
        def always_fails() -> str:
            raise TimeoutError("Serviço inalcançável")

        with self.assertRaises(TimeoutError):
            execute_with_retry(
                action=always_fails,
                max_attempts=2,
                initial_delay_seconds=0.01,
            )

    def test_resilient_gateway_integration(self) -> None:
        raw_gateway = PixPaymentGateway(simulate_network_failure=False)
        cb = CircuitBreaker(failure_threshold=2)
        resilient_gateway = ResilientPaymentGateway(inner_gateway=raw_gateway, circuit_breaker=cb)

        req = PaymentRequest("ORD-1", Money.from_float(10.0), PaymentMethod.PIX, "a@b.com")
        result = resilient_gateway.process_payment(req)
        self.assertTrue(result.success)
        self.assertEqual(cb.state, CircuitState.CLOSED)


if __name__ == "__main__":
    unittest.main()
