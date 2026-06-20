# 🇫🇷 Fase 05b — Tradução IA (LM Studio + Mistral Nemo Instruct 2407)

[← Índice](README.md) · [Arquitetura](arquitetura.md) · [Guia de execução](guia-de-execucao.md)

**Pasta:** [`05b_tradutor_llm_mistral_nemo/`](../05b_tradutor_llm_mistral_nemo/)

---

## O que faz

Motor de tradução via LM Studio + **Mistral Nemo Instruct 2407 (GGUF)** — substituiu o Gemma 4B para o par francês→português (qualidade muito superior) e também é usado para um título em inglês (Detonator Orgun).

---

## Scripts

| Script | Entrada | Saída | Título / Esteira |
|:---|:---|:---|:---|
| `frances_para_ptbr/macross_deslta.py` | `.mkv` (ASS embutido FR) | `traducao/*_PTBR.ass` | Macross Delta TV (Esteira D) e Filme 2 (Esteira E) — extrai + traduz, multi-thread (2 threads) |
| `frances_para_ptbr/script_tradutor_fr_gundam_origin.py` | `.mkv` (ASS embutido FR, SUBFRENCH) | `traducao/*_PTBR.ass` | Gundam Origin, legenda francesa (Esteira J) |
| `Detonator_Orgun/script_tradutor_en_detonator_orgun.py` | `.mkv`/`.srt` (EN) | `traducao/*_PTBR.ass` | Detonator Orgun (Esteira M) — validador anti-alucinação em inglês |

Cada subpasta mantém seu próprio cache (`traducao_cache_fr.json`, `traducao_cache_orgun_en.json`).

---

## Uso típico

```powershell
# Pré-requisito: LM Studio na porta 1234 com mistralai/mistral-nemo-instruct-2407 (GGUF) carregado
python ".\05b_tradutor_llm_mistral_nemo\frances_para_ptbr\macross_deslta.py"
python ".\05b_tradutor_llm_mistral_nemo\frances_para_ptbr\script_tradutor_fr_gundam_origin.py"
python ".\05b_tradutor_llm_mistral_nemo\Detonator_Orgun\script_tradutor_en_detonator_orgun.py"
```

---

## Nota — rótulo de modelo desatualizado em `config_fr_*.txt`

O snapshot de configuração (`config_fr_*.txt`) ainda imprime "Modelo: Gemma 4B" em ambos os scripts de `frances_para_ptbr/`, resíduo da época em que esses scripts usavam Gemma 4B. **A tradução em si usa o modelo correto** (Mistral Nemo) — confira o modelo real na linha `Usando modelo: ...` do `pipeline_fr_*.txt`. Detalhes: [Solução de problemas](solucao-de-problemas.md#fase-05b--mistral-nemo-francês-e-inglês).

---

[← Fase 05a](modulo-fase-05a.md) · [Índice](README.md) · [Fase 05c →](modulo-fase-05c.md)
