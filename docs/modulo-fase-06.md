# 🩹 Fase 06 — Cura de legendas

[← Índice](README.md) · [Arquitetura](arquitetura.md) · [Guia de execução](guia-de-execucao.md)

**Pasta:** [`06_cura_legendas/`](../06_cura_legendas/)

---

## O que faz

Repara offline (sem IA) a corrupção conhecida em que a palavra `TAG` (ou `_TAG_`) aparece grudada no início/meio dos diálogos traduzidos, restaurando as tags ASS originais. Específica para o pipeline de **Gundam Unicorn** (Esteira G), mas reaproveitável para outros títulos que usem o mesmo mascaramento de tags.

---

## Scripts

| Script | Entrada | Saída | Modo |
|:---|:---|:---|:---|
| `cura_legendas_tag.py` | `legendas_eng/*_ENG.ass` + `traducao/*_PTBR.ass` | `traducao_curada/*_PTBR.ass` | Casamento ENG/PTBR — restaura a tag correta linha a linha |
| `cura_gundam_mkv.py` | `.mkv` já remuxado (Gundam Unicorn) com `TAG` residual | `.mkv` corrigido | Dois modos: cura com correspondência (com `*_ENG.ass`) ou cura cega (regex, sem ENG) |

```powershell
python ".\06_cura_legendas\cura_legendas_tag.py"
python ".\06_cura_legendas\cura_gundam_mkv.py"
```

Processamento 100% offline — segundos para uma temporada completa.

---

[← Fase 05c-2](modulo-fase-05c2.md) · [Índice](README.md) · [Fase 07 →](modulo-fase-07.md)
