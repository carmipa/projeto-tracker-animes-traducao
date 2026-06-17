# 📚 Documentação — Tracker Animes

Índice central. O [README principal](../README.md) traz visão rápida e links para esta pasta.

<p>
  <img src="https://img.shields.io/badge/12_Fases-1_a_12-blueviolet?style=flat-square" alt="12 Fases"/>
  <img src="https://img.shields.io/badge/Esteiras-A_a_I-9146FF?style=flat-square" alt="Esteiras A-I"/>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/LM_Studio-Gemma_%2B_Qwen2.5-FF6B35?style=flat-square&logo=openai&logoColor=white" alt="LM Studio"/>
  <img src="https://img.shields.io/badge/100%25-Offline-success?style=flat-square" alt="Offline"/>
</p>

---

## 🗂️ Guias gerais

| Documento | Conteúdo |
|:---|:---|
| [**🏗️ Arquitetura do pipeline**](arquitetura.md) | Mapa das 12 fases + diagramas de todas as esteiras (A–I) |
| [📦 Estrutura do repositório](estrutura-repositorio.md) | Árvore de pastas (fases 1–12) + pastas legadas |
| [**🎬 Pipeline SRT (Esteira B)**](pipeline-srt.md) | Filmes e legendas externas |
| [⚙️ Instalação e pré-requisitos](instalacao.md) | Checklist SO, venv, LM Studio, MKVToolNix, FFmpeg |
| [🐍 Dependências Python](dependencias-python.md) | `requirements.txt` |
| [▶️ Guia de execução](guia-de-execucao.md) | Comandos por fase e por esteira |
| [📊 Logs e auditoria](logs-e-auditoria.md) | Artefatos de log por fase |
| [⚠️ Solução de problemas](solucao-de-problemas.md) | Troubleshooting |

---

## 🛠️ Módulos por fase

| Fase | Documento | Pasta / script principal |
|:---:|:---|:---|
| 1 | [🔍 Analisador de mídia](modulo-fase-1.md) | `1_analisador_de_midia/media_analyzer.py` |
| 2 | [✂️ Extração de legendas](modulo-fase-2.md) | `2_extrator_legenda/` (ASS, SRT, PGS) |
| 3 | [🔁 Conversor SRT → ASS](modulo-fase-3.md) | `3-conversor_str_ass/conversor_srt_para_ass.py` |
| 4 | [🤖 Tradução IA (LM Studio/Gemma)](modulo-fase-4.md) | `4_tradutor_ia_gemma4/` (4 variantes, inglês, 1 por título) |
| 4-B | [🇫🇷 Tradução IA (LM Studio/Mistral Nemo)](modulo-fase-4b.md) | `4_b_mistrall_nemo_instruct_2407_GGUF_tradutor/` (2 variantes, francês) |
| 5 | [🎬 Remuxer](modulo-fase-5.md) | `5_juntar_legendas_filmes/batch_remuxer.py` |
| 6 | [⏱️ Sincronização de legendas](modulo-fase-6.md) | `6_sincronizacao_legenda/` |
| 7 | [🎮 Otimização de vídeo (GPU)](modulo-fase-7.md) | `7_decodificador/gpu_video_optimizer.py` |
| 8 | [🩹 Cura de legendas](modulo-fase-8.md) | `8_cura_legendas/` |
| 9 | [🩹 Reparo de tradução](modulo-fase-9.md) | `9_reparo_de_traducao/` |
| 10 | [🎵 Correção Guilty Crown](modulo-fase-10.md) | `10_correcao_guilty_crown/` |
| 11 | [🐉 Tradução chinês (Qwen2.5)](modulo-fase-11.md) | `11_chines_LLM_alibaba_qwen2/` |
| 12 | [🔬 Revisão final por título](modulo-fase-12.md) | `12_revisao_legenda/` |

---

## 🔄 Esteiras (fluxos completos)

| Esteira | Fases | Cenário | Documento |
|:---:|:---|:---|:---|
| **A** | 4 → [12] → 5 | Eighty-Six, ASS embutido (inglês) | [Arquitetura](arquitetura.md#esteira-a--episódio-mkv-com-ass-embutido-inglês) |
| **B** | 4 → 3 → 5 | Filme com SRT externo (inglês, Macross) | [Pipeline SRT](pipeline-srt.md) |
| **C** | 2 → OCR externo → 3 → 5 | Legenda PGS (Blu-ray bitmap) | [Arquitetura](arquitetura.md#esteira-c--legenda-pgs-bluray-bitmap) |
| **D** | 4-B → [12] → 5 | Macross Delta, ASS embutido (francês, Mistral Nemo) | [Arquitetura](arquitetura.md#esteira-d--macross-delta-tradução-francês--pt-br-multi-thread) |
| **E** | 2 → 4 → 5 | Lote ASS pré-extraído (Gundam Reconguista) | [Arquitetura](arquitetura.md#esteira-e--lote-ass-pré-extraído-gundam-reconguista) |
| **F** | 2 → 4 → 8 → [12] → 5 | Gundam Unicorn (especializada) | [Arquitetura](arquitetura.md#esteira-f--gundam-unicorn-especializada) |
| **G** | 2 → 4 → 10 → [12] → 5 | Guilty Crown (correção de nomes e cores) | [Arquitetura](arquitetura.md#esteira-g--guilty-crown-correção-de-nomes-e-cores-de-músicas) |
| **H** | 2 → 11 → [12] → 5 | Gundam Origin, legenda chinesa (CHS, Qwen2.5) | [Arquitetura](arquitetura.md#esteira-h--gundam-origin-legenda-chinesa-chs-qwen25) |
| **I** | 4-B → 5 | Gundam Origin, legenda francesa (SUBFRENCH, Mistral Nemo) | [Arquitetura](arquitetura.md#esteira-i--gundam-origin-legenda-francesa-subfrench) |

`[12]` = passo opcional de QA/correção final por título. Fases **1, 6, 7, 8** são auxiliares e podem ser usadas em qualquer esteira. **Fase 4-B** é a variante em francês da Fase 4 (modelo Mistral Nemo em vez de Gemma). Fases **9, 10, 11** são reparos pós-tradução para falhas `[ERRO_TRADUCAO:]`. A Fase **12** é o catálogo de revisões finais por título.

---

## Ordem de leitura

**Primeira vez:** [Instalação](instalacao.md) → [Arquitetura](arquitetura.md) → [Estrutura do repositório](estrutura-repositorio.md)

**Episódios MKV (Esteira A, inglês):** Fases [1](modulo-fase-1.md) (opcional) → [4](modulo-fase-4.md) → [5](modulo-fase-5.md)

**Episódios MKV (Esteira D, francês):** Fases [1](modulo-fase-1.md) (opcional) → [4-B](modulo-fase-4b.md) → [5](modulo-fase-5.md)

**Filme/SRT (Esteira B):** [Pipeline SRT](pipeline-srt.md) → Fases 4 → 3 → 5

**Gundam Origin (Esteira H, legenda chinesa):** [Fase 2](modulo-fase-2.md) → [Fase 11](modulo-fase-11.md) → [Fase 12](modulo-fase-12.md) → [Fase 5](modulo-fase-5.md)

**Problemas:** [Logs](logs-e-auditoria.md) → [Solução de problemas](solucao-de-problemas.md)

**Falhas `[ERRO_TRADUCAO:]` pós-tradução:** [Fase 9](modulo-fase-9.md) (reparo via IA/Gemma), [Fase 10](modulo-fase-10.md) (correção offline, Guilty Crown) ou [Fase 11](modulo-fase-11.md#repara_erros_origin_zhpy) (reparo via IA/Qwen2.5, Gundam Origin)

**Erros de lore/resíduos após a tradução:** [Fase 12](modulo-fase-12.md) — catálogo de scripts de QA por título

---

## 👤 Autoria

**[Paulo André Carminati](https://github.com/carmipa)** · Python · Antigravity · Cursor IDE · Gemini · Claude

---

[← Voltar ao README principal](../README.md)
