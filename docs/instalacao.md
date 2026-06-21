# ✅ Instalação e pré-requisitos

[← Índice](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/README.md) · [README principal](../README.md) · [Arquitetura](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/arquitetura.md)

---

## Checklist rápido

| # | Tipo | Item | Obrigatório para |
|:---:|:---|:---|:---|
| 1 | **SO** | [MKVToolNix](https://mkvtoolnix.download/downloads.html) (`mkvmerge`, `mkvextract`) | Fases **02, 05a, 05b, 06, 10 (opcional), 12** |
| 2 | **SO** | [MediaInfo](https://mediaarea.net/en/MediaInfo/Download) | Fase **01** |
| 3 | **SO** | [LM Studio](https://lmstudio.ai/) + **Gemma 4B** na porta **1234** | Fases **05a, 07** |
| 3b | **SO** | [LM Studio](https://lmstudio.ai/) + **Mistral Nemo Instruct 2407 (GGUF)** na porta **1234** | Fase **05b** (Macross Delta, Gundam Origin francês, Detonator Orgun) |
| 3c | **SO** | [LM Studio](https://lmstudio.ai/) + **Qwen2.5-7B-Instruct** na porta **1234** | Fase **05c** (Gundam The Origin, legenda chinesa) |
| 3d | **SO** | [LM Studio](https://lmstudio.ai/) + **TranslateGemma 12B** na porta **1234** | Fase **05c-2** (Gundam Zeta, Gundam ZZ) |
| 4 | **SO** | [FFmpeg/FFprobe](https://ffmpeg.org/download.html) (build com `hevc_nvenc` para Fase 03) | Fases **08, 03** |
| 5 | **Python** | 3.10+ | Todas |
| 6 | **pip** | [`requirements.txt`](../requirements.txt) | Todas |

| Esteira | Fases | MKVToolNix | LM Studio | FFmpeg |
|:---|:---|:---:|:---:|:---:|
| A — Eighty-Six (ASS embutido EN) | 05a → [07] → 12 → [10] | ✅ | ✅ Gemma (05a/07) | — |
| B — Filme/SRT externo (Macross) | 05a → 04 → 12 | ✅ (Fase 12) | ✅ Gemma (05a) | — |
| C — Legenda PGS (Blu-ray) | 02 → 04 → 12 | ✅ | — | — |
| D — Macross Delta TV (ASS embutido FR) | 05b → [07] → 12 → [10] | ✅ | ✅ **Mistral Nemo** (05b) | — |
| E — Macross Delta Filme 2 (FR) | 05b → 07 → 10 → 12 | ✅ | ✅ **Mistral Nemo** (05b) | — |
| F/G — Lote ASS (Gundam) | 02 → 05a → [06] → [07] → 12 → [10] | ✅ | ✅ Gemma (05a/07) | — |
| H — Guilty Crown | 02 → 05a → [07] → 11 → 12 → [10] | ✅ | ✅ Gemma (05a/07) | — |
| I — Gundam The Origin (legenda chinesa) | 02 → 05c → [07] → 12 → [10] | ✅ (10 opcional) | ✅ **Qwen2.5** (05c) | — |
| J — Gundam Origin (legenda francesa) | 05b → [07] → 12 | ✅ | ✅ **Mistral Nemo** (05b) | — |
| K — Gundam Zeta | 05c-2 → [07] → 12 | ✅ | ✅ **TranslateGemma** (05c-2) | — |
| L — Gundam ZZ | 05c-2 → [07] → 12 | ✅ | ✅ **TranslateGemma** (05c-2) | — |
| M — Detonator Orgun | 05b → [07] → 12 | ✅ | ✅ **Mistral Nemo** (05b) | — |
| N — Knights of Sidonia | 05a → [07] → 12 | ✅ | ✅ Gemma (05a/07) | — |
| 08 — Sincronização (auxiliar) | 08 | — | — | ✅ |
| 03 — Otimização GPU (auxiliar) | 03 | — | — | ✅ NVENC |

> Esteira C também depende de uma ferramenta de **OCR externa** (ex.: Subtitle Edit + Tesseract) entre as Fases 02 e 04 — não incluída neste repositório.
> As esteiras e ferramentas que indicam a **Fase 07** usam scripts de higienização de lore específicos do título e/ou reparos de tradução via IA. Troque o modelo carregado no LM Studio antes de alternar entre esteiras com idiomas de origem diferentes (Gemma 4B ↔ Mistral Nemo Instruct 2407 ↔ Qwen2.5-7B-Instruct ↔ TranslateGemma 12B).

---

## MKVToolNix

```text
C:\Program Files\MKVToolNix\
├── mkvextract.exe    ← extração de legendas (Fases 02, 05a, 06)
└── mkvmerge.exe      ← identificação de tracks e remux (Fases 02, 05a, 12, 06)
```

---

## FFmpeg / FFprobe

Necessário para a **Fase 08** (sincronização) e **Fase 03** (otimização de vídeo). Adicione `ffmpeg.exe`/`ffprobe.exe` ao `PATH` do Windows.

- Fase 08 (`subtitle_fixer.py`, `auditor_sincronia.py`): apenas `ffprobe`.
- Fase 03 (`gpu_video_optimizer.py`): `ffmpeg` com encoder `hevc_nvenc` (requer **GPU NVIDIA** com suporte a NVENC).

Verifique com:

```powershell
ffmpeg -encoders | Select-String nvenc
```

---

## Ambiente Python (venv)

```powershell
cd D:\PROJETOS-OPEN\projeto-tracker-animes-traducao
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Instalação mínima (pacotes diretos):

```powershell
pip install colorama tqdm requests pymediainfo
```

> `tkinter` (usado pelos seletores de arquivo da Fase 08) já vem incluso na instalação padrão do Python no Windows — nenhuma instalação extra é necessária.

Referência completa dos pacotes: [Dependências Python](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/dependencias-python.md).

---

## LM Studio

1. Instale o [LM Studio](https://lmstudio.ai/).
2. Carregue **`google/gemma-4-e4b`** (ou Gemma 4B equivalente) para as **Fases 05a e 07**.
3. Inicie o servidor em **`http://127.0.0.1:1234`**.
4. Todos os scripts das **Fases 05a, 05b, 05c, 05c-2 e 07** validam `GET /v1/models` antes de processar e usam o **modelo detectado dinamicamente** — não há nome de modelo fixo no código.
5. Para a **[Fase 05b](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-05b.md)** (Macross Delta, Gundam Origin francês, Detonator Orgun), descarregue o Gemma e carregue **`mistralai/mistral-nemo-instruct-2407`** (GGUF) — qualidade de tradução muito superior no par francês→português e usado também para o inglês de Detonator Orgun.
6. Para a **[Fase 05c](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-05c.md)** (Gundam The Origin, legenda chinesa), carregue **`qwen2.5-7b-instruct`** antes de rodar `batch_translator_origin_zh.py` ou `repara_erros_origin_zh.py` — o desempenho do Qwen2.5 para o par chinês→português é muito superior ao do Gemma 4B.
7. Para a **[Fase 05c-2](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-05c2.md)** (Gundam Zeta, Gundam ZZ, revisão de PT-BR), carregue o modelo **TranslateGemma 12B**.

---

## Pronto para rodar

| Objetivo | Guia |
|:---|:---|
| Episódios `.mkv` (ASS embutido) | [Guia de execução — Esteira A](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/guia-de-execucao.md#esteira-a--eighty-six-mkv-ass-embutido-inglês--fases-05a--10--12) |
| Filme / SRT externo | [Pipeline SRT (Esteira B)](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/pipeline-srt.md) |
| Visão completa de todas as esteiras | [Arquitetura](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/arquitetura.md) |

Requisitos mínimos: **venv** + **`requirements.txt`** + **LM Studio** (Fase 05a, com Gemma 4B) + **MKVToolNix** (Fases 02, 05a, 12, 06). FFmpeg só é necessário se for usar as Fases 08/03. Para as Esteiras D/E/J/M ([Fase 05b](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-05b.md)), troque o modelo do LM Studio para Mistral Nemo Instruct 2407 (GGUF); para a Esteira I ([Fase 05c](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-05c.md)), troque para Qwen2.5-7B-Instruct; para as Esteiras K/L ([Fase 05c-2](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-05c2.md)), troque para TranslateGemma 12B.

---

[← Índice](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/README.md)
