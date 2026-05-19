# 🐍 Dependências Python (`requirements.txt`)

[← Índice](README.md) · [Arquivo `requirements.txt`](../requirements.txt)

Versões fixadas para reprodutibilidade no Windows.

---

## Pacotes usados diretamente

| Pacote | Versão | Usado em | Fase | Função |
|:---|:---:|:---|:---:|:---|
| **`colorama`** | 0.4.6 | Scripts `1_`–`3_`, `5_`, `6_` | 0–2, 5, 6 | Cores ANSI no terminal |
| **`tqdm`** | 4.67.3 | Scripts `1_`–`3_`, `5_`, `6_` | 0–2, 5, 6 | Barras de progresso |
| **`requests`** | 2.34.2 | `sub_extractor.py`, `tradutor_srt_direto.py` | 1, 5 | HTTP para LM Studio |
| **`pymediainfo`** | 7.0.1 | `media_analyzer.py` | 0 | Metadados via DLL MediaInfo |

> **MediaInfo (SO):** necessário além do pacote pip. [Download MediaInfo](https://mediaarea.net/en/MediaInfo/Download).

---

## Pacotes transitivos

| Pacote | Versão | Puxado por | Função |
|:---|:---:|:---|:---|
| `urllib3` | 2.7.0 | `requests` | Pool HTTP |
| `certifi` | 2026.4.22 | `requests` | Certificados SSL |
| `charset-normalizer` | 3.4.7 | `requests` | Encoding HTTP |
| `idna` | 3.15 | `requests` | Domínios IDN |
| `httpx` | 0.28.1 | `ollama` | Cliente async |
| `httpcore` | 1.0.9 | `httpx` | Camada baixa |
| `h11` | 0.16.0 | `httpcore` | HTTP/1.1 |
| `anyio` | 4.13.0 | `httpx` | I/O async |
| `pydantic` | 2.13.4 | `ollama` | Validação |
| `pydantic_core` | 2.46.4 | `pydantic` | Núcleo |
| `annotated-types` | 0.7.0 | `pydantic` | Tipos |
| `typing_extensions` | 4.15.0 | `pydantic` | Backport |
| `typing-inspection` | 0.4.2 | `pydantic` | Inspeção runtime |

---

## `ollama` — sem uso no pipeline atual

| Pacote | Versão | Observação |
|:---|:---:|:---|
| **`ollama`** | 0.6.2 | Listado no `requirements.txt`, mas **nenhum script importa `ollama`**. Fases 1 e 5 usam **LM Studio + `requests`**. |

---

## Mapa por fase

```mermaid
flowchart LR
    subgraph F0["Fase 0"]
        MI[pymediainfo]
        C0[colorama]
        T0[tqdm]
    end

    subgraph F1["Fase 1"]
        REQ[requests]
        C1[colorama]
        T1[tqdm]
    end

    subgraph F2["Fase 2"]
        C2[colorama]
        T2[tqdm]
    end

    subgraph F5["Fase 5"]
        REQ5[requests]
        C5[colorama]
        T5[tqdm]
    end

    subgraph F6["Fase 6"]
        C6[colorama]
        T6[tqdm]
    end

    MI --> F0
    REQ --> F1
    REQ5 --> F5
    C0 --> F0
    T0 --> F0
    C1 --> F1
    T1 --> F1
    C2 --> F2
    T2 --> F2
    C5 --> F5
    T5 --> F5
    C6 --> F6
    T6 --> F6
```

---

## Comandos úteis

```powershell
pip list
pip show requests
pip install -r requirements.txt --force-reinstall
```

---

[← Instalação](instalacao.md) · [Índice](README.md)
