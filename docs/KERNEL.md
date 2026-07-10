# KERNEL

O kernel e a infra transversal que vive **fora da arvore de comportamentos**. Ha um kernel por lado (`apps/backend/kernel`, `apps/frontend/kernel`), declarado em `bpt.config.yaml`. Comportamento e ilha isolada; o kernel e o chao comum embaixo de todas as ilhas.

O objetivo do BPT e minimizar o contexto necessario para fazer uma mudanca. O kernel serve a esse objetivo quando concentra o que e genuinamente compartilhado. Ele **trai** esse objetivo quando vira deposito de conveniencias: cada coisa que sobe ao kernel sem merecer aumenta o contexto de todo mundo. Por isso o kernel e pequeno por design e a barra de entrada e alta.

## A regra de direcao (absoluta)

Existe uma unica direcao permitida:

> **Comportamento importa do kernel. O kernel NUNCA importa de comportamento.**

O kernel nao conhece nenhum comportamento pelo nome. Se voce precisa citar `produto.listar` dentro do kernel, aquilo nao e kernel: e comportamento vazado para o lugar errado. Essa regra e o que mantem cada comportamento uma ilha: mexer em `produto.detalhar` nunca pode reagir de volta pelo kernel e afetar `produto.listar`.

O kernel se descreve sem citar dominio. `auth`, `db`, `config`, `app-shell`, `design-system`: nenhum desses precisa saber o que e um produto.

## O que pertence ao kernel

Infra transversal, usada por muitos comportamentos, sem sabor de dominio:

- **auth**: quem e o usuario, sessao, verificacao de papel (o *mecanismo*, nao a politica de qual papel acessa o que; a politica mora no `authorization` do contrato).
- **db**: conexao, pool, transacao, cliente do banco, runner de migracao (o *encanamento*, nao as tabelas de negocio).
- **config**: leitura de ambiente, flags, segredos, bootstrap.
- **app-shell** (frontend): roteador raiz, layout de moldura, providers globais, tratamento de erro de topo.
- **design-system** (frontend): tokens, componentes primitivos (botao, input, tabela), tema. Sem tela de dominio.

Sinal de que pertence: descreve-se sem nomear comportamento, e transversal, e usado por 2 ou mais comportamentos hoje.

## O que NAO pertence ao kernel

- **Regra de UM comportamento**: se so `produto.listar` usa, mora em `produto.listar`. Nunca sobe "por precaucao".
- **Tipos do contrato**: o tipo neutro vive no `contract.yaml`; a materializacao vive no `__generated__/` do no (via `codegen`). Nao ha tipos de dominio compartilhados no kernel.
- **Uma tela so**: uma tela especifica e um comportamento no frontend, nao design-system. O design-system entrega o botao; a tela de checkout usa o botao.
- **Regra de negocio compartilhada**: vira **dado** no bloco `rules` do contrato, nunca codigo de kernel (secao proprio abaixo).
- **helpers / utils / misc / shared**: pastas guarda-chuva sao proibidas. Ver anti-inchaco.

## Promocao ao kernel: as 3 perguntas

Uma coisa so sobe ao kernel se a resposta e **sim** para as tres:

1. **Ja e usado por 2 ou mais comportamentos hoje?** (uso real, nao futuro imaginado)
2. **E transversal?** (nao pertence a nenhum dominio em particular)
3. **Descreve-se sem citar o nome de nenhum comportamento?**

Qualquer "nao" reprova. "Vai que alguem precisa depois" nao conta como sim na pergunta 1.

## A regra do tres (graduacao)

A promocao acontece na terceira ocorrencia, nao antes:

1. **1a vez**: nasce dentro do comportamento que precisa. Fica la.
2. **2a vez**: outro comportamento precisa do mesmo. **Copie.** Duplicacao e barata; abstracao errada e cara.
3. **3a vez**: um terceiro precisa. Agora sobe ao kernel, e os dois anteriores passam a importar de la.

Copiar na 2a ocorrencia e intencional: e o tempo que voce ganha para ver se as tres copias sao mesmo a mesma coisa ou tres coisas parecidas que vao divergir. Se divergiram, nunca eram kernel.

## Anti-inchaco

O kernel morre de sucesso: quanto mais util, mais gente quer colar coisa nele. Contramedidas:

- **Dono por submodulo**: cada submodulo do kernel (`auth`, `db`, ...) tem um responsavel. Nada entra sem passar pelo dono do submodulo. Isso impede a terra-de-ninguem.
- **Proibido `helpers`, `utils`, `misc`, `shared`**: toda pasta do kernel nomeia uma capacidade transversal concreta. Se voce nao consegue nomear a capacidade, nao e kernel.
- **Mede fan-in**: para cada modulo do kernel, conte quantos comportamentos importam dele (fan-in). Fan-in e a metrica de saude: alto justifica a existencia, baixo e suspeito.
- **Democao**: quando o fan-in de um modulo volta a **1 consumidor**, ele desce de volta para dentro daquele comportamento. Kernel com um consumidor so nao e kernel.
- **Teto**: existe um teto de tamanho por submodulo. Estourar o teto **dispara revisao** obrigatoria (nao um bloqueio automatico, mas um portao humano).
- **Onda de kernel serializada**: mudanca no kernel roda em uma **onda propria, antes** de todas as ondas de comportamento, e vem com **CHANGELOG**. Como o kernel e a base de todo mundo, ele nunca muda em paralelo com quem depende dele; muda primeiro, sozinho, e anuncia a mudanca.

## Regra de negocio compartilhada NAO vira codigo de kernel

Regra de negocio que os dois lados precisam respeitar (ordenacao, arredondamento de preco, case-insensitive de busca) e o exemplo classico de coisa que "parece" kernel. Nao e.

Ela vai como **dado**, no bloco `rules` do contrato:

```yaml
rules:
  - ordenacao: itens por nome ascendente
  - busca-case-insensitive: ignora caixa
```

**Cada lado implementa a regra na sua stack.** Um **teste de contrato bilateral** (consumer-driven) mantem os dois honestos: se o backend ordena e o frontend nao, o teste bilateral reprova.

Por que dado e nao codigo compartilhado:

- Codigo compartilhado de dominio criaria uma dependencia que atravessa os dois lados e fura o espelho. O contrato neutro e justamente a **unica** junta entre backend e frontend.
- A regra fica legivel por qualquer agente sem carregar codigo de outra stack: o contexto continua minimo.
- O nucleo e agnostico de linguagem e runtime; regra como dado sobrevive a isso, codigo nao.

**Quando a regra e complexa demais para caber como dado?** Ela deixa de ser "uma regra" e vira **um comportamento**: crie um no dedicado (ex.: `preco.calcular`) com seu proprio contrato, e os outros nos o consomem via `consumes`. A complexidade ganha uma ilha propria, testes de cenario proprios e uma identidade nas duas arvores. O que voce **nao** faz e esconde-la num modulo de kernel: isso reintroduziria a dependencia de dominio que o BPT existe para eliminar.

## Dados e migracoes

- **Cada comportamento e dono das suas tabelas.** A migracao mora junto do comportamento, dentro da pasta do no.
- O kernel entrega o **encanamento** de banco (conexao, transacao, runner de migracao), nunca tabela de negocio.
- **Tabela tocada por 2 ou mais comportamentos = acoplamento global explicito.** Isso nao e proibido, mas e um evento revisado: precisa ser declarado e passar por revisao, porque quebra o isolamento das ilhas. O padrao e cada tabela ter um dono unico.

## Enforcement no `verify` do adapter

O hook `verify` do adapter checa a direcao de import e reprova o build se o grafo violar a regra. Arestas:

**Permitidas:**

| De | Para |
| --- | --- |
| `behaviors/*` | `kernel` |
| `behaviors/*` | `contracts` |
| `kernel` | `kernel` |
| `kernel` | `contracts` |

**Proibidas:**

| De | Para | Por que |
| --- | --- | --- |
| `kernel` | `behaviors/*` | fura a direcao absoluta |
| `behaviors/a` | `behaviors/b` | comportamento nao importa comportamento; a junta e o contrato |

Comportamento fala com outro comportamento **so** pelo contrato (`consumes`), nunca por import direto de codigo.

O validador estatico reforca isso de outro angulo: o dominio `kernel` e **reservado** (invariante 6 do `./bpt validate`), entao nenhum `id` de no pode nascer sob a pasta de kernel.

## DO vs NAO

**1. Cliente HTTP generico**
DO: `kernel/http` com o cliente base, retry, timeout. NAO: `kernel/produto-api` que sabe montar a chamada de listar produto (isso e do comportamento `produto.listar`).

**2. Componente de tabela**
DO: `design-system/table` (colunas genericas, ordenacao visual). NAO: `design-system/tabela-de-produtos` com colunas `nome, preco, disponivel` (isso e a tela de `produto.listar`).

**3. Regra de ordenacao**
DO: `rules: [ordenacao: itens por nome ascendente]` no contrato, cada lado implementa, teste bilateral guarda. NAO: `kernel/ordenador` com a logica de ordenar produtos.

**4. Verificacao de papel**
DO: `kernel/auth` que responde "qual papel tem esse usuario". NAO: `kernel/auth` decidindo que "cliente pode listar produtos" (essa politica mora em `authorization.roles` do contrato).

**5. Tabela de dados**
DO: migracao de `produtos` dentro de `apps/backend/behaviors/produto/listar/`, dono unico. NAO: migracao de `produtos` em `kernel/db/migrations` como se fosse infra.

**6. Regra complexa demais para dado**
DO: promover o calculo a um no proprio `preco.calcular` com contrato, consumido via `consumes`. NAO: `kernel/precificacao` com a arvore de descontos e impostos.
