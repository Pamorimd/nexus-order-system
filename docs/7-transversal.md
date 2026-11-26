# 7. Padrão Transversal: Resiliência

## 7.1. Problema

O Nexus Order System depende de serviços externos para processar pagamentos. Essas dependências podem apresentar lentidão, falhas temporárias de rede ou indisponibilidade.

Sem mecanismos de proteção, uma chamada demorada pode atrasar o fluxo de processamento de pedidos, enquanto falhas repetidas podem consumir recursos e comprometer a disponibilidade do sistema.

## 7.2. Decisão

Foi adotado o padrão transversal de **Resiliência**, conforme o capítulo 18.4 do livro da disciplina. A implementação combina três mecanismos:

- **Timeout:** estabelece um limite de espera para chamadas externas. Quando o limite é excedido, é lançada a exceção `ExternalCallTimeoutError`.
- **Retry com Exponential Backoff:** repete operações que falharam por motivos transitórios, aumentando progressivamente o intervalo entre as tentativas. Exceções de domínio não transitórias não são repetidas.
- **Circuit Breaker:** monitora falhas consecutivas e interrompe temporariamente novas chamadas quando o limite é atingido. Opera em três estados: `CLOSED`, `OPEN` e `HALF_OPEN`.

A integração é realizada por `ResilientPaymentGateway`, que envolve uma implementação de `PaymentGatewayPort` e aplica os mecanismos sem exigir alterações no gateway concreto.

## 7.3. Implementação no código

A implementação foi dividida em componentes com responsabilidades específicas:

| Responsabilidade | Arquivo | Evidência no código |
|---|---|---|
| Controle dos estados e transições do circuito | [`circuit_breaker.py`](https://github.com/Pamorimd/nexus-order-system/blob/f9384ab/src/nexus/resilience/circuit_breaker.py#L30-L76) | `CircuitBreaker`, `CircuitState` e `before_call()` |
| Repetição de operações | [`retry.py`](https://github.com/Pamorimd/nexus-order-system/blob/f9384ab/src/nexus/resilience/retry.py#L229-L260) | `execute_with_retry()` |
| Limite de espera | [`timeout.py`](https://github.com/Pamorimd/nexus-order-system/blob/f9384ab/src/nexus/resilience/timeout.py#L285-L298) | `execute_with_timeout()` |
| Integração dos mecanismos com pagamentos | [`resilient_gateway.py`](https://github.com/Pamorimd/nexus-order-system/blob/f9384ab/src/nexus/resilience/resilient_gateway.py#L136-L184) | `ResilientPaymentGateway` |

### Circuit Breaker

O Circuit Breaker controla a disponibilidade das chamadas externas. Quando o número de falhas atinge o limite configurado, o circuito passa para `OPEN` e bloqueia novas chamadas. Após o período de recuperação, passa para `HALF_OPEN`, permitindo verificar se o serviço voltou a funcionar.

Trecho de `before_call()`:

```python
def before_call(self) -> None:
    current_state = self.state
    if current_state == CircuitState.OPEN:
        raise CircuitBreakerOpenError(
            f"Circuito ABERTO: Serviço externo indisponível temporariamente "
            f"(aguardando recuperação de {self.recovery_timeout_seconds}s)."
        )
```

A implementação das transições pode ser consultada em [`circuit_breaker.py`](https://github.com/Pamorimd/nexus-order-system/blob/f9384ab/src/nexus/resilience/circuit_breaker.py#L102-L110).

### Retry com Exponential Backoff

O mecanismo Retry repete a operação quando ocorre uma exceção elegível, respeitando o número máximo de tentativas. O intervalo entre as tentativas aumenta de acordo com o fator de backoff configurado.

São consideradas elegíveis, por padrão, falhas de conexão, timeout e `ExternalCallTimeoutError`.

Trecho de `execute_with_retry()`:

```python
while attempt < max_attempts:
    try:
        return