---
id: produto.listar
title: Listar produtos
surfaces:
  frontend: { type: tela, route: /produtos }
  backend:  { type: endpoint }
contract: produto/listar
consumes: []
status: { backend: draft, frontend: draft }   # draft -> ready -> built -> verified, por lado
# binding de UI: mapa neutro superficie -> handle estavel (o verify do frontend usa)
ui_bindings:
  lista-produtos: lista-produtos
  estado-vazio: estado-vazio
---

## Comportamento
Acao: o usuario abre /produtos. Resultado: ve a lista paginada de produtos disponiveis.

## Regras
- So produtos disponiveis, ordem por nome crescente.
- Busca por nome, sem diferenciar caixa.
- Paginacao padrao 20, teto 100.

## Cenarios (dado / quando / entao, por superficie)
- catalogo com itens: dado produtos disponiveis, quando abre /produtos,
  entao [contrato] output.total > 0 e [tela] mostra a primeira pagina.
- catalogo vazio: dado nenhum produto, quando abre /produtos,
  entao [tela] mostra estado vazio e nao mostra paginacao.
- parametro invalido: dado tamanho 500, quando carrega,
  entao [contrato] erro PARAMETRO_INVALIDO e [tela] mostra "nao foi possivel carregar".

## Fora de escopo
- Criar, editar, excluir produto (outros comportamentos).
- Detalhar um produto (produto.detalhar).
