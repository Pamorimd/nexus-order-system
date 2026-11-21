"""Portas abstratas da Arquitetura Hexagonal (Ports & Adapters).

Definem contratos puros do domínio sem acoplamento com bibliotecas externas,
bancos de dados ou SDKs de terceiros.
Aplica ISP (Interface Segregation Principle) e DIP (Dependency Inversion Principle).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from nexus.domain.value_objects import Money, PaymentMethod

if TYPE_CHECKING:
    from nexus.domain.entities import Order


@dataclass(frozen=True)
class PaymentRequest:
    """Dados de entrada normalizados para processamento de pagamento."""

    order_id: str
    amount: Money
    method: PaymentMethod
    customer_email: str
    metadata: dict[str, str] | None = None


@dataclass(frozen=True)
class PaymentResult:
    """Resultado emitido pelo gateway de pagamento."""

    success: bool
    transaction_id: str
    message: str
    authorization_code: str | None = None


@dataclass(frozen=True)
class RefundResult:
    """Resultado de estorno emitido pelo gateway."""

    success: bool
    refund_id: str
    amount_refunded: Money
    message: str


class OrderRepositoryPort(ABC):
    """Porta de saída para persistência e recuperação de pedidos."""

    @abstractmethod
    def save(self, order: Order) -> None:
        """Salva ou atualiza o pedido no armazenamento."""

    @abstractmethod
    def find_by_id(self, order_id: str) -> Order | None:
        """Localiza um pedido pelo identificador único."""

    @abstractmethod
    def list_all(self) -> list[Order]:
        """Retorna todos os pedidos registrados."""


class PaymentGatewayPort(ABC):
    """Porta de saída essencial para cobrança financeira.

    Segregada de operações de estorno (ISP).
    """

    @abstractmethod
    def process_payment(self, request: PaymentRequest) -> PaymentResult:
        """Executa a liquidação da transação no gateway remoto."""

    @property
    @abstractmethod
    def gateway_name(self) -> str:
        """Identificador textual do provedor de pagamento."""


class RefundablePaymentPort(PaymentGatewayPort):
    """Porta especializada para gateways que suportam estorno imediato (ISP).

    Nem todo gateway (ex: boleto bancário offline) suporta estorno programático síncrono.
    """

    @abstractmethod
    def process_refund(self, transaction_id: str, amount: Money) -> RefundResult:
        """Executa o estorno total ou parcial de uma transação prévia."""


class ShippingCalculatorPort(ABC):
    """Porta de saída para cálculo de frete por operadoras logísticas."""

    @abstractmethod
    def calculate_shipping(
        self, origin_cep: str, destination_cep: str, weight_kg: float
    ) -> Money:
        """Calcula o custo monetário da entrega para o trecho e peso."""

    @abstractmethod
    def estimate_days(self, origin_cep: str, destination_cep: str) -> int:
        """Estima o prazo de entrega em dias úteis."""
