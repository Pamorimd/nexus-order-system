"""Padrão Transversal de Resiliência: Timeout (Capítulo 18.4).

Limita o tempo máximo de espera por um serviço externo, para que uma
dependência lenta não prenda o fluxo de checkout.
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from typing import TypeVar

from nexus.domain.exceptions import ExternalCallTimeoutError

T = TypeVar("T")


def execute_with_timeout(action: Callable[[], T], timeout_seconds: float) -> T:
    """Executa a ação e falha com ExternalCallTimeoutError se passar do limite."""
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(action)
    try:
        return future.result(timeout=timeout_seconds)
    except FutureTimeoutError as exc:
        raise ExternalCallTimeoutError(
            f"Serviço externo não respondeu em {timeout_seconds}s."
        ) from exc
    finally:
        # Não espera a thread lenta terminar: o objetivo é liberar o chamador.
        executor.shutdown(wait=False)
