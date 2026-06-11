# 🏗️ Arquitetura do Pipeline

[← Índice da documentação](README.md) · [README principal](../README.md)

O projeto oferece **duas esteiras** independentes que convergem na **Fase 2 (remux)**:

| Esteira | Fases | Entrada típica |
|:---|:---|:---|
| **MKV (episódios)** | 0 → 1 → 2 | `.mkv` com legenda ASS embutida |
| **SRT (legendas externas)** | 5 → 6 → 2 | `.srt` separado + `.mkv` do filme |

> Detalhes da esteira SRT: [Pipeline SRT](pipeline-srt.md)

---

## Esteira MKV — visão macro

```mermaid
flowchart LR
    MKV["Pasta episodios .mkv"]

    MKV --> P0["1_analisador_de_midia"]
    P0 -.->|opcional| P1
    MKV --> P1["4_tradutor_ia_gemma4"]

    P0 --> R0["relatorio/*.txt"]
    P1 --> R1["traducao/*_PTBR.ass"]

    MKV --> P2["5_juntar_legendas_filmes"]
    R1 --> P2
    P2 --> R2["mkv_final_ptbr/*_PTBR.mkv"]

    style P0 fill:#2d3748,stroke:#00E5FF,color:#fff
    style P1 fill:#4B0082,stroke:#00E5FF,color:#fff
    style P2 fill:#1e4620,stroke:#32CD32,color:#fff
```

Diagramas por módulo: [Fase 0](modulo-fase-0.md) · [Fase 1](modulo-fase-1.md) · [Fase 2](modulo-fase-2.md)

---

## Esteira SRT — visão macro

```mermaid
flowchart LR
    SRT["legenda/*.srt EN"] --> P5["5_tradutor_de_legenda"]
    P5 --> SRTPT["*_PTBR.srt"]
    SRTPT --> P6["3-conversor_str_ass"]
    P6 --> ASS["traducao/*_PTBR.ass"]

    MKV["filme.mkv"] --> P2["5_juntar_legendas_filmes"]
    ASS --> P2
    P2 --> OUT["mkv_final_ptbr/*_PTBR.mkv"]

    style P5 fill:#4B0082,stroke:#00E5FF,color:#fff
    style P6 fill:#6b21a8,stroke:#00E5FF,color:#fff
    style P2 fill:#1e4620,stroke:#32CD32,color:#fff
```

Diagramas: [Fase 5](modulo-fase-5.md) · [Fase 6](modulo-fase-6.md)

---

## Camadas de dependência (todas as fases)

```mermaid
flowchart TB
    subgraph DEP["Dependencias externas"]
        MKVT["MKVToolNix<br/>Fases 1 e 2"]
        LM["LM Studio :1234<br/>Fases 1 e 5"]
        MI["MediaInfo<br/>Fase 0"]
    end

    subgraph PY["Scripts Python"]
        S0["media_analyzer.py"]
        S1["sub_extractor.py"]
        S2["batch_remuxer.py"]
        S5["tradutor_srt_direto.py"]
        S6["conversor_srt_para_ass.py"]
    end

    MI --> S0
    MKVT --> S1
    MKVT --> S2
    LM --> S1
    LM --> S5
    S5 --> S6
    S6 --> S2

    style DEP fill:#1a1a2e,stroke:#666,color:#fff
    style PY fill:#2b2b2b,stroke:#00E5FF,color:#fff
```

---

## Binários externos (Windows)

| Executável | Fases | Caminho padrão |
|:---|:---|:---|
| `mkvmerge.exe` | 1, 2 | `C:\Program Files\MKVToolNix\` |
| `mkvextract.exe` | 1 | `C:\Program Files\MKVToolNix\` |

[Fases 5 e 6](pipeline-srt.md) **não** usam MKVToolNix.

---

## Servidor de IA

| Componente | Fases |
|:---|:---|
| **[LM Studio](https://lmstudio.ai/)** porta **1234** | 1, 5 |
| **Gemma 4B** | Tradução ASS (Fase 1) e SRT (Fase 5) |

A **Fase 6** é conversão estrutural + sync FPS — sem IA.

Instalação: [instalacao.md](instalacao.md)

---

[← Índice da documentação](README.md)
