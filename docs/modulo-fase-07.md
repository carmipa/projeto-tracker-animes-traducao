# 🩹 Fase 07 — Reparo de tradução

[← Índice](README.md) · [Arquitetura](arquitetura.md) · [Guia de execução](guia-de-execucao.md)

**Pasta:** [`07_reparo_traducao/`](../07_reparo_traducao/)

---

## O que faz

Conjunto de scripts para reparar/refinar legendas já traduzidas que ficaram com marcadores `[ERRO_TRADUCAO: ...]` ou que precisam de revisão fina (gênero, pronomes, resíduos de francês). Usa LM Studio (Gemma) para o reparo via IA, com opção de limpeza puramente offline para os casos persistentes.

---

## Scripts

| Script | Entrada | Saída | Função |
|:---|:---|:---|:---|
| `repara_erros_traducao.py` | `legendas_eng/*_ENG.ass` + `legendas_ptbr/*_PTBR.ass` com `[ERRO_TRADUCAO:]` | Mesmo `*_PTBR.ass`, em-place | Retradução avulsa (batch=1) via LM Studio, com tags restauradas |
| `limpa_erros_residuais.py` | Mesmo que acima | Mesmo arquivo, em-place | Substitui o erro pelo texto original (sem IA) — usado quando o termo é protegido/nome próprio |
| `refina_traducao_fr.py` | `legendas_ptbr/*_ENG.ass` (traduzido) + `traducao_cache_fr.json` | Mesmo arquivo + relatório no terminal | Revisão de gênero/concordância/patentes via engenharia reversa do cache francês |
| `extrai_linhas_suspeitas.py` | Legendas traduzidas | `linhas_para_revisar.json` | Varre e exporta falas que precisam de refinamento manual |
| `aplica_linhas_revisadas.py` | `linhas_revisadas.json` (editado manualmente) | `.ass` correspondentes + cache atualizado | Aplica de volta as correções revisadas à mão |

```powershell
# Requer LM Studio na porta 1234 (Gemma 4B)
python ".\07_reparo_traducao\repara_erros_traducao.py" "<legendas_eng>" "<legendas_ptbr>"
python ".\07_reparo_traducao\limpa_erros_residuais.py" "<legendas_eng>" "<legendas_ptbr>"
python ".\07_reparo_traducao\refina_traducao_fr.py"
```

`[ABORTADO] 5 falhas consecutivas` em `repara_erros_traducao.py` indica LM Studio offline/instável — arquivos já reparados são preservados; rode novamente após restaurar o servidor.

---

## Logs e troubleshooting

[Logs e auditoria — Fase 07](logs-e-auditoria.md#fase-07--reparo-de-tradução) · [Solução de problemas](solucao-de-problemas.md#fases-0711--reparo-de-tradução-e-esteira-h-guilty-crown)

---

[← Fase 06](modulo-fase-06.md) · [Índice](README.md) · [Fase 08 →](modulo-fase-08.md)
