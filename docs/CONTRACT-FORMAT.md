# Formato do Contrato Neutro

O contrato e a junta do BPT. Ele e o unico ponto onde backend e frontend se encontram, e faz isso sem que um lado precise conhecer o codigo do outro. Um comportamento two-sided existe nos dois lados com a mesma identidade e a mesma spec; o que amarra os dois e este arquivo YAML neutro.

A regra de ouro: o contrato descreve **o que** o comportamento aceita e devolve, nunca **como** um lado implementa. Nada de tipo de linguagem, nada de rota, nada de verbo HTTP.

## Onde mora

Um contrato por comportamento, no caminho canonico derivado do id (ponto vira barra):

```
packages/contracts/<caminho>/contract.yaml
packages/contracts/<caminho>/spec.md
```

Exemplo para `produto.listar`:

```
packages/contracts/produto/listar/contract.yaml
packages/contracts/produto/listar/spec.md
```

O contrato vive **fora** de `apps/backend` e `apps/frontend`, em `packages/contracts`. A spec fica ao lado do contrato, uma so, nunca duplicada por lado. A raiz de contratos e declarada no `bpt.config.yaml`:

```yaml
contracts:
  root: packages/contracts
```

## Propriedade

Ninguem e dono do contrato no sentido de um lado poder muda-lo por conveniencia. As regras de propriedade:

- **Ninguem e dono unilateral.** O contrato existe fora dos apps justamente para nao pertencer a nenhum deles.
- **Os apps leem, nunca escrevem fora de um PR de contrato.** Backend e frontend consomem o contrato como fonte da verdade. Alterar o contrato e uma mudanca deliberada, revisada em um PR proprio de contrato, nao um efeito colateral de mexer no codigo de um lado.
- **Um lado nunca importa do outro.** Backend nao importa de frontend e vice-versa. Toda comunicacao entre lados passa pelo contrato.
- **Em conflito, o contrato decide.** Se a implementacao de um lado diverge do contrato, quem esta errado e a implementacao. O contrato e o arbitro; o codigo se ajusta a ele, nunca o contrario dentro do mesmo PR.

## Tipos neutros

Os campos de `input` e `output` usam apenas tipos neutros, sem vinculo com stack:

| Tipo | Significado |
|------|-------------|
| `text` | Texto livre. |
| `integer` | Numero inteiro. |
| `decimal` | Numero com casas decimais (nao monetario). |
| `boolean` | Verdadeiro ou falso. |
| `money` | Valor monetario (semantica de dinheiro, tratada com cuidado por cada lado). |
| `list` | Colecao ordenada (`list of <tipo>`). |
| `object` | Estrutura com campos nomeados. |

### Por que nada de tipo de linguagem, rota ou verbo HTTP

- **Tipo de linguagem** (`String`, `BigDecimal`, `Int32`, `Optional<T>`) amarraria o contrato a uma stack. O contrato precisa ser lido igualmente por qualquer adapter, em qualquer runtime.
- **Rota** (`/produtos`, `/api/v2/...`) e detalhe de superficie. Uma rota mora na spec, no bloco `surfaces`, porque e o **como** o frontend ou o backend expoe o comportamento, nao o **que** ele faz.
- **Verbo HTTP** (`GET`, `POST`) presume transporte HTTP. Um mesmo comportamento poderia ser exposto como endpoint, comando de CLI, job ou evento. O contrato usa `kind` (`query` ou `command`) para capturar a intencao de forma neutra, deixando o transporte a cargo do adapter.

## Campos do contrato

| Campo | Obrigatorio | Descricao |
|-------|-------------|-----------|
| `id` | sim | Identidade canonica `dominio.acao`. Igual nos dois lados. |
| `version` | sim | Inteiro (ver Versionamento). |
| `kind` | sim | `query` (le, nao muda estado) ou `command` (muda estado). |
| `title` | sim | Titulo humano curto. |
| `authorization` | sim | `required` (boolean) e `roles` (lista de papeis de dominio). |
| `input` | sim | Campos de entrada, cada um com tipo neutro e restricoes (`min`, `max`, `default`, `opcional`). |
| `output` | sim | Forma do resultado, com tipos neutros aninhados. |
| `rules` | sim | Regras de negocio como dado (ver abaixo). |
| `errors` | sim | Lista de erros possiveis. |

### Erros

Cada erro tem quatro atributos:

- `code`: identificador em portugues, caixa alta (`PARAMETRO_INVALIDO`, `NAO_AUTORIZADO`).
- `category`: classe do erro (`validation`, `user`, e afins).
- `retryable`: se vale a pena tentar de novo (`retryable` ou `nao-retryable`).
- `when`: a condicao que dispara o erro (descrita na spec quando precisa de detalhe).

## Regra de negocio compartilhada como DADO

Nao existe pacote de dominio em codigo compartilhado. Uma regra que vale para os dois lados vive no bloco `rules` do contrato, como **dado**, com um id e uma descricao neutra:

```yaml
rules:
  - ordenacao: itens por nome ascendente
  - busca-case-insensitive: ignora caixa
```

Cada lado implementa a regra no seu codigo. A honestidade dos dois e garantida pelo teste de contrato bilateral (consumer-driven): o cenario mora na spec e roda em cada superficie no `verify`. A regra e uma so (o dado no contrato), mas tem duas implementacoes que precisam concordar.

Regra compartilhada **nunca** vira codigo de kernel. Kernel e infra transversal; regra de negocio e dado no contrato.

## Versionamento enxuto no v1

- `version` e um **inteiro**, nao semver.
- Mudanca **aditiva** (novo campo opcional de input, novo campo de output, novo erro) **nao** sobe a version. Consumidores antigos continuam validos.
- Mudanca que **quebra** (remover ou renomear campo, tornar obrigatorio o que era opcional, mudar tipo, mudar significado) **sobe** a version.

Semver completo, convivencia N e N-1 e expand/contract ficam para o futuro. No v1 a distincao e binaria: aditivo mantem, quebra sobe.

## Deteccao de drift no v1

No v1, a deteccao de drift e simples e verificada pelo validador: o **trio de arquivos existe**.

- `contract.yaml` presente.
- `spec.md` presente ao lado.
- Pasta do comportamento existe em cada lado declarado em `sides`.

Um no two-sided precisa de contrato; um no one-sided declara `contract: none`. Hash canonico, registro central e negociacao N/N-1 sao futuro, nao v1.

## Idioma hibrido

- **Chaves estruturais de schema em ingles**: `id`, `version`, `kind`, `title`, `authorization`, `input`, `output`, `rules`, `errors`, `code`, `category`, `retryable`.
- **Vocabulario de dominio e ids em portugues**: `produto.listar`, `busca`, `preco`, `disponivel`, `PARAMETRO_INVALIDO`, `NAO_AUTORIZADO`, papeis como `cliente`.

A estrutura e universal; o dominio e do projeto.

## Exemplo real: produto.listar

`packages/contracts/produto/listar/contract.yaml`:

```yaml
id: produto.listar
version: 1
kind: query
title: Listar produtos

authorization:
  required: true
  roles: [cliente]

input:
  busca:
    type: text
    opcional: true
  pagina:
    type: integer
    min: 1
    default: 1
  tamanho:
    type: integer
    min: 1
    max: 100
    default: 20

output:
  itens:
    type: list
    of:
      type: object
      fields:
        id: text
        nome: text
        preco: money
        disponivel: boolean
  total: integer
  pagina: integer

rules:
  - ordenacao: itens por nome ascendente
  - busca-case-insensitive: ignora caixa

errors:
  - code: PARAMETRO_INVALIDO
    category: validation
    retryable: nao-retryable
  - code: NAO_AUTORIZADO
    category: user
    retryable: nao-retryable
```

Note o que **nao** esta aqui: nenhum tipo de linguagem, nenhuma rota `/produtos`, nenhum verbo HTTP. A rota e o tipo de superficie moram na spec, no bloco `surfaces`. O contrato so diz o que `produto.listar` aceita, o que devolve, quais regras valem para os dois lados e como pode falhar.
