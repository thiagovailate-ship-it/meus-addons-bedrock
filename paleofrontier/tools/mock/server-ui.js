/**
 * Headless mock of @minecraft/server-ui.
 *
 * The harness installs a responder: a function that receives the built form
 * (title/body/buttons/labels) and returns the selection index (or -1 to cancel).
 * Every form shown is recorded so tests can assert on what the player saw.
 */

import { checkRawMessage } from "./rawtext.js";

export const shownForms = [];
let responder = () => -1;

export function setResponder(fn) {
  responder = fn;
}

class BaseForm {
  constructor(kind) {
    this.kind = kind;
    this.titleText = undefined;
    this.bodyText = undefined;
    this.buttons = [];
    this.labels = [];
  }
  title(text) {
    checkRawMessage(text, `${this.kind}.title`);
    this.titleText = text;
    return this;
  }
  body(text) {
    checkRawMessage(text, `${this.kind}.body`);
    this.bodyText = text;
    return this;
  }
  label(text) {
    checkRawMessage(text, `${this.kind}.label`);
    this.labels.push(text);
    return this;
  }
  button(text) {
    checkRawMessage(text, `${this.kind}.button`);
    this.buttons.push(text);
    return this;
  }
  async show(player) {
    const record = {
      kind: this.kind,
      player: player.name,
      title: this.titleText,
      body: this.bodyText,
      buttons: this.buttons,
      labels: this.labels,
    };
    shownForms.push(record);
    const selection = responder(record);
    return { canceled: selection < 0, selection: selection < 0 ? undefined : selection };
  }
}

export class ActionFormData extends BaseForm {
  constructor() {
    super("action");
  }
  divider() {
    return this;
  }
  header(text) {
    return this.title(text);
  }
}

export class MessageFormData extends BaseForm {
  constructor() {
    super("message");
  }
  button1(text) {
    return this.button(text);
  }
  button2(text) {
    return this.button(text);
  }
}

export class ModalFormData extends BaseForm {
  constructor() {
    super("modal");
  }
  dropdown() {
    return this;
  }
  slider() {
    return this;
  }
  textField() {
    return this;
  }
  toggle() {
    return this;
  }
  submitButton(text) {
    return this.button(text);
  }
}
