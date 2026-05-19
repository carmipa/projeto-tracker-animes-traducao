# 📊 Logs e auditoria

[← Índice](README.md)

---

## Fase 1 — Tradutor MKV (`sub_extractor.py`)

Quatro artefatos por execução em `2_tradutor_ia_gemma4/logs/`:

| Arquivo | Conteúdo |
|:---|:---|
| `pipeline_*.txt` | Fluxo completo |
| `config_*.txt` | Snapshot de infraestrutura |
| `erros_*.txt` | Erros e stack traces |
| `stats_*.json` | Telemetria (encodings, cache, requisições) |

---

## Fase 5 — Tradutor SRT (`tradutor_srt_direto.py`)

Um arquivo por execução em `5_tradutor_de_legenda/logs/`:

| Arquivo | Conteúdo |
|:---|:---|
| `pipeline_direct_srt_*.txt` | Auditoria completa: blocos, lotes, encoding, caminho de saída |

Níveis: `SUCESSO`, `ERRO`, `AVISO`, `DEBUG`, `INFO`.

---

## Fase 2 — Remuxer (`batch_remuxer.py`)

Quatro artefatos em `multiplexar/logs/`:

| Arquivo | Conteúdo |
|:---|:---|
| `remux_pipeline_*.txt` | Fluxo do remux |
| `remux_config_*.txt` | Caminhos e binário mkvmerge |
| `remux_erros_*.txt` | Dumps de erro |
| `remux_stats_*.json` | Bytes gerados, pareamentos, falhas |

---

## Fases 0 e 6

| Fase | Log |
|:---|:---|
| 0 | Relatórios em `relatorio/*.txt` (não usa pasta `logs/`) |
| 6 | Saída apenas no console (`tqdm` + `colorama`) |

---

## Níveis no console (colorama)

| Tag | Cor | Significado |
|:---:|:---:|:---|
| `[SUCESSO]` | 🟢 Verde | Operação concluída |
| `[INFO]` / `[DEBUG]` | ⚪ / 🔵 | Fluxo normal / detalhe |
| `[AVISO]` | 🟡 Amarelo | Situação recuperável |
| `[ERRO]` | 🔴 Vermelho | Falha ou aborto |

---

[← Guia de execução](guia-de-execucao.md) · [Solução de problemas →](solucao-de-problemas.md)
