# Validador BPT

`tools/bpt/validate.py` e o validador de referencia do template. Ele e **tooling**, nao a stack do app: existe para checar a arvore e derivar as ondas de paralelismo, e pode ser trocado por qualquer implementacao equivalente sem afetar o codigo de producao.

## Uso

```
./bpt validate
```

O comando le o `bpt.config.yaml` da raiz mais os contratos e specs, roda as 7 invariantes e, no final, imprime as ondas de paralelismo.

## Dependencia

Dependencia unica: **PyYAML**.

```
pip install pyyaml
```

Python 3 + PyYAML e proposital: e um tooling leve e trocavel, deliberadamente desacoplado da linguagem, do framework e do runtime do app.

## As 7 invariantes

1. Schema presente e suportado (`bpt/v1`).
2. Cada `id` e unico e segue o formato `dominio.acao`.
3. `sides` nao e vazio e cada lado declarado existe.
4. Refs de `deps`/`consumes` existem, sem auto-dependencia, e o grafo e aciclico (Kahn aponta o ciclo).
5. No two-sided tem contrato; no one-sided declara `contract: none`.
6. Nenhum `id` mora sob pasta de kernel (o dominio `kernel` e reservado).
7. Trio de arquivos existe: `contract.yaml` + `spec.md` + a pasta do no por lado.

## Ondas de paralelismo

Alem de validar, o nucleo deriva as **ondas** por ordem topologica do grafo de dependencias e as imprime. Cada onda e o conjunto de nos que podem ser construidos em paralelo naquele passo, com as ondas de kernel primeiro. E o mapa que o adapter usa para paralelizar o trabalho respeitando o DAG.
