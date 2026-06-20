# 🔍 Fase 01 — Analisador de mídia

[← Índice](README.md) · [Arquitetura](arquitetura.md) · [Guia de execução](guia-de-execucao.md)

**Pasta:** [`01_analisador_midia/`](../01_analisador_midia/)

---

## O que faz

`media_analyzer.py` faz auditoria técnica profunda em arquivos de vídeo (`.mkv`, `.mp4`, etc.) via `pymediainfo`: codecs, faixas de vídeo/áudio/legenda, detecção de legendas embutidas (PGS vs ASS) e indícios de dessincronia. É **opcional** — pode ser usado em qualquer esteira antes de decidir qual fluxo seguir.

---

## Script

| Script | Entrada | Saída |
|:---|:---|:---|
| `media_analyzer.py` | Pasta ou arquivo `.mkv`/`.mp4` | `relatorio/{arquivo}_{timestamp}.txt` (ou `relatorio/consolidado_{titulo}_{timestamp}.txt` para pastas com vários episódios) |

```powershell
python ".\01_analisador_midia\media_analyzer.py" "C:\TRACKER-ANIMES\animes\Macross Delta"
```

---

## Quando usar

- Antes de decidir entre as Esteiras A/D/K/L/M/N (ASS embutido), F/G/H/N (lote pré-extraído), B (SRT externo) ou C (PGS) — o relatório identifica o formato real da legenda.
- Para diagnosticar dessincronia antes de rodar a [Fase 08](modulo-fase-08.md).

---

[← Fase 00](modulo-fase-00.md) · [Índice](README.md) · [Fase 02 →](modulo-fase-02.md)
