# 7. Padrão Transversal: Resiliência

## 7.1. Problema

O Nexus Order System depende de serviços externos para processar pagamentos. Essas dependências podem apresentar lentidão, falhas temporárias de rede ou indisponibilidade.

Sem mecanismos de proteção, uma chamada demorada pode atrasar o fluxo de processamento de pedidos, enquanto falhas repetidas podem consumir recursos e comprometer a disponibilidade do sistema.

## 7.2. Decisão

Foi adotado o padrão transversal de **Resiliência**. A implementação combina três mecanismos:

- **Timeout:** estabelece um limite de espera para chamadas externas. Quando o limite é excedido, é lançada a exceção `ExternalCallTimeoutError`.
- **Retry com Exponential Backoff:** repete operações que falharam por motivos transitórios, aumentando progressivamente o intervalo entre as tentativas. Exceções de domínio não transitórias não são repetidas.
- **Circuit Breaker:** monitora falhas consecutivas e interrompe temporariamente novas chamadas quando o limite é atingido. Opera em três estados: `CLOSED`, `OPEN` e `HALF_OPEN`.

A integração é realizada por `ResilientPaymentGateway`, que envolve uma implementação de `PaymentGatewayPort` e aplica os mecanismos sem exigir alterações no gateway concreto.

## 7.3. Implementação no código

A implementação foi dividida em componentes com responsabilidades específicas:

| Responsabilidade | Arquivo | Evidência no código |
|---|---|---|
| Controle dos estados e transições do circuito | [circuit_breaker.py](https://github.com/Pamorimd/nexus-order-system/blob/f9384ab/src/nexus/resilience/circuit_breaker.py) | `CircuitBreaker`, `CircuitState` e `before_call()` |
| Repetição de operações | [retry.py](https://github.com/Pamorimd/nexus-order-system/blob/f9384ab/src/nexus/resilience/retry.py) | `execute_with_retry()` |
| Limite de espera | [timeout.py](https://github.com/Pamorimd/nexus-order-system/blob/f9384ab/src/nexus/resilience/timeout.py) | `execute_with_timeout()` |
| Integração dos mecanismos com pagamentos | [resilient_gateway.py](https://github.com/Pamorimd/nexus-order-system/blob/f9384ab/src/nexus/resilience/resilient_gateway.py) | `ResilientPaymentGateway` |

### Circuit Breaker

O Circuit Breaker controla a disponibilidade das chamadas externas. Quando o número de falhas atinge o limite configurado, o circuito passa para `OPEN` e bloqueia novas chamadas. Após o período de recuperação, passa para `HALF_OPEN`, permitindo verificar se o serviço voltou a funcionar.

Os três estados possuem as seguintes responsabilidades:

- `CLOSED`: permite chamadas normalmente e contabiliza falhas consecutivas.
- `OPEN`: bloqueia novas chamadas enquanto o serviço está temporariamente indisponível.
- `HALF_OPEN`: permite chamadas de verificação para avaliar a recuperação do serviço.

A implementação das transições e da verificação antes das chamadas está em [circuit_breaker.py](https://github.com/Pamorimd/nexus-order-system/blob/f9384ab/src/nexus/resilience/circuit_breaker.py).

### Retry com Exponential Backoff

O mecanismo Retry repete a operação quando ocorre uma exceção elegível, respeitando o número máximo de tentativas. O intervalo entre as tentativas aumenta de acordo com o fator de backoff configurado.

São consideradas elegíveis, por padrão, falhas de conexão, timeout e `ExternalCallTimeoutError`. Exceções de domínio não transitórias não são repetidas.

O mecanismo está implementado em [retry.py](https://github.com/Pamorimd/nexus-order-system/blob/f9384ab/src/nexus/resilience/retry.py).

### Timeout

O Timeout limita o tempo que o fluxo chamador aguarda pela resposta de uma operação externa. A implementação utiliza `ThreadPoolExecutor` e `future.result(timeout=...)` para estabelecer esse limite.

Quando o tempo configurado é excedido, é lançada `ExternalCallTimeoutError`, permitindo que o mecanismo Retry trate a falha conforme suas regras.

A implementação está em [timeout.py](https://github.com/Pamorimd/nexus-order-system/blob/f9384ab/src/nexus/resilience/timeout.py).

**Limitação:** o timeout interrompe a espera do chamador, mas não garante o encerramento da operação que já está em execução na thread. Essa limitação decorre do funcionamento das threads em Python.

### Integração com o gateway de pagamento

A classe `ResilientPaymentGateway` atua como um invólucro para o gateway concreto. Ela coordena o Circuit Breaker, o Retry e o Timeout durante as operações de pagamento e reembolso.

Dessa forma, as proteções ficam concentradas em um componente, evitando que cada gateway concreto precise implementar individualmente os mecanismos de resiliência.

A integração está implementada em [resilient_gateway.py](https://github.com/Pamorimd/nexus-order-system/blob/f9384ab/src/nexus/resilience/resilient_gateway.py).

## 7.4. Testes

Os mecanismos foram validados por testes automatizados em [test_resilience_circuit_breaker.py](https://github.com/Pamorimd/nexus-order-system/blob/f9384ab/tests/test_resilience_circuit_breaker.py).

Os testes específicos de resiliência verificam:

- Transição do Circuit Breaker entre `CLOSED`, `OPEN` e `HALF_OPEN`.
- Reabertura do circuito quando ocorre falha durante a recuperação.
- Sucesso de uma operação após novas tentativas.
- Esgotamento do número máximo de tentativas.
- Integração dos mecanismos com um gateway de pagamento.
- Lançamento da exceção quando o tempo limite é excedido.
- Retorno rápido de uma chamada que ultrapassa o timeout.
- Abertura do circuito após falhas de um gateway lento.
- Comportamento de fail-fast para chamadas com o circuito aberto.

**Validação geral:** a suíte completa foi executada com `python3 -m pytest -v`, resultando em **26 testes aprovados**.

## 7.5. Benefícios e trade-offs

**Benefícios:**

- Reduz o tempo de espera do fluxo chamador em operações externas demoradas.
- Permite novas tentativas diante de falhas transitórias.
- Evita chamadas repetidas a serviços que apresentam falhas consecutivas.
- Centraliza os mecanismos de proteção em um componente reutilizável.
- Mantém os gateways concretos separados das responsabilidades de resiliência.

**Trade-offs e limitações:**

- As novas tentativas aumentam o tempo total de execução quando ocorrem falhas.
- O Circuit Breaker pode bloquear temporariamente chamadas mesmo quando o serviço externo já voltou a funcionar, até que ocorra a verificação de recuperação.
- O Timeout não garante o cancelamento de uma operação que já esteja em execução.
- O uso de threads e mecanismos de espera acrescenta complexidade à implementação.

## 7.6. Justificativa

A adoção da resiliência atende à necessidade de proteger o sistema contra falhas e lentidão de serviços externos, especialmente no processamento de pagamentos.

A combinação de Timeout, Retry com Exponential Backoff e Circuit Breaker permite tratar diferentes situações de falha de maneira específica. A utilização de `ResilientPaymentGateway` mantém essas responsabilidades concentradas e separadas das implementações concretas dos gateways.

A solução também permite testar os mecanismos individualmente e em conjunto, demonstrando sua aplicação no código e sua contribuição para a disponibilidade e a tolerância a falhas do sistema.
