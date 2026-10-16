#!/usr/bin/env python3
"""Generates every PNG asset for PALEOFRONTIER.

All art is produced procedurally with a fixed seed so builds are reproducible.
Nothing references an external image.

Requires: Pillow  (pip install Pillow)
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_model as cm  # noqa: E402

from PIL import Image, ImageDraw  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(ROOT, "resource_pack")
BP = os.path.join(ROOT, "behavior_pack")
HERE = os.path.dirname(os.path.abspath(__file__))

SEED = 20261016


def rng(*salt):
    """Deterministic RNG seeded from the constant seed plus a stable salt hash."""
    h = hashlib.sha256()
    h.update(str(SEED).encode("utf-8"))
    for s in salt:
        h.update(b"|")
        h.update(str(s).encode("utf-8"))
    return random.Random(int(h.hexdigest()[:16], 16))


def save(img, rel, root=RP):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, "PNG", optimize=True)
    return path


def shade(col, amount):
    """amount > 0 lightens, < 0 darkens."""
    if amount >= 0:
        return tuple(min(255, int(c + (255 - c) * amount)) for c in col[:3])
    return tuple(max(0, int(c * (1 + amount))) for c in col[:3])


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def putpx(img, x, y, col):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), tuple(col))


# ===========================================================================
# 1. Block textures (16x16)
# ===========================================================================
def noise_fill(img, base, spread, r, alpha=255):
    for y in range(img.height):
        for x in range(img.width):
            d = r.randint(-spread, spread)
            putpx(img, x, y, (base[0] + d, base[1] + d, base[2] + d, alpha))


def strata(img, r, bands, jitter=1):
    """Horizontal sediment bands."""
    y = 0
    for colour, thickness in bands:
        for _ in range(thickness):
            if y >= img.height:
                break
            for x in range(img.width):
                d = r.randint(-jitter * 6, jitter * 6)
                putpx(img, x, y, (colour[0] + d, colour[1] + d, colour[2] + d, 255))
            y += 1
        y += r.randint(0, 1)


def speckle(img, r, colours, count, alpha=255):
    for _ in range(count):
        x = r.randrange(img.width)
        y = r.randrange(img.height)
        c = r.choice(colours)
        putpx(img, x, y, (c[0], c[1], c[2], alpha))


def fossil_deposit_texture():
    img = Image.new("RGBA", (16, 16))
    r = rng("fossil_deposit")
    strata(img, r, [
        ((150, 133, 106), 3),
        ((132, 116, 92), 2),
        ((158, 141, 113), 4),
        ((120, 105, 84), 2),
        ((146, 129, 103), 3),
        ((128, 112, 90), 2),
    ], jitter=1)
    speckle(img, r, [(96, 84, 66), (176, 160, 132), (84, 74, 58)], 34)
    # small embedded bone flecks
    for _ in range(5):
        x = r.randrange(1, 13)
        y = r.randrange(1, 13)
        putpx(img, x, y, (214, 205, 182, 255))
        putpx(img, x + 1, y, (196, 186, 162, 255))
        putpx(img, x + 1, y + 1, (176, 166, 142, 255))
    return img


def shale_matrix_texture():
    img = Image.new("RGBA", (16, 16))
    r = rng("shale_matrix")
    strata(img, r, [
        ((70, 78, 88), 2),
        ((58, 65, 74), 3),
        ((80, 88, 98), 2),
        ((52, 58, 66), 3),
        ((72, 80, 90), 2),
        ((60, 67, 76), 4),
    ], jitter=1)
    # fissures
    for _ in range(4):
        y = r.randrange(0, 16)
        x = r.randrange(0, 6)
        length = r.randint(6, 11)
        for i in range(length):
            putpx(img, x + i, y + (1 if r.random() < 0.25 else 0), (36, 40, 46, 255))
    speckle(img, r, [(94, 102, 114), (40, 45, 52)], 26)
    # faint rib impression
    for i in range(5):
        putpx(img, 4 + i * 2, 6 + (i % 2), (118, 114, 102, 255))
        putpx(img, 4 + i * 2, 7 + (i % 2), (98, 94, 84, 255))
    return img


def bone_bed_texture():
    img = Image.new("RGBA", (16, 16))
    r = rng("bone_bed")
    strata(img, r, [
        ((168, 152, 124), 3),
        ((146, 131, 106), 3),
        ((176, 160, 132), 4),
        ((138, 124, 100), 3),
        ((162, 146, 120), 3),
    ], jitter=1)
    speckle(img, r, [(120, 108, 88), (198, 184, 156)], 22)
    bone = (232, 226, 206)
    bone_dark = (196, 188, 164)
    # vertebral column running diagonally with ribs
    for i in range(7):
        x, y = 2 + i * 2, 3 + i
        putpx(img, x, y, bone)
        putpx(img, x + 1, y, bone_dark)
        putpx(img, x, y + 1, bone_dark)
        # rib arc
        for j in range(4):
            putpx(img, x, y + 2 + j, bone if j < 2 else bone_dark)
    putpx(img, 13, 12, bone)
    putpx(img, 14, 12, bone_dark)
    putpx(img, 14, 13, bone_dark)
    return img


def research_bench_top():
    img = Image.new("RGBA", (16, 16))
    r = rng("bench_top")
    wood = (92, 68, 46)
    for y in range(16):
        for x in range(16):
            d = r.randint(-9, 9)
            putpx(img, x, y, (wood[0] + d, wood[1] + d, wood[2] + d, 255))
    # plank seams
    for x in range(16):
        putpx(img, x, 5, (66, 48, 32, 255))
        putpx(img, x, 11, (66, 48, 32, 255))
    # metal frame border
    for x in range(16):
        putpx(img, x, 0, (126, 126, 130, 255))
        putpx(img, x, 15, (110, 110, 114, 255))
    for y in range(16):
        putpx(img, 0, y, (126, 126, 130, 255))
        putpx(img, 15, y, (110, 110, 114, 255))
    # amber sample + lens
    for (x, y) in [(4, 8), (5, 8), (4, 9), (5, 9)]:
        putpx(img, x, y, (214, 158, 52, 255))
    putpx(img, 5, 8, (240, 200, 110, 255))
    for (x, y) in [(10, 7), (11, 7), (10, 8), (11, 8), (12, 8)]:
        putpx(img, x, y, (168, 206, 208, 255))
    putpx(img, 10, 7, (216, 240, 240, 255))
    # notebook
    for x in range(2, 8):
        for y in range(2, 5):
            putpx(img, x, y, (222, 214, 192, 255))
    putpx(img, 3, 3, (120, 108, 88, 255))
    putpx(img, 5, 3, (120, 108, 88, 255))
    return img


def research_bench_side():
    img = Image.new("RGBA", (16, 16))
    r = rng("bench_side")
    wood = (84, 62, 42)
    for y in range(16):
        for x in range(16):
            d = r.randint(-8, 8)
            putpx(img, x, y, (wood[0] + d, wood[1] + d, wood[2] + d, 255))
    for x in range(16):
        putpx(img, x, 0, (132, 132, 136, 255))
        putpx(img, x, 1, (104, 104, 108, 255))
        putpx(img, x, 14, (58, 42, 28, 255))
        putpx(img, x, 15, (48, 34, 22, 255))
    # drawer
    for x in range(3, 13):
        for y in range(5, 11):
            putpx(img, x, y, (66, 48, 32, 255))
    for x in range(4, 12):
        for y in range(6, 10):
            putpx(img, x, y, (98, 72, 50, 255))
    putpx(img, 7, 8, (176, 160, 96, 255))
    putpx(img, 8, 8, (176, 160, 96, 255))
    # iron bracket legs
    for y in range(11, 15):
        putpx(img, 1, y, (120, 120, 124, 255))
        putpx(img, 14, y, (120, 120, 124, 255))
    return img


def research_bench_front():
    img = research_bench_side().copy()
    r = rng("bench_front")
    # instrument panel with a teal readout
    for x in range(3, 13):
        for y in range(4, 10):
            putpx(img, x, y, (54, 62, 68, 255))
    for x in range(4, 12):
        for y in range(5, 9):
            putpx(img, x, y, (30, 44, 48, 255))
    for i, x in enumerate(range(4, 12)):
        h = [1, 2, 3, 2, 1, 2, 3, 1][i]
        for y in range(8 - h, 9):
            putpx(img, x, y, (96, 214, 200, 255))
    # magnifier arm
    for y in range(1, 5):
        putpx(img, 13, y, (140, 140, 144, 255))
    for x in range(11, 15):
        putpx(img, x, 1, (140, 140, 144, 255))
    for (x, y) in [(10, 2), (11, 2), (10, 3), (11, 3)]:
        putpx(img, x, y, (178, 214, 216, 255))
    return img


def incubator_side():
    img = Image.new("RGBA", (16, 16))
    r = rng("incu_side")
    iron = (118, 122, 126)
    for y in range(16):
        for x in range(16):
            d = r.randint(-8, 8)
            putpx(img, x, y, (iron[0] + d, iron[1] + d, iron[2] + d, 255))
    for x in range(16):
        putpx(img, x, 0, (86, 90, 94, 255))
        putpx(img, x, 15, (76, 80, 84, 255))
    for y in range(16):
        putpx(img, 0, y, (94, 98, 102, 255))
        putpx(img, 15, y, (94, 98, 102, 255))
    # copper rivets
    for (x, y) in [(1, 1), (14, 1), (1, 14), (14, 14)]:
        putpx(img, x, y, (178, 108, 62, 255))
    # coolant strip
    for y in range(3, 13):
        putpx(img, 3, y, (58, 128, 128, 255))
        putpx(img, 4, y, (86, 176, 172, 255))
    # vent grille
    for y in range(4, 13, 2):
        for x in range(8, 14):
            putpx(img, x, y, (70, 74, 78, 255))
    return img


def incubator_top():
    img = Image.new("RGBA", (16, 16))
    r = rng("incu_top")
    iron = (126, 130, 134)
    for y in range(16):
        for x in range(16):
            d = r.randint(-7, 7)
            putpx(img, x, y, (iron[0] + d, iron[1] + d, iron[2] + d, 255))
    # circular vent
    cx, cy = 8, 8
    for y in range(16):
        for x in range(16):
            dx, dy = x - cx, y - cy
            d2 = dx * dx + dy * dy
            if d2 <= 20:
                putpx(img, x, y, (62, 66, 70, 255))
            elif d2 <= 26:
                putpx(img, x, y, (150, 154, 158, 255))
    for i in range(4):
        putpx(img, cx - 3 + i * 2, cy, (104, 108, 112, 255))
    for (x, y) in [(1, 1), (14, 1), (1, 14), (14, 14)]:
        putpx(img, x, y, (178, 108, 62, 255))
    return img


def incubator_chamber(stage, egg_colour):
    """Glass chamber; stage 0..4 fills with gel and grows an embryo."""
    img = Image.new("RGBA", (16, 16))
    r = rng("incu_chamber", stage)
    frame = (86, 90, 94)
    for y in range(16):
        for x in range(16):
            putpx(img, x, y, frame + (255,))
    glass = (150, 196, 198, 96)
    for y in range(2, 14):
        for x in range(2, 14):
            putpx(img, x, y, glass)
    gel = (70, 196, 168, 235)
    fill_top = {0: 14, 1: 12, 2: 10, 3: 7, 4: 4}[stage]
    for y in range(fill_top, 14):
        for x in range(2, 14):
            d = r.randint(-10, 10)
            putpx(img, x, y, (gel[0] + d, gel[1] + d, gel[2] + d, gel[3]))
    for x in range(2, 14):
        if fill_top < 14:
            putpx(img, x, fill_top, (176, 250, 230, 255))
    if stage >= 1:
        # egg suspended in the gel
        ex, ey = 8, min(10, fill_top + 3)
        for y in range(ey - 2, ey + 3):
            for x in range(ex - 2, ex + 3):
                dx, dy = x - ex, y - ey
                if dx * dx * 1.4 + dy * dy <= 5.2:
                    putpx(img, x, y, egg_colour["base"] + (255,))
        for _ in range(5):
            putpx(img, ex + r.randint(-2, 2), ey + r.randint(-2, 2),
                  egg_colour["spots"] + (255,))
    if stage >= 3:
        # embryo silhouette
        ex, ey = 8, min(11, fill_top + 3)
        spine = (60, 44, 34, 255)
        for i in range(4):
            putpx(img, ex - 1 + i, ey - 1 + (i % 2), spine)
        putpx(img, ex + 2, ey - 2, spine)
        putpx(img, ex - 2, ey + 1, spine)
    if stage >= 4:
        # ready: bright rim + cracks
        for x in range(2, 14):
            putpx(img, x, 2, (214, 255, 236, 220))
            putpx(img, x, 13, (214, 255, 236, 220))
        for y in range(2, 14):
            putpx(img, 2, y, (214, 255, 236, 220))
            putpx(img, 13, y, (214, 255, 236, 220))
        putpx(img, 7, 8, (255, 255, 255, 255))
        putpx(img, 8, 9, (255, 255, 255, 255))
        putpx(img, 9, 8, (255, 255, 255, 255))
    # glass highlight
    putpx(img, 3, 3, (232, 250, 250, 150))
    putpx(img, 4, 3, (232, 250, 250, 120))
    putpx(img, 3, 4, (232, 250, 250, 120))
    return img


def gen_block_textures():
    out = []
    out.append(save(fossil_deposit_texture(), "textures/blocks/paleo_fossil_deposit.png"))
    out.append(save(shale_matrix_texture(), "textures/blocks/paleo_shale_matrix.png"))
    out.append(save(bone_bed_texture(), "textures/blocks/paleo_bone_bed.png"))
    out.append(save(research_bench_top(), "textures/blocks/paleo_research_bench_top.png"))
    out.append(save(research_bench_side(), "textures/blocks/paleo_research_bench_side.png"))
    out.append(save(research_bench_front(), "textures/blocks/paleo_research_bench_front.png"))
    out.append(save(incubator_side(), "textures/blocks/paleo_incubator_side.png"))
    out.append(save(incubator_top(), "textures/blocks/paleo_incubator_top.png"))
    for stage in range(5):
        species = cm.SPECIES[stage % len(cm.SPECIES)]
        base = tuple(int(species["egg_color"]["base"].lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
        spots = tuple(int(species["egg_color"]["spots"].lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
        out.append(save(
            incubator_chamber(stage, dict(base=base, spots=spots)),
            f"textures/blocks/paleo_incubator_chamber_{stage}.png",
        ))
    return out


# ===========================================================================
# 2. Item textures (16x16)
# ===========================================================================
def blank():
    return Image.new("RGBA", (16, 16), (0, 0, 0, 0))


def outline_shape(img, mask_fn, fill, edge, r):
    for y in range(16):
        for x in range(16):
            if mask_fn(x, y):
                inner = all(mask_fn(x + dx, y + dy)
                            for dx in (-1, 0, 1) for dy in (-1, 0, 1))
                c = fill if inner else edge
                d = r.randint(-10, 10)
                putpx(img, x, y, (c[0] + d, c[1] + d, c[2] + d, 255))


def tex_fossil_chip():
    img = blank()
    r = rng("chip")
    poly = [(6, 3), (9, 2), (12, 4), (13, 8), (12, 12), (9, 14), (5, 13),
            (3, 10), (2, 6), (4, 4)]

    def inside(x, y):
        n = len(poly)
        inside_ = False
        j = n - 1
        for i in range(n):
            xi, yi = poly[i]
            xj, yj = poly[j]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside_ = not inside_
            j = i
        return inside_

    outline_shape(img, inside, (162, 146, 118), (100, 88, 70), r)
    # facets
    for (x, y) in [(7, 5), (8, 6), (6, 6)]:
        putpx(img, x, y, (196, 182, 152, 255))
    # crack
    for (x, y) in [(5, 8), (6, 9), (7, 9), (8, 10), (9, 11)]:
        putpx(img, x, y, (92, 80, 64, 255))
    # embedded bone fleck
    putpx(img, 9, 8, (228, 220, 196, 255))
    putpx(img, 10, 8, (208, 200, 176, 255))
    putpx(img, 10, 9, (208, 200, 176, 255))
    return img


def tex_bone_shard():
    img = blank()
    r = rng("shard")
    # diagonal shaft from (4,11) to (11,4), two knobs per end
    shaft = []
    for i in range(8):
        shaft.append((4 + i, 11 - i))
        shaft.append((5 + i, 11 - i))
        shaft.append((4 + i, 12 - i))
    knobs = [(3, 10), (2, 11), (3, 12), (4, 13), (2, 12),
             (11, 3), (12, 2), (13, 3), (12, 4), (13, 4), (11, 2)]
    pts = set(shaft) | set(knobs)

    def m(x, y):
        return (x, y) in pts

    outline_shape(img, m, (236, 230, 210), (172, 164, 142), r)
    for (x, y) in [(5, 10), (6, 9), (7, 8), (8, 7)]:
        putpx(img, x, y, (252, 248, 234, 255))
    putpx(img, 3, 11, (150, 140, 118, 255))
    putpx(img, 12, 3, (150, 140, 118, 255))
    return img


def tex_amber():
    img = blank()
    r = rng("amber")

    def m(x, y):
        dx, dy = x - 8, y - 8
        return dx * dx * 1.1 + dy * dy * 1.25 <= 34

    outline_shape(img, m, (226, 168, 58), (150, 96, 26), r)
    for y in range(16):
        for x in range(16):
            if m(x, y) and (x + y) % 5 == 0:
                putpx(img, x, y, (246, 200, 96, 255))
    putpx(img, 6, 6, (255, 236, 168, 255))
    putpx(img, 7, 6, (255, 240, 186, 255))
    # trapped insect
    for (x, y) in [(8, 9), (9, 9), (9, 10), (10, 8), (8, 10), (7, 9)]:
        putpx(img, x, y, (66, 40, 18, 255))
    return img


def tex_nutrient_gel():
    img = blank()
    r = rng("gel")
    # dish
    for x in range(3, 13):
        putpx(img, x, 12, (196, 200, 202, 255))
        putpx(img, x, 13, (150, 154, 158, 255))
    for y in range(7, 13):
        putpx(img, 3, y, (176, 180, 184, 255))
        putpx(img, 12, y, (176, 180, 184, 255))

    def m(x, y):
        dx, dy = x - 7.5, y - 9
        return dx * dx + dy * dy * 1.6 <= 15

    outline_shape(img, m, (104, 208, 182), (56, 140, 122), r)
    putpx(img, 6, 7, (188, 250, 232, 255))
    putpx(img, 9, 9, (150, 236, 214, 255))
    return img


def tex_genetic_matrix():
    img = blank()
    r = rng("matrix")
    # dark slate tablet
    for y in range(3, 14):
        for x in range(3, 13):
            d = r.randint(-8, 8)
            putpx(img, x, y, (44 + d, 50 + d, 58 + d, 255))
    for x in range(3, 13):
        putpx(img, x, 2, (74, 82, 92, 255))
        putpx(img, x, 14, (26, 30, 36, 255))
    for y in range(2, 15):
        putpx(img, 2, y, (66, 74, 84, 255))
        putpx(img, 13, y, (30, 34, 40, 255))
    # double helix
    glow_a = (126, 232, 214)
    glow_b = (214, 168, 250)
    for i in range(9):
        y = 4 + i
        off = [0, 1, 2, 3, 4, 3, 2, 1, 0][i]
        putpx(img, 5 + off, y, glow_a + (255,))
        putpx(img, 10 - off, y, glow_b + (255,))
        if i % 2 == 0:
            putpx(img, 6 + off // 2, y, (90, 170, 168, 255))
            putpx(img, 9 - off // 2, y, (150, 120, 180, 255))
    return img


def tex_shovel():
    img = blank()
    r = rng("shovel")
    # handle
    for i in range(9):
        putpx(img, 3 + i, 12 - i, (126, 92, 54, 255))
        putpx(img, 4 + i, 12 - i, (98, 70, 40, 255))
    # binding
    putpx(img, 8, 8, (178, 108, 62, 255))
    putpx(img, 9, 7, (178, 108, 62, 255))

    def m(x, y):
        return (9 <= x <= 14) and (1 <= y <= 7) and (x + y) <= 19 and (x + y) >= 11

    outline_shape(img, m, (198, 202, 206), (132, 136, 142), r)
    # bone reinforcement along the blade edge
    for i in range(4):
        putpx(img, 10 + i, 6 - i, (236, 230, 210, 255))
    putpx(img, 12, 3, (238, 242, 246, 255))
    return img


def tex_brush():
    img = blank()
    r = rng("brush")
    for i in range(8):
        putpx(img, 3 + i, 12 - i, (140, 104, 62, 255))
        putpx(img, 4 + i, 13 - i, (108, 78, 46, 255))
    # ferrule
    putpx(img, 10, 4, (176, 176, 180, 255))
    putpx(img, 11, 3, (176, 176, 180, 255))
    putpx(img, 11, 4, (138, 138, 142, 255))

    def m(x, y):
        return (11 <= x <= 15) and (0 <= y <= 4) and (x - y) >= 8 and (x + y) <= 18

    outline_shape(img, m, (228, 214, 178), (176, 158, 120), r)
    for (x, y) in [(14, 1), (13, 2), (15, 2)]:
        putpx(img, x, y, (250, 244, 224, 255))
    return img


def tex_scanner():
    img = blank()
    r = rng("scanner")
    # body
    for y in range(5, 14):
        for x in range(4, 12):
            d = r.randint(-7, 7)
            putpx(img, x, y, (58 + d, 64 + d, 72 + d, 255))
    for x in range(4, 12):
        putpx(img, x, 4, (94, 100, 108, 255))
        putpx(img, x, 14, (32, 36, 42, 255))
    for y in range(4, 15):
        putpx(img, 3, y, (86, 92, 100, 255))
        putpx(img, 12, y, (36, 40, 46, 255))
    # screen with a sweep
    for y in range(6, 11):
        for x in range(5, 11):
            putpx(img, x, y, (22, 46, 48, 255))
    for i, x in enumerate(range(5, 11)):
        h = [1, 2, 3, 2, 4, 2][i]
        for y in range(10 - h, 10):
            putpx(img, x, y, (104, 226, 206, 255))
    putpx(img, 8, 7, (220, 255, 244, 255))
    # copper coil antenna
    for y in range(1, 5):
        putpx(img, 10, y, (178, 108, 62, 255))
        putpx(img, 11, y, (214, 146, 92, 255))
    putpx(img, 10, 0, (232, 176, 118, 255))
    putpx(img, 11, 0, (232, 176, 118, 255))
    # grip
    for y in range(11, 15):
        putpx(img, 6, y, (110, 82, 50, 255))
        putpx(img, 7, y, (88, 64, 38, 255))
    return img


def tex_field_case():
    img = blank()
    r = rng("case")
    for y in range(4, 14):
        for x in range(2, 14):
            d = r.randint(-9, 9)
            putpx(img, x, y, (126 + d, 90 + d, 56 + d, 255))
    for x in range(2, 14):
        putpx(img, x, 3, (150, 110, 70, 255))
        putpx(img, x, 14, (86, 60, 36, 255))
    for y in range(3, 15):
        putpx(img, 1, y, (140, 102, 64, 255))
        putpx(img, 14, y, (92, 64, 38, 255))
    # lid seam + straps
    for x in range(2, 14):
        putpx(img, x, 8, (92, 64, 38, 255))
    for y in range(3, 15):
        putpx(img, 5, y, (74, 52, 30, 255))
        putpx(img, 10, y, (74, 52, 30, 255))
    # buckles
    putpx(img, 5, 8, (196, 168, 92, 255))
    putpx(img, 10, 8, (196, 168, 92, 255))
    # paper tag
    for y in range(10, 13):
        for x in range(6, 10):
            putpx(img, x, y, (226, 218, 194, 255))
    putpx(img, 7, 11, (120, 108, 88, 255))
    # handle
    for x in range(6, 10):
        putpx(img, x, 2, (98, 70, 42, 255))
    return img


SPECIMEN_SILHOUETTES = {
    # 12x9 silhouettes drawn inside a stone slab, one per species
    "compy": [
        "....XXXX....",
        "...XXXXXX...",
        "..XX.XXXX...",
        "..XXXXXXX...",
        ".XXXXXXXX...",
        "XXXXXXX.....",
        ".XXXXX......",
        "..XX.X......",
        "..X..X......",
    ],
    "trike": [
        "....XXXXXX..",
        "..XXXXXXXXXX",
        ".XXXXXXXXXXX",
        "XXXXXXXXXX..",
        ".XXXXXXXX...",
        "..XXXXXX....",
        "..XX..XX....",
        "..XX..XX....",
        ".XXX..XXX...",
    ],
    "raptor": [
        ".....XXXX...",
        "....XXXXXX..",
        "...XXXXXXX..",
        "..XXXXXXXX..",
        ".XXXXXXXXX..",
        "XXXXXXXX....",
        ".XXXXXX.....",
        "..XX.XX.....",
        ".XX...XX....",
    ],
    "rex": [
        "......XXXXX.",
        ".....XXXXXXX",
        "....XXXXXXXX",
        "...XXXXXXX..",
        "..XXXXXXXX..",
        ".XXXXXXXXX..",
        "XXXXXXXXX...",
        "..XXXX.XX...",
        ".XXX...XXX..",
    ],
}


def tex_specimen(key, rarity):
    img = blank()
    r = rng("specimen", key)
    slab = (118, 112, 98)
    slab_dark = (78, 74, 64)
    for y in range(1, 15):
        for x in range(1, 15):
            d = r.randint(-9, 9)
            edge = x in (1, 14) or y in (1, 14)
            putpx(img, x, y, ((slab_dark if edge else slab)[0] + d,
                              (slab_dark if edge else slab)[1] + d,
                              (slab_dark if edge else slab)[2] + d, 255))
    speckle(img, r, [(140, 134, 118), (92, 88, 76)], 20)
    bone = (242, 236, 216)
    bone_sh = (204, 196, 174)
    outline = (52, 48, 40)
    rows = SPECIMEN_SILHOUETTES[key]
    silhouette = set()
    for ry, row in enumerate(rows):
        for rx, ch in enumerate(row):
            if ch == "X":
                silhouette.add((2 + rx, 3 + ry))
    # dark outline halo so the fossil pops out of the slab
    for (x, y) in silhouette:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if (x + dx, y + dy) not in silhouette:
                    putpx(img, x + dx, y + dy, outline + (255,))
    for (x, y) in silhouette:
        putpx(img, x, y, bone + (255,))
        if (x, y + 1) not in silhouette:
            putpx(img, x, y, bone_sh + (255,))
    for (x, y) in silhouette:
        if (x - 1, y) not in silhouette:
            putpx(img, x, y, bone_sh + (255,))
    rim = {
        "common": (150, 150, 150),
        "uncommon": (96, 178, 96),
        "rare": (86, 138, 214),
        "epic": (168, 92, 214),
        "legendary": (226, 158, 52),
    }[rarity]
    for x in range(2, 14):
        putpx(img, x, 14, rim + (255,))
    for y in range(2, 14):
        putpx(img, 14, y, rim + (255,))
    return img


def tex_egg(sp):
    img = blank()
    r = rng("egg", sp["key"])
    base = tuple(int(sp["egg_color"]["base"].lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    spots = tuple(int(sp["egg_color"]["spots"].lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))

    def m(x, y):
        dx, dy = x - 7.5, (y - 8.0) * 1.34
        return dx * dx + dy * dy <= 33

    outline_shape(img, m, base, shade(base, -0.34), r)
    for _ in range(16):
        x = r.randrange(3, 13)
        y = r.randrange(3, 14)
        if m(x, y):
            putpx(img, x, y, spots + (255,))
            if m(x + 1, y):
                putpx(img, x + 1, y, shade(spots, -0.15) + (255,))
    # highlight and contact shadow
    for (x, y) in [(4, 4), (5, 3), (5, 4)]:
        if m(x, y):
            putpx(img, x, y, shade(base, 0.5) + (255,))
    for x in range(3, 13):
        if m(x, 13):
            putpx(img, x, 13, shade(base, -0.4) + (255,))
    # rarity ring at the base
    rim = {
        "common": (150, 150, 150),
        "uncommon": (96, 178, 96),
        "rare": (86, 138, 214),
        "legendary": (226, 158, 52),
    }.get(sp["rarity_en"], (168, 92, 214))
    for x in range(5, 12):
        putpx(img, x, 14, rim + (255,))
    return img


def tex_spawn_egg(sp):
    img = blank()
    r = rng("spawnegg", sp["key"])
    base = tuple(int(sp["egg_color"]["base"].lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    spots = tuple(int(sp["egg_color"]["spots"].lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))

    def m(x, y):
        dx, dy = x - 8, (y - 8.5) * 1.22
        return dx * dx + dy * dy <= 30

    outline_shape(img, m, (238, 236, 228), (176, 172, 162), r)

    def m2(x, y):
        dx, dy = x - 8, (y - 8.5) * 1.45
        return dx * dx + dy * dy <= 21

    outline_shape(img, m2, base, shade(base, -0.3), r)
    for _ in range(11):
        x = r.randrange(4, 12)
        y = r.randrange(5, 13)
        if m2(x, y):
            putpx(img, x, y, spots + (255,))
    return img


ITEM_TEXTURE_BUILDERS = {
    "fossil_chip": tex_fossil_chip,
    "bone_shard": tex_bone_shard,
    "amber_inclusion": tex_amber,
    "nutrient_gel": tex_nutrient_gel,
    "genetic_matrix": tex_genetic_matrix,
    "excavation_shovel": tex_shovel,
    "brush": tex_brush,
    "fossil_scanner": tex_scanner,
    "field_case": tex_field_case,
}


def gen_item_textures():
    out = []
    for short, builder in ITEM_TEXTURE_BUILDERS.items():
        out.append(save(builder(), f"textures/items/paleo_{short}.png"))
    for sp in cm.SPECIES:
        out.append(save(tex_specimen(sp["key"], sp["rarity_en"]),
                        f"textures/items/paleo_specimen_{sp['key']}.png"))
        out.append(save(tex_egg(sp), f"textures/items/paleo_egg_{sp['key']}.png"))
        out.append(save(tex_spawn_egg(sp),
                        f"textures/items/paleo_spawn_egg_{sp['entity']}.png"))
    return out


# ===========================================================================
# 3. Entity textures, painted straight onto the generated box-UV atlas
# ===========================================================================
PALETTES = {
    "compsognathus": dict(
        wild=dict(dorsal=(112, 122, 74), base=(138, 144, 92), belly=(210, 200, 160),
                  accent=(74, 88, 54), horn=(226, 218, 190), eye=(24, 22, 18),
                  pattern="stripes"),
        bonded=dict(dorsal=(126, 134, 82), base=(158, 158, 100), belly=(226, 216, 174),
                    accent=(88, 100, 60), horn=(232, 224, 196), eye=(24, 22, 18),
                    pattern="stripes", collar=(196, 150, 74)),
        alert=dict(dorsal=(96, 104, 60), base=(120, 126, 78), belly=(196, 186, 148),
                   accent=(58, 70, 42), horn=(220, 212, 184), eye=(148, 40, 28),
                   pattern="stripes"),
    ),
    "triceratops": dict(
        wild=dict(dorsal=(112, 100, 82), base=(140, 126, 104), belly=(184, 170, 142),
                  accent=(154, 92, 58), horn=(232, 224, 198), eye=(30, 26, 20),
                  pattern="mottle", frill=(158, 96, 60), beak=(176, 158, 122)),
        bonded=dict(dorsal=(122, 112, 94), base=(152, 140, 116), belly=(196, 184, 156),
                    accent=(120, 148, 138), horn=(238, 232, 208), eye=(30, 26, 20),
                    pattern="mottle", frill=(168, 112, 74), beak=(186, 168, 132),
                    collar=(96, 152, 148)),
        alert=dict(dorsal=(96, 82, 68), base=(124, 108, 90), belly=(166, 150, 126),
                   accent=(182, 78, 46), horn=(228, 218, 190), eye=(156, 46, 26),
                   pattern="mottle", frill=(186, 84, 48), beak=(166, 148, 114)),
    ),
    "velociraptor": dict(
        wild=dict(dorsal=(84, 102, 108), base=(116, 132, 136), belly=(198, 192, 168),
                  accent=(48, 64, 70), horn=(226, 220, 196), eye=(212, 176, 44),
                  pattern="bands"),
        bonded=dict(dorsal=(94, 116, 108), base=(132, 150, 138), belly=(210, 204, 180),
                    accent=(56, 76, 70), horn=(232, 226, 202), eye=(216, 184, 56),
                    pattern="bands", collar=(188, 142, 66)),
        alert=dict(dorsal=(64, 82, 92), base=(94, 112, 122), belly=(176, 172, 152),
                   accent=(34, 48, 56), horn=(214, 208, 186), eye=(226, 74, 40),
                   pattern="bands"),
    ),
    "tyrannosaurus": dict(
        wild=dict(dorsal=(74, 54, 40), base=(116, 86, 62), belly=(176, 148, 112),
                  accent=(52, 38, 28), horn=(228, 220, 196), eye=(214, 158, 44),
                  pattern="scales"),
        bonded=dict(dorsal=(86, 66, 48), base=(130, 100, 72), belly=(190, 164, 128),
                    accent=(60, 46, 34), horn=(234, 228, 204), eye=(220, 176, 60),
                    pattern="scales", collar=(176, 132, 62)),
        alert=dict(dorsal=(58, 40, 30), base=(100, 70, 50), belly=(158, 132, 100),
                   accent=(40, 28, 20), horn=(222, 214, 190), eye=(232, 68, 34),
                   pattern="scales"),
    ),
}

# Which model "kind" tags use which palette slot.
KIND_SLOT = {
    "torso": "base", "neck": "base", "head": "base", "jaw": "belly",
    "tail": "base", "leg": "base", "foot": "belly", "arm": "base",
    "claw": "horn", "horn": "horn", "frill": "frill", "beak": "beak",
    "crest": "dorsal",
}


def box_uv_faces(u, v, w, h, l):
    """Bedrock box UV face rectangles: name -> (x, y, fw, fh)."""
    return {
        "top": (u + l, v, w, l),
        "bottom": (u + l + w, v, w, l),
        "west": (u, v + l, l, h),
        "north": (u + l, v + l, w, h),
        "east": (u + l + w, v + l, l, h),
        "south": (u + 2 * l + w, v + l, w, h),
    }


def paint_face(img, rect, colour_fn, r, noise=9):
    x0, y0, fw, fh = rect
    for fy in range(fh):
        for fx in range(fw):
            c = colour_fn(fx, fy, fw, fh)
            d = r.randint(-noise, noise)
            putpx(img, x0 + fx, y0 + fy,
                  (max(0, min(255, c[0] + d)), max(0, min(255, c[1] + d)),
                   max(0, min(255, c[2] + d)), 255))


def tagged_palette(base):
    pal = dict(base["wild"])
    pal["collar"] = (206, 178, 92)
    return pal


for _entity, _pal in PALETTES.items():
    _pal["tagged"] = tagged_palette(_pal)


def paint_entity(entity, variant, uv_map, tex_w, tex_h):
    pal = PALETTES[entity][variant]
    img = Image.new("RGBA", (tex_w, tex_h), (0, 0, 0, 0))
    r = rng("entity", entity, variant)

    # Model extents, used for countershading and pattern bands.
    ys = []
    zs = []
    for cube in uv_map:
        ox, oy, oz = cube["origin"]
        w, h, l = cube["size"]
        ys += [oy, oy + h]
        zs += [oz, oz + l]
    y_min, y_max = min(ys), max(ys)
    z_min, z_max = min(zs), max(zs)

    def pattern_amount(kind, fy, fh, y_abs):
        t = 0.0 if y_max == y_min else (y_abs - y_min) / (y_max - y_min)
        if pal["pattern"] == "stripes":
            return 1.0 if (int(fy + y_abs * 0.5) % 4) < 2 else 0.0
        if pal["pattern"] == "bands":
            return 1.0 if (int(y_abs) % 6) < 3 else 0.0
        if pal["pattern"] == "mottle":
            return 1.0 if ((int(fy * 1.7) + int(y_abs * 1.3)) % 7) < 3 else 0.0
        return 1.0 if ((fy + int(y_abs)) % 5) < 2 else 0.0

    for cube in uv_map:
        w, h, l = cube["size"]
        u, v = cube["uv"]
        ox, oy, oz = cube["origin"]
        kind = cube["kind"]
        bone = cube["bone"]
        slot = KIND_SLOT.get(kind, "base")
        base_col = pal.get(slot, pal["base"])
        faces = box_uv_faces(u, v, w, h, l)

        y_centre = oy + h / 2.0
        t = 0.0 if y_max == y_min else (y_centre - y_min) / (y_max - y_min)

        def face_colour(face, base_col=base_col, t=t, oy=oy, h=h, kind=kind, bone=bone):
            def fn(fx, fy, fw, fh):
                col = base_col
                if face == "top":
                    col = pal["dorsal"] if kind in ("torso", "neck", "tail", "head") else shade(base_col, -0.16)
                elif face == "bottom":
                    col = pal["belly"]
                elif face in ("west", "east"):
                    col = shade(base_col, -0.07)
                elif face == "north":
                    col = shade(base_col, 0.05)
                else:
                    col = base_col
                # countershading: darker towards the feet
                col = mix(col, pal["belly"], (1.0 - t) * 0.18)
                # pattern
                y_abs = oy + h - fy
                if pal["pattern"] and kind in ("torso", "neck", "tail", "leg", "head"):
                    if pattern_amount(kind, fy, fh, y_abs) > 0.5:
                        col = mix(col, pal["accent"], 0.42)
                return col
            return fn

        for face, rect in faces.items():
            paint_face(img, rect, face_colour(face), r, noise=8)

        # --- species details -------------------------------------------------
        if bone == "head" and kind == "head":
            # eyes on both side faces + brow shading on the front
            for face in ("west", "east"):
                x0, y0, fw, fh = faces[face]
                ex = max(0, int(fw * 0.32))
                ey = max(0, int(fh * 0.34))
                putpx(img, x0 + ex, y0 + ey, pal["eye"] + (255,))
                putpx(img, x0 + ex + 1, y0 + ey, shade(pal["eye"], 0.35) + (255,))
                putpx(img, x0 + ex, y0 + ey - 1 if ey > 0 else y0 + ey,
                      shade(pal["dorsal"], -0.25) + (255,))
            x0, y0, fw, fh = faces["north"]
            for i in range(fw):
                putpx(img, x0 + i, y0 + fh - 1, shade(pal["dorsal"], -0.2) + (255,))
        if bone == "jaw":
            # teeth line along the front edge of the lower jaw
            x0, y0, fw, fh = faces["north"]
            for i in range(fw):
                if i % 2 == 0:
                    putpx(img, x0 + i, y0, (244, 240, 224, 255))
        if kind == "frill":
            x0, y0, fw, fh = faces["south"]
            for i in range(fw):
                if i % 3 == 0:
                    for j in range(fh):
                        putpx(img, x0 + i, y0 + j, shade(pal["frill"], 0.18) + (255,))
            for i in range(fw):
                putpx(img, x0 + i, y0, shade(pal["horn"], -0.25) + (255,))
        if kind == "horn":
            for face, rect in faces.items():
                paint_face(img, rect, lambda fx, fy, fw, fh: shade(pal["horn"], -0.04 * fy),
                           r, noise=5)
        if kind == "claw":
            for face, rect in faces.items():
                paint_face(img, rect, lambda fx, fy, fw, fh: shade(pal["horn"], -0.06 * fy),
                           r, noise=4)
        if kind == "crest":
            for face, rect in faces.items():
                paint_face(img, rect,
                           lambda fx, fy, fw, fh: mix(pal["dorsal"], pal["accent"], 0.35),
                           r, noise=6)
        if "collar" in pal and bone == "neck":
            x0, y0, fw, fh = faces["north"]
            for i in range(fw):
                for j in range(min(2, fh)):
                    putpx(img, x0 + i, y0 + j, pal["collar"] + (255,))

    # studied individuals wear a small archive field-tag band on the tail base
    if variant == "tagged":
        for cube in uv_map:
            if cube["bone"] == "tail_1":
                faces = box_uv_faces(cube["uv"][0], cube["uv"][1],
                                     cube["size"][0], cube["size"][1],
                                     cube["size"][2])
                x0, y0, fw, fh = faces["south"]
                for i in range(fw):
                    putpx(img, x0 + i, y0 + fh - 1, (206, 178, 92, 255))
                    putpx(img, x0 + i, y0 + fh - 2, (150, 122, 58, 255))
                x0, y0, fw, fh = faces["north"]
                for i in range(fw):
                    putpx(img, x0 + i, y0 + fh - 1, (206, 178, 92, 255))
                break
    return img


def gen_entity_textures():
    out = []
    layout = json.load(open(os.path.join(HERE, "uv_layout.json"), encoding="utf-8"))
    for sp in cm.SPECIES:
        entity = sp["entity"]
        tex_w, tex_h = layout[entity]["texture"]
        uv_map = layout[entity]["cubes"]
        for variant in ("wild", "bonded", "alert", "tagged"):
            img = paint_entity(entity, variant, uv_map, tex_w, tex_h)
            out.append(save(img, f"textures/entity/paleo_{entity}_{variant}.png"))
    return out


# ===========================================================================
# 4. Pack icons
# ===========================================================================
def pack_icon(kind):
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 255))
    r = rng("icon", kind)
    if kind == "bp":
        sky = ((38, 30, 24), (86, 62, 40))
    else:
        sky = ((26, 40, 44), (62, 96, 92))
    for y in range(size):
        t = y / size
        c = mix(sky[0], sky[1], t)
        for x in range(size):
            d = r.randint(-5, 5)
            putpx(img, x, y, (c[0] + d, c[1] + d, c[2] + d, 255))
    # strata bands
    for i in range(7):
        y0 = int(size * (0.42 + i * 0.083))
        h = int(size * 0.05)
        c = mix((150, 132, 104), (84, 70, 54), i / 6.0)
        for y in range(y0, min(size, y0 + h)):
            for x in range(size):
                d = r.randint(-10, 10)
                putpx(img, x, y, (c[0] + d, c[1] + d, c[2] + d, 255))
    # big bone silhouette
    bone = (236, 230, 210)
    for i in range(9):
        cx = int(size * (0.16 + i * 0.085))
        cy = int(size * (0.60 + (i % 2) * 0.02))
        rad = int(size * 0.028)
        for y in range(cy - rad, cy + rad + 1):
            for x in range(cx - rad, cx + rad + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= rad * rad:
                    putpx(img, x, y, bone + (255,))
        for y in range(cy, cy + int(size * 0.16)):
            for x in range(cx - 3, cx + 4):
                putpx(img, x, y, shade(bone, -0.12) + (255,))
    # amber gem
    cx, cy = int(size * 0.76), int(size * 0.30)
    rad = int(size * 0.10)
    for y in range(cy - rad, cy + rad + 1):
        for x in range(cx - rad, cx + rad + 1):
            dx, dy = (x - cx) / rad, (y - cy) / (rad * 1.15)
            if dx * dx + dy * dy <= 1.0:
                t = (dx + dy) * 0.5
                col = mix((246, 200, 96), (150, 92, 22), max(0.0, min(1.0, t + 0.4)))
                putpx(img, x, y, col + (255,))
    putpx(img, cx - rad // 3, cy - rad // 3, (255, 240, 190, 255))
    putpx(img, cx - rad // 3 + 1, cy - rad // 3, (255, 246, 214, 255))
    # frame
    d = ImageDraw.Draw(img)
    d.rectangle([4, 4, size - 5, size - 5], outline=(20, 18, 16, 255), width=4)
    d.rectangle([10, 10, size - 11, size - 11], outline=(178, 148, 92, 255), width=2)
    return img


def main():
    written = []
    written += gen_block_textures()
    written += gen_item_textures()
    written += gen_entity_textures()
    written.append(save(pack_icon("bp"), "pack_icon.png", root=BP))
    written.append(save(pack_icon("rp"), "pack_icon.png", root=RP))
    print(f"[gen_textures] wrote {len(written)} images")


if __name__ == "__main__":
    main()
