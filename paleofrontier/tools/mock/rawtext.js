/**
 * Validacao de RawMessage compartilhada pelos mocks de @minecraft/server e
 * @minecraft/server-ui.
 *
 * Contrato oficial (@minecraft/server 2.10.0, index.d.ts):
 *
 *     interface RawMessage {
 *       rawtext?: RawMessage[];
 *       score?: RawMessageScore;
 *       text?: string;
 *       translate?: string;
 *       with?: string[] | RawMessage;      // <-- a armadilha
 *     }
 *
 * `with` aceita OU um array de strings OU um unico RawMessage.  Um array misto
 * (`[{translate:"x"}, 3]`) nao e nenhum dos dois e o cliente falha com
 * "Native variant type conversion failed", derrubando a tela/mensagem inteira.
 * Reproduzir isso no mock faz o harness falhar no ponto certo, em vez de passar
 * verde e quebrar dentro do jogo.
 */

const ALLOWED_KEYS = new Set([
  "rawtext",
  "score",
  "text",
  "translate",
  "with",
  "json",
  "selector",
]);

export function checkRawMessage(value, where) {
  if (value === undefined || value === null || typeof value === "string") {
    return;
  }
  if (typeof value !== "object" || Array.isArray(value)) {
    throw new TypeError(
      `${where}: Native variant type conversion failed (esperava string ou RawMessage, veio ${typeof value})`,
    );
  }
  for (const key of Object.keys(value)) {
    if (!ALLOWED_KEYS.has(key)) {
      throw new TypeError(
        `${where}: RawMessage tem a chave desconhecida '${key}' (oficiais: ${[...ALLOWED_KEYS].join(", ")})`,
      );
    }
  }
  if (value.translate !== undefined && typeof value.translate !== "string") {
    throw new TypeError(`${where}: 'translate' precisa ser string`);
  }
  if (value.text !== undefined && typeof value.text !== "string") {
    throw new TypeError(`${where}: 'text' precisa ser string`);
  }
  if (Array.isArray(value.rawtext)) {
    value.rawtext.forEach((part, i) => checkRawMessage(part, `${where}.rawtext[${i}]`));
  }
  const withValue = value.with;
  if (withValue === undefined) {
    return;
  }
  if (Array.isArray(withValue)) {
    if (!withValue.every((entry) => typeof entry === "string")) {
      throw new TypeError(
        `${where}: Native variant type conversion failed - 'with' como array SO aceita ` +
          `strings (a API declara string[] | RawMessage); recebeu ${JSON.stringify(withValue).slice(0, 90)}. ` +
          `Use args() de core/text.js para misturar traducao com numeros.`,
      );
    }
    return;
  }
  if (typeof withValue !== "object" || withValue === null) {
    throw new TypeError(`${where}: 'with' precisa ser string[] ou RawMessage`);
  }
  checkRawMessage(withValue, `${where}.with`);
}
