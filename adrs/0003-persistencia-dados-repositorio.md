# ADR 0003: Estratégia de Persistência via Padrão Repository e Armazenamento Desacoplado

## Status
Aceito

## Contexto
O agregado `Order` precisa ser salvo e consultado durante as transições de seu ciclo de vida. Amarrar a camada de aplicação diretamente a queries SQL ou dependências pesadas de ORMs (como SQLAlchemy ou Django ORM) criaria lentidão na suíte de testes unitários e acoplamento a um banco de dados relacional específico.

## Decisão
Decidimos implementar o padrão **Repository** por meio da porta abstrata `OrderRepositoryPort` no domínio, com um adaptador inicial de alto desempenho `InMemoryOrderRepository` (dicionário thread-safe em memória com deep copy conceitual), projetado para ser substituível por adaptadores SQLite ou PostgreSQL sem qualquer impacto sobre os Casos de Uso.

## Alternativas Consideradas e Motivos de Descarte
1. **Active Record (ORM onde a entidade herda de Model):**
   * *Motivo do descarte:* Viola frontalmente o Princípio de Responsabilidade Única (SRP) e o Princípio de Inversão de Dependência (DIP), pois a entidade de negócio passa a carregar métodos de persistência (`order.save()`, `order.objects.filter()`).
2. **Banco NoSQL Orientado a Documentos (ex: MongoDB nativo):**
   * *Motivo do descarte:* Introduziria um serviço externo adicional de banco no ambiente local e no pipeline de CI desnecessariamente para a fase atual do projeto.

## Consequências
### Positivas
* **Execução Instantânea de Testes:** A suíte de 37 testes automatizados roda em menos de 0.5 segundo, sem necessidade de levantar contêineres de banco de dados.
* **Isolamento de Domínio:** A entidade `Order` não herda de nenhuma superclasse de banco e permanece um objeto Python puro.
* **Extensibilidade:** Para plugar PostgreSQL em produção, basta criar `SqliteOrderRepository` implementando a mesma interface `OrderRepositoryPort`.

### Negativas
* **Volatilidade no Adaptador em Memória:** Os dados são reiniciados a cada execução do processo no ambiente de demonstração CLI (comportamento desejável para testes e demonstrações isoladas).

## Pull Request
Implementado via Pull Request [#3](https://github.com/Pamorimd/nexus-order-system/pull/3) (feat/repository-port-and-memory-adapter).
