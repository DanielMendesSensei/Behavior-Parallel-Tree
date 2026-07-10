# Adapter

O nucleo do BPT so declara: arvore, espelho, contrato e spec. Quem executa (worktrees, paralelismo, loop de construcao, geracao de codigo) e o adapter. O adapter e a unica peca que conhece linguagem, framework e runtime. Trocar de stack e trocar de adapter, sem tocar no nucleo.

No v1 a interface do adapter e deferida: existe o protocolo, o envelope e a tabela de hooks, mas o template so traz um adapter placeholder que faz scaffold de verdade. Os outros hooks do placeholder respondem com status ok vazio.

## Onde o adapter e declarado

O adapter e um executavel apontado em `bpt.config.yaml`:

```yaml
adapter: placeholder
```

O nome resolve para um executavel do template (por exemplo `tools/bpt/adapters/placeholder`). O nucleo invoca esse executavel uma vez por hook, por unidade de execucao.

## Unidade de execucao

A unidade de execucao e o **no por lado**, chaveada em `(lado, id)`. O no `produto.listar` two-sided gera duas unidades: `(backend, produto.listar)` e `(frontend, produto.listar)`. Cada unidade tem sua propria worktree.

O adapter pode ser um so para os dois lados ou um por lado. Um adapter por lado e uma escolha valida e comum, ja que backend e frontend costumam viver em stacks diferentes.

## Protocolo neutro

O contrato entre nucleo e adapter e um protocolo de processo, neutro de linguagem:

```
bpt-adapter <hook>
```

- **stdin**: exatamente 1 documento JSON, o envelope da requisicao.
- **stdout**: exatamente 1 documento JSON, o resultado do hook.
- **stderr**: logs livres (progresso, diagnostico). O nucleo repassa stderr sem interpretar.

### Semantica de exit code

- **exit 0**: o adapter rodou. O que aconteceu de fato esta no `status` do JSON de saida (`ok`, `blocked`, `skipped`). Um no bloqueado depois de 3 tentativas ainda sai com exit 0 e `status: blocked`.
- **exit != 0**: o adapter quebrou. Nao ha resultado confiavel; o nucleo trata como falha de infraestrutura, nao como resultado de negocio.

Regra pratica: erro de produto (o comportamento nao ficou pronto) e `exit 0` com status no payload; erro de ferramenta (o adapter em si falhou) e `exit != 0`.

## Envelope da requisicao (stdin)

O nucleo monta o envelope a partir da arvore, do contrato e da spec. Campos:

| Campo | Significado |
|-------|-------------|
| `hook` | qual dos 6 hooks executar (`scaffold`, `plan`, `execute`, `verify`, `review`, `codegen`) |
| `mode` | modo de orquestracao (por exemplo `normal` ou `yolo`) |
| `attempt` | numero da tentativa no loop (1 a 3) |
| `node.id` | id canonico do no, forma `dominio.acao` |
| `node.side` | lado desta unidade (`backend`, `frontend`, ou outro lado declarado) |
| `node.deps` | ids dos nos dos quais este depende (ja resolvidos por lado quando o grafo diverge) |
| `node.paths` | pastas do no neste lado, raiz `apps/<lado>/behaviors/<caminho>/` |
| `spec.ref` | caminho da spec unica, `packages/contracts/<caminho>/spec.md` |
| `contract.ref` | caminho do contrato, `packages/contracts/<caminho>/contract.yaml` (ou nulo em no one-sided com `contract: none`) |
| `consumes` | contratos consumidos por este no (telas compostas consomem N contratos) |
| `workspace.worktree` | caminho da worktree desta unidade |
| `workspace.branch` | branch da unidade, `bpt/<lado>/<id>` |
| `workspace.base_branch` | branch base sobre a qual a worktree foi criada |
| `kernel.ref` | raiz do kernel do lado, `apps/<lado>/kernel` (somente leitura) |
| `prior_artifacts` | artefatos produzidos por hooks anteriores desta unidade (por exemplo plano do `plan`) |
| `feedback` | achados da tentativa anterior, quando `attempt > 1` |

## Resultado (stdout)

O JSON de saida sempre traz um `status`. Alem disso pode trazer artefatos que o nucleo repassa como `prior_artifacts` para o proximo hook, e `findings` que viram `feedback` na proxima tentativa.

```json
{ "status": "ok", "artifacts": {}, "findings": [] }
```

## Os 6 hooks

| Hook | O que faz | O que escreve |
|------|-----------|---------------|
| `scaffold` | cria as pastas espelhadas do no a partir da spec, mais stub de contrato e de spec. Idempotente: rodar de novo nao duplica nem sobrescreve trabalho humano | `apps/<lado>/behaviors/<caminho>/src/`, stub em `packages/contracts/<caminho>/` |
| `plan` | produz um plano tecnico para implementar o no. Nao escreve codigo de produto | artefato de plano em `prior_artifacts` |
| `execute` | implementa o comportamento, escrevendo somente dentro das pastas do no | `apps/<lado>/behaviors/<caminho>/src/` |
| `verify` | roda os cenarios da superficie mais os testes unitarios e checa a direcao dos imports | relatorio de verificacao, `status` e `findings` |
| `review` | revisao semantica do que foi construido; portao depois do verde | `status` e `findings` |
| `codegen` | materializa o contrato neutro em tipos e validadores da stack | `apps/<lado>/behaviors/<caminho>/__generated__/` |

Regras de fronteira que todo hook respeita:

- Codigo humano mora em `src/` dentro do no; codigo gerado mora em `__generated__/` dentro do no. So o `codegen` escreve em `__generated__/`.
- `execute` escreve apenas nas pastas do no. Contratos consumidos e kernel entram somente para leitura.
- O `verify` reprova import de `kernel -> behaviors/*` e de `behaviors/a -> behaviors/b`. Permite `behaviors/* -> kernel`, `behaviors/* -> contracts`, `kernel -> kernel` e `kernel -> contracts`.

## Expectativas de orquestracao

O nucleo deriva as ondas de paralelismo por ordem topologica do DAG. O adapter honra a orquestracao assim:

- **Worktree por no-por-lado**: uma worktree por unidade `(lado, id)`, na branch `bpt/<lado>/<id>`, criada sobre a `base_branch`.
- **Recorte de contexto**: cada worktree ve as pastas do no, os contratos consumidos e o kernel do lado somente leitura. Esse recorte e o objetivo do BPT: minimizar o contexto de cada mudanca.
- **Ondas**: o paralelismo respeita o DAG. As ondas de kernel rodam primeiro e serializadas (com CHANGELOG do kernel), depois as ondas de comportamento.
- **Loop de construcao**: `codegen -> plan -> execute -> verify -> review`, com ate 3 tentativas. Os `findings` de uma tentativa voltam como `feedback` na proxima. Na 3a falha o no fica `blocked` com a worktree preservada para inspecao.
- **Teste de contrato bilateral**: antes de dar um no two-sided por pronto, roda o teste de contrato consumer-driven que mantem backend e frontend honestos contra a mesma spec.
- **Modo yolo**: modo de orquestracao acelerado, sinalizado em `mode`, para quem quer pular portoes intermediarios.

Nada disso vive no nucleo alem da declaracao: o nucleo diz o que e a unidade, qual a branch, qual o recorte e qual a ordem das ondas; o adapter executa.

## O que o placeholder faz

O adapter placeholder do template faz **scaffold de verdade** e mais nada. Os hooks `plan`, `execute`, `verify`, `review` e `codegen` respondem com `status: ok` e payload vazio, para que voce veja o loop rodar de ponta a ponta antes de plugar uma stack real.

### Exemplo de chamada de scaffold

Entrada (stdin de `bpt-adapter scaffold`):

```json
{
  "hook": "scaffold",
  "mode": "normal",
  "attempt": 1,
  "node": {
    "id": "produto.listar",
    "side": "backend",
    "deps": [],
    "paths": ["apps/backend/behaviors/produto/listar"]
  },
  "spec": { "ref": "packages/contracts/produto/listar/spec.md" },
  "contract": { "ref": "packages/contracts/produto/listar/contract.yaml" },
  "consumes": [],
  "workspace": {
    "worktree": ".bpt/worktrees/backend/produto.listar",
    "branch": "bpt/backend/produto.listar",
    "base_branch": "main"
  },
  "kernel": { "ref": "apps/backend/kernel" },
  "prior_artifacts": {},
  "feedback": []
}
```

Saida (stdout):

```json
{
  "status": "ok",
  "artifacts": {
    "created": [
      "apps/backend/behaviors/produto/listar/src/",
      "packages/contracts/produto/listar/contract.yaml",
      "packages/contracts/produto/listar/spec.md"
    ]
  },
  "findings": []
}
```

Rodar o mesmo scaffold de novo devolve `status: ok` com `created` vazio: o hook e idempotente e nao mexe no que ja existe.

## Como escrever um adapter real

1. Copie a pasta do placeholder para uma nova pasta de adapter (por exemplo por stack) e aponte `adapter:` no `bpt.config.yaml` para o novo executavel.
2. Substitua os hooks um a um dentro de `hooks/`. Comece pelo `codegen` (para ter tipos da sua stack) e pelo `execute`, depois `verify`, `review` e `plan`. O `scaffold` do placeholder ja serve de base.
3. Mantenha o protocolo: leia 1 JSON de stdin, escreva 1 JSON em stdout, mande log para stderr, use exit 0 para resultado de negocio e exit != 0 so quando o proprio adapter quebrar.
4. Respeite as fronteiras de import e a regra de escrita por pasta. O `verify` e onde voce faz cumprir a direcao dos imports na sua linguagem.
5. Um adapter por lado e uma escolha valida: declare o executavel de cada lado se backend e frontend usam stacks diferentes. A chave `(lado, id)` ja separa as unidades, entao cada adapter so precisa cuidar do seu lado.

O que fica de fora do v1 e vira futuro: orquestracao real (paralelismo, retries automaticos, yolo de verdade, PR por PRD, tracking de deploy), codegen rico com JSON Schema e `$ref`, e comite multi-agente de revisao. A interface acima ja e desenhada para receber isso sem mudar de forma.
