# PALEOFRONTIER — relatório de testes

Ambiente de teste: sandbox Linux (Node 22, Python 3.11) com os schemas oficiais
`Mojang/bedrock-schemas` (1.26.60-beta.24), as type definitions oficiais
`@minecraft/server@2.10.0` / `@minecraft/server-ui@2.2.0` (npm) e a documentação
oficial (`MicrosoftDocs/minecraft-creator`, `Mojang/bedrock-samples` 1.26.50.4).

**Não havia instância executável do Minecraft Bedrock neste ambiente.** Tudo o que
pode ser verificado sem o cliente foi verificado e está listado abaixo; o que
exige o cliente está declarado em `docs/LIMITATIONS.md`. Nada neste relatório
afirma teste em jogo que não tenha sido executado.

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
- Nenhum arquivo vazio (201 arquivos de pacote verificados).
- Manifestos: UUIDs únicos entre BP/RP, BP depende do UUID do header do RP,
  dependências de módulo `@minecraft/server 2.10.0` e `@minecraft/server-ui 2.2.0`
  (versões estáveis correspondentes ao 1.26.52), entry `scripts/main.js` existe.

## Camada 3 — integridade de referências cruzadas (753 verificações)

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

Resultado: **753 verificações, 0 falhas.**

## Camada 4 — play-through headless (39 asserções)

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

Resultado: **39/39 asserções.**

## Camada 5 — verificação de API contra as type definitions oficiais

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
python3 tools/validate.py  # camadas 1-3 (sh tools/fetch_schemas.sh habilita a 1)
node tools/simulate.mjs    # camada 4
python3 tools/build.py     # PALEOFRONTIER.mcaddon
```
