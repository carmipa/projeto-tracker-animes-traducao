# 🔬 Fase 10 — Auditoria e revisão final

[← Índice](README.md) · [Arquitetura](arquitetura.md) · [Guia de execução](guia-de-execucao.md)

**Pasta:** [`10_auditoria_e_revisao/`](../10_auditoria_e_revisao/)

---

## O que faz

Catálogo de scripts de **QA por título** — corrigem erros de lore, resíduos de tradução e alucinações residuais específicas de cada série/filme, e opcionalmente remultiplexam o `.mkv` final via `mkvmerge`. Roda depois (ou antes, dependendo do script) do remux principal da [Fase 12](modulo-fase-12.md). Cada script tem a lista de patches (regex/dicionário) **hardcoded para um título específico** — não reaproveite entre séries diferentes sem revisar.

---

## Scripts por título

| Script | Título / Esteira | Função |
|:---|:---|:---|
| `revisao_86.py` | Eighty-Six (Esteira A) | Corrige alucinações residuais (ex.: `[T0]` não restaurado), padroniza termos, remux final |
| `revisao_legenda_macross_delta.py` | Macross Delta TV (Esteira D) | Lore, traduções em inglês faltantes, tags ASS corrompidas |
| `micross_delta_filme2.py` | Macross Delta Filme 2 (Esteira E) | Lore + resíduos de francês + remux do filme |
| `revisao_legenda_gundam_unicornio.py` | Gundam Unicorn (Esteira G) | Episódio 1 + letras OP/ED (Into the Sky, RE:I AM), remux dos 22 episódios |
| `revisao_guild_crown.py` | Guilty Crown (Esteira H) | Diálogos (ex.: "Funerária" → "Sepolcro"), remove notas de tradutor (`{...}`), padroniza letras OP/ED |
| `revisao_legenda_origin.py` | Gundam The Origin (Esteira I) | Lore/tradução, atualiza `traducao_cache_origin_zh.json`, remux opcional para `corrigidos/` |

Roteiro de referência usado em apoio manual: `_dialogos_eng_brutos.txt` (gerado pela [Fase 02](modulo-fase-02.md), `extrator_texto_bruto.py`).

```powershell
python ".\10_auditoria_e_revisao\revisao_86.py"
python ".\10_auditoria_e_revisao\revisao_legenda_origin.py"
```

Cada script tem constantes `PASTA_ANIME`/`PASTA_LEGENDA` hardcoded no topo apontando para a árvore de mídia do autor — edite para o caminho real antes de rodar.

---

## Logs e troubleshooting

[Logs e auditoria — Fase 10](logs-e-auditoria.md#fase-10--auditoria-e-revisão-final) · [Solução de problemas](solucao-de-problemas.md#fase-10--revisão-final-por-título-todas-as-esteiras-com-qa)

---

[← Fase 09](modulo-fase-09.md) · [Índice](README.md) · [Fase 11 →](modulo-fase-11.md)
