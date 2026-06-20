# 🐉 Fase 05c — Tradução IA (LM Studio + Qwen2.5-7B-Instruct)

[← Índice](README.md) · [Arquitetura](arquitetura.md) · [Guia de execução](guia-de-execucao.md)

**Pasta:** [`05c_tradutor_llm_qwen2/`](../05c_tradutor_llm_qwen2/)

---

## O que faz

Motor de tradução **chinês simplificado (CHS) → PT-BR** via LM Studio + Qwen2.5-7B-Instruct, dedicado a **Gundam The Origin** (Esteira I) — o único título do pipeline com legenda chinesa embutida.

---

## Scripts

| Script | Entrada | Saída | Função |
|:---|:---|:---|:---|
| `batch_translator_origin_zh.py` | `*.chs.ass` (saída da [Fase 02](modulo-fase-02.md)) | `legendas_ptbr/*_PTBR.ass` | Tradução em lote (Batch Mode v5 — Resiliente), cache persistente (`traducao_cache_origin_zh.json` + `.bak`), fallback linha a linha |
| `repara_erros_origin_zh.py` | `legendas_ptbr/*_PTBR.ass` com `[ERRO_TRADUCAO:]` | Mesmo arquivo, em-place | Reparo avulso (batch=1) com suporte a raciocínio (CoT) via LM Studio |
| `test_reparo.py` | — | `debug_test.txt` | Utilitário de depuração manual (3 linhas fixas), fora do pipeline regular |

```powershell
# Pré-requisito: LM Studio na porta 1234 com qwen2.5-7b-instruct carregado
python ".\05c_tradutor_llm_qwen2\batch_translator_origin_zh.py" --entrada "<pasta_chs_ass>" --saida "<pasta_saida>"
python ".\05c_tradutor_llm_qwen2\repara_erros_origin_zh.py" --originais "<pasta_chs_ass>" --traduzidas "<pasta_ptbr>"
```

`MAX_THREADS = 2` é o limite seguro para GPUs com 8GB de VRAM — reduza `--batch-size` ou use `--threads 1` se necessário.

---

## Logs e troubleshooting

[Logs e auditoria — Fase 05c](logs-e-auditoria.md#fase-05c--tradução-chinês-qwen25-gundam-the-origin) · [Solução de problemas — Esteira I](solucao-de-problemas.md#esteira-i--gundam-the-origin-legenda-chinesa-fases-02--05c--10--12)

---

[← Fase 05b](modulo-fase-05b.md) · [Índice](README.md) · [Fase 05c-2 →](modulo-fase-05c2.md)
