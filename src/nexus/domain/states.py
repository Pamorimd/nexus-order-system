"""Padrão GoF Comportamental: State (Refactoring Guru).

Encapsula os estados do ciclo de vida do pedido e suas transições válidas,
eliminando condicionais complexas ('Switch Statements' / code smell) da entidade Order.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from nexus.domain.exceptions import InvalidStateTransitionError
from nexus.domain.value_objects import OrderStatus

if TYPE_CHECKING:
    from nexus.domain.entities import Order


class OrderState(ABC):
    """Interface abstrata do estado do pedido (GoF State)."""

    @abstractmethod
    def get_status(self) -> OrderStatus:
        """Retorna o identificador enum do estado."""

    @abstractmethod
    def pay(self, order: Order, transaction_id: str) -> None:
        """Processa a transição para o estado de pago."""

    @abstractmethod
    def ship(self, order: Order, tracking_code: str) -> None:
        """Processa a transição para o estado de despachado."""

    @abstractmethod
    def cancel(self, order: Order, reason: str) -> None:
        """Processa o cancelamento do pedido."""


class PendingPaymentState(OrderState):
    """Estado inicial: aguardando confirmação do pagamento."""

    def get_status(self) -> OrderStatus:
        return OrderStatus.PENDING_PAYMENT

    def pay(self, order: Order, transaction_id: str) -> None:
        order.transaction_id = transaction_id
        order.set_state(PaidState())

    def ship(self, order: Order, tracking_code: str) -> None:
        raise InvalidStateTransitionError(
            "Regra violada: Impossível despachar um pedido que ainda não foi pago."
        )

    def cancel(self, order: Order, reason: str) -> None:
        order.cancellation_reason = reason
        order.set_state(CancelledState())


class PaidState(OrderState):
    """Estado em que o pagamento foi compensado e o pedido aguarda despacho."""

    def get_status(self) -> OrderStatus:
        return OrderStatus.PAID

    def pay(self, order: Order, transaction_id: str) -> None:
        raise InvalidStateTransitionError(
            "Regra violada: Este pedido já foi pago anteriormente."
        )

    def ship(self, order: Order, tracking_code: str) -> None:
        order.tracking_code = tracking_code
        order.set_state(ShippedState())

    def cancel(self, order: Order, reason: str) -> None:
        order.cancellation_reason = reason
        order.set_state(CancelledState())


class ShippedState(OrderState):
    """Estado em que os produtos foram despachados para a transportadora."""

    def get_status(self) -> OrderStatus:
        return OrderStatus.SHIPPED

    def pay(self, order: Order, transaction_id: str) -> None:
        raise InvalidStateTransitionError(
            "Regra violada: Pedido já despachado; liquidação já ocorrida."
        )

    def ship(self, order: Order, tracking_code: str) -> None:
        raise InvalidStateTransitionError(
            "Regra violada: Pedido já se encontra em transporte."
        )

    def cancel(self, order: Order, reason: str) -> None:
        raise InvalidStateTransitionError(
            "Regra violada: Não é permitido cancelamento direto de pedido já despachado."
        )


class CancelledState(OrderState):
    """Estado terminal de cancelamento do pedido."""

    def get_status(self) -> OrderStatus:
        return OrderStatus.CANCELLED

    def pay(self, order: Order, transaction_id: str) -> None:
        raise InvalidStateTransitionError(
            "Regra violada: Não é possível pagar um pedido previamente cancelado."
        )

    def ship(self, order: Order, tracking_code: str) -> None:
        raise InvalidStateTransitionError(
            "Regra violada: Não é possível despachar um pedido cancelado."
        )

    def cancel(self, order: Order, reason: str) -> None:
        raise InvalidStateTransitionError(
            "Regra violada: O pedido já se encontra cancelado."
        )
