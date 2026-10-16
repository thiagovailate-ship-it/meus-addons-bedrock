# PALEOFRONTIER — relatório de testes

Ambiente de teste: sandbox Linux (Node 22, Python 3.11) com os schemas oficiais
`Mojang/bedrock-schemas` (1.26.60-beta.24), as type definitions oficiais
`@minecraft/server@2.10.0` / `@minecraft/server-ui@2.2.0` (npm) e a documentação
oficial (`MicrosoftDocs/minecraft-creator`, `Mojang/bedrock-samples` 1.26.50.4).

**Não havia instância executável do Minecraft Bedrock neste ambiente** durante o
desenvolvimento. Tudo o que podia ser verificado sem o cliente foi verificado; o
que exigia o cliente estava declarado em `docs/LIMITATIONS.md`.

**Atualização: uma rodada real no cliente aconteceu** (Bedrock 1.26.52, iOS) e o
log foi analisado linha a linha. Ela está documentada na Camada 0 abaixo, junto
com o que cada erro revelou, a correção aplicada e a checagem permanente que foi
criada para que a mesma classe de erro não volte a passar.

## Camada 0 — teste real no cliente (Bedrock 1.26.52, iOS)

O log real apontou 7 classes de erro. **Nenhuma delas era detectável pelas
camadas 1–4 da forma como estavam**: os schemas oficiais da Mojang são lenientes
nesses pontos, e o mock do harness era menos fiel que o cliente. Todas foram
corrigidas na fonte (`tools/content_model.py` e geradores, não nos arquivos
gerados) e cada uma virou uma checagem permanente.

| # | Erro no log do cliente | Causa raiz | Correção | Regra permanente criada |
|---|---|---|---|---|
| 1 | `menu_category -> group: string must be prefixed with a namespace` (3 blocos) | `group: "itemGroup.name.ore"` sem namespace; validação estrita desde 1.26.20 | `"minecraft:itemGroup.name.ore"` + normalização defensiva no gerador | camada 4: group namespaced **e** pertencente à lista oficial de grupos vanilla |
| 2 | `minecraft:fire_resistant: expected an object` + `Missing icon for data-driven item` (4 ovos) | componente escrito como booleano; forma vanilla é `{"value": true}`. O ícone "sumido" era consequência do parse abortado | `{"value": true}` | camada 4: tabela de componentes de item que só aceitam objeto |
| 3 | `1.20+ Recipes require unlock data` (6 receitas) | campo `unlock` ausente | `"unlock": {"context": "AlwaysUnlocked"}` | camada 4: `unlock` obrigatório |
| 4 | `Event name 'power_on' is not a valid LevelSoundEvent` (9 eventos) | eventos de som escritos com underscore; o cliente usa notação com ponto | `item.use.on`, `power.on`, `power.off`, `attack.strong`, `prepare.attack` | camada 4: nomes confrontados com os 44+166 eventos extraídos do `sounds.json` vanilla |
| 5 | `animations \| attack \| blend_out_time \| child not valid here` (4 animações) | `blend_out_time` não existe no formato de animação | removido; blending movido para o **animation controller** (`blend_transition` 0.2/0.3), que é o lugar oficial | camada 4: chaves de animação ⊆ as 8 chaves usadas pelas 700+ animações vanilla |
| 6 | `client_entity \| description \| animation_controllers \| child not valid here` (4 arquivos) | ruído do parser de animação — **reproduzível até no `iron_golem.entity.json` vanilla** | adotado o padrão do `armor_stand`: controller em `animations` + `scripts.animate`, sem a chave | camada 4: rejeita `animation_controllers` em client entity e exige que `scripts.animate` referencie nomes declarados |
| 7 | `minecraft:pushable: not present in the Schema` → **as 4 entidades não carregavam** | `minecraft:pushable` deixou de ser parseado no 1.26.10 (dividido em `pushable_by_entity` / `pushable_by_block`) | componentes substituídos preservando a semântica exata (trike: só pistão; rex: nenhum) | camada 6: componentes removidos, **gated por format_version** |
| 8 | `[paleo:error] join: cannot read property 'id' of undefined` | `PlayerJoinAfterEvent` expõe só `playerId`/`playerName`; **não existe `event.player`** | `world.getEntity(event.playerId)` dentro de `system.run()` | mock agora **rejeita** eventos com forma inventada; camada 5 varre os scripts |
| 9 | `[paleo:error] lab_ui.open / journal_ui.open: Native variant type conversion failed` | `RawMessage.with` é declarado `string[] \| RawMessage`; os 35 usos passavam array **misto** (`[{translate}, número]`) | novo `scripts/core/text.js` com `args()`/`tr()`; 36 sítios normalizados para `{rawtext: [...]}` | mock reproduz a conversão nativa e falha; camada 5 exige `args()` em todo `with:` |

### Dois bugs que o log não mostrou (e que só a análise estática pegou)

O log do cliente **mascara** o que está atrás de uma falha de parse. Cruzando os
update notes oficiais 1.26.x com os componentes usados, apareceram dois problemas
que a próxima rodada de teste revelaria:

- **Receitas inalcançáveis (grave).** As 6 receitas usavam tags customizadas
  (`paleo_field_gear`, `paleo_station`). O jogo só reconhece tags de menu
  oficiais (`crafting_table`, `furnace`, …): com tag desconhecida a receita
  **não aparece em bancada nenhuma**, e a progressão inteira ficaria travada sem
  nenhum erro no log. Corrigido para `crafting_table` + checagem permanente
  contra as 11 tags oficiais.
- **`attack_interval` escalar.** `minecraft:behavior.nearest_attackable_target`
  exige `{"min","max"}` desde 1.26.0 (3 ocorrências). Estava invisível porque as
  entidades abortavam o parse antes, em `pushable`. Corrigido preservando o valor
  exato. Já `defend_trusted_target.attack_interval` segue **inteiro** — o schema
  oficial o declara `"type": "integer"`, e mudar isso teria sido um falso positivo.

### Por que o harness não pegou nada disso

Duas lacunas de fidelidade, ambas corrigidas:

1. O mock entregava `playerJoin` com `{ player }`, forma que **não existe** na
   API. Agora cada `Signal` conhece as propriedades reais do evento
   (`EVENT_SHAPES`, copiado do `index.d.ts`) e **lança erro** se o harness
   inventar uma.
2. O mock de UI aceitava qualquer valor em `title/body/label/button`. Agora
   reproduz a conversão nativa de `RawMessage` e falha com a mesma mensagem do
   cliente.

A seção `[11] mock fidelity guards` do play-through existe para provar que esses
dois guardas têm dentes: são asserções **negativas** (disparam a forma errada de
propósito e exigem que o mock reprova).

### Calibração: as regras novas não acusam o conteúdo da Mojang

Uma regra de validação só vale se o conteúdo oficial passar por ela.
`tools/calibrate_entity_rules.py` aplica as regras a **todas as 128 entidades do
bedrock-samples 1.26.50.4**:

| Regra | Severidade | Resultado no vanilla |
|---|---|---|
| componente removido (`pushable`) | FAIL | **limpa** (0 violações) |
| campo float-range fora de `{min,max}` | FAIL | **limpa** (0 violações) |
| campo ausente do form oficial | aviso | 35 divergências → os forms são incompletos |
| tipo divergente do form | aviso | 41 divergências → os forms são lenientes |

O detalhe que torna as duas primeiras confiáveis é o **gating por
`format_version`**: os samples trazem arquivos legado (`creeper.json` fv 1.26.0
com `pushable`, `bat.json` fv 1.26.0 com `float_duration` em array) que o cliente
continua aceitando e migrando. Sem o gating, a regra acusaria a Mojang; com ele,
aplica-se exatamente onde o cliente aplica — e as nossas entidades são fv 1.26.50.

Duas fontes também se mostraram insuficientes sozinhas, e isso está codificado:
os forms oficiais declaram `tempt.items` como `string` quando o vanilla usa
**lista**, e `despawn_from_distance` como `objectArray` quando o vanilla usa
**objeto**. Por isso esses dois casos são aviso, não falha.

## Camada 1 — schemas oficiais (ajv, draft-07)

`tools/schema_check.mjs` valida cada JSON do pacote contra o schema oficial
correspondente (blocos, itens, entidades, loot, features, feature_rules,
spawn_rules, manifestos, modelos, animações, animation/render controllers,
client entities, sound definitions, terrain/item atlases).

Resultado: **62 arquivos validados, 0 falhas.**

Divergências documentadas (não são defeitos do pacote):
- `bp/blocks`, `bp/entities` e `rp/particles`: o conjunto oficial tem um `$ref`
  pendente (`../../common/expression.schema.json`, arquivo inexistente no repo da
  Mojang) → essas famílias são puladas com aviso (`SKIP`) e cobertas pelas
  camadas 2/3.
- `bp/recipes`: o repo oficial só publica o schema de *brewing mix*; receitas
  shaped são validadas estruturalmente na camada 3.
- `rp/texts/languages.json`: o schema oficial modela a lista de locales como
  objeto, enquanto o jogo (e o próprio arquivo da Mojang) usa array → validado
  estruturalmente na camada 3.
- Campos numéricos de geometria (`pivot/origin/size/uv`) e `version` do manifesto
  RP: o schema oficial tipa como string (molang) enquanto todo conteúdo vanilla
  usa números/arrays → normalizados apenas na cópia validada, com nota no código.

## Camada 2 — estrutura

- Todo `.json` dos dois pacotes parseia (0 erros de sintaxe).
- Nenhum arquivo vazio (202 arquivos de pacote verificados).
- Manifestos: UUIDs únicos entre BP/RP, BP depende do UUID do header do RP,
  dependências de módulo `@minecraft/server 2.10.0` e `@minecraft/server-ui 2.2.0`
  (versões estáveis correspondentes ao 1.26.52), entry `scripts/main.js` existe.

## Camada 3 — integridade de referências cruzadas

`tools/validate.py` garante, entre outros:
- geometrias/material instances de blocos → entradas do `terrain_texture.json` →
  arquivos `.png` existentes;
- ícones de itens → `item_texture.json` → `.png` existentes;
- loot tables e receitas → apenas ids `paleo:*` realmente definidos;
- identifiers de features = nome do arquivo; `places_feature` resolve;
- spawn rules → entidades existentes;
- entidades: todo evento referenciado existe, todo component group referenciado
  existe, loot tables existem;
- client entities: animações, animation controllers, render controllers,
  geometrias, texturas e spawn-egg texture todos definidos/existentes; arrays dos
  render controllers mapeiam para texturas/geometrias declaradas;
- `sounds.json` → `sound_definitions.json` → 45 arquivos `.ogg` existentes;
- traduções: toda chave `translate` usada pelos scripts e toda chave derivada do
  modelo de conteúdo existe em `en_US.lang` **e** `pt_BR.lang` (conjuntos idênticos);
- scripts: sintaxe OK (`node --check`), todos os imports relativos resolvem e
  **todo módulo é alcançável a partir de `main.js`** (nenhum módulo órfão).

## Camada 4 — vocabulário oficial do cliente

Confronta cada nome que o cliente precisa reconhecer com o vocabulário extraído
do conteúdo vanilla e da documentação oficial (`tools/bedrock_names.py`):
grupos e categorias do menu criativo, tags de menu de receita, presença de
`unlock`, nomes de `LevelSoundEvent` de bloco e de entidade, chaves do formato de
animação, chaves de `client_entity.description`, forma dos componentes de item
que só aceitam objeto. Cada regra nasceu de um erro real da Camada 0.

## Camada 5 — fidelidade da Script API

Varre os scripts por dois usos que o cliente pune e o mock antigo tolerava:
`RawMessage.with` fora das formas oficiais (`string[] | RawMessage`) e leitura de
`event.player` num handler de `playerJoin`. Comentários são removidos antes da
varredura (`strip_js_comments`), porque `core/text.js` documenta justamente as
formas **inválidas** em exemplos.

## Camada 6 — componentes de entidade (gated por versão)

`tools/check_entity_fields.py`: componentes que o cliente deixou de parsear e
campos float-range fora do formato `{"min","max"}`, ambos aplicados só a partir
do `format_version` em que a regra ficou estrita. Quando `tools/.forms/` está
vendorado, soma-se a comparação campo a campo com os forms oficiais (avisos).
Calibrado contra as 128 entidades vanilla — ver Camada 0.

**Resultado das camadas 2 a 6: 1023 verificações, 0 falhas.**

## Camada 7 — play-through headless (42 asserções)

`tools/simulate.mjs` sobe os **scripts reais do behavior pack** contra um mock
fiel da Script API (eventos, dynamic properties, inventários, `getBlocks` sobre
uma grade real de blocos, relógio controlável) e executa o ciclo completo:

| # | Cenário | Resultado |
|---|---|---|
| 1 | bootstrap + mensagem de boas-vindas | ok |
| 2 | scanner acha depósito real (distância 11, bearing leste, força), respeita cooldown e reporta "nenhum sinal" sem depósitos | ok |
| 3 | escavação registra espécime + âmbar no caderno e mostra o flourish de descoberta | ok |
| 4 | estação consome 8 fragmentos + 4 lascas + 1 espécime e identifica a espécie no registro compartilhado, concedendo XP | ok |
| 5 | reconstrução consome matriz/espécime/gel e concede exatamente 1 ovo | ok |
| 6 | incubação consome o ovo, avança com o tempo, e eclode 1 criatura com `paleo:trike_hatched` + tag `paleo:raised`, limpando a sessão e o estágio do bloco | ok |
| 7 | quebrar a incubadora devolve o ovo **uma única vez** como item no mundo | ok |
| 8 | registro/incubadoras/caderno persistem em dynamic properties e são restaurados após "reload" simulado | ok |
| 9 | duplo toque abre 1 formulário; inventário de outro jogador intocado | ok |
| 10 | caderno abre pela maleta, tela de objetivos acessível, `/scriptevent paleo:dump` responde | ok |
| 11 | guardas de fidelidade do mock: rejeita `playerJoin` com `event.player`, rejeita `with` misto, aceita a forma normalizada | ok |

Resultado: **42/42 asserções.**

## Camada 8 — verificação de API contra as type definitions oficiais

Cada API usada pelos scripts foi conferida contra `@minecraft/server@2.10.0`
(index.d.ts) e `@minecraft/server-ui@2.2.0`: `Dimension.getBlocks/BlockVolume/
ListBlockVolume.getClosest`, `world.afterEvents.*`, `system.runInterval/
runTimeout/beforeEvents.shutdown/afterEvents.scriptEventReceive`, dynamic
properties de mundo/jogador, `ActionFormData/ModalFormData/MessageFormData.show`,
`Player.onScreenDisplay/startItemCooldown/getItemCooldown/addExperience`,
`Container/ItemStack/ItemDurabilityComponent`, `Entity.triggerEvent/addTag/
hasTag`, `Block.permutation.withState/setPermutation/getLightLevel`. Nenhuma API
beta/experimental é usada; nada foi inventado.

## Reprodução

```sh
cd paleofrontier
sh tools/run_all.sh        # gera tudo, valida, simula e empacota
# ou passo a passo:
python3 tools/validate.py          # camadas 1-6 (sh tools/fetch_schemas.sh habilita 1 e 6 completa)
python3 tools/check_entity_fields.py   # camada 6 isolada
python3 tools/calibrate_entity_rules.py  # prova que as regras nao acusam o vanilla
node tools/simulate.mjs            # camada 7
python3 tools/build.py     # PALEOFRONTIER.mcaddon
```
