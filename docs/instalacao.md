# ✅ Instalação e pré-requisitos

[← Índice](README.md) · [README principal](../README.md) · [Arquitetura](arquitetura.md)

---

## Checklist rápido

| # | Tipo | Item | Obrigatório para |
|:---:|:---|:---|:---|
| 1 | **SO** | [MKVToolNix](https://mkvtoolnix.download/downloads.html) (`mkvmerge`, `mkvextract`) | Fases **2, 4, 5, 8, 12 (opcional)** |
| 2 | **SO** | [MediaInfo](https://mediaarea.net/en/MediaInfo/Download) | Fase **1** |
| 3 | **SO** | [LM Studio](https://lmstudio.ai/) + **Gemma 4B** na porta **1234** | Fases **4, 9** |
| 3b | **SO** | [LM Studio](https://lmstudio.ai/) + **Qwen2.5-7B-Instruct** na porta **1234** | Fase **11** (Gundam Origin, legenda chinesa) |
| 4 | **SO** | [FFmpeg/FFprobe](https://ffmpeg.org/download.html) (build com `hevc_nvenc` para Fase 7) | Fases **6, 7** |
| 5 | **Python** | 3.10+ | Todas |
| 6 | **pip** | [`requirements.txt`](../requirements.txt) | Todas |

| Esteira | Fases | MKVToolNix | LM Studio | FFmpeg |
|:---|:---|:---:|:---:|:---:|
| A — Eighty-Six (ASS embutido EN) | 4 → [12] → 5 | ✅ | ✅ Gemma (Fase 4) | — |
| B — Filme/SRT externo (Macross) | 4 → 3 → 5 | ✅ (Fase 5) | ✅ Gemma (Fase 4) | — |
| C — Legenda PGS (Blu-ray) | 2 → 3 → 5 | ✅ | — | — |
| D — Macross Delta (ASS embutido FR) | 4 → [12] → 5 | ✅ | ✅ Gemma (Fase 4) | — |
| E/F — Lote ASS (Gundam) | 2 → 4 → 5 (+8, +12) | ✅ | ✅ Gemma (Fase 4) | — |
| G — Guilty Crown | 2 → 4 → 10 → [12] → 5 | ✅ | ✅ Gemma (Fase 4) | — |
| H — Gundam Origin (legenda chinesa) | 2 → 11 → [12] → 5 | ✅ (12 opcional) | ✅ **Qwen2.5** (Fase 11) | — |
| I — Gundam Origin (legenda francesa) | 4 → 5 | ✅ | ✅ Gemma (Fase 4) | — |
| 6 — Sincronização (auxiliar) | 6 | — | — | ✅ |
| 7 — Otimização GPU (auxiliar) | 7 | — | — | ✅ NVENC |

> Esteira C também depende de uma ferramenta de **OCR externa** (ex.: Subtitle Edit + Tesseract) entre as Fases 2 e 3 — não incluída neste repositório.
> Esteira H usa um modelo **diferente** das demais (Qwen2.5-7B-Instruct em vez de Gemma 4B) — troque o modelo carregado no LM Studio antes de alternar entre essas esteiras.

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
2. Carregue **`google/gemma-4-e4b`** (ou Gemma 4B equivalente) para as **Fases 4 e 9**.
3. Inicie o servidor em **`http://127.0.0.1:1234`**.
4. Todos os scripts das **Fases 4, 9 e 11** validam `GET /v1/models` antes de processar.
5. Para a **[Fase 11](modulo-fase-11.md)** (Gundam Origin, legenda chinesa), descarregue o Gemma e carregue **`qwen2.5-7b-instruct`** no LM Studio antes de rodar `batch_translator_origin_zh.py` ou `repara_erros_origin_zh.py` — o desempenho do Qwen2.5 para o par chinês→português é muito superior ao do Gemma 4B.

---

## Pronto para rodar

| Objetivo | Guia |
|:---|:---|
| Episódios `.mkv` (ASS embutido) | [Guia de execução — Esteira A](guia-de-execucao.md#esteira-a--episódios-mkv-ass-embutido-fases-4--5) |
| Filme / SRT externo | [Pipeline SRT (Esteira B)](pipeline-srt.md) |
| Visão completa de todas as esteiras | [Arquitetura](arquitetura.md) |

Requisitos mínimos: **venv** + **`requirements.txt`** + **LM Studio** (Fase 4, com Gemma 4B) + **MKVToolNix** (Fases 2, 4, 5, 8). FFmpeg só é necessário se for usar as Fases 6/7. Para a Esteira H ([Fase 11](modulo-fase-11.md)), troque o modelo do LM Studio para Qwen2.5-7B-Instruct.

---

[← Índice](README.md)
