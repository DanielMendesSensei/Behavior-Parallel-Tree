#!/usr/bin/env python3
"""Validador de referencia do Behavior Parallel Tree (BPT).

Ferramenta de desenvolvimento (tooling), NAO a stack do app. Le bpt.config.yaml
e a arvore de arquivos e roda as 7 invariantes do nucleo. Nenhum efeito colateral:
so le, valida e reporta. Um adapter real pode reimplementar isto na sua stack.

Uso:
    ./bpt validate                 # valida o projeto no diretorio atual
    python3 tools/bpt/validate.py [caminho-da-raiz]

Saida:
    exit 0  -> tudo valido (pode haver avisos)
    exit 1  -> uma ou mais invariantes violadas

Dependencia unica: PyYAML (pip install pyyaml). E tooling, trocavel.
"""
import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "erro: PyYAML nao encontrado. Instale com: pip install pyyaml\n"
        "(e dependencia de tooling do validador, nao da stack do app)\n"
    )
    raise SystemExit(2)

ID_RE = re.compile(r"^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*){1,2}$")  # 2 a 3 segmentos
SUPPORTED_SCHEMA = {"bpt/v1"}

# Acumuladores de diagnostico.
ERRORS = []
WARNINGS = []


def err(inv, msg):
    ERRORS.append("[INV %s] %s" % (inv, msg))


def warn(inv, msg):
    WARNINGS.append("[INV %s] %s" % (inv, msg))


def load_config(root):
    path = os.path.join(root, "bpt.config.yaml")
    if not os.path.exists(path):
        err(0, "bpt.config.yaml nao encontrado em %s" % root)
        return None
    with open(path, encoding="utf-8") as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            err(0, "bpt.config.yaml invalido: %s" % e)
            return None


def node_path(node_id):
    return node_id.replace(".", "/")


def collect_dep_ids(node):
    """Retorna a lista plana de ids referenciados em deps (lista ou por lado) + consumes."""
    refs = []
    deps = node.get("deps", [])
    if isinstance(deps, dict):
        for side_deps in deps.values():
            refs.extend(side_deps or [])
    elif isinstance(deps, list):
        refs.extend(deps)
    refs.extend(node.get("consumes", []) or [])
    return refs


def build_edges(nodes_by_id):
    """Arestas dependente -> dependencia, a partir de deps e consumes."""
    edges = {}
    for nid, node in nodes_by_id.items():
        edges[nid] = set(r for r in collect_dep_ids(node) if r in nodes_by_id)
    return edges


def find_cycle(edges):
    """Kahn: se sobrar no com grau de entrada > 0, ha ciclo. Devolve um caminho de ciclo."""
    indeg = {n: 0 for n in edges}
    for n, deps in edges.items():
        for d in deps:
            indeg[n] += 1  # n depende de d, entao n tem uma aresta de entrada
    queue = [n for n, g in indeg.items() if g == 0]
    seen = 0
    while queue:
        n = queue.pop()
        seen += 1
        for m, deps in edges.items():
            if n in deps:
                indeg[m] -= 1
                if indeg[m] == 0:
                    queue.append(m)
    if seen == len(edges):
        return None
    # ainda ha nos presos: reconstroi um ciclo simples via DFS entre os restantes
    restantes = {n for n, g in indeg.items() if g > 0}
    return _trace_cycle(edges, restantes)


def _trace_cycle(edges, restantes):
    start = next(iter(restantes))
    path = [start]
    seen = {start}
    cur = start
    while True:
        nxt = next((d for d in edges[cur] if d in restantes), None)
        if nxt is None:
            return path
        if nxt in seen:
            return path[path.index(nxt):] + [nxt]
        path.append(nxt)
        seen.add(nxt)
        cur = nxt


def waves(edges):
    """Ordena em ondas topologicas (o que o adapter roda em paralelo por onda)."""
    indeg = {n: len(deps) for n, deps in edges.items()}
    result = []
    remaining = dict(indeg)
    while remaining:
        layer = sorted(n for n, g in remaining.items() if g == 0)
        if not layer:
            return None  # ciclo
        result.append(layer)
        for n in layer:
            del remaining[n]
        for n in list(remaining):
            remaining[n] = len([d for d in edges[n] if d in remaining])
    return result


def validate(root):
    cfg = load_config(root)
    if cfg is None:
        return

    # INV 1: schema presente e suportado.
    schema = cfg.get("schema")
    if not schema:
        err(1, "campo 'schema' ausente em bpt.config.yaml")
    elif schema not in SUPPORTED_SCHEMA:
        err(1, "schema '%s' nao suportado (suportados: %s)" % (schema, ", ".join(sorted(SUPPORTED_SCHEMA))))

    sides_cfg = cfg.get("sides", {}) or {}
    contracts_root = (cfg.get("contracts", {}) or {}).get("root", "packages/contracts")
    nodes = cfg.get("nodes", []) or []

    nodes_by_id = {}
    for node in nodes:
        nid = node.get("id")
        if not nid:
            err(2, "no sem 'id' em nodes")
            continue
        # INV 2: id unico e no formato dominio.acao.
        if nid in nodes_by_id:
            err(2, "id duplicado: %s" % nid)
        if not ID_RE.match(nid):
            err(2, "id fora do formato dominio.acao (2 a 3 segmentos, minusculo): %s" % nid)
        nodes_by_id[nid] = node

    for nid, node in nodes_by_id.items():
        sides = node.get("sides") or []
        # INV 3: sides nao vazio e cada lado existe em sides do topo.
        if not sides:
            err(3, "%s: 'sides' vazio" % nid)
        for s in sides:
            if s not in sides_cfg:
                err(3, "%s: lado '%s' nao declarado em sides do topo" % (nid, s))

        # INV 6: nenhum id cai sob pasta de kernel.
        if nid.split(".")[0] == "kernel":
            err(6, "%s: dominio 'kernel' e reservado (kernel fica fora da arvore)" % nid)

        # INV 5: two-sided tem contrato; one-sided tem contract: none.
        contract_field = node.get("contract")
        two_sided = len(sides) >= 2
        if two_sided:
            if contract_field == "none":
                err(5, "%s e two-sided mas declara contract: none" % nid)
        else:
            if contract_field != "none":
                err(5, "%s e one-sided; declare contract: none" % nid)

    # INV 4: refs existem, sem auto-dependencia, grafo aciclico.
    for nid, node in nodes_by_id.items():
        for ref in collect_dep_ids(node):
            if ref == nid:
                err(4, "%s depende de si mesmo" % nid)
            if ref not in nodes_by_id:
                err(4, "%s referencia id inexistente: %s" % (nid, ref))
    edges = build_edges(nodes_by_id)
    cycle = find_cycle(edges)
    if cycle:
        err(4, "ciclo de dependencia: %s" % " -> ".join(cycle))

    # INV 7: trio de arquivos existe (contrato + spec + pasta por lado).
    for nid, node in nodes_by_id.items():
        sides = node.get("sides") or []
        p = node_path(nid)
        two_sided = len(sides) >= 2 and node.get("contract") != "none"
        spec = os.path.join(root, contracts_root, p, "spec.md")
        if not os.path.exists(spec):
            err(7, "%s: spec ausente em %s" % (nid, os.path.relpath(spec, root)))
        if two_sided:
            contract = os.path.join(root, contracts_root, p, "contract.yaml")
            if not os.path.exists(contract):
                err(7, "%s: contract.yaml ausente em %s" % (nid, os.path.relpath(contract, root)))
        for s in sides:
            side_root = (sides_cfg.get(s) or {}).get("root", os.path.join("apps", s, "behaviors"))
            folder = os.path.join(root, side_root, p)
            if not os.path.isdir(folder):
                err(7, "%s: pasta do lado '%s' ausente em %s" % (nid, s, os.path.relpath(folder, root)))

    # Informativo: ondas de paralelismo (o nucleo deriva, o adapter percorre).
    if not ERRORS:
        w = waves(edges)
        if w:
            print("ondas de paralelismo (o adapter percorre nesta ordem):")
            for i, layer in enumerate(w, 1):
                print("  onda %d: %s" % (i, ", ".join(layer)))


def main(argv):
    root = os.path.abspath(argv[1]) if len(argv) > 1 else os.getcwd()
    print("bpt validate: %s" % root)
    validate(root)
    for w in WARNINGS:
        print("aviso  %s" % w)
    if ERRORS:
        for e in ERRORS:
            print("ERRO   %s" % e)
        print("\nfalhou: %d erro(s), %d aviso(s)" % (len(ERRORS), len(WARNINGS)))
        return 1
    print("\nok: bpt.config.yaml e a arvore passaram nas 7 invariantes (%d aviso(s))" % len(WARNINGS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
