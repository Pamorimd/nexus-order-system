"""Entidades centrais do domínio Nexus.

Aplicam o Princípio de Responsabilidade Única (SRP): a entidade Order encapsula
estritamente as invariantes de negócio e orquestra o padrão State.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from nexus.domain.exceptions import EmptyOrderError, InvalidAmountError
from nexus.domain.states import OrderState, PendingPaymentState
from nexus.domain.value_objects import Address, Money, OrderStatus, generate_order_id


@dataclass
class OrderItem:
    """Item individual pertencente a um pedido comercial."""

    product_id: str
    product_name: str
    unit_price: Money
    quantity: int
    weight_kg: float

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise InvalidAmountError("A quantidade do item deve ser maior que zero.")
        if self.weight_kg <= 0:
            raise InvalidAmountError("O peso do item deve ser maior que zero.")

    @property
    def subtotal(self) -> Money:
        """Calcula o valor total do item (preço unitário * quantidade)."""
        return self.unit_price.multiply(self.quantity)

    @property
    def total_weight(self) -> float:
        """Calcula o peso total da linha de itens."""
        return self.weight_kg * self.quantity


class Order:
    """Entidade raiz de agregação do pedido (Aggregate Root).

    Garante invariantes de cálculo e ciclo de vida através do padrão State.
    """

    def __init__(
        self,
        customer_email: str,
        delivery_address: Address,
        items: list[OrderItem],
        order_id: str | None = None,
        shipping_cost: Money | None = None,
        discount: Money | None = None,
        initial_state: OrderState | None = None,
    ) -> None:
        if not items:
            raise EmptyOrderError("Não é permitido criar um pedido sem itens.")

        self.order_id: str = order_id or generate_order_id()
        self.customer_email: str = customer_email
        self.delivery_address: Address = delivery_address
        self.items: list[OrderItem] = list(items)
        self.shipping_cost: Money = shipping_cost or Money.zero()
        self.discount: Money = discount or Money.zero()

        # Atributos de transição de estado
        self.transaction_id: str | None = None
        self.tracking_code: str | None = None
        self.cancellation_reason: str | None = None
        self.created_at: datetime = datetime.now(timezone.utc)

        # GoF State Pattern: Inicializa o estado (padrão: PendingPaymentState)
        self._state: OrderState = initial_state or PendingPaymentState()

    @property
    def state(self) -> OrderState:
        """Acesso somente leitura ao objeto de estado."""
        return self._state

    @property
    def status(self) -> OrderStatus:
        """Consulta o status atual por meio do padrão State."""
        return self._state.get_status()

    def set_state(self, new_state: OrderState) -> None:
        """Altera internamente o estado do pedido."""
        self._state = new_state

    # --- Transições de ciclo de vida delegadas ao State ---

    def pay(self, transaction_id: str) -> None:
        """Liquida financeiramente o pedido."""
        self._state.pay(self, transaction_id)

    def ship(self, tracking_code: str) -> None:
        """Despacha o pedido para entrega."""
        self._state.ship(self, tracking_code)

    def cancel(self, reason: str) -> None:
        """Cancela o pedido."""
        self._state.cancel(self, reason)

    # --- Cálculos financeiros do Agregado ---

    @property
    def items_subtotal(self) -> Money:
        """Calcula a soma de todos os subtotais dos itens."""
        total = Money.zero()
        for item in self.items:
            total = total.add(item.subtotal)
        return total

    @property
    def total_weight_kg(self) -> float:
        """Calcula o peso total da remessa."""
        return sum(item.total_weight for item in self.items)

    @property
    def final_total(self) -> Money:
        """Calcula o montante final líquido: (itens + frete) - desconto."""
        gross = self.items_subtotal.add(self.shipping_cost)
        if self.discount.amount > gross.amount:
            return Money.zero()
        return gross.subtract(self.discount)
