# 📚 Documentação — Tracker Animes

Índice central. O [README principal](../README.md) traz visão rápida e links para esta pasta.

<p>
  <img src="https://img.shields.io/badge/Fases-00_a_12-blueviolet?style=flat-square" alt="Fases 00 a 12"/>
  <img src="https://img.shields.io/badge/Esteiras-A_a_N-9146FF?style=flat-square" alt="Esteiras A-N"/>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/LM_Studio-4_modelos-FF6B35?style=flat-square&logo=openai&logoColor=white" alt="LM Studio"/>
  <img src="https://img.shields.io/badge/100%25-Offline-success?style=flat-square" alt="Offline"/>
</p>

---

## 🗂️ Guias gerais

| Documento | Conteúdo |
|:---|:---|
| [**🏗️ Arquitetura do pipeline**](arquitetura.md) | Mapa das fases 00–12 + diagramas de todas as esteiras (A–N) |
| [📦 Estrutura do repositório](estrutura-repositorio.md) | Árvore de pastas real do projeto |
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
| 00 | [🧹 Higienização](modulo-fase-00.md) | `00_scripts_higienizacao/<Título>/` |
| 01 | [🔍 Analisador de mídia](modulo-fase-01.md) | `01_analisador_midia/media_analyzer.py` |
| 02 | [✂️ Extração de legendas](modulo-fase-02.md) | `02_extrator_legenda/` (ASS, SRT, PGS) |
| 03 | [🎮 Otimização de vídeo (GPU)](modulo-fase-03.md) | `03_decodificador_caracteres/gpu_video_optimizer.py` |
| 04 | [🔁 Conversor SRT → ASS](modulo-fase-04.md) | `04_conversor_srt_ass/conversor_srt_para_ass.py` |
| 05a | [🤖 Tradução IA (Gemma 4B)](modulo-fase-05a.md) | `05a_tradutor_llm_gemma4/` (multi-título, inglês) |
| 05b | [🇫🇷 Tradução IA (Mistral Nemo)](modulo-fase-05b.md) | `05b_tradutor_llm_mistral_nemo/` (francês + inglês) |
| 05c | [🐉 Tradução IA (Qwen2.5)](modulo-fase-05c.md) | `05c_tradutor_llm_qwen2/` (chinês simplificado) |
| 05c-2 | [🌐 Tradução/Revisão IA (TranslateGemma)](modulo-fase-05c2.md) | `05c_tradutor_llm_translategemma/` (inglês) |
| 06 | [🩹 Cura de legendas](modulo-fase-06.md) | `06_cura_legendas/` |
| 07 | [🩹 Reparo de tradução](modulo-fase-07.md) | `07_reparo_traducao/` |
| 08 | [⏱️ Sincronização de legendas](modulo-fase-08.md) | `08_sincronizacao_legenda/` |
| 09 | [🎵 Injetor de músicas](modulo-fase-09.md) | `09_injetor_musicas/injetor_de_musicas.py` |
| 10 | [🔬 Auditoria e revisão final](modulo-fase-10.md) | `10_auditoria_e_revisao/` |
| 11 | [🎨 Correção de projetos legados](modulo-fase-11.md) | `11_correcao_projetos_legados/` |
| 12 | [🎬 Remuxer](modulo-fase-12.md) | `12_remuxer_mkvmerge/batch_remuxer.py` |

---

## 🔄 Esteiras (fluxos completos)

| Esteira | Fases | Cenário | Documento |
|:---:|:---|:---|:---|
| **A** | 00 → 05a → 12 → [10] | Eighty-Six, ASS embutido (inglês) | [Arquitetura](arquitetura.md#esteira-a--eighty-six-ass-embutido-inglês) |
| **B** | 05a → 04 → 12 | Filme com SRT externo (inglês, Macross) | [Pipeline SRT](pipeline-srt.md) |
| **C** | 02 → OCR externo → 04 → 12 | Legenda PGS (Blu-ray bitmap) | [Arquitetura](arquitetura.md#esteira-c--legenda-pgs-bluray-bitmap) |
| **D** | 05b → 12 → [10] | Macross Delta TV, ASS embutido (francês) | [Arquitetura](arquitetura.md#esteira-d--macross-delta-tv-tradução-francês--pt-br) |
| **E** | 05b → 12 → 10 | Macross Delta Filme 2 (francês) | [Arquitetura](arquitetura.md#esteira-e--macross-delta-filme-2-francês) |
| **F** | 02 → 05a → 12 | Lote ASS pré-extraído (Gundam Reconguista) | [Arquitetura](arquitetura.md#esteira-f--lote-ass-pré-extraído-gundam-reconguista) |
| **G** | 02 → 05a → [06] → [10] → 12 | Gundam Unicorn (especializada) | [Arquitetura](arquitetura.md#esteira-g--gundam-unicorn-especializada) |
| **H** | 02 → 05a → 11 → [10] → 12 | Guilty Crown (correção de nomes e cores) | [Arquitetura](arquitetura.md#esteira-h--guilty-crown-correção-de-nomes-e-cores-de-músicas) |
| **I** | 02 → 05c → [10] → 12 | Gundam The Origin, legenda chinesa (CHS) | [Arquitetura](arquitetura.md#esteira-i--gundam-the-origin-legenda-chinesa-chs) |
| **J** | 05b → [07] → 12 | Gundam Origin, legenda francesa (SUBFRENCH) | [Arquitetura](arquitetura.md#esteira-j--gundam-origin-legenda-francesa-subfrench) |
| **K** | 05c-2 → 12 | Gundam Zeta | [Arquitetura](arquitetura.md#esteira-k--gundam-zeta) |
| **L** | 05c-2 → 12 | Gundam ZZ | [Arquitetura](arquitetura.md#esteira-l--gundam-zz) |
| **M** | 05b → 12 | Detonator Orgun | [Arquitetura](arquitetura.md#esteira-m--detonator-orgun) |
| **N** | 05a → 12 | Knights of Sidonia | [Arquitetura](arquitetura.md#esteira-n--knights-of-sidonia) |

`[10]`/`[06]`/`[07]` = passo opcional/condicional. **Fase 00** é transversal — normaliza lore/gramática de legendas já traduzidas, independente da esteira. **Fases 01, 03, 08, 09** são auxiliares, usadas conforme necessário em qualquer esteira. **Fases 05a/05b/05c/05c-2** são variantes de motor de IA do mesmo papel (extrai/traduz), escolhidas pelo idioma de origem e pelo título. **Fases 06, 07, 11** são reparos pós-tradução. A **Fase 10** é o catálogo de revisões finais por título.

---

## Ordem de leitura

**Primeira vez:** [Instalação](instalacao.md) → [Arquitetura](arquitetura.md) → [Estrutura do repositório](estrutura-repositorio.md)

**Episódios MKV (Esteira A, inglês, Gemma 4B):** Fases [01](modulo-fase-01.md) (opcional) → [05a](modulo-fase-05a.md) → [12](modulo-fase-12.md)

**Episódios MKV (Esteira D, francês, Mistral Nemo):** Fases [01](modulo-fase-01.md) (opcional) → [05b](modulo-fase-05b.md) → [12](modulo-fase-12.md)

**Filme/SRT (Esteira B):** [Pipeline SRT](pipeline-srt.md) → Fases 05a → 04 → 12

**Gundam The Origin (Esteira I, legenda chinesa):** [Fase 02](modulo-fase-02.md) → [Fase 05c](modulo-fase-05c.md) → [Fase 10](modulo-fase-10.md) → [Fase 12](modulo-fase-12.md)

**Problemas:** [Logs](logs-e-auditoria.md) → [Solução de problemas](solucao-de-problemas.md)

**Falhas `[ERRO_TRADUCAO:]` pós-tradução:** [Fase 07](modulo-fase-07.md) (reparo via IA/Gemma) ou [Fase 11](modulo-fase-11.md) (correção offline, Guilty Crown)

**Erros de lore/resíduos após a tradução:** [Fase 00](modulo-fase-00.md) (higienização por título) e [Fase 10](modulo-fase-10.md) (catálogo de scripts de QA + remux)

---

## 👤 Autoria

**[Paulo André Carminati](https://github.com/carmipa)** · Python · Antigravity · Cursor IDE · Gemini · Claude

---

[← Voltar ao README principal](../README.md)
