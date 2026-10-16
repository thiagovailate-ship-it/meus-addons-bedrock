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

Esta camada tem **três logs reais**, coletados em três instalações do add-on no
mesmo dispositivo (Bedrock 1.26.52, iOS):

| rodada | versão testada | classes de erro novas | classes anteriores |
|---|---|---|---|
| 1º log | v1.0.0 | 9 | — |
| 2º log | v1.0.1 | 5 (mascaradas atrás das 9) | **todas desapareceram** |
| 3º log | v1.0.2 | 2 | **todas desapareceram** |

Nenhuma delas era detectável pelas camadas 1–4 da forma como estavam: os schemas
oficiais da Mojang são lenientes nesses pontos, os forms do `minecraft-creator`
estão desatualizados em relação ao parser, e o mock do harness era menos fiel que
o cliente. Todas foram corrigidas na fonte (`tools/content_model.py`,
`tools/gen_bp.py`, `tools/bedrock_names.py`, `tools/vendor_forms.py` e nos scripts
do pacote, não nos arquivos gerados) e cada uma virou uma checagem permanente.

O padrão das três rodadas é o mesmo: cada log confirma as correções anteriores e
revela uma camada que estava **escondida atrás** delas — porque o cliente aborta
no primeiro erro de parse por entidade, e porque um mock infiel faz asserções
antigas passarem de forma vazia.

### Primeiro log (v1.0.0 → v1.0.1)

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

### Segundo log real (v1.0.1 → v1.0.2)

O mesmo cliente, após importar a v1.0.1. Os 9 erros anteriores **desapareceram**
— o que confirma aquelas correções. Restaram 5 classes novas, todas escondidas
atrás das antigas:

| # | Erro no log do cliente | Causa raiz | Correção | Regra permanente criada |
|---|---|---|---|---|
| 10 | `minecraft:breathability: member is deprecated` (3 blocos) + `Unknown block during Deferred BlockDescriptor resolution` | componente deprecated; **o bloco deixava de ser registrado** e sumia do mundo. Nenhum bloco vanilla o usa, e a documentação (`Blocks.html`) diz que o default já é `"solid"` | removido do gerador — **zero mudança de comportamento**, porque o valor declarado era exatamente o default | camada 4: componentes de bloco deprecated |
| 11 | `hurt_by_target.alert_same_type: not present in the Schema` (2 entidades) | campo removido do schema. **Os forms oficiais ainda o listam como boolean** — estão desatualizados em relação ao parser | removido. Era **redundante**: o alerta de matilha já estava implementado em `minecraft:angry.broadcast_anger_on_being_attacked` + `broadcast_targets` (padrão `piglin.json` fv 1.26.20). No triceratops, `broadcast_targets` foi declarado explicitamente | camada 6: campos rejeitados pelo cliente (log real vence documentação) |
| 12 | `avoid_mob_type.sound_interval.range_min/range_max: not present in the Schema` (2 entidades) | a forma de `sound_interval` **varia por componente** | `{min,max}` só em `avoid_mob_type`. `panic` e `angry` **mantiveram** `{range_min,range_max}` — o vanilla prova (hoglin/piglin vs. 4 usos em `angry`) e o cliente ficou em silêncio sobre eles | camada 6: membros de objetos aninhados, por componente |
| 13 | `nearest_attackable_target.entity_types[1].must_see_forget_duration: invalid numeric value` (2 entidades) | o campo só é válido **no nível do componente**; o censo vanilla tem 8 usos lá e **0** dentro de `entity_types` | removido das entradas; passa a valer o valor do componente (rex 9.0, raptor 6.0) | camada 6: membros válidos dentro de `entity_types[]`, por componente |
| 14 | `[paleo:error] journal_ui.open: cannot read property 'rex' of undefined` | a fábrica do journal declarava `found/studied/hatched/raised`, mas o código lia **`.bonded`** — e `raised` nunca foi usado por ninguém. `bumpJournal` se autocorrigia ao *escrever*, então o bug só aparecia em quem **nunca** tinha criado um vínculo: exatamente quem abre o diário pela primeira vez | `JOURNAL_BUCKETS` como fonte única; leitores e escritores passam por `journalBucket()`, que autocorrige; `normalizeJournal()` re-afirma os buckets ao carregar um save antigo | seção `[12]` do play-through: jogador **novo** visita todas as telas do diário |

### O detalhe que mudou a forma de investigar: o cliente aborta no primeiro erro

O log reporta **um** erro por entidade e para. As 4 entidades falhavam, então
tudo que estivesse depois do primeiro erro em cada arquivo ficou invisível. Isso
teve duas consequências práticas:

- **Corrigir só o que o log mostrou teria sido insuficiente.** `alert_same_type`
  apareceu em 1 entidade no log, mas existia em 2; `sound_interval` errado
  apareceu em 2, mas o censo interno achou todas as ocorrências por componente.
  A varredura foi feita sobre o pacote inteiro, não sobre o log.
- **Silêncio do cliente sobre um arquivo que já falhou não é evidência de
  validade.** Para os blocos valeu o raciocínio inverso e ele foi produtivo: a
  ordem dos componentes no JSON prova que `map_color` (índice 6),
  `material_instances` (5), `geometry` (4), `selection_box` (1),
  `light_dampening` (7) e `friction` (8) foram parseados **antes** de
  `breathability` (9) — logo estão confirmados como aceitos, e a decisão anterior
  de não convertê-los deixou de ser inferência. `sound`/`tags`/`loot` vinham
  depois (mascarados), mas `incubator` e `research_bench` não tinham
  `breathability` e usam as mesmas formas sem nenhum erro: ficam cobertos por
  eles.

### Um bug latente achado por varredura, não pelo log

Cruzando cada par `(componente, campo)` do pacote com as 128 entidades vanilla,
sobrou um par sem referência: `damage_sensor.deals_damage` escrito como
`{"value": false}`. O vanilla usa **string** em 70 ocorrências (`no`=30,
`no_but_entity_effects_apply`=19, `yes`=17, `no_but_side_effects_apply`=4) e o
`Update1.21.40.md` oficial é explícito: *"the `deals_damage` field has been
changed from a Boolean to supporting three values"*. Corrigido para `"no"`.
O cliente nunca reportaria isso: o compsognathus já abortava antes.

### Terceiro log real (v1.0.2 → v1.0.3)

O mesmo cliente, após importar a v1.0.2 em mundo novo. As 5 classes da rodada
anterior **desapareceram**: nenhuma reclamação de `breathability`,
`alert_same_type`, `sound_interval`, `must_see_forget_duration` ou
`deals_damage`, e nenhum `Unknown block`. Restaram 2 classes:

| # | Erro no log do cliente | Causa raiz | Correção | Regra permanente criada |
|---|---|---|---|---|
| 15 | `minecraft:leashable \| hard_distance \| child 'hard_distance' not valid here` (idem `soft_distance`/`max_distance`; 7 sítios nas 4 entidades = 21 linhas) | desde **fv 1.21.80** as distâncias do leashable **migraram para dentro de `presets[]`**. O próprio form oficial documenta isso no `note2`: *"Each preset has its own `filter`, `hard_distance`, `soft_distance`, and `max_distance` — replacing the flat root fields previously used"* | `{soft,hard,max}_distance` → `presets: [{soft,hard,max}_distance]`, com os 7 conjuntos de valores preservados um a um. Modelo vanilla na **mesma** format_version: `dolphin.json` fv 1.26.50 | camada 6: `RELOCATED_TO_PRESETS` (gated por fv) + vocabulário de membros de `presets[]` derivado do vanilla + `presets` precisa ser lista |
| 16 | `journal_ui.open: Failed to resolve raw message from json` com `{"translate":"paleo.ui.obj.gear","with":{"text":""}}` | `args([])` devolvia `{ text: "" }`. Um `with` **presente porém vazio** não é resolvível. Como 6 dos 7 passos de objetivo não têm `args`, a tela de objetivos quebrava para quase todo mundo | `args([])` → `undefined`; novo `translateWith(chave, valores)`, que **omite** a chave quando não há argumentos | camada 5: `args()` só aceita array literal não-vazio (argumento dinâmico tem que ir por `translateWith`); mock rejeita `with` vazio com a mesma mensagem do cliente |

### A causa-raiz de ferramenta por trás do erro 15

Este é o achado mais importante da rodada, porque explica **por que o validador
deixou passar** um campo que a própria documentação oficial dizia ter migrado.

Cada `.form.json` do `minecraft-creator` traz a lista de campos em até três
lugares: `fields` (escrita à mão), `generatedFromSchema_doNotEdit` e
`generated_doNotEdit` (geradas do schema atual). `tools/vendor_forms.py` fundia as
três **sem distinguir a origem**, com a intenção declarada de "evitar falso
positivo de campo que não existe". O efeito foi o oposto: um falso **negativo**.

Para `minecraft:leashable`:

| campo | `fields` (manual) | `generated_doNotEdit` | cliente 1.26.52 |
|---|---|---|---|
| `soft_distance` / `hard_distance` / `max_distance` | presente | **ausente** | **rejeita** |
| `presets` | ausente | presente | aceita |

A lista manual envelhece; a gerada não. A correção foi registrar a
**proveniência** de cada campo (`manual` / `generated` / `both`) e capturar também
o `note2` — que era justamente onde a migração estava documentada e que o extrator
descartava.

Um detalhe de calibração: "campo só na lista manual" **não** pode virar FAIL
sozinho. Aplicado cruamente produz 34 avisos no próprio pacote, todos em campos
universais (`health.value`, `movement.value`, `follow_range.max`) que a lista
gerada apenas representa de outro jeito — ruído que esconde o único sinal
verdadeiro. O filtro que separa os casos é **o form documentar migração/remoção**:
dos 400 componentes, 30 têm essa nota e só **4** têm nota *e* campos manuais
(`ageable`, `breedable`, `leashable`, `tameable`). Com o filtro: 0 avisos no
pacote, e o `leashable` teria sido sinalizado.

Os forms continuam sem ser prova em nenhuma direção — `alert_same_type` consta no
`generated_doNotEdit` e o cliente o rejeita. Daí a hierarquia permanecer
**log real > censo vanilla > forms**.

### Um teste antigo que passava de forma vazia

Ao ensinar o mock a rejeitar `with` vazio, a asserção **já existente** `"objectives
screen reachable"` (seção `[10]`) passou a falhar com o código antigo. Ou seja: a
tela de objetivos estava quebrada no jogo e o harness a dava como OK, porque o
mock aceitava a mensagem inválida. Restaurando `text.js`/`journal_ui.js` do commit
anterior o harness reprova; com a correção, passa. É o mesmo padrão da seção
`[11]`: guarda de fidelidade vale mais que asserção de funcionalidade.

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
| **checker real inteiro** (`check_entity_fields.check_doc` aplicado ao vanilla, inclui todas as regras de profundidade) | FAIL | **limpa** (0 violações) |
| componente removido (`pushable`) | FAIL | **limpa** (0 violações) |
| campo float-range fora de `{min,max}` | FAIL | **limpa** (0 violações) |
| campo ausente do form oficial | aviso | 35 divergências → os forms são incompletos |
| tipo divergente do form | aviso | 41 divergências → os forms são lenientes |

A primeira linha é a calibração mais forte disponível: em vez de reimplementar as
regras, ela roda **o checker de produção** sobre o vanilla. É o que garante que as
regras de profundidade criadas a partir do segundo log (membros de
`entity_types[]`, membros de objetos aninhados, enums folha) não acusam o
conteúdo da Mojang.

Duas ressalvas honestas sobre a tabela de avisos: os forms oficiais provaram estar
**desatualizados** em relação ao parser (listavam `alert_same_type`, que o cliente
rejeita), então a hierarquia de evidência adotada é **log real do cliente > censo
vanilla > forms/documentação**. E o censo vanilla é um subconjunto estreito — os
98 blocos dos samples, por exemplo, não usam `friction`/`light_emission`/`sound`,
o que não significa que sejam inválidos.

### Teste de mutação: as regras têm dentes

Cada regra nova foi validada reinjetando o defeito correspondente numa cópia do
pacote e confirmando que o pipeline reprova. Acumulado das três rodadas: **10
classes de mutação, 10 detectadas**.

| Mutação | Detectada por |
|---|---|
| `avoid_mob_type.sound_interval` de volta a `{range_min,range_max}` | camada 6 |
| `angry.sound_interval` trocado para `{min,max}` | camada 6 — **prova a precisão por componente**: a regra não é um rename global, ela sabe que `angry` e `avoid_mob_type` exigem formas diferentes |
| `hurt_by_target.alert_same_type` reinserido | camada 6 |
| `entity_types[1].must_see_forget_duration` reinserido | camada 6 |
| `damage_sensor.deals_damage` de volta a `{"value": false}` | camada 6 |
| `minecraft:breathability` reinserido num bloco | camada 4 |
| `leashable` com as distâncias achatadas no nível de cima (o erro exato do 3º log) | camada 6 |
| membro inventado (`leash_strength`) dentro de `leashable.presets[]` | camada 6 |
| `leashable.presets` como objeto em vez de lista | camada 6 — **achada pelo teste**: a primeira versão da regra só iterava quando era lista, e portanto não pegava esta |
| `args(step.args \|\| [])` (argumento não-literal, possivelmente vazio) | camada 5 |

Dois bugs de script foram validados do mesmo modo, no harness, restaurando os
arquivos do commit anterior:

- `store.js`/`journal.js` sem o bucket `bonded` → a seção `[12]` **falha 3
  asserções** e captura exatamente a classe de erro do cliente;
- `text.js`/`journal_ui.js` com `args([])` → `{text:""}` → a asserção **já
  existente** `"objectives screen reachable"` falha.

Com as correções, tudo passa.

### Reprodutibilidade do artefato

Dois defeitos faziam o `.mcaddon` mudar de bytes sem nenhuma mudança de conteúdo,
o que tornava o SHA-256 publicado inverificável:

- `tools/gen_sounds.py` semeava o RNG com `abs(hash(nome))`. O Python randomiza
  `hash()` de strings por processo (`PYTHONHASHSEED`), então os **45 OGGs** mudavam
  a cada execução. Trocado por `zlib.crc32(nome)`, que depende só do nome.
- O libsndfile sorteia um *bitstream serial number* por arquivo Ogg.
  `normalize_ogg_serial()` o fixa deterministicamente e recalcula os CRCs de
  página (implementação do CRC-32 Ogg validada reproduzindo byte a byte os CRCs
  que o próprio libsndfile gravou). Há auto-verificação: o áudio decodificado é
  comparado antes e depois, e a geração aborta se diferir.
- `tools/build.py` gravava o mtime de cada entrada no zip. Passou a usar data fixa
  e percurso ordenado.

Resultado: três execuções completas do pipeline produzem o **mesmo** SHA-256, e o
hash não muda quando os mtimes dos arquivos são alterados.

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

**Resultado das camadas 2 a 6: 1067 verificações, 0 falhas.**

## Camada 7 — play-through headless (47 asserções)

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
| 11 | guardas de fidelidade do mock (5): rejeita `playerJoin` com `event.player`, rejeita `with` misto, **rejeita `with` vazio**, aceita `translate` sem `with`, aceita a forma normalizada | ok |
| 12 | **jogador novo** abre todas as telas do caderno (criaturas + os 4 dossiers) sem erro de script — regressão do segundo log real | ok |

Resultado: **47/47 asserções.**

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
