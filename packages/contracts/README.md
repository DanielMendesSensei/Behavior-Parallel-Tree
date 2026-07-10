# packages/contracts

A junta neutra entre as duas arvores de comportamentos. Aqui mora o acordo que liga backend e frontend sem que um lado conheca o codigo do outro.

## O que fica aqui

Um par de arquivos por comportamento, no caminho derivado do id (o ponto vira barra, ou seja `produto.listar` vira `produto/listar`):

- `contract.yaml`: o contrato neutro (kind, input, output, rules, errors, authorization). Fonte da verdade da interface.
- `spec.md`: a especificacao unica do comportamento (uma so, ao lado do contrato, nunca duplicada por lado).

Exemplo:

```
packages/contracts/
  produto/listar/contract.yaml
  produto/listar/spec.md
  produto/detalhar/contract.yaml
  produto/detalhar/spec.md
```

## Regras da junta

- **Ninguem e dono.** O contrato pertence a fronteira, nao a um lado. Backend e frontend implementam contra ele.
- **Os apps leem, nunca escrevem fora de um PR de contrato.** Mudar a interface e um ato deliberado e revisado, nao um efeito colateral de implementar um lado.
- **Um lado nunca importa do outro.** A unica ponte permitida e o contrato. `apps/backend` e `apps/frontend` so se enxergam atraves daqui.
- **Regra de negocio compartilhada e dado**, no bloco `rules` do contrato. Cada lado a implementa; o teste bilateral mantem os dois honestos.

## Formatos

- Formato do contrato: veja `docs/CONTRACT-FORMAT.md`.
- Formato da spec: veja `docs/SPEC-FORMAT.md`.

## Futuro: `_flows/`

Testes de fluxo (jornadas que atravessam varios comportamentos) vao morar em `packages/contracts/_flows/<prd>/`, com dono no nivel do PRD. Ainda nao faz parte do v1.
