/**
 * PALEOFRONTIER - construcao de RawMessage.
 *
 * Por que este modulo existe
 * --------------------------
 * A API oficial declara (@minecraft/server 2.10.0):
 *
 *     interface RawMessage {
 *       translate?: string;
 *       with?: string[] | RawMessage;   // <-- OU array de strings, OU 1 RawMessage
 *       ...
 *     }
 *
 * Um array **misto** - por exemplo `with: [{ translate: "x" }, 3]` - nao e
 * nenhuma das duas formas aceitas.  O cliente tenta converter isso para o tipo
 * nativo e falha com:
 *
 *     [Scripting][error]-[paleo:error] lab_ui.open: Native variant type
 *     conversion failed.
 *
 * Como o formulario inteiro e construido antes de `show()`, um unico `with`
 * invalido derruba a tela toda (e o erro sai com o rotulo do ponto de entrada,
 * nao da linha exata).
 *
 * A forma oficial de misturar texto traduzido com valores dinamicos e um
 * RawMessage unico contendo `rawtext`:
 *
 *     { translate: "paleo.ui.x", with: { rawtext: [ { translate: "y" }, { text: "3" } ] } }
 *
 * Todo `with` deste pacote passa por `args()`, que garante essa forma e
 * converte numeros/booleanos em `{ text: String(v) }`.
 */

/** Converte um valor qualquer em um RawMessage valido. */
export function toRaw(value) {
  if (value === null || value === undefined) {
    return { text: "" };
  }
  if (typeof value === "object") {
    return value;
  }
  return { text: String(value) };
}

/**
 * Normaliza argumentos de traducao para a forma `string[] | RawMessage`.
 * Aceita um array (ou valor unico) com strings, numeros, booleanos e
 * RawMessages misturados.
 */
export function args(values) {
  const list = Array.isArray(values) ? values : [values];
  if (list.length === 0) {
    return { text: "" };
  }
  // Tudo string?  A forma `string[]` e a mais barata e tambem e oficial.
  if (list.every((v) => typeof v === "string")) {
    return list.slice();
  }
  return { rawtext: list.map(toRaw) };
}

/**
 * Atalho para mensagens traduzidas com argumentos:
 *   tr("paleo.ui.x")            -> { translate: "paleo.ui.x" }
 *   tr("paleo.ui.x", name, 3)   -> { translate: "paleo.ui.x", with: <normalizado> }
 */
export function tr(key, ...values) {
  return values.length > 0 ? { translate: key, with: args(values) } : { translate: key };
}

/**
 * Valida um RawMessage antes de entrega-lo ao cliente.  Usado pelos testes
 * (tools/mock) para reproduzir a conversao nativa e falhar cedo, no harness,
 * em vez de falhar silenciosamente dentro do jogo.
 */
export function assertRawMessage(value, where) {
  if (value === undefined || value === null || typeof value === "string") {
    return;
  }
  if (typeof value !== "object") {
    throw new TypeError(`${where}: RawMessage precisa ser string ou objeto`);
  }
  const withValue = value.with;
  if (withValue === undefined) {
    return;
  }
  if (Array.isArray(withValue)) {
    if (!withValue.every((v) => typeof v === "string")) {
      throw new TypeError(
        `${where}: 'with' como array so aceita strings (a API declara ` +
          `string[] | RawMessage); use args() de core/text.js`,
      );
    }
    return;
  }
  if (typeof withValue !== "object") {
    throw new TypeError(`${where}: 'with' precisa ser string[] ou RawMessage`);
  }
  for (const part of withValue.rawtext || []) {
    assertRawMessage(part, `${where}.with.rawtext`);
  }
}
