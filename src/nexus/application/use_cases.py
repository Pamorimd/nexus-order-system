"""Casos de Uso da camada de aplicação do Nexus.

Orquestram os fluxos de negócio sem conter lógica de infraestrutura.
Dependem exclusivamente de abstrações e portas de domínio (DIP e Clean Architecture).
"""

from __future__ import annotations

from decimal import Decimal

from nexus.adapters.gateways.factory import PaymentGatewayFactory
from nexus.application.dtos import (
    CreateOrderInputDTO,
    OrderOutputDTO,
    ProcessPaymentInputDTO,
    ProcessPaymentOutputDTO,
)
from nexus.domain.entities import Order, OrderItem
from nexus.domain.exceptions import OrderNotFoundError, PaymentProcessingError
from nexus.domain.ports import OrderRepositoryPort, PaymentRequest
from nexus.domain.strategies import (
    ExpressTransportadoraShippingStrategy,
    NoDiscountStrategy,
    PacShippingStrategy,
    PercentageDiscountStrategy,
    SedexShippingStrategy,
    ShippingStrategy,
)
from nexus.domain.value_objects import Money


class CreateOrderUseCase:
    """Caso de uso para criação e cálculo preliminar de pedidos com frete e desconto."""

    def __init__(self, order_repository: OrderRepositoryPort) -> None:
        self._order_repository = order_repository
        self._shipping_strategies: dict[str, ShippingStrategy] = {
            "CORREIOS_SEDEX": SedexShippingStrategy(),
            "CORREIOS_PAC": PacShippingStrategy(),
            "TRANSPORTADORA_EXPRESS": ExpressTransportadoraShippingStrategy(),
        }

    def execute(self, input_dto: CreateOrderInputDTO) -> OrderOutputDTO:
        # 1. Converte DTOs em entidades de domínio
        items = [
            OrderItem(
                product_id=item.product_id,
                product_name=item.product_name,
                unit_price=Money.from_float(item.unit_price),
                quantity=item.quantity,
                weight_kg=item.weight_kg,
            )
            for item in input_dto.items
        ]

        # 2. Seleciona e executa a estratégia de frete (GoF Strategy + OCP)
        strategy = self._shipping_strategies.get(
            input_dto.shipping_strategy_name, SedexShippingStrategy()
        )
        total_weight = sum(item.total_weight for item in items)
        shipping_cost = strategy.calculate(
            origin_cep=input_dto.origin_cep,
            destination_cep=input_dto.delivery_address.postal_code,
            total_weight_kg=total_weight,
        )

        # 3. Calcula subtotal e estratégia de desconto
        subtotal = Money.zero()
        for item in items:
            subtotal = subtotal.add(item.subtotal)

        discount_strategy = (
            PercentageDiscountStrategy(Decimal(str(input_dto.discount_percentage)))
            if input_dto.discount_percentage > 0
            else NoDiscountStrategy()
        )
        discount = discount_strategy.apply_discount(subtotal)

        # 4. Instancia e persiste o Agregado
        order = Order(
            customer_email=input_dto.customer_email,
            delivery_address=input_dto.delivery_address,
            items=items,
            shipping_cost=shipping_cost,
            discount=discount,
        )

        self._order_repository.save(order)

        return self._to_output_dto(order)

    def _to_output_dto(self, order: Order) -> OrderOutputDTO:
        return OrderOutputDTO(
            order_id=order.order_id,
            customer_email=order.customer_email,
            status=order.status,
            items_subtotal=str(order.items_subtotal),
            shipping_cost=str(order.shipping_cost),
            discount=str(order.discount),
            final_total=str(order.final_total),
            transaction_id=order.transaction_id,
            tracking_code=order.tracking_code,
            cancellation_reason=order.cancellation_reason,
        )


class ProcessPaymentUseCase:
    """Caso de uso de liquidação financeira com gateway resiliente."""

    def __init__(
        self,
        order_repository: OrderRepositoryPort,
        gateway_factory: PaymentGatewayFactory,
    ) -> None:
        self._order_repository = order_repository
        self._gateway_factory = gateway_factory

    def execute(self, input_dto: ProcessPaymentInputDTO) -> ProcessPaymentOutputDTO:
        # 1. Recupera o pedido do repositório
        order = self._order_repository.find_by_id(input_dto.order_id)
        if not order:
            raise OrderNotFoundError(f"Pedido com ID {input_dto.order_id} não foi encontrado.")

        # 2. Cria o adaptador via Factory Method (GoF Factory Method)
        gateway = self._gateway_factory.create(
            method=input_dto.payment_method,
            simulate_network_failure=input_dto.simulate_failure,
        )

        # 3. Monta a requisição para a porta
        payment_request = PaymentRequest(
            order_id=order.order_id,
            amount=order.final_total,
            method=input_dto.payment_method,
            customer_email=input_dto.customer_email,
        )

        # 4. Executa a cobrança (envolvida por Circuit Breaker e Retry)
        result = gateway.process_payment(payment_request)

        if not result.success:
            raise PaymentProcessingError(f"Falha na cobrança: {result.message}")

        # 5. Executa transição de estado na entidade (GoF State)
        order.pay(transaction_id=result.transaction_id)
        self._order_repository.save(order)

        return ProcessPaymentOutputDTO(
            order_id=order.order_id,
            success=True,
            transaction_id=result.transaction_id,
            message=result.message,
            new_status=order.status,
        )


class ShipOrderUseCase:
    """Caso de uso para expedição logística do pedido."""

    def __init__(self, order_repository: OrderRepositoryPort) -> None:
        self._order_repository = order_repository

    def execute(self, order_id: str, tracking_code: str) -> OrderOutputDTO:
        order = self._order_repository.find_by_id(order_id)
        if not order:
            raise OrderNotFoundError(f"Pedido {order_id} não encontrado.")

        order.ship(tracking_code=tracking_code)
        self._order_repository.save(order)

        return OrderOutputDTO(
            order_id=order.order_id,
            customer_email=order.customer_email,
            status=order.status,
            items_subtotal=str(order.items_subtotal),
            shipping_cost=str(order.shipping_cost),
            discount=str(order.discount),
            final_total=str(order.final_total),
            transaction_id=order.transaction_id,
            tracking_code=order.tracking_code,
            cancellation_reason=order.cancellation_reason,
        )


class CancelOrderUseCase:
    """Caso de uso para cancelamento formal do pedido."""

    def __init__(self, order_repository: OrderRepositoryPort) -> None:
        self._order_repository = order_repository

    def execute(self, order_id: str, reason: str) -> OrderOutputDTO:
        order = self._order_repository.find_by_id(order_id)
        if not order:
            raise OrderNotFoundError(f"Pedido {order_id} não encontrado.")

        order.cancel(reason=reason)
        self._order_repository.save(order)

        return OrderOutputDTO(
            order_id=order.order_id,
            customer_email=order.customer_email,
            status=order.status,
            items_subtotal=str(order.items_subtotal),
            shipping_cost=str(order.shipping_cost),
            discount=str(order.discount),
            final_total=str(order.final_total),
            transaction_id=order.transaction_id,
            tracking_code=order.tracking_code,
            cancellation_reason=order.cancellation_reason,
        )
