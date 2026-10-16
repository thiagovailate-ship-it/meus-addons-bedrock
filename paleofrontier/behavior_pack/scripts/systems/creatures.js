/**
 * PALEOFRONTIER - creature bookkeeping.
 *
 * All locomotion, hunting, fleeing, feeding, growth and bonding behaviour is
 * handled by the native entity components (see the behavior pack JSON).  This
 * module only keeps the *record* of what happened: which creatures were raised
 * or bonded by whom, and it powers the "study a creature" action of the field
 * case, which tags the individual and flips its `studied` component group so
 * the animal visibly carries a field tag.
 */

import {
  ALL_ENTITY_IDS,
  SPECIES_BY_ENTITY,
  SOUNDS,
  PARTICLES,
} from "../data/content.js";
import * as store from "../core/store.js";
import * as log from "../core/log.js";

export function isOurs(typeId) {
  return SPECIES_BY_ENTITY[typeId] !== undefined;
}

export function onEntitySpawn(event) {
  const entity = event.entity;
  if (!isOurs(entity.typeId)) {
    return;
  }
  log.guard("creatures.spawn", () => {
    entity.addTag("paleo:creature");
  });
}

export function onEntityDie(event) {
  const entity = event.deadEntity;
  if (!isOurs(entity.typeId)) {
    return;
  }
  store.bumpStat("deaths", 1);
}

export function onTamed(event) {
  const entity = event.entity;
  const species = SPECIES_BY_ENTITY[entity.typeId];
  if (!species) {
    return;
  }
  const player = event.tamingEntity;
  log.guard("creatures.tamed", () => {
    if (player && player.typeId === "minecraft:player") {
      store.bumpJournal(player, "bonded", species.key, 1);
      player.onScreenDisplay.setTitle({
        translate: "paleo.ui.creatures.bonded",
        with: [{ translate: `entity.paleo:${species.entity}.name` }],
      });
      player.playSound(SOUNDS.discover);
    }
    entity.dimension.spawnParticle(PARTICLES.spark, {
      x: entity.location.x,
      y: entity.location.y + entity.getAABB().height + 0.3,
      z: entity.location.z,
    });
  });
}

/** Nearest archive creature around the player, if any. */
export function nearestCreature(player, radius = 8) {
  const found = log.guard("creatures.nearest", () =>
    player.dimension.getEntities({
      location: player.location,
      maxDistance: radius,
      families: ["paleo_dinosaur"],
      closest: 1,
    }));
  return found && found.length ? found[0] : undefined;
}

export function study(player, creature) {
  const species = SPECIES_BY_ENTITY[creature.typeId];
  if (!species) {
    return false;
  }
  const tag = `paleo:studied:${player.id}`;
  if (creature.hasTag(tag)) {
    player.onScreenDisplay.setActionBar({ translate: "paleo.ui.study.already" });
    return false;
  }
  creature.addTag(tag);
  log.guard("creatures.study.event", () => {
    creature.triggerEvent(`paleo:${species.key}_studied`);
  });
  store.bumpJournal(player, "studied", species.key, 1);
  store.bumpStat("studied", 1);
  player.addExperience(12);
  player.playSound(SOUNDS.labIdentify);
  player.onScreenDisplay.setActionBar({
    translate: "paleo.ui.study.done",
    with: [{ translate: `entity.paleo:${species.entity}.name` }],
  });
  return true;
}

export { ALL_ENTITY_IDS };
