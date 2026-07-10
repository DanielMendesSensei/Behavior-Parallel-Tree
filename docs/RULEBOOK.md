# BPT Rulebook

O documento mestre do Behavior Parallel Tree (BPT). Aqui estao a visao geral, os principios, as formas canonicas e o mapa do template. Para o detalhe de cada parte, consulte os docs especificos apontados ao longo do texto.

## BPT em uma frase

Duas arvores espelhadas de comportamentos, onde cada comportamento e uma ilha isolada que um agente constroi em paralelo, porque a arvore declara nos, dependencias e o contrato neutro que liga backend e frontend, com um unico objetivo: minimizar o contexto necessario para fazer uma mudanca.

## O que e o BPT

O BPT e uma arquitetura de software agnostica de stack. Ele nao conhece linguagem, framework nem runtime. O que ele define e uma forma de organizar o codigo em torno de comportamentos, de modo que:

- cada comportamento seja uma unidade isolada, com fronteiras claras;
- o mesmo comportamento exista dos dois lados (backend e frontend) com a mesma identidade, ligado por um contrato neutro;
- um agente (humano ou automatizado) consiga trabalhar em um comportamento carregando o minimo de contexto possivel;
- os comportamentos independentes possam ser construidos em paralelo, respeitando um grafo de dependencias.

O nucleo do BPT apenas declara (arvore, espelho, contrato, spec). Quem executa (worktrees, paralelismo, loop de construcao) e um adapter especifico de stack. O template nasce com 1 adapter placeholder e um validador minimo.

## Os 8 principios

1. Contexto minimo por mudanca. Toda decisao de arquitetura serve a esta meta: para mudar um comportamento, voce carrega o comportamento, seu contrato e o kernel. Nada mais.
2. Comportamento e a unidade atomica. Nao se pensa em camadas nem em modulos tecnicos. Pensa-se em comportamentos observaveis (produto.listar, produto.detalhar). Tudo que um comportamento precisa mora junto dele.
3. Outside-in. Comeca pela superficie e pelo resultado observavel (a spec), depois o contrato, depois a implementacao de cada lado. O que o usuario percebe vem antes do como.
4. Arvores espelhadas por identidade, junta por contrato. Backend e frontend sao arvores separadas. O mesmo comportamento existe nos dois lados com a mesma identidade e a mesma spec. A junta entre eles e um contrato neutro. O espelho e N:M via contrato, nao um acoplamento 1:1 rigido.
5. Comportamentos sao ilhas. Um comportamento nao importa de outro comportamento. Se dois comportamentos precisam de algo em comum, ou vira dependencia declarada via contrato, ou sobe para o kernel. Ilha nao fala com ilha direto.
6. Duplique antes de abstrair. Regra do tres: o codigo nasce no comportamento, e copiado na 2a ocorrencia, e so sobe para o kernel na 3a. Abstracao precoce e o maior inimigo do contexto minimo.
7. Core declara, adapter executa. O nucleo do BPT declara a estrutura (arvore, espelho, contrato, spec) e valida invariantes. O adapter da stack executa (cria worktrees, roda o loop de construcao, gera codigo). A fronteira entre os dois e um protocolo neutro de hooks.
8. Uma forma canonica so. Cada coisa tem uma unica forma de ser escrita: um id, um caminho, um lugar para a spec, um lugar para o contrato. Sem sinonimos, sem variantes. A convencao e a documentacao.

## Formas canonicas

Uma so forma, valida em todo o template.

| Item | Forma canonica |
| --- | --- |
| id | `dominio.acao` (minusculo, ponto separa segmentos, hifen em composto), 2 a 3 segmentos, prefira 2 |
| caminho | o ponto vira barra: `produto.listar` vira `produto/listar` |
| raiz de comportamentos | `apps/<lado>/behaviors/<caminho>/` |
| contrato | `packages/contracts/<caminho>/contract.yaml` |
| spec | `packages/contracts/<caminho>/spec.md` (uma so, ao lado do contrato, nunca duplicada por lado) |
| config | `bpt.config.yaml` (arquivo unico na raiz) |
| codigo humano | `src/` dentro do no |
| codigo gerado | `__generated__/` dentro do no (o adapter preenche) |

Nao existe arquivo de metadado por no. A pasta na convencao mais a entrada no `bpt.config.yaml` ja sao a declaracao do no.

Detalhe completo em [NAMING.md](./NAMING.md).

## Estrutura do monorepo

Um unico monorepo. As duas arvores de comportamento vivem sob `apps/`, os contratos e specs vivem sob `packages/contracts/`, e a config na raiz.

```
meu-app/
  bpt.config.yaml
  apps/
    backend/
      kernel/                         infra transversal do backend
      behaviors/
        produto/
          listar/
            src/                       codigo humano
            __generated__/             codigo gerado pelo adapter
          detalhar/
            src/
            __generated__/
    frontend/
      kernel/                         infra transversal do frontend
      behaviors/
        produto/
          listar/
            src/
            __generated__/
          detalhar/
            src/
            __generated__/
  packages/
    contracts/
      produto/
        listar/
          contract.yaml                contrato neutro
          spec.md                      spec unica, os dois lados
        detalhar/
          contract.yaml
          spec.md
      _flows/                          testes de fluxo/e2e por PRD
  tools/
    bpt/
      validate.py                      validador minimo (Python 3 + PyYAML)
```

O mesmo comportamento (`produto.listar`) aparece em `apps/backend/behaviors/produto/listar/` e em `apps/frontend/behaviors/produto/listar/`, com um unico contrato e uma unica spec em `packages/contracts/produto/listar/`.

## O modelo de no

A unidade de execucao e o no por lado, chaveado em `(lado, id)`. Um no two-sided como `produto.listar` gera duas unidades de trabalho: `(backend, produto.listar)` e `(frontend, produto.listar)`.

Cada no e declarado no `bpt.config.yaml` com:

- `id`: a identidade canonica, unica no projeto.
- `sides`: em quais lados o comportamento existe (`sides` e uma lista aberta).
- `deps`: de quais outros comportamentos ele depende. Pode divergir por lado.

O `bpt.config.yaml` vivo nasce com dois nos reais:

```yaml
schema: bpt/v1
project: meu-app
adapter: placeholder
sides:
  backend:  { root: apps/backend/behaviors,  kernel: apps/backend/kernel }
  frontend: { root: apps/frontend/behaviors, kernel: apps/frontend/kernel }
contracts:
  root: packages/contracts
nodes:
  produto.listar:   { sides: [backend, frontend], deps: [] }
  produto.detalhar: { sides: [backend, frontend], deps: [produto.listar] }
```

O naming resumido: id em `dominio.acao`, 2 a 3 segmentos (prefira 2), minusculo, ponto separando segmentos, hifen dentro de um segmento composto. O caminho no disco troca ponto por barra. Regras completas em [NAMING.md](./NAMING.md).

Cada no two-sided precisa do trio: `contract.yaml`, `spec.md` e a pasta por lado. Formato da spec em [SPEC-FORMAT.md](./SPEC-FORMAT.md), formato do contrato em [CONTRACT-FORMAT.md](./CONTRACT-FORMAT.md).

## Kernel

O kernel e infra transversal por lado (auth, db, config, app-shell, design-system). Existe um kernel para o backend e um para o frontend.

A regra de ouro: comportamento importa do kernel, o kernel nunca importa de comportamento. E comportamento nunca importa de comportamento.

Regra de negocio compartilhada nao vira codigo de kernel: vira dado no bloco `rules` do contrato, e cada lado implementa. Um teste bilateral mantem os dois honestos.

Criterios de promocao ao kernel, regra do tres, anti-inchaco, dono por submodulo e enforcement de direcao de import estao em [KERNEL.md](./KERNEL.md).

## Validador

O template traz um validador minimo: `./bpt validate` (implementado em `tools/bpt/validate.py`, Python 3 mais PyYAML). O tooling e swappable e nao e a stack do app.

Ele roda 7 invariantes:

1. schema presente e suportado (`bpt/v1`);
2. id unico e no formato `dominio.acao`;
3. `sides` nao vazio e cada lado existe na config;
4. refs de `deps` e `consumes` existem, sem auto-dependencia, grafo aciclico (Kahn aponta o ciclo);
5. no two-sided tem contrato, no one-sided tem `contract: none`;
6. nenhum id sob pasta de kernel (o dominio `kernel` e reservado);
7. o trio de arquivos existe (contract, spec e a pasta por lado).

O nucleo tambem deriva as ondas de paralelismo por ordem topologica.

## Adapter

O adapter e um executavel declarado no `bpt.config.yaml`. Protocolo neutro: `bpt-adapter <hook>` le um JSON de stdin, escreve um JSON em stdout, logs em stderr. Exit 0 significa que rodou (o status vai no payload), exit diferente de 0 significa que o adapter quebrou.

Sao 6 hooks: `scaffold`, `plan`, `execute`, `verify`, `review`, `codegen`. O placeholder do template so faz `scaffold` de verdade; os outros retornam status ok vazio.

O protocolo completo, a orquestracao (worktree por no-por-lado, ondas do DAG, loop com ate 3 tentativas, teste bilateral, modo yolo) esta em [ADAPTER.md](./ADAPTER.md).

## Testes

Tres camadas:

- Cenario: testa comportamento observavel (contrato mais superficie), mora na `spec.md`, sobrevive a refactor, nunca cita nome de funcao ou tabela.
- Unitario: testa os internals (o como), mora ao lado do codigo, muda com o codigo.
- Fluxo/e2e: jornada atravessando N comportamentos, mora em `packages/contracts/_flows/<prd>/`, dono no nivel do PRD.

O `entao` do cenario e projetado por superficie: o `verify` do backend roda o contrato, o do frontend roda a tela. Revisao semantica e o portao depois do verde. Detalhe em [TESTING.md](./TESTING.md).

## Exemplos avancados

Estes exemplos documentam formas suportadas. Eles nao estao no `bpt.config.yaml` vivo, que so tem os dois nos reais.

### No one-sided

Um comportamento pode existir em um lado so. Ele nao tem contrato proprio, consome o de outro:

```yaml
catalogo.filtrar:
  sides: [frontend]
  contract: none
  consumes: [produto.listar]
  deps: [produto.listar]
```

### N:M via consumes

Uma tela composta consome N contratos declarando `consumes: [...]`. E um mesmo contrato pode servir N telas. O espelho e N:M, nao 1:1.

### Deps por lado

Quando o grafo de dependencias diverge entre os lados, `deps` vira um mapa por lado:

```yaml
checkout.pagar:
  sides: [backend, frontend]
  deps:
    backend:  [pagamento.cartao.autorizar]
    frontend: [carrinho.revisar]
  prd: checkout-v1
```

### PRD

Um no pode declarar `prd` para amarrar comportamentos a uma unidade de produto. Os testes de fluxo/e2e sao donos no nivel do PRD, sob `packages/contracts/_flows/<prd>/`.

### Superficies genericas

`sides` e uma lista aberta e a superficie de cada lado pode ser: `tela`, `comando-cli`, `endpoint`, `job` ou `evento`. Uma aplicacao de CLI, por exemplo, usaria `sides: [cli]`.

## Idioma

Idioma hibrido. As chaves estruturais de schema ficam em ingles (`kind`, `input`, `output`, `errors`, `sides`, `deps`, `rules`, e assim por diante). O vocabulario de dominio e os ids ficam em portugues (`produto.listar`, `busca`, `preco`, `PARAMETRO_INVALIDO`).

## Fora de escopo (v1)

O que fica de fora do v1, citado aqui como futuro:

- JSON Schema mais `$ref` mais codegen rico;
- hash canonico e registro central de contratos;
- semver mais convivencia N/N-1 mais expand/contract;
- kinds `event` e `stream`;
- property e mutation tests no config;
- orquestracao real (paralelismo, retries, yolo, PR-por-PRD, tracking de deploy);
- observabilidade de runtime;
- comite multi-agente de revisao;
- guia completo de brownfield/strangler.
