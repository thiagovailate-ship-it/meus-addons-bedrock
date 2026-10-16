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
rm -rf "$TMP"
echo "schemas vendored at $DIR/.schemas/schemas"
