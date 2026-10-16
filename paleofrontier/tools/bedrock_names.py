"""Vocabulario oficial do Bedrock, derivado dos samples vanilla 1.26.50.4.

Fonte: Mojang/bedrock-samples (tag 1.26.50.4) + MicrosoftDocs/minecraft-creator.
Usado por gen_rp.py (para emitir nomes corretos) e por validate.py (para
rejeitar qualquer nome fora do vocabulario que o cliente aceita).
"""

BLOCK_SOUND_EVENTS = frozenset({
    "activate", "ambient", "ambient.in.water", "break",
    "break_pot", "brush", "brush_completed", "button.click_off",
    "button.click_on", "chest.closed", "chest.open", "close",
    "close_long", "creaking_heart_spawn", "deactivate", "default",
    "door.close", "door.open", "fall", "fence_gate.close",
    "fence_gate.open", "hit", "insert", "insert_enchanted",
    "item.use.on", "multi_swap", "open", "open_long",
    "pickup", "pickup_enchanted", "place", "place_in_water",
    "place_item", "power.off", "power.on", "pressure_plate.click_off",
    "pressure_plate.click_on", "shatter_pot", "single_swap", "state_change",
    "step", "straw_bed.break_leave", "trapdoor.close", "trapdoor.open",
})

ENTITY_SOUND_EVENTS = frozenset({
    "absorb_block", "activate", "add.chest", "admire",
    "agitated", "ambient", "ambient.aggressive", "ambient.baby",
    "ambient.in.air", "ambient.in.raid", "ambient.in.water", "ambient.pollinate",
    "ambient.screamer", "ambient.tame", "ambient.worried", "angry",
    "armor", "armor.equip_generic", "armor.unequip_generic", "attach",
    "attack", "attack.critical", "attack.nodamage", "attack.strong",
    "boost", "born", "bounce", "break.block",
    "breathe", "cant_breed", "cast.spell", "celebrate",
    "charge", "creaking_heart_spawn", "dash_ready", "deactivate",
    "death", "death.baby", "death.in.water", "death.mid.volume",
    "death.min.volume", "death.screamer", "death.to.zombie", "detach",
    "disappeared", "dismount", "drink", "drink.milk",
    "eat", "eject_block", "elderguardian.curse", "explode",
    "fang", "fizz", "flap", "flop",
    "fly", "freeze", "fuse", "growl",
    "haggle", "haggle.no", "haggle.yes", "heartbeat",
    "hurt", "hurt.baby", "hurt.in.water", "hurt.reduced",
    "hurt.screamer", "imitate.blaze", "imitate.bogged", "imitate.breeze",
    "imitate.camel_husk", "imitate.cave_spider", "imitate.creaking", "imitate.creeper",
    "imitate.drowned", "imitate.elder_guardian", "imitate.ender_dragon", "imitate.enderman",
    "imitate.endermite", "imitate.evocation_illager", "imitate.ghast", "imitate.guardian",
    "imitate.happy_ghast", "imitate.husk", "imitate.magma_cube", "imitate.parched",
    "imitate.phantom", "imitate.pillager", "imitate.polar_bear", "imitate.ravager",
    "imitate.shulker", "imitate.silverfish", "imitate.skeleton", "imitate.slime",
    "imitate.spider", "imitate.stray", "imitate.vex", "imitate.vindication_illager",
    "imitate.warden", "imitate.witch", "imitate.wither", "imitate.wither_skeleton",
    "imitate.wolf", "imitate.zoglin", "imitate.zombie", "imitate.zombie_pigman",
    "imitate.zombie_villager", "irongolem.crack", "irongolem.repair", "jump",
    "jump_to_block", "land", "listening", "listening_angry",
    "mad", "mob.warning", "mount", "nearby_close",
    "nearby_closer", "nearby_closest", "panic", "pant",
    "plop", "prepare.attack", "prepare.summon", "prepare.wololo",
    "presneeze", "purr", "purreow", "reappeared",
    "reflect", "retreat", "roar", "saddle",
    "saddle_in_water", "screech", "shake", "shoot",
    "shulker.close", "shulker.open", "sleep", "slime_landing",
    "sneeze", "spawn", "splash", "squish.big",
    "squish.small", "stare", "step", "step.baby",
    "step_lava", "step_sand", "stun", "swim",
    "swoop", "takeoff", "teleport", "tempt",
    "throw", "thunder", "unfreeze", "unsaddle",
    "warn", "whine",
})

ANIMATION_KEYS = frozenset({
    "anim_time_update", "animation_length", "bones", "loop",
    "override_previous_animation", "particle_effects", "sound_effects", "start_delay",
})

CLIENT_ENTITY_DESCRIPTION_KEYS = frozenset({
    "animation_controllers", "animations", "enable_attachables", "geometry",
    "held_item_ignores_lighting", "held_item_scale", "hide_armor", "identifier",
    "materials", "min_engine_version", "particle_effects", "particle_emitters",
    "render_controllers", "scripts", "sound_effects", "spawn_egg",
    "textures",
})

RECIPE_MENU_TAGS = frozenset({
    "blast_furnace", "brewing_stand", "campfire", "cartography_table",
    "crafting_table", "deprecated", "furnace", "smithing_table",
    "smoker", "soul_campfire", "stonecutter",
})


# Grupos vanilla do catalogo criativo (CraftingItemCatalogDocumentation.md).
ITEM_GROUPS = frozenset({
    "minecraft:itemGroup.name.planks", "minecraft:itemGroup.name.walls", "minecraft:itemGroup.name.fence",
    "minecraft:itemGroup.name.fenceGate", "minecraft:itemGroup.name.stairs", "minecraft:itemGroup.name.door",
    "minecraft:itemGroup.name.trapdoor", "minecraft:itemGroup.name.glass", "minecraft:itemGroup.name.glassPane",
    "minecraft:itemGroup.name.slab", "minecraft:itemGroup.name.stoneBrick", "minecraft:itemGroup.name.sandstone",
    "minecraft:itemGroup.name.copper", "minecraft:itemGroup.name.wool", "minecraft:itemGroup.name.woolCarpet",
    "minecraft:itemGroup.name.concretePowder", "minecraft:itemGroup.name.concrete", "minecraft:itemGroup.name.stainedClay",
    "minecraft:itemGroup.name.glazedTerracotta", "minecraft:itemGroup.name.ore", "minecraft:itemGroup.name.stone",
    "minecraft:itemGroup.name.log", "minecraft:itemGroup.name.wood", "minecraft:itemGroup.name.leaves",
    "minecraft:itemGroup.name.sapling", "minecraft:itemGroup.name.seed", "minecraft:itemGroup.name.crop",
    "minecraft:itemGroup.name.grass", "minecraft:itemGroup.name.coral_decorations", "minecraft:itemGroup.name.flower",
    "minecraft:itemGroup.name.dye", "minecraft:itemGroup.name.rawFood", "minecraft:itemGroup.name.mushroom",
    "minecraft:itemGroup.name.monsterStoneEgg", "minecraft:itemGroup.name.mobEgg", "minecraft:itemGroup.name.coral",
    "minecraft:itemGroup.name.sculk", "minecraft:itemGroup.name.helmet", "minecraft:itemGroup.name.chestplate",
    "minecraft:itemGroup.name.leggings", "minecraft:itemGroup.name.boots", "minecraft:itemGroup.name.sword",
    "minecraft:itemGroup.name.axe", "minecraft:itemGroup.name.pickaxe", "minecraft:itemGroup.name.shovel",
    "minecraft:itemGroup.name.hoe", "minecraft:itemGroup.name.arrow", "minecraft:itemGroup.name.cookedFood",
    "minecraft:itemGroup.name.miscFood", "minecraft:itemGroup.name.goatHorn", "minecraft:itemGroup.name.bundles",
    "minecraft:itemGroup.name.horseArmor", "minecraft:itemGroup.name.potion", "minecraft:itemGroup.name.splashPotion",
    "minecraft:itemGroup.name.lingeringPotion", "minecraft:itemGroup.name.ominousBottle", "minecraft:itemGroup.name.bed",
    "minecraft:itemGroup.name.candles", "minecraft:itemGroup.name.anvil", "minecraft:itemGroup.name.chest",
    "minecraft:itemGroup.name.shulkerBox", "minecraft:itemGroup.name.record", "minecraft:itemGroup.name.sign",
    "minecraft:itemGroup.name.hanging_sign", "minecraft:itemGroup.name.skull", "minecraft:itemGroup.name.boat",
    "minecraft:itemGroup.name.chestboat", "minecraft:itemGroup.name.rail", "minecraft:itemGroup.name.minecart",
    "minecraft:itemGroup.name.buttons", "minecraft:itemGroup.name.pressurePlate", "minecraft:itemGroup.name.banner_pattern",
    "minecraft:itemGroup.name.potterySherds", "minecraft:itemGroup.name.smithing_templates",
})

# Componentes de entidade que o cliente 1.26.x NAO parseia mais, com o
# substituto oficial.  Fonte: MicrosoftDocs/minecraft-creator,
# Update1.26.10.md ("Pushable Component Split": "The original
# minecraft:pushable component will no longer be parsed").
REMOVED_ENTITY_COMPONENTS = {
    "minecraft:pushable": ("minecraft:pushable_by_entity", "minecraft:pushable_by_block"),
}

# Mapeamento dos nomes usados no content_model (identificadores Python nao
# podem conter ponto) para os nomes de LevelSoundEvent que o cliente aceita.
SOUND_EVENT_ALIASES = {
    "item_use_on": "item.use.on",
    "power_on": "power.on",
    "power_off": "power.off",
    "prepare_attack": "prepare.attack",
    "attack_strong": "attack.strong",
    "attack_critical": "attack.critical",
    "attack_nodamage": "attack.nodamage",
    "cast_spell": "cast.spell",
    "death_baby": "death.baby",
    "hurt_baby": "hurt.baby",
    "step_baby": "step.baby",
    "ambient_baby": "ambient.baby",
    "ambient_in_water": "ambient.in.water",
    "death_in_water": "death.in.water",
    "hurt_in_water": "hurt.in.water",
}


def sound_event_key(name):
    """Traduz um nome de evento do content_model para o nome do cliente."""
    return SOUND_EVENT_ALIASES.get(name, name)


# Campos "float range": a partir do format_version indicado SO aceitam um objeto
# {"min": ..., "max": ...}.  Qualquer outro formato faz o JSON da entidade
# falhar ao carregar.  Entidades com format_version anterior continuam aceitando
# o formato legado (o proprio bedrock-samples traz arquivos assim: bat.json
# fv 1.26.0, bogged.json fv 1.26.30), por isso a regra e gated por versao.
#
# Fonte: MicrosoftDocs/minecraft-creator
#   Update1.26.0.md  "Float Range Field Updates" / "Look At Behavior Updates"
#   Update1.26.10.md "Float Range Field Changes"
#   Update1.26.40.md "migration requirements for format_version 1.26.40 and later"
#
# Calibrado por tools/calibrate_entity_rules.py: com o gating abaixo, nenhuma
# entidade vanilla do bedrock-samples 1.26.50.4 viola a regra.
FLOAT_RANGE_FIELDS = {
    # --- estritos desde 1.26.0 ---
    "minecraft:behavior.nearest_attackable_target": {"attack_interval": "1.26.0"},
    "minecraft:behavior.dragonchargeplayer": {"target_zone": "1.26.0"},
    "minecraft:behavior.dragonstrafeplayer": {"target_zone": "1.26.0"},
    "minecraft:behavior.timer_flag_1": {"cooldown_range": "1.26.0", "duration_range": "1.26.0"},
    "minecraft:behavior.timer_flag_2": {"cooldown_range": "1.26.0", "duration_range": "1.26.0"},
    "minecraft:behavior.timer_flag_3": {"cooldown_range": "1.26.0", "duration_range": "1.26.0"},
    "minecraft:behavior.look_at_entity": {"look_time": "1.26.0"},
    "minecraft:behavior.look_at_player": {"look_time": "1.26.0"},
    "minecraft:behavior.look_at_target": {"look_time": "1.26.0"},
    "minecraft:behavior.look_at_trading_player": {"look_time": "1.26.0"},
    # --- estritos desde 1.26.10 ---
    "minecraft:behavior.drop_item_for": {"time_of_day_range": "1.26.10"},
    "minecraft:behavior.ram_attack": {"cooldown_range": "1.26.10"},
    "minecraft:behavior.celebrate": {"sound_interval": "1.26.10", "jump_interval": "1.26.10"},
    "minecraft:behavior.celebrate_survive": {"fireworks_interval": "1.26.10"},
    "minecraft:behavior.random_search_and_dig": {
        "cooldown_range": "1.26.10",
        "digging_duration_range": "1.26.10",
    },
    "minecraft:behavior.play_dead": {"random_damage_range": "1.26.10"},
    # --- estritos desde 1.26.40 ---
    "minecraft:behavior.beg": {"look_time": "1.26.40"},
    "minecraft:behavior.float_wander": {"float_duration": "1.26.40"},
    "minecraft:behavior.ranged_attack": {"attack_interval": "1.26.40"},
}

# Versao em que cada componente deixou de ser parseado pelo cliente.
REMOVED_COMPONENT_SINCE = {
    "minecraft:pushable": "1.26.10",
}


def version_tuple(text):
    """'1.26.50' -> (1, 26, 50); tolera sufixos como '1.26.50-beta'."""
    out = []
    for part in str(text).split(".")[:3]:
        digits = ""
        for ch in part:
            if ch.isdigit():
                digits += ch
            else:
                break
        out.append(int(digits) if digits else 0)
    while len(out) < 3:
        out.append(0)
    return tuple(out)


def version_at_least(fv, minimum):
    return version_tuple(fv) >= version_tuple(minimum)


# Campos renomeados/removidos dentro de componentes (nao o componente inteiro).
RENAMED_COMPONENT_FIELDS = {
    "minecraft:behavior.look_at_player": {"min_look_time": "look_time.min", "max_look_time": "look_time.max"},
    "minecraft:behavior.look_at_entity": {"min_look_time": "look_time.min", "max_look_time": "look_time.max"},
    "minecraft:behavior.look_at_target": {"min_look_time": "look_time.min", "max_look_time": "look_time.max"},
    "minecraft:behavior.ranged_attack": {"attack_interval_min": "attack_interval.min", "attack_interval_max": "attack_interval.max"},
    "minecraft:buoyant": {"simulate_waves": "movement_type"},
    "minecraft:apply_knockback_rules": {"scale_previous_velocity": "slowdown_scale"},
}


# Categorias do inventario criativo (content/forms/block/menu_category.form.json).
MENU_CATEGORIES = frozenset({"construction", "equipment", "items", "nature", "none"})


# Componentes de ITEM cujo valor o cliente exige como OBJETO.  Um escalar aqui
# faz o arquivo inteiro falhar ao parsear e o icone desaparecer:
#   [Item][error]- Failed to parse field ' -> components ->
#                  minecraft:fire_resistant: expected an object'
#   [Item][error]-Missing icon for data-driven item 'paleo:egg_compy'.
# Forma correta confirmada no vanilla (behavior_pack/items/netherite_spear.json,
# samples 1.26.50.4):  "minecraft:fire_resistant": { "value": true }
#
# Deliberadamente NAO inclui minecraft:damage / minecraft:geometry /
# minecraft:map_color / minecraft:selection_box: o log real do cliente 1.26.52
# mostrou incubator/research_bench e os 13 itens sem ovo carregando sem erro
# usando as formas escalar/string/bool, ou seja, o cliente aceita as duas formas
# nesses componentes.  Sem evidencia de falha, nao viram regra.
OBJECT_ONLY_ITEM_COMPONENTS = {
    "minecraft:fire_resistant": ("value",),
}
