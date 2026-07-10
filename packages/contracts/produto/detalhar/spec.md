---
id: produto.detalhar
title: Detalhar produto
surfaces:
  frontend: { type: tela, route: /produtos/:produtoId }
  backend:  { type: endpoint }
contract: produto/detalhar
consumes: [produto.listar]
status: { backend: draft, frontend: draft }
ui_bindings:
  detalhe-produto: detalhe-produto
  aviso-indisponivel: aviso-indisponivel
---

## Comportamento
Acao: o usuario clica em um produto na lista. Resultado: ve a pagina de detalhe do produto.

## Regras
- Mostra nome, descricao, preco e disponibilidade.
- Produto indisponivel aparece com aviso e sem botao de compra.

## Cenarios (dado / quando / entao, por superficie)
- produto existente: dado um produtoId valido, quando abre a tela,
  entao [contrato] output.id igual ao pedido e [tela] mostra nome e preco.
- produto inexistente: dado um produtoId que nao existe, quando abre a tela,
  entao [contrato] erro PRODUTO_NAO_ENCONTRADO e [tela] mostra "produto nao encontrado".
- produto indisponivel: dado um produto sem estoque, quando abre a tela,
  entao [tela] mostra aviso de indisponivel e nao mostra a acao de compra.

## Fora de escopo
- Listar produtos (produto.listar).
- Adicionar ao carrinho (outro comportamento).
