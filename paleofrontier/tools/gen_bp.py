#!/usr/bin/env python3
"""Generates every data-driven Behavior Pack file for PALEOFRONTIER.

Run from anywhere:  python3 tools/gen_bp.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_model as cm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BP = os.path.join(ROOT, "behavior_pack")


def write(rel, data):
    path = os.path.join(BP, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return path


# ---------------------------------------------------------------------------
# Blocks
# ---------------------------------------------------------------------------
def menu_category(category, group=None):
    """Creative-inventory placement.

    Since format version 1.26.20 the game validates this strictly: `category`
    is required and `group`, when present, must be a namespaced string
    ("minecraft:itemGroup.name.ore").  An unprefixed group makes the whole
    block definition fail to load, so normalise defensively here.
    """
    out = {"category": category}
    if group:
        out["group"] = group if ":" in group else f"minecraft:{group}"
    return out


def deposit_block(b):
    return {
        "format_version": cm.FORMAT_BLOCK,
        "minecraft:block": {
            "description": {
                "identifier": cm.item_id(b["id"]),
                "menu_category": menu_category(b["category"], b.get("group")),
            },
            "components": {
                "minecraft:collision_box": True,
                "minecraft:selection_box": True,
                "minecraft:destructible_by_mining": {"seconds_to_destroy": b["seconds_to_destroy"]},
                "minecraft:destructible_by_explosion": {"explosion_resistance": b["explosion_resistance"]},
                "minecraft:geometry": "minecraft:geometry.full_block",
                "minecraft:material_instances": {
                    "*": {"texture": b["texture"], "render_method": "opaque"}
                },
                "minecraft:map_color": {"color": b["map_color"]},
                "minecraft:light_dampening": 15,
                "minecraft:friction": 0.6,
                "minecraft:breathability": "solid",
                "minecraft:sound": {"sound": cm.BLOCK_SOUND_ASSIGNMENT[b["id"]]},
                "minecraft:tags": cm.BLOCK_ITEM_TAGS[b["id"]],
                "minecraft:loot": b["loot"],
            },
        },
    }


def research_bench_block(b):
    components = {
        "minecraft:collision_box": True,
        "minecraft:selection_box": True,
        "minecraft:destructible_by_mining": {"seconds_to_destroy": b["seconds_to_destroy"]},
        "minecraft:destructible_by_explosion": {"explosion_resistance": b["explosion_resistance"]},
        "minecraft:geometry": b["geometry"],
        # Built-in face-named instances: the work surface on top and the
        # instrument panel on the face that rotates towards the player.
        "minecraft:material_instances": {
            "*": {"texture": f"{b['texture_prefix']}_side", "render_method": "opaque"},
            "up": {"texture": f"{b['texture_prefix']}_top", "render_method": "opaque"},
            "south": {"texture": f"{b['texture_prefix']}_front", "render_method": "opaque"},
        },
        "minecraft:map_color": {"color": b["map_color"]},
        "minecraft:light_dampening": 0,
        "minecraft:light_emission": b["light"],
        "minecraft:friction": 0.6,
        "minecraft:sound": {"sound": cm.BLOCK_SOUND_ASSIGNMENT[b["id"]]},
        "minecraft:tags": cm.BLOCK_ITEM_TAGS[b["id"]],
        "minecraft:loot": b["loot"],
    }
    permutations = []
    for facing, rot in (("north", [0, 180, 0]), ("south", [0, 0, 0]),
                        ("east", [0, 90, 0]), ("west", [0, 270, 0])):
        permutations.append({
            "condition": f"q.block_state('minecraft:cardinal_direction') == '{facing}'",
            "components": {"minecraft:transformation": {"rotation": rot}},
        })
    return {
        "format_version": cm.FORMAT_BLOCK,
        "minecraft:block": {
            "description": {
                "identifier": cm.item_id(b["id"]),
                "menu_category": menu_category(b["category"], b.get("group")),
                "traits": {
                    "minecraft:placement_direction": {
                        "enabled_states": ["minecraft:cardinal_direction"]
                    }
                },
            },
            "components": components,
            "permutations": permutations,
        },
    }


def incubator_block(b):
    stage_state = f"{cm.NAMESPACE}:stage"
    components = {
        "minecraft:collision_box": True,
        "minecraft:selection_box": True,
        "minecraft:destructible_by_mining": {"seconds_to_destroy": b["seconds_to_destroy"]},
        "minecraft:destructible_by_explosion": {"explosion_resistance": b["explosion_resistance"]},
        "minecraft:geometry": b["geometry"],
        # The four sides are the glass chamber, whose texture is swapped per
        # incubation stage by the permutations below.
        "minecraft:material_instances": {
            "*": {"texture": f"{b['texture_prefix']}_chamber_0", "render_method": "opaque"},
            "up": {"texture": f"{b['texture_prefix']}_top", "render_method": "opaque"},
            "down": {"texture": f"{b['texture_prefix']}_side", "render_method": "opaque"},
        },
        "minecraft:map_color": {"color": b["map_color"]},
        "minecraft:light_dampening": 0,
        "minecraft:light_emission": 3,
        "minecraft:friction": 0.6,
        "minecraft:sound": {"sound": cm.BLOCK_SOUND_ASSIGNMENT[b["id"]]},
        "minecraft:tags": cm.BLOCK_ITEM_TAGS[b["id"]],
        "minecraft:loot": b["loot"],
    }
    permutations = []
    light_by_stage = {0: 3, 1: 5, 2: 8, 3: 11, 4: 15}
    for stage in b["states"]["stage"]:
        permutations.append({
            "condition": f"q.block_state('{stage_state}') == {stage}",
            "components": {
                "minecraft:light_emission": light_by_stage[stage],
                "minecraft:material_instances": {
                    "*": {
                        "texture": f"{b['texture_prefix']}_chamber_{stage}",
                        "render_method": "opaque",
                    },
                    "up": {"texture": f"{b['texture_prefix']}_top", "render_method": "opaque"},
                    "down": {"texture": f"{b['texture_prefix']}_side", "render_method": "opaque"},
                },
            },
        })
    return {
        "format_version": cm.FORMAT_BLOCK,
        "minecraft:block": {
            "description": {
                "identifier": cm.item_id(b["id"]),
                "menu_category": menu_category(b["category"], b.get("group")),
                "states": {stage_state: b["states"]["stage"]},
            },
            "components": components,
            "permutations": permutations,
        },
    }


def gen_blocks():
    written = []
    for b in cm.DEPOSIT_BLOCKS:
        written.append(write(f"blocks/{b['id']}.block.json", deposit_block(b)))
    for b in cm.STATION_BLOCKS:
        data = research_bench_block(b) if b["id"] == "research_bench" else incubator_block(b)
        written.append(write(f"blocks/{b['id']}.block.json", data))
    return written


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------
RARITY_COMPONENT = {
    "common": "common",
    "uncommon": "uncommon",
    "rare": "rare",
    "epic": "epic",
    "legendary": "epic",
}


def item_json(it):
    identifier = cm.item_id(it["id"])
    description = {
        "identifier": identifier,
        "menu_category": menu_category(it["category"], it.get("group")),
    }
    components = {
        "minecraft:icon": {"textures": {"default": f"paleo_{it['id']}"}},
        "minecraft:max_stack_size": it["stack"],
    }
    if it.get("glint"):
        components["minecraft:glint"] = True
    if it.get("tags"):
        components["minecraft:tags"] = {"tags": it["tags"]}
    if it.get("hover"):
        # minecraft:rarity only knows common/uncommon/rare/epic
        components["minecraft:rarity"] = RARITY_COMPONENT.get(it["hover"], "epic")
    if it.get("durability"):
        components["minecraft:durability"] = {
            "max_durability": it["durability"],
            "damage_chance": {"min": 90, "max": 100},
        }
        repair_items = [
            {
                "items": [identifier],
                "repair_amount": "context.other->query.remaining_durability",
            }
        ]
        if it.get("repair"):
            repair_items.insert(0, {
                "items": it["repair"]["items"],
                "repair_amount": it["repair"]["amount"],
            })
        components["minecraft:repairable"] = {"repair_items": repair_items}
    if it.get("enchantable"):
        components["minecraft:enchantable"] = {
            "slot": it["enchantable"]["slot"],
            "value": it["enchantable"]["value"],
        }
    if it.get("damage"):
        components["minecraft:damage"] = it["damage"]
    if it.get("hand_equipped"):
        components["minecraft:hand_equipped"] = {"value": True}
    if it.get("dig_speed"):
        targets = []
        for dep in cm.DEPOSIT_BLOCKS:
            targets.append({"block": cm.item_id(dep["id"]), "speed": it["dig_speed"]})
        # Field tools also work on the natural hosts of a fossil bed.
        for extra in ("minecraft:gravel", "minecraft:sand", "minecraft:dirt",
                      "minecraft:clay", "minecraft:soul_sand"):
            if it["id"] == "excavation_shovel":
                targets.append({"block": extra, "speed": it["dig_speed"]})
        components["minecraft:digger"] = {"destroy_speeds": targets, "use_efficiency": True}
    if it.get("cooldown"):
        components["minecraft:cooldown"] = {
            "category": it["cooldown"]["category"],
            "duration": it["cooldown"]["duration"],
            "type": "use",
        }
    if it["kind"] == "egg":
        # Deliberately NO minecraft:entity_placer and NO use action: a viable egg
        # can only be developed inside an incubator, it cannot be thrown straight
        # into the world. The incubator UI consumes it from the player inventory.
        components["minecraft:fire_resistant"] = {"value": True}
    return {
        "format_version": cm.FORMAT_ITEM,
        "minecraft:item": {"description": description, "components": components},
    }


def gen_items():
    return [write(f"items/{it['id']}.item.json", item_json(it)) for it in cm.ALL_ITEMS]


# ---------------------------------------------------------------------------
# Recipes
# ---------------------------------------------------------------------------
def gen_recipes():
    out = []
    for r in cm.RECIPES:
        out.append(write(f"recipes/{r['id']}.recipe.json", {
            "format_version": cm.FORMAT_RECIPE,
            "minecraft:recipe_shaped": {
                "description": {"identifier": cm.item_id(r["id"])},
                "tags": r["tags"],
                "pattern": r["pattern"],
                "key": {k: {"item": v} for k, v in r["key"].items()},
                "unlock": r["unlock"],
                "result": {"item": r["result"], "count": r["count"]},
            },
        }))
    return out


# ---------------------------------------------------------------------------
# Loot tables
# ---------------------------------------------------------------------------
def gen_loot():
    out = []
    for name, table in cm.LOOT_DEPOSITS.items():
        out.append(write(f"loot_tables/blocks/{name}.json", table))
    for name, table in cm.LOOT_STATIONS.items():
        out.append(write(f"loot_tables/blocks/{name}.json", table))
    for name, table in cm.LOOT_ENTITIES.items():
        out.append(write(f"loot_tables/entities/{name}.json", table))
    return out


# ---------------------------------------------------------------------------
# World generation: features + feature rules
# ---------------------------------------------------------------------------
def gen_features():
    out = []
    for f in cm.FEATURES:
        fid = cm.item_id(f["id"])
        out.append(write(f"features/{f['id']}.json", {
            "format_version": cm.FORMAT_FEATURE,
            "minecraft:ore_feature": {
                "description": {"identifier": fid},
                "count": f["count"],
                "replace_rules": [
                    {"places_block": f["block"], "may_replace": [host]} for host in f["replace"]
                ],
            },
        }))
        biome_filter = {
            "any_of": [
                {"test": "has_biome_tag", "operator": "==", "value": tag}
                for tag in f["biome_tags"]
            ]
        }
        if len(f["biome_tags"]) == 1:
            biome_filter = {"test": "has_biome_tag", "operator": "==", "value": f["biome_tags"][0]}
        out.append(write(f"feature_rules/{f['rule_id']}.json", {
            "format_version": cm.FORMAT_FEATURE_RULES,
            "minecraft:feature_rules": {
                "description": {
                    "identifier": cm.item_id(f["rule_id"]),
                    "places_feature": fid,
                },
                "conditions": {
                    "placement_pass": f["pass_"],
                    "minecraft:biome_filter": biome_filter,
                },
                "distribution": {
                    "iterations": f["iterations"],
                    "coordinate_eval_order": "zyx",
                    "x": {"distribution": "uniform", "extent": [0, 16]},
                    "y": {"distribution": "uniform", "extent": [f["y_min"], f["y_max"]]},
                    "z": {"distribution": "uniform", "extent": [0, 16]},
                },
            },
        }))
    return out


# ---------------------------------------------------------------------------
# Generated script-side content registry (keeps JS and JSON in lockstep)
# ---------------------------------------------------------------------------
NL = chr(10)
COMMA_NL = "," + NL


def gen_script_content():
    global SPECIES_JOINER, PROCESS_JOINER, DEPOSIT_JOINER  # noqa: PLW0603
    species_js = []
    for sp in cm.SPECIES:
        species_js.append(
            "  {\n"
            f'    key: "{sp["key"]}",\n'
            f'    entityId: "{sp["entity_id"]}",\n'
            f'    specimenId: "{sp["specimen_id"]}",\n'
            f'    eggId: "{sp["egg_id"]}",\n'
            f'    namePt: "{cm.pt_br(sp["pt"])}",\n'
            f'    nameEn: "{sp["en"]}",\n'
            f'    sci: "{sp["sci"]}",\n'
            f'    eraPt: "{cm.pt_br(sp["era_pt"])}",\n'
            f'    dietPt: "{cm.pt_br(sp["diet_pt"])}",\n'
            f'    sizePt: "{cm.pt_br(sp["size_pt"])}",\n'
            f'    notePt: "{cm.pt_br(sp["note_pt"])}",\n'
            f'    rarityPt: "{cm.pt_br(sp["rarity"])}",\n'
            f'    rarityEn: "{sp["rarity_en"]}",\n'
            f'    incubationSeconds: {sp["incubation_seconds"]},\n'
            f'    bondable: {str(sp["bondable"]).lower()},\n'
            f'    examineCost: {{ specimen: {sp["examine"]["specimen"]}, chip: {sp["examine"]["chip"]}, '
            f'shard: {sp["examine"]["shard"]}, amber: {sp["examine"]["amber"]} }},\n'
            f'    examineXp: {sp["examine"]["xp"]},\n'
            f'    reconstructCost: {{ matrix: {sp["reconstruct"]["matrix"]}, specimen: {sp["reconstruct"]["specimen"]}, '
            f'gel: {sp["reconstruct"]["gel"]}, amber: {sp["reconstruct"]["amber"]} }},\n'
            f'    reconstructXp: {sp["reconstruct"]["xp"]},\n'
            "  }"
        )
    processes_js = []
    for pr in cm.LAB_PROCESSES:
        inputs = ", ".join(f'["{i}", {n}]' for i, n in pr["inputs"])
        outputs = ", ".join(f'["{o}", {n}]' for o, n in pr["outputs"])
        processes_js.append(
            "  {\n"
            f'    id: "{pr["id"]}",\n'
            f'    namePt: "{pr["pt"]}",\n'
            f'    descPt: "{pr["desc_pt"]}",\n'
            f'    inputs: [{inputs}],\n'
            f'    outputs: [{outputs}],\n'
            f'    xp: {pr["xp"]},\n'
            f'    sound: "{pr["sound"]}",\n'
            f'    requiresAnySpecies: {str(pr.get("requires_any_species", False)).lower()},\n'
            "  }"
        )
    SPECIES_JOINER = COMMA_NL.join(species_js)
    PROCESS_JOINER = COMMA_NL.join(processes_js)
    DEPOSIT_JOINER = COMMA_NL.join(f'  "{t}",' for t in cm.DEPOSIT_TYPE_IDS)
    body = f'''/**
 * PALEOFRONTIER - generated content registry.
 * AUTO-GENERATED by tools/gen_bp.py from tools/content_model.py.
 * Do not edit by hand: change the model and regenerate.
 */

export const NAMESPACE = "{cm.NAMESPACE}";

export const BLOCKS = {{
  fossilDeposit: "{cm.NAMESPACE}:fossil_deposit",
  shaleMatrix: "{cm.NAMESPACE}:shale_matrix",
  boneBed: "{cm.NAMESPACE}:bone_bed",
  researchBench: "{cm.NAMESPACE}:research_bench",
  incubator: "{cm.NAMESPACE}:incubator",
}};

/** Every block the fossil scanner can detect, in increasing value order. */
export const DEPOSIT_BLOCKS = [
{DEPOSIT_JOINER}
];

/** Signal weight per deposit type used by the scanner readout. */
export const DEPOSIT_WEIGHT = {{
  "{cm.NAMESPACE}:fossil_deposit": 1,
  "{cm.NAMESPACE}:shale_matrix": 2,
  "{cm.NAMESPACE}:bone_bed": 4,
}};

export const ITEMS = {{
  fossilChip: "{cm.NAMESPACE}:fossil_chip",
  boneShard: "{cm.NAMESPACE}:bone_shard",
  amberInclusion: "{cm.NAMESPACE}:amber_inclusion",
  nutrientGel: "{cm.NAMESPACE}:nutrient_gel",
  geneticMatrix: "{cm.NAMESPACE}:genetic_matrix",
  excavationShovel: "{cm.NAMESPACE}:excavation_shovel",
  brush: "{cm.NAMESPACE}:brush",
  fossilScanner: "{cm.NAMESPACE}:fossil_scanner",
  fieldCase: "{cm.NAMESPACE}:field_case",
}};

export const SPECIES = [
{SPECIES_JOINER}
];

export const LAB_PROCESSES = [
{PROCESS_JOINER}
];

export const SPECIES_BY_KEY = {{}};
for (const species of SPECIES) {{
  SPECIES_BY_KEY[species.key] = species;
}}

export const SPECIES_BY_SPECIMEN = {{}};
export const SPECIES_BY_EGG = {{}};
export const SPECIES_BY_ENTITY = {{}};
for (const species of SPECIES) {{
  SPECIES_BY_SPECIMEN[species.specimenId] = species;
  SPECIES_BY_EGG[species.eggId] = species;
  SPECIES_BY_ENTITY[species.entityId] = species;
}}

export const ALL_SPECIMEN_IDS = SPECIES.map((s) => s.specimenId);
export const ALL_EGG_IDS = SPECIES.map((s) => s.eggId);
export const ALL_ENTITY_IDS = SPECIES.map((s) => s.entityId);

export const SOUNDS = {{
  discover: "{cm.NAMESPACE}.discover",
  discoverRare: "{cm.NAMESPACE}.discover.rare",
  scanPing: "{cm.NAMESPACE}.scanner.ping",
  scanStrong: "{cm.NAMESPACE}.scanner.strong",
  scanEmpty: "{cm.NAMESPACE}.scanner.empty",
  labProcess: "{cm.NAMESPACE}.lab.process",
  labIdentify: "{cm.NAMESPACE}.lab.identify",
  labDeny: "{cm.NAMESPACE}.lab.deny",
  benchOpen: "{cm.NAMESPACE}.bench.open",
  incubatorStart: "{cm.NAMESPACE}.incubator.start",
  incubatorProgress: "{cm.NAMESPACE}.incubator.progress",
  incubatorHatch: "{cm.NAMESPACE}.incubator.hatch",
  digSediment: "{cm.NAMESPACE}.dig.sediment",
  digBrush: "{cm.NAMESPACE}.dig.brush",
}};

export const PARTICLES = {{
  dust: "{cm.NAMESPACE}:excavation_dust",
  spark: "{cm.NAMESPACE}:research_spark",
  scanPulse: "{cm.NAMESPACE}:scan_pulse",
  incubation: "{cm.NAMESPACE}:incubation_glow",
}};

export const INCUBATOR_STAGE_STATE = "{cm.NAMESPACE}:stage";
'''
    path = os.path.join(BP, "scripts", "data", "content.js")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    return [path]


def main():
    written = []
    written += gen_blocks()
    written += gen_items()
    written += gen_recipes()
    written += gen_loot()
    written += gen_features()
    written += gen_script_content()
    print(f"[gen_bp] wrote {len(written)} files")
    for path in written:
        print("   ", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
