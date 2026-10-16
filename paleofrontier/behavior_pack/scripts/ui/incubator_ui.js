/**
 * PALEOFRONTIER - incubator interface.
 */

import { ActionFormData } from "@minecraft/server-ui";
import { ALL_EGG_IDS, SPECIES_BY_EGG, SPECIES_BY_KEY } from "../data/content.js";
import * as incubator from "../systems/incubator.js";
import * as inv from "../core/inventory.js";
import * as store from "../core/store.js";
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

export async function open(player, block) {
  await ui.run(player, "incubator_ui.open", () => inner(player, block));
}

async function inner(player, block) {
  if (!block.isValid || block.typeId !== "paleo:incubator") {
    return;
  }
  const entry = incubator.entryAt(incubator.keyFor(block));
  const form = new ActionFormData()
    .title({ translate: "paleo.ui.incubator.title" });
  const handlers = [];

  if (!entry) {
    form.label({ translate: "paleo.ui.incubator.empty" });
    const carried = ALL_EGG_IDS
      .map((id) => ({ id, n: inv.countItem(player, id) }))
      .filter((e) => e.n > 0);
    for (const egg of carried) {
      const species = SPECIES_BY_EGG[egg.id];
      form.button({
        translate: "paleo.ui.incubator.insert_one",
        with: [{ translate: `entity.paleo:${species.entity}.name` }, egg.n],
      });
      handlers.push(() => {
        if (incubator.start(player, block, egg.id)) {
          store.bumpJournal(player, "found", `${species.key}.incubated`, 1);
        }
      });
    }
  } else {
    const species = SPECIES_BY_KEY[entry.species];
    const percent = incubator.progressPercent(entry);
    const stage = Math.min(4, Math.floor(percent / 20) + (percent >= 100 ? 0 : percent > 0 ? 1 : 0));
    form.label({
      translate: percent >= 100
        ? "paleo.ui.incubator.ready"
        : "paleo.ui.incubator.status",
      with: [{ translate: `entity.paleo:${species.entity}.name` }, percent, stage],
    });
    form.label({
      translate: incubator.heatMultiplier(block) > 1
        ? "paleo.ui.incubator.warm"
        : "paleo.ui.incubator.nolight",
    });
    form.button({ translate: "paleo.ui.incubator.status_btn" });
    handlers.push(() => {
      statusMenu(player, block, entry);
    });
    form.button({ translate: "paleo.ui.incubator.remove" });
    handlers.push(() => {
      const eggId = incubator.cancel(block);
      if (eggId) {
        inv.grantAll(player, [[eggId, 1]]);
        player.onScreenDisplay.setActionBar({ translate: "paleo.ui.incubator.removed" });
      }
    });
  }
  form.label({ translate: "paleo.ui.incubator.tip" });
  form.button({ translate: "paleo.ui.lab.exit" });
  handlers.push(null);
  await showMenu(player, form, handlers);
}

async function statusMenu(player, block, entry) {
  const species = SPECIES_BY_KEY[entry.species];
  const percent = incubator.progressPercent(entry);
  const form = new ActionFormData()
    .title({ translate: "paleo.ui.incubator.title" });
  form.label({ translate: "paleo.ui.incubator.s_species", with: [{ translate: `entity.paleo:${species.entity}.name` }] });
  form.label({ translate: "paleo.ui.incubator.s_progress", with: [percent] });
  form.label({ translate: "paleo.ui.incubator.s_elapsed", with: [Math.round(entry.progressMs / 1000), species.incubationSeconds] });
  form.label({ translate: "paleo.ui.incubator.s_heat", with: [Math.round((incubator.heatMultiplier(block) - 1) * 100)] });
  form.label({ translate: "paleo.ui.incubator.tip" });
  form.button({ translate: "paleo.ui.lab.cancel" });
  await showMenu(player, form, [null]);
}
