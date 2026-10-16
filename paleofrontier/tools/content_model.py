"""PALEOFRONTIER - single source of truth for all addon content identifiers.

Everything that has to stay in sync between the Behavior Pack, the Resource Pack
and the runtime scripts (identifiers, textures, loot, recipes, progression costs,
sound definitions, translations) is described here exactly once. The generators in
this folder emit the JSON/LANG/JS artifacts from this table, and ``validate.py``
re-reads the emitted files to prove that nothing drifted.
"""

import re

NAMESPACE = "paleo"
PACK_NAME = "PALEOFRONTIER: Arquivo dos Gigantes"
TARGET_GAME_VERSION = "1.26.52"
MIN_ENGINE_VERSION = [1, 26, 50]

BP_UUID = "9a1f3d1d-ef22-4052-8e72-01afee4a75de"
BP_DATA_UUID = "19cefacf-0cf9-4ad0-a3ba-c3f1546edc7c"
BP_SCRIPT_UUID = "41f22d2e-2c99-4bad-8689-aa921e6c7fa3"
RP_UUID = "714d82a3-b073-4c75-9da3-3de9463ad77c"
RP_MODULE_UUID = "61da0acf-e8cd-4640-a2b9-e97a703389f5"

FORMAT_BLOCK = "1.26.50"
FORMAT_ITEM = "1.26.50"
FORMAT_ENTITY = "1.26.50"
FORMAT_FEATURE = "1.13.0"
FORMAT_FEATURE_RULES = "1.13.0"
FORMAT_SPAWN_RULES = "1.8.0"
FORMAT_RECIPE = "1.20.10"
FORMAT_CLIENT_ENTITY = "1.10.0"
FORMAT_GEOMETRY = "1.16.0"
FORMAT_ANIMATION = "1.8.0"
FORMAT_ANIMATION_CONTROLLER = "1.10.0"
FORMAT_RENDER_CONTROLLER = "1.8.0"
FORMAT_SOUND_DEFINITIONS = "1.26.50"

# --------------------------------------------------------------------------
# Materials / progression items
# --------------------------------------------------------------------------
# kind: material | specimen | egg | tool
ITEMS = [
    dict(
        id="fossil_chip",
        kind="material",
        pt="Fragmento de Sedimento",
        en="Sediment Fragment",
        lore_pt="Matriz rochosa retirada de um deposito fossilifero. Insumo basico de laboratorio.",
        lore_en="Rocky matrix chipped out of a fossil deposit. Basic laboratory feedstock.",
        stack=64,
        category="items",
        rarity="common",
    ),
    dict(
        id="bone_shard",
        kind="material",
        pt="Lasca Ossea",
        en="Bone Shard",
        lore_pt="Fragmento de osso mineralizado. Fonte de calcio para reconstrucao biologica.",
        lore_en="Mineralised bone splinter. Calcium source for biological reconstruction.",
        stack=64,
        category="items",
        rarity="common",
    ),
    dict(
        id="amber_inclusion",
        kind="material",
        pt="Inclusao em Ambar",
        en="Amber Inclusion",
        lore_pt="Resina fossil com tecido preservado. Catalisador raro de extracao genetica.",
        lore_en="Fossil resin with preserved tissue. Rare genetic extraction catalyst.",
        stack=16,
        category="items",
        rarity="rare",
        glint=True,
    ),
    dict(
        id="nutrient_gel",
        kind="material",
        pt="Gel Nutritivo",
        en="Nutrient Gel",
        lore_pt="Meio de cultura sintetizado na estacao de pesquisa. Alimenta uma incubadora.",
        lore_en="Culture medium synthesised at the research station. Feeds an incubator.",
        stack=16,
        category="items",
        rarity="uncommon",
    ),
    dict(
        id="genetic_matrix",
        kind="material",
        pt="Matriz Genetica",
        en="Genetic Matrix",
        lore_pt="Sequencia pre-historica reconstituida. Nucleo de qualquer ovo vital.",
        lore_en="Reconstituted prehistoric sequence. Core of any viable egg.",
        stack=16,
        category="items",
        rarity="epic",
        glint=True,
    ),
    dict(
        id="excavation_shovel",
        kind="tool",
        pt="Pa de Escavacao",
        en="Excavation Shovel",
        lore_pt="Reforcada com lasca ossea. Remove grandes volumes de sedimento, mas danifica especimes.",
        lore_en="Reinforced with bone shard. Moves bulk sediment fast but damages specimens.",
        stack=1,
        category="equipment",
        rarity="uncommon",
        durability=640,
        damage=3,
        hand_equipped=True,
        dig_speed=9,
        tags=["paleo:is_excavator", "paleo:is_field_tool", "minecraft:is_tool", "minecraft:is_shovel"],
        enchantable=dict(slot="shovel", value=14),
        repair=dict(items=["minecraft:iron_ingot"], amount="query.max_durability * 0.25"),
    ),
    dict(
        id="brush",
        kind="tool",
        pt="Pincel Paleontologico",
        en="Paleontology Brush",
        lore_pt="Extrai especimes integros que ferramentas brutas destroem. Lenta, mas precisa.",
        lore_en="Extracts intact specimens that brute tools destroy. Slow, but precise.",
        stack=1,
        category="equipment",
        rarity="uncommon",
        durability=192,
        damage=1,
        hand_equipped=True,
        dig_speed=2,
        tags=["paleo:is_brush", "paleo:is_field_tool", "minecraft:is_tool"],
        enchantable=dict(slot="shears", value=10),
        repair=dict(items=["minecraft:feather"], amount="query.max_durability * 0.25"),
    ),
    dict(
        id="fossil_scanner",
        kind="tool",
        pt="Scanner de Fosseis",
        en="Fossil Scanner",
        lore_pt="Detecta depositos fossiliferos reais num raio limitado e indica direcao e distancia.",
        lore_en="Detects real fossil deposits within a limited radius and reports bearing and range.",
        stack=1,
        category="equipment",
        rarity="rare",
        durability=320,
        hand_equipped=False,
        tags=["paleo:is_field_tool"],
        repair=dict(items=["minecraft:copper_ingot"], amount="query.max_durability * 0.25"),
        cooldown=dict(category="paleo_scanner", duration=8.0),
    ),
    dict(
        id="field_case",
        kind="tool",
        pt="Maleta de Campo",
        en="Field Case",
        lore_pt="Abre o caderno de campo e permite estudar criaturas recriadas.",
        lore_en="Opens the field journal and lets you study re-created creatures.",
        stack=1,
        category="equipment",
        rarity="uncommon",
        hand_equipped=False,
        tags=["paleo:is_field_tool"],
        cooldown=dict(category="paleo_fieldcase", duration=0.5),
    ),
]

# --------------------------------------------------------------------------
# Species
# --------------------------------------------------------------------------
# pool: which deposit yields the specimen; rarity drives loot weights AND lab costs
SPECIES = [
    dict(
        key="compy",
        entity="compsognathus",
        pt="Compsognato",
        en="Compsognathus",
        sci="Compsognathus longipes",
        era_pt="Jurassico Superior",
        era_en="Late Jurassic",
        diet_pt="Carnivoro de pequeno porte (insetos, lagartos)",
        diet_en="Small carnivore (insects, lizards)",
        size_pt="0,6 m de comprimento",
        size_en="0.6 m long",
        note_pt="Curioso e agil. Anda em bandos e foge de predadores grandes.",
        note_en="Curious and agile. Roams in packs and flees larger predators.",
        rarity="comum",
        rarity_en="common",
        egg_color=dict(base="#d9c48a", spots="#8c6b3f"),
        incubation_seconds=120,
        bondable=True,
        examine=dict(specimen=1, chip=4, shard=0, amber=0, xp=30),
        reconstruct=dict(matrix=1, specimen=1, gel=2, amber=0, xp=60),
    ),
    dict(
        key="trike",
        entity="triceratops",
        pt="Triceratopo",
        en="Triceratops",
        sci="Triceratops horridus",
        era_pt="Cretaceo Superior",
        era_en="Late Cretaceous",
        diet_pt="Herbivoro robusto (vegetacao rasteira, feno)",
        diet_en="Sturdy herbivore (low vegetation, hay)",
        size_pt="8 m de comprimento",
        size_en="8 m long",
        note_pt="Territorial quando acuado. Usa o chifre para repelir predadores.",
        note_en="Territorial when cornered. Uses its horn to repel predators.",
        rarity="incomum",
        rarity_en="uncommon",
        egg_color=dict(base="#a8b08c", spots="#5c6b45"),
        incubation_seconds=300,
        bondable=True,
        examine=dict(specimen=1, chip=8, shard=4, amber=0, xp=55),
        reconstruct=dict(matrix=2, specimen=2, gel=3, amber=0, xp=90),
    ),
    dict(
        key="raptor",
        entity="velociraptor",
        pt="Velociraptor",
        en="Velociraptor",
        sci="Velociraptor mongoliensis",
        era_pt="Cretaceo Superior",
        era_en="Late Cretaceous",
        diet_pt="Carnivoro agil, caca em matilha",
        diet_en="Agile carnivore, hunts in a pack",
        size_pt="2 m de comprimento",
        size_en="2 m long",
        note_pt="Persegue ate perder o alvo. O furor se propaga para individuos proximos.",
        note_en="Chases until the target escapes. Fury broadcasts to nearby individuals.",
        rarity="raro",
        rarity_en="rare",
        egg_color=dict(base="#8fa3a8", spots="#3d4f57"),
        incubation_seconds=360,
        bondable=True,
        examine=dict(specimen=2, chip=12, shard=8, amber=0, xp=90),
        reconstruct=dict(matrix=3, specimen=3, gel=4, amber=1, xp=140),
    ),
    dict(
        key="rex",
        entity="tyrannosaurus",
        pt="Tiranossauro",
        en="Tyrannosaurus",
        sci="Tyrannosaurus rex",
        era_pt="Cretaceo Superior",
        era_en="Late Cretaceous",
        diet_pt="Superpredador",
        diet_en="Apex predator",
        size_pt="12 m de comprimento",
        size_en="12 m long",
        note_pt="Patrulha um territorio. Ruge antes de avancar e desiste se a presa escapar.",
        note_en="Patrols a territory. Roars before charging and gives up if the prey escapes.",
        rarity="lendario",
        rarity_en="legendary",
        egg_color=dict(base="#7d5a44", spots="#3a2519"),
        incubation_seconds=600,
        bondable=True,
        examine=dict(specimen=3, chip=24, shard=16, amber=2, xp=160),
        reconstruct=dict(matrix=5, specimen=4, gel=6, amber=3, xp=260),
    ),
]

for sp in SPECIES:
    sp["entity_id"] = f"{NAMESPACE}:{sp['entity']}"
    sp["specimen_id"] = f"{NAMESPACE}:specimen_{sp['key']}"
    sp["egg_id"] = f"{NAMESPACE}:egg_{sp['key']}"

SPECIMEN_ITEMS = [
    dict(
        id=f"specimen_{sp['key']}",
        kind="specimen",
        species=sp["key"],
        pt=f"Especime Integro: {sp['pt']}",
        en=f"Intact Specimen: {sp['en']}",
        lore_pt=f"Fossil identificado de {sp['sci']}. Use na estacao de pesquisa.",
        lore_en=f"Identified fossil of {sp['sci']}. Bring it to the research station.",
        stack=16,
        category="items",
        rarity=sp["rarity_en"],
        hover=sp["rarity_en"],
    )
    for sp in SPECIES
]

EGG_ITEMS = [
    dict(
        id=f"egg_{sp['key']}",
        kind="egg",
        species=sp["key"],
        pt=f"Ovo Vital: {sp['pt']}",
        en=f"Viable Egg: {sp['en']}",
        lore_pt=f"Reconstrucao biologica estavel de {sp['sci']}. Precisa de uma incubadora.",
        lore_en=f"Stable biological reconstruction of {sp['sci']}. Requires an incubator.",
        stack=1,
        category="nature",
        rarity=sp["rarity_en"],
        hover=sp["rarity_en"],
    )
    for sp in SPECIES
]

ALL_ITEMS = ITEMS + SPECIMEN_ITEMS + EGG_ITEMS
ITEM_BY_ID = {it["id"]: it for it in ALL_ITEMS}
SPECIES_BY_KEY = {sp["key"]: sp for sp in SPECIES}


def item_id(short):
    return f"{NAMESPACE}:{short}"

BRUSH_TAG = "paleo:is_brush"
SHOVEL_TAG = "paleo:is_excavator"


# --------------------------------------------------------------------------
# Blocks
# --------------------------------------------------------------------------
DEPOSIT_BLOCKS = [
    dict(
        id="fossil_deposit",
        pt="Deposito Fossilifero",
        en="Fossiliferous Deposit",
        texture="paleo_fossil_deposit",
        map_color="#8a7358",
        seconds_to_destroy=1.15,
        explosion_resistance=6,
        sound="gravel",
        category="nature",
        group="itemGroup.name.ore",
        loot="loot_tables/blocks/fossil_deposit.json",
        tier="shallow",
    ),
    dict(
        id="shale_matrix",
        pt="Matriz de Folhelho",
        en="Shale Matrix",
        texture="paleo_shale_matrix",
        map_color="#4d545c",
        seconds_to_destroy=1.8,
        explosion_resistance=6,
        sound="stone",
        category="nature",
        group="itemGroup.name.ore",
        loot="loot_tables/blocks/shale_matrix.json",
        tier="deep",
    ),
    dict(
        id="bone_bed",
        pt="Leito Osseo",
        en="Bone Bed",
        texture="paleo_bone_bed",
        map_color="#c9bda2",
        seconds_to_destroy=2.2,
        explosion_resistance=6,
        sound="bone_block",
        category="nature",
        group="itemGroup.name.ore",
        loot="loot_tables/blocks/bone_bed.json",
        tier="rich",
    ),
]

STATION_BLOCKS = [
    dict(
        id="research_bench",
        pt="Estacao de Pesquisa",
        en="Research Station",
        geometry="geometry.paleo_research_bench",
        texture_prefix="paleo_research_bench",
        map_color="#6b5a44",
        seconds_to_destroy=1.6,
        explosion_resistance=12,
        sound="wood",
        category="construction",
        loot="loot_tables/blocks/research_bench.json",
        rotate=True,
        light=4,
    ),
    dict(
        id="incubator",
        pt="Incubadora",
        en="Incubator",
        geometry="geometry.paleo_incubator",
        texture_prefix="paleo_incubator",
        map_color="#4d6b6b",
        seconds_to_destroy=2.0,
        explosion_resistance=12,
        sound="metal",
        category="construction",
        loot="loot_tables/blocks/incubator.json",
        rotate=False,
        light=6,
        states=dict(stage=[0, 1, 2, 3, 4]),
    ),
]

ALL_BLOCKS = DEPOSIT_BLOCKS + STATION_BLOCKS
BLOCK_BY_ID = {b["id"]: b for b in ALL_BLOCKS}
DEPOSIT_TYPE_IDS = [f"{NAMESPACE}:{b['id']}" for b in DEPOSIT_BLOCKS]

# --------------------------------------------------------------------------
# World generation
# --------------------------------------------------------------------------
FEATURES = [
    dict(
        id="fossil_deposit_feature",
        rule_id="fossil_deposit_rule",
        block=f"{NAMESPACE}:fossil_deposit",
        count=9,
        y_min=-44,
        y_max=40,
        iterations=14,
        pass_="underground_pass",
        biome_tags=["overworld"],
        replace=[
            "minecraft:stone",
            "minecraft:granite",
            "minecraft:diorite",
            "minecraft:andesite",
            "minecraft:dirt",
            "minecraft:gravel",
        ],
    ),
    dict(
        id="shale_matrix_feature",
        rule_id="shale_matrix_rule",
        block=f"{NAMESPACE}:shale_matrix",
        count=7,
        y_min=-60,
        y_max=2,
        iterations=9,
        pass_="underground_pass",
        biome_tags=["overworld"],
        replace=[
            "minecraft:deepslate",
            "minecraft:tuff",
            "minecraft:stone",
            "minecraft:andesite",
        ],
    ),
    dict(
        id="bone_bed_feature",
        rule_id="bone_bed_rule",
        block=f"{NAMESPACE}:bone_bed",
        count=4,
        y_min=-40,
        y_max=26,
        iterations=3,
        pass_="underground_pass",
        biome_tags=["overworld"],
        replace=[
            "minecraft:stone",
            "minecraft:deepslate",
            "minecraft:granite",
            "minecraft:andesite",
            "minecraft:tuff",
        ],
    ),
    dict(
        id="surface_outcrop_feature",
        rule_id="surface_outcrop_rule",
        block=f"{NAMESPACE}:fossil_deposit",
        count=6,
        y_min=60,
        y_max=120,
        iterations=6,
        pass_="surface_pass",
        biome_tags=["mesa", "desert", "beach", "savanna"],
        replace=[
            "minecraft:sandstone",
            "minecraft:sand",
            "minecraft:red_sandstone",
            "minecraft:stone",
            "minecraft:gravel",
        ],
    ),
]

# --------------------------------------------------------------------------
# Crafting recipes (crafting table) - the lab/inventory actions live in scripts
# --------------------------------------------------------------------------
RECIPES = [
    dict(
        id="brush",
        result="paleo:brush",
        count=1,
        pattern=["  F", " B ", "S  "],
        key=dict(F="minecraft:feather", B="paleo:bone_shard", S="minecraft:stick"),
        tags=["paleo_field_gear"],
    ),
    dict(
        id="excavation_shovel",
        result="paleo:excavation_shovel",
        count=1,
        pattern=["BIB", " S ", " S "],
        key=dict(B="paleo:bone_shard", I="minecraft:iron_ingot", S="minecraft:stick"),
        tags=["paleo_field_gear"],
    ),
    dict(
        id="field_case",
        result="paleo:field_case",
        count=1,
        pattern=["LPL", "PCP", "LPL"],
        key=dict(
            L="minecraft:leather",
            P="minecraft:paper",
            C="paleo:fossil_chip",
        ),
        tags=["paleo_field_gear"],
    ),
    dict(
        id="fossil_scanner",
        result="paleo:fossil_scanner",
        count=1,
        pattern=["IGI", "CRC", "SFS"],
        key=dict(
            I="minecraft:iron_ingot",
            G="minecraft:glass",
            C="minecraft:copper_ingot",
            R="minecraft:redstone",
            S="paleo:bone_shard",
            F="paleo:fossil_chip",
        ),
        tags=["paleo_field_gear"],
    ),
    dict(
        id="research_bench",
        result="paleo:research_bench",
        count=1,
        pattern=["GBG", "ITI", "SPS"],
        key=dict(
            G="minecraft:glass",
            B="minecraft:book",
            I="minecraft:iron_ingot",
            T="minecraft:crafting_table",
            S="paleo:bone_shard",
            P="minecraft:oak_planks",
        ),
        tags=["paleo_station"],
    ),
    dict(
        id="incubator",
        result="paleo:incubator",
        count=1,
        pattern=["IGI", "RIR", "NIN"],
        key=dict(
            I="minecraft:iron_ingot",
            G="minecraft:glass",
            R="minecraft:redstone",
            N="paleo:nutrient_gel",
        ),
        tags=["paleo_station"],
    ),
]

# Laboratory conversions (executed by script against the player inventory).
LAB_PROCESSES = [
    dict(
        id="refine_matrix",
        pt="Refinar Matriz Genetica",
        en="Refine Genetic Matrix",
        desc_pt="12 Fragmentos de Sedimento + 6 Lascas Osseas -> 1 Matriz Genetica",
        desc_en="12 Sediment Fragment + 6 Bone Shard -> 1 Genetic Matrix",
        inputs=[("paleo:fossil_chip", 12), ("paleo:bone_shard", 6)],
        outputs=[("paleo:genetic_matrix", 1)],
        xp=20,
        sound="paleo.lab.process",
    ),
    dict(
        id="catalyze_matrix",
        pt="Catalisar Matriz com Ambar",
        en="Catalyse Matrix with Amber",
        desc_pt="1 Matriz Genetica + 1 Inclusao em Ambar -> 3 Matrizes Geneticas",
        desc_en="1 Genetic Matrix + 1 Amber Inclusion -> 3 Genetic Matrix",
        inputs=[("paleo:genetic_matrix", 1), ("paleo:amber_inclusion", 1)],
        outputs=[("paleo:genetic_matrix", 3)],
        xp=35,
        sound="paleo.lab.process",
        requires_any_species=True,
    ),
    dict(
        id="synthesize_gel",
        pt="Sintetizar Gel Nutritivo",
        en="Synthesise Nutrient Gel",
        desc_pt="4 Lascas Osseas + 6 Fragmentos de Sedimento -> 2 Geis Nutritivos",
        desc_en="4 Bone Shard + 6 Sediment Fragment -> 2 Nutrient Gel",
        inputs=[("paleo:bone_shard", 4), ("paleo:fossil_chip", 6)],
        outputs=[("paleo:nutrient_gel", 2)],
        xp=12,
        sound="paleo.lab.process",
    ),
]

# --------------------------------------------------------------------------
# Loot tables
# --------------------------------------------------------------------------
def _with_brush():
    """Loot condition: the tool in hand carries the paleo brush tag."""
    return dict(condition="match_tool", **{"minecraft:match_tool_filter_all": [BRUSH_TAG]})


def _without_brush():
    """Loot condition: the tool in hand is NOT a paleo brush (brute extraction)."""
    return dict(condition="match_tool", **{"minecraft:match_tool_filter_none": [BRUSH_TAG]})


def _with_shovel():
    return dict(condition="match_tool", **{"minecraft:match_tool_filter_all": [SHOVEL_TAG]})


def _chance(value):
    return dict(condition="random_chance", chance=value)


# --------------------------------------------------------------------------
# Loot tables
#
# Design rules enforced purely by data (no script, no cancellation, so they hold
# in multiplayer and even if the script layer is disabled):
#   * every deposit yields a guaranteed base pool, so nothing is ever a dead block
#   * intact species specimens ONLY drop for the paleontological brush
#   * the excavation shovel trades specimen integrity for bulk sediment
#   * amber inclusions are brush-only and depth-gated (rarity == effort)
# --------------------------------------------------------------------------
LOOT_DEPOSITS = {
    "fossil_deposit": dict(
        pools=[
            dict(
                rolls=dict(min=1, max=2),
                entries=[
                    dict(type="item", name=item_id("fossil_chip"), weight=6),
                    dict(type="item", name=item_id("bone_shard"), weight=2),
                ],
            ),
            dict(
                rolls=1,
                conditions=[_with_brush()],
                entries=[
                    dict(type="item", name=item_id("specimen_compy"), weight=26),
                    dict(type="item", name=item_id("specimen_trike"), weight=9),
                    dict(type="empty", weight=65),
                ],
            ),
            dict(
                rolls=1,
                conditions=[_with_brush(), _chance(0.06)],
                entries=[dict(type="item", name=item_id("amber_inclusion"), weight=1)],
            ),
            dict(
                rolls=dict(min=2, max=4),
                conditions=[_with_shovel()],
                entries=[dict(type="item", name=item_id("fossil_chip"), weight=1)],
            ),
        ],
    ),
    "shale_matrix": dict(
        pools=[
            dict(
                rolls=dict(min=2, max=3),
                entries=[
                    dict(type="item", name=item_id("fossil_chip"), weight=4),
                    dict(type="item", name=item_id("bone_shard"), weight=4),
                ],
            ),
            dict(
                rolls=1,
                conditions=[_with_brush()],
                entries=[
                    dict(type="item", name=item_id("specimen_trike"), weight=13),
                    dict(type="item", name=item_id("specimen_raptor"), weight=10),
                    dict(type="item", name=item_id("specimen_compy"), weight=5),
                    dict(type="item", name=item_id("specimen_rex"), weight=2),
                    dict(type="empty", weight=70),
                ],
            ),
            dict(
                rolls=1,
                conditions=[_with_brush(), _chance(0.14)],
                entries=[dict(type="item", name=item_id("amber_inclusion"), weight=1)],
            ),
            dict(
                rolls=dict(min=2, max=5),
                conditions=[_with_shovel()],
                entries=[
                    dict(type="item", name=item_id("bone_shard"), weight=1),
                    dict(type="item", name=item_id("fossil_chip"), weight=2),
                ],
            ),
        ],
    ),
    "bone_bed": dict(
        pools=[
            # Brush: the specimen comes out intact.
            dict(
                rolls=dict(min=1, max=2),
                conditions=[_with_brush()],
                entries=[dict(type="item", name=item_id("bone_shard"), weight=1)],
            ),
            dict(
                rolls=1,
                conditions=[_with_brush()],
                entries=[
                    dict(type="item", name=item_id("specimen_compy"), weight=20),
                    dict(type="item", name=item_id("specimen_trike"), weight=22),
                    dict(type="item", name=item_id("specimen_raptor"), weight=20),
                    dict(type="item", name=item_id("specimen_rex"), weight=8),
                    dict(type="empty", weight=30),
                ],
            ),
            dict(
                rolls=1,
                conditions=[_with_brush(), _chance(0.25)],
                entries=[dict(type="item", name=item_id("amber_inclusion"), weight=1)],
            ),
            # No brush: the skeleton shatters, only shards survive.
            dict(
                rolls=dict(min=2, max=4),
                conditions=[_without_brush()],
                entries=[dict(type="item", name=item_id("bone_shard"), weight=1)],
            ),
            dict(
                rolls=dict(min=1, max=3),
                conditions=[_with_shovel()],
                entries=[dict(type="item", name=item_id("fossil_chip"), weight=1)],
            ),
        ],
    ),
}

LOOT_STATIONS = {
    "research_bench": dict(
        pools=[dict(rolls=1, entries=[dict(type="item", name=item_id("research_bench"), weight=1)])]
    ),
    "incubator": dict(
        pools=[dict(rolls=1, entries=[dict(type="item", name=item_id("incubator"), weight=1)])]
    ),
}

LOOT_ENTITIES = {
    "compsognathus": dict(
        pools=[
            dict(rolls=dict(min=0, max=2),
                 entries=[dict(type="item", name=item_id("bone_shard"), weight=1)]),
            dict(rolls=dict(min=0, max=2),
                 conditions=[dict(condition="killed_by_player")],
                 entries=[dict(type="item", name=item_id("fossil_chip"), weight=1)]),
        ]
    ),
    "triceratops": dict(
        pools=[
            dict(rolls=dict(min=1, max=3),
                 entries=[dict(type="item", name=item_id("bone_shard"), weight=1)]),
            dict(rolls=dict(min=1, max=3),
                 entries=[dict(type="item", name="minecraft:leather", weight=1)]),
            dict(rolls=1, conditions=[dict(condition="random_chance", chance=0.06)],
                 entries=[dict(type="item", name=item_id("amber_inclusion"), weight=1)]),
        ]
    ),
    "velociraptor": dict(
        pools=[
            dict(rolls=dict(min=1, max=3),
                 entries=[dict(type="item", name=item_id("bone_shard"), weight=1)]),
            dict(rolls=dict(min=0, max=2),
                 entries=[dict(type="item", name=item_id("fossil_chip"), weight=1)]),
            dict(rolls=1, conditions=[dict(condition="random_chance", chance=0.10)],
                 entries=[dict(type="item", name=item_id("amber_inclusion"), weight=1)]),
        ]
    ),
    "tyrannosaurus": dict(
        pools=[
            dict(rolls=dict(min=4, max=8),
                 entries=[dict(type="item", name=item_id("bone_shard"), weight=1)]),
            dict(rolls=dict(min=2, max=5),
                 entries=[dict(type="item", name=item_id("fossil_chip"), weight=1)]),
            dict(rolls=1, conditions=[dict(condition="random_chance", chance=0.35)],
                 entries=[dict(type="item", name=item_id("amber_inclusion"), weight=1)]),
        ]
    ),
}

# --------------------------------------------------------------------------
# Sounds
# --------------------------------------------------------------------------
# Each entry becomes one generated .ogg + one sound_definitions.json entry.
SOUND_DEFS = [
    # field work
    dict(id="paleo.dig.sediment", files=["sediment1", "sediment2", "sediment3"], category="block", volume=0.9, pitch=[0.9, 1.15]),
    dict(id="paleo.dig.brush", files=["brush1", "brush2"], category="block", volume=0.8, pitch=[0.95, 1.2]),
    dict(id="paleo.discover", files=["discover"], category="player", volume=1.0, pitch=[1.0, 1.05]),
    dict(id="paleo.discover.rare", files=["discover_rare"], category="player", volume=1.0, pitch=[1.0, 1.03]),
    dict(id="paleo.scanner.ping", files=["scan_ping"], category="player", volume=0.9, pitch=[1.0, 1.08]),
    dict(id="paleo.scanner.strong", files=["scan_strong"], category="player", volume=1.0, pitch=[1.0, 1.04]),
    dict(id="paleo.scanner.empty", files=["scan_empty"], category="player", volume=0.7, pitch=[1.0, 1.05]),
    # laboratory
    dict(id="paleo.lab.process", files=["lab_process"], category="player", volume=1.0, pitch=[1.0, 1.04]),
    dict(id="paleo.lab.identify", files=["lab_identify"], category="player", volume=1.0, pitch=[1.0, 1.03]),
    dict(id="paleo.lab.deny", files=["lab_deny"], category="player", volume=0.8, pitch=[1.0, 1.05]),
    dict(id="paleo.bench.open", files=["bench_open"], category="block", volume=0.9, pitch=[0.95, 1.05]),
    # incubator
    dict(id="paleo.incubator.start", files=["incu_start"], category="block", volume=1.0, pitch=[1.0, 1.04]),
    dict(id="paleo.incubator.progress", files=["incu_progress"], category="block", volume=0.55, pitch=[1.0, 1.1]),
    dict(id="paleo.incubator.hatch", files=["incu_hatch"], category="block", volume=1.0, pitch=[1.0, 1.03]),
    # creatures
    dict(id="paleo.mob.compy.idle", files=["compy_idle1", "compy_idle2"], category="neutral", volume=0.7, pitch=[0.95, 1.2]),
    dict(id="paleo.mob.compy.hurt", files=["compy_hurt"], category="neutral", volume=0.9, pitch=[0.95, 1.1]),
    dict(id="paleo.mob.compy.death", files=["compy_death"], category="neutral", volume=0.9, pitch=[0.95, 1.05]),
    dict(id="paleo.mob.compy.step", files=["compy_step1", "compy_step2"], category="neutral", volume=0.35, pitch=[0.9, 1.2]),
    dict(id="paleo.mob.trike.idle", files=["trike_idle1", "trike_idle2"], category="neutral", volume=0.9, pitch=[0.9, 1.1]),
    dict(id="paleo.mob.trike.hurt", files=["trike_hurt"], category="neutral", volume=1.0, pitch=[0.9, 1.05]),
    dict(id="paleo.mob.trike.death", files=["trike_death"], category="neutral", volume=1.0, pitch=[0.9, 1.0]),
    dict(id="paleo.mob.trike.step", files=["trike_step1", "trike_step2"], category="neutral", volume=0.75, pitch=[0.85, 1.1]),
    dict(id="paleo.mob.trike.angry", files=["trike_angry"], category="neutral", volume=1.0, pitch=[0.92, 1.05]),
    dict(id="paleo.mob.raptor.idle", files=["raptor_idle1", "raptor_idle2"], category="hostile", volume=0.85, pitch=[0.95, 1.15]),
    dict(id="paleo.mob.raptor.hurt", files=["raptor_hurt"], category="hostile", volume=0.95, pitch=[0.95, 1.1]),
    dict(id="paleo.mob.raptor.death", files=["raptor_death"], category="hostile", volume=0.95, pitch=[0.95, 1.05]),
    dict(id="paleo.mob.raptor.step", files=["raptor_step1", "raptor_step2"], category="hostile", volume=0.45, pitch=[0.9, 1.2]),
    dict(id="paleo.mob.raptor.screech", files=["raptor_screech"], category="hostile", volume=1.0, pitch=[0.97, 1.08]),
    dict(id="paleo.mob.rex.idle", files=["rex_idle1", "rex_idle2"], category="hostile", volume=1.0, pitch=[0.88, 1.05]),
    dict(id="paleo.mob.rex.hurt", files=["rex_hurt"], category="hostile", volume=1.0, pitch=[0.9, 1.02]),
    dict(id="paleo.mob.rex.death", files=["rex_death"], category="hostile", volume=1.0, pitch=[0.9, 1.0]),
    dict(id="paleo.mob.rex.step", files=["rex_step1", "rex_step2"], category="hostile", volume=0.95, pitch=[0.8, 1.0]),
    dict(id="paleo.mob.rex.roar", files=["rex_roar"], category="hostile", volume=1.0, pitch=[0.95, 1.02]),
    dict(id="paleo.mob.rex.bite", files=["rex_bite"], category="hostile", volume=1.0, pitch=[0.95, 1.05]),
]

SOUND_IDS = [s["id"] for s in SOUND_DEFS]

ENTITY_SOUND_EVENTS = {
    "compsognathus": dict(
        volume=1.0, pitch=[0.95, 1.1],
        events=dict(
            ambient=f"{NAMESPACE}.mob.compy.idle",
            hurt=f"{NAMESPACE}.mob.compy.hurt",
            death=f"{NAMESPACE}.mob.compy.death",
            step=f"{NAMESPACE}.mob.compy.step",
        ),
    ),
    "triceratops": dict(
        volume=1.0, pitch=[0.92, 1.08],
        events=dict(
            ambient=f"{NAMESPACE}.mob.trike.idle",
            hurt=f"{NAMESPACE}.mob.trike.hurt",
            death=f"{NAMESPACE}.mob.trike.death",
            step=f"{NAMESPACE}.mob.trike.step",
            angry=f"{NAMESPACE}.mob.trike.angry",
        ),
    ),
    "velociraptor": dict(
        volume=1.0, pitch=[0.95, 1.1],
        events=dict(
            ambient=f"{NAMESPACE}.mob.raptor.idle",
            hurt=f"{NAMESPACE}.mob.raptor.hurt",
            death=f"{NAMESPACE}.mob.raptor.death",
            step=f"{NAMESPACE}.mob.raptor.step",
            angry=f"{NAMESPACE}.mob.raptor.screech",
            attack=f"{NAMESPACE}.mob.raptor.screech",
        ),
    ),
    "tyrannosaurus": dict(
        volume=1.0, pitch=[0.95, 1.05],
        events=dict(
            ambient=f"{NAMESPACE}.mob.rex.idle",
            hurt=f"{NAMESPACE}.mob.rex.hurt",
            death=f"{NAMESPACE}.mob.rex.death",
            step=f"{NAMESPACE}.mob.rex.step",
            roar=f"{NAMESPACE}.mob.rex.roar",
            prepare_attack=f"{NAMESPACE}.mob.rex.roar",
            attack_strong=f"{NAMESPACE}.mob.rex.bite",
            angry=f"{NAMESPACE}.mob.rex.roar",
        ),
    ),
}

BLOCK_SOUND_GROUPS = {
    "paleo:sediment": dict(
        events=dict(
            default=dict(sound="paleo.dig.sediment", volume=1.0, pitch=1.0),
            item_use_on=dict(sound="paleo.dig.sediment", volume=0.9, pitch=1.0),
            **{"break": dict(sound="paleo.dig.sediment", volume=1.0, pitch=0.95)},
            place=dict(sound="paleo.dig.sediment", volume=1.0, pitch=0.9),
            hit=dict(sound="paleo.dig.sediment", volume=0.35, pitch=0.6),
            power_on=dict(sound="block.click", volume=1.0, pitch=0.6),
            power_off=dict(sound="block.click", volume=1.0, pitch=0.5),
        ),
        volume=1.0,
        pitch=1.0,
    ),
    "paleo:bone": dict(
        events=dict(
            default=dict(sound="paleo.dig.sediment", volume=1.0, pitch=0.85),
            item_use_on=dict(sound="paleo.dig.sediment", volume=0.9, pitch=0.85),
            **{"break": dict(sound="paleo.dig.sediment", volume=1.0, pitch=0.8)},
            place=dict(sound="paleo.dig.sediment", volume=1.0, pitch=0.78),
            hit=dict(sound="paleo.dig.sediment", volume=0.35, pitch=0.55),
            power_on=dict(sound="block.click", volume=1.0, pitch=0.6),
            power_off=dict(sound="block.click", volume=1.0, pitch=0.5),
        ),
        volume=1.0,
        pitch=1.0,
    ),
    "paleo:machine": dict(
        events=dict(
            default=dict(sound="paleo.bench.open", volume=0.9, pitch=1.0),
            item_use_on=dict(sound="paleo.bench.open", volume=0.9, pitch=1.0),
            **{"break": dict(sound="paleo.lab.deny", volume=0.8, pitch=0.9)},
            place=dict(sound="paleo.bench.open", volume=1.0, pitch=0.85),
            hit=dict(sound="paleo.bench.open", volume=0.3, pitch=0.6),
            power_on=dict(sound="block.click", volume=1.0, pitch=0.7),
            power_off=dict(sound="block.click", volume=1.0, pitch=0.6),
        ),
        volume=1.0,
        pitch=1.0,
    ),
}

BLOCK_SOUND_ASSIGNMENT = {
    "fossil_deposit": "paleo:sediment",
    "shale_matrix": "paleo:sediment",
    "bone_bed": "paleo:bone",
    "research_bench": "paleo:machine",
    "incubator": "paleo:machine",
}

# Block tags: which vanilla tool families mine the block faster.
BLOCK_ITEM_TAGS = {
    "fossil_deposit": ["minecraft:is_shovel_item_destructible", "minecraft:is_pickaxe_item_destructible"],
    "shale_matrix": ["minecraft:is_pickaxe_item_destructible"],
    "bone_bed": ["minecraft:is_pickaxe_item_destructible"],
    "research_bench": ["minecraft:is_pickaxe_item_destructible", "minecraft:is_axe_item_destructible"],
    "incubator": ["minecraft:is_pickaxe_item_destructible"],
}

# ---------------------------------------------------------------------------
# PT-BR orthography: the tables above are kept ASCII for tooling safety and the
# accents are applied deterministically at generation time.
# ---------------------------------------------------------------------------
PT_PHRASES = {
    " esta vazia": " está vazia",
    " esta fria": " está fria",
    " esta pronto": " está pronto",
    "A camara esta": "A câmara está",
    "O ovo so se desenvolve": "O ovo só se desenvolve",
}

PT_ACCENTS = {
    "Ambar": "Âmbar", "ambar": "âmbar", "Bonus": "Bônus", "Camara": "Câmara",
    "camara": "câmara", "Carnivoro": "Carnívoro", "Cretaceo": "Cretáceo",
    "Deposito": "Depósito", "deposito": "depósito", "Depositos": "Depósitos",
    "depositos": "depósitos", "Escavacao": "Escavação", "Especie": "Espécie",
    "especie": "espécie", "Especies": "Espécies", "especies": "espécies",
    "Especime": "Espécime", "especime": "espécime", "especimes": "espécimes",
    "Estacao": "Estação", "estacao": "estação", "Estatisticas": "Estatísticas",
    "Fosseis": "Fósseis", "fosseis": "fósseis", "Fossil": "Fóssil",
    "fossil": "fóssil", "Fossilifero": "Fossilífero", "fossilifero": "fossilífero",
    "fossiliferos": "fossilíferos", "Genetica": "Genética", "genetica": "genética",
    "Herbivoro": "Herbívoro", "Inclusao": "Inclusão", "Incubacao": "Incubação",
    "incubacao": "incubação", "Individuos": "Indivíduos", "individuos": "indivíduos",
    "Integro": "Íntegro", "integro": "íntegro", "integros": "íntegros",
    "Jurassico": "Jurássico", "NAO": "NÃO", "Nao": "Não", "nao": "não",
    "Nivel": "Nível", "Nucleo": "Núcleo", "Operacao": "Operação",
    "operacao": "operação", "Ossea": "Óssea", "ossea": "óssea", "osseas": "ósseas",
    "Osseo": "Ósseo", "Pa": "Pá", "Paleontologico": "Paleontológico",
    "Reconstrucao": "Reconstrução", "reconstrucao": "reconstrução",
    "Reforcada": "Reforçada", "Sequencia": "Sequência", "Voce": "Você",
    "voce": "você", "agil": "ágil", "area": "área", "ate": "até",
    "avanca": "avança", "avancar": "avançar", "basico": "básico",
    "biologica": "biológica", "caca": "caça", "calcio": "cálcio",
    "concluida": "concluída", "conversao": "conversão", "direcao": "direção",
    "distancia": "distância", "epico": "épico", "estagio": "estágio",
    "estavel": "estável", "expedicao": "expedição", "extracao": "extração",
    "forca": "força", "historica": "histórica", "individuo": "indivíduo",
    "inventario": "inventário", "ja": "já", "laboratorio": "laboratório",
    "lendario": "lendário", "necessarios": "necessários", "proxima": "próxima",
    "proximos": "próximos", "quao": "quão", "reconstituida": "reconstituída",
    "so": "só", "territorio": "território", "vegetacao": "vegetação",
}


def pt_br(text):
    """Applies PT-BR orthography to an ASCII-safe source string."""
    if not text:
        return text
    for source, target in PT_PHRASES.items():
        text = text.replace(source, target)
    for source, target in PT_ACCENTS.items():
        text = re.sub(rf"\b{source}\b", target, text)
    return text

