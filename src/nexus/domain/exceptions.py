"""Exceções explícitas de domínio do sistema Nexus.

Seguindo os princípios de Clean Code, erros de domínio são representados por
tipos específicos em vez de exceções genéricas ou códigos de status numéricos.
"""


class DomainError(Exception):
    """Exceção base para todos os erros de negócio do domínio."""


class InvalidAmountError(DomainError):
    """Lançada quando um valor monetário for negativo ou inválido."""


class CurrencyMismatchError(DomainError):
    """Lançada ao tentar operar moedas distintas sem conversão explícita."""


class EmptyOrderError(DomainError):
    """Lançada ao tentar criar um pedido sem nenhum item."""


class OrderNotFoundError(DomainError):
    """Lançada quando um pedido solicitado não for localizado no repositório."""


class InvalidStateTransitionError(DomainError):
    """Lançada ao tentar realizar uma transição ilegal no ciclo de vida do pedido."""


class PaymentProcessingError(DomainError):
    """Lançada quando o processamento de pagamento falha de forma definitiva."""


class CircuitBreakerOpenError(DomainError):
    """Lançada quando uma chamada a serviço externo é bloqueada pelo Circuit Breaker."""


class ShippingCalculationError(DomainError):
    """Lançada quando o cálculo de frete não pode ser concluído para a rota."""
