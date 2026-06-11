# 📚 Documentação — Tracker Animes

Índice central. O [README principal](../README.md) traz visão rápida e links para esta pasta.

---

## 🗂️ Guias gerais

| Documento | Conteúdo |
|:---|:---|
| [**Arquitetura do pipeline**](arquitetura.md) | Mapa das 8 fases + diagramas de todas as esteiras (A–F) |
| [Estrutura do repositório](estrutura-repositorio.md) | Árvore de pastas (fases 1–8) + pastas legadas |
| [**Pipeline SRT (Esteira B)**](pipeline-srt.md) | Filmes e legendas externas |
| [Instalação e pré-requisitos](instalacao.md) | Checklist SO, venv, LM Studio, MKVToolNix, FFmpeg |
| [Dependências Python](dependencias-python.md) | `requirements.txt` |
| [Guia de execução](guia-de-execucao.md) | Comandos por fase e por esteira |
| [Logs e auditoria](logs-e-auditoria.md) | Artefatos de log por fase |
| [Solução de problemas](solucao-de-problemas.md) | Troubleshooting |

---

## 🛠️ Módulos por fase

| Fase | Documento | Pasta / script principal |
|:---:|:---|:---|
| 1 | [Analisador de mídia](modulo-fase-1.md) | `1_analisador_de_midia/media_analyzer.py` |
| 2 | [Extração de legendas](modulo-fase-2.md) | `2_extrator_legenda/` (ASS, SRT, PGS) |
| 3 | [Conversor SRT → ASS](modulo-fase-3.md) | `3-conversor_str_ass/conversor_srt_para_ass.py` |
| 4 | [Tradução IA (LM Studio/Gemma)](modulo-fase-4.md) | `4_tradutor_ia_gemma4/` (5 variantes) |
| 5 | [Remuxer](modulo-fase-5.md) | `5_juntar_legendas_filmes/batch_remuxer.py` |
| 6 | [Sincronização de legendas](modulo-fase-6.md) | `6_sincronizacao_legenda/` |
| 7 | [Otimização de vídeo (GPU)](modulo-fase-7.md) | `7_decodificador/gpu_video_optimizer.py` |
| 8 | [Cura de legendas](modulo-fase-8.md) | `8_cura_legendas/` |

---

## 🔄 Esteiras (fluxos completos)

| Esteira | Fases | Cenário | Documento |
|:---:|:---|:---|:---|
| **A** | 4 → 5 | Episódio MKV, ASS embutido (inglês) | [Arquitetura](arquitetura.md#esteira-a--episódio-mkv-com-ass-embutido-inglês) |
| **B** | 4 → 3 → 5 | Filme com SRT externo (inglês) | [Pipeline SRT](pipeline-srt.md) |
| **C** | 2 → OCR externo → 3 → 5 | Legenda PGS (Blu-ray bitmap) | [Arquitetura](arquitetura.md#esteira-c--legenda-pgs-bluray-bitmap) |
| **D** | 4 → 5 | Episódio MKV, ASS embutido (francês) | [Arquitetura](arquitetura.md#esteira-d--tradução-francês--pt-br-multi-thread) |
| **E** | 2 → 4 → 5 | Lote ASS pré-extraído (Gundam Reconguista) | [Arquitetura](arquitetura.md#esteira-e--lote-ass-pré-extraído-gundam-reconguista) |
| **F** | 2 → 4 → 8 → 5 | Gundam Unicorn (especializada) | [Arquitetura](arquitetura.md#esteira-f--gundam-unicorn-especializada) |

Fases **1, 6, 7, 8** são auxiliares e podem ser usadas em qualquer esteira.

---

## Ordem de leitura

**Primeira vez:** [Instalação](instalacao.md) → [Arquitetura](arquitetura.md) → [Estrutura do repositório](estrutura-repositorio.md)

**Episódios MKV (Esteira A/D):** Fases [1](modulo-fase-1.md) (opcional) → [4](modulo-fase-4.md) → [5](modulo-fase-5.md)

**Filme/SRT (Esteira B):** [Pipeline SRT](pipeline-srt.md) → Fases 4 → 3 → 5

**Problemas:** [Logs](logs-e-auditoria.md) → [Solução de problemas](solucao-de-problemas.md)

---

## 👤 Autoria

**[Paulo André Carminati](https://github.com/carmipa)** · Python · Antigravity · Cursor IDE · Gemini · Claude

---

[← Voltar ao README principal](../README.md)
