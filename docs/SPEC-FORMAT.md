# Como escrever uma spec.md

A `spec.md` e o documento humano de um comportamento. Ela descreve o QUE o
comportamento faz, para as pessoas e para o agente, em linguagem que sobrevive a
refatoracao. O `contract.yaml` (ao lado) fala a maquina; a `spec.md` fala a
intencao. Os dois moram juntos e valem para os dois lados do espelho.

Regra de ouro, valida em cada linha deste documento: a spec diz o QUE, nunca o
COMO. Ela nao cita nome de funcao, de tabela, de componente, de biblioteca nem
de rota interna. Se um trecho so faz sentido depois de escolher a stack, ele nao
pertence a spec.

## Onde a spec mora

Existe UMA spec por comportamento, ao lado do contrato, nunca duplicada por
lado:

```
packages/contracts/<caminho>/spec.md
packages/contracts/<caminho>/contract.yaml
```

O `<caminho>` vem do id do comportamento trocando ponto por barra. O
comportamento `produto.listar` tem id com dois segmentos (`dominio.acao`) e vira
o caminho `produto/listar`. Logo:

```
packages/contracts/produto/listar/spec.md
packages/contracts/produto/listar/contract.yaml
```

O comportamento existe nas duas arvores (`apps/backend/behaviors/produto/listar/`
e `apps/frontend/behaviors/produto/listar/`), mas a spec e o contrato ficam
apenas em `packages/contracts`. Backend e frontend leem a mesma fonte de verdade.
Isso e o que mantem o espelho honesto: uma so descricao, duas implementacoes.

## Anatomia da spec

A spec tem duas partes: o front-matter (metadados estruturais em YAML) e o corpo
(secoes em Markdown). O idioma segue a regra hibrida do BPT: as chaves de
estrutura ficam em ingles (`id`, `title`, `surfaces`, `contract`, `consumes`,
`status`, `ui_bindings`); o vocabulario de dominio e os ids ficam em portugues
(`produto.listar`, `busca`, `/produtos`).

## O front-matter

O front-matter e um bloco YAML no topo do arquivo, delimitado por `---`. Ele
declara a identidade do comportamento e como ele aparece em cada superficie.

Campos:

- `id`: o id canonico do comportamento, na forma `dominio.acao`. Igual a chave no
  `bpt.config.yaml` e ao `id` do contrato.
- `title`: titulo curto e legivel.
- `surfaces`: mapa de lado para superficie. Cada lado declara o `type` da
  superficie e os dados especificos dela. Uma tela declara `route`; um endpoint
  nao precisa de rota publica. Tipos de superficie sao um vocabulario aberto:
  `tela`, `comando-cli`, `endpoint`, `job`, `evento`.
- `contract`: caminho do contrato que este comportamento cumpre
  (`produto/listar`). Um comportamento one-sided sem contrato usa
  `contract: none`.
- `consumes`: lista de contratos que este comportamento le de outros
  comportamentos. Vazia (`[]`) quando ele nao depende de nenhum contrato alheio.
- `status`: mapa de lado para estado. Os estados avancam nesta ordem:
  `draft` (so a spec existe), `ready` (spec fechada, pronta para construir),
  `built` (implementado) e `verified` (cenarios passaram no verify). Cada lado
  caminha no seu proprio ritmo.
- `ui_bindings`: mapa neutro de superficie para handle estavel. E o ponto de
  ancoragem por onde o teste de tela encontra um elemento sem depender do nome
  interno do componente. Continua sendo o QUE (existe um alvo chamado assim), nao
  o COMO.

## As secoes do corpo

Depois do front-matter vem o corpo, sempre nesta ordem:

### Comportamento

Duas coisas em prosa curta: a acao que o comportamento oferece e o resultado que
o usuario obtem. Sem passos internos, sem mencao a como o dado e buscado.

### Regras

As regras de negocio observaveis, em lista. Cada regra tem um id curto e uma
descricao. As mesmas regras aparecem no bloco `rules` do contrato: la elas viram
dado que cada lado implementa, aqui elas viram texto para o leitor. Uma regra
nunca vira codigo compartilhado; o teste bilateral e que mantem os dois lados
honestos.

### Cenarios

Os cenarios descrevem o comportamento observavel no formato dado / quando /
entao. O `entao` e projetado por superficie: um mesmo `dado`/`quando` pode ter um
`entao` marcado com `[contrato]` (o que o backend garante) e outro marcado com
`[tela]` (o que o usuario ve). O verify do backend roda os `entao` de contrato; o
do frontend roda os de tela.

Um cenario testa comportamento, nao implementacao: ele nunca cita nome de funcao
ou de tabela e sobrevive a um refactor completo por dentro.

### Fora de escopo

O que este comportamento deliberadamente nao faz. Serve para cortar suposicao e
impedir que o comportamento cresca sem decisao explicita.

## Exemplo guiado: produto.listar

Abaixo esta a spec real de `produto.listar`, campo a campo.

```markdown
---
id: produto.listar
title: Listar produtos
surfaces:
  frontend:
    type: tela
    route: /produtos
  backend:
    type: endpoint
contract: produto/listar
consumes: []
status:
  backend: draft
  frontend: draft
ui_bindings:
  frontend:
    campo-busca: busca-produtos
    lista-resultados: lista-produtos
    rotulo-total: total-produtos
---

# Comportamento

O cliente lista os produtos disponiveis e pode filtrar por um texto de busca.
O resultado vem paginado, com o total de itens encontrados.

# Regras

- ordenacao: os itens saem ordenados por nome em ordem ascendente.
- busca-case-insensitive: a busca ignora a diferenca entre maiusculas e
  minusculas.

# Cenarios

## Listagem sem busca

- Dado que existem produtos disponiveis
- Quando o cliente abre a listagem sem informar busca
- Entao [contrato] retorna a primeira pagina com ate 20 itens, ordenados por
  nome ascendente, e o total de itens
- Entao [tela] a lista de resultados mostra os produtos em ordem de nome e
  exibe o total encontrado

## Busca por texto

- Dado que existem produtos cujo nome contem "cafe" em qualquer caixa
- Quando o cliente informa "CAFE" no campo de busca
- Entao [contrato] retorna apenas os itens cujo nome casa com o texto,
  ignorando a caixa
- Entao [tela] a lista de resultados mostra somente os produtos que casam com
  a busca

## Parametro invalido

- Dado que o cliente pede uma pagina menor que 1
- Quando a requisicao chega
- Entao [contrato] responde com o erro PARAMETRO_INVALIDO

# Fora de escopo

- Ordenacao por outros campos alem de nome.
- Detalhe de um produto individual (isso e produto.detalhar).
- Estoque em tempo real.
```

### Lendo o front-matter do exemplo

- `id: produto.listar` e `title: Listar produtos`: a identidade, identica a
  chave no config e ao id do contrato.
- `surfaces`: o comportamento aparece como `tela` no frontend, na rota
  `/produtos`, e como `endpoint` no backend. O mesmo comportamento, duas
  superficies.
- `contract: produto/listar`: aponta para
  `packages/contracts/produto/listar/contract.yaml`, que fica no mesmo diretorio.
- `consumes: []`: `produto.listar` nao le nenhum contrato de outro comportamento.
  (Ja `produto.detalhar` teria `produto/listar` aqui se dependesse do contrato
  dele.)
- `status`: ambos os lados comecam em `draft`. Conforme o trabalho anda, cada
  lado sobe pela escada `draft` para `ready` para `built` para `verified` no seu
  proprio ritmo.
- `ui_bindings`: para a superficie de tela, os handles estaveis
  (`busca-produtos`, `lista-produtos`, `total-produtos`) permitem que o teste de
  tela encontre os elementos sem saber o nome do componente que os renderiza.

### Lendo o corpo do exemplo

- Comportamento: duas frases. Diz a acao (listar e filtrar) e o resultado
  (pagina com total). Nao diz como a busca acontece.
- Regras: `ordenacao` e `busca-case-insensitive` sao as mesmas duas regras do
  bloco `rules` do contrato. A spec descreve; o contrato carrega o dado; cada
  lado implementa; o teste bilateral cobra os dois.
- Cenarios: cada um separa `[contrato]` de `[tela]`. Repare que o cenario de
  parametro invalido so tem `[contrato]`, porque o erro `PARAMETRO_INVALIDO` e
  uma garantia do backend. Nenhum cenario menciona funcao, tabela ou componente.
- Fora de escopo: corta ordenacao alternativa, detalhe de produto e estoque, para
  que ninguem assuma esses comportamentos por conta propria.

## Checklist antes de marcar ready

- O `id` no front-matter bate com o `bpt.config.yaml` e com o contrato.
- Todo lado listado em `surfaces` tem entrada em `status`.
- Existe pelo menos um cenario por superficie ativa, com `[contrato]` e `[tela]`
  onde faz sentido.
- Nenhuma linha da spec cita funcao, tabela, componente, biblioteca ou rota
  interna: so o QUE.
- As regras da spec correspondem ao bloco `rules` do contrato.
- Fora de escopo esta preenchido com o que foi deliberadamente deixado de fora.
