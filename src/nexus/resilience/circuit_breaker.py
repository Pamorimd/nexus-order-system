"""Padrão Transversal de Resiliência: Circuit Breaker (Capítulo 18.4).

Impede falhas em cascata e degradação de recursos quando serviços externos
(gateways de pagamento, serviços de frete) estiverem instáveis ou fora do ar.
"""

from __future__ import annotations

import time
from enum import Enum

from nexus.domain.exceptions import CircuitBreakerOpenError


class CircuitState(str, Enum):
    """Estados operacionais do Circuit Breaker."""

    CLOSED = "CLOSED"  # Operação normal: requisições passam
    OPEN = "OPEN"  # Circuito aberto: falhas repetidas; fail-fast imediato
    HALF_OPEN = (
        "HALF_OPEN"  # Teste de recuperação: permite número controlado de tentativas
    )


class CircuitBreaker:
    """Implementação do padrão Circuit Breaker com fail-fast e recuperação automática."""

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout_seconds: float = 10.0,
        half_open_success_threshold: int = 2,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.half_open_success_threshold = half_open_success_threshold

        self._state: CircuitState = CircuitState.CLOSED
        self._consecutive_failures: int = 0
        self._consecutive_successes: int = 0
        self._last_state_change: float = time.time()

    @property
    def state(self) -> CircuitState:
        """Verifica o estado atual considerando a expiração da janela de recuperação."""
        now = time.time()
        if (
            self._state == CircuitState.OPEN
            and (now - self._last_state_change) >= self.recovery_timeout_seconds
        ):
            self._transition_to(CircuitState.HALF_OPEN)
        return self._state

    def before_call(self) -> None:
        """Valida se a chamada externa pode ser executada ou deve falhar imediatamente."""
        current_state = self.state
        if current_state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                f"Circuito ABERTO: Serviço externo indisponível temporariamente "
                f"(aguardando recuperação de {self.recovery_timeout_seconds}s)."
            )

    def record_success(self) -> None:
        """Registra execução bem-sucedida da chamada externa."""
        current_state = self.state
        if current_state == CircuitState.HALF_OPEN:
            self._consecutive_successes += 1
            if self._consecutive_successes >= self.half_open_success_threshold:
                self._transition_to(CircuitState.CLOSED)
        elif current_state == CircuitState.CLOSED:
            self._consecutive_failures = 0

    def record_failure(self) -> None:
        """Registra falha de comunicação ou exceção no serviço externo."""
        self._consecutive_failures += 1
        current_state = self.state

        if current_state == CircuitState.HALF_OPEN:
            # Qualquer falha durante recuperação reabre imediatamente o circuito
            self._transition_to(CircuitState.OPEN)
        elif (
            current_state == CircuitState.CLOSED
            and self._consecutive_failures >= self.failure_threshold
        ):
            self._transition_to(CircuitState.OPEN)

    def _transition_to(self, new_state: CircuitState) -> None:
        self._state = new_state
        self._last_state_change = time.time()
        if new_state == CircuitState.CLOSED:
            self._consecutive_failures = 0
            self._consecutive_successes = 0
        elif new_state == CircuitState.OPEN or new_state == CircuitState.HALF_OPEN:
            self._consecutive_successes = 0
