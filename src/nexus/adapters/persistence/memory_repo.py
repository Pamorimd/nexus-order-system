"""Adaptador de persistência em memória (In-Memory Repository).

Implementa a porta OrderRepositoryPort (Arquitetura Hexagonal e DIP).
"""

from __future__ import annotations

from nexus.domain.entities import Order
from nexus.domain.ports import OrderRepositoryPort


class InMemoryOrderRepository(OrderRepositoryPort):
    """Repositório thread-safe em memória para armazenar e consultar pedidos."""

    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}

    def save(self, order: Order) -> None:
        self._orders[order.order_id] = order

    def find_by_id(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)

    def list_all(self) -> list[Order]:
        return list(self._orders.values())

    def clear(self) -> None:
        """Limpa o repositório (útil para suíte de testes)."""
        self._orders.clear()
