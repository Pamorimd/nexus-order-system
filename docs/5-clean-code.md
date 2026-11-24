# 5. Práticas de Clean Code e Qualidade de Código

A base de código do **Nexus Order System** foi construída seguindo as diretrizes clássicas de *Clean Code* (Robert C. Martin) e o catálogo de *Code Smells & Refactoring* do **Refactoring Guru**.

---

## 5.1 Comprovação das Práticas de Clean Code no Código

### 1. Nomes Claros e Intencionais
Os identificadores expressam intenção de negócio diretamente, evitando abreviações crípticas ou tipos húngaros:
```python
# Trecho de src/nexus/domain/states.py
class PendingPaymentState(OrderState):
    def ship(self, order: Order, tracking_code: str) -> None:
        raise InvalidStateTransitionError(
            "Regra violada: Impossível despachar um pedido que ainda não foi pago."
        )
```
Link: [`src/nexus/domain/states.py#L42-L46`](https://github.com/Pamorimd/nexus-order-system/blob/main/src/nexus/domain/states.py#L42-L46)

### 2. Funções Pequenas, com Responsabilidade Única e Poucos Parâmetros
Todas as funções possuem menos de 20 linhas e realizam apenas uma ação coesa. Parâmetros agrupados utilizam DTOs e Value Objects:
```python
# Trecho de src/nexus/application/use_cases.py
def _to_output_dto(self, order: Order) -> OrderOutputDTO:
    return OrderOutputDTO(
        order_id=order.order_id,
        customer_email=order.customer_email,
        status=order.status,
        items_subtotal=str(order.items_subtotal),
        shipping_cost=str(order.shipping_cost),
        discount=str(order.discount),
        final_total=str(order.final_total),
        transaction_id=order.transaction_id,
        tracking_code=order.tracking_code,
        cancellation_reason=order.cancellation_reason,
    )
```
Link: [`src/nexus/application/use_cases.py#L82-L95`](https://github.com/Pamorimd/nexus-order-system/blob/main/src/nexus/application/use_cases.py#L82-L95)

### 3. Ausência de Duplicação Relevante (DRY)
A lógica de arredondamento financeiro, soma com verificação de moeda e checagem de valores negativos foi centralizada de forma definitiva no objeto de valor `Money`:
```python
# Trecho de src/nexus/domain/value_objects.py
def _ensure_same_currency(self, other: Money) -> None:
    if self.currency != other.currency:
        raise CurrencyMismatchError(
            f"Incompatibilidade de moedas: {self.currency} vs {other.currency}"
        )
```
Link: [`src/nexus/domain/value_objects.py#L65-L70`](https://github.com/Pamorimd/nexus-order-system/blob/main/src/nexus/domain/value_objects.py#L65-L70)

### 4. Baixo Acoplamento e Alta Coesão
Casos de uso não realizam chamadas diretas a APIs externas. O caso de uso `ProcessPaymentUseCase` apenas invoca a abstração `gateway.process_payment(request)`, mantendo coesão máxima com a orquestração do fluxo.

### 5. Comentários Apenas para Explicar o "Porquê"
O código é autoexplicativo. Comentários são usados exclusivamente para justificar decisões de arquitetura ou comportamentos não triviais de resiliência:
```python
# Trecho de src/nexus/resilience/circuit_breaker.py
# Qualquer falha durante recuperação em HALF_OPEN reabre imediatamente o circuito
if current_state == CircuitState.HALF_OPEN:
    self._transition_to(CircuitState.OPEN)
```
Link: [`src/nexus/resilience/circuit_breaker.py#L71-L74`](https://github.com/Pamorimd/nexus-order-system/blob/main/src/nexus/resilience/circuit_breaker.py#L71-L74)

### 6. Tratamento de Erro Explícito
Substituição de códigos de erro numéricos ou retorno de `None` por exceções de domínio ricas e tipadas:
```python
# Trecho de src/nexus/domain/exceptions.py
class DomainError(Exception):
    """Exceção base para todos os erros de negócio do domínio."""

class InvalidStateTransitionError(DomainError):
    """Lançada ao tentar realizar uma transição ilegal no ciclo de vida do pedido."""
```
Link: [`src/nexus/domain/exceptions.py#L7-L28`](https://github.com/Pamorimd/nexus-order-system/blob/main/src/nexus/domain/exceptions.py#L7-L28)

---

## 5.2 Code Smells Removidos (Catálogo Refactoring Guru)

| Code Smell Identificado | Onde Estaria Sem Refatoração | Técnica de Refatoração Aplicada | Resultado Obtido |
| :--- | :--- | :--- | :--- |
| **Primitive Obsession** | Usar números `float` puros para valores monetários e `str` para status. | *Replace Data Value with Object* (Criação de `Money` e `OrderStatus`). | Eliminação de erros de arredondamento de ponto flutuante e validação garantida na instanciação. |
| **Switch Statements** | Condicionais `if/elif` extensas para verificar status do pedido ou transportadoras. | *Replace Conditional with Polymorphism* (Padrões **State** e **Strategy**). | Cada estado/algoritmo encapsula suas regras em classes polimórficas independentes. |
| **Long Method** | Um único método de checkout calculando frete, itens, chamando banco e gateway. | *Extract Method* e divisão em Casos de Uso na camada de aplicação. | Métodos pequenos (< 15 linhas) com responsabilidades bem delimitadas. |

---

## 5.3 Linter e Formatador (Ruff)

Conforme exigido pelo enunciado para projetos em Python, utilizamos o **Ruff** (`ruff check` e `ruff format`), com o arquivo `pyproject.toml` versionado no repositório.

### Regras Habilitadas no `pyproject.toml`:
* `E`, `W`: Erros e avisos de estilo PEP 8 (*pycodestyle*).
* `F`: Detecção de bugs e variáveis não utilizadas (*pyflakes*).
* `I`: Ordenação e organização automática de imports (*isort*).
* `N`: Convenções de nomenclatura PEP 8 (*pep8-naming*).
* `UP`: Atualização para sintaxe moderna do Python 3.10+ (*pyupgrade*).
* `B`: Boas práticas e prevenção de armadilhas (*flake8-bugbear*).
* `C4`: Otimização de compreensões de lista/dicionário (*flake8-comprehensions*).
* `SIM`: Simplificação de código redundante (*flake8-simplify*).

### Comandos de Execução:
```bash
# 1. Verificação estática de regras e bugs
ruff check .

# 2. Verificação de conformidade de formatação
ruff format . --check
```

---

## 5.4 Testes Automatizados e Cobertura

O repositório possui uma suíte com **37 testes automatizados** cobrindo entidades, objetos de valor, padrões GoF, resiliência e casos de uso.

### Como Executar os Testes:
```bash
# Execução via Pytest (utilizado no CI do GitHub Actions):
pytest -v

# Ou via módulo nativo unittest do Python (zero dependências locais):
python3 -m unittest discover -s tests -v
```

### Resumo da Cobertura de Testes:
* `tests/test_domain_entities.py`: Invariantes de `Order`, cálculos e precisão decimal de `Money`.
* `tests/test_gof_strategy.py`: Estratégias de frete (Sedex, PAC, Express) e descontos.
* `tests/test_gof_state.py`: Transições válidas e bloqueio de transições ilegais do ciclo de vida.
* `tests/test_gof_factory.py`: Instanciação dinâmica de gateways pela fábrica.
* `tests/test_solid_principles.py`: Prova formal unitária de SRP, OCP, LSP, ISP e DIP.
* `tests/test_resilience_circuit_breaker.py`: Estados do Circuit Breaker, fail-fast e retries com backoff.
* `tests/test_use_cases.py`: Fluxos completos de criação, pagamento, despacho e cancelamento.
