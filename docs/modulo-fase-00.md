# 🧹 Fase 00 — Higienização de lore e gramática

[← Índice](README.md) · [Arquitetura](arquitetura.md) · [Guia de execução](guia-de-execucao.md)

**Pasta:** [`00_scripts_higienizacao/`](../00_scripts_higienizacao/)

---

## O que faz

Normaliza, por **título**, termos de lore/marca, gramática (gerundismo, "mais"/"mas", literalismos de IA) e formatação de tags ASS em uma legenda **já traduzida** (saída das Fases 05a/05b/05c/05c-2, geralmente já passada pelas Fases 07/10/11 quando aplicável). Cada subpasta contém um ou mais scripts hardcoded para o glossário e os bugs conhecidos de um título específico — não são genéricos entre séries.

> **Sobre o prefixo `00`:** é apenas ordenação alfabética no explorador de arquivos. Na prática, a higienização roda **depois** da tradução, não antes — geralmente como o último ajuste de texto antes (ou depois) do remux da [Fase 12](modulo-fase-12.md).

---

## Scripts por título

| Pasta | Script(s) | Título | Observação |
|:---|:---|:---|:---|
| `86_Eighty_Six/` | `audit_86.py`, `limpeza_geral_86.py` | Eighty-Six (Esteira A) | Patentes/jargões militares; auditoria separada da limpeza |
| `Detonator_Orgun/` | `limpeza_geral_orgun.py` | Detonator Orgun (Esteira M) | Normalização de lore/marca |
| `Guilty_Crown/` | `limpeza_geral_guilty.py` | Guilty Crown (Esteira H) | Roda após a [Fase 11](modulo-fase-11.md) |
| `Gundam_Origin/` | `limpeza_origin_extrema.py`, `limpeza_origin_finais.py`, `limpeza_origin_gramatica_profunda.py`, `limpeza_origin_total.py` | Gundam Origin, francês (Esteira J) | 4 scripts: correção de `\N` mal formatado, dicionário de correção contextual FR→PT-BR, francesismos/vocabulário |
| `Gundam_The_Origin/` | `limpeza_geral_origin.py` | Gundam The Origin, chinês (Esteira I) | Pasta com nome distinto de `Gundam_Origin/` — não confundir |
| `Gundam_Unicorn/` | `limpeza_geral_unicorn.py` | Gundam Unicorn (Esteira G) | |
| `Gundam_Zeta/` | `limpeza_zeta_extrema.py` | Gundam Zeta (Esteira K) | Motor regex `\b` (V3): lore case-insensitive, balanceamento de tags itálico/negrito |
| `Knights_of_Sidonia/` | `limpeza_sidonia_extrema.py` | Knights of Sidonia (Esteira N) | |
| `Macross_Delta/` | `limpeza_geral_macross.py` | Macross Delta TV (Esteira D) | |
| `Macross_Delta_Filme_1/` | `limpeza_macross_filme1_extrema.py` | Macross Delta Filme 1 | |
| `Macross_Delta_Filme_2/` | `limpeza_macross_filme2_extrema.py` | Macross Delta Filme 2 (Esteira E) | |
| `Sword_Art_Online_Filme_2/` | `limpeza_sao_filme2_extrema.py` | SAO Filme 2 (Esteira C) | |

> **Gundam ZZ** (Esteira L) ainda não tem script de higienização dedicado — título mais recente do pipeline.

---

## Uso típico

```powershell
python ".\00_scripts_higienizacao\Gundam_Zeta\limpeza_zeta_extrema.py"
```

Cada script edita o `.ass` traduzido **em-place** (ou grava em uma pasta de saída própria, conforme o script) — confira o cabeçalho/prompt interativo de cada um antes de rodar em um título diferente.

---

## Relação com outras fases

- Roda depois das Fases **05a/05b/05c/05c-2** (precisa de texto já em PT-BR).
- Pode rodar antes ou depois da [Fase 10](modulo-fase-10.md) (revisão final por título) — não há ordem rígida entre as duas; verifique o que cada script de um título espera como entrada.
- Não deve ser usada para `[ERRO_TRADUCAO:]` — isso é tarefa das Fases [07](modulo-fase-07.md)/[11](modulo-fase-11.md).

---

[← Índice](README.md) · [Fase 01 →](modulo-fase-01.md)
