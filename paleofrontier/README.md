# PALEOFRONTIER: Arquivo dos Gigantes

Addon completo de exploração, arqueologia e ecossistemas pré-históricos para
**Minecraft Bedrock 1.26.52** — sem toggles experimentais.

- **Artefato pronto:** [`PALEOFRONTIER.mcaddon`](PALEOFRONTIER.mcaddon)
  (Behavior + Resource). Veja [`docs/INSTALL.md`](docs/INSTALL.md).
- **Ciclo real:** prospecção → escavação com ferramentas distintas → estação de
  pesquisa → reconstrução → incubação → criação/estudo de 4 espécies.
- **Geração natural:** depósitos fossilíferos via `features`/`feature_rules`.
- **Persistência:** dynamic properties de mundo (compartilhado) e de jogador
  (caderno de campo); sobrevive a sair/entrar no mundo.
- **4 espécies** com IA nativa distinta (comportamentos de presa, herbívoro
  defensivo, predador de matilha e apex com telegraph e desistência).
- **Assets próprios:** 51 PNG e 45 OGG gerados proceduralmente, 8 geometrias,
  animações/ controllers por espécie, traduções en_US + pt_BR.

## Documentos

| Doc | Conteúdo |
|---|---|
| [`docs/INSTALL.md`](docs/INSTALL.md) | importação, ativação, primeiro ciclo |
| [`docs/DESIGN.md`](docs/DESIGN.md) | arquitetura, sistemas, persistência, multiplayer |
| [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md) | 1023 verificações + 42 asserções headless + rodada real no cliente 1.26.52 |
| [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) | o que não pôde ser testado e por quê |

## Desenvolvimento

```sh
sh tools/run_all.sh     # gera -> valida -> simula -> empacota
```

`tools/content_model.py` é a fonte única de verdade; os geradores emitem todos
os JSON/PNG/OGG/JS e `tools/validate.py` prova a consistência em 6 camadas
(schemas oficiais da Mojang, estrutura, referências cruzadas, vocabulário oficial
do cliente, fidelidade da Script API e componentes de entidade por versão),
quando vendadas com `tools/fetch_schemas.sh`.

Duas ferramentas extras existem por causa de um teste real no cliente
(Bedrock 1.26.52, iOS) — ver [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md),
Camada 0:

- `tools/check_entity_fields.py` — componentes de entidade conferidos contra os
  update notes oficiais e os forms do `minecraft-creator`, **gated por
  `format_version`** (é assim que o cliente se comporta).
- `tools/calibrate_entity_rules.py` — aplica essas regras às 128 entidades do
  `bedrock-samples`: uma regra que acusa o conteúdo da Mojang é regra errada.
