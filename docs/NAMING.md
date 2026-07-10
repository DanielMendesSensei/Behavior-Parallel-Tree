# Identidade e Naming no BPT

Este documento define como um comportamento ganha nome no Behavior Parallel Tree. O `id` e a coisa mais importante de todo o template: ele e a identidade que atravessa os dois lados (backend e frontend), amarra o contrato, nomeia a pasta e chaveia a execucao. Acertar o `id` e acertar o recorte do comportamento, e recortar bem e o que mantem cada comportamento como uma ilha isolada de contexto minimo.

## Gramatica do id

Um `id` tem a forma:

```
dominio.acao
```

Regras:

- Tudo minusculo.
- O ponto (`.`) separa segmentos.
- Hifen simples (`-`) so aparece dentro de um segmento composto (exemplo: `nota-fiscal`).
- 2 a 3 segmentos. Prefira 2. Use 3 apenas quando um subdominio real existe no modelo mental (exemplo: `pagamento.cartao.autorizar`).
- O ultimo segmento e sempre a acao (verbo). Os segmentos anteriores formam o dominio.

Regex conceitual (a intencao, nao um parser rigido):

```
^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*){1,2}$
```

Ou seja: cada segmento comeca por letra, aceita letra, digito e hifen interno, e ha de 2 a 3 segmentos ligados por ponto.

Exemplos validos:

```
produto.listar
produto.detalhar
carrinho.revisar
pagamento.cartao.autorizar
nota-fiscal.emitir
```

Exemplos invalidos:

```
listar                 (falta o dominio)
produto                (falta a acao)
Produto.Listar         (maiusculas)
produto_listar         (underscore no lugar do ponto)
produto.listar.itens.paginado   (4 segmentos, granularidade errada)
```

### dominio = substantivo do modelo mental do usuario

O dominio e o nome da coisa como o usuario pensa nela, nao como o banco ou o framework a modela. Escolha o substantivo que apareceria numa conversa com quem usa o produto: `produto`, `carrinho`, `pedido`, `pagamento`. Evite nomes tecnicos de implementacao (`tabela`, `service`, `repository`, `dto`) e evite nomes de camada (`api`, `controller`, `component`).

### acao = verbo no infinitivo

A acao e sempre um verbo no infinitivo, descrevendo o que o comportamento faz do ponto de vista de quem observa o resultado. Um verbo, uma acao.

Lista sugerida de verbos, como guia e nao como portao:

- `listar`: devolve uma colecao, geralmente paginada e filtravel.
- `detalhar`: devolve um item completo por identidade.
- `criar`: nasce uma entidade nova.
- `editar`: altera uma entidade existente.
- `cancelar`: encerra ou invalida algo sem apagar historico.
- `pagar`: fecha uma transacao financeira do lado de quem paga.
- `autorizar`: aprova ou nega uma operacao contra uma regra ou provedor.

Esta lista existe para dar consistencia, nao para limitar. Se o dominio pede um verbo que nao esta aqui (`emitir`, `arquivar`, `duplicar`, `revisar`), use o verbo que descreve a acao com honestidade. O gate real nao e o vocabulario: sao os quatro testes de granularidade abaixo.

## Id imutavel

Uma vez que um `id` existe (pasta criada, contrato escrito, no no `bpt.config.yaml`), ele e imutavel. O `id` e a chave de identidade que liga backend, frontend, contrato, spec e execucao: mudar a string quebra todas essas amarras de uma vez.

Renomear um comportamento nao e uma edicao, e uma migracao. O procedimento de renome (mover pastas nos dois lados, mover contrato e spec, atualizar `deps` e `consumes` de todos os nos que apontam para ele, atualizar a entrada no `bpt.config.yaml`) esta descrito em `MIGRATION.md`. Nao renomeie na mao pasta por pasta.

## Os 4 testes de granularidade

Antes de criar um `id`, passe o comportamento pelos quatro testes. Eles decidem se voce tem um comportamento ou dois disfarcados de um.

### 1. Regra do "e"

Se voce precisa da palavra "e" para descrever o que o comportamento faz, provavelmente sao dois comportamentos. "Listar produtos E aplicar cupom" e `produto.listar` mais outra coisa. Quebre no "e".

### 2. Um verbo, um id

A acao tem exatamente um verbo. Se a descricao natural usa dois verbos ("criar e notificar", "salvar e publicar"), ha dois `ids`. Um deles pode depender do outro via `deps`, mas cada verbo tem sua ilha.

### 3. Uma acao, uma superficie principal, um resultado

Um comportamento produz um resultado observavel por superficie. Se a mesma acao produz resultados conceitualmente diferentes dependendo de um modo ou flag, e sinal de que ha mais de um comportamento. Uma tela composta que le varios contratos nao viola isto: ela consome N comportamentos via `consumes`, ela nao e um comportamento gigante.

### 4. Orcamento de contexto

O teste final e o proprio objetivo do BPT: um agente deveria conseguir construir este comportamento, dos dois lados, carregando so a pasta do no, os contratos que ele consome e o kernel em leitura. Se para implementar o comportamento voce precisa carregar meio sistema na cabeca, o recorte esta grande demais. Encolha ate caber no orcamento de contexto de uma ilha.

## Idioma hibrido

O BPT mistura dois idiomas de proposito, e a fronteira e clara:

- **Chaves estruturais de schema ficam em ingles.** Sao as palavras do proprio BPT, iguais em todo projeto: `kind`, `input`, `output`, `errors`, `sides`, `deps`, `consumes`, `rules`, `version`, `title`, `authorization`, `roles`, `surfaces`, `status`. Elas nao mudam com o dominio.

- **Vocabulario de dominio e ids ficam em portugues.** Sao as palavras do produto: `produto.listar`, `busca`, `pagina`, `tamanho`, `preco`, `disponivel`, `cliente`. Os codigos de erro tambem: `PARAMETRO_INVALIDO`, `NAO_AUTORIZADO`.

A regra pratica: se a palavra descreve o mecanismo do BPT, ingles; se descreve o negocio, portugues. Um `id` e sempre negocio, entao e sempre portugues. Uma chave do contrato e sempre mecanismo, entao e sempre ingles.

Exemplo do contrato mostrando a fronteira:

```
id produto.listar          # id: portugues
kind query                 # chave: ingles
input:                     # chave: ingles
  busca text opcional      # campo de dominio: portugues
  pagina integer default 1 # campo de dominio: portugues
errors:                    # chave: ingles
  PARAMETRO_INVALIDO ...   # codigo de dominio: portugues
```

## Superficies genericas e sides como lista aberta

O `id` nao carrega a superficie. `produto.listar` e o mesmo comportamento quer ele apareca como tela, como endpoint ou como comando de linha. A superficie e declarada na spec (`surfaces`), nao no nome.

As superficies sao genericas:

```
tela | comando-cli | endpoint | job | evento
```

E `sides` e uma lista aberta. Os dois lados que o template nasce conhecendo sao `backend` e `frontend`, mas nada no nucleo trava esse par. Um projeto de linha de comando poderia declarar um no com `sides: [cli]`. Um projeto com worker poderia ter um lado dedicado. O espelho e N:M via contrato, nao um 1:1 rigido entre backend e frontend: o que amarra os lados e a identidade compartilhada (o `id`) e o contrato neutro, nao a quantidade de lados.

O `id` continua sendo a unica identidade, independente de quantos lados existam ou de que superficie cada lado exponha.
