# 📊 Logs e auditoria

[← Índice](README.md)

Cada execução das Fases 1 e 2 gera **quatro artefatos** com timestamp `YYYY-MM-DD_HH-MM-SS`:

| Arquivo | Conteúdo |
|:---|:---|
| `pipeline_*.txt` / `remux_pipeline_*.txt` | Fluxo completo |
| `config_*.txt` / `remux_config_*.txt` | Snapshot de infraestrutura |
| `erros_*.txt` / `remux_erros_*.txt` | Erros e stack traces |
| `stats_*.json` / `remux_stats_*.json` | Telemetria (contagens, bytes, encodings) |

---

## Pastas de log

| Módulo | Pasta |
|:---|:---|
| Fase 1 | `2_tradutor_ia_gemma4/logs/` |
| Fase 2 | `multiplexar/logs/` (definido em `batch_remuxer.py`) |

---

## Níveis no console (colorama)

| Tag | Cor | Significado |
|:---:|:---:|:---|
| `[SUCESSO]` | 🟢 Verde | Operação concluída |
| `[INFO]` / `[DEBUG]` | ⚪ / 🔵 | Fluxo normal / detalhe |
| `[AVISO]` | 🟡 Amarelo | Situação recuperável |
| `[ERRO]` / `[CRÍTICO]` | 🔴 Vermelho | Falha ou aborto |

---

[← Guia de execução](guia-de-execucao.md) · [Solução de problemas →](solucao-de-problemas.md)
