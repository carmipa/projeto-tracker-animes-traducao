# ✅ Instalação e pré-requisitos

[← Índice](README.md) · [README principal](../README.md) · [Arquitetura](arquitetura.md)

---

## Checklist rápido

| # | Tipo | Item | Obrigatório para |
|:---:|:---|:---|:---|
| 1 | **SO** | [MKVToolNix](https://mkvtoolnix.download/downloads.html) (`mkvmerge`, `mkvextract`) | Fases **2, 4, 5, 8** |
| 2 | **SO** | [MediaInfo](https://mediaarea.net/en/MediaInfo/Download) | Fase **1** |
| 3 | **SO** | [LM Studio](https://lmstudio.ai/) + Gemma 4B na porta **1234** | Fase **4** |
| 4 | **SO** | [FFmpeg/FFprobe](https://ffmpeg.org/download.html) (build com `hevc_nvenc` para Fase 7) | Fases **6, 7** |
| 5 | **Python** | 3.10+ | Todas |
| 6 | **pip** | [`requirements.txt`](../requirements.txt) | Todas |

| Esteira | Fases | MKVToolNix | LM Studio | FFmpeg |
|:---|:---|:---:|:---:|:---:|
| A — Episódios MKV (ASS embutido EN) | 4 → 5 | ✅ | ✅ (Fase 4) | — |
| B — Filme/SRT externo | 4 → 3 → 5 | ✅ (Fase 5) | ✅ (Fase 4) | — |
| C — Legenda PGS (Blu-ray) | 2 → 3 → 5 | ✅ | — | — |
| D — Episódios MKV (ASS embutido FR) | 4 → 5 | ✅ | ✅ (Fase 4) | — |
| E/F — Lote ASS (Gundam) | 2 → 4 → 5 (+8) | ✅ | ✅ (Fase 4) | — |
| 6 — Sincronização (auxiliar) | 6 | — | — | ✅ |
| 7 — Otimização GPU (auxiliar) | 7 | — | — | ✅ NVENC |

> Esteira C também depende de uma ferramenta de **OCR externa** (ex.: Subtitle Edit + Tesseract) entre as Fases 2 e 3 — não incluída neste repositório.

---

## MKVToolNix

```text
C:\Program Files\MKVToolNix\
├── mkvextract.exe    ← extração de legendas (Fases 2, 4, 8)
└── mkvmerge.exe      ← identificação de tracks e remux (Fases 2, 4, 5, 8)
```

---

## FFmpeg / FFprobe

Necessário para a **Fase 6** (sincronização) e **Fase 7** (otimização de vídeo). Adicione `ffmpeg.exe`/`ffprobe.exe` ao `PATH` do Windows.

- Fase 6 (`subtitle_fixer.py`, `auditor_sincronia.py`): apenas `ffprobe`.
- Fase 7 (`gpu_video_optimizer.py`): `ffmpeg` com encoder `hevc_nvenc` (requer **GPU NVIDIA** com suporte a NVENC).

Verifique com:

```powershell
ffmpeg -encoders | Select-String nvenc
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

> `tkinter` (usado pelos seletores de arquivo da Fase 6) já vem incluso na instalação padrão do Python no Windows — nenhuma instalação extra é necessária.

Referência completa dos pacotes: [Dependências Python](dependencias-python.md).

---

## LM Studio

1. Instale o [LM Studio](https://lmstudio.ai/).
2. Carregue **`google/gemma-4-e4b`** (ou Gemma 4B equivalente).
3. Inicie o servidor em **`http://127.0.0.1:1234`**.
4. Todos os scripts da **Fase 4** validam `GET /v1/models` antes de processar.

---

## Pronto para rodar

| Objetivo | Guia |
|:---|:---|
| Episódios `.mkv` (ASS embutido) | [Guia de execução — Esteira A](guia-de-execucao.md#esteira-a--episódios-mkv-ass-embutido-fases-4--5) |
| Filme / SRT externo | [Pipeline SRT (Esteira B)](pipeline-srt.md) |
| Visão completa de todas as esteiras | [Arquitetura](arquitetura.md) |

Requisitos mínimos: **venv** + **`requirements.txt`** + **LM Studio** (Fase 4) + **MKVToolNix** (Fases 2, 4, 5, 8). FFmpeg só é necessário se for usar as Fases 6/7.

---

[← Índice](README.md)
