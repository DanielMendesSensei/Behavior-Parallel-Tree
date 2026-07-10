# Adapter Placeholder

Este adapter honra a interface inteira do BPT, mas nao conhece nenhuma stack. Ele existe para provar o contrato de adapter e para deixar o template rodavel sem escolher linguagem, framework ou runtime. Dos seis hooks, apenas o `scaffold` faz trabalho real; os outros cinco respondem com um status ok vazio.

O nucleo do BPT declara (arvore, espelho, contrato, spec) e o adapter executa (worktrees, paralelismo, loop). Este placeholder ocupa o lugar do executor sem executar de fato.

## Protocolo

O adapter e um executavel declarado no `bpt.config.yaml` (aqui, `adapter: placeholder`). O nucleo invoca sempre da mesma forma:

```
bpt-adapter <hook>
```

- Le **um** objeto JSON de `stdin`.
- Escreve **um** objeto JSON em `stdout`.
- Manda logs para `stderr`.
- `exit 0` significa que o hook rodou (o resultado real vai no `status` do payload).
- `exit != 0` significa que o adapter quebrou.

A unidade de execucao e o **no por lado**, chaveada em `(lado, id)`. Cada no-por-lado roda em uma worktree propria. Pode existir um adapter por lado, ou seja, `backend` e `frontend` podem apontar para executaveis diferentes, cada um falando o mesmo protocolo neutro.

## Os seis hooks

| hook | papel | neste placeholder |
| --- | --- | --- |
| `scaffold` | cria pastas espelhadas + stub de contrato e spec, idempotente | faz trabalho real |
| `plan` | monta o plano tecnico, nao escreve produto | status ok vazio |
| `execute` | implementa so nas pastas do no | status ok vazio |
| `verify` | roda cenarios da superficie + unit tests + checa direcao de import | status ok vazio |
| `review` | revisao semantica | status ok vazio |
| `codegen` | materializa o contrato neutro em tipos/validadores da stack em `__generated__/` | status ok vazio |

## Exemplo: chamando o scaffold

Voce passa por pipe o JSON de um no, com `id` e `sides`, para o hook `scaffold`:

```
echo '{
  "id": "produto.listar",
  "sides": ["backend", "frontend"]
}' | bin/bpt-adapter scaffold
```

O que ele cria, seguindo as formas canonicas (`id` `produto.listar` vira caminho `produto/listar`):

- `apps/backend/behaviors/produto/listar/` com `src/` e `__generated__/`.
- `apps/frontend/behaviors/produto/listar/` com `src/` e `__generated__/`.
- `packages/contracts/produto/listar/contract.yaml` (stub), se ainda nao existir.
- `packages/contracts/produto/listar/spec.md` (stub a partir da spec), se ainda nao existir.

O scaffold e **idempotente**: rodar de novo sobre um no ja criado nao apaga nem duplica nada. As pastas espelhadas nos dois lados compartilham uma unica spec, que mora ao lado do contrato, nunca duplicada por lado. O `src/` e para codigo humano; o `__generated__/` fica vazio aqui, porque quem o preenche e o `codegen` de um adapter real.

Nao existe arquivo de metadado por no: a pasta na convencao mais a entrada no `bpt.config.yaml` ja sao a declaracao.

## De placeholder para adapter real

Um adapter real nao muda o protocolo, ele troca a implementacao. Voce substitui os scripts em `hooks/` pela logica da sua stack:

- `hooks/plan` passa a produzir um plano tecnico de verdade.
- `hooks/execute` passa a escrever codigo dentro das pastas do no.
- `hooks/verify` passa a rodar os cenarios da superficie, os unit tests e a checagem de direcao de import (reprova `kernel -> behaviors/*` e `behaviors/a -> behaviors/b`).
- `hooks/review` passa a fazer revisao semantica.
- `hooks/codegen` passa a materializar o contrato neutro em tipos e validadores da stack, dentro de `__generated__/`.

Como pode haver um adapter por lado, um lado backend pode gerar tipos de uma linguagem e o lado frontend de outra, cada um lendo o mesmo contrato neutro.

## Onde continuar

A referencia completa da interface, dos payloads e da orquestracao que um adapter real deve honrar (worktree por no-por-lado na branch `bpt/<lado>/<id>`, ondas de kernel primeiro, loop `codegen -> plan -> execute -> verify -> review` com ate 3 tentativas, teste de contrato bilateral) esta em `docs/ADAPTER.md`.
