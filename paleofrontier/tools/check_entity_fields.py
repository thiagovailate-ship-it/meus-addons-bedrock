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


def walk_component_body(comp, node, path, out):
    """Regras que so aparecem descendo no corpo do componente.

    Tres classes que o checker original nao cobria e que o segundo log real do
    cliente provou serem fatais:

      * membros dentro dos itens de `entity_types` (o cliente abortou a entidade
        por `entity_types[1].must_see_forget_duration`);
      * nomes de membros de objetos aninhados (`avoid_mob_type.sound_interval`
        usa {min,max} enquanto `angry.sound_interval` usa {range_min,range_max});
      * campos folha que viraram enum de string (`damage_sensor.deals_damage`,
        que estava como `{"value": false}` e nem chegou a ser reportado porque a
        entidade ja tinha falhado antes).
    """
    if isinstance(node, dict):
        for field, allowed in bn.LEAF_ENUM_FIELDS.items():
            if field in node:
                value = node[field]
                if not (isinstance(value, str) and value in allowed):
                    out.append(
                        f"'{comp}{('.' + path) if path else ''}.{field}' precisa ser uma destas "
                        f"strings {sorted(allowed)} (encontrado {json.dumps(value)}): o campo "
                        f"deixou de ser boolean/objeto em fv 1.21.40"
                    )
        if "entity_types" in node:
            allowed = bn.ENTITY_TYPES_ITEM_FIELDS.get(comp)
            if allowed is not None:
                entries = node["entity_types"]
                items = entries if isinstance(entries, list) else [entries]
                for index, item in enumerate(items):
                    if not isinstance(item, dict):
                        continue
                    for member in item:
                        if member not in allowed:
                            suffix = "" if isinstance(entries, list) else " (objeto)"
                            out.append(
                                f"'{comp}.entity_types[{index}]{suffix}.{member}' nao e um membro "
                                f"valido; o vanilla usa apenas {sorted(allowed)} nesse componente"
                            )
        for key, value in node.items():
            child = f"{path}.{key}" if path else key
            if isinstance(value, dict):
                members = bn.NESTED_OBJECT_FIELD_MEMBERS.get((comp, key))
                if members is not None:
                    extra = set(value) - set(members)
                    if extra:
                        out.append(
                            f"'{comp}.{child}' tem membros {sorted(extra)} que o vanilla nao usa "
                            f"nesse componente; os membros validos aqui sao {sorted(members)}"
                        )
            walk_component_body(comp, value, child, out)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            walk_component_body(comp, item, f"{path}[{index}]", out)


def component_sections(doc):
    entity = doc.get("minecraft:entity") or {}
    comps = entity.get("components")
    if isinstance(comps, dict):
        yield "components", comps
    for group, body in (entity.get("component_groups") or {}).items():
        if isinstance(body, dict):
            yield f"component_groups.{group}", body


def check_doc(doc, rel, forms):
    fails, warns = [], []
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

            # ---- FAIL: campos que o cliente rejeitou explicitamente --------
            # Os forms oficiais ainda listam `alert_same_type`; o cliente 1.26.52
            # responde "this member was found in the input, but is not present in
            # the Schema" e 0 das 128 entidades vanilla o usam.  Log real vence
            # documentacao.
            for field in sorted(bn.CLIENT_REJECTED_ENTITY_FIELDS.get(comp) or ()):
                if field in body:
                    fails.append(
                        f"{rel} {ident} {label}: '{comp}.{field}' foi rejeitado pelo cliente "
                        f"1.26.52 ('not present in the Schema') e nao aparece em nenhuma das "
                        f"128 entidades vanilla; use 'minecraft:angry' com "
                        f"broadcast_anger_on_being_attacked + broadcast_targets (padrao piglin)"
                    )

            # ---- FAIL: campos que migraram para dentro de presets[] --------
            # leashable.soft/hard/max_distance sao achatados ate fv 1.21.80; a
            # partir dali vivem em `presets[]` e o cliente responde
            # "child 'X' not valid here".  As 4 entidades deste pacote estao em
            # fv 1.26.50, entao a regra se aplica.
            relocated = bn.RELOCATED_TO_PRESETS.get(comp)
            if relocated and bn.version_at_least(fv, relocated["since"]):
                flat = sorted(set(body) & set(relocated["fields"]))
                if flat:
                    fails.append(
                        f"{rel} {ident} {label}: '{comp}' tem {flat} no nivel de cima, mas "
                        f"desde fv {relocated['since']} esses campos vivem dentro de "
                        f"'presets[]' (o cliente responde \"child not valid here\"); "
                        f"modelo vanilla na mesma fv: dolphin.json"
                    )

            # ---- FAIL: membros dentro de presets[] ------------------------
            allowed_preset = bn.PRESET_ITEM_FIELDS.get(comp)
            if allowed_preset is not None and "presets" in body:
                presets = body.get("presets")
                if not isinstance(presets, list):
                    fails.append(
                        f"{rel} {ident} {label}: '{comp}.presets' precisa ser uma LISTA de "
                        f"presets (encontrado {type(presets).__name__}); o vanilla usa "
                        f'"presets": [{{...}}]'
                    )
                else:
                    for index, preset in enumerate(presets):
                        if not isinstance(preset, dict):
                            fails.append(
                                f"{rel} {ident} {label}: '{comp}.presets[{index}]' precisa ser "
                                f"um objeto"
                            )
                            continue
                        extra = sorted(set(preset) - set(allowed_preset))
                        if extra:
                            fails.append(
                                f"{rel} {ident} {label}: '{comp}.presets[{index}]' tem membros "
                                f"{extra} fora do vocabulario vanilla {sorted(allowed_preset)}"
                            )

            # ---- FAIL: regras de profundidade (entity_types, objetos, enums)
            deep = []
            walk_component_body(comp, body, "", deep)
            for msg in deep:
                fails.append(f"{rel} {ident} {label}: {msg}")

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
            # So vale desconfiar da lista manual quando o proprio form documenta
            # uma migracao/remocao.  Sem esse filtro o aviso dispara em campos
            # universais (`health.value`, `movement.value`, `follow_range.max`),
            # que a lista gerada apenas representa de outro jeito: 34 avisos de
            # ruido escondendo o unico sinal verdadeiro.  Com o filtro, sobram os
            # 4 componentes que tem nota de migracao E campos so-manuais
            # (ageable, breedable, leashable, tameable).
            stale_suspect = bool(spec.get("note"))
            for field, value in body.items():
                info = declared.get(field)
                if info is None:
                    warns.append(f"{rel} {ident} {label}: '{comp}.{field}' nao consta no form oficial")
                    continue
                if stale_suspect and info.get("source") == "manual":
                    warns.append(
                        f"{rel} {ident} {label}: '{comp}.{field}' consta SO na lista manual do "
                        f"form (ausente da lista gerada do schema atual) e o form documenta "
                        f"migracao/remocao: {spec['note'][:180]}"
                    )
                ok, why = kind_ok(info.get("type"), value)
                if not ok:
                    warns.append(f"{rel} {ident} {label}: '{comp}.{field}' {why}")
    return fails, warns


def check_file(path, forms):
    doc = json.load(open(path, encoding="utf-8"))
    return check_doc(doc, os.path.relpath(path, ROOT), forms)


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
