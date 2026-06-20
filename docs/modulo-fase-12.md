# 🎬 Fase 12 — Remuxer (MKVMerge)

[← Índice](README.md) · [Arquitetura](arquitetura.md) · [Guia de execução](guia-de-execucao.md)

**Pasta:** [`12_remuxer_mkvmerge/`](../12_remuxer_mkvmerge/)

---

## O que faz

`batch_remuxer.py` orquestra a multiplexação (remux) em lote: recebe os vídeos originais (`.mkv`) e as legendas traduzidas (`.ass`) e usa `mkvmerge` para uni-los **sem re-encodar** vídeo ou áudio. A nova legenda é definida como faixa padrão (Default Track) em português. É o passo final de **todas** as esteiras (A–N).

---

## Script

| Script | Entrada | Saída |
|:---|:---|:---|
| `batch_remuxer.py` | `*.mkv` + `traducao/*.ass` (ou `legendas_ptbr/*.ass`, conforme a esteira) | `mkv_final_ptbr/*_PTBR.mkv` |

```powershell
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
```

Pareamento por nome base — garanta que o `.ass` tenha o mesmo nome base do `.mkv` (com sufixo `_PTBR`), senão o episódio é ignorado no lote.

---

## Logs

Os logs reais ficam em **`multiplexar/logs/`** (caminho hardcoded no script, não em `12_remuxer_mkvmerge/logs/`, que é resíduo de execuções antigas): `remux_pipeline_*.txt`, `remux_config_*.txt`, `remux_erros_*.txt`, `remux_stats_*.json`. Detalhes: [Logs e auditoria — Fase 12](logs-e-auditoria.md#fase-12--remuxer-batch_remuxerpy).

---

[← Fase 11](modulo-fase-11.md) · [Índice](README.md)
