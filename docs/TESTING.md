# Testes e Verificacao no BPT

O BPT tem um objetivo unico: minimizar o contexto necessario para fazer uma mudanca. O modelo de testes serve a esse objetivo. Cada tipo de teste tem um lugar fixo, uma responsabilidade estreita e uma regra clara sobre se ele sobrevive ou nao a um refactor. Quando isso e respeitado, um agente consegue trabalhar um comportamento como ilha isolada sem carregar o resto do sistema na cabeca.

Este documento descreve as tres camadas de teste, como o cenario e projetado por superficie, como o `verify` do adapter consome os cenarios da spec, o teste de contrato bilateral, as auditorias opcionais (property e mutation) e a revisao semantica como portao final.

## As tres camadas

Sao tres camadas com papeis distintos. A regra que separa uma da outra e simples: o cenario testa o **que** (comportamento observavel), o unitario testa o **como** (internals), o fluxo testa a **jornada** (varios comportamentos juntos).

| Camada | O que testa | Onde mora | Sobrevive a refactor? |
| --- | --- | --- | --- |
| Cenario | Comportamento observavel: o contrato e a superficie. Nunca cita nome de funcao, classe ou tabela. | `packages/contracts/<caminho>/spec.md`, na secao Cenarios | Sim. So muda quando o comportamento observavel muda. |
| Unitario | Internals: o como. Logica interna, ramos, casos de borda de uma unidade de codigo. | Ao lado do codigo, dentro de `src/` do no | Nao. E descartavel: muda junto com o codigo que ele cobre. |
| Fluxo / e2e | Jornada que atravessa N comportamentos, ancorada num PRD. | `packages/contracts/_flows/<prd>/` | Parcial. Sobrevive a refactor interno; muda quando a jornada de negocio muda. |

A intuicao por tras da coluna "sobrevive a refactor": o cenario e o unitario existem em niveis de estabilidade diferentes de proposito. O cenario e um contrato com o mundo e deve durar; o unitario e um andaime que voce joga fora quando reescreve a unidade. Se um refactor interno quebra um cenario, o cenario estava olhando para o lugar errado (para o como, nao para o que).

## Cenario: so contrato e superficie

O cenario e a camada central do BPT porque e a unica que mora na fronteira do comportamento, e nao dentro dele. Ele fala de duas coisas, e apenas essas duas:

- O **contrato** (`contract.yaml`): input, output, `rules`, `errors`, autorizacao.
- A **superficie** (declarada na spec: tela, endpoint, comando-cli, job, evento).

Um cenario nunca menciona o nome de uma funcao, de um metodo, de uma tabela ou de um componente. Se ele precisar desses nomes para ser escrito, ele virou um teste unitario disfarcado. O texto de um cenario deve continuar valido mesmo que toda a implementacao interna do no seja reescrita do zero em outra stack.

Os cenarios moram na secao **Cenarios** da `spec.md`, escritos em dado / quando / entao. Cada cenario marca a que ele pertence:

- `[contrato]`: verificavel na fronteira de dados, independente de superficie visual. E o que o backend roda.
- `[tela]` (ou a superficie equivalente): verificavel na superficie concreta. E o que o frontend roda.

### O "entao" e projetado por superficie

Um mesmo cenario tem um so "dado" e um so "quando", mas o "entao" e **projetado por superficie**. O comportamento observavel e um; a forma de observa-lo depende de onde voce olha.

Exemplo, para `produto.listar` com a regra `ordenacao: itens por nome ascendente`:

- Projecao `[contrato]` (verify do backend): o `entao` afirma sobre o `output` do contrato. "Entao a lista `itens` vem ordenada por `nome` ascendente e `total` reflete a contagem." Roda contra a resposta de dados, sem tela.
- Projecao `[tela]` (verify do frontend): o `entao` afirma sobre a superficie. "Entao a tela de produtos mostra os itens na ordem de nome ascendente." Roda contra a superficie renderizada.

O `verify` do backend executa as projecoes `[contrato]`; o `verify` do frontend executa as projecoes `[tela]`. Cada lado prova a mesma verdade na sua propria linguagem. Isso e o que permite espelhar o comportamento nos dois lados sem duplicar a spec: a spec e uma so, as projecoes e que se separam.

### Binding de UI: verify de frontend deterministico

Um cenario `[tela]` nao pode depender de texto visivel ou de estrutura de layout, senao ele quebra a cada ajuste de copy ou de CSS, e volta a nao sobreviver a refactor. Para manter o `verify` de frontend deterministico, a spec declara `ui_bindings`: um mapa neutro de **superficie para handle estavel**.

O handle e um identificador estavel (por exemplo um test id) que o cenario referencia por nome logico. O adapter, no `codegen` ou no `execute`, materializa esse handle na superficie concreta da stack. O cenario diz "o handle `lista-produtos` contem os itens ordenados"; ele nao diz "o `<ul class=...>` contem". Assim o texto do cenario permanece estavel e o `verify` do frontend tem um alvo deterministico para inspecionar.

## Unitario: descartavel, colado ao codigo

O unitario testa os internals: ramos condicionais, casos de borda de uma funcao, invariantes de uma estrutura de dados interna. Ele mora dentro de `src/` do no, ao lado do codigo que cobre, e pertence ao mesmo escopo de contexto do codigo.

A propriedade que define o unitario e ser **descartavel**. Quando voce reescreve a unidade, voce reescreve (ou deleta) os testes unitarios dela sem cerimonia. Eles nao sao um contrato com ninguem de fora do no; sao ferramenta do autor da unidade. Por isso eles podem e devem citar nomes de funcao e de estrutura interna: e exatamente o que estao testando.

Um unitario nunca vaza para fora do no. Se um teste precisa conhecer o internals de dois comportamentos ao mesmo tempo, ele nao e unitario: ou virou cenario (na fronteira) ou virou fluxo (atravessando comportamentos).

## Fluxo / e2e: a jornada atraves de N comportamentos

O teste de fluxo cobre uma jornada de negocio que atravessa varios comportamentos, ancorada num PRD. Ele mora em `packages/contracts/_flows/<prd>/`, fora de qualquer no, porque nenhum no e dono dele: o dono e o nivel do PRD.

Exemplo: uma jornada de compra que passa por `produto.listar`, `produto.detalhar`, `carrinho.revisar` e `checkout.pagar` vive em `packages/contracts/_flows/checkout-v1/`. Ela nao pertence a nenhum desses nos individualmente; ela verifica que a costura entre eles entrega a jornada prometida no PRD.

O fluxo e o unico teste autorizado a conhecer varios comportamentos de uma vez. Justamente por isso ele e caro em contexto e deve ser raro: um por jornada de PRD, nao um por combinacao possivel de nos.

## Teste de contrato bilateral, consumer-driven

Um no two-sided existe nos dois lados com a mesma identidade e a mesma spec, ligados pelo contrato neutro. A forma do contrato (a estrutura de `input` e `output`) pode ate ser conferida por comparacao estrutural, mas **forma nao basta**: dois lados podem concordar na forma e discordar no significado. O backend pode ordenar por nome descendente enquanto o frontend espera ascendente; ambos respeitam a forma `output` e ainda assim o comportamento esta quebrado.

Por isso todo no two-sided passa por um **teste de contrato bilateral, consumer-driven**, antes de ser dado por pronto:

- **Consumer-driven**: o consumidor (tipicamente o frontend, ou o no que aparece em `consumes`) declara o que espera do contrato, incluindo as `rules` que dependem daquele significado. Essa expectativa e a fonte da verdade do teste.
- **Bilateral**: o provedor (tipicamente o backend) e verificado contra essa expectativa. Os dois lados sao mantidos honestos pelo mesmo conjunto de cenarios de contrato, cada um provando a sua projecao (`[contrato]` de um lado, `[tela]` do outro).

E aqui que a decisao de tratar regra de negocio compartilhada como **dado** fecha o ciclo: as `rules` do contrato descrevem o significado, cada lado implementa, e o teste de contrato bilateral e o que garante que as duas implementacoes concordam sobre esse significado. Nao existe pacote de dominio em codigo compartilhado; existe o dado no bloco `rules` mais o teste bilateral que o mantem verdadeiro dos dois lados.

O adapter honra isso na orquestracao: um no two-sided so e considerado pronto depois que o teste de contrato bilateral passa. Enquanto ele nao passa, os dois lados nao estao de fato espelhados.

## Property e mutation: auditoria opcional

Property tests (gerar muitas entradas e checar invariantes) e mutation tests (introduzir defeitos e conferir se a suite os pega) sao **auditorias da suite**, nao parte do loop rapido de construcao do no.

- Ficam **fora do loop rapido** `codegen -> plan -> execute -> verify -> review`. Eles nao decidem se um no esta pronto no dia a dia.
- Servem para auditar a qualidade dos testes existentes: property tests exploram o espaco de entrada alem dos cenarios escritos; mutation tests medem se os cenarios e unitarios realmente pegariam uma regressao.
- Sao opcionais no v1 e nao entram no `bpt.config.yaml`. Rode-os como passo separado, periodico, quando quiser confianca extra na suite.

## Revisao semantica: portao depois do verde

Verde nao e pronto. Depois que os cenarios, os unitarios e (para two-sided) o contrato bilateral passam, o no ainda atravessa a **revisao semantica** (`review`), que e um portao **depois do verde**.

A revisao semantica pergunta o que os testes nao conseguem perguntar: a implementacao faz o que a spec queria dizer, e nao apenas o que ela literalmente checou? A direcao de import esta respeitada? O comportamento honra o espirito das `rules`? Ela roda como ultimo estagio do loop e pode devolver findings, que voltam como feedback para uma nova tentativa (ate 3; a 3a falha marca o no como `blocked` com o worktree preservado).

## Como o verify hook consome os cenarios

O `verify` e o hook do adapter que transforma a spec em veredito. Ele nao inventa o que testar: ele **le os cenarios da `spec.md`** e executa a projecao correspondente ao lado em que esta rodando.

Fluxo do `verify`, por no e por lado, chaveado em (lado, id):

1. Le a `spec.md` do contrato ligado ao no e extrai os cenarios da secao Cenarios.
2. Seleciona a projecao do lado: no backend, as marcadas `[contrato]`; no frontend, as marcadas `[tela]`.
3. Executa a projecao contra a implementacao daquele lado. No frontend, resolve os alvos via `ui_bindings` (superficie para handle estavel), o que torna a verificacao deterministica.
4. Roda os testes unitarios do no daquele lado.
5. Checa a **direcao de import** (enforcement de kernel): reprova `kernel -> behaviors/*` e `behaviors/a -> behaviors/b`; permite `behaviors/* -> kernel`, `behaviors/* -> contracts`, `kernel -> kernel` e `kernel -> contracts`.
6. Para no two-sided, o pronto so vem depois que o teste de contrato bilateral tambem passa.

O `verify` reporta status pelo protocolo neutro do adapter: exit 0 significa que rodou (o veredito vem no payload JSON de stdout), exit diferente de 0 significa que o proprio adapter quebrou. No adapter placeholder, `verify` retorna status ok vazio; um adapter real de stack e quem de fato executa as projecoes, os unitarios e a checagem de import.
