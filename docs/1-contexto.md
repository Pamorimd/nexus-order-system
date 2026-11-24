# 1. Contexto do Sistema

## 1.1 O Problema e o Público-Alvo
No comércio eletrônico moderno e nas plataformas de serviços B2B/B2C, o processo de checkout é a etapa mais sensível do negócio. Falhas de tarifação de frete, regras confusas de desconto ou lentidão e instabilidade na comunicação com gateways bancários (como arranjo Pix, adquirentes de cartão e CIP para boletos) resultam em perda imediata de conversão, transações duplicadas e insatisfação do cliente.

O **Nexus Order System** é um motor especializado de processamento de pedidos, tarifação logística dinâmica, cálculo de descontos e liquidação financeira multigateway resiliente a falhas. 

O público-alvo são **plataformas de comércio eletrônico, marketplaces e empresas de venda direta** que necessitam de um núcleo de pedidos desacoplado de interfaces visuais, altamente manutenível e imune a falhas em cascata de provedores externos.

---

## 1.2 Escopo do Sistema

### O que entra no escopo (In-Scope):
* **Composição e Invariantes do Pedido:** Criação de pedidos com validação de itens, quantidades positivas e encapsulamento monetário com precisão decimal (`Money`).
* **Tarifação Logística Dinâmica:** Cálculo automatizado de prazos e valores de frete por faixa de peso e região através de múltiplas estratégias (`CORREIOS_SEDEX`, `CORREIOS_PAC`, `TRANSPORTADORA_EXPRESS`).
* **Políticas Promocionais de Desconto:** Aplicação de cupons percentuais e descontos automáticos por modalidade de pagamento.
* **Máquina de Estados Finita do Ciclo de Vida:** Orquestração estrita das transições entre estados (`PENDING_PAYMENT` $\to$ `PAID` $\to$ `SHIPPED` ou `CANCELLED`), impedindo transições ilegais na raiz do domínio.
* **Liquidação Multigateway Resiliente:** Processamento de pagamentos via Pix, Cartão de Crédito e Boleto Bancário com proteção por *Circuit Breaker* e *Retry com Exponential Backoff*.
* **Interface de Operação:** Ponto de entrada CLI completo e executável para testes e demonstrações de ponta a ponta.

### O que fica de fora do escopo (Out-of-Scope):
* **Interface Gráfica de Loja Virtual (Storefront):** O sistema é projetado como um motor de regras de negócio de backend/CLI, sem renderização de páginas HTML de vitrine.
* **Sistema Físico de Gestão de Armazém (WMS):** A separação e embalagem física de produtos nos centros de distribuição são representadas apenas pelos eventos de transição de status.
* **Emissão Fiscal Real de NF-e:** A integração com a Secretaria da Fazenda (SEFAZ) para assinatura digital de notas fiscais foi simplificada para os códigos de autorização do pedido.

---

## 1.3 Regra de Ouro da Documentação
> **REGRA DE OURO:** Cada afirmação desta documentação técnica aponta diretamente para o trecho de código que a prova no repositório.

Exemplo de verificação no código:
A validação de que um pedido não pode ser criado vazio ou com valores negativos encontra-se implementada nas invariantes da entidade:
```python
# Trecho de src/nexus/domain/entities.py
if not items:
    raise EmptyOrderError("Não é permitido criar um pedido sem itens.")
```
Link permanente no repositório: [`src/nexus/domain/entities.py#L65-L67`](https://github.com/Pamorimd/nexus-order-system/blob/main/src/nexus/domain/entities.py#L65-L67)
