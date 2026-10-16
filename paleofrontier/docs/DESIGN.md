# PALEOFRONTIER — arquitetura e decisões de design

Alvo: **Minecraft Bedrock 1.26.52** · Script API estável `@minecraft/server 2.10.0`
e `@minecraft/server-ui 2.2.0` · namespace `paleo:` · **zero toggles experimentais**.

## 1. Layout

```
paleofrontier/
├── PALEOFRONTIER.mcaddon          <- artefato final (BP+RP)
├── behavior_pack/                 <- dados + scripts
│   ├── blocks/  items/  entities/  spawn_rules/
│   ├── features/  feature_rules/    <- geração natural dos depósitos
│   ├── loot_tables/  recipes/  texts/
│   └── scripts/
│       ├── main.js                <- entrada: eventos + tarefas periódicas
│       ├── data/content.js        <- REGISTRO GERADO (fonte única de ids/custos)
│       ├── core/    log · store · inventory · scheduler
│       ├── systems/ scanner · excavation · lab · journal · incubator · creatures
│       └── ui/      forms · lab_ui · journal_ui · incubator_ui
├── resource_pack/                 <- texturas, modelos, animações, sons, langs
├── tools/                         <- geradores + validação + simulador + build
└── docs/                          <- INSTALL · DESIGN · TEST_REPORT · LIMITATIONS
```

`tools/content_model.py` é a **fonte única de verdade**: blocos, itens, espécies,
custos de pesquisa, loot, receitas, sons e traduções nascem dele. Os geradores
emitem JSON/PNG/OGG/JS a partir dele e `tools/validate.py` re-lê tudo para provar
que nada divergiu (741 verificações de referência cruzada).

## 2. Ciclo de jogo e como cada etapa é real

| Etapa | Mecanismo | Por que é real |
|---|---|---|
| Prospecção | `features` + `feature_rules` (ore_feature, underground/surface pass) | geração natural do motor, sem estruturas manuais |
| Detecção | `Dimension.getBlocks(volume, {includeTypes, closest})` | consulta blocos **existentes**; sem sinal => "nenhum sinal" |
| Escavação | loot tables com `match_tool` (`match_tool_filter_all/none`) | pincel libera espécimes/âmbar; pá rende volume; sem pincel o Leito Ósseo degrada |
| Identificação | UI (`ActionFormData`) → `systems/lab.js` | consome espécime+insumos do inventário do ator, grava registro compartilhado |
| Processamento | receitas de laboratório em script | transações atômicas consume→grant |
| Reconstrução | laboratório → item `paleo:egg_*` | ovo só existe após identificação + custos |
| Incubação | registro em dynamic property do mundo + tick de 40t | estado persistente, estágio visível no bloco (state 0–4 + light emission) |
| Criação | `spawnEntity` + eventos `paleo:<sp>_hatched/_raised` | bebê real com ageable/healable/tameable nativos |
| Estudo | Maleta de Campo + `triggerEvent('paleo:<sp>_studied')` | marca o indivíduo (mark_variant) e o caderno |

## 3. Ferramentas com funções distintas e verificáveis

- **Pincel Paleontológico** — única rota para espécimes íntegros e âmbar
  (`match_tool_filter_all: ["paleo:is_brush"]` no loot).
- **Pá de Escavação** — `minecraft:digger` rápido nos depósitos + pool de volume
  no loot (`paleo:is_excavator`); não obtém espécimes.
- **Scanner** — `getBlocks` num volume limitado (16/20/24 por progresso), cooldown
  nativo `minecraft:cooldown` + `startItemCooldown`, dano de durabilidade.
- **Maleta de Campo** — abre o caderno (UI) e estuda criaturas
  (`playerInteractWithEntity`).

Nenhum drop é inventado por script: o loot é data-driven, então multiplayer,
explosões e quebras fora do script continuam coerentes. O script apenas observa
o inventário (diff pós-quebra) para **registrar** o que foi recuperado.

## 4. Persistência

- Mundo: `paleo.world.registry` (espécies identificadas + estatísticas) e
  `paleo.world.incubators` (sessões: espécie, progresso acumulado, último tick).
- Jogador: `paleo.player.journal` (encontrados, estudados, eclodidos, vínculos).
- Escrita **batched**: mutações marcam dirty; flush a cada 200 ticks, em
  `playerLeave` e em `system.beforeEvents.shutdown`. Nada é reescrito por tick.
- Limite de 28 KB por propriedade com poda defensiva (nunca estoura os 32 KB).
- Recarga simulada no harness: apaga o estado em memória e relê da propriedade.

## 5. Multiplayer e integridade

- Host autoritativo: scripts rodam no servidor; UI apenas pede.
- Rate limit de 8 ticks por jogador para interações + trava de formulário por
  jogador (`ui/forms.js`) → duplo toque/dupla mão abrem **um** fluxo.
- Transações verificam e consomem do inventário **do ator** antes de conceder.
- Incubadora quebrada devolve o ovo **uma vez** como item no mundo (a sessão é
  removida do registro antes), sem duplicar.
- Registro de incubadoras faz GC de entradas cujo bloco sumiu (chunk recarregado
  sem bloco => entrada descartada).

## 6. Ecossistema (componentes nativos, sem IA por tick de script)

| Espécie | Comportamentos-chave (nativos) |
|---|---|
| Compsognato | `tempt`, `panic`, `avoid_mob_type(predadores)`, `follow_parent`, herds de 2–4 via spawn rules, `tameable` |
| Tricerátopo | `eat_block` (pasto/feno), `avoid_mob_type(predadores)`, `angry`+`melee_attack`+`knockback_roar` quando ferido (`on_hurt`), `tameable` |
| Velociraptor | `stalk_and_pounce_on_target`, `leap_at_target`, `angry` com `broadcast_anger` (matilha), `on_target_escape`→`attack_cooldown` (desiste) |
| Tiranossauro | `home`+`move_towards_home_restriction` (patrulha), `knockback_roar` como telegraph, `delayed_attack` (alcance/intervalo claros), `on_target_escape`→`attack_cooldown` (sem perseguição infinita), imprinting juvenil via `tameable` |

Script só **registra** (spawn/death/tame/study) — nunca recalcula IA por tick.

## 7. Desempenho mobile

- Tarefas periódicas: 2 (flush 200t, incubadora 40t). Nada roda por tick.
- Scanner: 1 consulta nativa por uso (volume ≤ 49³, com cooldown de 8 s).
- Sem loops de inventário por frame; diffs só após quebra de depósito.
- Partículas: rajadas curtas e contínuas apenas na incubadora (emitter looping
  de 12/s com teto de 40), nunca efeitos de tela cheia.
- Texturas: 16×16 blocos/itens; entidades 64×32 … 256×256 (apex apenas).
- Sons: 45 OGG gerados (256 KiB), categorias válidas, sem loops longos.

## 8. Identidade visual/sonora

- Paleta mineral/terrosa; fósseis com silhueta legível; equipamentos distintos.
- 4 geometrias de dinossauros propias (bípedes/quadrúpede, crânios e caudas
  diferentes) + variantes de pele por estado (selvagem / vinculado / alerta /
  marcado-pelo-campo) — não é uma textura recolorida entre espécies.
- Animações próprias por espécie (walk/idle/look/eat/rest/roar/attack) geradas
  com pivôs corretos; controladores calm/aggressive/sleeping.
- `tools/preview_model.py` renderiza os modelos offline para inspeção visual.
