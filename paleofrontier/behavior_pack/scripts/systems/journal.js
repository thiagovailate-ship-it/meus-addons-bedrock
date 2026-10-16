/**
 * PALEOFRONTIER - field journal data.
 *
 * The journal is the player's personal record.  The species dossier and the
 * objective checklist shown in the UI are derived here from the journal plus
 * the shared registry, so both always agree with reality.
 */

import { SPECIES, SPECIES_BY_KEY, ITEMS } from "../data/content.js";
import * as inv from "../core/inventory.js";
import * as store from "../core/store.js";
import * as lab from "./lab.js";
import { args } from "../core/text.js";

function foundCount(player, key) {
  return store.journalFor(player).found[key] || 0;
}

export function specimenFound(player, key) {
  return foundCount(player, key);
}

export function hatchedCount(player, key) {
  return store.journalFor(player).hatched[key] || 0;
}

export function studiedCount(player, key) {
  return store.journalFor(player).studied[key] || 0;
}

export function bondedCount(player, key) {
  return store.journalFor(player).bonded[key] || 0;
}

/** First three unfinished milestones, as translatable objective lines. */
export function objectives(player) {
  const steps = [];
  if (inv.countItem(player, ITEMS.brush) === 0 &&
      inv.countItem(player, ITEMS.excavationShovel) === 0) {
    steps.push({ key: "paleo.ui.obj.gear" });
  }
  const anyFound = SPECIES.some((s) => specimenFound(player, s.key) > 0);
  if (!anyFound) {
    steps.push({ key: "paleo.ui.obj.specimen" });
  }
  if (lab.identifiedKeys().length === 0) {
    steps.push({ key: "paleo.ui.obj.identify" });
  }
  const anyEgg = SPECIES.some((s) => foundCount(player, `${s.key}.eggs`) > 0);
  if (!anyEgg && lab.identifiedKeys().length > 0) {
    steps.push({ key: "paleo.ui.obj.egg" });
  }
  const anyHatched = SPECIES.some((s) => hatchedCount(player, s.key) > 0);
  if (!anyHatched) {
    steps.push({ key: "paleo.ui.obj.hatch" });
  }
  const anyStudied = SPECIES.some((s) => studiedCount(player, s.key) > 0);
  if (!anyStudied) {
    steps.push({ key: "paleo.ui.obj.study" });
  }
  if (lab.identifiedKeys().length < SPECIES.length) {
    steps.push({
      key: "paleo.ui.obj.all",
      args: [lab.identifiedKeys().length, SPECIES.length],
    });
  }
  return steps.slice(0, 3);
}

export function dossierLines(player, key) {
  const sp = SPECIES_BY_KEY[key];
  const identified = lab.isIdentified(key);
  const lines = [];
  lines.push({ translate: "paleo.ui.dossier.name", with: args([{ translate: `entity.paleo:${sp.entity}.name` }, sp.sci])});
  lines.push({ translate: "paleo.ui.dossier.status", with: args([identified
    ? { translate: "paleo.ui.journal.identified" }
    : { translate: "paleo.ui.journal.unknown" }])});
  lines.push({ translate: "paleo.ui.dossier.rarity", with: args([{ translate: `paleo.rarity.${sp.rarityEn}` }])});
  if (identified) {
    lines.push({ translate: "paleo.ui.dossier.era", with: args([sp.eraPt])});
    lines.push({ translate: "paleo.ui.dossier.diet", with: args([sp.dietPt])});
    lines.push({ translate: "paleo.ui.dossier.size", with: args([sp.sizePt])});
    lines.push({ translate: "paleo.ui.dossier.note", with: args([sp.notePt])});
    lines.push({ translate: "paleo.ui.dossier.incubation", with: args([Math.round(sp.incubationSeconds / 60)])});
    const cost = sp.reconstructCost;
    lines.push({
      translate: "paleo.ui.dossier.cost",
      with: args([cost.matrix, cost.specimen, cost.gel, cost.amber]),
    });
  } else {
    lines.push({ translate: "paleo.ui.dossier.locked" });
    lines.push({
      translate: "paleo.ui.dossier.examine_cost",
      with: args([sp.examineCost.specimen, sp.examineCost.chip, sp.examineCost.shard, sp.examineCost.amber]),
    });
  }
  lines.push({
    translate: "paleo.ui.dossier.progress",
    with: args([
      specimenFound(player, key),
      hatchedCount(player, key),
      studiedCount(player, key),
      bondedCount(player, key),
    ]),
  });
  return lines;
}

export function statsLines(player) {
  const stats = store.registry().stats;
  return [
    { translate: "paleo.ui.stats.mined", with: args([stats.mined || 0])},
    { translate: "paleo.ui.stats.identified", with: args([lab.identifiedKeys().length, SPECIES.length])},
    { translate: "paleo.ui.stats.hatched", with: args([stats.hatched || 0])},
    { translate: "paleo.ui.stats.studied", with: args([stats.studied || 0])},
  ];
}
