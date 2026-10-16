# PALEOFRONTIER — limitações conhecidas

## 1. Verificação em cliente

### O que já se sabe do cliente real

**Duas rodadas reais** aconteceram (Bedrock 1.26.52, iOS) e ambas produziram log.
A primeira (sobre a v1.0.0) apontou 9 classes de erro; a segunda (sobre a v1.0.1)
apontou 5 classes novas que estavam mascaradas atrás das primeiras. Todas foram
corrigidas e cada uma virou uma checagem permanente — o detalhe está em
`docs/TEST_REPORT.md`, Camada 0.

O segundo log **confirmou as correções do primeiro**, porque o cliente continuou
parseando os mesmos arquivos e parou de reclamar deles:

- os 9 erros da primeira rodada **desapareceram** por completo: nenhum erro de
  `menu_category`, `fire_resistant`, receita, `LevelSoundEvent`, animação, client
  entity ou `pushable`;
- os blocos continuaram sendo validados (o log cita `breathability` nos 3
  blocos), então o silêncio sobre `menu_category`/`map_color`/`geometry` é
  evidência positiva, não ausência de parse;
- as entidades continuaram sendo validadas (o log cita outros campos delas), então
  o silêncio sobre `pushable` confirma aquela correção;
- os dois pacotes seguem importados e ativados no mundo
  (`behavior_packs/Paleo-BP`, `resource_packs/Paleo-RP`);
- os scripts carregam e executam, e o sistema de diagnóstico `[paleo:error]`
  continua funcionando como projetado: capturou, rotulou e reportou a falha do
  journal em vez de travar o mundo.

A ordem dos componentes dentro do JSON dos blocos permitiu uma conclusão extra:
`map_color`, `material_instances`, `geometry`, `selection_box`, `light_dampening`
e `friction` vêm **antes** de `breathability`, logo foram parseados e aceitos — a
decisão de mantê-los nas formas escalar/objeto/`{color}` deixou de ser inferência
e passou a ser fato observado.

### O que ainda NÃO foi re-verificado no cliente

**As 6 correções da v1.0.2 ainda não foram re-testadas em cliente** (as 5 do
segundo log + `damage_sensor.deals_damage`, achada por varredura). O que existe é:
evidência dos dois logs, confronto com o conteúdo vanilla 1.26.50.4, com a
documentação oficial e com as type definitions — mais as checagens permanentes,
calibradas para não acusar o conteúdo da Mojang e validadas por teste de mutação.
Um terceiro log é o que fecha o ciclo.

Risco residual honesto: 13 pares `(componente, campo)` usados pelas entidades não
têm correspondência no vanilla dos samples (`melee_attack.track_target`,
`navigation.walk.can_jump`, `sound_volume.value`, …). Todos constam nos forms
oficiais com tipo compatível, e `sound_volume` é confirmado por **duas** fontes
independentes (form `value: float` + JSON schema `value: number`). Mas os forms
já provaram estar desatualizados uma vez (`alert_same_type`), então isso é
confiança moderada, não prova. Não foram alterados: sem evidência de falha, mexer
neles seria trocar um risco conhecido por um desconhecido.

| Item | Por que não foi testado | Mitigação aplicada |
|---|---|---|
| Ausência de erros no log após as correções da v1.0.2 | exige nova rodada no cliente | 1032 verificações + 45 asserções; regras calibradas contra as 128 entidades vanilla (0 falso positivo) e validadas por 6 mutações reinjetadas |
| Renderização final de modelos/texturas/partículas | exige o cliente | geometria conferida contra o formato oficial e renderizada offline por `tools/preview_model.py`; UVs gerados por packer sem sobreposição |
| Distribuição real dos depósitos em seeds | geração ocorre no motor, em mundo novo | feature rules no formato oficial (`ore_feature` + `feature_rules`), mesmos padrões dos samples da Mojang (`custom_features/basic_orange_ore`, `casual_creator/gray_wave`) |
| Blocos aparecendo no mundo após o fim do erro `Unknown block` | exige mundo novo no cliente | `breathability` removido (era o que impedia o registro); o default oficial já é `"solid"`, então a remoção não altera comportamento |
| Receitas aparecendo na bancada | **confirmado indiretamente**: o segundo log não reportou erro de receita | tags oficiais (`crafting_table`) + `unlock`; checagem permanente contra as 11 tags oficiais |
| UX dos formulários em touch | exige dispositivo | apenas `ActionFormData` (title/body/label/button), sem UI JSON customizada, sem comandos; `RawMessage` normalizado por `core/text.js` |
| Reprodução dos 45 `.ogg` | exige o motor de áudio | arquivos gerados com libsndfile (Vorbis), categorias do enum oficial, durações curtas; eventos de som conferidos contra os 44 de bloco e 166 de entidade do `sounds.json` vanilla; todos os 45 decodificados e conferidos após a normalização do container |
| "Feel" da IA (prioridades/intervalos) | exige observação em jogo | comportamentos 100% nativos copiados de padrões vanilla validados (wolf/hoglin/ravager/fox/goat/piglin), com cooldowns de ataque e desistência explícitos; alerta de matilha/manada via `angry.broadcast_*` (padrão piglin) |
| Desempenho em mobile real | exige device | zero trabalho por tick (2 intervalos: 200t e 40t); scanner com 1 consulta e cooldown; partículas limitadas |
| Servidor dedicado/realm com muitos jogadores | exige infraestrutura | lógica host-autoritativa; o simulador cobre 2 jogadores e dupla interação |


## 2. Decisões de design com impacto percebido

- **Incubação exige chunk carregado.** O progresso acumula apenas enquanto a
  câmara está em área carregada (e credita no máx. 5 s por pulso, para não
  "teleportar" progresso após longas ausências). Luz ≥ 10 acelera 25%. A UI
  explica ambos.
- **Tiranossauro impronta só enquanto juvenil.** Adulto selvagem é um encontro
  de alto risco; adulto imprintado não ataca o dono (grupo de componentes
  separado, padrão wolf).
- **Compsognato tem spawn egg no criativo** (`is_spawnable: true`) porque é a
  espécie que ainda sobrevive no mundo (spawn natural em grupos de 2–4).
  Tricerátopo, Velociraptor e Tiranossauro **não** têm spawn egg: só existem via
  reconstrução + incubação.
- **Sem reprodução/genética.** Deliberado: o ciclo é exploração → pesquisa →
  reconstrução → cuidado. Criaturas continuam relevantes por estudo, vínculo,
  defesa e loot de materiais.
- **Scanner**: uma consulta de volume por uso (raio 16/20/24 conforme pesquisa),
  cooldown nativo de 8 s e 1 de durabilidade. Aponte para o bloco/uso do item.
- **Estágio da incubadora**: state inteiro 0–4 (o formato permite até 16), com
  textura da câmara e emissão de luz por estágio.
- **Categorias de som**: usam apenas valores do enum oficial
  (`player`, `block`, `neutral`, `hostile`) — não `master`, que o schema oficial
  1.26.60-beta não lista.
- **pt_BR**: acentuação aplicada por tabela curada (`cm.pt_br`). Novas strings
  devem nascer ASCII no modelo e passar por `pt_br` na geração.

## 3. Divergências do schema oficial (não são defeitos do pacote)

- `bp/blocks`, `bp/entities`, `rp/particles`: `$ref` pendente no repo da Mojang
  (`../../common/expression.schema.json` inexistente) → famílias puladas com
  aviso e cobertas pelas demais camadas de validação.
- `bp/recipes`: só existe schema de brewing mix no repo oficial → receitas
  validadas estruturalmente (padrão 3×3, chaves usadas/definidas, ids existentes).
- `rp/texts/languages.json`: schema oficial modela array como objeto → validado
  estruturalmente.
- Geometria (`pivot/origin/size/uv` numéricos) e `version` de manifesto RP
  (array): schema oficial tipa como string; todo conteúdo vanilla usa
  números/arrays → normalização apenas na cópia validada, documentada no código.

## 4. Riscos residuais assumidos

- `match_tool` com **tags custom** (`paleo:is_brush`) depende do suporte
  documentado a item tags em loot desde 1.21.70 (anterior ao alvo 1.26.52).
- `minecraft:home` + `move_towards_home_restriction` do T-Rex assume que o ponto
  de casa é fixado no spawn (comportamento vanilla de mobs com restrição).
- A textura de destruição de blocos usa a instância `down`/`*` (padrão do motor).
- O mock headless não reproduz o motor de loot: o registro de descobertas é
  testado via diff de inventário (exatamente como o script age em jogo).
