#!/usr/bin/env python3
"""Bump coerente da versao dos dois manifests do PALEOFRONTIER.

Existir como ferramenta e deliberate: bumpar a versao do pacote tem um detalhe
que quebra o add-on em silencio.  O BP depende do RP POR UUID, e dependencia por
UUID casa a versao EXATA.  Bumpar o RP sem bumpar a dependencia no BP faz a
dependencia deixar de resolver - e o BP nao ativa, sem mensagem obvia.

Manter a mesma versao tambem tem custo: o cliente (sobretudo iOS) pode conservar
o pacote antigo em cache e nao substitui-lo ao importar o .mcaddon corrigido.

Uso:
    python3 tools/bump_version.py 1.0.2
    python3 tools/bump_version.py            # so valida a coerencia atual
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BP = os.path.join(ROOT, "behavior_pack", "manifest.json")
RP = os.path.join(ROOT, "resource_pack", "manifest.json")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def write(path, doc):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")


def parse(text):
    parts = text.strip().split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise SystemExit(f"versao invalida: '{text}' (esperado MAJOR.MINOR.PATCH)")
    return [int(p) for p in parts]


def report(bp, rp):
    """Devolve a lista de incoerencias entre os dois manifests."""
    problems = []
    rp_version = rp["header"]["version"]
    if bp["header"]["version"] != rp_version:
        problems.append(
            f"header BP {bp['header']['version']} != header RP {rp_version}")
    for tag, manifest in (("BP", bp), ("RP", rp)):
        for module in manifest["modules"]:
            if module["version"] != manifest["header"]["version"]:
                problems.append(
                    f"{tag}: modulo '{module['type']}' {module['version']} != "
                    f"header {manifest['header']['version']}")
    deps = [d for d in bp.get("dependencies", []) if "uuid" in d]
    if not any(d["uuid"] == rp["header"]["uuid"] for d in deps):
        problems.append("BP nao depende do UUID do header do RP")
    for dep in deps:
        if dep["uuid"] == rp["header"]["uuid"] and dep.get("version") != rp_version:
            problems.append(
                f"BP depende do RP na versao {dep.get('version')} mas o RP esta em "
                f"{rp_version}: a dependencia nao resolve e o BP nao ativa")
    return problems


def main(argv):
    bp, rp = read(BP), read(RP)
    current = bp["header"]["version"]

    if len(argv) < 2:
        problems = report(bp, rp)
        print(f"[bump] versao atual: {'.'.join(map(str, current))}")
        for line in problems:
            print(f"[FAIL] {line}")
        return 1 if problems else 0

    target = parse(argv[1])
    if target == current:
        print(f"[bump] ja esta em {'.'.join(map(str, target))}; nada a fazer")
        return 0

    rp["header"]["version"] = list(target)
    for module in rp["modules"]:
        module["version"] = list(target)

    bp["header"]["version"] = list(target)
    for module in bp["modules"]:
        module["version"] = list(target)
    for dep in bp.get("dependencies", []):
        if dep.get("uuid") == rp["header"]["uuid"]:
            dep["version"] = list(target)

    problems = report(bp, rp)
    if problems:
        for line in problems:
            print(f"[FAIL] {line}")
        return 1

    write(RP, rp)
    write(BP, bp)
    print(
        f"[bump] {'.'.join(map(str, current))} -> {'.'.join(map(str, target))}: "
        f"header BP/RP, {len(bp['modules']) + len(rp['modules'])} modulos e a "
        f"dependencia BP->RP por UUID"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
