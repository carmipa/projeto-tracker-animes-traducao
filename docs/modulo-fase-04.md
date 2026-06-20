# 🔁 Fase 04 — Conversor SRT → ASS

[← Índice](README.md) · [Arquitetura](arquitetura.md) · [Guia de execução](guia-de-execucao.md)

**Pasta:** [`04_conversor_srt_ass/`](../04_conversor_srt_ass/)

---

## O que faz

`conversor_srt_para_ass.py` converte uma legenda `.srt` já traduzida (`*_PTBR.srt`) para o formato estruturado `.ass`, aplicando correção matemática de sincronismo progressivo (`FATOR_SINCRO = 1.042709`, equivalente a 25fps → 23.976fps). Usado pelas **Esteiras B** (filme/SRT externo) e **C** (PGS, após OCR).

---

## Scripts

| Script | Entrada | Saída | Esteiras |
|:---|:---|:---|:---|
| `conversor_srt_para_ass.py` | `legenda/*_PTBR.srt` | `traducao/*_PTBR.ass` | B, C |
| `verificador.py` | — | — | placeholder, sem docstring/uso definido |

```powershell
python ".\04_conversor_srt_ass\conversor_srt_para_ass.py"
```

Prompts interativos: pasta com o `.srt` traduzido e pasta de saída do `.ass`. Detalhes de uso: [Pipeline SRT](pipeline-srt.md).

---

## Dessincronia

Se a legenda final ficar fora de sincronia, confira se a fonte realmente é 25fps — ajuste `FATOR_SINCRO` no script se for outro frame rate. Veja também [Fase 08](modulo-fase-08.md) para correção pós-remux.

---

[← Fase 03](modulo-fase-03.md) · [Índice](README.md) · [Fase 05a →](modulo-fase-05a.md)
