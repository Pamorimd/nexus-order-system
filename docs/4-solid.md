# 4. Princípios SOLID no Código

Nesta seção, comprovamos a aplicação dos cinco princípios **SOLID** diretamente na base de código do **Nexus Order System**. Conforme a regra de ouro do trabalho, cada princípio apresenta o trecho de código correspondente e o efeito arquitetural concreto gerado no sistema.

---

## 4.1 S - Single Responsibility Principle (Princípio da Responsabilidade Única)

### Trecho de Código
A entidade `Order` é responsável exclusivamente por manter a integridade dos dados e regras do agregado comercial (itens, cálculos monetários de totais e delegação de transição de estado), sem conhecer nada sobre banco de dados, HTTP ou serialização. A persistência é de responsabilidade única da porta `OrderRepositoryPort`:

```python
# Trecho de src/nexus/domain/entities.py
class Order:
    """Entidade raiz de agregação do pedido (Aggregate Root).
    Garante invariantes de cálculo e ciclo de vida através do padrão State.
    """
    @property
    def final_total(self) -> Money:
        """Calcula o montante final líquido: (itens + frete) - desconto."""
        gross = self.items_subtotal.add(self.shipping_cost)
        if self.discount.amount > gross.amount:
            return Money.zero()
        return gross.subtract(self.discount)
```
Link: [`src/nexus/domain/entities.py#L108-L115`](https://github.com/Pamorimd/nexus-order-system/blob/main/src/nexus/domain/entities.py#L108-L115)

E a persistência fica isolada em sua própria classe:
```python
# Trecho de src/nexus/adapters/persistence/memory_repo.py
class InMemoryOrderRepository(OrderRepositoryPort):
    def save(self, order: Order) -> None:
        self._orders[order.order_id] = order
```
Link: [`src/nexus/adapters/persistence/memory_repo.py#L16-L18`](https://github.com/Pamorimd/nexus-order-system/blob/main/src/nexus/adapters/persistence/memory_repo.py#L16-L18)

### Efeito no Código (Problema Resolvido / Evitado)
* **Problema Evitado:** Evitou-se o code smell *God Class* e o modelo *Active Record*, onde a mesma classe realiza cálculos matemáticos, validações e comandos SQL no banco (`order.save()`).
* **Efeito Real:** Mudanças no esquema de banco de dados ou no provedor de armazenamento não causam nenhum impacto ou risco de quebra nas regras financeiras de cálculo do pedido.

---

## 4.2 O - Open/Closed Principle (Princípio Aberto/Fechado)

### Trecho de Código
O cálculo de frete é aberto para extensão (novas transportadoras ou operadoras logísticas), mas fechado para modificação. A classe abstrata `ShippingStrategy` define o contrato:

```python
# Trecho de src/nexus/domain/strategies.py
class ShippingStrategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Nome identificador da modalidade de envio."""

    @abstractmethod
    def calculate(self, origin_cep: str, destination_cep: str, total_weight_kg: float) -> Money:
        """Calcula o valor do frete."""
```
Link: [`src/nexus/domain/strategies.py#L17-L28`](https://github.com/Pamorimd/nexus-order-system/blob/main/src/nexus/domain/strategies.py#L17-L28)

Para adicionar uma nova transportadora (ex: entrega via Drone ou Loggi), basta criar uma nova classe sem editar nenhuma linha de `CreateOrderUseCase`:
```python
# Exemplo comprovado no teste tests/test_solid_principles.py
class DroneShippingStrategy(ShippingStrategy):
    @property
    def name(self) -> str:
        return "DRONE_SUPER_FAST"

    def calculate(self, origin_cep: str, destination_cep: str, total_weight_kg: float) -> Money:
        return Money.from_float(75.00)
```
Link: [`tests/test_solid_principles.py#L48-L60`](https://github.com/Pamorimd/nexus-order-system/blob/main/tests/test_solid_principles.py#L48-L60)

### Efeito no Código (Problema Resolvido / Evitado)
* **Problema Evitado:** Evitou cadeias extensas de `if/elif/else` baseadas em strings (`if transportadora == "CORREIOS": ... elif transportadora == "LOGGI": ...`).
* **Efeito Real:** Novas operadoras logísticas podem ser plugadas em produção sem risco de introduzir bugs nas regras das operadoras antigas já homologadas.

---

## 4.3 L - Liskov Substitution Principle (Princípio da Substituição de Liskov)

### Trecho de Código
Todas as classes concretas de pagamento (`PixPaymentGateway`, `CreditCardPaymentGateway`, `BoletoPaymentGateway`) implementam o contrato estrito de `PaymentGatewayPort`:

```python
# Trecho de src/nexus/domain/ports.py
class PaymentGatewayPort(ABC):
    @abstractmethod
    def process_payment(self, request: PaymentRequest) -> PaymentResult:
        """Executa a liquidação da transação no gateway remoto."""
```
Link: [`src/nexus/domain/ports.py#L48-L53`](https://github.com/Pamorimd/nexus-order-system/blob/main/src/nexus/domain/ports.py#L48-L53)

Todas as implementações recebem um `PaymentRequest` e devolvem um `PaymentResult` válido, sem lançar exceções inesperadas que violem as expectativas do cliente chamador:
```python
# Trecho de tests/test_solid_principles.py
for gateway in [PixPaymentGateway(), CreditCardPaymentGateway(), BoletoPaymentGateway()]:
    result = gateway.process_payment(req)
    assert isinstance(result.success, bool)
    assert len(result.transaction_id) > 0
```
Link: [`tests/test_solid_principles.py#L76-L84`](https://github.com/Pamorimd/nexus-order-system/blob/main/tests/test_solid_principles.py#L76-L84)

### Efeito no Código (Problema Resolvido / Evitado)
* **Problema Evitado:** Evitou que uma subclasse fizesse assunções estranhas ao contrato (como retornar tipos incompatíveis, retornar `None` em vez de objeto de resultado ou exigir parâmetros fora da abstração).
* **Efeito Real:** O caso de uso `ProcessPaymentUseCase` pode substituir qualquer gateway de pagamento em tempo de execução de forma totalmente transparente e segura.

---

## 4.4 I - Interface Segregation Principle (Princípio da Segregação de Interfaces)

### Trecho de Código
Nem todo meio de pagamento suporta estorno programático imediato (por exemplo, um boleto bancário pago em lotérica não pode ser estornado diretamente para uma conta de forma síncrona). Em vez de poluir a interface base `PaymentGatewayPort` com métodos inúteis de reembolso, segregamos essa capacidade na interface especializada `RefundablePaymentPort`:

```python
# Trecho de src/nexus/domain/ports.py
class PaymentGatewayPort(ABC):
    @abstractmethod
    def process_payment(self, request: PaymentRequest) -> PaymentResult:
        """Cobrança essencial suportada por todos os gateways."""

class RefundablePaymentPort(PaymentGatewayPort):
    """Porta especializada apenas para quem suporta estorno síncrono (ISP)."""
    @abstractmethod
    def process_refund(self, transaction_id: str, amount: Money) -> RefundResult:
        """Executa estorno."""
```
Link: [`src/nexus/domain/ports.py#L48-L64`](https://github.com/Pamorimd/nexus-order-system/blob/main/src/nexus/domain/ports.py#L48-L64)

Assim, `BoletoPaymentGateway` implementa apenas `PaymentGatewayPort`:
```python
# Trecho de src/nexus/adapters/gateways/boleto.py
class BoletoPaymentGateway(PaymentGatewayPort):
    # Não precisa implementar 'process_refund' nem levantar NotImplementedError!
```
Link: [`src/nexus/adapters/gateways/boleto.py#L16-L23`](https://github.com/Pamorimd/nexus-order-system/blob/main/src/nexus/adapters/gateways/boleto.py#L16-L23)

### Efeito no Código (Problema Resolvido / Evitado)
* **Problema Evitado:** Evitou o anti-padrão de forçar classes a implementar métodos que elas não suportam (que resultaria em lançar `raise NotImplementedError` ou deixar métodos vazios).
* **Efeito Real:** Interfaces enxutas e coesas, onde os consumidores dependem apenas dos métodos que realmente utilizam.

---

## 4.5 D - Dependency Inversion Principle (Princípio da Inversão de Dependência)

### Trecho de Código
Módulos de alto nível (os Casos de Uso) não dependem de módulos de baixo nível (as classes de banco ou gateways externos). Ambos dependem de abstrações (Portas). 

O `ProcessPaymentUseCase` recebe a fábrica e as portas por injeção de dependência no seu construtor:

```python
# Trecho de src/nexus/application/use_cases.py
class ProcessPaymentUseCase:
    def __init__(
        self,
        order_repository: OrderRepositoryPort,
        gateway_factory: PaymentGatewayFactory,
    ) -> None:
        self._order_repository = order_repository
        self._gateway_factory = gateway_factory
```
Link: [`src/nexus/application/use_cases.py#L86-L95`](https://github.com/Pamorimd/nexus-order-system/blob/main/src/nexus/application/use_cases.py#L86-L95)

### Efeito no Código (Problema Resolvido / Evitado)
* **Problema Evitado:** Elimina o acoplamento rígido gerado pelo uso de `import` de classes concretas de infraestrutura dentro de arquivos de regras de negócio.
* **Efeito Real:** Permite a substituição completa da infraestrutura (por exemplo, injetar um repositório mock nos testes unitários) sem modificar uma única linha do caso de uso.
