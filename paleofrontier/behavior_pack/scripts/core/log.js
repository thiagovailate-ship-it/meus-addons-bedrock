/**
 * PALEOFRONTIER - diagnostics.
 *
 * The add-on must never spam the chat.  Every diagnostic is deduplicated by key
 * and only the first occurrence is pushed to the console; a rolling in-memory
 * buffer keeps the last entries so a developer can inspect them with
 *   /scriptevent paleo:dump
 * (handled in main.js) without touching gameplay.
 */

const BUFFER_LIMIT = 120;

/** @type {string[]} */
const ring = [];
/** @type {Set<string>} */
const seen = new Set();

function push(level, key, message) {
  const line = `[paleo:${level}] ${key}: ${message}`;
  ring.push(line);
  if (ring.length > BUFFER_LIMIT) {
    ring.shift();
  }
  if (seen.has(key + level)) {
    return;
  }
  seen.add(key + level);
  if (level === "error") {
    console.error(line);
  } else {
    console.warn(line);
  }
}

export function warn(key, message) {
  push("warn", key, message);
}

export function error(key, message) {
  push("error", key, message);
}

/** Wraps a callback so a failure never breaks the game loop. */
export function guard(key, fn) {
  try {
    return fn();
  } catch (err) {
    error(key, err && err.message ? err.message : String(err));
    return undefined;
  }
}

export function dump() {
  return ring.slice(-25).join("\n") || "paleo: diagnostic buffer is empty";
}
