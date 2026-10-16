/**
 * PALEOFRONTIER - form plumbing.
 *
 * Bedrock only presents one form per player at a time and a double tap could
 * otherwise start two flows for the same station.  Root entry points claim the
 * player; nested navigation runs inside that claim and never re-claims.
 */

import * as log from "../core/log.js";

const claimed = new Set();

export function claim(player) {
  if (claimed.has(player.id)) {
    return false;
  }
  claimed.add(player.id);
  return true;
}

export function release(player) {
  claimed.delete(player.id);
}

export function isClaimed(player) {
  return claimed.has(player.id);
}

/** Runs an async form flow, always releasing the claim and never throwing. */
export async function run(player, key, body) {
  if (!claim(player)) {
    return;
  }
  try {
    await body();
  } catch (err) {
    log.error(key, err && err.message ? err.message : String(err));
  } finally {
    release(player);
  }
}
