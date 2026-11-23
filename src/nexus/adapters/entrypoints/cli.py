"""Ponto de entrada de linha de comando (CLI Entrypoint).

Demonstra o funcionamento integrado de todos os componentes da aplicação:
- Arquitetura Hexagonal (Portas e Adaptadores)
- SOLID em ação
- Padrões GoF (Strategy, State, Factory Method)
- Padrão Transversal de Resiliência (Circuit Breaker e Retries)
"""

from __future__ import annotations

import sys
import time

from nexus.adapters.gateways.factory import PaymentGatewayFactory
from nexus.adapters.persistence.memory_repo import InMemoryOrderRepository
from nexus.application.dtos import (
    CreateOrderInputDTO,
    ItemInputDTO,
    ProcessPaymentInputDTO,
)
from nexus.application.use_cases import (
    CreateOrderUseCase,
    ProcessPaymentUseCase,
    ShipOrderUseCase,
)
from nexus.domain.exceptions import CircuitBreakerOpenError, InvalidStateTransitionError
from nexus.domain.value_objects import Address, PaymentMethod
from nexus.resilience.circuit_breaker import CircuitBreaker


def print_banner(title: str) -> None:
    print(f"\n{'=' * 65}")
    print(f"  {title}")
    print(f"{'=' * 65}")


def main() -> None:
    print_banner("NEXUS ORDER SYSTEM - DEMONSTRAÇÃO COMPLETA")
    print("Iniciando componentes da Arquitetura Hexagonal...")

    # 1. Instanciação dos adaptadores e injeção de dependências (DIP)
    repository = InMemoryOrderRepository()
    shared_circuit_breaker = CircuitBreaker(
        failure_threshold=2,
        recovery_timeout_seconds=1.5,
        half_open_success_threshold=1,
    )
    gateway_factory = PaymentGatewayFactory(
        enable_resilience=True,
        shared_circuit_breaker=shared_circuit_breaker,
    )

    create_order_uc = CreateOrderUseCase(order_repository=repository)
    process_payment_uc = ProcessPaymentUseCase(
        order_repository=repository,
        gateway_factory=gateway_factory,
    )
    ship_order_uc = ShipOrderUseCase(order_repository=repository)

    # 2. Cenário 1: Fluxo Principal com Sucesso (Happy Path)
    print_banner("CENÁRIO 1: Criação de Pedido, GoF Strategy e Liquidação Pix")
    delivery_address = Address(
        street="Av. Rebouças",
        number="1000",
        city="Campinas",
        state="SP",
        postal_code="13010000",
    )
    order_input = CreateOrderInputDTO(
        customer_email="aluno.puc@puc-campinas.edu.br",
        delivery_address=delivery_address,
        items=[
            ItemInputDTO(
                product_id="PROD-001",
                product_name="Livro de Arquitetura de Software",
                unit_price=120.00,
                quantity=2,
                weight_kg=0.8,
            ),
            ItemInputDTO(
                product_id="PROD-002",
                product_name="Mouse Ergonômico",
                unit_price=150.00,
                quantity=1,
                weight_kg=0.3,
            ),
        ],
        shipping_strategy_name="CORREIOS_SEDEX",
        origin_cep="13083852",
        discount_percentage=10.0,
    )

    order_output = create_order_uc.execute(order_input)
    print(f"[+] Pedido criado com sucesso: {order_output.order_id}")
    print(f"    Subtotal Itens: {order_output.items_subtotal}")
    print(f"    Custo de Frete (Strategy Sedex): {order_output.shipping_cost}")
    print(f"    Desconto Aplicado (10%): {order_output.discount}")
    print(f"    Total Final a Pagar: {order_output.final_total}")
    print(f"    Status Inicial (GoF State): {order_output.status.value}")

    print("\nExecutando Liquidação Financeira via Pix (GoF Factory + Resiliência)...")
    payment_input = ProcessPaymentInputDTO(
        order_id=order_output.order_id,
        payment_method=PaymentMethod.PIX,
        customer_email="aluno.puc@puc-campinas.edu.br",
    )
    payment_output = process_payment_uc.execute(payment_input)
    print(f"[+] Pagamento confirmado!")
    print(f"    Transação ID: {payment_output.transaction_id}")
    print(f"    Mensagem: {payment_output.message}")
    print(f"    Novo Status do Pedido: {payment_output.new_status.value}")

    print("\nDespachando Pedido para Transportadora...")
    shipped_output = ship_order_uc.execute(
        order_id=order_output.order_id,
        tracking_code="BR987654321SP",
    )
    print(f"[+] Pedido despachado!")
    print(f"    Código de Rastreio: {shipped_output.tracking_code}")
    print(f"    Status Atualizado: {shipped_output.status.value}")

    # 3. Cenário 2: Validação de Regras de Negócio e Invariantes do State
    print_banner("CENÁRIO 2: Validação de Regras do GoF State (Transição Inválida)")
    print("Tentativa ilegal: despachar novamente um pedido que já está em trânsito...")
    try:
        ship_order_uc.execute(order_output.order_id, tracking_code="OUTRO-CODIGO")
    except InvalidStateTransitionError as exc:
        print(f"[SUCESSO NA PROTEÇÃO DO ESTADO] Exceção capturada com precisão: {exc}")

    # 4. Cenário 3: Padrão Transversal de Resiliência (Circuit Breaker e Retries)
    print_banner("CENÁRIO 3: Padrão Transversal (Resiliência, Retry e Circuit Breaker)")
    print(f"Estado inicial do Circuit Breaker: {shared_circuit_breaker.state.value}")

    # Cria pedido para o teste de falha
    fail_order_input = CreateOrderInputDTO(
        customer_email="teste.falha@puc-campinas.edu.br",
        delivery_address=delivery_address,
        items=[
            ItemInputDTO(
                product_id="PROD-003",
                product_name="Teclado Mecânico",
                unit_price=300.00,
                quantity=1,
                weight_kg=1.1,
            )
        ],
    )
    fail_order = create_order_uc.execute(fail_order_input)

    print("\n1. Simulando falha transitória de rede com o gateway de cartão de crédito...")
    print("   O decorador resiliente executará até 3 tentativas com backoff exponencial...")
    try:
        process_payment_uc.execute(
            ProcessPaymentInputDTO(
                order_id=fail_order.order_id,
                payment_method=PaymentMethod.CREDIT_CARD,
                customer_email="teste.falha@puc-campinas.edu.br",
                simulate_failure=True,
            )
        )
    except Exception as exc:
        print(f"   [!] Falha esperada registrada após retries: {exc}")

    print(f"   Estado do Circuit Breaker após falha 1: {shared_circuit_breaker.state.value}")

    print("\n2. Segunda falha simulada (atingindo o limiar de falhas)...")
    try:
        process_payment_uc.execute(
            ProcessPaymentInputDTO(
                order_id=fail_order.order_id,
                payment_method=PaymentMethod.CREDIT_CARD,
                customer_email="teste.falha@puc-campinas.edu.br",
                simulate_failure=True,
            )
        )
    except Exception as exc:
        print(f"   [!] Falha esperada registrada: {exc}")

    print(f"   Estado do Circuit Breaker após atingir o limite: {shared_circuit_breaker.state.value}")

    print("\n3. Terceira chamada imediata: Circuit Breaker em ação (Fail-Fast sem retry)...")
    try:
        process_payment_uc.execute(
            ProcessPaymentInputDTO(
                order_id=fail_order.order_id,
                payment_method=PaymentMethod.CREDIT_CARD,
                customer_email="teste.falha@puc-campinas.edu.br",
            )
        )
    except CircuitBreakerOpenError as exc:
        print(f"   [PROTEÇÃO ATIVADA] Chamada bloqueada na borda: {exc}")

    print(f"\n4. Aguardando recuperação automática ({shared_circuit_breaker.recovery_timeout_seconds}s)...")
    time.sleep(shared_circuit_breaker.recovery_timeout_seconds + 0.1)
    print(f"   Estado após timeout de recuperação: {shared_circuit_breaker.state.value} (Pronto para teste de recuperação)")

    print("\n5. Chamada de teste bem-sucedida em HALF-OPEN...")
    recovery_output = process_payment_uc.execute(
        ProcessPaymentInputDTO(
            order_id=fail_order.order_id,
            payment_method=PaymentMethod.PIX,
            customer_email="teste.falha@puc-campinas.edu.br",
            simulate_failure=False,
        )
    )
    print(f"   [RECUPERADO] Transação confirmada: {recovery_output.transaction_id}")
    print(f"   Estado final do Circuit Breaker: {shared_circuit_breaker.state.value}")

    print_banner("DEMONSTRAÇÃO CONCLUÍDA COM 100% DE SUCESSO!")


if __name__ == "__main__":
    main()
