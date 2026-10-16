/**
 * PALEOFRONTIER - research station interface.
 *
 * Built on the stable @minecraft/server-ui forms so it works on touch devices
 * with no commands involved.  Every button leads to a real transaction handled
 * by systems/lab.js.
 */

import { ActionFormData } from "@minecraft/server-ui";
import { SPECIES, SPECIES_BY_KEY, LAB_PROCESSES, ALL_SPECIMEN_IDS } from "../data/content.js";
import * as inv from "../core/inventory.js";
import * as lab from "../systems/lab.js";
import * as journal from "../systems/journal.js";
import * as journalUi from "./journal_ui.js";
import * as ui from "./forms.js";
import * as log from "../core/log.js";
import { args } from "../core/text.js";

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
  await ui.run(player, "lab_ui.open", () => root(player));
}

async function root(player) {
  const form = new ActionFormData()
    .title({ translate: "paleo.ui.lab.title" })
    .body({ translate: "paleo.ui.lab.body" });
  const handlers = [];
  const entries = [
    ["paleo.ui.lab.examine", () => examineMenu(player)],
    ["paleo.ui.lab.process", () => processMenu(player)],
    ["paleo.ui.lab.reconstruct", () => reconstructMenu(player)],
    ["paleo.ui.lab.projects", () => projectsMenu(player)],
    ["paleo.ui.lab.journal", () => journalUi.inner(player)],
    ["paleo.ui.lab.exit", null],
  ];
  for (const [key] of entries) {
    form.button({ translate: key });
  }
  for (const [, handler] of entries) {
    handlers.push(handler);
  }
  await showMenu(player, form, handlers);
}

async function examineMenu(player) {
  const carried = ALL_SPECIMEN_IDS
    .map((id) => ({ id, n: inv.countItem(player, id) }))
    .filter((e) => e.n > 0);
  if (carried.length === 0) {
    const form = new ActionFormData()
      .title({ translate: "paleo.ui.lab.title" })
      .body({ translate: "paleo.ui.lab.no_specimen" })
      .button({ translate: "paleo.ui.lab.cancel" });
    await form.show(player);
    return;
  }
  const form = new ActionFormData()
    .title({ translate: "paleo.ui.lab.examine" })
    .body({ translate: "paleo.ui.lab.pick" });
  const handlers = [];
  for (const entry of carried) {
    const species = SPECIES.find((s) => s.specimenId === entry.id);
    const identified = lab.isIdentified(species.key);
    form.button({
      translate: identified ? "paleo.ui.lab.examine_again" : "paleo.ui.lab.examine_one",
      with: args([{ translate: `entity.paleo:${species.entity}.name` }, entry.n]),
    });
    handlers.push(() => {
      lab.identify(player, species.key);
    });
  }
  form.button({ translate: "paleo.ui.lab.cancel" });
  handlers.push(null);
  await showMenu(player, form, handlers);
}

async function processMenu(player) {
  const form = new ActionFormData()
    .title({ translate: "paleo.ui.lab.process" })
    .body({ translate: "paleo.ui.lab.pick_process" });
  const handlers = [];
  for (const recipe of LAB_PROCESSES) {
    const missing = lab.missing(player, recipe.inputs);
    form.button({
      translate: missing.length === 0 ? "paleo.ui.lab.process_ok" : "paleo.ui.lab.process_lack",
      with: args([{ translate: `paleo.proc.${recipe.id}` }]),
    });
    form.label(recipe.descPt);
    handlers.push(() => {
      lab.process(player, recipe.id);
    });
  }
  form.button({ translate: "paleo.ui.lab.cancel" });
  handlers.push(null);
  await showMenu(player, form, handlers);
}

async function reconstructMenu(player) {
  const identified = lab.identifiedKeys();
  const form = new ActionFormData()
    .title({ translate: "paleo.ui.lab.reconstruct" })
    .body({ translate: "paleo.ui.lab.pick_species" });
  const handlers = [];
  if (identified.length === 0) {
    form.label({ translate: "paleo.ui.lab.none_identified" });
  }
  for (const key of identified) {
    const species = SPECIES_BY_KEY[key];
    const costs = lab.reconstructCosts(key);
    const missing = lab.missing(player, costs);
    form.button({
      translate: missing.length === 0 ? "paleo.ui.lab.reconstruct_ok" : "paleo.ui.lab.reconstruct_lack",
      with: args([{ translate: `entity.paleo:${species.entity}.name` }]),
    });
    handlers.push(() => {
      lab.reconstruct(player, key);
    });
  }
  form.button({ translate: "paleo.ui.lab.cancel" });
  handlers.push(null);
  await showMenu(player, form, handlers);
}

async function projectsMenu(player) {
  const form = new ActionFormData()
    .title({ translate: "paleo.ui.lab.projects" })
    .body({ translate: "paleo.ui.lab.projects_body" });
  const handlers = [];
  for (const species of SPECIES) {
    const identified = lab.isIdentified(species.key);
    form.label({
      translate: identified ? "paleo.ui.lab.project_open" : "paleo.ui.lab.project_locked",
      with: args([{ translate: `entity.paleo:${species.entity}.name` }, { translate: `paleo.rarity.${species.rarityEn}` }]),
    });
    const costs = lab.reconstructCosts(species.key);
    const owned = costs
      .map(([id, need]) => `${Math.min(need, inv.countItem(player, id))}/${need}`)
      .join("  ");
    form.label(owned);
    handlers.push(() => {
      dossierMenu(player, species.key);
    });
  }
  form.button({ translate: "paleo.ui.lab.cancel" });
  handlers.push(null);
  await showMenu(player, form, handlers);
}

async function dossierMenu(player, key) {
  const form = new ActionFormData()
    .title({ translate: `entity.paleo:${SPECIES_BY_KEY[key].entity}.name` });
  for (const line of journal.dossierLines(player, key)) {
    form.label(line);
  }
  form.button({ translate: "paleo.ui.lab.cancel" });
  await showMenu(player, form, [null]);
}

export { log };
