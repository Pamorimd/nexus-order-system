# Nexus Order System

> **PUC-Campinas · Faculdade de Sistemas de Informação**  
> **Disciplina:** Projeto de Software com Arquitetura Justificada, SOLID, Clean Code e Padrões GoF (12452)  
> **Trabalho Final** · Semestre 2026-2

---

## 📌 O que é o Sistema?
O **Nexus Order System** é um motor moderno de processamento de pedidos, tarifação logística dinâmica, cálculo de descontos promocionais e liquidação financeira multigateway.

Construído sob o estilo **Monolito Modular** e estruturado internamente em **Arquitetura Hexagonal (Ports & Adapters)**, o sistema aplica rigorosamente os princípios **SOLID**, padrões de projeto **GoF** (*Strategy*, *State*, *Factory Method*) e o padrão transversal de **Resiliência** (*Circuit Breaker* com *Retries e Exponential Backoff*), garantindo tolerância a falhas na comunicação com adquirentes e bancos externos.

---

## 👥 Integrantes do Grupo
* **Priscila Amorim dos Santos** — RA: `24787350` — `priscilaa.amorin@outlook.com` (Líder / Arquitetura do Domínio e Resiliência)
* **Enrico Colella** — `colellaenrico0@gmail.com` (Portas Hexagonais, Repositório e GoF Factory Method)
* **Jhonatan Decreci** — `jhonatandecrecims@gmail.com` (Padrão GoF Strategy, Casos de Uso e CLI)
* **Bransani** — `bransani88@gmail.com` (Padrão GoF State e Ciclo de Vida do Pedido)

---

## 🗺️ Mapa da Documentação Técnica
Toda a documentação do projeto está versionada em Markdown no repositório, com diagramas renderizados nativamente em Mermaid:

| Documento | Conteúdo e Justificativas |
| :--- | :--- |
| [`docs/1-contexto.md`](docs/1-contexto.md) | Problema que o sistema resolve, público-alvo, escopo detalhado e Regra de Ouro. |
| [`docs/2-qualidade.md`](docs/2-qualidade.md) | 3 Atributos de Qualidade (ISO/IEC 25010:2023), medidas observáveis e trade-off assumido. |
| [`docs/3-arquitetura.md`](docs/3-arquitetura.md) | Estilo macro (Monolito Modular) e interno (Hexagonal), 2 estilos descartados, Diagramas C4 (Contexto, Contêineres, Componentes) e Diagrama de Sequência. |
| [`docs/4-solid.md`](docs/4-solid.md) | Os 5 princípios SOLID comprovados com trechos de código e efeitos na arquitetura. |
| [`docs/5-clean-code.md`](docs/5-clean-code.md) | Nomes claros, funções coesas, DRY, tratamento explícito de erros, configuração do linter Ruff e testes. |
| [`docs/6-gof.md`](docs/6-gof.md) | 3 Padrões GoF (Strategy, State, Factory Method) com problemas reais, código e diagramas de classes. |
| [`docs/7-transversal.md`](docs/7-transversal.md) | Padrão Transversal de Resiliência (Circuit Breaker, Retries com Backoff e Timeout). |
| [`docs/8-conclusao.md`](docs/8-conclusao.md) | O que funcionou, desafios, o que faríamos diferente e referências bibliográficas completas. |

### Registros de Decisão de Arquitetura (ADRs)
* [`adrs/0001-estrutura-macro-monolito-modular.md`](adrs/0001-estrutura-macro-monolito-modular.md)
* [`adrs/0002-organizacao-interna-arquitetura-hexagonal.md`](adrs/0002-organizacao-interna-arquitetura-hexagonal.md)
* [`adrs/0003-persistencia-dados-repositorio.md`](adrs/0003-persistencia-dados-repositorio.md)
* [`adrs/0004-implantacao-containerizada-docker.md`](adrs/0004-implantacao-containerizada-docker.md)
* [`adrs/0005-integracao-sincrona-gateway-pagamento.md`](adrs/0005-integracao-sincrona-gateway-pagamento.md) *(Substituído pelo ADR-0006)*
* [`adrs/0006-resiliencia-circuit-breaker-e-retries-gateway.md`](adrs/0006-resiliencia-circuit-breaker-e-retries-gateway.md) *(Substitui o ADR-0005)*

---

## 🚀 Como Instalar e Rodar

### Pré-requisitos
* Python 3.10+ instalado no sistema (ou Docker).
* Git configurado.

### Opção 1: Execução Local (Ambiente Python)

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/Pamorimd/nexus-order-system.git
   cd nexus-order-system
   ```

2. **Crie e ative o ambiente virtual:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # No Linux/macOS
   # ou .venv\Scripts\activate no Windows
   ```

3. **Instale as dependências de desenvolvimento (Linter e Testes):**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Execute a demonstração interativa do sistema (CLI):**
   ```bash
   python src/nexus/adapters/entrypoints/cli.py
   ```

---

### Opção 2: Execução Containerizada via Docker

Para rodar todo o sistema e testes em contêiner isolado sem instalar nada localmente:

```bash
docker compose up --build
```

---

## 🧪 Como Executar a Suíte de Testes Automatizados

O sistema conta com 37 testes automatizados cobrindo invariantes de negócio, padrões de projeto e tolerância a falhas.

```bash
# Execução com Pytest:
pytest -v

# Ou execução nativa (zero dependências extras):
python3 -m unittest discover -s tests -v
```

---

## 🔍 Como Executar o Linter e Formatador (Ruff)

Conforme a especificação do trabalho para Python, o repositório é validado pelo **Ruff**:

```bash
# 1. Checagem estática de código (erros, imports e boas práticas PEP 8)
ruff check .

# 2. Verificação de formatação de código
ruff format . --check
```

---

## ⚙️ Integração Contínua (CI) e Governança do Repositório
* **Proteção do Ramo `main`:** Mudanças são integradas exclusivamente através de Pull Requests.
* **Template Padronizado de PR:** Versionado em [`.github/pull_request_template.md`](.github/pull_request_template.md).
* **Pipeline Automatizado de CI:** Configurado em [`.github/workflows/ci.yml`](.github/workflows/ci.yml), executando `ruff check`, `ruff format` e `pytest` em cada PR e push no `main`.
