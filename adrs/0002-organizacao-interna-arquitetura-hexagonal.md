# ADR 0002: Organização Interna via Arquitetura Hexagonal (Ports & Adapters)

## Status
Aceito

## Contexto
O núcleo de negócio do sistema envolve regras complexas de cálculo de frete por faixa de peso, máquina de estados finitos do pedido e políticas financeiras. Se o código do domínio for acoplado diretamente a frameworks web, drivers de banco de dados ou SDKs de gateways bancários de terceiros, os testes se tornam frágeis e qualquer mudança em fornecedores externos forçará alterações nas regras de negócio.

## Decisão
Decidimos organizar o código interno no padrão **Arquitetura Hexagonal (Ports & Adapters)** (Capítulo 6 do livro e Alistair Cockburn). O sistema é estruturado em três camadas concêntricas:
1. `domain`: Entidades (`Order`, `OrderItem`), Objetos de Valor (`Money`, `Address`), Estados (`OrderState`) e Portas Abstratas (`OrderRepositoryPort`, `PaymentGatewayPort`, `ShippingCalculatorPort`).
2. `application`: Casos de Uso (`CreateOrderUseCase`, `ProcessPaymentUseCase`, `ShipOrderUseCase`) e DTOs.
3. `adapters`: Adaptadores concretos de entrada (`entrypoints/cli.py`) e saída (`persistence/`, `gateways/`, `shipping/`).

## Alternativas Consideradas e Motivos de Descarte
1. **Arquitetura em Camadas Tradicional (MVC com Dependência no Banco - Capítulo 6):**
   * *Motivo do descarte:* O modelo relacional tende a ditar o modelo de domínio (ActiveRecord). As regras de negócio ficam amarradas aos schemas das tabelas, dificultando a aplicação de SOLID (especialmente DIP).
2. **Clean Architecture Clássica com 4 camadas estritas:**
   * *Motivo do descarte:* Para a escala deste motor, a Hexagonal fornece o exato nível de desacoplamento por portas sem a proliferação excessiva de mappers intermediários da Clean Architecture canônica.

## Consequências
### Positivas
* **Independência Tecnológica:** Os gateways de pagamento (Pix, Cartão, Boleto) e métodos de frete podem ser substituídos ou mockados sem modificar uma linha do domínio.
* **Testabilidade Notável:** 100% das regras de negócio, cálculos de frete e transições de estado são testáveis em frações de segundo em memória.
* **Aderência Direta a SOLID:** O Princípio de Inversão de Dependência (DIP) e a Segregação de Interfaces (ISP) tornam-se requisitos arquiteturais naturais.

### Negativas
* **Maior Quantidade de Arquivos e Indireções:** Criação explícita de interfaces de portas e adaptadores, exigindo familiaridade da equipe com polimorfismo.

## Pull Request
Implementado via Pull Request [#2](https://github.com/Pamorimd/nexus-order-system/pull/2) (`feat/hexagonal-ports-and-repo`), que introduz as portas de domínio e o primeiro adaptador.
