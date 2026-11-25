# ADR 0001: Adoção do Estilo Arquitetural Monolito Modular no Plano Macro

## Status
Aceito

## Contexto
O sistema **Nexus Order System** tem como objetivo central orquestrar o ciclo de vida de pedidos comerciais, cálculos tarifários de frete, aplicação de regras de desconto e liquidação financeira multigateway. O domínio requer consistência transacional imediata entre a atualização de estoque, confirmação de pagamento e emissão de autorização de frete. A equipe de desenvolvimento é enxuta e o volume de requisições projetado pode ser plenamente atendido por um único processo executando de forma otimizada.

## Decisão
Decidimos adotar o estilo arquitetural **Monolito Modular** (Capítulo 5 do livro da disciplina) como o plano macro da solução, empacotando todo o ciclo de vida do pedido dentro de uma única base de código e unidade de implantação, dividida estritamente em módulos com fronteiras bem delimitadas.

## Alternativas Consideradas e Motivos de Descarte
1. **Microsserviços (Capítulo 7):**
   * *Motivo do descarte:* Introduziria complexidade operacional prematura e custos reais ocultos (latência de rede inter-serviços, necessidade de transações distribuídas via padrão Saga, observabilidade distribuída complexa e sobrecarga de infraestrutura), injustificáveis para o escopo e o tamanho da equipe.
2. **Serverless / FaaS orientada a Eventos (Capítulo 9):**
   * *Motivo do descarte:* Causaria problema de "cold start" crítico em rotas de checkout de alta conversão, além de dificultar testes automatizados locais integrados sem emuladores em nuvem.

## Consequências
### Positivas
* **Simplicidade de Implantação e Operação:** Um único artefato de execução, reduzindo drasticamente o pipeline de CI/CD.
* **Desempenho e Consistência:** Comunicação entre módulos por chamadas de função locais em memória, eliminando latência de rede e serialização/desserialização JSON entre subsistemas.
* **Facilidade de Refatoração:** Ajustes de contratos e entidades de domínio ocorrem com verificação estática de tipos, sem quebra de contratos de rede remotos.

### Negativas
* **Escalabilidade em Bloco:** Caso a demanda por cálculo de frete aumente muito além da liquidação de pagamentos, toda a aplicação deve ser escalada horizontalmente em conjunto.
* **Risco de Acoplamento Acidental:** Exige disciplina estrita da equipe para não violar as fronteiras de módulos (mitigado pelo linter e arquitetura hexagonal).

## Pull Request
Implementado via Pull Request [#1](https://github.com/Pamorimd/nexus-order-system/pull/1) (`feat/domain-model-and-entities`), que cria o núcleo do monolito. A estrutura inicial do repositório entrou antes dos PRs, no commit de scaffold `287a995`.
