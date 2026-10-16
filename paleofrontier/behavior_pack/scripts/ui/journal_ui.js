/**
 * PALEOFRONTIER - field journal interface (opened by the field case).
 */

import { ActionFormData } from "@minecraft/server-ui";
import { SPECIES } from "../data/content.js";
import * as journal from "../systems/journal.js";
import * as creatures from "../systems/creatures.js";
import * as ui from "./forms.js";

const BACK = -1;

async function showMenu(player, form, handlers) {
  const res = await form.show(player);
  if (res.canceled || res.selection === undefined) {
    return BACK;
  }
  const handler = handlers[res.selection];
  if (handler) {
    await handler();
  }
  return res.selection;
}

export async function open(player) {
  await ui.run(player, "journal_ui.open", () => inner(player));
}

export async function inner(player) {
  const form = new ActionFormData()
    .title({ translate: "paleo.ui.journal.title" })
    .body({ translate: "paleo.ui.journal.body" });
  const entries = [
    ["paleo.ui.journal.species", () => speciesMenu(player)],
    ["paleo.ui.journal.objectives", () => objectivesMenu(player)],
    ["paleo.ui.journal.creatures", () => creaturesMenu(player)],
    ["paleo.ui.journal.stats", () => statsMenu(player)],
    ["paleo.ui.journal.study", () => studyAction(player)],
    ["paleo.ui.lab.exit", null],
  ];
  const handlers = [];
  for (const [key] of entries) {
    form.button({ translate: key });
  }
  for (const [, handler] of entries) {
    handlers.push(handler);
  }
  await showMenu(player, form, handlers);
}

async function speciesMenu(player) {
  const form = new ActionFormData()
    .title({ translate: "paleo.ui.journal.species" });
  const handlers = [];
  for (const species of SPECIES) {
    form.button({
      translate: "paleo.ui.journal.species_entry",
      with: [
        { translate: `entity.paleo:${species.entity}.name` },
        journal.specimenFound(player, species.key),
      ],
    });
    handlers.push(() => dossier(player, species.key));
  }
  form.button({ translate: "paleo.ui.lab.cancel" });
  handlers.push(null);
  await showMenu(player, form, handlers);
}

async function dossier(player, key) {
  const form = new ActionFormData().title({ translate: "paleo.ui.journal.species" });
  for (const line of journal.dossierLines(player, key)) {
    form.label(line);
  }
  form.button({ translate: "paleo.ui.lab.cancel" });
  await showMenu(player, form, [null]);
}

async function objectivesMenu(player) {
  const form = new ActionFormData()
    .title({ translate: "paleo.ui.journal.objectives" });
  const steps = journal.objectives(player);
  if (steps.length === 0) {
    form.label({ translate: "paleo.ui.journal.complete" });
  }
  steps.forEach((step, index) => {
    form.label({ translate: "paleo.ui.journal.objective_n", with: [index + 1, { translate: step.key, with: step.args || [] }] });
  });
  form.button({ translate: "paleo.ui.lab.cancel" });
  await showMenu(player, form, [null]);
}

async function creaturesMenu(player) {
  const form = new ActionFormData()
    .title({ translate: "paleo.ui.journal.creatures" });
  let any = false;
  for (const species of SPECIES) {
    const hatched = journal.hatchedCount(player, species.key);
    const bonded = journal.bondedCount(player, species.key);
    const studied = journal.studiedCount(player, species.key);
    if (hatched + bonded + studied === 0) {
      continue;
    }
    any = true;
    form.label({
      translate: "paleo.ui.journal.creature_line",
      with: [
        { translate: `entity.paleo:${species.entity}.name` },
        hatched,
        bonded,
        studied,
      ],
    });
  }
  if (!any) {
    form.label({ translate: "paleo.ui.journal.none" });
  }
  form.button({ translate: "paleo.ui.lab.cancel" });
  await showMenu(player, form, [null]);
}

async function statsMenu(player) {
  const form = new ActionFormData()
    .title({ translate: "paleo.ui.journal.stats" });
  for (const line of journal.statsLines(player)) {
    form.label(line);
  }
  form.button({ translate: "paleo.ui.lab.cancel" });
  await showMenu(player, form, [null]);
}

async function studyAction(player) {
  const creature = creatures.nearestCreature(player, 8);
  if (!creature) {
    player.onScreenDisplay.setActionBar({ translate: "paleo.ui.study.none" });
    return;
  }
  creatures.study(player, creature);
}
