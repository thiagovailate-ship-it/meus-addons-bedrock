# PALEOFRONTIER — instalação e ativação

## Arquivo pronto

- `paleofrontier/PALEOFRONTIER.mcaddon` — pacote duplo (Behavior + Resource).
- `paleofrontier/dist/paleofrontier_bp.mcpack` e `dist/paleofrontier_rp.mcpack` —
  pacotes individuais, caso prefira importar separadamente.

## Importar (qualquer plataforma: Windows 10/11, Android, iOS, consoles)

1. Dê dois cliques/toque em `PALEOFRONTIER.mcaddon`. O Minecraft abre e importa
   os dois pacotes automaticamente.
   - Alternativa manual: copie as pastas `behavior_pack/` e `resource_pack/`
     para `development_behavior_packs/` e `development_resource_packs/` da sua
     pasta `com.mojang` (útil para desenvolvimento com hot-reload).
2. Crie um mundo novo (Survival recomendado) ou edite um existente.
3. Em **Pacotes de comportamento**, ative *PALEOFRONTIER: Arquivo dos Gigantes [BP]*.
4. Em **Pacotes de recursos**, ative *PALEOFRONTIER: Arquivo dos Gigantes [RP]*
   (o BP já declara dependência do RP, então o jogo ativa os dois juntos).
5. **Nenhuma opção experimental é necessária.** O addon não usa Beta APIs,
   Upcoming Creator Features, Holidays Coming nem dimensões customizadas.
6. Versão alvo: **Minecraft Bedrock 1.26.52** (funciona em 1.26.50+; o manifesto
   declara `min_engine_version [1, 26, 50]`).

## Primeiro ciclo de jogo (sem comandos)

1. Explore cavernas/encostas e procure os blocos de sedimento
   (*Depósito Fossilífero*, *Matriz de Folhelho* em profundidade, *Leito Ósseo* raro).
   Eles são gerados naturalmente por feature rules do próprio pacote.
2. Craft inicial (mesa de craft vanilla):
   - **Pincel Paleontológico** = pena + lasca óssea + graveto (diagonal).
   - **Pá de Escavação** = 2 lascas ósseas + 2 lingotes de ferro + 2 gravetos.
   - **Scanner de Fósseis** = ferro/vidro/cobre/redstone + lascas e fragmentos.
   - **Maleta de Campo** = couro + papel + fragmento de sedimento.
3. Escove um depósito: espécimes íntegros **só saem com o pincel**; a pá rende
   volume; sem ferramenta delicada o Leito Ósseo vira apenas lascas.
4. Use o scanner apontando para o chão: ele consulta blocos reais num raio de
   16/20/24 blocos (cresce com a pesquisa) e informa direção, distância e força.
5. Craft da **Estação de Pesquisa** e examine um espécime → espécie identificada.
6. Processe *Matriz Genética* e *Gel Nutritivo*, reconstrua um **Ovo Vital**.
7. Craft da **Incubadora**, insira o ovo e aguarde (a câmara precisa estar em área
   carregada; luz ≥ 10 acelera 25%). O bloco mostra o estágio (0–4) e emite luz.
8. Ao eclodir, crie/alimente/estude a criatura com a Maleta de Campo.
   O caderno de campo (maleta) registra tudo e sobrevive a sair/entrar no mundo.

## Multiplayer

Todo estado compartilhado (espécies identificadas, incubadoras, estatísticas)
fica em dynamic properties do **mundo**; o caderno de campo fica em dynamic
properties do **jogador**. Interações são rate-limitadas por jogador e os
formulários têm trava anti-duplo-clique, então dois jogadores na mesma estação
não duplicam itens nem progresso.

## Diagnóstico

- Erros de script/conteúdo aparecem no Content Log com prefixo `[paleo:...]`
  (deduplicados, sem spam de chat).
- No jogo, `/scriptevent paleo:dump` imprime os últimos diagnósticos para quem
  executou (útil para suporte).
