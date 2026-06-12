# 🏗️ Arquitetura do Pipeline

[← Índice da documentação](README.md) · [README principal](../README.md)

<p>
  <img src="https://img.shields.io/badge/10_Fases-1_a_10-blueviolet?style=flat-square" alt="10 Fases"/>
  <img src="https://img.shields.io/badge/Esteiras-A_a_G-9146FF?style=flat-square" alt="Esteiras A-G"/>
  <img src="https://img.shields.io/badge/100%25-Offline-success?style=flat-square" alt="Offline"/>
  <img src="https://img.shields.io/badge/Remux-Sem_Re--encode-blue?style=flat-square" alt="Remux sem re-encode"/>
</p>

O projeto é organizado em **10 fases numeradas** (pastas `1_` a `10_`). Cada **esteira** (fluxo de trabalho) usa um subconjunto dessas fases, dependendo do formato de origem da legenda (ASS embutido, SRT externo, PGS bitmap), do idioma de origem (inglês, francês) e de eventuais reparos pós-tradução específicos da série.

---

## Mapa de fases

| Fase | Pasta | Função | Doc |
|:---:|:---|:---|:---|
| **1** | `1_analisador_de_midia/` | Audita mídia: codecs, faixas, sincronia | [Fase 1](modulo-fase-1.md) |
| **2** | `2_extrator_legenda/` | Extrai legenda original (ASS/SRT/PGS) do `.mkv` | [Fase 2](modulo-fase-2.md) |
| **3** | `3-conversor_str_ass/` | Converte `*_PTBR.srt` → `*_PTBR.ass` com sync de FPS | [Fase 3](modulo-fase-3.md) |
| **4** | `4_tradutor_ia_gemma4/` | Tradução via LM Studio + Gemma (5 variantes) | [Fase 4](modulo-fase-4.md) |
| **5** | `5_juntar_legendas_filmes/` | Remux: junta vídeo + legenda PT-BR | [Fase 5](modulo-fase-5.md) |
| **6** | `6_sincronizacao_legenda/` | Auxiliar: audita/corrige dessincronia | [Fase 6](modulo-fase-6.md) |
| **7** | `7_decodificador/` | Auxiliar: recomprime vídeo (HEVC/NVENC) | [Fase 7](modulo-fase-7.md) |
| **8** | `8_cura_legendas/` | Auxiliar: repara corrupção de tags PT-BR | [Fase 8](modulo-fase-8.md) |
| **9** | `9_reparo_de_traducao/` | 🩹 Reparo: retraduz linhas `[ERRO_TRADUCAO: ...]` via IA (batch=1) | [Fase 9](modulo-fase-9.md) |
| **10** | `10_correcao_guilty_crown/` | 🎵 Correção offline de `[ERRO_TRADUCAO:]` e cores/tags de músicas OP/ED | [Fase 10](modulo-fase-10.md) |

As fases **1, 6, 7 e 8** são **opcionais/auxiliares** e podem ser usadas em qualquer esteira, conforme necessário. As fases **2, 3, 4 e 5** formam o núcleo das esteiras abaixo. As fases **9 e 10** são **reparos pós-tradução**, aplicados sobre a saída da Fase 4 quando há marcadores `[ERRO_TRADUCAO:]` — a Fase 9 usa IA local (LM Studio), a Fase 10 é especializada para a série *Guilty Crown* e roda 100% offline.

---

## Visão geral — todas as esteiras

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

---

## Esteira A — Episódio MKV com ASS embutido (inglês)

Fluxo padrão para episódios de série com legenda `S_TEXT/ASS` em inglês embutida no `.mkv`.

```mermaid
flowchart LR
    MKV["episodios/*.mkv"] --> F1["Fase 1 - opcional\nmedia_analyzer.py"]
    F1 --> F4["Fase 4\nsub_extractor.py\n(extrai + traduz)"]
    F4 --> ASS["traducao/*_PTBR.ass"]
    MKV --> F5["Fase 5\nbatch_remuxer.py"]
    ASS --> F5
    F5 --> OUT["mkv_final_ptbr/*_PTBR.mkv"]

    style F4 fill:#4B0082,stroke:#00E5FF,color:#fff
    style F5 fill:#1e4620,stroke:#32CD32,color:#fff
```

```powershell
python ".\1_analisador_de_midia\media_analyzer.py"      # opcional
python ".\4_tradutor_ia_gemma4\sub_extractor.py"
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
```

---

## Esteira B — Filme com SRT externo (inglês)

Para filmes/releases cuja legenda em inglês vem **separada** em um `.srt`. Detalhes: [Pipeline SRT](pipeline-srt.md).

```mermaid
flowchart LR
    SRT["legenda/*.srt EN"] --> F4["Fase 4\ntradutor_srt_direto.py"]
    F4 --> SRTPT["legenda/*_PTBR.srt"]
    SRTPT --> F3["Fase 3\nconversor_srt_para_ass.py"]
    F3 --> ASS["traducao/*_PTBR.ass"]

    MKV["filme.mkv"] --> F5["Fase 5\nbatch_remuxer.py"]
    ASS --> F5
    F5 --> OUT["mkv_final_ptbr/*_PTBR.mkv"]

    style F4 fill:#4B0082,stroke:#00E5FF,color:#fff
    style F3 fill:#2d3748,stroke:#00E5FF,color:#fff
    style F5 fill:#1e4620,stroke:#32CD32,color:#fff
```

```powershell
python ".\4_tradutor_ia_gemma4\5_tradutor_de_legenda\tradutor_srt_direto.py"
python ".\3-conversor_str_ass\conversor_srt_para_ass.py"
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
```

---

## Esteira C — Legenda PGS (Blu-ray bitmap)

Para releases cuja única legenda embutida é **PGS** (`S_HDMV/PGS`, imagem). Requer **OCR externo** (não incluso no repositório).

```mermaid
flowchart LR
    MKV["filme.mkv (PGS)"] --> F2["Fase 2\nextrator_inteligente_pgs.py"]
    F2 --> SUP["extraidos_sup/*.sup"]
    SUP --> OCR["OCR externo\nSubtitle Edit + Tesseract"]
    OCR --> SRT["*_PTBR.srt"]
    SRT --> F3["Fase 3\nconversor_srt_para_ass.py"]
    F3 --> ASS["traducao/*_PTBR.ass"]

    MKV --> F5["Fase 5\nbatch_remuxer.py"]
    ASS --> F5
    F5 --> OUT["mkv_final_ptbr/*_PTBR.mkv"]

    style F2 fill:#2d3748,stroke:#00E5FF,color:#fff
    style OCR fill:#5c1010,stroke:#ff4444,color:#fff
    style F3 fill:#2d3748,stroke:#00E5FF,color:#fff
    style F5 fill:#1e4620,stroke:#32CD32,color:#fff
```

```powershell
python ".\2_extrator_legenda\extrator_inteligente_pgs.py"
# OCR externo (Subtitle Edit + Tesseract) -> *_PTBR.srt
python ".\3-conversor_str_ass\conversor_srt_para_ass.py"
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
```

> O OCR `.sup → .srt` **não faz parte** deste repositório. A legenda traduzida deve ser gerada externamente antes da Fase 3.

---

## Esteira D — Tradução francês → PT-BR (multi-thread)

Mesmo formato da Esteira A, mas para legendas **ASS embutidas em francês**, com glossário e cache dedicados.

```mermaid
flowchart LR
    MKV["episodios/*.mkv (FR)"] --> F1["Fase 1 - opcional"]
    F1 --> F4["Fase 4\nscript_tradutor_fr.py\n(extrai + traduz, 2 threads)"]
    F4 --> ASS["traducao/*_PTBR.ass"]
    MKV --> F5["Fase 5\nbatch_remuxer.py"]
    ASS --> F5
    F5 --> OUT["mkv_final_ptbr/*_PTBR.mkv"]

    style F4 fill:#4B0082,stroke:#00E5FF,color:#fff
    style F5 fill:#1e4620,stroke:#32CD32,color:#fff
```

```powershell
python ".\4_tradutor_ia_gemma4\script_tradutor_fr.py"
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
```

---

## Esteira E — Lote ASS pré-extraído (Gundam Reconguista)

Para quando a legenda já foi extraída (Fase 2) e a tradução é feita em **lote agrupado** (menos chamadas HTTP).

```mermaid
flowchart LR
    MKV["episodios/*.mkv"] --> F2["Fase 2\nextrator_inteligente_ass.py"]
    F2 --> ENG["legendas_eng/*_ENG.ass"]
    ENG --> F4["Fase 4\nbatch_translator_ass.py"]
    F4 --> PT["*_PTBR.ass"]
    MKV --> F5["Fase 5\nbatch_remuxer.py"]
    PT --> F5
    F5 --> OUT["mkv_final_ptbr/*_PTBR.mkv"]

    style F2 fill:#2d3748,stroke:#00E5FF,color:#fff
    style F4 fill:#4B0082,stroke:#00E5FF,color:#fff
    style F5 fill:#1e4620,stroke:#32CD32,color:#fff
```

```powershell
python ".\2_extrator_legenda\extrator_inteligente_ass.py"
python ".\4_tradutor_ia_gemma4\tradutor_ass\batch_translator_ass.py"
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
```

---

## Esteira F — Gundam Unicorn (especializada)

Igual à Esteira E, com glossário Universal Century e etapa de **cura de legendas** para corrigir corrupção de tags conhecida.

```mermaid
flowchart LR
    MKV["episodios/*.mkv"] --> F2["Fase 2\nextrator_inteligente_ass.py"]
    F2 --> ENG["*_ENG.ass"]
    ENG --> F4["Fase 4\nbatch_translator_unicorn.py"]
    F4 --> PT["*_PTBR.ass"]
    PT -.->|se TAG corrompido| F8["Fase 8\ncura_legendas_tag.py /\ncura_gundam_mkv.py"]
    F8 --> PTC["traducao_curada/*_PTBR.ass"]
    PT --> F5["Fase 5\nbatch_remuxer.py"]
    PTC --> F5
    MKV --> F5
    F5 --> OUT["mkv_final_ptbr/*_PTBR.mkv"]

    style F2 fill:#2d3748,stroke:#00E5FF,color:#fff
    style F4 fill:#4B0082,stroke:#00E5FF,color:#fff
    style F8 fill:#5c1010,stroke:#ff4444,color:#fff
    style F5 fill:#1e4620,stroke:#32CD32,color:#fff
```

```powershell
python ".\2_extrator_legenda\extrator_inteligente_ass.py"
python ".\4_tradutor_ia_gemma4\tradutor_gundam_unicornio\batch_translator_unicorn.py"
python ".\8_cura_legendas\cura_legendas_tag.py"          # se necessario
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
```

---

## Esteira G — Guilty Crown (correção de nomes e cores de músicas)

<p>
  <img src="https://img.shields.io/badge/100%25-Offline-success?style=flat-square" alt="Offline"/>
  <img src="https://img.shields.io/badge/Especializado-Guilty_Crown-9146FF?style=flat-square" alt="Guilty Crown"/>
</p>

Igual à Esteira E, mas a saída da Fase 4 fica com marcadores `[ERRO_TRADUCAO: ...]` (nomes próprios) e cores de OP/ED ilegíveis. A **[Fase 10](modulo-fase-10.md)** corrige os dois problemas **sem precisar do LM Studio**.

```mermaid
flowchart LR
    MKV["episodios/*.mkv\n(Guilty Crown)"] --> F2["Fase 2\nextrator_inteligente_ass.py"]
    F2 --> ENG["legendas_eng/*_ENG.ass"]
    ENG --> F4["Fase 4\nbatch_translator_ass.py\n(ou variante)"]
    F4 --> PTERR["legendas_eng/*_ENG.ass\ncom [ERRO_TRADUCAO:...]"]
    PTERR --> F10A["Fase 10a\ncorrigir_guilty_crown.py"]
    F10A --> PT["legendas_ptbr/*_PTBR.ass"]
    PT --> F10B["Fase 10b\ncorrigir_cores_musicas.py"]
    F10B --> PTOK["legendas_ptbr/*_PTBR.ass\ncores OP/ED corrigidas"]
    MKV --> F5["Fase 5\nbatch_remuxer.py"]
    PTOK --> F5
    F5 --> OUT["mkv_final_ptbr/*_PTBR.mkv"]

    style F2 fill:#2d3748,stroke:#00E5FF,color:#fff
    style F4 fill:#4B0082,stroke:#00E5FF,color:#fff
    style F10A fill:#5c1010,stroke:#ff4444,color:#fff
    style F10B fill:#5c1010,stroke:#ff4444,color:#fff
    style F5 fill:#1e4620,stroke:#32CD32,color:#fff
    style OUT fill:#1e4620,stroke:#32CD32,color:#fff
```

```powershell
python ".\2_extrator_legenda\extrator_inteligente_ass.py"
python ".\4_tradutor_ia_gemma4\tradutor_ass\batch_translator_ass.py"   # ou variante adequada
python ".\10_correcao_guilty_crown\corrigir_guilty_crown.py"           # remove [ERRO_TRADUCAO:]
python ".\10_correcao_guilty_crown\corrigir_cores_musicas.py"          # cores/tags OP-ED
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
```

> Se preferir retraduzir as falhas via IA em vez de manter o texto em inglês, use a **[Fase 9](modulo-fase-9.md)** (`repara_erros_traducao.py`, requer LM Studio) antes da Fase 10.

---

## Camadas de dependência (todas as fases)

```mermaid
flowchart TB
    subgraph DEP["Dependencias externas"]
        MKVT["MKVToolNix\nFases 2, 4, 5, 8"]
        LM["LM Studio :1234\nFases 4 e 9"]
        MI["MediaInfo\nFase 1"]
        FF["FFmpeg/FFprobe\nFases 6 e 7"]
        OCRX["Subtitle Edit + Tesseract\nEsteira C (externo)"]
    end

    subgraph PY["Scripts Python"]
        S1["media_analyzer.py"]
        S2["extrator_inteligente_*.py"]
        S3["conversor_srt_para_ass.py"]
        S4["sub_extractor.py / script_tradutor_fr.py /\nbatch_translator_*.py / tradutor_srt_direto.py"]
        S5["batch_remuxer.py"]
        S6["subtitle_fixer/stretcher/auditor"]
        S7["gpu_video_optimizer.py"]
        S8["cura_*.py"]
        S9["repara_erros_traducao.py /\nlimpa_erros_residuais.py"]
        S10["corrigir_guilty_crown.py /\ncorrigir_cores_musicas.py"]
    end

    MI --> S1
    MKVT --> S2
    MKVT --> S4
    MKVT --> S5
    MKVT --> S8
    LM --> S4
    LM --> S9
    FF --> S6
    FF --> S7
    OCRX -.-> S3
    S4 -.->|ERRO_TRADUCAO| S9
    S4 -.->|ERRO_TRADUCAO, Guilty Crown| S10

    style DEP fill:#1a1a2e,stroke:#666,color:#fff
    style PY fill:#2b2b2b,stroke:#00E5FF,color:#fff
```

---

## Binários externos (Windows)

| Executável | Fases | Caminho padrão |
|:---|:---|:---|
| `mkvmerge.exe` | 2, 4, 5, 8 | `C:\Program Files\MKVToolNix\` |
| `mkvextract.exe` | 2, 4, 8 | `C:\Program Files\MKVToolNix\` |
| `ffmpeg.exe` / `ffprobe.exe` | 6, 7 | PATH do sistema |

[Fase 3](modulo-fase-3.md) **não** usa MKVToolNix nem FFmpeg — conversão pura Python. As **[Fase 9](modulo-fase-9.md)** e **[Fase 10](modulo-fase-10.md)** também não dependem de nenhum binário externo (apenas leitura/escrita de `.ass`).

---

## Servidor de IA

| Componente | Fase | Observação |
|:---|:---|:---|
| **[LM Studio](https://lmstudio.ai/)** porta **1234** | 4, 9 | Servidor OpenAI-compatível local |
| **Gemma 4B** (`google/gemma-4-e4b`) | 4, 9 | Modelo carregado no LM Studio |

As **Fases 3, 6, 7, 8 e 10** **não** usam IA — apenas a **Fase 4** (tradução em lote) e a **Fase 9** (reparo avulso) dependem do LM Studio.

Instalação: [instalacao.md](instalacao.md)

---

[← Índice da documentação](README.md)
