# ADR 0006: Aplicação do Padrão Transversal de Resiliência (Circuit Breaker e Retries) nos Gateways Externos

## Status
Aceito (Substitui o [ADR-0005](0005-integracao-sincrona-gateway-pagamento.md))

## Contexto
Conforme observado na vigência do ADR-0005, chamadas síncronas sem proteção a serviços externos de pagamentos expõem o sistema a indisponibilidades, picos de latência e esgotamento de conexões. O Capítulo 18.4 do livro da disciplina prescreve padrões transversais de resiliência: *Timeout*, *Retry* (com recuo exponencial) e *Circuit Breaker* para evitar falhas em cascata e degradação sistêmica.

## Decisão
Substituímos a abordagem síncrona ingênua do ADR-0005 pela implementação do **Padrão Transversal de Resiliência (Capítulo 18.4)**:
1. Criamos a classe `CircuitBreaker` com máquina de estados finitos (`CLOSED`, `OPEN`, `HALF_OPEN`), limiar de falhas configurável (`failure_threshold = 2`) e janela de recuperação temporizada (`recovery_timeout_seconds = 1.5s`).
2. Criamos o utilitário `execute_with_retry` aplicando algoritmo de repetições com recuo exponencial (*exponential backoff*).
3. Implementamos o decorador `ResilientPaymentGateway` que envolve qualquer implementação de `PaymentGatewayPort` (e `RefundablePaymentPort`), aplicando Circuit Breaker e Retry de forma transparente para a camada de aplicação.

## Alternativas Consideradas e Motivos de Descarte
1. **Tratamento ad-hoc de `try/except` dentro do Caso de Uso:**
   * *Motivo do descarte:* Poluiria os casos de uso com lógica de infraestrutura e rede, violando o SRP e o princípio de separação de interesses da Arquitetura Hexagonal.
2. **Biblioteca Externa Pesada (ex: PyBreaker ou Tenacity):**
   * *Motivo do descarte:* A implementação direta e orientada a objetos no pacote `nexus.resilience` garante zero dependências externas no código de produção e clareza didática para auditoria do professor.

## Consequências
### Positivas
* **Fail-Fast Protetivo:** Quando o gateway externo falha repetidamente, o circuito abre e as chamadas subsequentes são rejeitadas instantaneamente com `CircuitBreakerOpenError`, sem prender threads nem sobrecarregar o provedor.
* **Auto-Recuperação:** Após o tempo de recuperação, o circuito transiciona para `HALF_OPEN` e testa uma chamada de sonda. Se for bem-sucedida, o circuito fecha automaticamente (`CLOSED`).
* **Resiliência a Falhas Transitórias:** Retries com recuo exponencial absorvem oscilações passageiras de rede sem intervenção do usuário.

### Negativas
* **Camada Adicional de Indireção:** Adiciona um nó decorador na pilha de chamadas entre o Caso de Uso e o Adaptador do Gateway.

## Pull Request
Implementado via Pull Request [#6](https://github.com/Pamorimd/nexus-order-system/pull/6) (refactor/resilience-circuit-breaker-retry).
