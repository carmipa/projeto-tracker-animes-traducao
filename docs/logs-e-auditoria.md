# 📊 Logs e auditoria

[← Índice](README.md) · [Guia de execução](guia-de-execucao.md)

---

## Fase 1 — Analisador de mídia (`media_analyzer.py`)

| Local | Arquivo |
|:---|:---|
| `1_analisador_de_midia/relatorio/` | `{arquivo}_{timestamp}.txt` — relatório técnico (codecs, faixas, sincronia) |

---

## Fase 2 — Extração de legendas

| Script | Local | Arquivo |
|:---|:---|:---|
| `extrator_inteligente_ass.py` / `_srt.py` / `_pgs.py` | `2_extrator_legenda/` | `info.txt` — auditoria das extrações (faixas detectadas, fallback usado) |
| `extrator_inteligente_pgs.py` | `2_extrator_legenda/log/` | `extracao_pgs_*.log` |

---

## Fase 4 — Tradução IA (LM Studio/Gemma)

### `sub_extractor.py` e `script_tradutor_fr.py`

Quatro artefatos por execução em `4_tradutor_ia_gemma4/logs/`:

| Arquivo | Conteúdo |
|:---|:---|
| `pipeline_*.txt` (ou `pipeline_fr_*.txt`) | Fluxo completo da execução |
| `config_*.txt` (ou `config_fr_*.txt`) | Snapshot de infraestrutura (binários, modelo, pastas) |
| `erros_*.txt` (ou `erros_fr_*.txt`) | Erros e stack traces |
| `stats_*.json` (ou `stats_fr_*.json`) | Telemetria: encodings detectados, cache, requisições |

`script_tradutor_fr.py` também persiste `traducao_cache_fr.json` (cache de traduções entre execuções).

### `tradutor_srt_direto.py`

Um arquivo por execução em `4_tradutor_ia_gemma4/5_tradutor_de_legenda/logs/`:

| Arquivo | Conteúdo |
|:---|:---|
| `pipeline_direct_srt_*.txt` | Auditoria completa: blocos, lotes, encoding, caminho de saída |

### `batch_translator_ass.py` e `batch_translator_unicorn.py`

Saída via console (`tqdm` + `colorama`); retry logic registrado inline no terminal.

---

## Fase 5 — Remuxer (`batch_remuxer.py`)

Quatro artefatos em `multiplexar/logs/`:

| Arquivo | Conteúdo |
|:---|:---|
| `remux_pipeline_*.txt` | Fluxo do remux |
| `remux_config_*.txt` | Caminhos e binário `mkvmerge` |
| `remux_erros_*.txt` | Dumps de erro |
| `remux_stats_*.json` | Bytes gerados, pareamentos, falhas |

---

## Fase 6 — Sincronização

| Script | Local | Arquivo |
|:---|:---|:---|
| `subtitle_fixer.py` | `6_sincronizacao_legenda/` | `processamento_log.txt` |
| `subtitle_stretcher.py` | — | apenas console |
| `auditor_sincronia.py` | `6_sincronizacao_legenda/auditor_sicronia/` | apenas console (relatório de drift via FFprobe) |

---

## Fase 7 — Otimização de vídeo (GPU)

| Script | Local | Arquivo |
|:---|:---|:---|
| `gpu_video_optimizer.py` | `7_decodificador/` | `optimizer_log.txt` |

---

## Fase 8 — Cura de legendas

| Script | Local | Arquivo |
|:---|:---|:---|
| `cura_gundam_mkv.py` / `cura_legendas_tag.py` | `8_cura_legendas/` | `info.txt` |

---

## Níveis no console (colorama)

| Tag | Cor | Significado |
|:---:|:---:|:---|
| `[SUCESSO]` | 🟢 Verde | Operação concluída |
| `[INFO]` / `[DEBUG]` | ⚪ / 🔵 | Fluxo normal / detalhe |
| `[AVISO]` | 🟡 Amarelo | Situação recuperável |
| `[ERRO]` | 🔴 Vermelho | Falha ou aborto |

Esses níveis aparecem em praticamente todos os scripts (Fases 1–8).

---

[← Guia de execução](guia-de-execucao.md) · [Solução de problemas →](solucao-de-problemas.md)
