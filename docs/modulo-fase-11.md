# 🎨 Fase 11 — Correção de projetos legados

[← Índice](README.md) · [Arquitetura](arquitetura.md) · [Guia de execução](guia-de-execucao.md)

**Pasta:** [`11_correcao_projetos_legados/`](../11_correcao_projetos_legados/)

---

## O que faz

Correção **100% offline** (sem IA) especializada para **Guilty Crown** (Esteira H): remove marcadores `[ERRO_TRADUCAO:]` restaurando o texto original (geralmente nomes próprios) e corrige cores/tags das músicas de abertura/encerramento.

---

## Scripts

| Script | Entrada | Saída |
|:---|:---|:---|
| `corrigir_guilty_crown.py` | `legendas_eng/*_ENG.ass` com `[ERRO_TRADUCAO:]` | `legendas_ptbr/*_PTBR.ass` |
| `corrigir_cores_musicas.py` | `legendas_ptbr/*_PTBR.ass` | Mesmo arquivo, em-place — cor principal branca (`\c&HFFFFFF&`), contorno preto (`\3c&H000000&`), remoção de resíduos `TAG` |

```powershell
python ".\11_correcao_projetos_legados\corrigir_guilty_crown.py"
python ".\11_correcao_projetos_legados\corrigir_cores_musicas.py"
```

Relatórios: `relatorio_correcao.txt` e `relatorio_cores_musicas.txt` (raiz da pasta).

---

[← Fase 10](modulo-fase-10.md) · [Índice](README.md) · [Fase 12 →](modulo-fase-12.md)
