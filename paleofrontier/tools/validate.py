#!/usr/bin/env python3
"""PALEOFRONTIER static validation.

Runs three layers of checks and prints a report:

 1. official Mojang JSON-schema validation (via node + ajv, needs tools/.schemas)
 2. structural checks (JSON parses, no empty files, manifests sane)
 3. cross-reference integrity: every id/path/texture/sound/animation/lang key
    referenced anywhere in the pack must actually exist.

Exit code 0 means every layer passed (schema layer may be skipped when the
official schemas are not vendored; that is reported explicitly).

Usage: python3 tools/validate.py [--schemas DIR]
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BP = os.path.join(ROOT, "behavior_pack")
RP = os.path.join(ROOT, "resource_pack")

FAILURES = []
WARNINGS = []
CHECKS = 0


def ok():
    global CHECKS
    CHECKS += 1


def fail(msg):
    FAILURES.append(msg)


def warn(msg):
    WARNINGS.append(msg)


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def walk(root, exts=None):
    for dirpath, _dirs, files in os.walk(root):
        for name in sorted(files):
            if exts is None or any(name.endswith(e) for e in exts):
                yield os.path.join(dirpath, name)


def rel(path):
    return os.path.relpath(path, ROOT)


# ---------------------------------------------------------------------------
# layer 1: official schemas
# ---------------------------------------------------------------------------
def run_schemas(schemas_dir):
    if not schemas_dir or not os.path.isdir(schemas_dir):
        warn("official Mojang schemas not present -> schema layer skipped "
             "(run tools/fetch_schemas.sh to enable it)")
        return
    node = os.path.join(HERE, "node_modules")
    if not os.path.isdir(node):
        subprocess.run(["npm", "install", "--silent", "--no-audit", "--no-fund"],
                       cwd=HERE, check=False)
    proc = subprocess.run(
        ["node", os.path.join(HERE, "schema_check.mjs"), schemas_dir, ROOT],
        capture_output=True, text=True)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    if proc.returncode != 0:
        fail("official schema validation reported failures")
    else:
        ok()


# ---------------------------------------------------------------------------
# layer 2: structural
# ---------------------------------------------------------------------------
def check_structure():
    for path in list(walk(BP)) + list(walk(RP)):
        if os.path.getsize(path) == 0:
            fail(f"empty file: {rel(path)}")
        ok()
    for path in list(walk(BP, [".json"])) + list(walk(RP, [".json"])):
        try:
            load(path)
        except Exception as err:  # noqa: BLE001
            fail(f"invalid JSON {rel(path)}: {err}")
        ok()


def check_manifests():
    bp = load(os.path.join(BP, "manifest.json"))
    rp = load(os.path.join(RP, "manifest.json"))
    uuids = []
    for manifest, tag in ((bp, "BP"), (rp, "RP")):
        uuids.append(manifest["header"]["uuid"])
        for module in manifest["modules"]:
            uuids.append(module["uuid"])
    if len(uuids) != len(set(uuids)):
        fail("duplicate UUIDs across manifests")
    ok()
    rp_uuid = rp["header"]["uuid"]
    deps = [d for d in bp.get("dependencies", []) if "uuid" in d]
    if not any(d["uuid"] == rp_uuid for d in deps):
        fail("BP manifest does not depend on the RP header uuid")
    ok()
    mods = {m["module_name"]: m["version"] for m in bp.get("dependencies", []) if "module_name" in m}
    if mods.get("@minecraft/server") != "2.10.0":
        fail("BP must depend on @minecraft/server 2.10.0 (stable for 1.26.52)")
    if mods.get("@minecraft/server-ui") != "2.2.0":
        fail("BP must depend on @minecraft/server-ui 2.2.0 (stable for 1.26.52)")
    ok()
    script_modules = [m for m in bp["modules"] if m["type"] == "script"]
    if len(script_modules) != 1:
        fail("expected exactly one script module")
    else:
        entry = os.path.join(BP, script_modules[0]["entry"])
        if not os.path.isfile(entry):
            fail(f"script entry missing: {script_modules[0]['entry']}")
    ok()


# ---------------------------------------------------------------------------
# layer 3: cross references
# ---------------------------------------------------------------------------
def collect_ids():
    blocks, items, entities = {}, {}, {}
    for path in walk(os.path.join(BP, "blocks"), [".json"]):
        doc = load(path)
        ident = doc["minecraft:block"]["description"]["identifier"]
        blocks[ident] = doc
    for path in walk(os.path.join(BP, "items"), [".json"]):
        doc = load(path)
        ident = doc["minecraft:item"]["description"]["identifier"]
        items[ident] = doc
    for path in walk(os.path.join(BP, "entities"), [".json"]):
        doc = load(path)
        ident = doc["minecraft:entity"]["description"]["identifier"]
        entities[ident] = doc
    return blocks, items, entities


def check_blocks(blocks):
    terrain = load(os.path.join(RP, "textures", "terrain_texture.json"))["texture_data"]
    for ident, doc in blocks.items():
        comps = doc["minecraft:block"].get("components", {})
        geo = comps.get("minecraft:geometry")
        if isinstance(geo, str) and not geo.startswith("minecraft:geometry."):
            if not geometry_exists(geo):
                fail(f"{ident}: geometry {geo} not found in RP models")
        ok()
        mats = comps.get("minecraft:material_instances", {})
        for _face, mat in mats.items():
            tex = mat.get("texture")
            if tex and tex not in terrain:
                fail(f"{ident}: texture '{tex}' missing from terrain_texture.json")
            elif tex:
                path = terrain[tex]["textures"]
                if isinstance(path, list):
                    path = path[0]
                if not path.endswith(".png"):
                    path += ".png"
                if not os.path.isfile(os.path.join(RP, path)):
                    fail(f"{ident}: texture file missing: {path}")
        ok()
        loot = comps.get("minecraft:loot")
        if loot and not os.path.isfile(os.path.join(BP, loot)):
            fail(f"{ident}: loot table missing: {loot}")
        ok()
        for perm in doc["minecraft:block"].get("permutations", []):
            for _k, pmat in perm.get("components", {}).get("minecraft:material_instances", {}).items():
                tex = pmat.get("texture")
                if tex and tex not in terrain:
                    fail(f"{ident}: permutation texture '{tex}' missing from terrain_texture.json")
        ok()


def geometry_exists(geo_id):
    for path in walk(os.path.join(RP, "models"), [".json"]):
        doc = load(path)
        for entry in doc.get("minecraft:geometry", []):
            if entry["description"]["identifier"] == geo_id:
                return True
    return False


def check_items(items):
    atlas = load(os.path.join(RP, "textures", "item_texture.json"))["texture_data"]
    for ident, doc in items.items():
        icon = doc["minecraft:item"]["components"].get("minecraft:icon", {})
        for name in icon.get("textures", {}).values():
            if name not in atlas:
                fail(f"{ident}: icon '{name}' missing from item_texture.json")
            else:
                path = atlas[name]["textures"]
                if isinstance(path, list):
                    path = path[0]
                if not path.endswith(".png"):
                    path += ".png"
                if not os.path.isfile(os.path.join(RP, path)):
                    fail(f"{ident}: icon file missing: {path}")
        ok()


def check_loot(blocks, items):
    for path in walk(os.path.join(BP, "loot_tables"), [".json"]):
        doc = load(path)
        for pool in doc.get("pools", []):
            for entry in pool.get("entries", []):
                if entry.get("type") != "item":
                    continue
                name = entry.get("name", "")
                if name.startswith("paleo:") and name not in items and name not in blocks:
                    fail(f"{rel(path)}: unknown paleo item in loot: {name}")
                ok()


def check_recipes(items, blocks):
    for path in walk(os.path.join(BP, "recipes"), [".json"]):
        doc = load(path)
        if "format_version" not in doc:
            fail(f"{rel(path)}: missing format_version")
        ok()
        body = doc.get("minecraft:recipe_shaped") or doc.get("minecraft:recipe_shapeless")
        if not body:
            fail(f"{rel(path)}: unsupported recipe type")
            continue
        if "minecraft:recipe_shaped" in doc:
            pattern = body.get("pattern", [])
            if len(pattern) != 3 or any(len(row) != 3 for row in pattern):
                fail(f"{rel(path)}: shaped pattern must be 3x3")
            ok()
            keymap = body.get("key", {})
            used = {ch for row in pattern for ch in row if ch != " "}
            if used - set(keymap):
                fail(f"{rel(path)}: pattern uses undefined keys {sorted(used - set(keymap))}")
            if set(keymap) - used:
                fail(f"{rel(path)}: unused recipe keys {sorted(set(keymap) - used)}")
            ok()
        ids = [body["result"]["item"]]
        for key in body.get("key", {}).values():
            ids.append(key["item"])
        for ident in ids:
            if ident.startswith("paleo:") and ident not in items and ident not in blocks:
                fail(f"{rel(path)}: unknown paleo id in recipe: {ident}")
        ok()


def check_features():
    features = {}
    for path in walk(os.path.join(BP, "features"), [".json"]):
        doc = load(path)
        for kind, body in doc.items():
            if kind.startswith("minecraft:") and isinstance(body, dict) and "description" in body:
                ident = body["description"]["identifier"]
                features[ident] = path
                if ident.split(":")[-1] != os.path.basename(path)[:-5]:
                    fail(f"{rel(path)}: feature identifier {ident} must match file name")
                ok()
    for path in walk(os.path.join(BP, "feature_rules"), [".json"]):
        doc = load(path)
        body = doc["minecraft:feature_rules"]
        ident = body["description"]["identifier"]
        if ident.split(":")[-1] != os.path.basename(path)[:-5]:
            fail(f"{rel(path)}: rule identifier {ident} must match file name")
        places = body["description"]["places_feature"]
        if places not in features:
            fail(f"{rel(path)}: places unknown feature {places}")
        ok()


def check_spawn_rules(entities):
    for path in walk(os.path.join(BP, "spawn_rules"), [".json"]):
        doc = load(path)
        ident = doc["minecraft:spawn_rules"]["description"]["identifier"]
        if ident not in entities:
            fail(f"{rel(path)}: spawn rule for unknown entity {ident}")
        ok()


def check_entities(entities):
    for ident, doc in entities.items():
        body = doc["minecraft:entity"]
        groups = set(body.get("component_groups", {}).keys())
        events = set(body.get("events", {}).keys())

        def scan_triggers(node):
            if isinstance(node, dict):
                for key, value in node.items():
                    if key in ("event",) and isinstance(value, str):
                        if value not in events and not value.startswith("minecraft:entity_"):
                            fail(f"{ident}: event {value} referenced but never defined")
                        ok()
                    scan_triggers(value)
            elif isinstance(node, list):
                for value in node:
                    scan_triggers(value)

        scan_triggers(body.get("component_groups", {}))
        scan_triggers(body.get("components", {}))
        for name, ev in body.get("events", {}).items():
            for section in ("add", "remove"):
                for group in ev.get(section, {}).get("component_groups", []):
                    if group not in groups:
                        fail(f"{ident}: event {name} references missing group {group}")
                    ok()
            scan_triggers(ev)
        loot = body.get("components", {}).get("minecraft:loot", {}).get("table")
        if loot and not os.path.isfile(os.path.join(BP, loot)):
            fail(f"{ident}: loot table missing {loot}")
        ok()


def check_client(entities):
    for ident in entities:
        name = ident.split(":")[-1]
        client_path = os.path.join(RP, "entity", f"paleo_{name}.entity.json")
        if not os.path.isfile(client_path):
            fail(f"missing client entity for {ident}")
            continue
        client = load(client_path)["minecraft:client_entity"]["description"]
        anim_path = os.path.join(RP, "animations", f"paleo_{name}.animation.json")
        ctrl_path = os.path.join(RP, "animation_controllers", f"paleo_{name}.animation_controllers.json")
        rc_path = os.path.join(RP, "render_controllers", f"paleo_{name}.render_controllers.json")
        geo_path = os.path.join(RP, "models", "entity", f"paleo_{name}.geo.json")
        for p in (anim_path, ctrl_path, rc_path, geo_path):
            if not os.path.isfile(p):
                fail(f"{ident}: missing {rel(p)}")
        ok()
        anims = set(load(anim_path)["animations"].keys()) if os.path.isfile(anim_path) else set()
        ctrls = set(load(ctrl_path)["animation_controllers"].keys()) if os.path.isfile(ctrl_path) else set()
        rcs = set(load(rc_path)["render_controllers"].keys()) if os.path.isfile(rc_path) else set()
        geos = set()
        if os.path.isfile(geo_path):
            for entry in load(geo_path)["minecraft:geometry"]:
                geos.add(entry["description"]["identifier"])
        for short, target in client.get("animations", {}).items():
            if target not in anims:
                fail(f"{ident}: client animation {target} not defined")
            ok()
        for entry in client.get("animation_controllers", []):
            for target in entry.values():
                if target not in ctrls:
                    fail(f"{ident}: controller {target} not defined")
                ok()
        for target in client.get("render_controllers", []):
            if target not in rcs:
                fail(f"{ident}: render controller {target} not defined")
            ok()
        for target in client.get("geometry", {}).values():
            if target not in geos:
                fail(f"{ident}: geometry {target} not defined")
            ok()
        for key, path in client.get("textures", {}).items():
            full = path + (".png" if not path.endswith(".png") else "")
            if not os.path.isfile(os.path.join(RP, full)):
                fail(f"{ident}: texture missing {full}")
            ok()
        egg = client.get("spawn_egg", {}).get("texture")
        if egg:
            atlas = load(os.path.join(RP, "textures", "item_texture.json"))["texture_data"]
            if egg not in atlas:
                fail(f"{ident}: spawn egg texture {egg} missing from item_texture.json")
            ok()
        # render controller arrays must map onto declared textures/geometry
        if os.path.isfile(rc_path):
            rc = list(load(rc_path)["render_controllers"].values())[0]
            arrays = rc.get("arrays", {})
            tex_names = set(client.get("textures", {}).keys())
            for ref in arrays.get("textures", {}).get("Array.skins", []):
                short = ref.split(".")[-1]
                if short not in tex_names:
                    fail(f"{ident}: render controller texture {ref} not declared in client entity")
                ok()
            geo_names = set(client.get("geometry", {}).keys())
            for ref in arrays.get("geometries", {}).get("Array.models", []):
                short = ref.split(".")[-1]
                if short not in geo_names:
                    fail(f"{ident}: render controller geometry {ref} not declared in client entity")
                ok()


def check_sounds():
    sounds = load(os.path.join(RP, "sounds.json"))
    defs = load(os.path.join(RP, "sounds", "sound_definitions.json"))["sound_definitions"]
    defined = set(defs.keys())
    for entity, spec in sounds.get("entity_sounds", {}).get("entities", {}).items():
        for event_name, sound_id in spec.get("events", {}).items():
            if isinstance(sound_id, dict):
                sound_id = sound_id.get("sound")
            if sound_id not in defined:
                fail(f"sounds.json: {entity} event {event_name} -> undefined sound {sound_id}")
            ok()
    for group, spec in sounds.get("block_sounds", {}).items():
        for event_name, val in spec.get("events", {}).items():
            sound_id = val.get("sound") if isinstance(val, dict) else val
            if sound_id and sound_id not in defined and not sound_id.startswith("block."):
                fail(f"sounds.json: {group} event {event_name} -> undefined sound {sound_id}")
            ok()
    for sound_id, spec in defs.items():
        for entry in spec.get("sounds", []):
            name = entry["name"]
            path = name + (".ogg" if not name.endswith(".ogg") else "")
            if not os.path.isfile(os.path.join(RP, path)):
                fail(f"sound_definitions: missing audio file {path}")
            ok()


def check_languages_file():
    for root in (RP, BP):
        path = os.path.join(root, "texts", "languages.json")
        doc = load(path)
        if not isinstance(doc, list) or not all(isinstance(x, str) for x in doc):
            fail(f"{rel(path)}: languages.json must be an array of locale codes")
        elif "en_US" not in doc or "pt_BR" not in doc:
            fail(f"{rel(path)}: languages.json must list en_US and pt_BR")
        ok()


def check_lang():
    en = {}
    pt = {}
    for path, bag in ((os.path.join(RP, "texts", "en_US.lang"), en),
                      (os.path.join(RP, "texts", "pt_BR.lang"), pt)):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _value = line.split("=", 1)
                bag[key] = True
    if set(en.keys()) != set(pt.keys()):
        missing_en = set(pt) - set(en)
        missing_pt = set(en) - set(pt)
        fail(f"lang mismatch: only-pt={sorted(missing_en)[:5]} only-en={sorted(missing_pt)[:5]}")
    ok()
    used = set()
    for path in walk(os.path.join(BP, "scripts"), [".js"]):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        for match in re.finditer(r'translate:\s*"([^"]+)"', text):
            used.add(match.group(1))
        for match in re.finditer(r'`translate:\s*"([^"$]+)"', text):
            used.add(match.group(1))
    # dynamic keys built from templates are checked against the content model
    sys.path.insert(0, HERE)
    import content_model as cm  # noqa: PLC0415
    for sp in cm.SPECIES:
        used.add(f"entity.{cm.NAMESPACE}:{sp['entity']}.name")
        used.add(f"item.spawn_egg.entity.{cm.NAMESPACE}:{sp['entity']}.name")
    for it in cm.ALL_ITEMS:
        used.add(f"item.{cm.NAMESPACE}:{it['id']}")
        used.add(f"item.{cm.NAMESPACE}:{it['id']}.name")
    for b in cm.ALL_BLOCKS:
        used.add(f"tile.{cm.NAMESPACE}:{b['id']}.name")
    for pr in cm.LAB_PROCESSES:
        used.add(f"paleo.proc.{pr['id']}")
    for sp in cm.SPECIES:
        used.add(f"paleo.rarity.{sp['rarity_en']}")
    missing = sorted(key for key in used
                     if "$" not in key and "{" not in key and key not in en)
    if missing:
        fail(f"lang keys used but not translated: {missing}")
    ok()


def check_scripts():
    scripts_root = os.path.join(BP, "scripts")
    entry = os.path.join(scripts_root, "main.js")
    if not os.path.isfile(entry):
        fail("scripts/main.js missing")
        return
    files = list(walk(scripts_root, [".js"]))
    # syntax
    for path in files:
        proc = subprocess.run(["node", "--check", path], capture_output=True, text=True)
        if proc.returncode != 0:
            fail(f"JS syntax error {rel(path)}: {proc.stderr.strip().splitlines()[-1] if proc.stderr else ''}")
        ok()
    # imports resolve + reachability from main.js
    import_re = re.compile(r'from\s+"(\./[^"]+|\.\./[^"]+)"')
    graph = {}
    for path in files:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        deps = []
        for match in import_re.finditer(text):
            target = os.path.normpath(os.path.join(os.path.dirname(path), match.group(1)))
            if not target.endswith(".js"):
                target += ".js"
            if not os.path.isfile(target):
                fail(f"{rel(path)}: unresolved import {match.group(1)}")
            deps.append(target)
            ok()
        graph[path] = deps
    seen = set()
    stack = [entry]
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        stack.extend(graph.get(current, []))
    orphans = [p for p in files if p not in seen]
    if orphans:
        fail(f"script modules not reachable from main.js: {[rel(p) for p in orphans]}")
    ok()


def main():
    schemas_dir = os.path.join(HERE, ".schemas", "schemas")
    if "--schemas" in sys.argv:
        schemas_dir = sys.argv[sys.argv.index("--schemas") + 1]
    run_schemas(schemas_dir)
    check_structure()
    check_manifests()
    blocks, items, entities = collect_ids()
    check_blocks(blocks)
    check_items(items)
    check_loot(blocks, items)
    check_recipes(items, blocks)
    check_features()
    check_spawn_rules(entities)
    check_entities(entities)
    check_client(entities)
    check_sounds()
    check_languages_file()
    check_lang()
    check_scripts()

    print()
    print(f"[validate] {CHECKS} checks executed")
    for w in WARNINGS:
        print(f"  WARN  {w}")
    if FAILURES:
        print(f"  {len(FAILURES)} FAILURE(S):")
        for f in FAILURES:
            print(f"  FAIL  {f}")
        sys.exit(1)
    print("  all cross-reference and structural checks passed")


if __name__ == "__main__":
    main()
