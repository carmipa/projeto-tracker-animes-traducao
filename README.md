<div align="center">

  <img src="icone.png?v=2" alt="Ícone do Projeto" width="220"/>

  <h1>🌌 Tracker Animes — Pipeline de Tradução & Multiplexação</h1>

  <p><strong>Esteira industrial local (on-premises) para auditar mídia, extrair, traduzir, sincronizar, curar e remuxar legendas de animes e filmes em PT-BR</strong></p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
    <img src="https://img.shields.io/badge/Windows-10%2F11-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows"/>
    <img src="https://img.shields.io/badge/LM_Studio-IA_Local-FF6B35?style=for-the-badge&logo=openai&logoColor=white" alt="LM Studio"/>
    <img src="https://img.shields.io/badge/MKVToolNix-Essencial-4B0082?style=for-the-badge&logo=ffmpeg&logoColor=white" alt="MKVToolNix"/>
    <img src="https://img.shields.io/badge/FFmpeg-NVENC_HEVC-2E7D32?style=for-the-badge&logo=ffmpeg&logoColor=white" alt="FFmpeg NVENC"/>
    <img src="https://img.shields.io/badge/Gemma_4B-LLM-00E5FF?style=for-the-badge&logo=google&logoColor=white" alt="Gemma 4B"/>
  </p>

  <p>
    <img src="https://img.shields.io/badge/100%25-Offline-success?style=flat-square" alt="Offline"/>
    <img src="https://img.shields.io/badge/Remux-Sem_Re--encode-blue?style=flat-square" alt="Remux"/>
    <img src="https://img.shields.io/badge/10_Fases-1_a_10-blueviolet?style=flat-square" alt="10 Fases"/>
    <img src="https://img.shields.io/badge/Esteiras-A_a_G-9146FF?style=flat-square" alt="Esteiras A-G"/>
    <img src="https://img.shields.io/badge/Logs-Auditáveis-informational?style=flat-square" alt="Logs"/>
  </p>

</div>

> **Documentação completa:** [`docs/`](docs/README.md) — guias por fase, diagramas e troubleshooting.

---

## 🚀 Visão geral

O projeto é organizado em **10 fases numeradas** (pastas `1_` a `10_`). Cada **esteira** (fluxo de trabalho) usa um subconjunto dessas fases, conforme o formato de origem da legenda (ASS embutido, SRT externo, PGS bitmap), o idioma de origem (inglês, francês) e eventuais reparos pós-tradução específicos da série.

| Fase | Pasta | Função |
|:---:|:---|:---|
| 1 | `1_analisador_de_midia/` | Audita mídia: codecs, faixas, sincronia *(opcional)* |
| 2 | `2_extrator_legenda/` | Extrai legenda original (ASS/SRT/PGS) do `.mkv` |
| 3 | `3-conversor_str_ass/` | Converte `*_PTBR.srt` → `*_PTBR.ass` com sync de FPS |
| 4 | `4_tradutor_ia_gemma4/` | Tradução via LM Studio + Gemma (5 variantes) |
| 5 | `5_juntar_legendas_filmes/` | Remux: junta vídeo + legenda PT-BR (sem re-encode) |
| 6 | `6_sincronizacao_legenda/` | Auxiliar: audita/corrige dessincronia |
| 7 | `7_decodificador/` | Auxiliar: recomprime vídeo (HEVC/NVENC) |
| 8 | `8_cura_legendas/` | Auxiliar: repara corrupção de tags PT-BR |
| 9 | `9_reparo_de_traducao/` | 🩹 Reparo: retraduz `[ERRO_TRADUCAO: ...]` via IA (batch=1) |
| 10 | `10_correcao_guilty_crown/` | 🎵 Correção offline de `[ERRO_TRADUCAO:]` e cores/tags de músicas OP/ED |

### Diagrama geral

```mermaid
flowchart LR
    MKV["Video .mkv"] --> F1["Fase 1\nAnalisador"]

    F1 -->|ASS embutido EN| A4["Fase 4\nsub_extractor.py"]
    F1 -->|ASS embutido FR| D4["Fase 4\nscript_tradutor_fr.py"]
    F1 -->|SRT externo| B4["Fase 4\ntradutor_srt_direto.py"]
    F1 -->|PGS bitmap| C2["Fase 2\nextrator_inteligente_pgs.py"]
    F1 -->|ASS para lote| E2["Fase 2\nextrator_inteligente_ass.py"]

    C2 --> OCR["OCR externo\nSubtitle Edit + Tesseract"]
    OCR --> C3["Fase 3\nconversor_srt_para_ass.py"]
    B4 --> B3["Fase 3\nconversor_srt_para_ass.py"]

    E2 --> E4["Fase 4\nbatch_translator_ass.py\nou batch_translator_unicorn.py"]
    E4 -.->|se TAG corrompido| F8["Fase 8\nCura de legendas"]
    E4 -.->|se ERRO_TRADUCAO| F9["Fase 9\nReparo via IA avulso"]
    D4 -.->|se ERRO_TRADUCAO| F9
    E4 -.->|Guilty Crown| F10["Fase 10\nCorrecao offline GC"]

    A4 --> F5["Fase 5\nbatch_remuxer.py"]
    D4 --> F5
    B3 --> F5
    C3 --> F5
    E4 --> F5
    F8 --> F5
    F9 --> F5
    F10 --> F5

    F5 --> OUT["mkv_final_ptbr/*_PTBR.mkv"]
    OUT -.->|opcional| F6["Fase 6\nSincronizacao"]
    OUT -.->|opcional, arquivo grande| F7["Fase 7\nOtimizacao GPU"]

    style F1 fill:#2d3748,stroke:#00E5FF,color:#fff
    style F5 fill:#1e4620,stroke:#32CD32,color:#fff
    style OUT fill:#1e4620,stroke:#32CD32,color:#fff
    style F8 fill:#5c1010,stroke:#ff4444,color:#fff
    style F9 fill:#5c1010,stroke:#ff4444,color:#fff
    style F10 fill:#5c1010,stroke:#ff4444,color:#fff
    style OCR fill:#5c1010,stroke:#ff4444,color:#fff
```

Diagramas detalhados de cada esteira: [docs/arquitetura.md](docs/arquitetura.md).

### Esteiras (fluxos completos)

| Esteira | Fases | Cenário |
|:---:|:---|:---|
| **A** | 4 → 5 | Episódio MKV, ASS embutido (inglês) |
| **B** | 4 → 3 → 5 | Filme com SRT externo (inglês) |
| **C** | 2 → OCR externo → 3 → 5 | Legenda PGS (Blu-ray bitmap) |
| **D** | 4 → 5 | Episódio MKV, ASS embutido (francês), multi-thread |
| **E** | 2 → 4 → 5 | Lote ASS pré-extraído (Gundam Reconguista) |
| **F** | 2 → 4 → 8 → 5 | Gundam Unicorn (especializada, com cura de legendas) |
| **G** | 2 → 4 → 10 → 5 | Guilty Crown (correção de nomes e cores de músicas) |

| ⚡ Remux ~1,5 s/ep. | 🔒 LLM local | 📺 PT-BR faixa padrão | 🎬 Sync FPS 25→23.976 | 🎮 Otimização NVENC | 🩹 Reparo `[ERRO_TRADUCAO:]` |
|:---:|:---:|:---:|:---:|:---:|:---:|

---

## ⚡ Início rápido

```powershell
cd C:\TRACKER-ANIMES\projeto-tracker-animes-traducao
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# LM Studio: Gemma 4B na porta 1234
```

**Esteira A — Episódios MKV (ASS embutido EN):**

```powershell
python ".\1_analisador_de_midia\media_analyzer.py"   # opcional
python ".\4_tradutor_ia_gemma4\sub_extractor.py"
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
```

**Esteira B — Filme (SRT externo):**

```powershell
python ".\4_tradutor_ia_gemma4\5_tradutor_de_legenda\tradutor_srt_direto.py"
python ".\3-conversor_str_ass\conversor_srt_para_ass.py"
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
```

**Esteira C — Legenda PGS (Blu-ray):**

```powershell
python ".\2_extrator_legenda\extrator_inteligente_pgs.py"
# OCR externo (Subtitle Edit + Tesseract) -> *_PTBR.srt
python ".\3-conversor_str_ass\conversor_srt_para_ass.py"
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
```

Demais esteiras (D, E, F, G) e fases auxiliares/reparos (6, 7, 8, 9, 10): [Guia de execução](docs/guia-de-execucao.md).

Pré-requisitos: **[docs/instalacao.md](docs/instalacao.md)** · Esteira B detalhada: **[docs/pipeline-srt.md](docs/pipeline-srt.md)**

---

## 📑 Índice da documentação

### Guias gerais

| Guia | Descrição |
|:---|:---|
| **[📖 Índice completo](docs/README.md)** | Hub da documentação |
| [Arquitetura](docs/arquitetura.md) | 10 fases + diagramas de todas as esteiras (A–G) |
| [Estrutura do repositório](docs/estrutura-repositorio.md) | Árvore de pastas e pastas legadas |
| [Pipeline SRT (Esteira B)](docs/pipeline-srt.md) | Filmes e legendas externas |
| [Instalação](docs/instalacao.md) | Checklist SO, venv, LM Studio, MKVToolNix, FFmpeg |
| [Dependências Python](docs/dependencias-python.md) | `requirements.txt` por fase |
| [Guia de execução](docs/guia-de-execucao.md) | Comandos por esteira e layout de pastas |
| [Logs e auditoria](docs/logs-e-auditoria.md) | Artefatos de log por fase |
| [Solução de problemas](docs/solucao-de-problemas.md) | Troubleshooting por esteira |

### Módulos por fase

| Fase | Documento | Pasta / script principal |
|:---:|:---|:---|
| 1 | [Analisador de mídia](docs/modulo-fase-1.md) | `1_analisador_de_midia/media_analyzer.py` |
| 2 | [Extração de legendas](docs/modulo-fase-2.md) | `2_extrator_legenda/` (ASS, SRT, PGS) |
| 3 | [Conversor SRT → ASS](docs/modulo-fase-3.md) | `3-conversor_str_ass/conversor_srt_para_ass.py` |
| 4 | [Tradução IA (LM Studio/Gemma)](docs/modulo-fase-4.md) | `4_tradutor_ia_gemma4/` (5 variantes) |
| 5 | [Remuxer](docs/modulo-fase-5.md) | `5_juntar_legendas_filmes/batch_remuxer.py` |
| 6 | [Sincronização de legendas](docs/modulo-fase-6.md) | `6_sincronizacao_legenda/` |
| 7 | [Otimização de vídeo (GPU)](docs/modulo-fase-7.md) | `7_decodificador/gpu_video_optimizer.py` |
| 8 | [Cura de legendas](docs/modulo-fase-8.md) | `8_cura_legendas/` |
| 9 | [Reparo de tradução](docs/modulo-fase-9.md) | `9_reparo_de_traducao/` |
| 10 | [Correção Guilty Crown](docs/modulo-fase-10.md) | `10_correcao_guilty_crown/` |

### Esteiras (fluxos completos)

| Esteira | Fases | Cenário | Documento |
|:---:|:---|:---|:---|
| **A** | 4 → 5 | Episódio MKV, ASS embutido (inglês) | [Arquitetura](docs/arquitetura.md#esteira-a--episódio-mkv-com-ass-embutido-inglês) |
| **B** | 4 → 3 → 5 | Filme com SRT externo (inglês) | [Pipeline SRT](docs/pipeline-srt.md) |
| **C** | 2 → OCR externo → 3 → 5 | Legenda PGS (Blu-ray bitmap) | [Arquitetura](docs/arquitetura.md#esteira-c--legenda-pgs-bluray-bitmap) |
| **D** | 4 → 5 | Episódio MKV, ASS embutido (francês) | [Arquitetura](docs/arquitetura.md#esteira-d--tradução-francês--pt-br-multi-thread) |
| **E** | 2 → 4 → 5 | Lote ASS pré-extraído (Gundam Reconguista) | [Arquitetura](docs/arquitetura.md#esteira-e--lote-ass-pré-extraído-gundam-reconguista) |
| **F** | 2 → 4 → 8 → 5 | Gundam Unicorn (especializada) | [Arquitetura](docs/arquitetura.md#esteira-f--gundam-unicorn-especializada) |
| **G** | 2 → 4 → 10 → 5 | Guilty Crown (correção de nomes e cores) | [Arquitetura](docs/arquitetura.md#esteira-g--guilty-crown-correção-de-nomes-e-cores-de-músicas) |

---

## 📄 Licença

[LICENSE](LICENSE)

---

<div align="center">

  <p>
    <strong>Construído por</strong>
    <a href="https://github.com/carmipa"><strong>Paulo André Carminati</strong></a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
    <img src="https://img.shields.io/badge/Antigravity-FF6B35?style=flat-square" alt="Antigravity"/>
    <img src="https://img.shields.io/badge/Cursor_IDE-000000?style=flat-square&logo=cursor&logoColor=white" alt="Cursor IDE"/>
    <img src="https://img.shields.io/badge/Gemini-4285F4?style=flat-square&logo=google&logoColor=white" alt="Gemini"/>
    <img src="https://img.shields.io/badge/Claude-CC785C?style=flat-square" alt="Claude"/>
  </p>

  <p><sub>Pipeline industrial de tradução local · Junho 2026</sub></p>

</div>
