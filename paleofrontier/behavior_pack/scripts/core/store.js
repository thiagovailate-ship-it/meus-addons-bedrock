/**
 * PALEOFRONTIER - persistence layer.
 *
 * Everything the add-on remembers is stored in officially supported dynamic
 * properties:
 *
 *  - world  scope  -> shared across every player in the world
 *      paleo.world.registry    identified species + global expedition stats
 *      paleo.world.incubators  live incubation sessions keyed by block position
 *  - player scope  -> personal, travels with that player's save data
 *      paleo.player.journal    the field journal (finds, studies, hatchings)
 *
 * Writes are batched: mutations only mark a scope dirty and a low-frequency
 * flush persists them (plus an immediate flush on leave / shutdown), so the
 * add-on never rewrites the same state every tick.
 */

import { world } from "@minecraft/server";
import * as log from "./log.js";

const WORLD_REGISTRY = "paleo.world.registry";
const WORLD_INCUBATORS = "paleo.world.incubators";
const PLAYER_JOURNAL_PREFIX = "paleo.player.journal";

/** Dynamic property strings are capped at 32767 bytes; stay well below it. */
const SERIAL_LIMIT = 28000;

function emptyRegistry() {
  return { v: 1, identified: {}, stats: { mined: 0, hatched: 0, studied: 0 } };
}

function emptyIncubators() {
  return { v: 1, items: [] };
}

function emptyJournal() {
  return { v: 1, found: {}, studied: {}, hatched: {}, raised: {}, welcomed: false };
}

const state = {
  registry: emptyRegistry(),
  incubators: emptyIncubators(),
  /** @type {Map<string, object>} player.id -> journal */
  journals: new Map(),
  dirty: new Set(),
  loaded: false,
};

function read(scope, fallbackFactory) {
  const raw = world.getDynamicProperty(scope);
  if (typeof raw !== "string" || raw.length === 0) {
    return fallbackFactory();
  }
  try {
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") {
      return fallbackFactory();
    }
    return Object.assign(fallbackFactory(), parsed);
  } catch (err) {
    log.warn("store.read", `${scope} held unreadable JSON, starting fresh`);
    return fallbackFactory();
  }
}

function write(scope, value) {
  const text = JSON.stringify(value);
  if (text.length > SERIAL_LIMIT) {
    log.warn("store.write", `${scope} exceeded ${SERIAL_LIMIT} bytes, trimming`);
    trim(value);
    return write(scope, value);
  }
  world.setDynamicProperty(scope, text);
}

function trim(value) {
  // Keep the most recent entries only.
  if (value && value.items && Array.isArray(value.items)) {
    value.items = value.items.slice(-48);
  }
  if (value && value.found) {
    const keys = Object.keys(value.found);
    for (const key of keys.slice(0, Math.max(0, keys.length - 8))) {
      delete value.found[key];
    }
  }
}

export function loadWorld() {
  state.registry = read(WORLD_REGISTRY, emptyRegistry);
  state.incubators = read(WORLD_INCUBATORS, emptyIncubators);
  state.loaded = true;
}

export function registry() {
  if (!state.loaded) {
    loadWorld();
  }
  return state.registry;
}

export function incubators() {
  if (!state.loaded) {
    loadWorld();
  }
  return state.incubators;
}

export function journalFor(player) {
  let journal = state.journals.get(player.id);
  if (!journal) {
    const raw = player.getDynamicProperty(PLAYER_JOURNAL_PREFIX);
    if (typeof raw === "string" && raw.length > 0) {
      try {
        journal = Object.assign(emptyJournal(), JSON.parse(raw));
      } catch (err) {
        log.warn("store.journal", `unreadable journal for ${player.name}`);
        journal = emptyJournal();
      }
    } else {
      journal = emptyJournal();
    }
    state.journals.set(player.id, journal);
  }
  return journal;
}

export function forgetPlayer(playerId) {
  state.journals.delete(playerId);
}

export function markDirty(scope) {
  state.dirty.add(scope);
}

export function dirtyCount() {
  return state.dirty.size;
}

/** Persists whatever changed since the last flush. Cheap when nothing did. */
export function flush() {
  if (state.dirty.size === 0) {
    return;
  }
  log.guard("store.flush", () => {
    if (state.dirty.has("registry")) {
      write(WORLD_REGISTRY, state.registry);
    }
    if (state.dirty.has("incubators")) {
      write(WORLD_INCUBATORS, state.incubators);
    }
    if (state.dirty.has("journals")) {
      for (const player of world.getAllPlayers()) {
        const journal = state.journals.get(player.id);
        if (journal) {
          const text = JSON.stringify(journal);
          if (text.length <= SERIAL_LIMIT) {
            player.setDynamicProperty(PLAYER_JOURNAL_PREFIX, text);
          }
        }
      }
    }
    state.dirty.clear();
  });
}

/** Adds n to a journal counter bucket, e.g. bumpJournal(player,'found','compy'). */
export function bumpJournal(player, bucket, key, n = 1) {
  const journal = journalFor(player);
  const bag = journal[bucket] || (journal[bucket] = {});
  bag[key] = (bag[key] || 0) + n;
  markDirty("journals");
  return bag[key];
}

export function bumpStat(key, n = 1) {
  const stats = registry().stats;
  stats[key] = (stats[key] || 0) + n;
  markDirty("registry");
  return stats[key];
}
