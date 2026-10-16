#!/usr/bin/env python3
"""Offline preview renderer for PALEOFRONTIER entity models.

Renders the generated geometry + texture atlas to a PNG so models can be
inspected without launching Minecraft.  Pure software renderer (orthographic
projection, painter's algorithm, affine texture mapping).

Usage:  python3 tools/preview_model.py [out.png]
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RP = os.path.join(ROOT, "resource_pack")


def rotation_matrix(yaw_deg, pitch_deg):
    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    return rx @ ry


def face_defs(u, v, w, h, l):
    """(name, corners[4] in cube-local, uv_quad[4] matching the corner order)."""
    return [
        ("top", [(0, h, 0), (w, h, 0), (w, h, l), (0, h, l)],
         [(u + l, v), (u + l + w, v), (u + l + w, v + l), (u + l, v + l)]),
        ("bottom", [(0, 0, l), (w, 0, l), (w, 0, 0), (0, 0, 0)],
         [(u + l + w, v), (u + l + 2 * w, v), (u + l + 2 * w, v + l), (u + l + w, v + l)]),
        ("north", [(w, 0, 0), (w, h, 0), (0, h, 0), (0, 0, 0)],
         [(u + l, v + l), (u + l, v + l + h), (u + l + w, v + l + h), (u + l + w, v + l)]),
        ("south", [(0, 0, l), (0, h, l), (w, h, l), (w, 0, l)],
         [(u + 2 * l + w, v + l), (u + 2 * l + w, v + l + h),
          (u + 2 * l + 2 * w, v + l + h), (u + 2 * l + 2 * w, v + l)]),
        ("west", [(0, 0, 0), (0, h, 0), (0, h, l), (0, 0, l)],
         [(u, v + l), (u, v + l + h), (u + l, v + l + h), (u + l, v + l)]),
        ("east", [(w, 0, l), (w, h, l), (w, h, 0), (w, 0, 0)],
         [(u + l + w, v + l), (u + l + w, v + l + h),
          (u + 2 * l + w, v + l + h), (u + 2 * l + w, v + l)]),
    ]


def draw_quad(canvas, alpha, poly, texture, uv_quad, scale):
    """Affine-map uv_quad (4 texture coords) onto poly (4 screen coords)."""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    x0, x1 = int(math.floor(min(xs))), int(math.ceil(max(xs))) + 1
    y0, y1 = int(math.floor(min(ys))), int(math.ceil(max(ys))) + 1
    w = x1 - x0
    h = y1 - y0
    if w <= 0 or h <= 0:
        return
    p = np.array(poly, dtype=float) - np.array([x0, y0], dtype=float)
    t = np.array(uv_quad, dtype=float)
    # least squares affine: [u,v,1] = M @ [x,y,1]
    A = np.column_stack([p[:, 0], p[:, 1], np.ones(4)])
    sol_u, *_ = np.linalg.lstsq(A, t[:, 0], rcond=None)
    sol_v, *_ = np.linalg.lstsq(A, t[:, 1], rcond=None)
    yy, xx = np.mgrid[0:h, 0:w]
    inside = point_in_poly(xx + x0 + 0.5, yy + y0 + 0.5, poly)
    us = sol_u[0] * (xx + 0.5) + sol_u[1] * (yy + 0.5) + sol_u[2]
    vs = sol_v[0] * (xx + 0.5) + sol_v[1] * (yy + 0.5) + sol_v[2]
    uidx = np.clip(np.round(us).astype(int), 0, texture.shape[1] - 1)
    vidx = np.clip(np.round(vs).astype(int), 0, texture.shape[0] - 1)
    cols = texture[vidx, uidx]
    region = canvas[y0:y1, x0:x1]
    aregion = alpha[y0:y1, x0:x1]
    mask = inside & (cols[:, :, 3] > 10)
    region[mask] = cols[mask]
    aregion[mask] = 255


def point_in_poly(xx, yy, poly):
    inside = np.zeros(xx.shape, dtype=bool)
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        cond = ((yi > yy) != (yj > yy)) & (xx < (xj - xi) * (yy - yi) / (yj - yi + 1e-12) + xi)
        inside ^= cond
        j = i
    return inside


def render_entity(entity, yaw=35, pitch=18, canvas_size=(320, 320), zoom=None,
                  variant="wild", baby=False):
    geo_path = os.path.join(RP, "models", "entity", f"paleo_{entity}.geo.json")
    tex_path = os.path.join(RP, "textures", "entity", f"paleo_{entity}_{variant}.png")
    geo = json.load(open(geo_path, encoding="utf-8"))["minecraft:geometry"]
    block = geo[1] if baby else geo[0]
    texture = np.array(Image.open(tex_path).convert("RGBA"))

    rot = rotation_matrix(yaw, pitch)
    # bone pivots form a parent-relative chain; cube origins are relative to
    # their bone pivot, so resolve absolute model-space positions first.
    world_pivot = {}
    for bone in block["bones"]:
        parent = bone.get("parent")
        base = world_pivot.get(parent, (0.0, 0.0, 0.0))
        pv = bone.get("pivot", [0, 0, 0])
        world_pivot[bone["name"]] = (base[0] + pv[0], base[1] + pv[1], base[2] + pv[2])

    faces = []
    for bone in block["bones"]:
        wp = world_pivot[bone["name"]]
        for cube in bone.get("cubes", []):
            ox = cube["origin"][0] + wp[0]
            oy = cube["origin"][1] + wp[1]
            oz = cube["origin"][2] + wp[2]
            w, h, l = cube["size"]
            u, v = cube["uv"]
            for name, corners, uvq in face_defs(u, v, w, h, l):
                world = [(ox + cx, oy + cy, oz + cz) for (cx, cy, cz) in corners]
                cam = [rot @ np.array(p, dtype=float) for p in world]
                depth = float(np.mean([c[2] for c in cam]))
                faces.append((depth, cam, uvq))
    faces.sort(key=lambda f: f[0])

    all_pts = [c for _, cam, _ in faces for c in cam]
    xs = [p[0] for p in all_pts]
    ys = [p[1] for p in all_pts]
    span = max(max(xs) - min(xs), max(ys) - min(ys))
    scale = zoom or (min(canvas_size) * 0.82 / max(span, 1))
    cx = (max(xs) + min(xs)) / 2
    cy = (max(ys) + min(ys)) / 2

    canvas = np.zeros((canvas_size[1], canvas_size[0], 4), dtype=np.uint8)
    canvas[:, :] = (28, 28, 32, 255)
    alpha = np.zeros((canvas_size[1], canvas_size[0]), dtype=np.uint8)

    for depth, cam, uvq in faces:
        poly = [(canvas_size[0] / 2 + (p[0] - cx) * scale,
                 canvas_size[1] / 2 - (p[1] - cy) * scale) for p in cam]
        area = 0.0
        for i in range(4):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % 4]
            area += x1 * y2 - x2 * y1
        if area <= 0:
            continue
        draw_quad(canvas, alpha, poly, texture, uvq, scale)
        # simple directional shading
        n = np.cross(np.array(cam[1]) - np.array(cam[0]), np.array(cam[3]) - np.array(cam[0]))
        nl = np.linalg.norm(n)
        if nl > 1e-6:
            n = n / nl
            light = np.array([0.35, 0.75, -0.55])
            light = light / np.linalg.norm(light)
            lamb = abs(float(np.dot(n, light)))
            factor = 0.55 + 0.45 * lamb
            ys_i = [int(p[1]) for p in poly]
            xs_i = [int(p[0]) for p in poly]
            y0, y1 = max(0, min(ys_i)), min(canvas.shape[0], max(ys_i) + 1)
            x0, x1 = max(0, min(xs_i)), min(canvas.shape[1], max(xs_i) + 1)
            region = canvas[y0:y1, x0:x1]
            amask = alpha[y0:y1, x0:x1] > 0
            yy, xx = np.mgrid[y0:y1, x0:x1]
            inside = point_in_poly(xx + 0.5, yy + 0.5, poly) & amask
            region[inside, :3] = np.clip(region[inside, :3] * factor, 0, 255).astype(np.uint8)
    return Image.fromarray(canvas, "RGBA")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, ".review", "model_preview.png")
    entities = ["compsognathus", "triceratops", "velociraptor", "tyrannosaurus"]
    views = [(35, 16), (210, 12), (60, 22), (300, 14)]
    cell = 300
    sheet = Image.new("RGBA", (cell * 2, cell * 2), (20, 20, 24, 255))
    for i, (entity, (yaw, pitch)) in enumerate(zip(entities, views)):
        img = render_entity(entity, yaw=yaw, pitch=pitch, canvas_size=(cell, cell))
        sheet.paste(img, ((i % 2) * cell, (i // 2) * cell))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out)
    print("[preview_model] wrote", out)


if __name__ == "__main__":
    main()
