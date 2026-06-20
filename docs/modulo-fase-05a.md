# 🤖 Fase 05a — Tradução IA (LM Studio + Gemma 4B)

[← Índice](README.md) · [Arquitetura](arquitetura.md) · [Guia de execução](guia-de-execucao.md)

**Pasta:** [`05a_tradutor_llm_gemma4/`](../05a_tradutor_llm_gemma4/)

---

## O que faz

Motor de tradução **inglês → PT-BR** via LM Studio + Gemma 4B, usado pela maioria dos títulos em inglês. Não é um script único: cada título (ou grupo de títulos) tem seu próprio script, com glossário, cache de tradução e mascaramento de tags ASS específicos. Todos validam `GET /v1/models` antes de processar e usam o modelo detectado dinamicamente.

---

## Scripts

| Script | Entrada | Saída | Título / Esteira |
|:---|:---|:---|:---|
| `86/sub_extractor.py` | `.mkv` (ASS embutido EN) | `traducao/*_PTBR.ass` | Eighty-Six (Esteira A) — extrai + traduz no mesmo passo |
| `5_tradutor_de_legenda/tradutor_srt_direto.py` | `legenda/*.srt` (EN) | `legenda/*_PTBR.srt` | Filme/SRT externo (Esteira B) |
| `tradutor_ass/batch_translator_ass.py` | `legendas_eng/*_ENG.ass` | `traducao/*_PTBR.ass` | Gundam Reconguista (Esteira F), Guilty Crown (Esteira H) |
| `tradutor_ass/batch_translator_sidonia.py` | `legendas_eng/*_ENG.ass` | `traducao/*_PTBR.ass` | Knights of Sidonia (Esteira N) |
| `tradutor_gundam_unicornio/batch_translator_unicorn.py` | `legendas_eng/*_ENG.ass` | `traducao/*_PTBR.ass` | Gundam Unicorn (Esteira G) |

Recursos comuns: cache persistente em disco (`traducao_cache_*.json`), mascaramento de tags ASS (`[T0]`, `[T1]`...) para evitar corrupção, concorrência multithread controlada (`ThreadPoolExecutor`), fallback resiliente linha a linha em caso de falha de lote, detecção automática de faixa/encoding.

`chines_para_pt_br/` é uma subpasta residual (sem scripts, apenas `__pycache__`) — herdada de uma reorganização anterior.

---

## Uso típico

```powershell
# Pré-requisito: LM Studio na porta 1234 com Gemma 4B carregado
python ".\05a_tradutor_llm_gemma4\86\sub_extractor.py"
python ".\05a_tradutor_llm_gemma4\tradutor_gundam_unicornio\batch_translator_unicorn.py"
```

---

## Logs e troubleshooting

[Logs e auditoria — Fase 05a](logs-e-auditoria.md#fase-05a--tradução-ia-lm-studiogemma) · [Solução de problemas](solucao-de-problemas.md#esteiras-adklmn--episódios-mkv-com-extração--tradução-integradas)

---

[← Fase 04](modulo-fase-04.md) · [Índice](README.md) · [Fase 05b →](modulo-fase-05b.md)
