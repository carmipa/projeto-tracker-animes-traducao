# 📐 Módulo — Fase 5 (Tradutor SRT direto)

[← Índice](README.md) · [`5_tradutor_de_legenda/tradutor_srt_direto.py`](../5_tradutor_de_legenda/tradutor_srt_direto.py)

**Esteira alternativa** para legendas **SRT externas** (não embutidas no `.mkv`). Ideal para filmes, releases com legenda separada ou quando a Fase 1 não se aplica.

---

## Função

| Entrada | Processamento | Saída |
|:---|:---|:---|
| Arquivo ou pasta com `.srt` em inglês | Tradução em lote via **LM Studio** (Gemma 4B) | `*_PTBR.srt` na mesma pasta |

**Não usa MKVToolNix** — apenas leitura de texto, HTTP local e gravação UTF-8.

---

## Recursos

| Recurso | Detalhe |
|:---|:---|
| **Auto-detecção** | 1 `.srt` na pasta → seleciona automaticamente; vários → menu numérico |
| **Encoding resiliente** | `utf-8` → `utf-8-sig` → `cp1252` → `latin-1` → `iso-8859-1` |
| **Lotes configuráveis** | Padrão 20 blocos SRT por requisição (ENTER mantém; ou digite outro valor) |
| **Prompt especializado** | Termos Macross (Fold, Valkyrie, etc.) + letras com `♪` |
| **Nome de saída** | Substitui sufixos `-en`, `english` por `_PTBR.srt` |
| **Logs** | `5_tradutor_de_legenda/logs/pipeline_direct_srt_*.txt` |

---

## Diagrama de fluxo

```mermaid
flowchart TB
    START([main]) --> INPUT[Pasta ou arquivo .srt]
    INPUT --> LOG[configurar_logs]
    LOG --> VAL[validar_lm_studio :1234]

    VAL -->|Falha| ABORT([sys.exit 1])
    VAL -->|OK| BATCH[obter_batch_size padrao 20]

    BATCH --> READ[ler_srt_com_encoding]
    READ --> SPLIT[split blocos SRT por linha dupla]
    SPLIT --> LOOP[Lotes com tqdm]

    LOOP --> API[POST /v1/chat/completions<br/>temperature 0.3]
    API -->|Erro| ABORT
    API -->|OK| LOOP

    LOOP --> SAVE[Grava _PTBR.srt UTF-8]
    SAVE --> REL[Relatorio no log]
    REL --> END([Fim])

    style API fill:#4B0082,stroke:#00E5FF,color:#fff
    style SAVE fill:#1a1a2e,stroke:#00E5FF,color:#fff
    style ABORT fill:#5c1010,stroke:#ff4444,color:#fff
```

---

## Sequência (API)

```mermaid
sequenceDiagram
    participant U as Usuario
    participant T as tradutor_srt_direto.py
    participant L as LM Studio :1234

    U->>T: Caminho pasta ou .srt
    T->>L: GET /v1/models
    L-->>T: Modelo ativo
    U->>T: Tamanho do lote opcional
  loop Cada lote de blocos SRT
        T->>L: POST /v1/chat/completions
        L-->>T: Blocos traduzidos PT-BR
    end
    T->>T: Salva nome_PTBR.srt
    T-->>U: Log em 5_tradutor_de_legenda/logs/
```

---

## Comando

```powershell
python .\5_tradutor_de_legenda\tradutor_srt_direto.py
```

| Prompt interativo | Exemplo |
|:---|:---|
| Caminho da pasta ou arquivo | `C:\TRACKER-ANIMES\animes\md-2\legenda` |
| Tamanho do lote | ENTER = 20 |

---

## Próximo passo

Após gerar o `*_PTBR.srt`, use a **[Fase 6](modulo-fase-6.md)** para converter em ASS com correção de FPS, e depois a **[Fase 2](modulo-fase-2.md)** para remuxar no `.mkv`.

---

[← Pipeline SRT](pipeline-srt.md) · [Fase 6 →](modulo-fase-6.md)
