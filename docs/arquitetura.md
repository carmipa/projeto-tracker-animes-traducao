# 🏗️ Arquitetura do Pipeline

[← Índice da documentação](README.md) · [README principal](../README.md)

Fluxo determinístico: **análise (opcional) → extração/tradução → multiplexação**.

> Diagramas detalhados por script: [Fase 0](modulo-fase-0.md) · [Fase 1](modulo-fase-1.md) · [Fase 2](modulo-fase-2.md)

---

## Visão macro

```mermaid
flowchart LR
    MKV["Pasta de episodios<br/>.mkv"]

    MKV --> P0["1_analisador_de_midia<br/>media_analyzer.py"]
    P0 -.->|opcional| P1
    MKV --> P1["2_tradutor_ia_gemma4<br/>sub_extractor.py"]

    P0 --> R0["relatorio/*.txt"]
    P1 --> R1["traducao/*_PTBR.ass"]

    MKV --> P2["3_juntar_legendas_filmes<br/>batch_remuxer.py"]
    R1 --> P2
    P2 --> R2["mkv_final_ptbr/*_PTBR.mkv"]

    style P0 fill:#2d3748,stroke:#00E5FF,color:#fff
    style P1 fill:#4B0082,stroke:#00E5FF,color:#fff
    style P2 fill:#1e4620,stroke:#32CD32,color:#fff
    style R2 fill:#006400,stroke:#32CD32,color:#fff
```

---

## Camadas de dependência

```mermaid
flowchart TB
    subgraph DEP["Camada de dependencias externas"]
        MKVT["MKVToolNix<br/>mkvmerge + mkvextract"]
        LM["LM Studio :1234<br/>Gemma 4B"]
        MI["MediaInfo DLL<br/>pymediainfo"]
    end

    subgraph PY["Camada Python - orquestracao"]
        S0["media_analyzer.py"]
        S1["sub_extractor.py"]
        S2["batch_remuxer.py"]
    end

    MI --> S0
    MKVT --> S1
    MKVT --> S2
    LM --> S1

    style DEP fill:#1a1a2e,stroke:#666,color:#fff
    style PY fill:#2b2b2b,stroke:#00E5FF,color:#fff
```

---

## Binários externos (Windows)

O Python **orquestra**; a manipulação de Matroska é feita pelos executáveis do MKVToolNix:

| Executável | Usado em | Caminho padrão |
|:---|:---|:---|
| `mkvmerge.exe` | Identificar tracks (`-J`) e remuxar | `C:\Program Files\MKVToolNix\` |
| `mkvextract.exe` | Extrair faixa de legenda `.ass` | `C:\Program Files\MKVToolNix\` |

> Instale o [MKVToolNix](https://mkvtoolnix.download/downloads.html). O código da Fase 1 também tenta `Program Files (x86)`.

---

## Servidor de IA

| Componente | Papel |
|:---|:---|
| **[LM Studio](https://lmstudio.ai/)** | Runtime on-premises: HTTP na porta **1234**, Prompt Cache, modelo na VRAM |
| **Gemma 4B** (`google/gemma-4-e4b`) | Modelo recomendado para ficção científica / mecha |

Antes da Fase 1: carregue o modelo → **Start Server** na porta `1234`.

Detalhes de instalação: [Instalação](instalacao.md).

---

[← Índice da documentação](README.md)
