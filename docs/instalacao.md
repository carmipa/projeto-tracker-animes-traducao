# ✅ Instalação e pré-requisitos

[← Índice](README.md) · [README principal](../README.md)

---

## Checklist rápido

| # | Tipo | Item | Obrigatório para |
|:---:|:---|:---|:---|
| 1 | **SO** | [MKVToolNix](https://mkvtoolnix.download/downloads.html) | Fases 1 e 2 *(esteira MKV e remux SRT)* |
| 2 | **SO** | [MediaInfo](https://mediaarea.net/en/MediaInfo/Download) | Fase 0 |
| 3 | **SO** | [LM Studio](https://lmstudio.ai/) + Gemma 4B na porta **1234** | Fases **1** e **5** |
| 4 | **Python** | 3.10+ | Todas |
| 5 | **pip** | [`requirements.txt`](../requirements.txt) | Todas |

| Esteira | Fases | MKVToolNix | LM Studio |
|:---|:---|:---:|:---:|
| Episódios MKV | 0 → 1 → 2 | ✅ | ✅ (Fase 1) |
| SRT externo | 5 → 6 → 2 | ✅ (só Fase 2) | ✅ (Fase 5) |

---

## MKVToolNix

```text
C:\Program Files\MKVToolNix\
├── mkvextract.exe    ← extração de legendas (Fase 1)
└── mkvmerge.exe      ← tracks e remux (Fases 1 e 2)
```

---

## Ambiente Python (venv)

```powershell
cd C:\TRACKER-ANIMES\projeto-tracker-animes-traducao
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Instalação mínima (pacotes diretos):

```powershell
pip install colorama tqdm requests pymediainfo
```

Referência completa dos pacotes: [Dependências Python](dependencias-python.md).

---

## LM Studio

1. Instale o [LM Studio](https://lmstudio.ai/).  
2. Carregue **`google/gemma-4-e4b`** (ou Gemma 4B equivalente).  
3. Inicie o servidor em **`http://127.0.0.1:1234`**.  
4. `sub_extractor.py` (Fase 1) e `tradutor_srt_direto.py` (Fase 5) validam `GET /v1/models` antes de processar.

---

## Pronto para rodar

| Objetivo | Guia |
|:---|:---|
| Episódios `.mkv` | [Guia de execução — Esteira A](guia-de-execucao.md#esteira-a--episódios-mkv-fases-0--1--2) |
| Filme / SRT externo | [Pipeline SRT](pipeline-srt.md) |

Requisitos mínimos: **venv** + **`requirements.txt`** + **LM Studio** (Fases 1 ou 5) + **MKVToolNix** (Fases 1–2 ou só 2 na esteira SRT).

---

[← Índice](README.md)
