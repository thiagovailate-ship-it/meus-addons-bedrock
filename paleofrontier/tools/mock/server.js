/**
 * Headless mock of the @minecraft/server surface used by PALEOFRONTIER.
 *
 * It is deliberately small but faithful where it matters: events fire in the
 * order the harness asks for, dynamic properties persist in a plain object
 * (so a "world reload" can be simulated), inventories behave like containers
 * and getBlocks() really scans a block grid.
 */

let tick = 0;
const intervals = new Map();
let nextRunId = 1;

class Signal {
  constructor() {
    this.handlers = [];
  }
  subscribe(fn) {
    this.handlers.push(fn);
    return fn;
  }
  unsubscribe(fn) {
    this.handlers = this.handlers.filter((h) => h !== fn);
  }
  fire(event) {
    for (const handler of [...this.handlers]) {
      handler(event);
    }
  }
}

export class BlockVolume {
  constructor(min, max) {
    this.min = { ...min };
    this.max = { ...max };
  }
}

export class ListBlockVolume {
  constructor(locations) {
    this.locations = locations.map((l) => ({ ...l }));
  }
  getCapacity() {
    return this.locations.length;
  }
  getClosest(count, location) {
    const sorted = [...this.locations].sort((a, b) => dist2(a, location) - dist2(b, location));
    return sorted.slice(0, count);
  }
}

function dist2(a, b) {
  return (a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2;
}

export class BlockPermutation {
  constructor(typeId, states = {}) {
    this.type = { id: typeId };
    this.states = { ...states };
  }
  getState(name) {
    return this.states[name];
  }
  withState(name, value) {
    return new BlockPermutation(this.type.id, { ...this.states, [name]: value });
  }
  matches(typeId) {
    return this.type.id === typeId;
  }
}

export class Block {
  constructor(dimension, x, y, z, typeId, states = {}) {
    this.dimension = dimension;
    this.location = { x, y, z };
    this.x = x;
    this.y = y;
    this.z = z;
    this.permutation = new BlockPermutation(typeId, states);
    this.isValid = true;
    this.light = 4;
  }
  get typeId() {
    return this.permutation.type.id;
  }
  getLightLevel() {
    return this.light;
  }
  setPermutation(permutation) {
    this.permutation = permutation;
    this.dimension.setBlockRaw(this.location, permutation.type.id, permutation.states);
  }
  setType(typeId) {
    this.permutation = new BlockPermutation(typeId, {});
  }
}

export class ItemStack {
  constructor(typeId, amount = 1) {
    this.typeId = typeId;
    this.type = { id: typeId };
    this.amount = amount;
    this.maxAmount = 64;
    this.components = new Map();
    if (DURABILITY[typeId]) {
      this.components.set("minecraft:durability", {
        damage: 0,
        maxDurability: DURABILITY[typeId],
        unbreakable: false,
      });
    }
  }
  clone() {
    const copy = new ItemStack(this.typeId, this.amount);
    for (const [k, v] of this.components) {
      copy.components.set(k, { ...v });
    }
    return copy;
  }
  getComponent(id) {
    return this.components.get(id);
  }
}

const DURABILITY = {
  "paleo:brush": 192,
  "paleo:excavation_shovel": 640,
  "paleo:fossil_scanner": 320,
};

export class Container {
  constructor(size = 36) {
    this.size = size;
    this.slots = new Array(size).fill(undefined);
  }
  getItem(i) {
    return this.slots[i];
  }
  setItem(i, item) {
    this.slots[i] = item;
  }
  addItem(stack) {
    for (let i = 0; i < this.size; i += 1) {
      const existing = this.slots[i];
      if (existing && existing.typeId === stack.typeId && existing.amount < existing.maxAmount) {
        const space = existing.maxAmount - existing.amount;
        const move = Math.min(space, stack.amount);
        existing.amount += move;
        stack.amount -= move;
        if (stack.amount <= 0) return undefined;
      }
    }
    for (let i = 0; i < this.size; i += 1) {
      if (!this.slots[i]) {
        this.slots[i] = stack;
        return undefined;
      }
    }
    return stack;
  }
}

export class Entity {
  constructor(dimension, typeId, location) {
    this.dimension = dimension;
    this.typeId = typeId;
    this.location = { ...location };
    this.tags = new Set();
    this.events = [];
    this.isValid = true;
    this.id = `e${Math.random().toString(36).slice(2, 9)}`;
    this.height = 1;
  }
  addTag(tag) {
    this.tags.add(tag);
    return true;
  }
  hasTag(tag) {
    return this.tags.has(tag);
  }
  removeTag(tag) {
    return this.tags.delete(tag);
  }
  triggerEvent(name) {
    this.events.push(name);
  }
  getAABB() {
    return { width: 1, height: this.height };
  }
  playSound() {}
  spawnParticle() {}
}

export class ScreenDisplay {
  constructor(player) {
    this.player = player;
    this.actionBar = [];
    this.titles = [];
    this.subtitles = [];
  }
  setActionBar(text) {
    this.actionBar.push(text);
  }
  setTitle(text) {
    this.titles.push(text);
  }
  updateSubtitle(text) {
    this.subtitles.push(text);
  }
}

export class Player extends Entity {
  constructor(dimension, name, location) {
    super(dimension, "minecraft:player", location);
    this.name = name;
    this.selectedSlotIndex = 0;
    this.inventory = new Container();
    this.onScreenDisplay = new ScreenDisplay(this);
    this.messages = [];
    this.experience = 0;
    this.cooldowns = new Map();
    this.dynamic = new Map();
    this.soundLog = [];
  }
  getComponent(id) {
    if (id === "minecraft:inventory") {
      return { container: this.inventory };
    }
    return undefined;
  }
  sendMessage(text) {
    this.messages.push(text);
  }
  playSound(id) {
    this.soundLog.push(id);
  }
  spawnParticle() {}
  addExperience(n) {
    this.experience += n;
  }
  getItemCooldown(category) {
    return this.cooldowns.get(category) || 0;
  }
  startItemCooldown(category, ticks) {
    this.cooldowns.set(category, ticks);
  }
  getDynamicProperty(key) {
    return this.dynamic.get(key);
  }
  setDynamicProperty(key, value) {
    if (value === undefined) this.dynamic.delete(key);
    else this.dynamic.set(key, value);
  }
  give(typeId, amount = 1) {
    this.inventory.addItem(new ItemStack(typeId, amount));
  }
  hold(typeId) {
    this.inventory.setItem(this.selectedSlotIndex, new ItemStack(typeId, 1));
  }
}

export class Dimension {
  constructor(id) {
    this.id = id;
    this.blocks = new Map();
    this.heightRange = { min: -64, max: 320 };
    this.spawnedItems = [];
    this.particles = [];
    this.sounds = [];
    this.loaded = true;
  }
  key(x, y, z) {
    return `${x},${y},${z}`;
  }
  setBlockRaw(location, typeId, states = {}) {
    const key = this.key(location.x, location.y, location.z);
    const existing = this.blocks.get(key);
    if (existing) {
      existing.permutation = new BlockPermutation(typeId, states);
      return existing;
    }
    const block = new Block(this, location.x, location.y, location.z, typeId, states);
    this.blocks.set(key, block);
    return block;
  }
  setBlock(location, typeId, states = {}) {
    return this.setBlockRaw(location, typeId, states);
  }
  getBlock(location) {
    return this.blocks.get(this.key(location.x, location.y, location.z));
  }
  isChunkLoaded() {
    return this.loaded;
  }
  getBlocks(volume, options = {}, _allowUnloaded = false) {
    const include = options.includeTypes || [];
    const found = [];
    for (const block of this.blocks.values()) {
      if (!include.includes(block.typeId)) continue;
      if (
        block.x >= volume.min.x && block.x <= volume.max.x &&
        block.y >= volume.min.y && block.y <= volume.max.y &&
        block.z >= volume.min.z && block.z <= volume.max.z
      ) {
        found.push(block.location);
      }
    }
    return new ListBlockVolume(found);
  }
  getEntities(options = {}) {
    let list = [...this.entities.values()].filter((e) => e.isValid);
    if (options.families) {
      list = list.filter((e) => options.families.some((f) => e.tags.has(`family:${f}`) || FAMILY[e.typeId] === f));
    }
    if (options.location && options.maxDistance !== undefined) {
      list = list.filter((e) => Math.sqrt(dist2(e.location, options.location)) <= options.maxDistance);
    }
    if (options.closest) {
      list.sort((a, b) => dist2(a.location, options.location) - dist2(b.location, options.location));
      list = list.slice(0, options.closest);
    }
    return list;
  }
  getPlayers(options = {}) {
    let list = [...world.players.values()];
    if (options.location && options.maxDistance !== undefined) {
      list = list.filter((p) => Math.sqrt(dist2(p.location, options.location)) <= options.maxDistance);
    }
    return list;
  }
  spawnEntity(typeId, location) {
    const entity = new Entity(this, typeId, location);
    this.entities.set(entity.id, entity);
    world.afterEvents.entitySpawn.fire({ entity, cause: "spawned" });
    return entity;
  }
  spawnItem(stack, location) {
    this.spawnedItems.push({ typeId: stack.typeId, amount: stack.amount, location });
    return new Entity(this, "minecraft:item", location);
  }
  spawnParticle(name, location) {
    this.particles.push({ name, location });
  }
  playSound(name, location) {
    this.sounds.push({ name, location });
  }
}

const FAMILY = {
  "paleo:compsognathus": "paleo_dinosaur",
  "paleo:triceratops": "paleo_dinosaur",
  "paleo:velociraptor": "paleo_dinosaur",
  "paleo:tyrannosaurus": "paleo_dinosaur",
};

export const EquipmentSlot = {
  Mainhand: "Mainhand",
  Offhand: "Offhand",
  Head: "Head",
  Chest: "Chest",
  Legs: "Legs",
  Feet: "Feet",
};

export const world = {
  dimensions: new Map([
    ["minecraft:overworld", new Dimension("minecraft:overworld")],
  ]),
  players: new Map(),
  properties: new Map(),
  afterEvents: {
    worldLoad: new Signal(),
    playerJoin: new Signal(),
    playerLeave: new Signal(),
    itemUse: new Signal(),
    playerInteractWithBlock: new Signal(),
    playerBreakBlock: new Signal(),
    entitySpawn: new Signal(),
    entityDie: new Signal(),
    entityTamed: new Signal(),
  },
  beforeEvents: {
    playerBreakBlock: new Signal(),
    shutdown: new Signal(),
  },
  getDimension(id) {
    return this.dimensions.get(id);
  },
  getAllPlayers() {
    return [...this.players.values()];
  },
  getDynamicProperty(key) {
    return this.properties.get(key);
  },
  setDynamicProperty(key, value) {
    if (value === undefined) this.properties.delete(key);
    else this.properties.set(key, value);
  },
  sendMessage() {},
  addPlayer(name, location) {
    const player = new Player(this.getDimension("minecraft:overworld"), name, location);
    this.players.set(player.id, player);
    return player;
  },
};

for (const dimension of world.dimensions.values()) {
  dimension.entities = new Map();
}

export const system = {
  get currentTick() {
    return tick;
  },
  runInterval(fn, interval = 1) {
    const id = nextRunId;
    nextRunId += 1;
    intervals.set(id, { fn, interval, next: tick + interval });
    return id;
  },
  runTimeout(fn, delay = 0) {
    const id = nextRunId;
    nextRunId += 1;
    intervals.set(id, { fn, interval: 0, next: tick + delay, once: true });
    return id;
  },
  clearRun(id) {
    intervals.delete(id);
  },
  beforeEvents: { shutdown: new Signal() },
  afterEvents: { scriptEventReceive: new Signal() },
};

/** Advances the mock clock, firing due intervals like the game would. */
export function advanceTicks(count = 1) {
  for (let i = 0; i < count; i += 1) {
    tick += 1;
    for (const [id, task] of [...intervals]) {
      if (task.next <= tick) {
        if (task.once) {
          intervals.delete(id);
        } else {
          task.next = tick + task.interval;
        }
        task.fn();
      }
    }
    for (const player of world.getAllPlayers()) {
      for (const [category, value] of [...player.cooldowns]) {
        if (value <= 1) player.cooldowns.delete(category);
        else player.cooldowns.set(category, value - 1);
      }
    }
  }
}

export function resetTick(value = 0) {
  tick = value;
}

export { tick as _tick };
