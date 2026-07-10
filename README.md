# BPT: Behavior Parallel Tree

O BPT sao duas arvores espelhadas de comportamentos, onde cada comportamento e uma ilha isolada que um agente constroi em paralelo, porque a arvore declara nos, dependencias e o contrato neutro que liga backend e frontend, com um unico objetivo: minimizar o contexto necessario para fazer uma mudanca.

Este repositorio e um template. A ideia e clona-lo a cada projeto novo, apagar os dois nos de exemplo e comecar a declarar os seus comportamentos. O nucleo e agnostico de stack: nao conhece linguagem, framework nem runtime. Quem executa o trabalho de verdade e um adapter, escolhido por projeto.

## Clone and go

Pre-requisitos: apenas Python 3 com PyYAML, e so para o validador de tooling. Isso nao e a stack do seu app: e a ferramenta que confere se a arvore esta coerente.

```bash
pip install pyyaml
./bpt validate
```

Saida esperada: o validador deriva as ondas de paralelismo (a ordem topologica que o adapter vai percorrer) e confirma as 7 invariantes.

```
bpt validate: /caminho/do/projeto
ondas de paralelismo (o adapter percorre nesta ordem):
  onda 1: produto.listar
  onda 2: produto.detalhar

ok: bpt.config.yaml e a arvore passaram nas 7 invariantes (0 aviso(s))
```

## Arvore de pastas

```
bpt.config.yaml              declaracao unica: sides, contratos e nos
bpt                          atalho para ./bpt validate
apps/
  backend/
    behaviors/               os nos do lado backend (raiz declarada em sides)
    kernel/                  infra transversal do backend (auth, db, config, app-shell)
  frontend/
    behaviors/               os nos do lado frontend
    kernel/                  infra transversal do frontend (+ design-system)
packages/
  contracts/                 um contrato + uma spec por comportamento
adapters/
  placeholder/               adapter de exemplo (so faz scaffold de verdade)
tools/
  bpt/validate.py            o validador (tooling swappable, nao a stack do app)
docs/                        o rulebook e o guia de contribuicao
```

Dentro de cada no ha `src/` (codigo humano) e `__generated__/` (codigo materializado pelo adapter a partir do contrato). Nao existe arquivo de metadado por no: a pasta na convencao mais a entrada no `bpt.config.yaml` ja sao a declaracao.

## O exemplo

O template nasce com 2 nos reais, os dois espelhados em backend e frontend:

- `produto.listar`: sem dependencias. Contrato em `packages/contracts/produto/listar/contract.yaml`, spec em `packages/contracts/produto/listar/spec.md`.
- `produto.detalhar`: depende de `produto.listar` (por isso cai na onda 2). Contrato e spec em `packages/contracts/produto/detalhar/`.

O codigo de cada no vive em `apps/backend/behaviors/produto/<acao>/` e `apps/frontend/behaviors/produto/<acao>/`. A spec fica ao lado do contrato, uma so, nunca duplicada por lado.

## Docs

- `docs/RULEBOOK.md`: o rulebook agnostico. Topologia espelhada, formas canonicas de id e caminho, contrato neutro, kernel, testes e exemplos avancados.
- `docs/CONTRIBUTING.md`: como adicionar um comportamento passo a passo.

## Como adicionar um comportamento

Em resumo: escolha o id no formato `dominio.acao`, crie a pasta do contrato mais a spec, declare o no em `bpt.config.yaml` (com `sides` e `deps`), rode `./bpt validate` e deixe o adapter construir. O passo a passo completo esta em `docs/CONTRIBUTING.md`.

## Sobre o adapter

O nucleo declara (arvore, espelho, contrato, spec); o adapter executa (worktrees, paralelismo, loop). O adapter incluido aqui e um placeholder: ele so faz o scaffold de verdade (cria as pastas espelhadas e os stubs a partir da spec). Os demais hooks retornam status ok vazio.

Um adapter real, escrito para a sua stack, e que vai rodar `plan`, `execute`, `verify`, `review` e `codegen`: planejar, implementar so nas pastas do no, rodar os cenarios da superficie e checar a direcao dos imports, revisar e materializar o contrato neutro em tipos e validadores da stack.
