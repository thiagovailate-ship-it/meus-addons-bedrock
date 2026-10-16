#!/usr/bin/env python3
"""Packages PALEOFRONTIER for import into Minecraft Bedrock.

Outputs:
  paleofrontier/PALEOFRONTIER.mcaddon   double pack bundle (import this)
  paleofrontier/dist/paleofrontier_bp.mcpack
  paleofrontier/dist/paleofrontier_rp.mcpack

Usage: python3 tools/build.py
"""
from __future__ import annotations

import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BP = os.path.join(ROOT, "behavior_pack")
RP = os.path.join(ROOT, "resource_pack")
OUT_ADDON = os.path.join(ROOT, "PALEOFRONTIER.mcaddon")
DIST = os.path.join(ROOT, "dist")

IGNORED_DIRS = {"node_modules", ".schemas", "__pycache__", ".git"}
IGNORED_FILES = {".DS_Store", "Thumbs.db"}

# O zip grava o mtime de cada entrada, entao o SHA-256 do .mcaddon mudava
# conforme a hora em que os arquivos tinham sido gerados - mesmo com o conteudo
# identico.  Com data fixa (e percurso ordenado) o artefato passa a ser
# reproduzivel byte a byte, e o hash publicado no release pode ser conferido por
# qualquer pessoa que rebuildar o pacote.  O cliente Bedrock ignora o mtime.
FIXED_DATE_TIME = (1980, 1, 1, 0, 0, 0)


def add_pack(zf, pack_dir, arc_prefix):
    count = 0
    for dirpath, dirnames, filenames in os.walk(pack_dir):
        # ordenar tambem os diretorios: os.walk nao garante ordem entre eles
        dirnames[:] = sorted(d for d in dirnames if d not in IGNORED_DIRS)
        for name in sorted(filenames):
            if name in IGNORED_FILES:
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, pack_dir).replace(os.sep, "/")
            info = zipfile.ZipInfo(f"{arc_prefix}/{rel}", date_time=FIXED_DATE_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            with open(full, "rb") as handle:
                zf.writestr(info, handle.read())
            count += 1
    return count


def main():
    os.makedirs(DIST, exist_ok=True)
    with zipfile.ZipFile(OUT_ADDON, "w", zipfile.ZIP_DEFLATED) as zf:
        bp_files = add_pack(zf, BP, "behavior_pack")
        rp_files = add_pack(zf, RP, "resource_pack")
    with zipfile.ZipFile(os.path.join(DIST, "paleofrontier_bp.mcpack"), "w",
                         zipfile.ZIP_DEFLATED) as zf:
        add_pack(zf, BP, ".")
    with zipfile.ZipFile(os.path.join(DIST, "paleofrontier_rp.mcpack"), "w",
                         zipfile.ZIP_DEFLATED) as zf:
        add_pack(zf, RP, ".")
    size = os.path.getsize(OUT_ADDON)
    print(f"[build] PALEOFRONTIER.mcaddon: {bp_files} BP + {rp_files} RP files, "
          f"{size / 1024:.0f} KiB")
    print(f"[build] dist/paleofrontier_bp.mcpack, dist/paleofrontier_rp.mcpack")


if __name__ == "__main__":
    main()
