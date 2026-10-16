#!/usr/bin/env python3
"""Valida os componentes das entidades contra o vocabulario oficial do Bedrock.

As regras sao **gated por format_version**, porque e assim que o cliente se
comporta: um campo legado continua valido em entidades antigas e passa a ser
rejeitado a partir da versao em que a regra ficou estrita.  O proprio
bedrock-samples traz arquivos legado (bat.json fv 1.26.0 com
`float_duration` em array, creeper.json fv 1.26.0 com `minecraft:pushable`),
entao uma regra nao gated acusaria o conteudo da Mojang - e por isso
`tools/calibrate_entity_rules.py` existe: ele prova que, com o gating abaixo,
nenhuma entidade vanilla viola regra nenhuma.

FAIL (regras calibradas, derivadas dos update notes oficiais):
  - componente que o cliente deixou de parsear (`minecraft:pushable` >= 1.26.10)
  - campo "float range" fora do formato `{"min","max"}` na versao em que ficou
    estrito (`nearest_attackable_target.attack_interval` >= 1.26.0, ...)

AVISO (fontes incompletas/lenientes demais para virar FAIL):
  - campo ausente do form oficial (os forms nao listam tudo: `alert_same_type`
    so aparece em `generated_doNotEdit`, `soft_distance` so na lista do topo)
  - tipo divergente do form (os forms declaram `string`/`object` onde o jogo
    aceita lista/escalar; `tempt.items` e lista no vanilla)
  - campo renomeado que o cliente ainda migra automaticamente (`min_look_time`)

Uso: python3 tools/check_entity_fields.py [dir-de-entidades]
"""
from __future__ import annotations

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bedrock_names as bn  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
FORMS = os.path.join(HERE, ".forms", "entity_fields.json")

# Chaves "minecraft:*" que nao sao componentes (nomes de evento/gatilho).
EVENT_TRIGGERS = frozenset({
    "minecraft:entity",
    "minecraft:entity_born",
    "minecraft:entity_spawned",
    "minecraft:entity_transformed",
    "minecraft:entity_died",
    "minecraft:on_death",
    "minecraft:on_hurt",
    "minecraft:on_target_acquired",
    "minecraft:on_target_escape",
    "minecraft:on_wake_with_owner",
    "minecraft:on_friendly_anger",
    "minecraft:spawn_entity",
})


def kind_ok(expected, value):
    if expected is None:
        return True, ""
    if expected == "object":
        return isinstance(value, dict), "o form declara objeto"
    if expected in ("int", "float", "decimal", "number"):
        if isinstance(value, bool):
            return False, "booleano onde o form declara numero"
        return isinstance(value, (int, float, str)), "o form declara numero"
    if expected == "boolean":
        return isinstance(value, bool), "o form declara true/false"
    if expected == "string":
        return isinstance(value, (str, int, float, list)), "o form declara string"
    if expected == "stringArray":
        return isinstance(value, list), "o form declara lista de strings"
    if expected in ("objectArray", "array", "list"):
        return isinstance(value, (list, dict)), "o form declara lista"
    return True, ""


def component_sections(doc):
    entity = doc.get("minecraft:entity") or {}
    comps = entity.get("components")
    if isinstance(comps, dict):
        yield "components", comps
    for group, body in (entity.get("component_groups") or {}).items():
        if isinstance(body, dict):
            yield f"component_groups.{group}", body


def check_file(path, forms):
    fails, warns = [], []
    doc = json.load(open(path, encoding="utf-8"))
    rel = os.path.relpath(path, ROOT)
    fv = doc.get("format_version", "0.0.0")
    ident = ((doc.get("minecraft:entity") or {}).get("description") or {}).get("identifier", "?")

    for label, comps in component_sections(doc):
        for comp, body in comps.items():
            # ---- FAIL: componente que o cliente nao parseia mais ----------
            since = bn.REMOVED_COMPONENT_SINCE.get(comp)
            if since and bn.version_at_least(fv, since):
                subs = ", ".join(bn.REMOVED_ENTITY_COMPONENTS.get(comp, ()))
                fails.append(
                    f"{rel} {ident} {label}: '{comp}' nao e parseado pelo cliente desde "
                    f"{since} (format_version do arquivo: {fv}); use {subs or 'o substituto oficial'}"
                )
                continue

            if not isinstance(body, dict):
                continue

            # ---- FAIL: campos float-range na versao em que ficaram estritos
            for field, gating in (bn.FLOAT_RANGE_FIELDS.get(comp) or {}).items():
                if field in body and bn.version_at_least(fv, gating) and not isinstance(body[field], dict):
                    fails.append(
                        f"{rel} {ident} {label}: '{comp}.{field}' precisa ser "
                        f'{{"min": ..., "max": ...}} desde {gating} (format_version: {fv}), '
                        f"encontrado {json.dumps(body[field])}"
                    )

            # ---- AVISO: campos renomeados que o cliente ainda migra -------
            for old, new in (bn.RENAMED_COMPONENT_FIELDS.get(comp) or {}).items():
                if old in body:
                    warns.append(
                        f"{rel} {ident} {label}: '{comp}.{old}' foi renomeado para '{new}' "
                        f"(o cliente migra automaticamente, mas vale atualizar)"
                    )

            # ---- AVISO: forms oficiais -----------------------------------
            if not forms:
                continue
            spec = forms.get(comp)
            if spec is None:
                if comp not in EVENT_TRIGGERS:
                    warns.append(f"{rel} {ident} {label}: '{comp}' sem form oficial (nao verificado)")
                continue
            declared = spec.get("fields") or {}
            if not declared:
                continue
            for field, value in body.items():
                info = declared.get(field)
                if info is None:
                    warns.append(f"{rel} {ident} {label}: '{comp}.{field}' nao consta no form oficial")
                    continue
                ok, why = kind_ok(info.get("type"), value)
                if not ok:
                    warns.append(f"{rel} {ident} {label}: '{comp}.{field}' {why}")
    return fails, warns


def main(argv=None):
    argv = argv or sys.argv
    entity_dir = argv[1] if len(argv) > 1 else os.path.join(ROOT, "behavior_pack", "entities")

    forms = None
    if os.path.isfile(FORMS):
        forms = json.load(open(FORMS, encoding="utf-8"))
    else:
        print(
            "[entity-fields] forms oficiais ausentes (tools/.forms/entity_fields.json):\n"
            "                rode tools/fetch_schemas.sh ou tools/vendor_forms.py para\n"
            "                habilitar tambem os avisos de campo/tipo."
        )

    files = sorted(glob.glob(os.path.join(entity_dir, "*.json")))
    if not files:
        print(f"[entity-fields] nenhuma entidade em {entity_dir}")
        return 1

    total_fail = total_warn = 0
    for path in files:
        fails, warns = check_file(path, forms)
        total_fail += len(fails)
        total_warn += len(warns)
        for f in fails:
            print(f"[FAIL] {f}")
        for w in warns:
            print(f"[warn] {w}")

    print(
        f"[entity-fields] {len(files)} entidades | "
        f"{total_fail} falhas | {total_warn} avisos | "
        f"camadas: version-gated + {'forms oficiais' if forms else 'so version-gated'}"
    )
    return 1 if total_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
