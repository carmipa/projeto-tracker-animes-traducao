# 📐 Módulo — Fase 1 (Tradutor)

[← Índice](README.md) · [`2_tradutor_ia_gemma4/sub_extractor.py`](../2_tradutor_ia_gemma4/sub_extractor.py)

---

## Recursos

| Recurso | Detalhe |
|:---|:---|
| **Autodetecção de track** | `mkvmerge -J` → faixa `subtitles` com `S_TEXT/ASS` |
| **Encoding resiliente** | `utf-8` → `utf-8-sig` → `cp1252` → `latin-1` → `iso-8859-1` → bypass |
| **Regex industrial** | `^(Dialogue:\s*[^,]*(?:,[^,]*){8},)(.*)$` |
| **Filtro de bloat** | Linhas &gt; 2000 caracteres (fontes Base64) |
| **Tradução em lote** | 20 diálogos por requisição HTTP |
| **Cache em memória** | Evita retraduzir lotes idênticos |
| **Saída** | `{pasta}/traducao/{nome}_PTBR.ass` |

---

## Diagrama de fluxo

```mermaid
flowchart TB
    START([main]) --> LOG[GerenciadorLogs<br/>4 arquivos de auditoria]
    LOG --> VAL[validar<br/>LM Studio + MKVToolNix]

    VAL -->|Falha| ABORT([Aborta])
    VAL -->|OK| PASTA[input pasta dos .mkv]
    PASTA --> LISTA[Lista mkv ordenados]
    LISTA --> LOOP{Para cada episodio}

    LOOP --> TRACK[mkvmerge -J<br/>descobrir track ASS]
    TRACK -->|Sem ASS| SKIP[Pula episodio]
    TRACK -->|OK| EXT[mkvextract tracks<br/>_extracted.ass]

    EXT --> READ[ler_arquivo_com_encoding]
    READ --> REGEX[Regex Dialogue<br/>filtro Base64]

    REGEX --> LOTE[Lotes de 20 linhas]
    LOTE --> API[POST /v1/chat/completions]
    API --> REBUILD[Reconstroi linhas ASS]
    REBUILD --> SAVE[traducao/nome_PTBR.ass]
    SAVE --> CLEAN[Remove _extracted.ass]
    CLEAN --> MORE{Mais episodios?}
    MORE -->|Sim| LOOP
    MORE -->|Nao| STATS[stats.json + relatorio final]
    STATS --> END([Fim])

    SKIP --> MORE

    style API fill:#4B0082,stroke:#00E5FF,color:#fff
    style SAVE fill:#1a1a2e,stroke:#00E5FF,color:#fff
    style ABORT fill:#5c1010,stroke:#ff4444,color:#fff
```

---

## Sequência (API local)

```mermaid
sequenceDiagram
    participant U as Usuario
    participant P as sub_extractor.py
    participant M as MKVToolNix
    participant L as LM Studio :1234

    U->>P: Informa pasta dos .mkv
    P->>L: GET /v1/models
    L-->>P: Modelo Gemma carregado
    loop Cada episodio .mkv
        P->>M: mkvmerge -J identifica track
        P->>M: mkvextract extrai .ass
        P->>P: Regex + filtros de encoding
        loop Lotes de 20 dialogos
            P->>L: POST /v1/chat/completions
            L-->>P: Texto PT-BR indexado
        end
        P->>P: Salva traducao/nome_PTBR.ass
    end
    P-->>U: Logs em 2_tradutor_ia_gemma4/logs/
```

---

## Entradas e saídas

| Entrada | Saída | Dependências |
|:---|:---|:---|
| Pasta com `.mkv` | `traducao/*_PTBR.ass` | MKVToolNix, LM Studio, `requests`, `colorama`, `tqdm` |

Logs: [Logs e auditoria](logs-e-auditoria.md)

---

[← Fase 0](modulo-fase-0.md) · [Próximo: Fase 2 →](modulo-fase-2.md)
