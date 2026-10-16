/**
 * PALEOFRONTIER - inventory helpers.
 *
 * All material checks/transactions in the add-on go through these functions so
 * that a laboratory operation can never hand out items that were not paid for.
 */

import { ItemStack, EquipmentSlot, world } from "@minecraft/server";
import * as log from "./log.js";

export function containerOf(player) {
  const inv = player.getComponent("minecraft:inventory");
  return inv ? inv.container : undefined;
}

export function countItem(player, typeId) {
  const container = containerOf(player);
  if (!container) {
    return 0;
  }
  let total = 0;
  for (let i = 0; i < container.size; i++) {
    const slot = container.getItem(i);
    if (slot && slot.typeId === typeId) {
      total += slot.amount;
    }
  }
  return total;
}

/** @param {string[][]} list of [typeId, amount] */
export function hasAll(player, list) {
  return list.every(([typeId, amount]) => countItem(player, typeId) >= amount);
}

/** Removes items; returns false (and removes nothing) when unaffordable. */
export function consumeAll(player, list) {
  if (!hasAll(player, list)) {
    return false;
  }
  const container = containerOf(player);
  if (!container) {
    return false;
  }
  for (const [typeId, amount] of list) {
    let left = amount;
    for (let i = 0; i < container.size && left > 0; i++) {
      const slot = container.getItem(i);
      if (!slot || slot.typeId !== typeId) {
        continue;
      }
      const take = Math.min(left, slot.amount);
      if (take === slot.amount) {
        container.setItem(i, undefined);
      } else {
        const rest = slot.clone();
        rest.amount = slot.amount - take;
        container.setItem(i, rest);
      }
      left -= take;
    }
  }
  return true;
}

/** Grants items; overflow is dropped at the player's feet instead of vanishing. */
export function grantAll(player, list) {
  const container = containerOf(player);
  for (const [typeId, amount] of list) {
    let left = amount;
    while (left > 0) {
      const stack = new ItemStack(typeId, Math.min(left, 64));
      const leftover = container ? container.addItem(stack) : stack;
      if (!leftover) {
        left -= stack.amount;
        continue;
      }
      left -= stack.amount - leftover.amount;
      if (leftover.amount > 0) {
        log.guard("inventory.grant", () => {
          player.dimension.spawnItem(leftover, {
            x: player.location.x,
            y: player.location.y + 1,
            z: player.location.z,
          });
        });
        left -= leftover.amount;
      }
    }
  }
}

export function heldItem(player) {
  const container = containerOf(player);
  if (!container) {
    return undefined;
  }
  return container.getItem(player.selectedSlotIndex);
}

export function heldTypeId(player) {
  const item = heldItem(player);
  return item ? item.typeId : undefined;
}

/** Applies durability damage to the held tool; breaks it when worn out. */
export function damageHeld(player, amount = 1) {
  log.guard("inventory.damageHeld", () => {
    const container = containerOf(player);
    if (!container) {
      return;
    }
    const index = player.selectedSlotIndex;
    const item = container.getItem(index);
    if (!item) {
      return;
    }
    const durability = item.getComponent("minecraft:durability");
    if (!durability || durability.unbreakable) {
      return;
    }
    const next = durability.damage + amount;
    if (next >= durability.maxDurability) {
      container.setItem(index, undefined);
      player.playSound("random.break");
      player.sendMessage({ translate: "paleo.ui.tool.broken" });
      return;
    }
    durability.damage = next;
    container.setItem(index, item);
  });
}

/** Removes one specific item type regardless of stack layout. */
export function removeAll(player, typeId) {
  const container = containerOf(player);
  if (!container) {
    return 0;
  }
  let removed = 0;
  for (let i = 0; i < container.size; i++) {
    const slot = container.getItem(i);
    if (slot && slot.typeId === typeId) {
      removed += slot.amount;
      container.setItem(i, undefined);
    }
  }
  return removed;
}

export function playersNear(entity, radius, familyFilter) {
  return log.guard("inventory.playersNear", () =>
    entity.dimension.getPlayers({
      location: entity.location,
      maxDistance: radius,
    })) || [];
}

export { EquipmentSlot, world };
