# ✅ Instalação e pré-requisitos

[← Índice](README.md) · [README principal](../README.md)

---

## Checklist rápido

| # | Tipo | Item | Obrigatório para |
|:---:|:---|:---|:---|
| 1 | **SO** | [MKVToolNix](https://mkvtoolnix.download/downloads.html) | Fases 1 e 2 |
| 2 | **SO** | [MediaInfo](https://mediaarea.net/en/MediaInfo/Download) | Fase 0 |
| 3 | **SO** | [LM Studio](https://lmstudio.ai/) + Gemma 4B na porta **1234** | Fase 1 |
| 4 | **Python** | 3.10+ | Todas |
| 5 | **pip** | [`requirements.txt`](../requirements.txt) | Todas |

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
4. O `sub_extractor.py` valida `GET /v1/models` antes de processar.

---

## Pronto para rodar

Com **MKVToolNix**, **venv ativo**, **`requirements.txt` instalado** e **LM Studio na porta 1234**, siga o [Guia de execução](guia-de-execucao.md).

---

[← Índice](README.md)
