# 3. Arquitetura do Sistema

## 3.1 Plano Macro: Monolito Modular
A macroestrutura do Nexus Order System adota o estilo **Monolito Modular** (Capítulo 5 do livro da disciplina). Todos os módulos funcionais (Pedidos, Tarifação de Frete, Liquidação Multigateway e Resiliência) coexistem na mesma base de código e rodam sob um único processo de aplicação, organizados com fronteiras lógicas estritas.

### Justificativa Baseada no Livro da Disciplina:
* **Quando Adotar (Seção do Livro):** É recomendado quando a equipe é pequena/focada, o domínio de negócio possui alta coesão e há necessidade de forte consistência transacional entre as etapas (ex: reservar estoque, aplicar frete e liquidar transação sem a sobrecarga de transações distribuídas de duas fases ou padrões Saga complexos).
* **Quando Evitar (Seção do Livro):** Deve ser evitado quando diferentes áreas de negócio necessitam de ciclos de vida de deploy totalmente independentes, com centenas de engenheiros trabalhando simultaneamente e com tecnologias de hardware heterogêneas.
* **Custo Real (Seção do Livro):** A divisão prematura em microsserviços introduz custos reais elevados: observabilidade distribuída (tracing, logs correlacionados), complexidade de rede, latência adicional por salto de requisição, serialização de dados e custo de múltiplos ambientes em nuvem. O monolito modular elimina completamente esses custos na fase atual do projeto.

---

## 3.2 Plano Interno: Arquitetura Hexagonal (Ports & Adapters)
Internamente, o código é estruturado seguindo os princípios de Alistair Cockburn e da Clean Architecture (Capítulo 6):

### Mapeamento de Pastas e Componentes:
| Camada | Pasta do Código | Responsabilidade e Componentes |
| :--- | :--- | :--- |
| **Domain** | `src/nexus/domain/` | Entidades puras (`Order`, `OrderItem`), Objetos de Valor (`Money`, `Address`), Exceções explícitas (`exceptions.py`), Portas abstratas (`ports.py`), Estados GoF (`states.py`) e Estratégias GoF (`strategies.py`). Não possui dependência de frameworks. |
| **Application** | `src/nexus/application/` | Casos de Uso (`use_cases.py`: `CreateOrderUseCase`, `ProcessPaymentUseCase`, `ShipOrderUseCase`) e DTOs (`dtos.py`). Orquestram os fluxos chamando as portas do domínio. |
| **Resilience** | `src/nexus/resilience/` | Padrões transversais de resiliência: `CircuitBreaker`, `execute_with_retry` e o decorador `ResilientPaymentGateway`. |
| **Adapters** | `src/nexus/adapters/` | Implementações concretas de infraestrutura: adaptadores de gateways (`gateways/`), frete (`shipping/`), persistência em memória (`persistence/`) e CLI de entrada (`entrypoints/`). |

### Diagrama da Organização Interna:
```mermaid
graph TD
    subgraph AdaptersEntrada["Adaptadores de Entrada (Driving)"]
        CLI["CLI Entrypoint<br>(src/nexus/adapters/entrypoints/cli.py)"]
    end

    subgraph Application["Camada de Aplicação (Casos de Uso)"]
        CreateUC["CreateOrderUseCase"]
        PayUC["ProcessPaymentUseCase"]
        ShipUC["ShipOrderUseCase"]
    end

    subgraph Domain["Núcleo Hexagonal (Domínio)"]
        Order["Entidade Order & OrderItem"]
        State["Padrão GoF State"]
        Strategy["Padrão GoF Strategy"]
        Ports["Portas de Domínio:<br>PaymentGatewayPort<br>OrderRepositoryPort<br>ShippingCalculatorPort"]
    end

    subgraph Resilience["Camada Transversal"]
        CB["Circuit Breaker & Retries"]
    end

    subgraph AdaptersSaida["Adaptadores de Saída (Driven)"]
        Repo["InMemoryOrderRepository"]
        Gateways["Pix / Card / Boleto Gateways"]
        ShippingAdapters["Correios / Express Adapters"]
    end

    CLI --> Application
    Application --> Domain
    Application --> Resilience
    Resilience --> Ports
    Ports -.-> AdaptersSaida
```

---

## 3.3 Dois Estilos Considerados e Descartados

1. **Microsserviços Distribuídos (Capítulo 7 do livro):**
   * *Motivo do Descarte:* Introduziria desnecessariamente complexidade de infraestrutura (service discovery, API gateways distribuídos, mensageria com RabbitMQ/Kafka, circuit breakers de rede de borda) e falhas parciais em cascata. Para o problema proposto, o ganho de desacoplamento físico não compensaria o custo operacional e cognitivo.
2. **Arquitetura em Camadas Tradicional com Dependência no Banco (MVC/Active Record - Capítulo 6):**
   * *Motivo do Descarte:* Em modelos tradicionais orientados a banco, as entidades herdam das classes de ORM e o domínio fica acoplado aos schemas do banco de dados, inviabilizando a Inversão de Dependência (DIP) e dificultando testes unitários rápidos e puros.

---

## 3.4 Diagramas C4 (Contexto, Contêineres e Componentes)

> **Nota:** Todos os conectores nos diagramas abaixo possuem rótulos explícitos de comunicação (`chamada`, `evento`, `fluxo`, `arquivo`), conforme exigido pelas diretrizes da disciplina e pelo Apêndice B.4.

### Nível 1: Diagrama de Contexto C4
Fonte em [`diagrams/c4-context.mmd`](../diagrams/c4-context.mmd)

```mermaid
graph TD
    User["Cliente / Comprador<br>[Pessoa]"]
    Admin["Operador Logístico / Admin<br>[Pessoa]"]
    Nexus["<b>Nexus Order System</b><br>[Software System]<br>Motor de pedidos, tarifação e liquidação"]
    BacenPix["Banco Central / Pix SPI<br>[External System]<br>Arranjo de Pagamentos Instantâneos"]
    CardAcquirer["Adquirente de Cartão<br>[External System]<br>Cielo / Stone / Stripe"]
    Correios["Serviço Postal (Correios)<br>[External System]<br>Cálculo de CEP, Sedex e PAC"]
    Transportadora["Transportadora Privada<br>[External System]<br>Malha aérea e rodoviária expressa"]

    User -- "chamada: Realiza checkout e consulta pedido" --> Nexus
    Admin -- "chamada: Consulta status e solicita despacho" --> Nexus
    Nexus -- "chamada: Liquida pagamento instantâneo" --> BacenPix
    Nexus -- "chamada: Captura e autoriza transação de crédito" --> CardAcquirer
    Nexus -- "chamada: Consulta frete e prazo por CEP" --> Correios
    Nexus -- "chamada: Consulta cotação expressa" --> Transportadora
```

---

### Nível 2: Diagrama de Contêineres C4
Fonte em [`diagrams/c4-container.mmd`](../diagrams/c4-container.mmd)

```mermaid
graph TD
    User["Cliente / Comprador<br>[Pessoa]"]
    Admin["Operador Logístico<br>[Pessoa]"]

    subgraph NexusBoundary["Nexus Order System [Container Boundary]"]
        CLI["CLI / Terminal Entrypoint<br>[Python CLI / Python 3.10]<br>Interface de linha de comando para operadores e checkout"]
        CoreEngine["Nexus Core Engine<br>[Python Package / Clean Architecture]<br>Orquestra casos de uso, regras de negócio e resiliência"]
        DataStore["In-Memory / SQLite Repository<br>[Data Store]<br>Armazena agregados de pedidos e transações"]
    end

    ExternalGateways["Gateways Financeiros & Logísticos Externos<br>[External APIs]<br>Pix, Adquirentes e Correios"]

    User -- "fluxo: Executa comandos de criação e pagamento" --> CLI
    Admin -- "fluxo: Executa comandos de despacho" --> CLI
    CLI -- "chamada: Invoca casos de uso da aplicação" --> CoreEngine
    CoreEngine -- "chamada: Persiste e consulta agregados Order" --> DataStore
    CoreEngine -- "chamada: Transações protegidas por Circuit Breaker" --> ExternalGateways
```

---

### Nível 3: Diagrama de Componentes C4
Fonte em [`diagrams/c4-component.mmd`](../diagrams/c4-component.mmd)

```mermaid
graph TD
    subgraph NexusCoreEngine["Nexus Core Engine [Component Boundary]"]
        CLIController["CLI Controller<br>[adapters/entrypoints/cli.py]<br>Captura comandos do usuário e formata saídas"]

        subgraph ApplicationLayer["Application Layer (Casos de Uso)"]
            CreateOrderUC["CreateOrderUseCase<br>[application/use_cases.py]<br>Valida itens, frete, descontos e cria pedido"]
            ProcessPaymentUC["ProcessPaymentUseCase<br>[application/use_cases.py]<br>Orquestra liquidação financeira com gateway"]
            ShipOrderUC["ShipOrderUseCase<br>[application/use_cases.py]<br>Gerencia despacho de remessas"]
        end

        subgraph DomainLayer["Domain Layer (Hexagonal Core)"]
            OrderAggregate["Order & OrderItem Entities<br>[domain/entities.py]<br>Invariantes, cálculos monetários e State"]
            StatePattern["OrderState Hierarchy<br>[domain/states.py]<br>Pending, Paid, Shipped, Cancelled"]
            StrategyPattern["ShippingStrategy Family<br>[domain/strategies.py]<br>Sedex, PAC, ExpressTransportadora"]
            DomainPorts["Domain Ports (Interfaces)<br>[domain/ports.py]<br>PaymentGatewayPort, OrderRepositoryPort, ShippingCalculatorPort"]
        end

        subgraph ResilienceLayer["Resilience Layer (Padrão Transversal 18.4)"]
            ResilientDecorator["ResilientPaymentGateway<br>[resilience/resilient_gateway.py]<br>Decora gateways com tolerância a falhas"]
            CircuitBreakerComp["CircuitBreaker<br>[resilience/circuit_breaker.py]<br>Closed, Open, Half-Open"]
            RetryPolicy["Retry Policy<br>[resilience/retry.py]<br>Exponential backoff"]
        end

        subgraph AdaptersLayer["Adapters Layer (Infraestrutura)"]
            GatewayFactory["PaymentGatewayFactory<br>[adapters/gateways/factory.py]<br>GoF Factory Method"]
            PixAdapter["PixPaymentGateway<br>[adapters/gateways/pix.py]"]
            CardAdapter["CreditCardPaymentGateway<br>[adapters/gateways/credit_card.py]"]
            BoletoAdapter["BoletoPaymentGateway<br>[adapters/gateways/boleto.py]"]
            MemoryRepo["InMemoryOrderRepository<br>[adapters/persistence/memory_repo.py]"]
        end
    end

    CLIController -- "fluxo: Dispara comandos de checkout" --> CreateOrderUC
    CLIController -- "fluxo: Dispara pagamento" --> ProcessPaymentUC
    CLIController -- "fluxo: Dispara envio" --> ShipOrderUC

    CreateOrderUC -- "chamada: Calcula frete via Strategy" --> StrategyPattern
    CreateOrderUC -- "chamada: Instancia e valida agregado" --> OrderAggregate
    CreateOrderUC -- "chamada: Salva pedido na porta" --> DomainPorts

    ProcessPaymentUC -- "chamada: Solicita gateway à fábrica" --> GatewayFactory
    GatewayFactory -- "chamada: Cria e encapsula no Decorador" --> ResilientDecorator
    ResilientDecorator -- "chamada: Controla abertura de circuito" --> CircuitBreakerComp
    ResilientDecorator -- "chamada: Executa repetições com backoff" --> RetryPolicy
    ResilientDecorator -- "chamada: Encaminha chamada ao adaptador concreto" --> PixAdapter
    ResilientDecorator -- "chamada: Encaminha chamada ao adaptador concreto" --> CardAdapter
    ResilientDecorator -- "chamada: Encaminha chamada ao adaptador concreto" --> BoletoAdapter

    ProcessPaymentUC -- "chamada: Executa transição pay() delegada ao State" --> OrderAggregate
    OrderAggregate -- "chamada: Modifica estado corrente" --> StatePattern

    DomainPorts -. "fluxo: Implementado por" .-> MemoryRepo
    DomainPorts -. "fluxo: Implementado por" .-> PixAdapter
    DomainPorts -. "fluxo: Implementado por" .-> CardAdapter
    DomainPorts -. "fluxo: Implementado por" .-> BoletoAdapter
```

---

## 3.5 Diagrama de Sequência: Fluxo Central de Checkout
Fonte em [`diagrams/sequence-checkout.mmd`](../diagrams/sequence-checkout.mmd)

```mermaid
sequenceDiagram
    autonumber
    actor Cliente as Cliente / Comprador
    participant CLI as CLI Controller
    participant CreateUC as CreateOrderUseCase
    participant Strategy as ShippingStrategy (Sedex)
    participant Order as Order Aggregate
    participant Repo as OrderRepositoryPort
    participant PayUC as ProcessPaymentUseCase
    participant Factory as PaymentGatewayFactory
    participant ResilientGW as ResilientPaymentGateway
    participant CB as CircuitBreaker
    participant PixGW as PixPaymentGateway
    participant State as OrderState (Pending->Paid)

    Cliente->>CLI: Solicita criação de pedido com frete Sedex
    CLI->>CreateUC: execute(CreateOrderInputDTO)
    CreateUC->>Strategy: calculate(origem, destino, peso)
    Strategy-->>CreateUC: Money(R$ 37.35)
    CreateUC->>Order: Order(items, shipping_cost, discount)
    Note over Order,State: Estado inicial instanciado: PendingPaymentState
    CreateUC->>Repo: save(order)
    Repo-->>CreateUC: Pedido salvo
    CreateUC-->>CLI: OrderOutputDTO (Status: PENDING_PAYMENT)
    CLI-->>Cliente: Exibe dados do pedido e resumo financeiro

    Cliente->>CLI: Confirma pagamento via Pix
    CLI->>PayUC: execute(ProcessPaymentInputDTO)
    PayUC->>Repo: find_by_id(order_id)
    Repo-->>PayUC: Instância de Order
    PayUC->>Factory: create(PaymentMethod.PIX)
    Factory-->>PayUC: Instância de ResilientPaymentGateway(PixGateway)
    PayUC->>ResilientGW: process_payment(PaymentRequest)
    ResilientGW->>CB: before_call()
    Note over CB: Estado atual: CLOSED (Permite passagem)
    CB-->>ResilientGW: OK
    ResilientGW->>PixGW: process_payment(PaymentRequest)
    PixGW-->>ResilientGW: PaymentResult(success=True, tx_id="PIX-...")
    ResilientGW->>CB: record_success()
    ResilientGW-->>PayUC: PaymentResult
    PayUC->>Order: pay(transaction_id)
    Order->>State: pay(order, transaction_id)
    State->>Order: set_state(PaidState)
    PayUC->>Repo: save(order)
    PayUC-->>CLI: ProcessPaymentOutputDTO (Status: PAID)
    CLI-->>Cliente: Exibe confirmação imediata e comprovante Pix
```
