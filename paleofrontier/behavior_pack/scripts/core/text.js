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
    // NAO existe "with vazio" valido.  Devolver `{ text: "" }` aqui produzia
    //   { translate: "paleo.ui.obj.gear", with: { text: "" } }
    // e o cliente respondia:
    //   [Scripting][error]-[paleo:error] journal_ui.open: Failed to resolve raw
    //   message from json
    // Quem nao tem argumento tem que OMITIR o `with` inteiro - para isso existem
    // translateWith() e tr().  Retornar undefined faz qualquer sitio que ignore
    // essa regra falhar no mock em vez de falhar no jogo.
    return undefined;
  }
  // Tudo string?  A forma `string[]` e a mais barata e tambem e oficial.
  if (list.every((v) => typeof v === "string")) {
    return list.slice();
  }
  return { rawtext: list.map(toRaw) };
}

/**
 * Constroi `{ translate }` omitindo o `with` quando nao ha argumentos.
 *
 *   translateWith("paleo.ui.obj.gear")          -> { translate: "paleo.ui.obj.gear" }
 *   translateWith("paleo.ui.obj.all", [2, 4])   -> { translate: ..., with: ["2","4"] }
 *
 * Use esta funcao sempre que a lista de argumentos puder vir vazia (ex.: um
 * passo de objetivo que nao tem parametros).
 */
export function translateWith(key, values) {
  const normalized = args(values);
  return normalized === undefined ? { translate: key } : { translate: key, with: normalized };
}

/**
 * Atalho para mensagens traduzidas com argumentos:
 *   tr("paleo.ui.x")            -> { translate: "paleo.ui.x" }
 *   tr("paleo.ui.x", name, 3)   -> { translate: "paleo.ui.x", with: <normalizado> }
 */
export function tr(key, ...values) {
  return translateWith(key, values);
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
  // `with` presente mas vazio nao e resolvivel pelo cliente:
  //   Failed to resolve raw message from json
  // Quem nao tem argumento deve omitir a chave (translateWith()/tr() fazem isso).
  if (Array.isArray(withValue) && withValue.length === 0) {
    throw new TypeError(`${where}: 'with' vazio - omita a chave quando nao houver argumentos`);
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
  if (Array.isArray(withValue.rawtext) && withValue.rawtext.length === 0) {
    throw new TypeError(`${where}: 'with.rawtext' vazio - omita a chave quando nao houver argumentos`);
  }
  if (withValue.text === "" && Object.keys(withValue).length === 1) {
    throw new TypeError(
      `${where}: 'with: { text: "" }' nao e resolvivel pelo cliente - omita a chave ` +
        `quando nao houver argumentos (use translateWith() de core/text.js)`,
    );
  }
  for (const part of withValue.rawtext || []) {
    assertRawMessage(part, `${where}.with.rawtext`);
  }
}
