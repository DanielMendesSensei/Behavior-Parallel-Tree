# Kernel do frontend

Infra transversal do lado frontend, FORA da arvore de comportamentos. Aqui mora so o que atende varios comportamentos ao mesmo tempo e nao pertence a nenhum deles: `app-shell/` (layout, roteamento, providers globais), `design-system/` (tokens, componentes base, temas), `auth/` (sessao, guardas de rota) e `config/` (ambiente, feature flags).

As subpastas nascem vazias de proposito. O kernel comeca magro; codigo so sobe pra ca quando passa nas regras de promocao (veja `docs/KERNEL.md`).

## Regra de direcao

A dependencia so aponta num sentido:

- comportamento PODE importar do kernel.
- kernel NUNCA importa de comportamento.
- kernel PODE importar de outro kernel e de `packages/contracts`.

O `verify` do adapter reprova `kernel -> behaviors/*` e `behaviors/a -> behaviors/b`. O dominio `kernel` e reservado: nenhum id de comportamento pode morar sob uma pasta de kernel.

## O que NAO entra aqui

Regra de negocio compartilhada nao vira codigo de kernel. Ela e DADO, no bloco `rules` do contrato, e cada lado implementa, com teste bilateral mantendo os dois lados honestos.

## Mais detalhes

Promocao, regra do tres, anti-inchaco, democao e a onda de kernel serializada antes das ondas de comportamento: tudo em `docs/KERNEL.md`.
