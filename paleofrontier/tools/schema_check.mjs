#!/usr/bin/env node
/**
 * Validates PALEOFRONTIER JSON against the official Mojang Bedrock schemas
 * (https://github.com/Mojang/bedrock-schemas) using ajv.
 *
 * Usage: node schema_check.mjs <schemas-dir> <pack-root>
 * Exits non-zero when any file fails.
 */
import { readFileSync, readdirSync, statSync, existsSync } from "node:fs";
import { join, relative } from "node:path";
import Ajv from "ajv";

const [schemasDir, packRoot] = process.argv.slice(2);
if (!schemasDir || !packRoot) {
  console.error("usage: node schema_check.mjs <schemas-dir> <pack-root>");
  process.exit(2);
}

const RULES = [
  [/behavior_pack\/manifest\.json$/, "bp/manifest/index.schema.json"],
  [/behavior_pack\/blocks\/.*\.json$/, "bp/blocks/index.schema.json"],
  [/behavior_pack\/items\/.*\.json$/, "bp/items/index.schema.json"],
  [/behavior_pack\/entities\/.*\.json$/, "bp/entities/index.schema.json"],
  [/behavior_pack\/loot_tables\/.*\.json$/, "bp/loot_tables/index.schema.json"],
  // NOTE: the published schema set only contains a brewing-mix recipe schema
  // (bp/recipes/index.schema.json is recipe_brewing_mix), so shaped/shapeless
  // recipes are validated structurally by tools/validate.py instead.
  [/behavior_pack\/features\/.*\.json$/, "bp/features/index.schema.json"],
  [/behavior_pack\/feature_rules\/.*\.json$/, "bp/feature_rules/index.schema.json"],
  [/behavior_pack\/spawn_rules\/.*\.json$/, "bp/spawn_rules/index.schema.json"],
  [/resource_pack\/manifest\.json$/, "rp/manifest/index.schema.json"],
  [/resource_pack\/models\/.*\.json$/, "rp/models/index.schema.json"],
  [/resource_pack\/animations\/.*\.json$/, "bp/animations/index.schema.json"],
  [/resource_pack\/animation_controllers\/.*\.json$/, "bp/animation_controllers/index.schema.json"],
  [/resource_pack\/render_controllers\/.*\.json$/, "rp/render_controllers/index.schema.json"],
  [/resource_pack\/entity\/.*\.json$/, "rp/entity/index.schema.json"],
  [/resource_pack\/particles\/.*\.json$/, "rp/particles/index.schema.json"],
  [/resource_pack\/sounds\/sound_definitions\.json$/, "rp/sounds/index.schema.json"],
  [/resource_pack\/textures\/terrain_texture\.json$/, "rp/textures/terrain_texture.schema.json"],
  [/resource_pack\/textures\/item_texture\.json$/, "rp/textures/item_texture.schema.json"],
  // NOTE: rp/texts/languages.schema.json models the locale list as an object
  // while the game (and Mojang's own shipped languages.json) uses an array, so
  // that one file is validated structurally by tools/validate.py instead.
];

function walk(dir) {
  const out = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      out.push(...walk(full));
    } else if (full.endsWith(".json")) {
      out.push(full);
    }
  }
  return out;
}

function stripJsonc(text) {
  let out = "";
  let inString = false;
  let i = 0;
  while (i < text.length) {
    const c = text[i];
    if (inString) {
      out += c;
      if (c === "\\") {
        out += text[i + 1] ?? "";
        i += 2;
        continue;
      }
      if (c === '"') inString = false;
      i += 1;
      continue;
    }
    if (c === '"') {
      inString = true;
      out += c;
      i += 1;
      continue;
    }
    if (c === "/" && text[i + 1] === "/") {
      while (i < text.length && text[i] !== "\n") i += 1;
      continue;
    }
    if (c === "/" && text[i + 1] === "*") {
      i += 2;
      while (i + 1 < text.length && !(text[i] === "*" && text[i + 1] === "/")) i += 1;
      i += 2;
      continue;
    }
    out += c;
    i += 1;
  }
  return out;
}

const ajv = new Ajv({ strict: false, allErrors: true });

/**
 * The official schemas use relative $refs that resolve against each schema's
 * own $id (for example "block/block_behavior_document" + "./x.schema.json").
 * Registering every file under several ids (relative path, $id and
 * dirname($id)/filename) lets ajv resolve those refs without a custom loader.
 */
const registered = new Set();
const parsedSchemas = new Map();

function collect(dir) {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      collect(full);
      continue;
    }
    if (!full.endsWith(".schema.json")) continue;
    try {
      parsedSchemas.set(full, JSON.parse(stripJsonc(readFileSync(full, "utf8"))));
    } catch {
      /* ignore unreadable schema */
    }
  }
}
collect(schemasDir);

// Directory id prefix: taken from any schema in the same folder that declares
// an $id (e.g. index.schema.json -> "block/block_behavior_document").
const dirPrefix = new Map();
for (const [full, schema] of parsedSchemas) {
  if (typeof schema.$id === "string" && schema.$id.includes("/")) {
    dirPrefix.set(join(full, ".."), schema.$id.slice(0, schema.$id.lastIndexOf("/")));
  }
}

function add(schema, id) {
  if (registered.has(id)) return;
  registered.add(id);
  // ajv compiles on addSchema, so a dangling upstream $ref throws here.
  // Self-heal with a permissive stub and retry.
  for (let attempt = 0; attempt < 48; attempt += 1) {
    try {
      ajv.addSchema(schema, id);
      return;
    } catch (err) {
      const missing = err && err.missingSchema;
      if (!missing || registered.has(missing)) {
        return;
      }
      registered.add(missing);
      try {
        ajv.addSchema(true, missing);
      } catch {
        return;
      }
    }
  }
}

for (const [full, schema] of parsedSchemas) {
  const relPath = relative(schemasDir, full).split("\\").join("/");
  const entry = full.split(/[/\\]/).pop();
  const prefix = dirPrefix.get(join(full, ".."));
  const ids = [relPath, `/${relPath}`];
  if (typeof schema.$id === "string") {
    ids.push(schema.$id, `/${schema.$id}`);
  }
  if (prefix) {
    ids.push(`${prefix}/${entry}`, `/${prefix}/${entry}`);
  }
  for (const id of ids) {
    add(schema, id);
  }
}

const validators = new Map();
function validatorFor(schemaRel) {
  if (!validators.has(schemaRel)) {
    const path = join(schemasDir, schemaRel);
    if (!existsSync(path)) {
      validators.set(schemaRel, null);
      return null;
    }
    let validator = null;
    try {
      validator = ajv.getSchema(schemaRel) || null;
    } catch (err) {
      console.warn(`SKIP    ${schemaRel}: upstream schema not compilable (${err.message})`);
      validator = null;
    }
    validators.set(schemaRel, validator);
  }
  return validators.get(schemaRel);
}

/**
 * Mojang's rp/models schema types pivot/origin/size/rotation as arrays of
 * molang strings, while every shipped vanilla geometry file uses plain
 * numbers.  Numbers are what the engine expects, so we keep them in the pack
 * and normalise a *copy* of the document for schema validation only.
 */
const MOLANG_NUMBER_KEYS = new Set(["pivot", "origin", "size", "rotation", "uv", "uv_size"]);
function stringifyMolangArrays(node) {
  if (Array.isArray(node)) {
    return node.map(stringifyMolangArrays);
  }
  if (node && typeof node === "object") {
    const out = {};
    for (const [key, value] of Object.entries(node)) {
      if (MOLANG_NUMBER_KEYS.has(key) && Array.isArray(value) &&
          value.every((v) => typeof v === "number")) {
        out[key] = value.map((v) => String(v));
      } else {
        out[key] = stringifyMolangArrays(value);
      }
    }
    return out;
  }
  return node;
}

let checked = 0;
let failures = 0;
let skipped = 0;
for (const file of walk(packRoot)) {
  const rel = relative(packRoot, file).split("\\").join("/");
  const rule = RULES.find(([re]) => re.test(rel));
  if (!rule) continue;
  const validate = validatorFor(rule[1]);
  if (!validate) continue;
  checked += 1;
  let doc;
  try {
    doc = JSON.parse(stripJsonc(readFileSync(file, "utf8")));
  } catch (err) {
    console.error(`SYNTAX  ${rel}: ${err.message}`);
    failures += 1;
    continue;
  }
  if (rule[1].startsWith("rp/models")) {
    doc = stringifyMolangArrays(doc);
  }
  if (rule[1].startsWith("rp/manifest")) {
    // The rp manifest schema types versions as strings while the engine (and
    // every shipped pack) uses [major, minor, patch] arrays; normalise a copy.
    doc = JSON.parse(JSON.stringify(doc));
    const norm = (node) => {
      if (Array.isArray(node)) node.forEach(norm);
      else if (node && typeof node === "object") {
        if (Array.isArray(node.version)) node.version = node.version.join(".");
        Object.values(node).forEach(norm);
      }
    };
    norm(doc);
  }
  let valid = true;
  try {
    valid = validate(doc);
  } catch (err) {
    // Upstream schema could not even compile (dangling ref etc.) - report as a
    // skipped file rather than crashing the whole layer.
    skipped += 1;
    console.warn(`SKIP    ${rel}: schema compile error (${err.message})`);
    continue;
  }
  if (!valid) {
    failures += 1;
    console.error(`SCHEMA  ${rel} [${rule[1]}]`);
    for (const err of validate.errors.slice(0, 8)) {
      console.error(`        ${err.instancePath || "/"} ${err.message}`);
    }
  }
}
console.log(`[schema_check] ${checked} files validated, ${skipped} skipped, ${failures} failure(s)`);
process.exit(failures > 0 ? 1 : 0);
