# Kernel do backend

Este e o kernel do lado backend: infra transversal que fica FORA da arvore de comportamentos. Aqui moram apenas coisas como auth, acesso a banco (db), config e app-shell, ou seja, o encanamento que varios comportamentos compartilham.

O kernel NAO e um comportamento. Ele nao tem contrato, nao tem spec e nao aparece como no no `bpt.config.yaml`. O dominio `kernel` e reservado: nenhum id de comportamento pode viver sob esta pasta.

## Regra de direcao (absoluta)

- Comportamento importa do kernel: permitido.
- Kernel importa de comportamento: PROIBIDO.

O kernel nunca conhece um comportamento pelo nome. Se algo aqui precisa saber qual comportamento o chama, esse algo esta no lugar errado. O `verify` do adapter reprova qualquer import na direcao `kernel -> behaviors/*`.

## Regra de negocio compartilhada nao mora aqui

Regra de negocio que dois lados ou dois comportamentos precisam respeitar NAO vira codigo de kernel. Ela vira DADO, declarada no bloco `rules` do contrato, e cada lado a implementa. Um teste bilateral mantem os dois lados honestos. O kernel guarda infra, nao politica de dominio.

## Subpastas vazias de proposito

Este kernel nasce vazio por ser agnostico de stack: o nucleo do BPT nao conhece linguagem, framework nem runtime. As subpastas (auth, db, config, app-shell, design-system e afins) sao preenchidas pelo adapter e pela stack escolhida do projeto, nao pelo nucleo.

## Saiba mais

Criterios de promocao ao kernel, regra do tres, anti-inchaco, democao, ondas serializadas e enforcement completo estao em `docs/KERNEL.md`.
