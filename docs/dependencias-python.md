# 🐍 Dependências Python (`requirements.txt`)

[← Índice](README.md) · [Arquivo `requirements.txt`](../requirements.txt)

<p>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/Fases-00_a_12-blueviolet?style=flat-square" alt="Fases 00-12"/>
</p>

Versões fixadas para reprodutibilidade no Windows.

---

## Pacotes usados diretamente

| Pacote | Versão | Usado em | Fase | Função |
|:---|:---:|:---|:---:|:---|
| **`colorama`** | 0.4.6 | Praticamente todos os scripts | 00–12 | Cores ANSI no terminal |
| **`tqdm`** | 4.68.3 | Praticamente todos os scripts | 01–05c-2, 07, 10, 11 | Barras de progresso |
| **`requests`** | 2.34.2 | Scripts de tradução (`05a_tradutor_llm_gemma4/`, `05b_tradutor_llm_mistral_nemo/`, `05c_tradutor_llm_qwen2/`, `05c_tradutor_llm_translategemma/`) + reparos via IA | 05a, 05b, 05c, 05c-2, 07 | HTTP para LM Studio |
| **`pymediainfo`** | 7.0.1 | `media_analyzer.py` | 01 | Metadados via DLL MediaInfo |

> **MediaInfo (SO):** necessário além do pacote pip. [Download MediaInfo](https://mediaarea.net/en/MediaInfo/Download).
> **Fases 08 e 03** dependem de **FFmpeg/FFprobe** (binário externo, não é pacote pip) e de `tkinter` (incluso no Python padrão do Windows).

---

## Pacotes transitivos

| Pacote | Versão | Puxado por | Função |
|:---|:---:|:---|:---|
| `urllib3` | 2.7.0 | `requests` | Pool HTTP |
| `certifi` | 2026.6.17 | `requests` | Certificados SSL |
| `charset-normalizer` | 3.4.7 | `requests` | Encoding HTTP |
| `idna` | 3.18 | `requests` | Domínios IDN |
| `httpx` | 0.28.1 | `ollama` | Cliente async |
| `httpcore` | 1.0.9 | `httpx` | Camada baixa |
| `h11` | 0.16.0 | `httpcore` | HTTP/1.1 |
| `anyio` | 4.14.0 | `httpx` | I/O async |
| `pydantic` | 2.13.4 | `ollama` | Validação |
| `pydantic_core` | 2.46.4 | `pydantic` | Núcleo |
| `annotated-types` | 0.7.0 | `pydantic` | Tipos |
| `typing_extensions` | 4.15.0 | `pydantic` | Backport |
| `typing-inspection` | 0.4.2 | `pydantic` | Inspeção runtime |

---

## `ollama` — sem uso no pipeline atual

| Pacote | Versão | Observação |
|:---|:---:|:---|
| **`ollama`** | 0.6.2 | Listado no `requirements.txt`, mas **nenhum script importa `ollama`**. As Fases 05a/05b/05c/05c-2 usam **LM Studio + `requests`**. Mantido deliberadamente na cadeia de dependências (decisão do usuário em 2026-06-20). |

---

## Mapa por fase

```mermaid
flowchart LR
    subgraph F01["Fase 01"]
        MI["pymediainfo"]
        C01["colorama"]
        T01["tqdm"]
    end

    subgraph F02["Fase 02"]
        C02["colorama"]
        T02["tqdm"]
        MKVT02["MKVToolNix"]
    end

    subgraph F04["Fase 04"]
        C04["colorama"]
        T04["tqdm"]
    end

    subgraph F05A["Fase 05a"]
        REQ05A["requests"]
        C05A["colorama"]
        T05A["tqdm"]
        MKVT05A["MKVToolNix"]
    end

    subgraph F05B["Fase 05b"]
        REQ05B["requests"]
        C05B["colorama"]
        T05B["tqdm"]
        MKVT05B["MKVToolNix"]
    end

    subgraph F05C["Fase 05c"]
        REQ05C["requests"]
        C05C["colorama"]
        T05C["tqdm"]
    end

    subgraph F05C2["Fase 05c-2"]
        REQ05C2["requests"]
        C05C2["colorama"]
        T05C2["tqdm"]
    end

    subgraph F06["Fase 06"]
        C06["colorama"]
        MKVT06["MKVToolNix"]
    end

    subgraph F07["Fase 07"]
        REQ07["requests"]
        C07["colorama"]
        T07["tqdm"]
    end

    subgraph F08["Fase 08"]
        FF08["FFprobe"]
        TK08["tkinter"]
        C08["colorama"]
    end

    subgraph F03["Fase 03"]
        FF03["FFmpeg NVENC"]
        C03["colorama"]
        T03["tqdm"]
    end

    subgraph F10["Fase 10"]
        C10["colorama"]
        MKVT10["MKVToolNix opcional"]
    end

    subgraph F11["Fase 11"]
        C11["colorama"]
        T11["tqdm"]
    end

    subgraph F12["Fase 12"]
        C12["colorama"]
        MKVT12["MKVToolNix"]
    end
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
