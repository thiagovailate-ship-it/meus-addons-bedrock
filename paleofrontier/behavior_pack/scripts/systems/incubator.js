/**
 * PALEOFRONTIER - incubation.
 *
 * The incubator block carries no inventory of its own: a viable egg is
 * consumed from the player when incubation starts and a session record is kept
 * in the world-scoped registry, keyed by the block position.  That makes the
 * state persistent (it survives leaving and re-entering the world) and makes
 * breaking the block a well defined event - the egg is refunded exactly once,
 * progress is lost, and nothing can be duplicated.
 *
 * Progress only accrues while the chamber sits in a loaded chunk, and a warm
 * (light level >= 10) chamber runs 25% faster.  Both are reported in the UI.
 */

import { ItemStack, world } from "@minecraft/server";
import {
  BLOCKS,
  SPECIES_BY_KEY,
  SPECIES_BY_EGG,
  INCUBATOR_STAGE_STATE,
  SOUNDS,
  PARTICLES,
} from "../data/content.js";
import * as store from "../core/store.js";
import * as inv from "../core/inventory.js";
import * as log from "../core/log.js";
import { nowMs } from "../core/scheduler.js";
import { args } from "../core/text.js";

/** Never credit more than 5s of progress per tick burst, so time spent away
 *  from an unloaded chamber does not teleport incubation forward. */
const MAX_CREDIT_MS = 5000;
const TICK_MS = 2000;

export function keyFor(block) {
  const loc = block.location;
  return `${block.dimension.id}|${loc.x}|${loc.y}|${loc.z}`;
}

export function entryAt(key) {
  return store.incubators().items.find((e) => e.key === key);
}

export function setStage(block, stage) {
  log.guard("incubator.stage", () => {
    const current = block.permutation.getState(INCUBATOR_STAGE_STATE);
    if (current !== stage) {
      block.setPermutation(block.permutation.withState(INCUBATOR_STAGE_STATE, stage));
    }
  });
}

export function start(player, block, eggId) {
  const species = SPECIES_BY_EGG[eggId];
  if (!species) {
    return false;
  }
  const key = keyFor(block);
  if (entryAt(key)) {
    return false;
  }
  if (!inv.consumeAll(player, [[eggId, 1]])) {
    return false;
  }
  store.incubators().items.push({
    key,
    species: species.key,
    startedMs: nowMs(),
    progressMs: 0,
    lastMs: nowMs(),
    stage: 0,
  });
  store.markDirty("incubators");
  setStage(block, 0);
  player.playSound(SOUNDS.incubatorStart);
  log.guard("incubator.start.fx", () => {
    block.dimension.spawnParticle(PARTICLES.glow, {
      x: block.location.x + 0.5,
      y: block.location.y + 0.8,
      z: block.location.z + 0.5,
    });
  });
  return true;
}

/** Cancels a session and hands the egg back. Returns the refunded egg id. */
export function cancel(block) {
  const key = keyFor(block);
  const list = store.incubators().items;
  const index = list.findIndex((e) => e.key === key);
  if (index < 0) {
    return undefined;
  }
  const entry = list[index];
  list.splice(index, 1);
  store.markDirty("incubators");
  setStage(block, 0);
  const species = SPECIES_BY_KEY[entry.species];
  return species ? species.eggId : undefined;
}

/** Called when the incubator block itself is destroyed. */
export function refundOnBreak(block) {
  const eggId = cancel(block);
  if (!eggId) {
    return;
  }
  log.guard("incubator.refund", () => {
    // Spawn the refunded egg as a world item so it cannot silently vanish.
    block.dimension.spawnItem(new ItemStack(eggId, 1), {
      x: block.location.x + 0.5,
      y: block.location.y + 0.6,
      z: block.location.z + 0.5,
    });
  });
}

export function progressPercent(entry) {
  const species = SPECIES_BY_KEY[entry.species];
  if (!species) {
    return 0;
  }
  const total = species.incubationSeconds * 1000;
  return Math.max(0, Math.min(100, Math.floor((entry.progressMs / total) * 100)));
}

export function heatMultiplier(block) {
  const light = log.guard("incubator.light", () => block.getLightLevel()) ?? 0;
  return light >= 10 ? 1.25 : 1.0;
}

function hatch(entry, block) {
  const species = SPECIES_BY_KEY[entry.species];
  const list = store.incubators().items;
  const index = list.findIndex((e) => e.key === entry.key);
  if (index >= 0) {
    list.splice(index, 1);
  }
  store.markDirty("incubators");
  setStage(block, 0);
  if (!species) {
    return;
  }
  const pos = {
    x: block.location.x + 0.5,
    y: block.location.y + 1.0,
    z: block.location.z + 0.5,
  };
  log.guard("incubator.hatch", () => {
    const baby = block.dimension.spawnEntity(species.entityId, pos);
    baby.triggerEvent(`paleo:${species.key}_hatched`);
    baby.triggerEvent(`paleo:${species.key}_raised`);
    baby.addTag("paleo:raised");
    block.dimension.spawnParticle(PARTICLES.spark, pos);
    block.dimension.playSound(SOUNDS.incubatorHatch, pos, { volume: 1.0 });
    store.bumpStat("hatched", 1);
    for (const player of block.dimension.getPlayers({ location: pos, maxDistance: 24 })) {
      store.bumpJournal(player, "hatched", species.key, 1);
      player.onScreenDisplay.setTitle({
        translate: "paleo.ui.incubator.hatched",
        with: args([{ translate: `entity.paleo:${species.entity}.name` }]),
      });
      player.playSound(SOUNDS.incubatorHatch);
    }
  });
}

export function tick() {
  const now = nowMs();
  const items = store.incubators().items;
  if (items.length === 0) {
    return;
  }
  let dirty = false;
  for (const entry of [...items]) {
    const parts = entry.key.split("|");
    const dim = log.guard("incubator.dim", () => world.getDimension(parts[0]));
    if (!dim) {
      continue;
    }
    const pos = { x: Number(parts[1]), y: Number(parts[2]), z: Number(parts[3]) };
    if (!dim.isChunkLoaded(pos)) {
      entry.lastMs = now;
      dirty = true;
      continue;
    }
    const block = log.guard("incubator.block", () => dim.getBlock(pos));
    if (!block || block.typeId !== BLOCKS.incubator) {
      const index = items.indexOf(entry);
      if (index >= 0) {
        items.splice(index, 1);
      }
      dirty = true;
      continue;
    }
    const elapsed = Math.min(Math.max(0, now - (entry.lastMs || now)), MAX_CREDIT_MS);
    entry.lastMs = now;
    entry.progressMs += elapsed * heatMultiplier(block);
    const species = SPECIES_BY_KEY[entry.species];
    const total = species ? species.incubationSeconds * 1000 : 1;
    const stage = Math.min(4, Math.floor((entry.progressMs / total) * 5));
    if (stage !== entry.stage) {
      entry.stage = stage;
      setStage(block, stage);
      if (stage > 0 && stage < 4) {
        dim.playSound(SOUNDS.incubatorProgress, pos, { volume: 0.5 });
      }
      log.guard("incubator.glow", () => {
        dim.spawnParticle(PARTICLES.glow, { x: pos.x + 0.5, y: pos.y + 0.8, z: pos.z + 0.5 });
      });
    }
    dirty = true;
    if (entry.progressMs >= total) {
      hatch(entry, block);
    }
  }
  if (dirty) {
    store.markDirty("incubators");
  }
  void TICK_MS;
}
