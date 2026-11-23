"""Data Transfer Objects (DTOs) da camada de aplicação.

Isolam a entrada e a saída de dados dos Casos de Uso, garantindo baixo acoplamento
entre a camada de entrega (CLI/HTTP) e o núcleo de domínio.
"""

from __future__ import annotations

from dataclasses import dataclass

from nexus.domain.value_objects import Address, OrderStatus, PaymentMethod


@dataclass(frozen=True)
class ItemInputDTO:
    product_id: str
    product_name: str
    unit_price: float
    quantity: int
    weight_kg: float


@dataclass(frozen=True)
class CreateOrderInputDTO:
    customer_email: str
    delivery_address: Address
    items: list[ItemInputDTO]
    shipping_strategy_name: str = "CORREIOS_SEDEX"
    origin_cep: str = "13083852"  # PUC-Campinas Campus I
    discount_percentage: float = 0.0


@dataclass(frozen=True)
class OrderOutputDTO:
    order_id: str
    customer_email: str
    status: OrderStatus
    items_subtotal: str
    shipping_cost: str
    discount: str
    final_total: str
    transaction_id: str | None
    tracking_code: str | None
    cancellation_reason: str | None


@dataclass(frozen=True)
class ProcessPaymentInputDTO:
    order_id: str
    payment_method: PaymentMethod
    customer_email: str
    simulate_failure: bool = False


@dataclass(frozen=True)
class ProcessPaymentOutputDTO:
    order_id: str
    success: bool
    transaction_id: str | None
    message: str
    new_status: OrderStatus
