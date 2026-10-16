# PALEOFRONTIER — limitações conhecidas

## 1. Não verificado em cliente (ambiente sem Minecraft executável)

| Item | Por que não foi testado | Mitigação aplicada |
|---|---|---|
| Renderização final de modelos/texturas/partículas | exige o cliente | geometria conferida contra o formato oficial e renderizada offline por `tools/preview_model.py`; UVs gerados por packer sem sobreposição |
| Distribuição real dos depósitos em seeds | geração ocorre no motor, em mundo novo | feature rules no formato oficial (`ore_feature` + `feature_rules`), mesmos padrões dos samples da Mojang (`custom_features/basic_orange_ore`, `casual_creator/gray_wave`) |
| UX dos formulários em touch | exige dispositivo | apenas `ActionFormData` (title/body/label/button), sem UI JSON customizada, sem comandos |
| Reprodução dos 45 `.ogg` | exige o motor de áudio | arquivos gerados com libsndfile (Vorbis), categorias do enum oficial, durações curtas |
| "Feel" da IA (prioridades/intervalos) | exige observação em jogo | comportamentos 100% nativos copiados de padrões vanilla validados (wolf/hoglin/ravager/fox/goat), com cooldowns de ataque e desistência explícitos |
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
