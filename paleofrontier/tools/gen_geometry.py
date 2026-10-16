#!/usr/bin/env python3
"""Generates entity geometry, animations, animation controllers, render
controllers and client entity definitions for the four PALEOFRONTIER species.

Everything is derived from MODELS below so that an animation never references a
bone that does not exist in that species' geometry (that would raise a content
error in game).
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

# ---------------------------------------------------------------------------
# Model definitions.  Bedrock entity models face -Z, Y is up, the origin is the
# block the entity stands on.  A cube is (x, y, z, w, h, l) with x/y/z the MIN
# corner.  "mirror" flips a bone definition across the X axis.
# ---------------------------------------------------------------------------


def mirror_cubes(cubes):
    out = []
    for (x, y, z, w, h, l, uv_key) in cubes:
        out.append((-x - w, y, z, w, h, l, uv_key))
    return out


def mirror_bone(bone):
    out = dict(bone)
    pivot = bone["pivot"]
    out["pivot"] = [-pivot[0], pivot[1], pivot[2]]
    out["cubes"] = mirror_cubes(bone["cubes"])
    return out


# Each bone: name, parent, pivot, cubes, optional rotation (bind pose)
MODELS = {
    "compsognathus": dict(
        texture=(64, 32),
        visible_bounds=(2.0, 1.25, [0, 0.35, 0]),
        baby_head_scale=1.35,
        gait=dict(stride=44.0, swing=62.0, tail_sway=26.0, bob=0.55),
        bones=[
            dict(name="body", parent="root", pivot=[0, 6, 1], cubes=[
                (-2, 4, -2, 4, 4, 6, "torso"),
                (-2, 4, 3, 4, 4, 3, "torso"),
            ]),
            dict(name="neck", parent="body", pivot=[0, 6, -2], cubes=[
                (-1, 5, -4, 2, 3, 3, "neck"),
            ]),
            dict(name="head", parent="neck", pivot=[0, 6, -4], head=True, cubes=[
                (-2, 5, -7, 4, 3, 3, "head"),
                (-1, 5, -9, 2, 2, 2, "head"),
                (-2, 7, -7, 4, 1, 2, "head"),
            ]),
            dict(name="jaw", parent="head", pivot=[0, 5, -4], jaw=True, cubes=[
                (-1, 4, -9, 2, 1, 5, "jaw"),
            ]),
            dict(name="tail_1", parent="body", pivot=[0, 6, 6], cubes=[
                (-1, 5, 6, 2, 2, 3, "tail"),
            ]),
            dict(name="tail_2", parent="tail_1", pivot=[0, 6, 9], cubes=[
                (-1, 5, 9, 2, 2, 3, "tail"),
            ]),
            dict(name="tail_3", parent="tail_2", pivot=[0, 6, 12], cubes=[
                (0, 5, 12, 1, 1, 4, "tail"),
            ]),
            dict(name="leg_left", parent="body", pivot=[-2, 4, 3], cubes=[
                (-3, 2, 2, 2, 3, 3, "leg"),
                (-3, 0, 3, 1, 2, 1, "leg"),
                (-3, 0, 1, 2, 1, 3, "foot"),
            ]),
            dict(name="arm_left", parent="body", pivot=[-2, 5, 0], cubes=[
                (-3, 3, -1, 1, 2, 1, "arm"),
                (-3, 2, -2, 1, 1, 1, "arm"),
            ]),
        ],
        mirrored=["leg_left", "arm_left"],
        extra_bones=[("root", None, [0, 0, 0])],
    ),
    "velociraptor": dict(
        texture=(128, 64),
        visible_bounds=(3.0, 2.25, [0, 0.9, 0]),
        baby_head_scale=1.3,
        gait=dict(stride=38.17, swing=76.0, tail_sway=22.0, bob=0.9),
        bones=[
            dict(name="body", parent="root", pivot=[0, 15, 2], cubes=[
                (-4, 12, -4, 8, 8, 13, "torso"),
                (-3, 12, 8, 6, 8, 6, "torso"),
            ]),
            dict(name="neck", parent="body", pivot=[0, 18, -4], cubes=[
                (-2, 16, -9, 4, 5, 6, "neck"),
            ]),
            dict(name="head", parent="neck", pivot=[0, 19, -9], head=True, cubes=[
                (-3, 17, -15, 6, 5, 7, "head"),
                (-2, 17, -19, 4, 3, 4, "head"),
                (-3, 21, -14, 6, 1, 5, "crest"),
            ]),
            dict(name="jaw", parent="head", pivot=[0, 17, -9], jaw=True, cubes=[
                (-2, 15, -19, 4, 2, 10, "jaw"),
            ]),
            dict(name="tail_1", parent="body", pivot=[0, 16, 14], cubes=[
                (-2, 14, 14, 4, 4, 7, "tail"),
            ]),
            dict(name="tail_2", parent="tail_1", pivot=[0, 15, 21], cubes=[
                (-1, 13, 21, 3, 3, 7, "tail"),
            ]),
            dict(name="tail_3", parent="tail_2", pivot=[0, 14, 28], cubes=[
                (-1, 12, 28, 2, 2, 8, "tail"),
            ]),
            dict(name="leg_left", parent="body", pivot=[-4, 12, 8], cubes=[
                (-6, 7, 5, 3, 8, 6, "leg"),
                (-6, 3, 7, 2, 6, 2, "leg"),
                (-6, 0, 4, 3, 3, 6, "foot"),
                (-6, 0, 2, 1, 2, 2, "claw"),
            ]),
            dict(name="arm_left", parent="body", pivot=[-4, 17, 0], cubes=[
                (-6, 14, -2, 2, 4, 2, "arm"),
                (-6, 12, -3, 2, 3, 2, "arm"),
                (-6, 11, -4, 1, 2, 1, "claw"),
            ]),
        ],
        mirrored=["leg_left", "arm_left"],
        extra_bones=[("root", None, [0, 0, 0])],
    ),
    "triceratops": dict(
        texture=(128, 128),
        visible_bounds=(5.0, 3.0, [0, 1.2, 0]),
        baby_head_scale=1.25,
        gait=dict(stride=38.17, swing=52.0, tail_sway=14.0, bob=1.1),
        quadruped=True,
        bones=[
            dict(name="body", parent="root", pivot=[0, 21, 0], cubes=[
                (-8, 15, -10, 16, 13, 22, "torso"),
                (-7, 15, 10, 14, 12, 8, "torso"),
            ]),
            dict(name="neck", parent="body", pivot=[0, 20, -10], cubes=[
                (-6, 15, -16, 12, 10, 7, "neck"),
            ]),
            dict(name="head", parent="neck", pivot=[0, 19, -16], head=True, cubes=[
                (-8, 19, -18, 16, 11, 3, "frill"),
                (-6, 15, -24, 12, 8, 8, "head"),
                (-3, 15, -27, 6, 5, 4, "beak"),
                (-1, 22, -24, 2, 5, 2, "horn"),
                (-5, 22, -21, 2, 7, 2, "horn"),
            ]),
            dict(name="jaw", parent="head", pivot=[0, 15, -16], jaw=True, cubes=[
                (-4, 12, -26, 8, 3, 11, "jaw"),
            ]),
            dict(name="tail_1", parent="body", pivot=[0, 21, 18], cubes=[
                (-4, 17, 18, 8, 8, 8, "tail"),
            ]),
            dict(name="tail_2", parent="tail_1", pivot=[0, 20, 26], cubes=[
                (-3, 17, 26, 6, 6, 7, "tail"),
            ]),
            dict(name="tail_3", parent="tail_2", pivot=[0, 19, 33], cubes=[
                (-2, 17, 33, 4, 4, 6, "tail"),
            ]),
            dict(name="leg_front_left", parent="body", pivot=[-7, 16, -6], cubes=[
                (-9, 7, -8, 4, 9, 6, "leg"),
                (-9, 0, -8, 4, 8, 5, "leg"),
            ]),
            dict(name="leg_back_left", parent="body", pivot=[-7, 17, 12], leg_left=True, cubes=[
                (-10, 7, 9, 5, 10, 8, "leg"),
                (-9, 0, 10, 4, 8, 5, "leg"),
            ]),
        ],
        mirrored=["leg_front_left", "leg_back_left"],
        mirror_names={"leg_front_left": "leg_front_right", "leg_back_left": "leg_back_right"},
        extra_bones=[("root", None, [0, 0, 0])],
    ),
    "tyrannosaurus": dict(
        texture=(256, 256),
        visible_bounds=(9.0, 6.0, [0, 2.4, 0]),
        baby_head_scale=1.3,
        gait=dict(stride=32.0, swing=48.0, tail_sway=12.0, bob=1.6),
        bones=[
            dict(name="body", parent="root", pivot=[0, 46, 0], cubes=[
                (-11, 36, -14, 22, 20, 30, "torso"),
                (-9, 36, 14, 18, 18, 12, "torso"),
            ]),
            dict(name="neck", parent="body", pivot=[0, 54, -14], cubes=[
                (-8, 48, -24, 16, 14, 12, "neck"),
            ]),
            dict(name="head", parent="neck", pivot=[0, 58, -24], head=True, cubes=[
                (-9, 50, -44, 18, 16, 22, "head"),
                (-7, 50, -56, 14, 10, 13, "head"),
                (-10, 64, -40, 4, 4, 12, "crest"),
            ]),
            dict(name="jaw", parent="head", pivot=[0, 52, -24], jaw=True, cubes=[
                (-7, 44, -56, 14, 7, 32, "jaw"),
            ]),
            dict(name="tail_1", parent="body", pivot=[0, 48, 26], cubes=[
                (-8, 40, 26, 16, 16, 18, "tail"),
            ]),
            dict(name="tail_2", parent="tail_1", pivot=[0, 47, 44], cubes=[
                (-6, 41, 44, 12, 12, 16, "tail"),
            ]),
            dict(name="tail_3", parent="tail_2", pivot=[0, 46, 60], cubes=[
                (-4, 42, 60, 8, 8, 14, "tail"),
            ]),
            dict(name="tail_4", parent="tail_3", pivot=[0, 45, 74], cubes=[
                (-2, 43, 74, 5, 5, 12, "tail"),
            ]),
            dict(name="leg_left", parent="body", pivot=[-9, 36, 14], cubes=[
                (-14, 20, 8, 9, 20, 14, "leg"),
                (-13, 8, 10, 7, 14, 7, "leg"),
                (-12, 4, 10, 5, 6, 5, "leg"),
                (-13, 0, 4, 9, 4, 14, "foot"),
                (-13, 0, 1, 3, 3, 3, "claw"),
                (-6, 0, 1, 3, 3, 3, "claw"),
            ]),
            dict(name="arm_left", parent="body", pivot=[-11, 50, -8], cubes=[
                (-14, 44, -10, 4, 8, 4, "arm"),
                (-14, 38, -12, 3, 7, 3, "arm"),
                (-14, 36, -14, 3, 3, 3, "claw"),
            ]),
        ],
        mirrored=["leg_left", "arm_left"],
        extra_bones=[("root", None, [0, 0, 0])],
    ),
}


# ---------------------------------------------------------------------------
# UV packing: give every cube face group its own non-overlapping rectangle so
# the generated texture atlas never has two faces fighting for the same pixels.
# ---------------------------------------------------------------------------
class UvPacker:
    """Shelf packer. Cubes are packed tallest-first for good atlas usage."""

    def __init__(self, width, height, pad=1):
        self.width = width
        self.height = height
        self.pad = pad
        self.assignments = {}

    def pack(self, requests):
        """requests: list of (key, w, h). Fills self.assignments[key] = (u, v)."""
        ordered = sorted(requests, key=lambda r: (-r[2], -r[1], r[0]))
        cursor_x = 0
        cursor_y = 0
        row_h = 0
        for key, w, h in ordered:
            if cursor_x + w > self.width:
                cursor_x = 0
                cursor_y += row_h + self.pad
                row_h = 0
            if cursor_y + h > self.height:
                raise RuntimeError(
                    f"texture atlas overflow placing {key} ({w}x{h}) in "
                    f"{self.width}x{self.height}"
                )
            self.assignments[key] = (cursor_x, cursor_y)
            cursor_x += w + self.pad
            row_h = max(row_h, h)
        return self.assignments


def box_uv_size(w, h, l):
    """Standard Bedrock box UV footprint for a cube of size w x h x l."""
    return (2 * (w + l), h + l)


def ordered_bones(spec):
    """Bones in parent-first order, including the mirrored counterparts."""
    order = []
    for bone in spec["bones"]:
        order.append(bone)
        if bone["name"] in spec["mirrored"]:
            mb = mirror_bone(bone)
            mb["name"] = spec.get("mirror_names", {}).get(
                bone["name"], bone["name"].replace("_left", "_right")
            )
            order.append(mb)
    return order


def world_pivots(spec):
    """Authored pivots are absolute model-space coordinates; Bedrock stores a
    bone pivot relative to its parent's pivot, so convert the chain here."""
    order = ordered_bones(spec)
    world = {}
    for bone in order:
        parent = bone["parent"]
        base = world.get(parent, [0.0, 0.0, 0.0])
        world[bone["name"]] = [
            base[0] + bone["pivot"][0],
            base[1] + bone["pivot"][1],
            base[2] + bone["pivot"][2],
        ]
    return world


def cube_key(bone_name, cube):
    x, y, z = cube[0], cube[1], cube[2]
    return f"{bone_name}|{x},{y},{z}"


def build_geometry(entity, baby=False):
    """Returns (geometry_dict, uv_map).

    uv_map lists {bone, kind, origin, size, uv} for every cube - exactly what the
    texture painter needs so each cube face lands on its own pixels.
    """
    spec = MODELS[entity]
    tex_w, tex_h = spec["texture"]
    order = ordered_bones(spec)

    requests = []
    for bone in order:
        for cube in bone["cubes"]:
            w, h, l = cube[3], cube[4], cube[5]
            uw, uh = box_uv_size(w, h, l)
            requests.append((cube_key(bone["name"], cube), uw, uh))

    packer = UvPacker(tex_w, tex_h)
    packed = packer.pack(requests)

    uv_map = []
    bones = []
    world = world_pivots(spec)
    for name, parent, pivot in spec["extra_bones"]:
        bones.append({"name": name, "pivot": list(pivot)})

    head_scale = spec["baby_head_scale"] if baby else 1.0

    for bone in order:
        wp = world[bone["name"]]
        pp = world.get(bone["parent"], [0.0, 0.0, 0.0])
        out = {
            "name": bone["name"],
            "parent": bone["parent"],
            "pivot": [wp[0] - pp[0], wp[1] - pp[1], wp[2] - pp[2]],
        }
        if bone.get("rotation"):
            out["rotation"] = bone["rotation"]
        cubes = []
        for (x, y, z, w, h, l, uv_key) in bone["cubes"]:
            uv = packed[cube_key(bone["name"], (x, y, z, w, h, l, uv_key))]
            rel = [x - wp[0], y - wp[1], z - wp[2]]
            cubes.append({
                "origin": rel,
                "size": [w, h, l],
                "uv": [uv[0], uv[1]],
            })
            uv_map.append({
                "bone": bone["name"],
                "kind": uv_key,
                # absolute origin, for the texture painter and the previewer
                "origin": [x, y, z],
                "size": [w, h, l],
                "uv": [uv[0], uv[1]],
            })
        if cubes:
            out["cubes"] = cubes
        bones.append(out)

    if baby:
        # Babies keep every bone name (so all animations still resolve) but get an
        # enlarged head/jaw and a slightly shorter body, like vanilla baby mobs.
        for bone in bones:
            if bone["name"] in ("head", "jaw"):
                for cube in bone.get("cubes", []):
                    ox, oy, oz = cube["origin"]
                    w, h, l = cube["size"]
                    nw = max(1, round(w * head_scale))
                    nh = max(1, round(h * head_scale))
                    nl = max(1, round(l * head_scale))
                    cube["origin"] = [
                        round(ox - (nw - w) / 2),
                        round(oy - (nh - h) / 2),
                        round(oz - (nl - l)),
                    ]
                    cube["size"] = [nw, nh, nl]
            elif bone["name"] in ("leg_front_left", "leg_front_right",
                                  "leg_back_left", "leg_back_right",
                                  "leg_left", "leg_right"):
                for cube in bone.get("cubes", []):
                    cube["size"] = [cube["size"][0], max(1, round(cube["size"][1] * 0.8)),
                                    cube["size"][2]]

    suffix = ".baby" if baby else ""
    geometry = {
        "description": {
            "identifier": f"geometry.paleo_{entity}{suffix}",
            "texture_width": tex_w,
            "texture_height": tex_h,
            "visible_bounds_width": spec["visible_bounds"][0],
            "visible_bounds_height": spec["visible_bounds"][1],
            "visible_bounds_offset": spec["visible_bounds"][2],
        },
        "bones": bones,
    }
    return geometry, uv_map


def bone_names(entity):
    names = ["root"]
    spec = MODELS[entity]
    for bone in spec["bones"]:
        names.append(bone["name"])
        if bone["name"] in spec["mirrored"]:
            names.append(spec.get("mirror_names", {}).get(
                bone["name"], bone["name"].replace("_left", "_right")
            ))
    return names


def tail_names(entity):
    return [n for n in bone_names(entity) if n.startswith("tail_")]


def leg_names(entity):
    names = bone_names(entity)
    return [n for n in names if n.startswith("leg_")]


def has_bone(entity, name):
    return name in bone_names(entity)


# ---------------------------------------------------------------------------
# Animations
# ---------------------------------------------------------------------------
def anim_walk(entity):
    spec = MODELS[entity]
    g = spec["gait"]
    legs = leg_names(entity)
    bones = {}
    # Diagonal gait: left front pairs with right back.
    phase = {}
    for i, leg in enumerate(sorted(legs)):
        phase[leg] = 1.0 if i % 2 == 0 else -1.0
    for leg in legs:
        bones[leg] = {
            "rotation": [
                f"math.cos(query.anim_time * {g['stride']}) * {g['swing'] * phase[leg]:.1f}",
                0.0,
                0.0,
            ]
        }
    tails = tail_names(entity)
    for i, t in enumerate(tails):
        amp = g["tail_sway"] * (0.6 + 0.25 * i)
        bones[t] = {
            "rotation": [
                f"math.cos(query.anim_time * {g['stride'] * 0.5:.2f}) * {amp * 0.35:.1f}",
                f"math.sin(query.anim_time * {g['stride'] * 0.5:.2f}) * {amp:.1f}",
                0.0,
            ]
        }
    bones["body"] = {
        "position": [
            0.0,
            f"math.cos(query.anim_time * {g['stride'] * 2:.2f}) * {g['bob']:.2f}",
            0.0,
        ],
        "rotation": [0.0, f"math.sin(query.anim_time * {g['stride'] * 0.5:.2f}) * 2.5", 0.0],
    }
    if has_bone(entity, "neck"):
        bones["neck"] = {
            "rotation": [
                f"-math.cos(query.anim_time * {g['stride']}) * 4.0",
                0.0,
                0.0,
            ]
        }
    for arm in ("arm_left", "arm_right"):
        if has_bone(entity, arm):
            sign = -1.0 if arm.endswith("left") else 1.0
            bones[arm] = {
                "rotation": [
                    f"math.cos(query.anim_time * {g['stride']}) * {24.0 * sign:.1f}",
                    0.0,
                    0.0,
                ]
            }
    return {
        "loop": True,
        "anim_time_update": "query.modified_distance_moved",
        "bones": bones,
    }


def anim_idle(entity):
    tails = tail_names(entity)
    bones = {
        "body": {
            "position": [0.0, "math.cos(query.life_time * 90) * 0.25", 0.0],
            "rotation": ["math.cos(query.life_time * 60) * 0.8", 0.0, 0.0],
        }
    }
    for i, t in enumerate(tails):
        bones[t] = {
            "rotation": [
                0.0,
                f"math.sin(query.life_time * {40 + 12 * i}) * {5.0 + 2.0 * i:.1f}",
                0.0,
            ]
        }
    if has_bone(entity, "head"):
        bones["head"] = {
            "rotation": ["math.cos(query.life_time * 45) * 1.6", 0.0, 0.0]
        }
    if has_bone(entity, "neck"):
        bones["neck"] = {
            "rotation": ["math.cos(query.life_time * 45) * -1.2", 0.0, 0.0]
        }
    for arm in ("arm_left", "arm_right"):
        if has_bone(entity, arm):
            bones[arm] = {"rotation": ["math.sin(query.life_time * 50) * 3.0", 0.0, 0.0]}
    return {
        "loop": True,
        "animation_length": 4.0,
        "bones": bones,
    }


def anim_look_at_target(entity):
    if not has_bone(entity, "head"):
        return None
    return {
        "loop": True,
        "bones": {
            "head": {
                "relative_to": {"rotation": "entity"},
                "rotation": [
                    "query.target_x_rotation - this",
                    "query.target_y_rotation - this",
                    0.0,
                ],
            }
        },
    }


def anim_attack(entity):
    bones = {}
    if has_bone(entity, "head"):
        bones["head"] = {
            "rotation": {
                "0.0": [-22.0, 0.0, 0.0],
                "0.28": [16.0, 0.0, 0.0],
                "0.55": [4.0, 0.0, 0.0],
                "0.8": [0.0, 0.0, 0.0],
            }
        }
    if has_bone(entity, "jaw"):
        bones["jaw"] = {
            "rotation": {
                "0.0": [4.0, 0.0, 0.0],
                "0.2": [30.0, 0.0, 0.0],
                "0.45": [10.0, 0.0, 0.0],
                "0.8": [0.0, 0.0, 0.0],
            }
        }
    if has_bone(entity, "neck"):
        bones["neck"] = {
            "rotation": {
                "0.0": [12.0, 0.0, 0.0],
                "0.28": [-14.0, 0.0, 0.0],
                "0.8": [0.0, 0.0, 0.0],
            }
        }
    bones["body"] = {
        "position": {
            "0.0": [0.0, 0.0, 0.0],
            "0.25": [0.0, -0.8, -1.4],
            "0.5": [0.0, 0.4, 1.0],
            "0.8": [0.0, 0.0, 0.0],
        }
    }
    # `blend_out_time` NAO existe no formato de animacao do Bedrock: as unicas
    # chaves validas (derivadas de 700+ animacoes vanilla) sao bones, loop,
    # animation_length, sound_effects, anim_time_update, particle_effects,
    # start_delay e override_previous_animation.  Blending pertence ao
    # animation controller, via blend_transition.
    return {
        "loop": False,
        "animation_length": 0.8,
        "override_previous_animation": True,
        "bones": bones,
    }


def anim_eat(entity):
    bones = {}
    if has_bone(entity, "head"):
        bones["head"] = {
            "rotation": {
                "0.0": [0.0, 0.0, 0.0],
                "0.4": [26.0, 0.0, 0.0],
                "0.8": [10.0, 0.0, 0.0],
                "1.2": [26.0, 0.0, 0.0],
                "1.6": [0.0, 0.0, 0.0],
            }
        }
    if has_bone(entity, "neck"):
        bones["neck"] = {
            "rotation": {
                "0.0": [0.0, 0.0, 0.0],
                "0.4": [18.0, 0.0, 0.0],
                "0.8": [8.0, 0.0, 0.0],
                "1.2": [18.0, 0.0, 0.0],
                "1.6": [0.0, 0.0, 0.0],
            }
        }
    if has_bone(entity, "jaw"):
        bones["jaw"] = {
            "rotation": {
                "0.0": [0.0, 0.0, 0.0],
                "0.4": [12.0, 0.0, 0.0],
                "0.6": [2.0, 0.0, 0.0],
                "1.2": [12.0, 0.0, 0.0],
                "1.6": [0.0, 0.0, 0.0],
            }
        }
    return {"loop": True, "animation_length": 1.6, "bones": bones}


def anim_rest(entity):
    bones = {
        "body": {
            "position": [0.0, -2.2, 0.0],
            "rotation": [6.0, 0.0, 0.0],
        }
    }
    for leg in leg_names(entity):
        bones[leg] = {"rotation": [-72.0, 0.0, 0.0], "position": [0.0, 1.2, 0.0]}
    for arm in ("arm_left", "arm_right"):
        if has_bone(entity, arm):
            bones[arm] = {"rotation": [-40.0, 0.0, 0.0]}
    if has_bone(entity, "neck"):
        bones["neck"] = {"rotation": [16.0, 0.0, 0.0]}
    if has_bone(entity, "head"):
        bones["head"] = {"rotation": [24.0, 0.0, 0.0]}
    for i, t in enumerate(tail_names(entity)):
        bones[t] = {"rotation": [0.0, 8.0 + 4.0 * i, 0.0]}
    return {"loop": True, "bones": bones}


def anim_roar(entity):
    bones = {}
    if has_bone(entity, "head"):
        bones["head"] = {
            "rotation": {
                "0.0": [0.0, 0.0, 0.0],
                "0.35": [-34.0, 0.0, 0.0],
                "1.1": [-28.0, 0.0, 0.0],
                "1.6": [0.0, 0.0, 0.0],
            }
        }
    if has_bone(entity, "jaw"):
        bones["jaw"] = {
            "rotation": {
                "0.0": [0.0, 0.0, 0.0],
                "0.3": [42.0, 0.0, 0.0],
                "1.15": [38.0, 0.0, 0.0],
                "1.6": [0.0, 0.0, 0.0],
            }
        }
    if has_bone(entity, "neck"):
        bones["neck"] = {
            "rotation": {
                "0.0": [0.0, 0.0, 0.0],
                "0.35": [-22.0, 0.0, 0.0],
                "1.1": [-18.0, 0.0, 0.0],
                "1.6": [0.0, 0.0, 0.0],
            }
        }
    bones["body"] = {
        "position": {
            "0.0": [0.0, 0.0, 0.0],
            "0.35": [0.0, 1.6, -1.0],
            "1.1": [0.0, 1.2, -0.6],
            "1.6": [0.0, 0.0, 0.0],
        },
        "rotation": {
            "0.0": [0.0, 0.0, 0.0],
            "0.35": [-12.0, 0.0, 0.0],
            "1.6": [0.0, 0.0, 0.0],
        },
    }
    for i, t in enumerate(tail_names(entity)):
        bones[t] = {
            "rotation": {
                "0.0": [0.0, 0.0, 0.0],
                "0.35": [8.0 + 3.0 * i, 0.0, 0.0],
                "1.1": [6.0 + 3.0 * i, 0.0, 0.0],
                "1.6": [0.0, 0.0, 0.0],
                "2.4": [0.0, 0.0, 0.0],
            }
        }
    return {"loop": True, "animation_length": 2.4, "bones": bones}


ANIMATION_BUILDERS = [
    ("walk", anim_walk),
    ("idle", anim_idle),
    ("look_at_target", anim_look_at_target),
    ("attack", anim_attack),
    ("eat", anim_eat),
    ("rest", anim_rest),
    ("roar", anim_roar),
]


def build_animation_controller(entity):
    """One controller drives every bone so tracks never fight each other.

    calm      -> idle or walk, head tracking, eating overlay
    aggressive-> idle or walk plus the looping roar/charge cycle
    sleeping  -> resting pose
    The bite ("attack") animation is fired from script with Entity.playAnimation
    exactly when a hit lands, so it is intentionally not part of this controller.
    """
    ident = f"controller.animation.paleo_{entity}"
    return {
        "format_version": cm.FORMAT_ANIMATION_CONTROLLER,
        "animation_controllers": {
            ident: {
                "initial_state": "calm",
                "states": {
                    "calm": {
                        "blend_transition": 0.2,
                        "animations": [
                            {"idle": "query.modified_move_speed <= 0.05"},
                            {"walk": "query.modified_move_speed"},
                            "look_at_target",
                            {"eat": "query.is_eating"},
                        ],
                        "transitions": [
                            {"aggressive": "query.is_angry"},
                            {"sleeping": "query.is_sleeping"},
                        ],
                    },
                    "aggressive": {
                        "blend_transition": 0.2,
                        "animations": [
                            {"idle": "query.modified_move_speed <= 0.05"},
                            {"walk": "query.modified_move_speed"},
                            "look_at_target",
                            {"roar": "1.0"},
                        ],
                        "transitions": [
                            {"calm": "!query.is_angry"},
                            {"sleeping": "query.is_sleeping"},
                        ],
                    },
                    "sleeping": {
                        "blend_transition": 0.3,
                        "animations": ["rest"],
                        "transitions": [
                            {"calm": "!query.is_sleeping"},
                        ],
                    },
                },
            }
        },
    }


def build_render_controller(entity):
    ident = f"controller.render.paleo_{entity}"
    return {
        "format_version": cm.FORMAT_RENDER_CONTROLLER,
        "render_controllers": {
            ident: {
                "arrays": {
                    "textures": {
                        "Array.skins": [
                            "Texture.wild",
                            "Texture.bonded",
                            "Texture.alert",
                            "Texture.tagged",
                        ]
                    },
                    "geometries": {
                        "Array.models": ["Geometry.default", "Geometry.baby"]
                    },
                },
                "geometry": "query.is_baby ? Array.models[1] : Array.models[0]",
                "materials": [{"*": "Material.default"}],
                # studied individuals (mark_variant 1) wear the field tag skin
                "textures": [
                    "Array.skins[query.mark_variant == 1 ? 3 : query.variant]"
                ],
            }
        },
    }


def build_client_entity(sp):
    entity = sp["entity"]
    prefix = f"paleo_{entity}"
    return {
        "format_version": cm.FORMAT_CLIENT_ENTITY,
        "minecraft:client_entity": {
            "description": {
                "identifier": sp["entity_id"],
                "materials": {"default": "entity_alphatest"},
                "textures": {
                    "wild": f"textures/entity/{prefix}_wild",
                    "bonded": f"textures/entity/{prefix}_bonded",
                    "alert": f"textures/entity/{prefix}_alert",
                    "tagged": f"textures/entity/{prefix}_tagged",
                },
                "geometry": {
                    "default": f"geometry.paleo_{entity}",
                    "baby": f"geometry.paleo_{entity}.baby",
                },
                "animations": {
                    "walk": f"animation.paleo_{entity}.walk",
                    "idle": f"animation.paleo_{entity}.idle",
                    "look_at_target": f"animation.paleo_{entity}.look_at_target",
                    "attack": f"animation.paleo_{entity}.attack",
                    "eat": f"animation.paleo_{entity}.eat",
                    "rest": f"animation.paleo_{entity}.rest",
                    "roar": f"animation.paleo_{entity}.roar",
                    "paleo_move": f"controller.animation.paleo_{entity}",
                },
                "scripts": {
                    "pre_animation": [
                        "variable.paleo_speed = query.modified_move_speed;",
                    ],
                    # Controller listado em `animations` + `scripts.animate`,
                    # como faz o armor_stand vanilla (fv 1.10.0).  Evita a chave
                    # `animation_controllers`, que o parser de animacao loga como
                    # erro mesmo em definicoes vanilla (iron_golem).
                    "animate": ["paleo_move"],
                    "scale": "1.0",
                },
                "render_controllers": [f"controller.render.paleo_{entity}"],
                "spawn_egg": {
                    "texture": f"paleo_spawn_egg_{entity}",
                    "texture_index": 0,
                },
            }
        },
    }


def write_json(rel, data):
    path = os.path.join(RP, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return path


def block_cube(identifier):
    face = {"uv": [0, 0], "uv_size": [16, 16]}
    flip = {"uv": [0, 16], "uv_size": [16, -16]}
    return {
        "format_version": "1.19.0",
        "minecraft:geometry": [
            {
                "description": {
                    "identifier": identifier,
                    "texture_width": 16,
                    "texture_height": 16,
                    "visible_bounds_width": 2,
                    "visible_bounds_height": 2,
                    "visible_bounds_offset": [0, 0.5, 0],
                },
                "bones": [
                    {
                        "name": "block",
                        "pivot": [0, 0, 0],
                        "cubes": [
                            {
                                "origin": [-8, 0, -8],
                                "size": [16, 16, 16],
                                "uv": {
                                    "north": face,
                                    "east": face,
                                    "south": face,
                                    "west": face,
                                    "up": flip,
                                    "down": flip,
                                },
                            }
                        ],
                    }
                ],
            }
        ],
    }


def main():
    written = []
    for identifier in ("geometry.paleo_research_bench", "geometry.paleo_incubator"):
        written.append(write_json(
            f"models/blocks/{identifier.split('.')[-1]}.geo.json", block_cube(identifier)))
    for sp in cm.SPECIES:
        entity = sp["entity"]
        adult, _ = build_geometry(entity, baby=False)
        baby, _ = build_geometry(entity, baby=True)
        written.append(write_json(f"models/entity/paleo_{entity}.geo.json", {
            "format_version": cm.FORMAT_GEOMETRY,
            "minecraft:geometry": [adult, baby],
        }))

        animations = {}
        for name, builder in ANIMATION_BUILDERS:
            anim = builder(entity)
            if anim is None:
                continue
            animations[f"animation.paleo_{entity}.{name}"] = anim
        written.append(write_json(f"animations/paleo_{entity}.animation.json", {
            "format_version": cm.FORMAT_ANIMATION,
            "animations": animations,
        }))
        written.append(write_json(
            f"animation_controllers/paleo_{entity}.animation_controllers.json",
            build_animation_controller(entity),
        ))
        written.append(write_json(
            f"render_controllers/paleo_{entity}.render_controllers.json",
            build_render_controller(entity),
        ))
        written.append(write_json(f"entity/paleo_{entity}.entity.json", build_client_entity(sp)))

    # Export the UV layout so the texture generator paints exactly these rects.
    layout = {}
    for sp in cm.SPECIES:
        entity = sp["entity"]
        _, uv_map = build_geometry(entity, baby=False)
        layout[entity] = dict(
            texture=list(MODELS[entity]["texture"]),
            cubes=uv_map,
        )
    layout_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uv_layout.json")
    with open(layout_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(layout, fh, indent=1)
    print("[gen_geometry] wrote uv_layout.json")

    print(f"[gen_geometry] wrote {len(written)} files")
    for path in written:
        print("   ", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
