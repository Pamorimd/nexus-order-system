# 8. Conclusão e Lições Aprendidas

## 8.1 O que Funcionou
* **Arquitetura Hexagonal com Ports & Adapters:** A separação estrita do núcleo de domínio em relação à infraestrutura permitiu construir e testar 100% da lógica de negócio, dos cálculos de frete e da máquina de estados sem levantar contêineres de banco de dados ou mockar servidores HTTP pesados. A suíte inteira de 37 testes automatizados executa em menos de meio segundo.
* **Padrões GoF Resolvendo Problemas Reais:** 
  * O padrão **Strategy** eliminou code smells de condicionais complexas nas taxas de frete.
  * O padrão **State** garantiu a inviolabilidade das regras de negócio do ciclo de vida do pedido (impossível despachar pedidos não pagos ou cancelar pedidos já entregues).
  * O padrão **Factory Method** centralizou a instanciação e o envelopamento transparente dos adaptadores de pagamento com resiliência.
* **Padrão Transversal de Resiliência:** A combinação de Circuit Breaker com Retry e Exponential Backoff protegeu a aplicação contra quedas e latências em serviços bancários externos, permitindo fail-fast instantâneo.
* **Governança de Código com Ruff:** A configuração rígida do linter e formatador no arquivo `pyproject.toml` assegurou conformidade total com o guia de estilo PEP 8 e tipagem estática moderna.

---

## 8.2 O que Não Funcionou e Desafios Encontrados
* **Sobrecarga Inicial de Boilerplate:** No início do desenvolvimento, a criação de interfaces de portas, objetos de valor (`Money`, `Address`) e mappers DTO gerou uma sensação de lentidão na entrega comparada à escrita de um script direto. Essa disciplina, no entanto, pagou-se rapidamente assim que iniciamos a escrita dos testes unitários e a expansão de novos gateways.
* **Disciplina de Limites do Domínio:** Evitar que preocupações de serialização de saída (como formatação de strings de moeda ou data) vazassem para dentro da entidade `Order` exigiu revisões cuidadosas para manter o princípio SRP.

---

## 8.3 O que Faríamos Diferente
* **Barramento de Eventos de Domínio (Event-Driven):** Em uma evolução futura, as transições de estado do pedido (ex: `OrderPaidEvent`, `OrderShippedEvent`) publicariam eventos em um *Domain Event Bus* local ou RabbitMQ, permitindo que módulos secundários (como disparo de e-mails transacionais e atualização de analytics) reagissem de forma assíncrona sem acoplar os casos de uso.
* **Implementação de Repositório SQLite Relacional:** Além do repositório em memória de alta performance para testes, poderíamos ter implementado um adaptador secundário baseado em SQLite nativo para persistência permanente em disco.

---

## 8.4 Referências Bibliográficas

1. **Livro-Texto da Disciplina:**
   * Autor / Coordenação: PUC-Campinas.
   * Título: *Arquitetura de Software: Padrões, Decisões e Estilos Arquiteturais*.
   * Ano: 2026.
   * Capítulos Utilizados: Cap. 2 (Atributos de Qualidade e Trade-offs ISO/IEC 25010), Cap. 3 e Apêndice B.4 (Modelagem C4 e Diagramas Mermaid), Cap. 4 (Registros de Decisão de Arquitetura - ADR), Cap. 5 (Monolitos Modulares), Cap. 6 (Arquitetura Hexagonal e Clean), Cap. 18.4 (Resiliência: Timeout, Retry e Circuit Breaker).

2. **Refactoring Guru:**
   * Autor: SHVETS, Alexander.
   * Título: *Design Patterns: Padrões de Projeto Explicados de Forma Clara e Visual*.
   * Ano: 2024.
   * Links Oficiais:
     * [Padrão Strategy](https://refactoring.guru/pt-br/design-patterns/strategy)
     * [Padrão State](https://refactoring.guru/pt-br/design-patterns/state)
     * [Padrão Factory Method](https://refactoring.guru/pt-br/design-patterns/factory-method)
     * [Catálogo de Code Smells](https://refactoring.guru/pt-br/refactoring/smells)

3. **Arquitetura Limpa e Princípios SOLID:**
   * Autor: MARTIN, Robert C.
   * Título: *Clean Architecture: A Craftsman's Guide to Software Structure and Design*.
   * Editora: Prentice Hall, 2017.

4. **Arquitetura Hexagonal (Ports & Adapters):**
   * Autor: COCKBURN, Alistair.
   * Título: *Hexagonal Architecture (Ports and Adapters Pattern)*.
   * Ano: 2005.
   * Link: [https://alistair.cockburn.us/hexagonal-architecture/](https://alistair.cockburn.us/hexagonal-architecture/)

5. **Norma Internacional de Qualidade de Produto de Software:**
   * Organização: ISO/IEC.
   * Norma: *ISO/IEC 25010:2023 - Systems and software engineering — Systems and software Quality Requirements and Evaluation (SQRE) — Product quality model*.
   * Ano: 2023.
