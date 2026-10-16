#!/usr/bin/env sh
# Vendors the official Mojang Bedrock JSON schemas into tools/.schemas so that
# tools/validate.py can run the schema layer offline afterwards.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -d "$DIR/.schemas/schemas" ]; then
  echo "schemas already vendored at $DIR/.schemas"
  exit 0
fi
TMP="$(mktemp -d)"
git clone --depth 1 --filter=blob:none --sparse https://github.com/Mojang/bedrock-schemas.git "$TMP/bedrock-schemas"
cd "$TMP/bedrock-schemas"
git sparse-checkout set schemas
mkdir -p "$DIR/.schemas"
cp -r schemas "$DIR/.schemas/schemas"
echo "schemas vendored at $DIR/.schemas/schemas"

# Forms oficiais dos componentes de entidade (MicrosoftDocs/minecraft-creator):
# alimentam tools/check_entity_fields.py com a lista de campos de cada
# componente.  Sem eles a checagem roda só na camada version-gated.
cd "$TMP"
git clone --depth 1 --filter=blob:none --sparse https://github.com/MicrosoftDocs/minecraft-creator.git "$TMP/minecraft-creator"
cd "$TMP/minecraft-creator"
git sparse-checkout set content/forms/entity
python3 "$DIR/vendor_forms.py" "$TMP/minecraft-creator" || echo "WARN: forms de entidade nao vendorados"

rm -rf "$TMP"
