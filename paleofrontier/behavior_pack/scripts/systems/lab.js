/**
 * PALEOFRONTIER - research station logic.
 *
 * Every operation is executed on the script host against the acting player's
 * inventory, which makes it authoritative in multiplayer: items are verified
 * and removed before anything is granted, and the shared species registry is
 * only ever mutated through this module.
 */

import {
  ITEMS,
  SPECIES_BY_KEY,
  LAB_PROCESSES,
  SOUNDS,
  PARTICLES,
} from "../data/content.js";
import * as inv from "../core/inventory.js";
import * as store from "../core/store.js";
import * as log from "../core/log.js";
import { args } from "../core/text.js";

function examineCosts(key) {
  const sp = SPECIES_BY_KEY[key];
  const cost = sp.examineCost;
  return [
    [sp.specimenId, cost.specimen],
    [ITEMS.fossilChip, cost.chip],
    [ITEMS.boneShard, cost.shard],
    [ITEMS.amberInclusion, cost.amber],
  ].filter(([, n]) => n > 0);
}

function reconstructCosts(key) {
  const sp = SPECIES_BY_KEY[key];
  const cost = sp.reconstructCost;
  return [
    [ITEMS.geneticMatrix, cost.matrix],
    [sp.specimenId, cost.specimen],
    [ITEMS.nutrientGel, cost.gel],
    [ITEMS.amberInclusion, cost.amber],
  ].filter(([, n]) => n > 0);
}

export function isIdentified(key) {
  return Boolean(store.registry().identified[key]);
}

export function identifiedKeys() {
  return Object.keys(store.registry().identified);
}

/** [{id, need, have}] for everything still missing. */
export function missing(player, costs) {
  const out = [];
  for (const [id, need] of costs) {
    const have = inv.countItem(player, id);
    if (have < need) {
      out.push({ id, need, have });
    }
  }
  return out;
}

function deny(player) {
  player.playSound(SOUNDS.labDeny);
  player.onScreenDisplay.setActionBar({ translate: "paleo.ui.lab.missing" });
}

function celebrate(player, sound) {
  player.playSound(sound);
  log.guard("lab.celebrate", () => {
    player.spawnParticle(PARTICLES.spark, {
      x: player.location.x,
      y: player.location.y + 1.2,
      z: player.location.z,
    });
  });
}

export function identify(player, key) {
  const species = SPECIES_BY_KEY[key];
  if (!species) {
    return false;
  }
  if (isIdentified(key)) {
    player.onScreenDisplay.setActionBar({
      translate: "paleo.ui.lab.identified",
      with: args([{ translate: `entity.paleo:${species.entity}.name` }]),
    });
    return false;
  }
  const costs = examineCosts(key);
  if (!inv.consumeAll(player, costs)) {
    deny(player);
    return false;
  }
  store.registry().identified[key] = {
    by: player.name,
    at: Date.now(),
  };
  store.markDirty("registry");
  store.bumpJournal(player, "found", `${key}.identified`, 1);
  store.bumpStat("identified", 1);
  player.addExperience(species.examineXp);
  celebrate(player, SOUNDS.labIdentify);
  player.onScreenDisplay.setTitle({
    translate: "paleo.ui.lab.identified",
    with: args([{ translate: `entity.paleo:${species.entity}.name` }]),
  });
  return true;
}

export function process(player, processId) {
  const recipe = LAB_PROCESSES.find((p) => p.id === processId);
  if (!recipe) {
    return false;
  }
  if (recipe.requiresAnySpecies && identifiedKeys().length === 0) {
    deny(player);
    return false;
  }
  if (!inv.consumeAll(player, recipe.inputs)) {
    deny(player);
    return false;
  }
  inv.grantAll(player, recipe.outputs);
  player.addExperience(recipe.xp);
  celebrate(player, recipe.sound || SOUNDS.labProcess);
  player.onScreenDisplay.setActionBar({ translate: "paleo.ui.lab.done" });
  return true;
}

export function reconstruct(player, key) {
  const species = SPECIES_BY_KEY[key];
  if (!species) {
    return false;
  }
  if (!isIdentified(key)) {
    deny(player);
    return false;
  }
  const costs = reconstructCosts(key);
  if (!inv.consumeAll(player, costs)) {
    deny(player);
    return false;
  }
  inv.grantAll(player, [[species.eggId, 1]]);
  player.addExperience(species.reconstructXp);
  celebrate(player, SOUNDS.labIdentify);
  player.onScreenDisplay.setTitle({ translate: "paleo.ui.lab.egg_ready" });
  player.onScreenDisplay.updateSubtitle({
    translate: "paleo.ui.lab.egg_ready.sub",
    with: args([{ translate: `entity.paleo:${species.entity}.name` }]),
  });
  store.bumpJournal(player, "found", `${key}.eggs`, 1);
  return true;
}

export { examineCosts, reconstructCosts };
