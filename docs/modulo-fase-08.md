# ⏱️ Fase 08 — Sincronização de legendas

[← Índice](README.md) · [Arquitetura](arquitetura.md) · [Guia de execução](guia-de-execucao.md)

**Pasta:** [`08_sincronizacao_legenda/`](../08_sincronizacao_legenda/)

---

## O que faz

Audita e corrige dessincronia entre os fluxos de áudio/vídeo e a legenda (embutida ou externa), via FFprobe. **Auxiliar/opcional** — usada quando há suspeita de drift após o remux ([Fase 12](modulo-fase-12.md)) ou quando a legenda foi gerada com FPS diferente do vídeo.

---

## Scripts

| Script | Função | Saída |
|:---|:---|:---|
| `auditor_sicronia/auditor_sincronia.py` | Calcula drift entre vídeo e legenda embutida, identifica FPS mismatch e sugere correção | Console (relatório de drift) |
| `subtitle_fixer.py` | Aplica shift (deslocamento) de tempo em legenda embutida no `.mkv` | `processamento_log.txt` |
| `subtitle_stretcher.py` | Time-stretch matemático (ratio + offset) em `.srt`/`.ass`, em Python puro, sem binários externos | Console |

```powershell
python ".\08_sincronizacao_legenda\auditor_sicronia\auditor_sincronia.py"
python ".\08_sincronizacao_legenda\subtitle_fixer.py"
```

Requer FFmpeg/FFprobe no `PATH`. `subtitle_fixer.py`/`subtitle_stretcher.py` usam `tkinter` (incluso no Python padrão do Windows) para os seletores de arquivo.

---

[← Fase 07](modulo-fase-07.md) · [Índice](README.md) · [Fase 09 →](modulo-fase-09.md)
