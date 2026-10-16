#!/usr/bin/env python3
"""Extrai o vocabulario oficial de componentes de entidade para tools/.forms.

Fonte: MicrosoftDocs/minecraft-creator -> content/forms/entity/*.form.json
(cada form lista os campos declarados de um componente e o tipo de cada um).

Uso:
    python3 tools/vendor_forms.py [caminho-do-checkout-de-minecraft-creator]

Sem argumento, procura um checkout em /tmp/refs/minecraft-creator.  O resultado
e gravado em tools/.forms/entity_fields.json (gitignored) e consumido por
tools/check_entity_fields.py.
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, ".forms", "entity_fields.json")
DEFAULT_SRC = "/tmp/refs/minecraft-creator"
SUFFIX = ".form.json"
NOTE_RE = re.compile(r"(?i)remov|renam|replac|deprecat|no longer|split")


def ident_from_filename(path):
    base = os.path.basename(path)[: -len(SUFFIX)]
    if not base.startswith("minecraft_"):
        return None
    if base.startswith("minecraft_memory_behavior_"):
        return None
    if base.startswith("minecraft_behavior_"):
        return "minecraft:behavior." + base[len("minecraft_behavior_"):]
    return "minecraft:" + base[len("minecraft_"):]


def extract(forms_dir):
    out = {}
    skipped = []
    for path in sorted(glob.glob(os.path.join(forms_dir, "*" + SUFFIX))):
        try:
            doc = json.load(open(path, encoding="utf-8"))
        except Exception as err:  # noqa: BLE001
            skipped.append((path, str(err)))
            continue
        gen = (
            doc.get("generatedFromSchema_doNotEdit")
            or doc.get("generated_doNotEdit")
            or {}
        )
        ident = doc.get("id") or gen.get("id") or ident_from_filename(path)
        if not ident or not str(ident).startswith("minecraft:"):
            skipped.append((path, "sem id"))
            continue
        # Um form pode trazer a lista de campos em ATE tres lugares: escrita a
        # mao no topo, `generatedFromSchema_doNotEdit` e `generated_doNotEdit`.
        # Nenhuma delas e completa sozinha:
        #   minecraft_leashable   -> soft/hard/max_distance so na lista do topo
        #   minecraft:behavior.hurt_by_target -> alert_same_type so em
        #                            generated_doNotEdit
        # Fundir as tres evita falso positivo de "campo nao existe".
        legacy = doc.get("generated_doNotEdit") or {}
        fields = {}
        # PROVENIENCIA importa.  As listas `generated*_doNotEdit` sao geradas a
        # partir do schema atual; a lista `fields` do topo e escrita a mao e
        # ENVELHECE.  Fundir tudo sem distinguir - que era o que este script
        # fazia - produz falso NEGATIVO: `minecraft:leashable` lista
        # soft/hard/max_distance no topo, campos que o form gerado ja nao tem
        # (migraram para `presets[]` em fv 1.21.80) e que o cliente 1.26.52
        # rejeita com "child not valid here".
        # Por isso cada campo guarda de onde veio, e o checker trata campo
        # "so manual" como aviso, nunca como aceite silencioso.
        grouped = [
            ("manual", doc.get("fields") or []),
            ("generated", (gen.get("fields") or []) + (legacy.get("fields") or [])),
        ]
        for source, src_fields in grouped:
            for field in src_fields:
                name = field.get("id")
                if not name:
                    continue
                entry = fields.get(name) or {}
                seen = entry.get("source")
                entry["source"] = "both" if seen and seen != source else source
                if field.get("dataType"):
                    entry.setdefault("type", field["dataType"])
                if field.get("choices"):
                    entry["choices"] = [c.get("id") for c in field["choices"]]
                if field.get("isRequired"):
                    entry["required"] = True
                fields[name] = entry
        record = {"fields": fields}
        # `note` E `note2`: foi o note2 do minecraft_leashable que documentou a
        # migracao ("From 1.21.80 onward, supports multiple presets via the
        # `presets` array ... replacing the flat root fields previously used").
        notes = [n for n in (doc.get("note"), doc.get("note2"),
                             gen.get("note"), gen.get("note2")) if n]
        for note in notes:
            if NOTE_RE.search(note):
                record.setdefault("note", "")
                record["note"] = (record["note"] + " | " + note)[:600].strip(" |")
        out[ident] = record
    return out, skipped


def main(argv):
    src = argv[1] if len(argv) > 1 else DEFAULT_SRC
    forms_dir = os.path.join(src, "content", "forms", "entity")
    if not os.path.isdir(forms_dir):
        print(f"[vendor_forms] nao achei {forms_dir}", file=sys.stderr)
        print(
            "               clone MicrosoftDocs/minecraft-creator e passe o caminho",
            file=sys.stderr,
        )
        return 1
    out, skipped = extract(forms_dir)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print(f"[vendor_forms] {len(out)} componentes -> {OUT} ({len(skipped)} forms pulados)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
