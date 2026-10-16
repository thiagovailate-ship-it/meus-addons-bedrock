#!/usr/bin/env python3
"""Calibra as regras de check_entity_fields.py contra o conteudo vanilla.

Uma regra de validacao so vale se o proprio conteudo da Mojang passar por ela.
Este script aplica cada regra candidata a TODAS as entidades de
behavior_pack/entities do bedrock-samples e imprime quantas violacoes cada uma
produz, com exemplos.  Regras com violacoes em vanilla sao falsos positivos e
nao podem virar FAIL.

Uso:
    python3 tools/calibrate_entity_rules.py [caminho-do-bedrock-samples]

Sem argumento usa /tmp/refs/bedrock-samples.
"""
from __future__ import annotations

import collections
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bedrock_names as bn  # noqa: E402
import check_entity_fields as cef  # noqa: E402

FORMS = os.path.join(HERE, ".forms", "entity_fields.json")
DEFAULT_SAMPLES = "/tmp/refs/bedrock-samples"


def load_jsonc(path):
    """Os samples vanilla usam comentarios // e /* */, que nao sao JSON puro."""
    text = open(path, encoding="utf-8").read()
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"(?m)//.*$", "", text)
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return json.loads(text)


def component_sections(doc):
    entity = doc.get("minecraft:entity") or {}
    comps = entity.get("components")
    if isinstance(comps, dict):
        yield "components", comps
    for group, body in (entity.get("component_groups") or {}).items():
        if isinstance(body, dict):
            yield f"component_groups.{group}", body


def main(argv):
    samples = argv[1] if len(argv) > 1 else DEFAULT_SAMPLES
    forms_path = FORMS
    if not os.path.isfile(forms_path):
        print("rode tools/vendor_forms.py antes de calibrar", file=sys.stderr)
        return 1
    forms = json.load(open(forms_path, encoding="utf-8"))

    files = sorted(glob.glob(os.path.join(samples, "behavior_pack", "entities", "*.json")))
    if not files:
        print(f"nenhuma entidade em {samples}", file=sys.stderr)
        return 1

    violations = collections.defaultdict(list)
    scanned = 0
    parsed = 0
    for path in files:
        scanned += 1
        try:
            doc = load_jsonc(path)
        except Exception:  # noqa: BLE001
            continue
        if "minecraft:entity" not in doc:
            continue
        parsed += 1
        name = os.path.basename(path)
        fv = doc.get("format_version", "0.0.0")
        # Regra E (FAIL): o checker REAL inteiro, aplicado ao vanilla.  E a
        # calibracao mais forte disponivel - testa as regras de producao em vez
        # de uma reimplementacao delas, e cobre as regras de profundidade
        # (entity_types, membros de objetos aninhados, enums folha) que o segundo
        # log real do cliente provou serem fatais.
        real_fails, _ = cef.check_doc(doc, name, forms)
        for msg in real_fails:
            violations["E_checker_real_no_vanilla"].append(msg)
        for _label, comps in component_sections(doc):
            for comp, body in comps.items():
                # Regra D (FAIL, gated): componente que o cliente nao parseia mais
                since = bn.REMOVED_COMPONENT_SINCE.get(comp)
                if since and bn.version_at_least(fv, since):
                    violations["D_componente_removido"].append(f"{name} fv={fv} {comp}")
                if not isinstance(body, dict):
                    continue
                # Regra C (FAIL, gated): campos float-range fora do formato objeto
                for field, gating in (bn.FLOAT_RANGE_FIELDS.get(comp) or {}).items():
                    if field in body and bn.version_at_least(fv, gating) and not isinstance(body[field], dict):
                        violations["C_float_range_nao_objeto"].append(
                            f"{name} fv={fv} {comp}.{field}={json.dumps(body[field])[:30]}"
                        )
                spec = forms.get(comp)
                if spec is None:
                    continue
                declared = spec.get("fields") or {}
                if not declared:
                    continue
                for field, value in body.items():
                    info = declared.get(field)
                    # Regra A (aviso): campo ausente do form oficial
                    if info is None:
                        violations["A_campo_nao_declarado"].append(f"{name} {comp}.{field}")
                        continue
                    # Regra B (aviso): tipo divergente do form
                    if info.get("type") == "object" and not isinstance(value, dict):
                        violations["B_object_recebeu_escalar"].append(
                            f"{name} {comp}.{field}={json.dumps(value)[:40]}"
                        )

    print(f"entidades vanilla lidas: {parsed}/{scanned} em {samples}")
    print()
    severity = {
        "E_checker_real_no_vanilla": "FAIL",
        "C_float_range_nao_objeto": "FAIL",
        "D_componente_removido": "FAIL",
        "A_campo_nao_declarado": "aviso",
        "B_object_recebeu_escalar": "aviso",
    }
    exit_code = 0
    for rule in ["E_checker_real_no_vanilla", "C_float_range_nao_objeto",
                 "D_componente_removido",
                 "A_campo_nao_declarado", "B_object_recebeu_escalar"]:
        items = violations.get(rule, [])
        sev = severity[rule]
        if sev == "FAIL":
            verdict = "LIMPA no vanilla -> regra confiavel" if not items else (
                f"{len(items)} violacoes no vanilla -> REGRA QUEBRADA")
            if items:
                exit_code = 1
        else:
            verdict = (f"{len(items)} divergencias -> mantida como {sev} "
                       f"(forms oficiais sao incompletos/lenientes)") if items else "sem divergencias"
        print(f"regra {rule}: {verdict}")
        for sample in items[:6]:
            print(f"    ex.: {sample}")
        if len(items) > 6:
            print(f"    ... +{len(items) - 6}")
        print()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
