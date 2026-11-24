# 2. Atributos de Qualidade (ISO/IEC 25010:2023)

Em conformidade com o Capítulo 2 (seção 2.3) do livro da disciplina e com a norma internacional **ISO/IEC 25010:2023 (Systems and software Quality Requirements and Evaluation)**, selecionamos os três atributos de qualidade fundamentais para o sucesso do Nexus Order System, seguidos pelo trade-off conscientemente assumido.

---

## 2.1 Os Três Atributos de Qualidade Mais Importantes

### 1. Confiabilidade / Tolerância a Falhas (*Fault Tolerance* - ISO/IEC 25010:2023 §4.2.4)
* **Por que este atributo e não outro:** O sistema interage diretamente com redes bancárias e APIs de terceiros que sofrem instabilidade frequente. Uma falha de comunicação com um gateway de pagamento ou cálculo de frete externo não pode causar colapso do sistema, travar processos de checkout concorrentes nem perder o estado do cliente.
* **Decisão de Arquitetura que o atende:** Adoção do Padrão Transversal de Resiliência com *Circuit Breaker* e *Retry com Exponential Backoff*, formalizado na decisão [ADR-0006](../adrs/0006-resiliencia-circuit-breaker-e-retries-gateway.md).
* **Medida Observável:** 
  * Abertura imediata do circuito (`fail-fast`) após exatamente $2$ falhas consecutivas de rede.
  * Tempo de resposta em falha reduzido de $\approx 5000\text{ ms}$ (timeout de rede convencional) para menos de $1\text{ ms}$ enquanto o circuito estiver no estado `OPEN`.
* **Comprovação no Código:**
  ```python
  # Trecho de src/nexus/resilience/circuit_breaker.py
  def before_call(self) -> None:
      current_state = self.state
      if current_state == CircuitState.OPEN:
          raise CircuitBreakerOpenError(
              f"Circuito ABERTO: Serviço externo indisponível temporariamente "
              f"(aguardando recuperação de {self.recovery_timeout_seconds}s)."
          )
  ```
  Link: [`src/nexus/resilience/circuit_breaker.py#L48-L56`](https://github.com/Pamorimd/nexus-order-system/blob/main/src/nexus/resilience/circuit_breaker.py#L48-L56)

---

### 2. Manutenibilidade / Modificabilidade (*Modifiability* - ISO/IEC 25010:2023 §4.2.7)
* **Por que este atributo e não outro:** Sistemas de e-commerce precisam adaptar-se com rapidez a novas operadoras logísticas (ex: transportadoras regionais, entregas no mesmo dia), novos provedores bancários (ex: carteiras digitais, criptomoedas) e novas campanhas promocionais sem riscos de regressão no núcleo estável de checkout.
* **Decisão de Arquitetura que o atende:** Organização interna em Arquitetura Hexagonal (*Ports & Adapters*) e aplicação do Padrão GoF *Strategy*, formalizados no [ADR-0002](../adrs/0002-organizacao-interna-arquitetura-hexagonal.md).
* **Medida Observável:** A adição de um novo meio de pagamento ou método de frete requer a criação de exatamente 1 arquivo na camada `adapters/` e zero alterações nas entidades ou casos de uso existentes, com $100\%$ de isolamento comprovado por testes automatizados.
* **Comprovação no Código:**
  ```python
  # Trecho de src/nexus/domain/ports.py
  class ShippingCalculatorPort(ABC):
      @abstractmethod
      def calculate_shipping(self, origin_cep: str, destination_cep: str, weight_kg: float) -> Money:
          """Calcula o custo monetário da entrega para o trecho e peso."""
  ```
  Link: [`src/nexus/domain/ports.py#L68-L74`](https://github.com/Pamorimd/nexus-order-system/blob/main/src/nexus/domain/ports.py#L68-L74)

---

### 3. Eficiência de Desempenho / Comportamento Temporal (*Time Behaviour* - ISO/IEC 25010:2023 §4.2.2)
* **Por que este atributo e não outro:** A latência na confirmação de etapas de checkout possui correlação direta com o abandono de carrinho. Operações internas de validação de itens, cálculo de descontos, agregação e transições de estado precisam ser instantâneas.
* **Decisão de Arquitetura que o atende:** Escolha do estilo Monolito Modular e repositório desacoplado em memória/banco local, formalizados no [ADR-0001](../adrs/0001-estrutura-macro-monolito-modular.md) e [ADR-0003](../adrs/0003-persistencia-dados-repositorio.md).
* **Medida Observável:** Tempo de execução da suíte completa de 37 testes unitários e de integração inferior a $1000\text{ ms}$ (atualmente aferida em $0.44\text{ s}$), e tempo de processamento interno da criação e tarifação do pedido inferior a $10\text{ ms}$ no host.
* **Comprovação no Código:**
  ```python
  # Trecho de src/nexus/application/use_cases.py
  def execute(self, input_dto: CreateOrderInputDTO) -> OrderOutputDTO:
      # Execução síncrona direta em memória sem saltos de rede entre serviços
      ...
  ```
  Link: [`src/nexus/application/use_cases.py#L42-L80`](https://github.com/Pamorimd/nexus-order-system/blob/main/src/nexus/application/use_cases.py#L42-L80)

---

## 2.2 Trade-off Assumido (Livro, Seção 2.4)

> **O que pioramos de propósito para ganhar esses atributos:**

Para atingir **Manutenibilidade** e **Tolerância a Falhas**, decidimos deliberadamente **aumentar a complexidade estrutural inicial do código e o número de classes e indireções**. 

Em um script procedural simples (ou num CRUD tradicional), o cálculo de frete e o envio de pagamento seriam feitos em uma única função linear com condicionais `if/else`. Para obter baixo acoplamento e resiliência, introduzimos:
* Portas abstratas (`PaymentGatewayPort`, `OrderRepositoryPort`);
* Múltiplas classes de adaptadores (`PixPaymentGateway`, `CreditCardPaymentGateway`, `BoletoPaymentGateway`);
* Fábrica de instanciação (`PaymentGatewayFactory`);
* Máquina de estados polimórfica (`OrderState`, `PendingPaymentState`, `PaidState`, `ShippedState`);
* Decoradores de resiliência interceptando as chamadas (`ResilientPaymentGateway`).

**Conclusão do Trade-off:** Sacrificamos a "simplicidade visual imediata" de um código de arquivo único em favor de robustez técnica, capacidade de extensão sem quebras (OCP) e garantia de que instabilidades em serviços externos jamais derrubarão o motor de pedidos.
