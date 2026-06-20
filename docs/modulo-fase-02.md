# ✂️ Fase 02 — Extração de legendas

[← Índice](README.md) · [Arquitetura](arquitetura.md) · [Guia de execução](guia-de-execucao.md)

**Pasta:** [`02_extrator_legenda/`](../02_extrator_legenda/)

---

## O que faz

Extrai a legenda original do `.mkv` para um arquivo independente, antes da tradução. Usada pelas esteiras cujo motor de tradução **não** extrai por conta própria (F, G, H, N) — as esteiras A/D/J/K/L/M usam scripts de Fase 05a/05b/05c-2 que já extraem e traduzem no mesmo passo.

---

## Scripts

| Script | Entrada | Saída | Esteiras |
|:---|:---|:---|:---|
| `extrator_inteligente_ass.py` | `.mkv` com faixa `S_TEXT/ASS` | `legendas_eng/*_ENG.ass` (ou `*.chs.ass` para Gundam The Origin) | F, G, H, I, N |
| `extrator_inteligente_srt.py` | `.mkv` com faixa `S_TEXT/UTF8` (SRT) | `legendas_eng/*_ENG.srt` | uso pontual |
| `extrator_inteligente_pgs.py` | `.mkv` com faixa `S_HDMV/PGS` (bitmap) | `extraidos_sup/*.sup` | C |
| `extrator_texto_bruto/extrator_texto_bruto.py` | `.mkv` + `.ass` já extraído | `texto_bruto_extraido_<capítulo>.txt` (roteiro numerado, para revisão manual) | utilitário, fora do pipeline automático |

Todos tratam variação de Track IDs automaticamente via `mkvextract`/`mkvmerge` (binário local do MKVToolNix), com fallback por prioridade de idioma quando há múltiplas faixas.

Log de auditoria das extrações: `info.txt` (raiz da pasta) — arquivo, Track ID, nome da faixa, formato, saída. Detalhes: [Logs e auditoria](logs-e-auditoria.md#fase-02--extração-de-legendas).

---

## Uso típico

```powershell
python ".\02_extrator_legenda\extrator_inteligente_ass.py"
python ".\02_extrator_legenda\extrator_inteligente_pgs.py"
```

---

## Pasta residual

`por_tipo/` contém apenas um `info.txt` de uma execução antiga — resíduo, sem impacto no pipeline atual.

---

[← Fase 01](modulo-fase-01.md) · [Índice](README.md) · [Fase 03 →](modulo-fase-03.md)
