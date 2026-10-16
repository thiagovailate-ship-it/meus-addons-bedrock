/**
 * PALEOFRONTIER: Arquivo dos Gigantes - entry point.
 *
 * Wires the gameplay systems to the stable Script API events and starts the
 * small set of coarse periodic tasks.  Nothing here runs per tick.
 *
 * Module map:
 *   data/content.js        generated registry (ids, costs, sounds)
 *   core/log.js            deduplicated diagnostics
 *   core/store.js          dynamic-property persistence (world + player)
 *   core/inventory.js      inventory transactions
 *   core/scheduler.js      coarse periodic work
 *   systems/scanner.js     fossil scanner (real block query)
 *   systems/excavation.js  dig feedback + discovery bookkeeping
 *   systems/lab.js         research station transactions
 *   systems/journal.js     journal data / objectives / dossier
 *   systems/incubator.js   incubation sessions
 *   systems/creatures.js   creature bookkeeping + study action
 *   ui/*                   form interfaces
 */

import { system, world } from "@minecraft/server";
import { BLOCKS, ITEMS, ALL_EGG_IDS } from "./data/content.js";
import * as log from "./core/log.js";
import * as store from "./core/store.js";
import * as inv from "./core/inventory.js";
import * as scheduler from "./core/scheduler.js";
import * as scanner from "./systems/scanner.js";
import * as excavation from "./systems/excavation.js";
import * as incubator from "./systems/incubator.js";
import * as creatures from "./systems/creatures.js";
import * as labUi from "./ui/lab_ui.js";
import * as journalUi from "./ui/journal_ui.js";
import * as incubatorUi from "./ui/incubator_ui.js";

/** One interaction per player every 8 ticks: blocks double-fires from
 *  main-hand/off-hand events and from rapid taps. */
const lastInteract = new Map();
const INTERACT_GAP_TICKS = 8;

function allowInteraction(player) {
  const now = system.currentTick;
  const last = lastInteract.get(player.id) ?? -999;
  if (now - last < INTERACT_GAP_TICKS) {
    return false;
  }
  lastInteract.set(player.id, now);
  return true;
}

function activateHeldItem(player, block) {
  const held = inv.heldTypeId(player);
  if (!held) {
    return false;
  }
  if (held === ITEMS.fossilScanner) {
    scanner.scan(player);
    return true;
  }
  if (held === ITEMS.fieldCase) {
    void journalUi.open(player);
    return true;
  }
  if (ALL_EGG_IDS.includes(held)) {
    if (!block || block.typeId !== BLOCKS.incubator) {
      player.onScreenDisplay.setActionBar({ translate: "paleo.ui.egg.hint" });
    }
    return true;
  }
  return false;
}

let booted = false;

function bootstrap() {
  if (booted) {
    return;
  }
  booted = true;
  log.guard("bootstrap", () => {
    store.loadWorld();
    scheduler.every("paleo.store.flush", 200, () => store.flush());
    scheduler.every("paleo.incubator.tick", 40, () => incubator.tick());
    console.warn("[paleo] PALEOFRONTIER systems online");
  });
}

world.afterEvents.worldLoad.subscribe(() => {
  bootstrap();
});

// Safety net: if the world was already loaded when scripts (re)started, the
// worldLoad signal will not fire again - boot once after a short grace period.
system.runTimeout(() => bootstrap(), 240);

world.afterEvents.playerJoin.subscribe((event) => {
  log.guard("join", () => {
    // PlayerJoinAfterEvent expoe apenas playerId e playerName na API estavel
    // (@minecraft/server 2.10.0): NAO existe event.player.  Ler event.player
    // devolve undefined e estoura com "cannot read property 'id' of undefined"
    // dentro de store.journalFor().  O objeto Player so existe depois, obtido
    // por world.getEntity(playerId) num tick seguinte.
    const playerId = event.playerId;
    store.loadWorld();
    system.run(() => {
      log.guard("join.welcome", () => {
        const player = world.getEntity(playerId);
        if (!player) {
          return;
        }
        const journal = store.journalFor(player);
        if (!journal.welcomed) {
          journal.welcomed = true;
          store.markDirty("journals");
          player.sendMessage({ translate: "paleo.ui.welcome" });
        }
      });
    });
  });
});

world.afterEvents.playerLeave.subscribe((event) => {
  log.guard("leave", () => {
    store.flush();
    store.forgetPlayer(event.playerId);
    lastInteract.delete(event.playerId);
  });
});

system.beforeEvents.shutdown.subscribe(() => {
  store.flush();
});

// --- field equipment -------------------------------------------------------
world.afterEvents.itemUse.subscribe((event) => {
  log.guard("itemUse", () => {
    const player = event.source;
    const typeId = event.itemStack ? event.itemStack.typeId : undefined;
    if (typeId !== ITEMS.fossilScanner && typeId !== ITEMS.fieldCase) {
      return;
    }
    if (!allowInteraction(player)) {
      return;
    }
    if (typeId === ITEMS.fossilScanner) {
      scanner.scan(player);
    } else {
      void journalUi.open(player);
    }
  });
});

world.afterEvents.playerInteractWithBlock.subscribe((event) => {
  log.guard("interactBlock", () => {
    if (!event.isFirstEvent) {
      return;
    }
    const player = event.player;
    const block = event.block;
    if (block.typeId === BLOCKS.researchBench) {
      if (allowInteraction(player)) {
        player.playSound("paleo.bench.open");
        void labUi.open(player);
      }
      return;
    }
    if (block.typeId === BLOCKS.incubator) {
      if (allowInteraction(player)) {
        void incubatorUi.open(player, block);
      }
      return;
    }
    if (!allowInteraction(player)) {
      return;
    }
    activateHeldItem(player, block);
  });
});

// --- excavation & incubator integrity --------------------------------------
world.afterEvents.playerBreakBlock.subscribe((event) => {
  log.guard("breakBlock", () => {
    if (event.brokenBlockPermutation.type.id === BLOCKS.incubator) {
      incubator.refundOnBreak(event.block);
      return;
    }
    excavation.onBreakBlock(event);
  });
});

// --- creatures --------------------------------------------------------------
world.afterEvents.entitySpawn.subscribe((event) => {
  log.guard("entitySpawn", () => creatures.onEntitySpawn(event));
});

world.afterEvents.entityDie.subscribe((event) => {
  log.guard("entityDie", () => creatures.onEntityDie(event));
});

world.afterEvents.entityTamed.subscribe((event) => {
  log.guard("entityTamed", () => creatures.onTamed(event));
});

// --- developer diagnostics ---------------------------------------------------
system.afterEvents.scriptEventReceive.subscribe(
  (event) => {
    if (event.id !== "paleo:dump") {
      return;
    }
    const source = event.initiator;
    const text = log.dump();
    if (source && source.typeId === "minecraft:player") {
      source.sendMessage(text);
    }
    console.warn(text);
  },
  { namespaces: ["paleo"] },
);
