# 7. Padrão Transversal: Resiliência (Capítulo 18.4)

Em conformidade com os capítulos 17 a 19 do livro da disciplina, implementamos o **Padrão Transversal de Resiliência (Capítulo 18.4)**, combinando três mecanismos essenciais:
1. **Timeout:** Limite de tempo determinístico para chamadas a serviços remotos;
2. **Retry com Exponential Backoff:** Repetições automáticas de falhas transitórias com recuo exponencial e aumento do intervalo entre tentativas;
3. **Circuit Breaker:** Bloqueio imediato (*fail-fast*) de requisições quando um serviço externo apresenta falhas reiteradas, evitando degradação sistêmica e consumo inútil de recursos.

---

## 7.1 Por que este Sistema Precisa de Resiliência?

O **Nexus Order System** interage com serviços externos críticos: o arranjo Pix do Banco Central (SPI), adquirentes de cartão de crédito e a CIP para registro de boletos. Na internet, conexões com essas entidades sofrem com:
* **Falhas Transitórias:** Pequenas oscilações de rede que duram centenas de milissegundos. Sem o mecanismo de *Retry*, uma venda legítima de um cliente seria abortada desnecessariamente.
* **Quedas Prolongadas:** Quando uma adquirente de cartão entra em manutenção não programada ou colapso, continuar enviando centenas de requisições síncronas bloqueantes consumiria todas as threads de execução da aplicação local, esgotaria pools de conexões e causaria colapso em cascata no motor de pedidos.
* **Comportamento do Circuit Breaker:** Ao detectar $2$ falhas consecutivas, o circuito abre (`OPEN`). As requisições seguintes são rejeitadas instantaneamente em $< 1\text{ ms}$ através da exceção `CircuitBreakerOpenError`, sem gastar tempo de rede. Após a janela de recuperação de $1.5\text{ s}$, o circuito transiciona para `HALF_OPEN` e testa uma chamada de sonda. Se responder com sucesso, o sistema fecha o circuito e restaura a operação normal.

---

## 7.2 Onde o Padrão Está no Código

O padrão está encapsulado de forma modular no pacote `src/nexus/resilience/`:

### 1. Máquina de Estados do Circuit Breaker (`src/nexus/resilience/circuit_breaker.py`)
Controla os estados `CLOSED`, `OPEN` e `HALF_OPEN`:
```python
# Trecho de src/nexus/resilience/circuit_breaker.py
class CircuitBreaker:
    def before_call(self) -> None:
        """Valida se a chamada externa pode ser executada ou deve falhar imediatamente."""
        current_state = self.state
        if current_state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                f"Circuito ABERTO: Serviço externo indisponível temporariamente "
                f"(aguardando recuperação de {self.recovery_timeout_seconds}s)."
            )

    def record_failure(self) -> None:
        self._consecutive_failures += 1
        current_state = self.state
        if current_state == CircuitState.HALF_OPEN or (
            current_state == CircuitState.CLOSED and self._consecutive_failures >= self.failure_threshold
        ):
            self._transition_to(CircuitState.OPEN)
```
Link: [`src/nexus/resilience/circuit_breaker.py#L48-L76`](https://github.com/Pamorimd/nexus-order-system/blob/main/src/nexus/resilience/circuit_breaker.py#L48-L76)

### 2. Algoritmo de Retry com Exponential Backoff (`src/nexus/resilience/retry.py`)
Garante recuo exponencial multiplicando o atraso por um fator configurável:
```python
# Trecho de src/nexus/resilience/retry.py
def execute_with_retry(
    action: Callable[[], T],
    max_attempts: int = 3,
    initial_delay_seconds: float = 0.05,
    backoff_factor: float = 2.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    attempt = 0
    delay = initial_delay_seconds
    while attempt < max_attempts:
        try:
            return action()
        except retryable_exceptions as exc:
            attempt += 1
            if attempt >= max_attempts:
                raise exc
            time.sleep(delay)
            delay *= backoff_factor
```
Link: [`src/nexus/resilience/retry.py#L17-L40`](https://github.com/Pamorimd/nexus-order-system/blob/main/src/nexus/resilience/retry.py#L17-L40)

### 3. Decorador Resiliente (`src/nexus/resilience/resilient_gateway.py`)
Intercepta a porta `PaymentGatewayPort` aplicando os dois mecanismos de forma transparente aos Casos de Uso:
```python
# Trecho de src/nexus/resilience/resilient_gateway.py
class ResilientPaymentGateway(RefundablePaymentPort):
    def process_payment(self, request: PaymentRequest) -> PaymentResult:
        # 1. Verifica estado do circuito (fail-fast imediato se estiver ABERTO)
        self._circuit_breaker.before_call()

        try:
            # 2. Executa com retry e exponential backoff
            result = execute_with_retry(
                action=lambda: self._inner_gateway.process_payment(request),
                max_attempts=self._max_attempts,
            )
            if result.success:
                self._circuit_breaker.record_success()
            else:
                self._circuit_breaker.record_failure()
            return result
        except Exception as exc:
            self._circuit_breaker.record_failure()
            raise exc
```
Link: [`src/nexus/resilience/resilient_gateway.py#L36-L58`](https://github.com/Pamorimd/nexus-order-system/blob/main/src/nexus/resilience/resilient_gateway.py#L36-L58)

---

## 7.3 Comprovação Automatizada do Comportamento

A eficácia do padrão transversal é comprovada na suíte de testes em `tests/test_resilience_circuit_breaker.py`:
* **Teste de Abertura e Bloqueio Fail-Fast:** `test_circuit_breaker_transitions()`
* **Teste de Reabertura Imediata em Falha de Teste:** `test_circuit_breaker_reopens_on_half_open_failure()`
* **Teste de Sucesso Eventual por Retry:** `test_retry_mechanism_eventual_success()`
* **Teste de Esgotamento de Tentativas:** `test_retry_exhaustion_raises_exception()`
* **Teste de Interceptação do Gateway:** `test_resilient_gateway_integration()`

Todos os 5 testes de resiliência executam com $100\%$ de sucesso em menos de $0.4\text{ s}$.
Link: [`tests/test_resilience_circuit_breaker.py`](https://github.com/Pamorimd/nexus-order-system/blob/main/tests/test_resilience_circuit_breaker.py)
