/**
 * PALEOFRONTIER - fossil scanner.
 *
 * The scanner performs a REAL query against the world: it asks the dimension
 * for fossil deposit blocks inside a bounded volume and reports the nearest
 * hit (bearing, range band and signal strength).  Nothing is invented - if the
 * query finds no deposit the scanner says so.
 *
 * The scan radius grows with the player's shared research progress, so
 * exploration and laboratory work feed back into field equipment.
 */

import { BlockVolume } from "@minecraft/server";
import {
  DEPOSIT_BLOCKS,
  DEPOSIT_WEIGHT,
  BLOCKS,
  SOUNDS,
  PARTICLES,
} from "../data/content.js";
import * as inv from "../core/inventory.js";
import * as store from "../core/store.js";
import * as log from "../core/log.js";
import { args } from "../core/text.js";

export const COOLDOWN_CATEGORY = "paleo_scanner";
const COOLDOWN_TICKS = 160; // 8 seconds

/** Index 0 = north, growing clockwise, matching directionKey() below. */
const DIR_KEYS = [
  "paleo.ui.scan.dir.n",
  "paleo.ui.scan.dir.ne",
  "paleo.ui.scan.dir.e",
  "paleo.ui.scan.dir.se",
  "paleo.ui.scan.dir.s",
  "paleo.ui.scan.dir.sw",
  "paleo.ui.scan.dir.w",
  "paleo.ui.scan.dir.nw",
];

export function scanRadius(player) {
  const identified = Object.keys(store.registry().identified).length;
  if (identified >= 4) {
    return 24;
  }
  if (identified >= 2) {
    return 20;
  }
  return 16;
}

function directionKey(dx, dz) {
  const angle = Math.atan2(dx, -dz); // 0 = north (-z), grows clockwise
  const step = Math.round(((angle + Math.PI * 2) % (Math.PI * 2)) / (Math.PI / 4)) % 8;
  return DIR_KEYS[step];
}

export function scan(player) {
  if (player.getItemCooldown(COOLDOWN_CATEGORY) > 0) {
    player.onScreenDisplay.setActionBar({ translate: "paleo.ui.scan.cooldown" });
    return;
  }
  player.startItemCooldown(COOLDOWN_CATEGORY, COOLDOWN_TICKS);
  inv.damageHeld(player, 1);

  const radius = scanRadius(player);
  const here = player.location;
  const dim = player.dimension;
  const range = dim.heightRange;
  const cx = Math.floor(here.x);
  const cy = Math.floor(here.y);
  const cz = Math.floor(here.z);
  const minY = Math.max(range.min, cy - radius);
  const maxY = Math.min(range.max - 1, cy + radius);
  if (minY > maxY) {
    return;
  }

  let hits;
  try {
    const volume = new BlockVolume(
      { x: cx - radius, y: minY, z: cz - radius },
      { x: cx + radius, y: maxY, z: cz + radius },
    );
    hits = dim.getBlocks(volume, { includeTypes: DEPOSIT_BLOCKS }, false);
  } catch (err) {
    log.warn("scanner.query", `volume query failed: ${err && err.message}`);
    player.onScreenDisplay.setActionBar({ translate: "paleo.ui.scan.none" });
    return;
  }

  const count = hits.getCapacity();
  if (count === 0) {
    player.playSound(SOUNDS.scanEmpty);
    player.onScreenDisplay.setActionBar({ translate: "paleo.ui.scan.none" });
    return;
  }

  const nearest = hits.getClosest(1, { x: cx, y: cy, z: cz })[0];
  if (!nearest) {
    player.onScreenDisplay.setActionBar({ translate: "paleo.ui.scan.none" });
    return;
  }
  const block = log.guard("scanner.block", () => dim.getBlock(nearest));
  const weight = block ? (DEPOSIT_WEIGHT[block.typeId] || 1) : 1;
  const strength = Math.max(1, Math.min(5, weight + (count >= 10 ? 2 : count >= 4 ? 1 : 0)));

  const dx = nearest.x + 0.5 - here.x;
  const dy = nearest.y + 0.5 - here.y;
  const dz = nearest.z + 0.5 - here.z;
  const horizontal = Math.sqrt(dx * dx + dz * dz);
  const distance = Math.max(1, Math.round(Math.sqrt(dx * dx + dy * dy + dz * dz)));
  let dirKey = directionKey(dx, dz);
  if (Math.abs(dy) > horizontal * 0.9) {
    dirKey = dy > 0 ? "paleo.ui.scan.dir.up" : "paleo.ui.scan.dir.down";
  }

  const depositNameKey = block && block.typeId === BLOCKS.shaleMatrix
    ? "tile.paleo:shale_matrix.name"
    : block && block.typeId === BLOCKS.boneBed
      ? "tile.paleo:bone_bed.name"
      : "tile.paleo:fossil_deposit.name";

  player.playSound(strength >= 4 ? SOUNDS.scanStrong : SOUNDS.scanPing);
  player.onScreenDisplay.setActionBar({
    translate: "paleo.ui.scan.found",
    with: args([{ translate: depositNameKey }, distance, { translate: dirKey }, strength]),
  });
  log.guard("scanner.pulse", () => {
    dim.spawnParticle(PARTICLES.scanPulse, {
      x: nearest.x + 0.5,
      y: nearest.y + 1.1,
      z: nearest.z + 0.5,
    });
  });
}
