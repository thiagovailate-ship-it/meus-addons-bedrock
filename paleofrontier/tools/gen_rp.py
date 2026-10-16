#!/usr/bin/env python3
"""Generates the data files of the PALEOFRONTIER resource pack:

- textures/terrain_texture.json, textures/item_texture.json
- sounds.json and sounds/sound_definitions.json
- texts/*.lang and texts/languages.json (BP + RP)
- particles/*.particle.json
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bedrock_names as bn  # noqa: E402
import content_model as cm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(ROOT, "resource_pack")
BP = os.path.join(ROOT, "behavior_pack")


def write(rel, data, root=RP):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        if isinstance(data, str):
            fh.write(data)
        else:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    return path


# ---------------------------------------------------------------------------
# Terrain / item atlases
# ---------------------------------------------------------------------------
def gen_atlases():
    terrain = {
        "resource_pack_name": "paleofrontier",
        "texture_name": "atlas.terrain",
        "padding": 8,
        "num_mip_levels": 4,
        "texture_data": {},
    }
    block_textures = []
    for b in cm.DEPOSIT_BLOCKS:
        block_textures.append((b["texture"], f"textures/blocks/{b['texture']}"))
    block_textures += [
        ("paleo_research_bench_side", "textures/blocks/paleo_research_bench_side"),
        ("paleo_research_bench_top", "textures/blocks/paleo_research_bench_top"),
        ("paleo_research_bench_front", "textures/blocks/paleo_research_bench_front"),
        ("paleo_incubator_side", "textures/blocks/paleo_incubator_side"),
        ("paleo_incubator_top", "textures/blocks/paleo_incubator_top"),
    ]
    block_textures += [(f"paleo_incubator_chamber_{i}", f"textures/blocks/paleo_incubator_chamber_{i}")
                       for i in range(5)]
    for name, path in block_textures:
        terrain["texture_data"][name] = {"textures": [path]}
    write("textures/terrain_texture.json", terrain)

    item = {
        "resource_pack_name": "paleofrontier",
        "texture_name": "atlas.items",
        "texture_data": {},
    }
    for it in cm.ALL_ITEMS:
        item["texture_data"][f"paleo_{it['id']}"] = {
            "textures": [f"textures/items/paleo_{it['id']}"]
        }
    for sp in cm.SPECIES:
        item["texture_data"][f"paleo_spawn_egg_{sp['entity']}"] = {
            "textures": [f"textures/items/paleo_spawn_egg_{sp['entity']}"]
        }
    write("textures/item_texture.json", item)
    return 2


# ---------------------------------------------------------------------------
# Sounds
# ---------------------------------------------------------------------------
def checked_sound_event(key, allowed):
    """Resolve um nome de evento do content_model e exige que o cliente o aceite.

    O cliente rejeita eventos fora da enum LevelSoundEvent (ex.: 'power_on' em
    vez de 'power.on'), entao falhar aqui e melhor que falhar no jogo.
    """
    out = bn.sound_event_key(key)
    if out not in allowed:
        raise SystemExit(
            f"[gen_rp] evento de som desconhecido: {key!r} -> {out!r}\n"
            f"         nomes validos (derivados dos samples vanilla): {sorted(allowed)}"
        )
    return out


def gen_sounds_json():
    data = {
        "block_sounds": {},
        "entity_sounds": {"defaults": {}, "entities": {}},
        "individual_event_sounds": {"events": {}},
        "individual_named_sounds": {"events": {}},
        "interactive_sounds": {"entities": {}},
    }
    for name, group in cm.BLOCK_SOUND_GROUPS.items():
        events = {}
        for key, val in group["events"].items():
            out_key = checked_sound_event(key, allowed=bn.BLOCK_SOUND_EVENTS)
            if isinstance(val, dict):
                events[out_key] = val
            else:
                events[out_key] = {"sound": val}
        data["block_sounds"][name] = {
            "pitch": group.get("pitch", 1.0),
            "volume": group.get("volume", 1.0),
            "events": events,
        }
    for entity, spec in cm.ENTITY_SOUND_EVENTS.items():
        data["entity_sounds"]["entities"][f"{cm.NAMESPACE}:{entity}"] = {
            "volume": spec["volume"],
            "pitch": spec["pitch"],
            "events": {
                checked_sound_event(k, allowed=bn.ENTITY_SOUND_EVENTS): v
                for k, v in spec["events"].items()
            },
        }
    write("sounds.json", data)

    defs = {"format_version": cm.FORMAT_SOUND_DEFINITIONS, "sound_definitions": {}}
    for s in cm.SOUND_DEFS:
        defs["sound_definitions"][s["id"]] = {
            "category": s["category"],
            "sounds": [
                {
                    "name": f"sounds/{s['id'].replace('.', '/')}/{f}",
                    "volume": s["volume"],
                    "pitch": list(s["pitch"]),
                    "load_on_low_memory": True,
                    "stream": False,
                }
                for f in s["files"]
            ],
        }
    write("sounds/sound_definitions.json", defs)
    return 2


# ---------------------------------------------------------------------------
# Particles
# ---------------------------------------------------------------------------
def gen_particles():
    out = []
    dust = {
        "format_version": "1.10.0",
        "particle_effect": {
            "description": {
                "identifier": f"{cm.NAMESPACE}:excavation_dust",
                "basic_render_parameters": {
                    "material": "particles_alpha",
                    "texture": "textures/particle/particles",
                },
            },
            "components": {
                "minecraft:emitter_rate_instant": {"num_particles": 14},
                "minecraft:emitter_lifetime_once": {"active_time": 0.25},
                "minecraft:emitter_shape_sphere": {
                    "radius": 0.35,
                    "direction": "outwards",
                },
                "minecraft:particle_lifetime_expression": {
                    "max_lifetime": "0.5 + Math.random(0, 0.4)"
                },
                "minecraft:particle_initial_speed": 1.6,
                "minecraft:particle_motion_dynamic": {
                    "minecraft:particle_drag_coefficient": 2.4,
                    "minecraft:particle_gravity": -0.35,
                },
                "minecraft:particle_appearance_billboard": {
                    "size": [0.10, 0.10],
                    "facing_camera_mode": "lookat_xyz",
                    "uv": {"texture_width": 128, "texture_height": 128,
                           "flipbook": {"base_UV": [64, 64], "size_UV": [8, 8],
                                        "step_UV": [-8, 0], "frames": 8,
                                        "max_frame": 8, "stretch_to_lifetime": True}},
                },
                "minecraft:particle_appearance_tinting": {
                    "color": [0.62, 0.55, 0.44, 1.0]
                },
            },
        },
    }
    out.append(write("particles/excavation_dust.particle.json", dust))

    spark = {
        "format_version": "1.10.0",
        "particle_effect": {
            "description": {
                "identifier": f"{cm.NAMESPACE}:research_spark",
                "basic_render_parameters": {
                    "material": "particles_add",
                    "texture": "textures/particle/particles",
                },
            },
            "components": {
                "minecraft:emitter_rate_instant": {"num_particles": 20},
                "minecraft:emitter_lifetime_once": {"active_time": 0.3},
                "minecraft:emitter_shape_sphere": {"radius": 0.25, "direction": "outwards"},
                "minecraft:particle_lifetime_expression": {
                    "max_lifetime": "0.45 + Math.random(0, 0.35)"
                },
                "minecraft:particle_initial_speed": 2.2,
                "minecraft:particle_motion_dynamic": {
                    "minecraft:particle_drag_coefficient": 3.0,
                    "minecraft:particle_gravity": 0.15,
                },
                "minecraft:particle_appearance_billboard": {
                    "size": ["0.08 + variable.particle_age * 0.05",
                             "0.08 + variable.particle_age * 0.05"],
                    "facing_camera_mode": "lookat_xyz",
                    "uv": {"texture_width": 128, "texture_height": 128,
                           "uv": [0, 0], "uv_size": [8, 8]},
                },
                "minecraft:particle_appearance_tinting": {
                    "color": ["Math.clamp(1.0 - variable.particle_age * 1.6, 0, 1) * 0.45",
                              "Math.clamp(1.0 - variable.particle_age * 1.2, 0, 1) * 0.95",
                              "Math.clamp(1.0 - variable.particle_age * 0.8, 0, 1) * 0.9",
                              "Math.clamp(1.4 - variable.particle_age * 2.0, 0, 1)"],
                },
            },
        },
    }
    out.append(write("particles/research_spark.particle.json", spark))

    pulse = {
        "format_version": "1.10.0",
        "particle_effect": {
            "description": {
                "identifier": f"{cm.NAMESPACE}:scan_pulse",
                "basic_render_parameters": {
                    "material": "particles_add",
                    "texture": "textures/particle/particles",
                },
            },
            "components": {
                "minecraft:emitter_rate_instant": {"num_particles": 10},
                "minecraft:emitter_lifetime_once": {"active_time": 0.2},
                "minecraft:emitter_shape_sphere": {"radius": 0.15, "direction": "outwards"},
                "minecraft:particle_lifetime_expression": {
                    "max_lifetime": "0.7 + Math.random(0, 0.3)"
                },
                "minecraft:particle_initial_speed": 0.6,
                "minecraft:particle_motion_dynamic": {
                    "minecraft:particle_drag_coefficient": 0.4,
                    "minecraft:particle_gravity": 0.0,
                },
                "minecraft:particle_appearance_billboard": {
                    "size": ["0.12 + variable.particle_age * 0.9",
                             "0.12 + variable.particle_age * 0.9"],
                    "facing_camera_mode": "lookat_xyz",
                    "uv": {"texture_width": 128, "texture_height": 128,
                           "uv": [8, 8], "uv_size": [8, 8]},
                },
                "minecraft:particle_appearance_tinting": {
                    "color": [0.35, 0.95, 0.85,
                              "Math.clamp(1.0 - variable.particle_age * 1.2, 0, 1)"],
                },
            },
        },
    }
    out.append(write("particles/scan_pulse.particle.json", pulse))

    glow = {
        "format_version": "1.10.0",
        "particle_effect": {
            "description": {
                "identifier": f"{cm.NAMESPACE}:incubation_glow",
                "basic_render_parameters": {
                    "material": "particles_add",
                    "texture": "textures/particle/particles",
                },
            },
            "components": {
                "minecraft:emitter_rate_steady": {
                    "spawn_rate": 12,
                    "max_particles": 40,
                },
                "minecraft:emitter_lifetime_looping": {"active_time": 2.0},
                "minecraft:emitter_shape_box": {
                    "offset": [0, 0.6, 0],
                    "half_dimensions": [0.4, 0.1, 0.4],
                    "direction": "outwards",
                },
                "minecraft:particle_lifetime_expression": {
                    "max_lifetime": "0.9 + Math.random(0, 0.6)"
                },
                "minecraft:particle_initial_speed": 0.25,
                "minecraft:particle_motion_dynamic": {
                    "minecraft:particle_drag_coefficient": 0.6,
                    "minecraft:particle_gravity": -0.12,
                },
                "minecraft:particle_appearance_billboard": {
                    "size": ["0.06 + variable.particle_age * 0.10",
                             "0.06 + variable.particle_age * 0.10"],
                    "facing_camera_mode": "lookat_xyz",
                    "uv": {"texture_width": 128, "texture_height": 128,
                           "uv": [16, 16], "uv_size": [8, 8]},
                },
                "minecraft:particle_appearance_tinting": {
                    "color": [0.30, 0.90, 0.75,
                              "Math.clamp(1.0 - variable.particle_age * 0.9, 0, 1) * 0.8"],
                },
            },
        },
    }
    out.append(write("particles/incubation_glow.particle.json", glow))
    return len(out)


# ---------------------------------------------------------------------------
# Translations
# ---------------------------------------------------------------------------
UI_TEXTS = [
    # --- research station ---
    ("paleo.ui.lab.title", "Research Station", "Estacao de Pesquisa"),
    ("paleo.ui.lab.body",
     "Choose an operation. The station consumes the listed materials from your inventory.",
     "Escolha uma operacao. A estacao consome os materiais listados do seu inventario."),
    ("paleo.ui.lab.examine", "Examine specimen", "Examinar especime"),
    ("paleo.ui.lab.examine_one", "Examine %s (carrying %d)", "Examinar %s (carregando %d)"),
    ("paleo.ui.lab.examine_again", "Re-read dossier: %s (carrying %d)", "Reler ficha: %s (carregando %d)"),
    ("paleo.ui.lab.process", "Process materials", "Processar materiais"),
    ("paleo.ui.lab.process_ok", "Run: %s", "Executar: %s"),
    ("paleo.ui.lab.process_lack", "Run: %s (missing materials)", "Executar: %s (materiais faltando)"),
    ("paleo.ui.lab.reconstruct", "Reconstruct viable egg", "Reconstruir ovo vital"),
    ("paleo.ui.lab.reconstruct_ok", "Reconstruct %s", "Reconstruir %s"),
    ("paleo.ui.lab.reconstruct_lack", "Reconstruct %s (missing materials)", "Reconstruir %s (materiais faltando)"),
    ("paleo.ui.lab.journal", "Open field journal", "Abrir caderno de campo"),
    ("paleo.ui.lab.projects", "Projects and requirements", "Projetos e requisitos"),
    ("paleo.ui.lab.projects_body",
     "Every species the archive can rebuild, and how close you are to each one.",
     "Cada especie que o arquivo pode reconstruir, e o quao perto voce esta de cada uma."),
    ("paleo.ui.lab.project_open", "%s - identified (%s)", "%s - identificada (%s)"),
    ("paleo.ui.lab.project_locked", "%s - NOT identified (%s)", "%s - NAO identificada (%s)"),
    ("paleo.ui.lab.exit", "Close", "Fechar"),
    ("paleo.ui.lab.pick", "Choose a specimen you carry", "Escolha um especime que voce carrega"),
    ("paleo.ui.lab.pick_process", "Choose a conversion", "Escolha uma conversao"),
    ("paleo.ui.lab.pick_species", "Choose a species", "Escolha uma especie"),
    ("paleo.ui.lab.cancel", "Back", "Voltar"),
    ("paleo.ui.lab.missing", "Missing materials", "Materiais insuficientes"),
    ("paleo.ui.lab.done", "Operation complete", "Operacao concluida"),
    ("paleo.ui.lab.identified", "Species identified: %s", "Especie identificada: %s"),
    ("paleo.ui.lab.no_specimen",
     "You carry no intact specimen. Use the Paleontology Brush on a fossil deposit.",
     "Voce nao carrega nenhum especime integro. Use o Pincel Paleontologico em um deposito fossil."),
    ("paleo.ui.lab.none_identified",
     "No species identified yet. Examine a specimen first.",
     "Nenhuma especie identificada ainda. Examine um especime primeiro."),
    ("paleo.ui.lab.discovered", "Specimen recovered", "Especime recuperado"),
    ("paleo.ui.lab.discovered.sub", "Check your field journal", "Confira seu caderno de campo"),
    ("paleo.ui.lab.egg_ready", "Viable egg synthesised", "Ovo vital sintetizado"),
    ("paleo.ui.lab.egg_ready.sub", "Place it in an incubator to develop the %s", "Coloque-o em uma incubadora para desenvolver o %s"),
    # --- journal ---
    ("paleo.ui.journal.title", "Field Journal", "Caderno de Campo"),
    ("paleo.ui.journal.body",
     "Your personal record of everything the archive has revealed.",
     "Seu registro pessoal de tudo o que o arquivo revelou."),
    ("paleo.ui.journal.species", "Species dossier", "Fichas de especies"),
    ("paleo.ui.journal.species_entry", "%s - specimens found: %d", "%s - especimes encontrados: %d"),
    ("paleo.ui.journal.objectives", "Current objectives", "Objetivos atuais"),
    ("paleo.ui.journal.objective_n", "%d. %s", "%d. %s"),
    ("paleo.ui.journal.creatures", "Creatures raised", "Criaturas criadas"),
    ("paleo.ui.journal.creature_line", "%s - hatched %d, bonded %d, studied %d", "%s - eclodidos %d, vinculados %d, estudados %d"),
    ("paleo.ui.journal.stats", "Expedition statistics", "Estatisticas da expedicao"),
    ("paleo.ui.journal.study", "Study a creature nearby", "Estudar uma criatura proxima"),
    ("paleo.ui.journal.none", "Nothing recorded yet.", "Nada registrado ainda."),
    ("paleo.ui.journal.identified", "Identified", "Identificada"),
    ("paleo.ui.journal.unknown", "Not identified", "Nao identificada"),
    ("paleo.ui.journal.complete", "Every objective is complete. The archive is yours.", "Todos os objetivos completos. O arquivo e seu."),
    ("paleo.ui.journal.raised", "Raised", "Criadas"),
    # --- objectives ---
    ("paleo.ui.obj.gear",
     "Craft a Paleontology Brush or an Excavation Shovel from bone shards.",
     "Crie um Pincel Paleontologico ou uma Pa de Escavacao com lascas osseas."),
    ("paleo.ui.obj.specimen",
     "Recover an intact specimen by brushing a fossil deposit.",
     "Recupere um especime integro escovando um deposito fossil."),
    ("paleo.ui.obj.identify",
     "Identify your first species at a Research Station.",
     "Identifique sua primeira especie em uma Estacao de Pesquisa."),
    ("paleo.ui.obj.egg",
     "Reconstruct a viable egg at the Research Station.",
     "Reconstrua um ovo vital na Estacao de Pesquisa."),
    ("paleo.ui.obj.hatch",
     "Develop an egg in an incubator until it hatches.",
     "Desenvolva um ovo em uma incubadora ate eclodir."),
    ("paleo.ui.obj.study",
     "Study a living creature with the field case.",
     "Estude uma criatura viva com a maleta de campo."),
    ("paleo.ui.obj.all",
     "Identify every species in the archive (%d of %d).",
     "Identifique todas as especies do arquivo (%d de %d)."),
    # --- dossier ---
    ("paleo.ui.dossier.name", "%s (%s)", "%s (%s)"),
    ("paleo.ui.dossier.status", "Status: %s", "Status: %s"),
    ("paleo.ui.dossier.rarity", "Rarity: %s", "Raridade: %s"),
    ("paleo.ui.dossier.era", "Stratum: %s", "Estrato: %s"),
    ("paleo.ui.dossier.diet", "Diet: %s", "Dieta: %s"),
    ("paleo.ui.dossier.size", "Size: %s", "Porte: %s"),
    ("paleo.ui.dossier.note", "Behaviour: %s", "Comportamento: %s"),
    ("paleo.ui.dossier.incubation", "Incubation: about %d min", "Incubacao: cerca de %d min"),
    ("paleo.ui.dossier.cost", "Egg needs %d matrix, %d specimen, %d gel, %d amber", "Ovo precisa de %d matriz, %d especime, %d gel, %d ambar"),
    ("paleo.ui.dossier.examine_cost", "Examination needs %d specimen, %d chips, %d shards, %d amber", "Exame precisa de %d especime, %d fragmentos, %d lascas, %d ambar"),
    ("paleo.ui.dossier.locked", "Bring an intact specimen to a Research Station to unlock this dossier.", "Traga um especime integro a uma Estacao de Pesquisa para liberar esta ficha."),
    ("paleo.ui.dossier.progress", "Found %d, hatched %d, studied %d, bonded %d", "Encontrados %d, eclodidos %d, estudados %d, vinculados %d"),
    # --- stats ---
    ("paleo.ui.stats.mined", "Deposits excavated: %d", "Depositos escavados: %d"),
    ("paleo.ui.stats.identified", "Species identified: %d of %d", "Especies identificadas: %d de %d"),
    ("paleo.ui.stats.hatched", "Creatures hatched (world): %d", "Criaturas eclodidas (mundo): %d"),
    ("paleo.ui.stats.studied", "Individuals studied (world): %d", "Individuos estudados (mundo): %d"),
    # --- incubator ---
    ("paleo.ui.incubator.title", "Incubator", "Incubadora"),
    ("paleo.ui.incubator.empty", "The chamber is empty.", "A camara esta vazia."),
    ("paleo.ui.incubator.insert", "Insert viable egg", "Inserir ovo vital"),
    ("paleo.ui.incubator.insert_one", "Develop %s (carrying %d)", "Desenvolver %s (carregando %d)"),
    ("paleo.ui.incubator.remove", "Withdraw egg (loses progress)", "Retirar ovo (perde o progresso)"),
    ("paleo.ui.incubator.removed", "Egg withdrawn.", "Ovo retirado."),
    ("paleo.ui.incubator.status_btn", "Detailed status", "Status detalhado"),
    ("paleo.ui.incubator.status", "Incubating %s - %d%% (stage %d/4)", "Incubando %s - %d%% (estagio %d/4)"),
    ("paleo.ui.incubator.ready", "%s is ready to hatch! (%d%%, stage %d/4)", "%s esta pronto para eclodir! (%d%%, estagio %d/4)"),
    ("paleo.ui.incubator.hatched", "A %s hatched!", "Um %s eclodiu!"),
    ("paleo.ui.incubator.warm", "Chamber is warm: incubation +25%.", "Camara aquecida: incubacao +25%."),
    ("paleo.ui.incubator.nolight", "The chamber is cold and dark - incubation runs at normal speed.", "A camara esta fria e escura - incubacao em velocidade normal."),
    ("paleo.ui.incubator.tip",
     "Incubation advances only while the chamber sits in a loaded area. Light level 10+ speeds it up by 25%.",
     "A incubacao avanca apenas com a camara em area carregada. Nivel de luz 10+ acelera em 25%."),
    ("paleo.ui.incubator.s_species", "Species: %s", "Especie: %s"),
    ("paleo.ui.incubator.s_progress", "Progress: %d%%", "Progresso: %d%%"),
    ("paleo.ui.incubator.s_elapsed", "Accumulated %d s of %d s required", "Acumulado %d s de %d s necessarios"),
    ("paleo.ui.incubator.s_heat", "Heat bonus: +%d%%", "Bonus de calor: +%d%%"),
    # --- scanner ---
    ("paleo.ui.scan.found", "Signal: %s, %d blocks to the %s (strength %d/5)", "Sinal: %s, %d blocos a %s (forca %d/5)"),
    ("paleo.ui.scan.none", "No fossil signal within range.", "Nenhum sinal fossil no alcance."),
    ("paleo.ui.scan.cooldown", "The scanner needs a moment to recharge.", "O scanner precisa de um momento para recarregar."),
    ("paleo.ui.scan.dir.n", "north", "norte"),
    ("paleo.ui.scan.dir.ne", "northeast", "nordeste"),
    ("paleo.ui.scan.dir.e", "east", "leste"),
    ("paleo.ui.scan.dir.se", "southeast", "sudeste"),
    ("paleo.ui.scan.dir.s", "south", "sul"),
    ("paleo.ui.scan.dir.sw", "southwest", "sudoeste"),
    ("paleo.ui.scan.dir.w", "west", "oeste"),
    ("paleo.ui.scan.dir.nw", "northwest", "noroeste"),
    ("paleo.ui.scan.dir.up", "above", "cima"),
    ("paleo.ui.scan.dir.down", "below", "baixo"),
    # --- misc ---
    ("paleo.ui.egg.hint", "This egg only develops inside an incubator.", "Este ovo so se desenvolve dentro de uma incubadora."),
    ("paleo.ui.study.done", "You recorded behavioural notes on the %s.", "Voce registrou notas de comportamento do %s."),
    ("paleo.ui.study.already", "You already studied this individual.", "Voce ja estudou este individuo."),
    ("paleo.ui.study.need", "Hold the field case to study a creature.", "Segure a maleta de campo para estudar uma criatura."),
    ("paleo.ui.study.none", "No archive creature close enough to study.", "Nenhuma criatura do arquivo perto o bastante para estudar."),
    ("paleo.ui.creatures.bonded", "The %s trusts you now.", "O %s agora confia em voce."),
    ("paleo.ui.tool.broken", "Your tool broke.", "Sua ferramenta quebrou."),
    ("paleo.ui.welcome",
     "The ground remembers. Brush fossil deposits, then bring specimens to a Research Station.",
     "O solo se lembra. Escove depositos fosseis e leve especimes a uma Estacao de Pesquisa."),
    # --- process names ---
    ("paleo.proc.refine_matrix", "Refine Genetic Matrix", "Refinar Matriz Genetica"),
    ("paleo.proc.catalyze_matrix", "Catalyse Matrix with Amber", "Catalisar Matriz com Ambar"),
    ("paleo.proc.synthesize_gel", "Synthesise Nutrient Gel", "Sintetizar Gel Nutritivo"),
    # --- rarity ---
    ("paleo.rarity.common", "common", "comum"),
    ("paleo.rarity.uncommon", "uncommon", "incomum"),
    ("paleo.rarity.rare", "rare", "raro"),
    ("paleo.rarity.epic", "epic", "epico"),
    ("paleo.rarity.legendary", "legendary", "lendario"),
]


def lang_content(lang):
    lines = [
        "## PALEOFRONTIER: Arquivo dos Gigantes",
        f"## language: {lang}",
        "",
    ]
    for b in cm.ALL_BLOCKS:
        if lang == "pt_BR":
            lines.append(f"tile.{cm.NAMESPACE}:{b['id']}.name={cm.pt_br(b['pt'])}")
        else:
            lines.append(f"tile.{cm.NAMESPACE}:{b['id']}.name={b['en']}")
    lines.append("")
    for it in cm.ALL_ITEMS:
        name = cm.pt_br(it["pt"]) if lang == "pt_BR" else it["en"]
        lines.append(f"item.{cm.NAMESPACE}:{it['id']}={name}")
        lines.append(f"item.{cm.NAMESPACE}:{it['id']}.name={name}")
        lore = it.get("lore_pt" if lang == "pt_BR" else "lore_en")
        if lore:
            lines.append(f"item.{cm.NAMESPACE}:{it['id']}.lore={cm.pt_br(lore) if lang == 'pt_BR' else lore}")
    lines.append("")
    for sp in cm.SPECIES:
        if lang == "pt_BR":
            lines.append(f"entity.{cm.NAMESPACE}:{sp['entity']}.name={cm.pt_br(sp['pt'])}")
            lines.append(f"item.spawn_egg.entity.{cm.NAMESPACE}:{sp['entity']}.name=Ovo gerador de {cm.pt_br(sp['pt'])}")
        else:
            lines.append(f"entity.{cm.NAMESPACE}:{sp['entity']}.name={sp['en']}")
            lines.append(f"item.spawn_egg.entity.{cm.NAMESPACE}:{sp['entity']}.name=Spawn {sp['en']}")
    lines.append("")
    for key, en, pt in UI_TEXTS:
        lines.append(f"{key}={cm.pt_br(pt) if lang == 'pt_BR' else en}")
    lines.append("")
    return "\n".join(lines)


def gen_langs():
    out = []
    for root in (RP, BP):
        out.append(write("texts/en_US.lang", lang_content("en_US"), root=root))
        out.append(write("texts/pt_BR.lang", lang_content("pt_BR"), root=root))
        out.append(write("texts/languages.json", json.dumps(["en_US", "pt_BR"], indent=1) + "\n", root=root))
    return len(out)


def main():
    n = 0
    n += gen_atlases()
    n += gen_sounds_json()
    n += gen_particles()
    n += gen_langs()
    print(f"[gen_rp] wrote {n} files")


if __name__ == "__main__":
    main()
