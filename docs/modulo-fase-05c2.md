# 🌐 Fase 05c-2 — Tradução/Revisão IA (LM Studio + TranslateGemma 12B)

[← Índice](README.md) · [Arquitetura](arquitetura.md) · [Guia de execução](guia-de-execucao.md)

**Pasta:** [`05c_tradutor_llm_translategemma/`](../05c_tradutor_llm_translategemma/)

---

## O que faz

Motor de tradução/revisão via LM Studio + **TranslateGemma 12B**, usado para **Gundam Zeta**, como rota legada/alternativa de **Gundam ZZ** (tradução inglês→PT-BR) e para revisão gramatical de PT-BR já traduzido em Gundam Origin. Para Gundam ZZ, a rota recomendada agora é o script Mistral Nemo da [Fase 05b](modulo-fase-05b.md). Compartilha o prefixo de pasta `05c_` com a [Fase 05c](modulo-fase-05c.md) (Qwen2.5) — são variantes-irmãs de motor de IA, não fases sequenciais.

---

## Scripts

| Script | Entrada | Saída | Título / Esteira |
|:---|:---|:---|:---|
| `Gundam_Zeta/script_tradutor_en_gundam_zeta.py` | `.mkv` (ASS embutido EN) | `traducao/*_PTBR.ass` | Gundam Zeta (Esteira K) — otimizado para preservação de tags/lore |
| `Gundam_ZZ/script_tradutor_en_gundam_zz.py` | `.mkv` (ASS embutido EN) | `traducao/*_PTBR.ass` | Gundam ZZ (Esteira L) — rota legada/alternativa; prefira `05b_tradutor_llm_mistral_nemo/Gundam_ZZ/tradutor_mistral_gundam_zz.py` |
| `Gundam_Origin/script_revisor_ptbr_gundam_origin.py` | PT-BR já traduzido (corrompido/com erros) | PT-BR revisado | Corretor ortográfico — TranslateGemma operando como revisor, não tradutor |

Cada script de tradução mantém seu próprio cache (`traducao_cache_gundam_zeta_en.json`, `traducao_cache_gundam_zz_en.json`).

```powershell
# Pré-requisito: LM Studio na porta 1234 com TranslateGemma 12B carregado
python ".\05c_tradutor_llm_translategemma\Gundam_Zeta\script_tradutor_en_gundam_zeta.py"
python ".\05c_tradutor_llm_translategemma\Gundam_ZZ\script_tradutor_en_gundam_zz.py"
```

> Para Gundam ZZ, prefira a rota Mistral Nemo da Fase 05b, que já incorpora glossário de lore no prompt/pós-processamento e pode ser seguida pela revisão dedicada da [Fase 07](modulo-fase-07.md).

---

[← Fase 05c](modulo-fase-05c.md) · [Índice](README.md) · [Fase 06 →](modulo-fase-06.md)
