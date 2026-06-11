# 📚 Documentação — Tracker Animes

Índice central. O [README principal](../README.md) traz visão rápida e links para esta pasta.

---

## 🗂️ Guias gerais

| Documento | Conteúdo |
|:---|:---|
| [Estrutura do repositório](estrutura-repositorio.md) | Árvore de pastas (fases 0–6) |
| [Arquitetura do pipeline](arquitetura.md) | Duas esteiras MKV e SRT + diagramas |
| [**Pipeline SRT (5→6→2)**](pipeline-srt.md) | Filmes e legendas externas |
| [Instalação e pré-requisitos](instalacao.md) | Checklist SO, venv, LM Studio |
| [Dependências Python](dependencias-python.md) | `requirements.txt` |
| [Guia de execução](guia-de-execucao.md) | Comandos por fase |
| [Logs e auditoria](logs-e-auditoria.md) | Artefatos de log |
| [Solução de problemas](solucao-de-problemas.md) | Troubleshooting |

---

## 🛠️ Módulos por fase

### Esteira MKV (episódios)

| Fase | Documento | Script |
|:---:|:---|:---|
| 0 | [Analisador](modulo-fase-0.md) | `1_analisador_de_midia/media_analyzer.py` |
| 1 | [Tradutor MKV](modulo-fase-1.md) | `2_tradutor_ia_gemma4/sub_extractor.py` |
| 2 | [Remuxer](modulo-fase-2.md) | `3_juntar_legendas_filmes/batch_remuxer.py` |

### Esteira SRT (legendas externas)

| Fase | Documento | Script |
|:---:|:---|:---|
| 5 | [Tradutor SRT direto](modulo-fase-5.md) | `5_tradutor_de_legenda/tradutor_srt_direto.py` |
| 6 | [Conversor SRT→ASS](modulo-fase-6.md) | `3-conversor_str_ass/conversor_srt_para_ass.py` |
| 2 | [Remuxer](modulo-fase-2.md) | *(mesmo da esteira MKV)* |

---

## 🔄 Ordem de leitura

**Episódios:** [Instalação](instalacao.md) → [Arquitetura](arquitetura.md) → Fases 0→1→2 → [Logs](logs-e-auditoria.md)

**Filmes / SRT:** [Instalação](instalacao.md) → [Pipeline SRT](pipeline-srt.md) → Fases 5→6→2

---

## 👤 Autoria

**[Paulo André Carminati](https://github.com/carmipa)** · Python · Antigravity · Cursor IDE · Gemini · Claude

---

[← Voltar ao README principal](../README.md)
