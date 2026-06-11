# 📐 Módulo — Fase 4 (Tradução IA — LM Studio / Gemma)

[← Índice](README.md) · [`4_tradutor_ia_gemma4/`](../4_tradutor_ia_gemma4/)

Núcleo do projeto: traduz legendas para **PT-BR** usando um LLM local servido pelo **LM Studio** (`http://127.0.0.1:1234`). A pasta concentra **5 variantes**, cada uma especializada em um cenário (idioma de origem, formato, glossário de anime).

---

## Visão geral dos scripts

| # | Script | Entrada | Saída | Idioma origem | Glossário/série |
|:---:|:---|:---|:---|:---|:---|
| 1 | [`sub_extractor.py`](../4_tradutor_ia_gemma4/sub_extractor.py) | Pasta `.mkv` (extrai ASS) | `traducao/{nome}_PTBR.ass` | Inglês | Genérico |
| 2 | [`script_tradutor_fr.py`](../4_tradutor_ia_gemma4/script_tradutor_fr.py) | Pasta `.mkv` (extrai ASS) | `traducao/{nome}_PTBR.ass` | Francês | Macross Delta |
| 3 | [`tradutor_ass/batch_translator_ass.py`](../4_tradutor_ia_gemma4/tradutor_ass/batch_translator_ass.py) | `legendas_eng/*_ENG.ass` (Fase 2) | `{nome}_PTBR.ass` + `info_traducao_ass.txt` | Inglês | Gundam Reconguista |
| 4 | [`tradutor_gundam_unicornio/batch_translator_unicorn.py`](../4_tradutor_ia_gemma4/tradutor_gundam_unicornio/batch_translator_unicorn.py) | `*_ENG.ass` (Fase 2) | `{nome}_PTBR.ass` + `info.txt` | Inglês | Gundam Unicorn (UC) |
| 5 | [`5_tradutor_de_legenda/tradutor_srt_direto.py`](../4_tradutor_ia_gemma4/5_tradutor_de_legenda/tradutor_srt_direto.py) | `.srt` externo (arquivo/pasta) | `*_PTBR.srt` | Inglês | Macross |

Todos compartilham: validação `GET /v1/models` no LM Studio antes de iniciar, encoding resiliente (`utf-8` → `utf-8-sig` → `cp1252` → `latin-1` → `iso-8859-1`), `colorama` + `tqdm` para feedback, e tradução em **lotes** via `POST /v1/chat/completions`.

---

## 1 — `sub_extractor.py` (pipeline completo MKV → PT-BR ASS)

Pipeline "tudo em um": extrai a faixa ASS do `.mkv` via MKVToolNix **e** traduz, sem passar pela Fase 2.

| Recurso | Detalhe |
|:---|:---|
| Autodetecção de track | `mkvmerge -J` → faixa `subtitles` com `S_TEXT/ASS` |
| Regex industrial | `^(Dialogue:\s*[^,]*(?:,[^,]*){8},)(.*)$` |
| Filtro de bloat | Linhas > 2000 caracteres (fontes Base64) |
| Tradução em lote | 20 diálogos por requisição HTTP, `temperature=0.7`, `max_tokens=2000` |
| Cache em memória | Evita retraduzir lotes idênticos |
| Saída | `{pasta}/traducao/{nome}_PTBR.ass` |

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
    P-->>U: Logs em 4_tradutor_ia_gemma4/logs/
```

**Comando:**

```powershell
python ".\4_tradutor_ia_gemma4\sub_extractor.py"
```

---

## 2 — `script_tradutor_fr.py` (Francês → PT-BR, multi-thread)

Mesma base do `sub_extractor.py`, mas otimizado para legendas em **francês**, com cache persistente em disco e processamento paralelo.

| Recurso | Detalhe |
|:---|:---|
| Detecção de track | Prioriza faixa com `lang` = `fre`/`fra`/`fr` |
| Glossário | Termos de Macross Delta (ex.: *Chanteuse des Étoiles* → "Cantora das Estrelas", *Chevalier Aérien* → "Cavaleiro Aéreo") |
| Paralelismo | `ThreadPoolExecutor`, máx. 2 threads (RTX 5600 8GB, contexto 8000 tokens) |
| Lote | 8 diálogos por requisição, `temperature=0.1` (alta fidelidade) |
| Cache persistente | `traducao_cache_fr.json` — evita retraduzir entre execuções |
| Preservação de tags | Máscaras `[T0]`, `[T1]`... restauradas após tradução |
| Saída | `{pasta}/traducao/{nome}_PTBR.ass` |

```mermaid
flowchart TB
    START([main]) --> VAL[Valida LM Studio + MKVToolNix]
    VAL -->|Falha| ABORT([Aborta])
    VAL -->|OK| CACHE[Carrega traducao_cache_fr.json]
    CACHE --> PASTA[input pasta dos .mkv]
    PASTA --> LOOP{Para cada episodio}

    LOOP --> TRACK[mkvmerge -J<br/>track lang=fre/fra/fr]
    TRACK -->|Sem FR| SKIP[Pula episodio]
    TRACK -->|OK| EXT[mkvextract -> _extracted.ass]

    EXT --> READ[ler_arquivo_com_encoding]
    READ --> MASK[Mascara tags ASS -> T0..Tn]
    MASK --> LOTE[Lotes de 8 linhas]

    LOTE --> POOL[ThreadPoolExecutor<br/>max 2 threads]
    POOL --> API[POST /v1/chat/completions<br/>temperature 0.1]
    API --> CHK{Em cache?}
    CHK -->|Sim| HIT[Usa cache]
    CHK -->|Nao| CALL[Chama LM Studio]
    CALL --> SAVECACHE[Grava no cache]

    HIT --> UNMASK[Restaura tags T0..Tn]
    SAVECACHE --> UNMASK
    UNMASK --> REBUILD[Reconstroi linhas ASS]
    REBUILD --> SAVE[traducao/nome_PTBR.ass]
    SAVE --> MORE{Mais episodios?}
    MORE -->|Sim| LOOP
    MORE -->|Nao| STATS[stats_fr.json + relatorio]
    STATS --> END([Fim])

    SKIP --> MORE

    style API fill:#4B0082,stroke:#00E5FF,color:#fff
    style SAVE fill:#1a1a2e,stroke:#00E5FF,color:#fff
    style ABORT fill:#5c1010,stroke:#ff4444,color:#fff
    style POOL fill:#2d3748,stroke:#00E5FF,color:#fff
```

**Comando:**

```powershell
python ".\4_tradutor_ia_gemma4\script_tradutor_fr.py"
```

Logs: `pipeline_fr_*.txt`, `erros_fr_*.txt`, `config_fr_*.txt`, `stats_fr_*.json` em `4_tradutor_ia_gemma4/logs/`.

---

## 3 — `tradutor_ass/batch_translator_ass.py` (lote para ASS já extraído)

Traduz arquivos `*_ENG.ass` **já extraídos** (Fase 2), agrupando diálogos para reduzir drasticamente o número de chamadas HTTP (~400 → ~40 por episódio).

| Recurso | Detalhe |
|:---|:---|
| Entrada | `legendas_eng/*_ENG.ass` (pasta padrão configurável no script) |
| Paralelismo | `ThreadPoolExecutor`, máx. 2 threads (RTX 5600 8GB) |
| Lote | 8 diálogos por requisição |
| Glossário | Gundam Reconguista (Regild Century, Capital Territory, nomes de Mobile Suit mantidos em inglês) |
| Preservação de tags | Máscaras `[T0]`/`[T1]` + fallback por regex |
| Retry | 3 tentativas por lote, backoff `tentativa * 5s` |
| Fallback de parsing | Tenta formato numerado `1. tradução`, depois extração de linha crua |
| Saída | `{pasta_saida}/{nome}_PTBR.ass` + `info_traducao_ass.txt` |
| Debug | `debug_last_failure_ass.txt` (primeira falha de lote) |

```mermaid
flowchart TB
    START([main]) --> SEL[Seleciona pasta com *_ENG.ass]
    SEL --> LOOP{Para cada arquivo}

    LOOP --> READ[Le ASS + mascara tags T0..Tn]
    READ --> LOTE[Agrupa em lotes de 8]
    LOTE --> POOL[ThreadPoolExecutor max 2]

    POOL --> API[POST /v1/chat/completions]
    API -->|Erro| RETRY{Tentativa < 3?}
    RETRY -->|Sim| WAIT[Espera tentativa x 5s]
    WAIT --> API
    RETRY -->|Nao| DEBUG[debug_last_failure_ass.txt]

    API -->|OK| PARSE{Formato numerado?}
    PARSE -->|Sim| OK1[Extrai 1. traducao]
    PARSE -->|Nao| OK2[Extracao por linha crua]

    OK1 --> UNMASK[Restaura tags]
    OK2 --> UNMASK
    DEBUG --> UNMASK

    UNMASK --> SAVE[Grava nome_PTBR.ass]
    SAVE --> REL[Atualiza info_traducao_ass.txt]
    REL --> MORE{Mais arquivos?}
    MORE -->|Sim| LOOP
    MORE -->|Nao| END([Fim])

    style API fill:#4B0082,stroke:#00E5FF,color:#fff
    style SAVE fill:#1a1a2e,stroke:#00E5FF,color:#fff
    style DEBUG fill:#5c1010,stroke:#ff4444,color:#fff
```

**Comando:**

```powershell
python ".\4_tradutor_ia_gemma4\tradutor_ass\batch_translator_ass.py"
```

---

## 4 — `tradutor_gundam_unicornio/batch_translator_unicorn.py` (Gundam Unicorn)

Variante especializada para a série **Gundam Unicorn**, mesma arquitetura do item 3 com glossário próprio.

| Recurso | Detalhe |
|:---|:---|
| Entrada | `*_ENG.ass` (pasta padrão `anime/unicornio`, editável no script) |
| Paralelismo | `ThreadPoolExecutor`, máx. 2 threads (Ryzen 7 5800X3D + RX 7800 XT + 64GB RAM) |
| Lote | 8 diálogos por requisição |
| Glossário | Universal Century: *Psychoframe*, *Mobile Suit*, *Newtype*, *Zeon*, *Neo Zeon*, *Londo Bell*, *Vist Foundation*, *Anaheim Electronics* |
| Preservação de tags | Placeholder `___TAG___` restaurado após tradução |
| Fallback | Retradução linha a linha se a resposta vier incompleta |
| Saída | `{pasta_saida}/{nome}_PTBR.ass` + `info.txt` (estatísticas: diálogos, chamadas, fallbacks) |

> Fluxo idêntico ao diagrama do item 3 (lote → API → parse → restauração de tags), trocando apenas o glossário e os caminhos padrão.

**Comando:**

```powershell
python ".\4_tradutor_ia_gemma4\tradutor_gundam_unicornio\batch_translator_unicorn.py"
```

> Se a saída apresentar a string `TAG` corrompendo o texto traduzido, use a **[Fase 8 — Cura de Legendas](modulo-fase-8.md)** (`cura_gundam_mkv.py`) antes do remux.

---

## 5 — `tradutor_srt_direto.py` (SRT externo)

Tradução **direta SRT → SRT**, sem MKVToolNix — usada na **[Esteira B (Pipeline SRT)](pipeline-srt.md)** para filmes/legendas externas.

| Recurso | Detalhe |
|:---|:---|
| Entrada | Arquivo ou pasta com `.srt`; 1 arquivo → seleciona automático, vários → menu numérico |
| Lote | Padrão 20 blocos SRT por requisição (ENTER mantém; ou digite outro valor) |
| Prompt especializado | Termos Macross (Fold, Valkyrie, etc.) + letras de música com `♪` traduzidas poeticamente |
| Nome de saída | Substitui sufixos `-en`/`english` por `_PTBR.srt` |
| Logs | `4_tradutor_ia_gemma4/5_tradutor_de_legenda/logs/pipeline_direct_srt_*.txt` |

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
    T-->>U: Log em 4_tradutor_ia_gemma4/5_tradutor_de_legenda/logs/
```

**Comando:**

```powershell
python ".\4_tradutor_ia_gemma4\5_tradutor_de_legenda\tradutor_srt_direto.py"
```

| Prompt interativo | Exemplo |
|:---|:---|
| Caminho da pasta ou arquivo | `C:\TRACKER-ANIMES\animes\md-2\legenda` |
| Tamanho do lote | ENTER = 20 |

---

## Próximo passo

| Saída gerada | Próxima fase |
|:---|:---|
| `traducao/*_PTBR.ass` (itens 1–4) | [Fase 5 — Remuxer](modulo-fase-5.md) |
| `*_PTBR.srt` (item 5) | [Fase 3 — Conversor SRT → ASS](modulo-fase-3.md) → [Fase 5](modulo-fase-5.md) |

Logs detalhados: [Logs e auditoria](logs-e-auditoria.md)

---

[← Fase 2](modulo-fase-2.md) · [Próximo: Fase 5 →](modulo-fase-5.md) · [Pipeline SRT](pipeline-srt.md)
