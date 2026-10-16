/**
 * PALEOFRONTIER - periodic work.
 *
 * Every repeating task in the add-on is registered here with a name and a tick
 * interval.  Intervals are deliberately coarse (never per-tick) and every body
 * runs inside a guard so one bad frame cannot break the world loop.
 */

import { system } from "@minecraft/server";
import * as log from "./log.js";

/** @type {Map<string, number>} name -> run id */
const tasks = new Map();

export function every(name, tickInterval, body) {
  if (tasks.has(name)) {
    return;
  }
  const id = system.runInterval(() => {
    log.guard(`task.${name}`, body);
  }, tickInterval);
  tasks.set(name, id);
}

export function later(name, tickDelay, body) {
  system.runTimeout(() => {
    log.guard(`task.${name}`, body);
  }, tickDelay);
}

export function stop(name) {
  const id = tasks.get(name);
  if (id !== undefined) {
    system.clearRun(id);
    tasks.delete(name);
  }
}

/** Monotonic seconds, used for incubation timing. */
export function nowMs() {
  return Date.now();
}
