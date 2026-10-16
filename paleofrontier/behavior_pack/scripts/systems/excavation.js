/**
 * PALEOFRONTIER - excavation feedback and discovery bookkeeping.
 *
 * Drops themselves are decided entirely by data-driven loot tables (including
 * `match_tool` conditions for the brush and the shovel), so this module never
 * spawns loot and can never duplicate an item.  What it does:
 *
 *  - plays the digging audio/particles that match the tool actually used,
 *  - diffs the player's inventory a few ticks after the break to learn which
 *    specimens and amber inclusions were recovered, and records them in the
 *    personal field journal (with the discovery flourish).
 */

import { system } from "@minecraft/server";
import {
  BLOCKS,
  ITEMS,
  ALL_SPECIMEN_IDS,
  SPECIES_BY_SPECIMEN,
  SOUNDS,
  PARTICLES,
} from "../data/content.js";
import * as store from "../core/store.js";
import * as log from "../core/log.js";

const TRACKED = [...ALL_SPECIMEN_IDS, ITEMS.amberInclusion];

function countTracked(player) {
  const snapshot = {};
  for (const id of TRACKED) {
    // Cheap path: reuse the inventory helper.
    snapshot[id] = 0;
  }
  const container = player.getComponent("minecraft:inventory");
  if (!container) {
    return snapshot;
  }
  for (let i = 0; i < container.container.size; i++) {
    const item = container.container.getItem(i);
    if (item && snapshot[item.typeId] !== undefined) {
      snapshot[item.typeId] += item.amount;
    }
  }
  return snapshot;
}

export function onBreakBlock(event) {
  const blockType = event.brokenBlockPermutation.type.id;
  const isDeposit =
    blockType === BLOCKS.fossilDeposit ||
    blockType === BLOCKS.shaleMatrix ||
    blockType === BLOCKS.boneBed;
  if (!isDeposit) {
    return;
  }
  const player = event.player;
  const position = event.block.location;
  const centre = {
    x: position.x + 0.5,
    y: position.y + 0.5,
    z: position.z + 0.5,
  };
  const tool = event.itemStackBeforeBreak ? event.itemStackBeforeBreak.typeId : undefined;

  log.guard("excavation.fx", () => {
    player.dimension.spawnParticle(PARTICLES.dust, centre);
    if (tool === ITEMS.brush) {
      player.dimension.playSound(SOUNDS.digBrush, centre, { volume: 0.9 });
    } else if (tool === ITEMS.excavationShovel) {
      player.dimension.playSound(SOUNDS.digSediment, centre, { volume: 1.0, pitch: 1.15 });
    } else {
      player.dimension.playSound(SOUNDS.digSediment, centre, { volume: 0.8 });
    }
  });

  store.bumpStat("mined", 1);
  const before = countTracked(player);

  // The loot lands a tick or two later; compare once it has arrived.
  system.runTimeout(() => {
    log.guard("excavation.diff", () => {
      if (!player.isValid) {
        return;
      }
      const after = countTracked(player);
      let recoveredSpecimen = false;
      for (const id of TRACKED) {
        const gained = after[id] - before[id];
        if (gained <= 0) {
          continue;
        }
        if (id === ITEMS.amberInclusion) {
          store.bumpJournal(player, "found", "amber", gained);
          continue;
        }
        const species = SPECIES_BY_SPECIMEN[id];
        if (!species) {
          continue;
        }
        store.bumpJournal(player, "found", species.key, gained);
        recoveredSpecimen = true;
      }
      if (recoveredSpecimen) {
        player.playSound(SOUNDS.discover);
        player.onScreenDisplay.setTitle({ translate: "paleo.ui.lab.discovered" });
        player.onScreenDisplay.updateSubtitle({ translate: "paleo.ui.lab.discovered.sub" });
      }
    });
  }, 4);
}
