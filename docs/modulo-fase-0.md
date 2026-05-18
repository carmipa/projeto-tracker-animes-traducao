# 📐 Módulo — Fase 0 (Analisador)

[← Índice](README.md) · [`1_analisador_de_midia/media_analyzer.py`](../1_analisador_de_midia/media_analyzer.py)

**Opcional**, mas recomendado antes da tradução.

---

## Função

Varredura recursiva de `.mkv`, `.mp4`, `.avi`, etc. Gera relatório por arquivo em `relatorio/` com:

- Container, duração, bitrate geral  
- Fluxos de vídeo (codec, resolução, FPS)  
- Fluxos de áudio (idioma, canais)  
- **Legendas:** distingue `ASS/SSA`, `SRT` e **`PGS` (bitmap — não extraível)**

> Confirme legenda **texto** (`S_TEXT/ASS`) antes de iniciar a Fase 1.

---

## Diagrama de fluxo

```mermaid
flowchart TB
    START([main]) --> ARG{Caminho via<br/>argumento?}

    ARG -->|Sim| PATH[Normaliza caminho]
    ARG -->|Nao| INPUT[input interativo]

    PATH --> TIPO{Tipo do caminho}
    INPUT --> TIPO

    TIPO -->|Pasta| WALK[os.walk recursivo<br/>filtra extensoes de video]
    TIPO -->|Arquivo| FILA[Lista com 1 arquivo]

    WALK --> FILA
    FILA --> LOOP{Para cada video}

    LOOP --> VAL[Valida existencia<br/>permissao e tamanho]
    VAL --> PARSE[MediaInfo.parse<br/>barra tqdm]

    PARSE --> CLASS[Classifica faixas<br/>General Video Audio Text]
    CLASS --> LEG{Codec da legenda}

    LEG -->|S_TEXT/ASS ou SSA| OK[Compativel com Fase 1]
    LEG -->|SRT UTF8| SRT[Texto simples]
    LEG -->|PGS ou In_Screen| BLOCK[NAO extraivel<br/>pare o pipeline]

    CLASS --> REL[Monta relatorio texto]
    REL --> SAVE[Salva relatorio/nome_timestamp.txt]
    SAVE --> NEXT{Mais arquivos?}
    NEXT -->|Sim| LOOP
    NEXT -->|Nao| END([Fim])

    style OK fill:#1e4620,stroke:#32CD32,color:#fff
    style BLOCK fill:#5c1010,stroke:#ff4444,color:#fff
    style PARSE fill:#2d3748,stroke:#00E5FF,color:#fff
```

---

## Entradas e saídas

| Entrada | Saída | Dependências |
|:---|:---|:---|
| Pasta ou arquivo de vídeo | `relatorio/*.txt` | `pymediainfo`, `colorama`, `tqdm`, MediaInfo |

Comando: [Guia de execução — Fase 0](guia-de-execucao.md#fase-0--auditoria-opcional)

---

[Próximo: Fase 1 — Tradutor →](modulo-fase-1.md)
