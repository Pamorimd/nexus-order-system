# ADR 0004: Estratégia de Implantação e Execução Containerizada com Docker

## Status
Aceito

## Contexto
O software precisa rodar de forma determinística em múltiplos ambientes: máquinas dos integrantes da equipe, pipeline de Integração Contínua (GitHub Actions) e na máquina de avaliação do professor da disciplina. Variações de versões do interpretador Python, dependências de sistema operacional e caminhos locais costumam provocar o problema clássico "na minha máquina funciona".

## Decisão
Decidimos padronizar a execução e implantação da aplicação através de contêineres Docker, fornecendo um `Dockerfile` baseado em imagem oficial `python:3.10-slim` e um manifesto `docker-compose.yml` para orquestração de desenvolvimento.

## Alternativas Consideradas e Motivos de Descarte
1. **Instalação Manual Bare-Metal via Virtualenv Local:**
   * *Motivo do descarte:* Deixa a execução vulnerável a incompatibilidades de pacotes do sistema operacional dos desenvolvedores e exige documentação extensa de pré-requisitos.
2. **Implantação em Kubernetes (K8s) com Helm Charts:**
   * *Motivo do descarte:* Superdimensionamento para um monolito modular; traria esforço desnecessário de manutenção de manifestos de pods e ingress.

## Consequências
### Positivas
* **Reprodutibilidade Garantida:** A imagem Docker empacota o código fonte, interpretador Python 3.10, linter e dependências com hash fixo.
* **Execução com Comando Único:** Qualquer avaliador pode executar o sistema completo rodando apenas `docker compose up --build`.
* **Ambiente Limpo:** Não polui o sistema operacional do host com pacotes ou variáveis globais.

### Negativas
* **Requisito de Instalação do Docker Daemon:** A máquina que executar o contêiner precisa do Docker e Docker Compose previamente instalados.

## Pull Request
Implementado via Pull Request [#4](https://github.com/Pamorimd/nexus-order-system/pull/4) (feat/dockerfile-and-compose-configuration).
