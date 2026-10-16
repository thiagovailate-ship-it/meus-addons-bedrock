#!/usr/bin/env sh
# Regenera, valida, simula e empacota o PALEOFRONTIER.
set -e
cd "$(dirname "$0")/.."

# escolhe um python com Pillow/numpy/soundfile disponiveis
if [ -n "$PY" ]; then :
elif python3 -c "import PIL, numpy, soundfile" 2>/dev/null; then PY=python3
elif [ -x ../.venv/bin/python ] && ../.venv/bin/python -c "import PIL, numpy, soundfile" 2>/dev/null; then PY=../.venv/bin/python
elif [ -x /home/user/.venv/bin/python ]; then PY=/home/user/.venv/bin/python
else PY=python3
fi
echo "== python: $PY"

# schemas oficiais + forms de componentes (opcionais; habilitam as camadas 1 e 6)
if [ ! -d tools/.schemas/schemas ] || [ ! -f tools/.forms/entity_fields.json ]; then
  sh tools/fetch_schemas.sh || echo "WARN: referencias oficiais indisponiveis; camadas 1/6 reduzidas"
fi

$PY tools/gen_bp.py
$PY tools/gen_rp.py
$PY tools/gen_geometry.py
$PY tools/gen_textures.py
$PY tools/gen_sounds.py
$PY tools/validate.py
node tools/simulate.mjs
$PY tools/build.py
echo "== tudo pronto: PALEOFRONTIER.mcaddon"
