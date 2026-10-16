#!/usr/bin/env node
/**
 * PALEOFRONTIER headless play-through.
 *
 * Boots the real behavior-pack scripts against a mock of the Script API and
 * exercises the whole gameplay loop, asserting on observable effects:
 *
 *   1  bootstrap + welcome message
 *   2  scanner reports a REAL deposit (bearing/range/strength), honours cooldown
 *   3  excavation records recovered specimens in the journal
 *   4  research station consumes materials and identifies a species
 *   5  reconstruction pays costs and grants exactly one egg
 *   6  incubation progresses over time, stages the block and hatches once
 *   7  breaking an incubator refunds the egg exactly once
 *   8  progress survives a simulated world reload
 *   9  double taps open one form; players never share inventory state
 *  10  journal UI and the developer dump hook work
 *  11  mock fidelity guards (negative assertions: the mock must still reject the
 *      shapes the real client rejected)
 *  12  a BRAND NEW player can open every journal screen - regression for the
 *      second real client log ("cannot read property 'rex' of undefined")
 *
 * Usage: node tools/simulate.mjs
 */
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const PACK = dirname(HERE);
const SCRIPTS = join(PACK, "behavior_pack", "scripts");

// ---------------------------------------------------------------------------
// install the @minecraft/* shims so the pack scripts resolve normally
// ---------------------------------------------------------------------------
function shim(name, target) {
  const dir = join(PACK, "node_modules", "@minecraft", name);
  mkdirSync(dir, { recursive: true });
  writeFileSync(
    join(dir, "package.json"),
    JSON.stringify({ name: `@minecraft/${name}`, version: "0.0.0-mock", type: "module", main: "index.js" }, null, 2),
  );
  writeFileSync(join(dir, "index.js"), `export * from ${JSON.stringify(target)};\n`);
}
if (!existsSync(join(PACK, "node_modules", "@minecraft", "server"))) {
  shim("server", join(HERE, "mock", "server.js"));
  shim("server-ui", join(HERE, "mock", "server-ui.js"));
}

// controllable wall clock for incubation timing
const realNow = Date.now.bind(Date);
let clockOffset = 0;
Date.now = () => realNow() + clockOffset;

const server = await import(join(HERE, "mock", "server.js"));
const forms = await import(join(HERE, "mock", "server-ui.js"));
const { world, system, advanceTicks } = server;

let passed = 0;
const failures = [];
function check(name, condition, detail = "") {
  if (condition) {
    passed += 1;
    console.log(`  ok   ${name}`);
  } else {
    failures.push(name);
    console.error(`  FAIL ${name}${detail ? ` -- ${detail}` : ""}`);
  }
}
const flush = async (turns = 12) => {
  for (let i = 0; i < turns; i += 1) {
    await new Promise((resolve) => setImmediate(resolve));
  }
};
const translateOf = (raw) => (raw && typeof raw === "object" ? raw.translate : raw);
/**
 * Le os argumentos de um RawMessage.  A API oficial declara
 * `with?: string[] | RawMessage`, e core/text.js normaliza tudo para a forma
 * `{ rawtext: [...] }` (misturar traducao com numero num array simples faz o
 * cliente falhar com "Native variant type conversion failed").  As assercoes
 * leem por aqui para funcionarem nas duas formas oficiais.
 */
const withParts = (raw) => {
  if (!raw || typeof raw !== "object" || raw.with === undefined) return [];
  if (Array.isArray(raw.with)) {
    return raw.with.map((v) => (typeof v === "string" ? { text: v } : v));
  }
  return raw.with.rawtext || [];
};
const partText = (raw, i) => {
  const part = withParts(raw)[i];
  return part === undefined ? undefined : part.text;
};
/** Interactions are rate limited per player, so space harness actions out. */
const useItem = (player, typeId) => {
  advanceTicks(10);
  world.afterEvents.itemUse.fire({ source: player, itemStack: { typeId } });
};
const interact = (player, block) => {
  advanceTicks(10);
  world.afterEvents.playerInteractWithBlock.fire({
    player, block, isFirstEvent: true, itemStack: undefined,
  });
};

// ---------------------------------------------------------------------------
// world fixtures
// ---------------------------------------------------------------------------
const overworld = world.getDimension("minecraft:overworld");
overworld.setBlock({ x: 10, y: 60, z: 0 }, "paleo:fossil_deposit");
overworld.setBlock({ x: 18, y: 58, z: 6 }, "paleo:shale_matrix");
overworld.setBlock({ x: -40, y: 60, z: -40 }, "paleo:bone_bed");
const bench = overworld.setBlock({ x: 2, y: 60, z: 2 }, "paleo:research_bench");
const incubatorBlock = overworld.setBlock({ x: 30, y: 60, z: 0 }, "paleo:incubator", { "paleo:stage": 0 });

// ---------------------------------------------------------------------------
// boot
// ---------------------------------------------------------------------------
await import(join(SCRIPTS, "main.js"));
world.afterEvents.worldLoad.fire({});
const alice = world.addPlayer("Alice", { x: 0, y: 60, z: 0 });
const bob = world.addPlayer("Bob", { x: 4, y: 60, z: 4 });
// Forma REAL do evento (@minecraft/server 2.10.0): PlayerJoinAfterEvent expoe
// apenas playerId e playerName - NAO existe event.player.  O mock rejeita
// qualquer propriedade fora dessa lista, entao um harness que invente a forma
// do evento quebra aqui em vez de passar verde e falhar no cliente.
// (`join` ja e o import de node:path, dai fireJoin)
const fireJoin = (player) => {
  world.afterEvents.playerJoin.fire({ playerId: player.id, playerName: player.name });
  advanceTicks(1); // main.js usa system.run(), que so executa no tick seguinte
};
fireJoin(alice);
fireJoin(bob);
await flush();

const store = await import(join(SCRIPTS, "core", "store.js"));

console.log("\n[1] bootstrap & welcome");
check("welcome message delivered", alice.messages.some((m) => translateOf(m) === "paleo.ui.welcome"));
check("journal marked welcomed", store.journalFor(alice).welcomed === true);

console.log("\n[2] scanner");
alice.hold("paleo:fossil_scanner");
useItem(alice, "paleo:fossil_scanner");
await flush();
let bar = alice.onScreenDisplay.actionBar.at(-1);
check("scanner reports a deposit", translateOf(bar) === "paleo.ui.scan.found", JSON.stringify(bar));
check("scanner distance is real", Number(partText(bar, 1)) === 11, JSON.stringify(withParts(bar)));
check("scanner bearing east", withParts(bar)[2]?.translate === "paleo.ui.scan.dir.e");
advanceTicks(10);
useItem(alice, "paleo:fossil_scanner");
await flush();
check("scanner cooldown blocks spam",
  translateOf(alice.onScreenDisplay.actionBar.at(-1)) === "paleo.ui.scan.cooldown");
alice.cooldowns.delete("paleo_scanner");
overworld.blocks.delete(overworld.key(10, 60, 0));
overworld.blocks.delete(overworld.key(18, 58, 6));
useItem(alice, "paleo:fossil_scanner");
await flush();
check("scanner says none when empty",
  translateOf(alice.onScreenDisplay.actionBar.at(-1)) === "paleo.ui.scan.none");

console.log("\n[3] excavation bookkeeping");
overworld.setBlock({ x: 10, y: 60, z: 0 }, "paleo:fossil_deposit");
const broken = overworld.getBlock({ x: 10, y: 60, z: 0 });
world.afterEvents.playerBreakBlock.fire({
  player: alice,
  block: broken,
  brokenBlockPermutation: { type: { id: "paleo:fossil_deposit" } },
  itemStackBeforeBreak: { typeId: "paleo:brush" },
});
alice.give("paleo:specimen_compy", 1);
alice.give("paleo:amber_inclusion", 1);
advanceTicks(6);
await flush();
check("journal recorded the specimen", store.journalFor(alice).found.compy === 1);
check("journal recorded the amber", store.journalFor(alice).found.amber === 1);
check("discovery flourish shown",
  alice.onScreenDisplay.titles.some((t) => translateOf(t) === "paleo.ui.lab.discovered"));

console.log("\n[4] research station identifies a species");
alice.give("paleo:specimen_trike", 1);
alice.give("paleo:fossil_chip", 8);
alice.give("paleo:bone_shard", 4);
const chipsBefore = count(alice, "paleo:fossil_chip");
forms.setResponder((form) => {
  if (translateOf(form.title) === "paleo.ui.lab.title") return 0; // examine
  // carried specimens are listed in species order: compy first, trike second
  if (translateOf(form.title) === "paleo.ui.lab.examine") return 1;
  return -1;
});
interact(alice, bench);
await flush();
check("species identified in shared registry", Boolean(store.registry().identified.trike));
check("examination consumed the chips", count(alice, "paleo:fossil_chip") === chipsBefore - 8);
check("examination consumed the specimen", count(alice, "paleo:specimen_trike") === 0);
check("experience granted", alice.experience > 0);

console.log("\n[5] reconstruction grants exactly one egg");
alice.give("paleo:genetic_matrix", 2);
alice.give("paleo:specimen_trike", 2);
alice.give("paleo:nutrient_gel", 3);
forms.setResponder((form) => {
  if (translateOf(form.title) === "paleo.ui.lab.title") return 2; // reconstruct
  if (translateOf(form.title) === "paleo.ui.lab.reconstruct") return 0;
  return -1;
});
interact(alice, bench);
await flush();
check("one egg granted", count(alice, "paleo:egg_trike") === 1);
check("matrix consumed", count(alice, "paleo:genetic_matrix") === 0);
check("gel consumed", count(alice, "paleo:nutrient_gel") === 0);

console.log("\n[6] incubation progresses and hatches once");
alice.location = { x: 30, y: 60, z: 2 };
forms.setResponder((form) => {
  if (translateOf(form.title) === "paleo.ui.incubator.title") return 0; // insert first egg
  return -1;
});
interact(alice, incubatorBlock);
await flush();
check("egg consumed on insert", count(alice, "paleo:egg_trike") === 0);
check("incubation session stored", store.incubators().items.length === 1);
check("block staged at 0", incubatorBlock.permutation.getState("paleo:stage") === 0);
for (let step = 0; step < 80; step += 1) {
  clockOffset += 5000;
  advanceTicks(40);
}
await flush();
const hatched = [...overworld.entities.values()].filter((e) => e.typeId === "paleo:triceratops");
check("creature hatched", hatched.length === 1, `entities=${hatched.length}`);
check("hatch event fired", hatched[0] && hatched[0].events.includes("paleo:trike_hatched"));
check("raised marker applied", hatched[0] && hatched[0].tags.has("paleo:raised"));
check("session cleared after hatch", store.incubators().items.length === 0);
check("block stage reset", incubatorBlock.permutation.getState("paleo:stage") === 0);
check("hatch recorded in journal", store.journalFor(alice).hatched.trike === 1);

console.log("\n[7] breaking an incubator refunds exactly once");
alice.give("paleo:egg_compy", 1);
forms.setResponder((form) => (translateOf(form.title) === "paleo.ui.incubator.title" ? 0 : -1));
interact(alice, incubatorBlock);
await flush();
check("second session stored", store.incubators().items.length === 1);
world.afterEvents.playerBreakBlock.fire({
  player: alice,
  block: incubatorBlock,
  brokenBlockPermutation: { type: { id: "paleo:incubator" } },
  itemStackBeforeBreak: { typeId: "paleo:excavation_shovel" },
});
await flush();
const refunds = overworld.spawnedItems.filter((i) => i.typeId === "paleo:egg_compy");
check("egg refunded as a world item", refunds.length === 1, JSON.stringify(refunds));
check("session removed", store.incubators().items.length === 0);
check("player did not keep a copy", count(alice, "paleo:egg_compy") === 0);

console.log("\n[8] persistence survives a reload");
store.flush();
const rawRegistry = world.getDynamicProperty("paleo.world.registry");
const rawIncubators = world.getDynamicProperty("paleo.world.incubators");
check("registry persisted", typeof rawRegistry === "string" && rawRegistry.includes("trike"));
check("incubator list persisted", typeof rawIncubators === "string");
store.registry().identified = {};
store.loadWorld();
check("identified species restored from storage", Boolean(store.registry().identified.trike));
const journalRaw = alice.getDynamicProperty("paleo.player.journal");
check("journal persisted on the player", typeof journalRaw === "string" && journalRaw.includes("compy"));

console.log("\n[9] interaction hygiene");
forms.shownForms.length = 0;
advanceTicks(10);
world.afterEvents.playerInteractWithBlock.fire({
  player: alice, block: bench, isFirstEvent: true, itemStack: undefined,
});
world.afterEvents.playerInteractWithBlock.fire({
  player: alice, block: bench, isFirstEvent: true, itemStack: undefined,
});
await flush();
check("double tap opens a single form", forms.shownForms.length === 1, `forms=${forms.shownForms.length}`);
forms.setResponder(() => -1);
await flush();
const bobChips = count(bob, "paleo:fossil_chip");
check("other player inventory untouched", bobChips === 0);

console.log("\n[10] journal UI & diagnostics");
forms.shownForms.length = 0;
forms.setResponder((form) => {
  if (translateOf(form.title) === "paleo.ui.journal.title") return 1; // objectives
  return -1;
});
alice.hold("paleo:field_case");
advanceTicks(10);
useItem(alice, "paleo:field_case");
await flush();
check("journal opened from the field case",
  forms.shownForms.some((f) => translateOf(f.title) === "paleo.ui.journal.title"));
check("objectives screen reachable",
  forms.shownForms.some((f) => translateOf(f.title) === "paleo.ui.journal.objectives"));
let dumped = false;
const originalWarn = console.warn;
console.warn = (line) => {
  if (String(line).includes("paleo:")) dumped = true;
};
system.afterEvents.scriptEventReceive.fire({ id: "paleo:dump", initiator: alice });
console.warn = originalWarn;
check("diagnostic dump hook responds", dumped);

// ---------------------------------------------------------------------------
// Guardas de fidelidade do mock.  Estas assercoes sao NEGATIVAS: elas provam
// que o harness reprova as duas formas de erro que passaram verde na primeira
// versao e so apareceram no cliente (log real de iOS, Bedrock 1.26.52):
//   1. playerJoin com `event.player` (a API so expoe playerId/playerName)
//      -> "cannot read property 'id' of undefined"
//   2. RawMessage com `with: [{translate}, numero]` (a API declara
//      string[] | RawMessage) -> "Native variant type conversion failed"
// Se um dia o mock afrouxar, estas linhas falham.
// ---------------------------------------------------------------------------
console.log("\n[11] mock fidelity guards");
const throwsWith = (fn, needle) => {
  try {
    fn();
    return false;
  } catch (err) {
    return String(err.message).includes(needle);
  }
};
check(
  "mock rejeita playerJoin com event.player (forma que nao existe na API)",
  throwsWith(
    () => world.afterEvents.playerJoin.fire({ player: alice }),
    "NAO existe na API oficial",
  ),
);
check(
  "mock rejeita RawMessage com array misto em 'with'",
  throwsWith(
    () => alice.sendMessage({ translate: "paleo.ui.welcome", with: [{ translate: "x" }, 3] }),
    "Native variant type conversion failed",
  ),
);
check(
  "mock aceita a forma normalizada por core/text.js",
  (() => {
    try {
      alice.sendMessage({ translate: "paleo.ui.welcome", with: { rawtext: [{ translate: "x" }, { text: "3" }] } });
      return true;
    } catch (err) {
      return false;
    }
  })(),
);

// ---------------------------------------------------------------------------
// [12] Regressao do SEGUNDO log real do cliente (Bedrock 1.26.52, iOS):
//   [Scripting][error]-[paleo:error] journal_ui.open: cannot read property
//   'rex' of undefined
// Causa: a fabrica do journal declarava os buckets found/studied/hatched/raised,
// mas o codigo lia `.bonded` - e `raised` nunca foi usado por ninguem.  Como
// `bumpJournal` se autocorrigia ao ESCREVER, o bug so aparecia num jogador que
// nunca tinha criado um vinculo: exatamente quem abre o diario pela primeira
// vez.  As secoes anteriores usam a Alice (que ja jogou) e navegam apenas ate
// "objectives", caminho que nao le `bonded`; por isso o harness passou verde.
// Aqui um jogador novo visita as duas telas que leem o bucket.
// ---------------------------------------------------------------------------
console.log("\n[12] journal de jogador novo (regressao do 2o log real)");
const carol = world.addPlayer("Carol", { x: 8, y: 60, z: 8 });
fireJoin(carol);
await flush();

const errorLines = [];
const originalError = console.error;
console.error = (line) => {
  errorLines.push(String(line));
};

// Diario -> "creatures" (indice 2): chama bondedCount para cada especie.
forms.shownForms.length = 0;
forms.setResponder((form) => {
  if (translateOf(form.title) === "paleo.ui.journal.title") return 2;
  return -1;
});
carol.hold("paleo:field_case");
advanceTicks(10);
useItem(carol, "paleo:field_case");
await flush();
check("jogador novo abre a tela de criaturas do diario",
  forms.shownForms.some((f) => translateOf(f.title) === "paleo.ui.journal.creatures"));

// Diario -> "species" (0) -> dossier de cada especie: dossierLines tambem le
// bondedCount.  speciesMenu e dossier usam o MESMO titulo, entao a navegacao
// conta as aparicoes: a primeira e o menu de especies, a segunda e o dossier.
let speciesTitleCount = 0;
for (const speciesIndex of [0, 1, 2, 3]) {
  let appearances = 0;
  forms.setResponder((form) => {
    const title = translateOf(form.title);
    if (title === "paleo.ui.journal.title") return 0;
    if (title === "paleo.ui.journal.species") {
      appearances += 1;
      speciesTitleCount += 1;
      return appearances === 1 ? speciesIndex : -1;
    }
    return -1;
  });
  advanceTicks(10);
  useItem(carol, "paleo:field_case");
  await flush();
}
check("jogador novo abre o dossier das 4 especies", speciesTitleCount === 8);

console.error = originalError;
const journalErrors = errorLines.filter((line) => line.includes("journal_ui"));
check("diario de jogador novo nao emite erro de script", journalErrors.length === 0);
for (const line of journalErrors) originalError(`    capturado: ${line}`);

console.log(`\n[simulate] ${passed} assertions passed, ${failures.length} failed`);
if (failures.length) {
  for (const f of failures) console.error(`  - ${f}`);
  process.exit(1);
}

function count(player, typeId) {
  let total = 0;
  for (let i = 0; i < player.inventory.size; i += 1) {
    const item = player.inventory.getItem(i);
    if (item && item.typeId === typeId) total += item.amount;
  }
  return total;
}
