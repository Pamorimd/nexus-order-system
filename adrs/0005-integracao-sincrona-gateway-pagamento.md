# ADR 0005: Integração Síncrona Direta com Gateways de Pagamento

## Status
Substituído pelo [ADR-0006](0006-resiliencia-circuit-breaker-e-retries-gateway.md)

## Contexto
Na primeira iteração do sistema de pagamentos, os adaptadores de pagamento (`PixPaymentGateway`, `CreditCardPaymentGateway` e `BoletoPaymentGateway`) eram invocados de forma direta e síncrona pelo Caso de Uso `ProcessPaymentUseCase`. Esperava-se que os provedores externos de pagamento respondessem sempre dentro de milissegundos sem falhas.

## Decisão
Decidimos que os adaptadores de gateway de pagamento seriam instanciados diretamente pela fábrica e chamados diretamente pelo caso de uso através de conexões de rede padrão bloqueantes, sem mecanismos intermediários de tolerância a falhas.

## Alternativas Consideradas e Motivos de Descarte
1. **Chamadas Assíncronas via Filas de Mensagens (RabbitMQ/Kafka):**
   * *Motivo do descarte:* Para pagamentos via Pix e Cartão, o comprador espera feedback síncrono imediato na tela de confirmação ("Pagamento Aprovado"), inviabilizando processamento puramente offline assíncrono para o fluxo principal.

## Consequências
### Positivas
* **Código Inicial Extremamente Simples:** Chamada direta sem camadas adicionais de interceptação ou controle de estado.

### Negativas (Motivo da Substituição)
* **Falhas em Cascata:** Quando um gateway externo sofria instabilidade ou timeout de rede, a requisição travava a aplicação e causava erro 500 no checkout.
* **Falta de Tolerância a Falhas Transitórias:** Uma oscilação de meio segundo de rede derrubava uma venda que poderia ser concluída com uma nova tentativa imediata.

## Pull Request
Implementado via Pull Request [#5](https://github.com/Pamorimd/nexus-order-system/pull/5) (feat/initial-synchronous-gateways).
Substituído formalmente no Pull Request [#6](https://github.com/Pamorimd/nexus-order-system/pull/6).
