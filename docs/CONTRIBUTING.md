# Como adicionar um comportamento (o 2o, o 3o, o N)

Este guia mostra o caminho completo para colocar um novo comportamento no ar dentro do BPT: escolher o id, rodar o scaffold, preencher a spec e o contrato, registrar o no e validar. O template ja nasce com dois nos reais (`produto.listar` e `produto.detalhar`), entao use-os como referencia viva enquanto le.

A ideia central: cada comportamento e uma ilha. Voce deve conseguir construi-lo olhando so a pasta dele, o contrato que ele expoe e os contratos que ele consome. Se voce precisar abrir o codigo de outro comportamento para terminar o seu, algo esta errado na modelagem.

## 1. Escolha o id (dominio.acao)

O id e a identidade do comportamento nos dois lados. Ele obedece a forma canonica:

- Tudo minusculo, o ponto separa segmentos, o hifen serve para palavra composta.
- De 2 a 3 segmentos, prefira 2. Exemplos bons: `produto.listar`, `carrinho.revisar`, `pagamento.cartao.autorizar`.
- O primeiro segmento e o dominio (`produto`, `carrinho`, `pagamento`), o ultimo e a acao (`listar`, `revisar`, `autorizar`).
- Evite `kernel` como dominio: ele e reservado para a infra transversal e o validador reprova qualquer id sob a pasta de kernel.

O id vira caminho trocando ponto por barra:

- `produto.detalhar` vira o caminho `produto/detalhar`.
- Comportamento: `apps/<lado>/behaviors/produto/detalhar/`
- Contrato: `packages/contracts/produto/detalhar/contract.yaml`
- Spec: `packages/contracts/produto/detalhar/spec.md`

Nao existe arquivo de metadado por no. A pasta na convencao mais a entrada no `bpt.config.yaml` ja sao toda a declaracao do comportamento.

## 2. Rode o scaffold do adapter

O scaffold cria as pastas espelhadas nos lados escolhidos e gera os stubs de contrato e spec. Ele e idempotente: rodar de novo nao quebra nada. O protocolo do adapter e neutro: ele le um JSON de stdin, escreve um JSON em stdout e manda logs para stderr.

Comando exato (troque o id e os sides conforme o seu no):

```bash
echo '{"id":"produto.detalhar","sides":["backend","frontend"],"paths":{"backend":"apps/backend/behaviors/produto/detalhar","frontend":"apps/frontend/behaviors/produto/detalhar","contract":"packages/contracts/produto/detalhar"}}' \
  | adapters/placeholder/bin/bpt-adapter scaffold
```

O adapter placeholder implementa o `scaffold` de verdade: ele cria as pastas do no em cada lado (com `src/` para o codigo humano e `__generated__/` para o codigo gerado depois pelo `codegen`) e deixa os stubs de `contract.yaml` e `spec.md` prontos para voce preencher. Os outros cinco hooks (`plan`, `execute`, `verify`, `review`, `codegen`) no placeholder apenas retornam status ok vazio, entao a construcao do produto em si voce faz a mao neste template.

Leitura do resultado:

- `exit 0` significa que o adapter rodou. O status real vem no JSON de stdout.
- `exit` diferente de 0 significa que o adapter quebrou, e nao que o comportamento falhou.

## 3. Preencha a spec.md

A spec e a fonte de verdade do comportamento observavel. Ela mora ao lado do contrato, uma so por comportamento, nunca duplicada por lado. Estrutura:

Front-matter:

- `id`, `title`
- `surfaces`: o que cada lado expoe. Ex.: `frontend { type: tela, route: /produtos }`, `backend { type: endpoint }`. Superficies possiveis: `tela`, `comando-cli`, `endpoint`, `job`, `evento`.
- `contract`: o caminho do contrato (`produto/detalhar`), ou nada quando o no e one-sided (veja a secao 6).
- `consumes`: lista de contratos que este comportamento le de outros (ex.: `[produto/listar]`). Vazio se ele nao compoe ninguem.
- `status`: por lado, um de `draft`, `ready`, `built`, `verified`. Comeca em `draft` dos dois lados.
- `ui_bindings`: mapa neutro superficie -> handle estavel, para os testes de tela amarrarem sem depender de nome de funcao.

Secoes do corpo:

- **Comportamento**: a acao e o resultado, em uma frase clara.
- **Regras**: o que sempre vale (ordenacao, normalizacao, limites).
- **Cenarios**: no formato dado / quando / entao, um por superficie. Marque cada cenario com `[contrato]` (roda no verify do backend) ou `[tela]` (roda no verify do frontend). O "entao" e projetado por superficie: o mesmo cenario tem consequencia observavel diferente em cada lado.
- **Fora de escopo**: o que este comportamento deliberadamente nao faz.

Os cenarios testam comportamento observavel, sobrevivem a refactor e nunca citam nome de funcao ou de tabela.

## 4. Preencha o contract.yaml

O contrato e o YAML neutro que liga os dois lados. Nenhuma linguagem, framework ou runtime aparece aqui. Tipos neutros disponiveis: `text`, `integer`, `decimal`, `boolean`, `money`, `list`, `object`.

Campos:

- `id`, `version`, `kind` (`query` ou `command`), `title`.
- `authorization`: `required` e `roles`.
- `input`: parametros com tipo, restricoes (`min`, `max`, `default`) e se sao opcionais.
- `output`: a forma do resultado, com `list of object { ... }` quando for colecao.
- `rules`: as regras de negocio compartilhadas, como DADO. Cada lado implementa a mesma regra; um teste de contrato bilateral mantem os dois honestos. Nao existe pacote de dominio em codigo compartilhado, a regra vive aqui e so aqui.
- `errors`: lista de erros com categoria (`validation`, `user`, ...) e se e retryable.

Referencia viva: `packages/contracts/produto/listar/contract.yaml`.

## 5. Registre o no no bpt.config.yaml

O `bpt.config.yaml` na raiz e o arquivo unico que declara todos os nos. Adicione o seu na lista `nodes`, informando os `sides` que ele ocupa e as `deps`:

```yaml
nodes:
  produto.listar:
    sides: [backend, frontend]
    deps: []
  produto.detalhar:
    sides: [backend, frontend]
    deps: [produto.listar]
```

Sobre `deps`:

- `deps` sao os comportamentos que precisam existir antes do seu. O nucleo usa isso para derivar as ondas de paralelismo por ordem topologica.
- O grafo deve ser aciclico. Sem auto-dependencia. Sem ciclo.
- Quando o grafo diverge entre os lados, declare `deps` por lado:

```yaml
  checkout.pagar:
    sides: [backend, frontend]
    deps:
      backend: [pagamento.cartao.autorizar]
      frontend: [carrinho.revisar]
    prd: checkout-v1
```

`sides` e uma lista aberta. Um comportamento so de linha de comando usaria `sides: [cli]`.

## 6. Quando o no e one-sided (contract: none)

Nem todo comportamento existe nos dois lados. Um no que so vive no frontend (por exemplo uma tela que apenas recombina dados que ja vem de outro contrato) e one-sided. Nesse caso:

- Ele declara um unico lado em `sides`.
- Ele nao expoe contrato proprio: na spec, `contract: none`.
- Ele consome os contratos de que precisa via `consumes`.

Exemplo (documental, nao esta no config vivo):

```yaml
  catalogo.filtrar:
    sides: [frontend]
    deps: [produto.listar]
    # contract: none  (declarado na spec; consome produto/listar)
```

O validador cobra a coerencia: no two-sided precisa de contrato; no one-sided precisa de `contract: none`.

## 7. Quando o no compoe (consumes)

`consumes` e como um comportamento le contratos de outros comportamentos sem tocar no codigo deles. E aqui que a topologia N:M aparece:

- Uma tela composta consome varios contratos: `consumes: [produto.listar, promocao.vigentes, estoque.disponibilidade]`.
- Um contrato serve varias telas ao mesmo tempo, sem saber quem o consome.

`consumes` entra tanto na spec (front-matter) quanto conta como dependencia no grafo. As refs precisam existir, senao o validate reprova.

## Regra que nunca se quebra: comportamento nao importa de comportamento

Um comportamento pode:

- importar do kernel do seu lado (infra transversal),
- ler contratos (o proprio e os que constam em `consumes`),
- e nada mais fora da sua propria pasta.

Um comportamento nunca importa o codigo de outro comportamento. A ligacao entre eles e sempre o contrato neutro, nunca o import direto. O kernel tambem obedece a direcao: comportamento importa do kernel, o kernel nunca importa de comportamento.

O `verify` do adapter e o guardiao dessa direcao. Ele:

- reprova `kernel -> behaviors/*`
- reprova `behaviors/a -> behaviors/b`
- permite `behaviors/* -> kernel`, `behaviors/* -> contracts`, `kernel -> kernel`, `kernel -> contracts`

Se voce sentir vontade de importar de outro comportamento, a resposta e uma destas: consuma o contrato dele via `consumes`, ou promova o pedaco comum ao kernel (so quando ele e transversal, usado por 2 ou mais comportamentos e descritivel sem citar nome de comportamento), ou mova a regra compartilhada para o bloco `rules` do contrato como dado.

## 8. Rode o validador ate passar

O validador e minimo e vive fora da stack do app (Python 3 mais PyYAML, tooling trocavel):

```bash
./bpt validate
```

Ele roda sete invariantes:

1. `schema` presente e suportado (`bpt/v1`).
2. `id` unico e no formato `dominio.acao`.
3. `sides` nao vazio e cada lado declarado existe.
4. refs de `deps` e `consumes` existem, sem auto-dependencia, grafo aciclico (se houver ciclo, ele aponta o ciclo).
5. no two-sided tem contrato; no one-sided tem `contract: none`.
6. nenhum id sob pasta de kernel (o dominio `kernel` e reservado).
7. o trio de arquivos existe: contrato mais spec mais a pasta do no em cada lado.

Alem de validar, o nucleo deriva dai as ondas de paralelismo por ordem topologica: o adapter usa essas ondas para construir varios comportamentos ao mesmo tempo, kernel primeiro, depois as ondas de comportamento respeitando o DAG.

Rode, leia o erro, corrija, repita. Quando `./bpt validate` passar limpo, o comportamento esta declarado de forma consistente e pronto para o adapter construir.

## Checklist final

- [ ] id no formato `dominio.acao`, 2 a 3 segmentos.
- [ ] scaffold rodado, pastas espelhadas e stubs criados.
- [ ] `spec.md` preenchida (surfaces, cenarios por superficie, ui_bindings, status).
- [ ] `contract.yaml` preenchido, ou `contract: none` se one-sided.
- [ ] no registrado no `bpt.config.yaml` com `sides`, `deps` e, se compoe, `consumes`.
- [ ] nenhum import de outro comportamento.
- [ ] `./bpt validate` passa limpo.
