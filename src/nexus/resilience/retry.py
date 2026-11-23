"""Padrão Transversal de Resiliência: Retry com Exponential Backoff (Capítulo 18.4).

Trata falhas transitórias de rede sem sobrecarregar o serviço de destino.
"""

from __future__ import annotations

from collections.abc import Callable
import time
from typing import TypeVar

from nexus.domain.exceptions import DomainError

T = TypeVar("T")


def execute_with_retry(
    action: Callable[[], T],
    max_attempts: int = 3,
    initial_delay_seconds: float = 0.05,
    backoff_factor: float = 2.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    """Executa uma ação com repetições e recuo exponencial em caso de falha transitória."""
    attempt = 0
    delay = initial_delay_seconds

    while attempt < max_attempts:
        try:
            return action()
        except retryable_exceptions as exc:
            attempt += 1
            if attempt >= max_attempts:
                # Esgotou as tentativas permitidas
                raise exc

            # Se for uma exceção de domínio fatal ou intencional, não deve retentar
            if isinstance(exc, DomainError) and not getattr(exc, "is_transient", False):
                raise exc

            time.sleep(delay)
            delay *= backoff_factor

    raise RuntimeError("Falha inesperada no laço de retry.")
