# Migração

Este documento cobre duas operações de migração no BPT:

1. Renomear o id de um comportamento.
2. Adotar BPT num código que já existe (visão geral do caminho incremental, estilo strangler).

Nenhuma das duas depende de tooling automático. No v1 o BPT declara e valida; mover pastas e reescrever referências é trabalho manual (ou do seu adapter, se você escrever um). O único automático aqui é `./bpt validate`, que reprova se algo ficou inconsistente.

---

## Renomear um id

O id é a identidade do comportamento. Ele aparece na convenção de pastas (`apps/<lado>/behaviors/<caminho>/`), no caminho do contrato (`packages/contracts/<caminho>/`), no `bpt.config.yaml` e em todo `deps`/`consumes` que aponta para ele. Por isso, na prática, o id é imutável: não existe operação "renomear". O que existe é mover tudo que carrega aquele id para o id novo, de uma vez, e validar.

Exemplo: renomear `produto.listar` para `catalogo.listar`.

Lembre das formas canônicas antes de começar:

- id: `dominio.acao`, minúsculo, ponto separa segmentos, hífen só em composto, 2 a 3 segmentos.
- caminho: o ponto vira barra, então `catalogo.listar` mora em `catalogo/listar`.

### Passo a passo

1. **Mover as pastas de behaviors nos dois lados.**
   O mesmo comportamento existe em cada lado com a mesma identidade, então os dois se movem juntos:
   - `apps/backend/behaviors/produto/listar/` vira `apps/backend/behaviors/catalogo/listar/`
   - `apps/frontend/behaviors/produto/listar/` vira `apps/frontend/behaviors/catalogo/listar/`

   Leve o conteúdo inteiro do nó (a pasta `src/` com o código humano e, se existir, `__generated__/`). O `__generated__/` pode ser regenerado depois pelo hook `codegen` do adapter, então não é problema se ele ficar para trás.

2. **Mover a pasta em `packages/contracts`.**
   `packages/contracts/produto/listar/` vira `packages/contracts/catalogo/listar/`. Isso carrega junto o `contract.yaml` e o `spec.md` (a spec é única, ao lado do contrato, nunca duplicada por lado).

3. **Atualizar o campo `id` dentro do contrato.**
   Em `packages/contracts/catalogo/listar/contract.yaml`, o `id` deixa de ser `produto.listar` e passa a ser `catalogo.listar`. Ajuste também o `id` no front-matter do `spec.md` e o campo `contract` da spec (que aponta para o caminho, agora `catalogo/listar`).

4. **Atualizar o `bpt.config.yaml`.**
   Troque a entrada do nó em `nodes`: o id `produto.listar` passa a `catalogo.listar`. O bloco `sides` do nó continua igual (a topologia espelhada não mudou).

5. **Atualizar todos os `deps` e `consumes` que apontam para o id antigo.**
   Este é o passo que mais escapa. Procure `produto.listar` em:
   - `deps` de outros nós no `bpt.config.yaml` (por exemplo, `produto.detalhar` depende de `produto.listar` e precisa passar a depender de `catalogo.listar`).
   - `consumes` no front-matter de outras `spec.md` (uma tela composta que consome este contrato).
   - `deps` por lado, quando o grafo diverge (a forma `deps {backend [...], frontend [...]}`): olhe os dois lados.

   Lembre que `deps` e `consumes` referenciam pelo id, não pelo caminho de arquivo. Todo lugar que escrevia `produto.listar` passa a escrever `catalogo.listar`.

6. **Rodar o validador.**
   ```
   ./bpt validate
   ```
   Ele reprova se algo ficou pela metade. Os invariantes que mais pegam erro de rename:
   - **id único e no formato `dominio.acao`**: pega o caso de você ter renomeado o config mas não a pasta, ou vice-versa.
   - **refs de `deps`/`consumes` existem**: pega o `deps` órfão que ainda aponta para `produto.listar`.
   - **grafo acíclico**: pega o caso raro de o rename ter criado um ciclo (o Kahn aponta onde).
   - **trio de arquivos existe** (contract + spec + pasta por lado): pega a pasta que você esqueceu de mover num dos lados.

   Só considere o rename pronto quando `./bpt validate` passa limpo.

### O que NÃO fazer

- Não deixe o id antigo e o novo convivendo. Não existe alias nem redirecionamento de id no v1. É corte seco.
- Não renomeie só um lado. O comportamento tem a mesma identidade nos dois lados; um lado sem o outro quebra o invariante do trio de arquivos e o espelho.
- Não edite `__generated__/` na mão para "consertar" o id. Isso é território do `codegen`; regenere.

---

## Adotar BPT num código existente

O caminho é incremental, no estilo strangler: você não reescreve o sistema. Você desenha a fronteira BPT em volta do que já existe e vai puxando pedaço por pedaço para dentro dela, enquanto o legado continua rodando atrás do kernel.

> O guia completo de brownfield (adoção em larga escala, estrangulamento sistemático, convivência de versões) é trabalho futuro, fora do v1. O que está aqui é a visão geral do caminho, o suficiente para começar sem se pintar num canto.

### A ideia em uma frase

Trate o sistema legado como infraestrutura transversal (kernel) e vá extraindo comportamentos visíveis para a árvore, um de cada vez, cada um com contrato próprio.

### Passos da adoção

1. **Identificar os comportamentos visíveis.**
   Um comportamento é uma ação de domínio com resultado observável, do ponto de vista de quem usa o sistema: "listar produtos", "detalhar produto", "filtrar catálogo". Não olhe para a estrutura interna do legado (classes, tabelas, serviços); olhe para as superfícies (telas, endpoints, comandos, jobs) e pergunte que ação cada uma entrega. Cada ação candidata vira um id na forma `dominio.acao`.

2. **Criar contratos para as fronteiras que já existem.**
   Para cada comportamento identificado, escreva um `contract.yaml` que descreva a fronteira como ela é hoje: `input`, `output`, `errors`, `rules`, com os tipos neutros (`text`, `integer`, `decimal`, `boolean`, `money`, `list`, `object`). Você está documentando o contrato real do que o legado já faz, não inventando um novo. Escreva a `spec.md` ao lado, com os cenários por superfície. Comece pelas fronteiras mais estáveis e mais consumidas: elas dão o maior retorno de clareza.

3. **Mover uma tela (um comportamento) de cada vez.**
   Escolha um comportamento e traga o código para dentro das pastas do nó (`apps/<lado>/behaviors/<caminho>/src/`), respeitando a topologia espelhada: o backend e o frontend do mesmo comportamento ganham a mesma identidade e a mesma spec, ligados pelo contrato. Registre o nó no `bpt.config.yaml` com seus `sides` e `deps`. Rode `./bpt validate`. Só então passe para o próximo comportamento. Um comportamento por vez mantém o raio de mudança pequeno, que é o objetivo do BPT.

4. **Deixar o legado atrás do kernel.**
   Tudo que ainda não foi extraído continua existindo, mas o comportamento novo não fala direto com o legado espalhado: ele fala com o kernel do seu lado (infra transversal: auth, db, config, app-shell, design-system). O legado vira uma dependência transversal acessada pelo kernel. Isso respeita a regra de direção de import (comportamento importa do kernel, kernel nunca importa de comportamento) e mantém o legado isolado atrás de uma fronteira única, em vez de vazar para dentro de cada nó novo.

   À medida que mais comportamentos saem para a árvore, o legado atrás do kernel encolhe. Quando um pedaço do legado deixa de ser usado por qualquer comportamento, ele pode ser removido. É o estrangulamento: o novo cresce, o velho míngua.

### Ordem sugerida na prática

- Comece por um comportamento de leitura, simples e sem dependências (um `query` folha, como `produto.listar`). Menos risco, contrato mais fácil de acertar.
- Depois puxe os comportamentos que dependem dele, na ordem topológica (as ondas que o núcleo deriva). Assim os `deps` já apontam para nós que existem.
- Deixe os comportamentos de escrita e os fluxos que cruzam vários comportamentos para quando você já tiver confiança no formato dos contratos.

### O que esperar do v1

- **Sem migração automática.** Não há ferramenta que leia seu código legado e gere contratos ou mova pastas. O `./bpt validate` confere consistência depois que você fez o trabalho; ele não faz o trabalho.
- **Regra de negócio compartilhada vira dado, não código.** Se uma regra do legado precisa valer nos dois lados, ela vai para o bloco `rules` do contrato e cada lado a implementa, com teste bilateral. Não crie um pacote de domínio compartilhado durante a adoção; isso reintroduz o acoplamento global que o BPT existe para evitar.
- **O guia completo de brownfield é futuro.** Convivência de versões (N/N-1, expand/contract), registro central de contratos e orquestração real de extração estão fora do v1. Por enquanto, adoção é manual, incremental e validada a cada passo.
