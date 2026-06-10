<div align="center">

  <img src="icone.png?v=2" alt="Ícone do Projeto" width="220"/>

  <h1>🌌 Tracker Animes — Pipeline de Tradução & Multiplexação</h1>

  <p><strong>Esteira industrial local (on-premises) para auditar mídia, traduzir legendas com IA e remuxar episódios e filmes em PT-BR</strong></p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
    <img src="https://img.shields.io/badge/Windows-10%2F11-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows"/>
    <img src="https://img.shields.io/badge/LM_Studio-IA_Local-FF6B35?style=for-the-badge&logo=openai&logoColor=white" alt="LM Studio"/>
    <img src="https://img.shields.io/badge/MKVToolNix-Essencial-4B0082?style=for-the-badge&logo=ffmpeg&logoColor=white" alt="MKVToolNix"/>
    <img src="https://img.shields.io/badge/Subtitle_Edit-OCR_PGS-2E7D32?style=for-the-badge" alt="Subtitle Edit"/>
    <img src="https://img.shields.io/badge/Gemma_4B-LLM-00E5FF?style=for-the-badge&logo=google&logoColor=white" alt="Gemma 4B"/>
    <img src="https://img.shields.io/badge/SRT-ASS_Converter-6B21A8?style=for-the-badge" alt="SRT Pipeline"/>
  </p>

  <p>
    <img src="https://img.shields.io/badge/100%25-Offline-success?style=flat-square" alt="Offline"/>
    <img src="https://img.shields.io/badge/Remux-Sem_Re--encode-blue?style=flat-square" alt="Remux"/>
    <img src="https://img.shields.io/badge/OCR-Tesseract-orange?style=flat-square" alt="Tesseract OCR"/>
    <img src="https://img.shields.io/badge/Logs-Auditáveis-informational?style=flat-square" alt="Logs"/>
  </p>

</div>

> **Documentação completa:** [`docs/`](docs/README.md) — guias por fase, diagramas e troubleshooting.

---

## 🚀 Visão geral

Três esteiras de processamento que compartilham a **Fase 2 (remux)**:

### Esteira MKV — episódios com legenda embutida (.ass)

| Etapa | Pasta | Script |
|:---:|:---|:---|
| **0** | `1_analisador_de_midia/` | `media_analyzer.py` *(opcional)* |
| **1** | `2_tradutor_ia_gemma4/` | `sub_extractor.py` |
| **2** | `3_juntar_legendas_filmes/` | `batch_remuxer.py` |

### Esteira SRT — legendas externas (filmes)

| Etapa | Pasta | Script |
|:---:|:---|:---|
| **5** | `5_tradutor_de_legenda/` | `tradutor_srt_direto.py` |
| **6** | `6-conversor_str_ass/` | `conversor_srt_para_ass.py` |
| **2** | `3_juntar_legendas_filmes/` | `batch_remuxer.py` |

### Esteira PGS — legendas gráficas de Blu-ray (.sup)

| Etapa | Pasta | Script |
|:---:|:---|:---|
| **A** | `extrator_legenda_PGS/` | `extrator_pgs.py` *(Extrai .sup de imagens PGS no .mkv)* |
| **B** | `tradutor_legenda_sup/` | `tradutor_sup.py` *(OCR .sup -> .srt + Tradução IA)* |
| **C** | `6-conversor_str_ass/` | `conversor_srt_para_ass.py` *(Opcional: converte para .ass)* |
| **2** | `3_juntar_legendas_filmes/` | `batch_remuxer.py` *(Remuxa no .mkv final)* |

| ⚡ Remux ~1,5 s/ep. | 🔒 LLM local | 📺 PT-BR faixa padrão | 🎬 Sync FPS 25→23.976 | 👁️ OCR Automático |
|:---:|:---:|:---:|:---:|:---:|

---

## ⚡ Início rápido

```powershell
cd C:\TRACKER-ANIMES\projeto-tracker-animes-traducao
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# LM Studio: Gemma 4B na porta 1234
```

**Episódios (.mkv + ASS interno):**

```powershell
python .\1_analisador_de_midia\media_analyzer.py    # opcional
python .\2_tradutor_ia_gemma4\sub_extractor.py
python .\3_juntar_legendas_filmes\batch_remuxer.py
```

**Filme (SRT externo):**

```powershell
python .\5_tradutor_de_legenda\tradutor_srt_direto.py
python .\6-conversor_str_ass\conversor_srt_para_ass.py
python .\3_juntar_legendas_filmes\batch_remuxer.py
```

**Legendas PGS/Blu-ray (.sup gráfico interno):**

```powershell
# 1. Extrai a legenda PGS (.sup) do MKV original
python .\extrator_legenda_PGS\extrator_pgs.py

# 2. Faz o OCR da legenda .sup para .srt e traduz usando IA local
python .\tradutor_legenda_sup\tradutor_sup.py

# 3. (Opcional) Converte o SRT traduzido para ASS
python .\6-conversor_str_ass\conversor_srt_para_ass.py

# 4. Multiplexa a legenda traduzida de volta para o vídeo
python .\3_juntar_legendas_filmes\batch_remuxer.py
```

Pré-requisitos: **[docs/instalacao.md](docs/instalacao.md)** · Esteira SRT: **[docs/pipeline-srt.md](docs/pipeline-srt.md)**

---

## 📚 Documentação (`docs/`)

| Guia | Descrição |
|:---|:---|
| **[📖 Índice completo](docs/README.md)** | Hub da documentação |
| [Pipeline SRT (5→6→2)](docs/pipeline-srt.md) | Filmes e legendas externas |
| [Arquitetura](docs/arquitetura.md) | Duas esteiras + diagramas |
| [Fase 0](docs/modulo-fase-0.md) · [1](docs/modulo-fase-1.md) · [2](docs/modulo-fase-2.md) | Esteira MKV |
| [Fase 5](docs/modulo-fase-5.md) · [6](docs/modulo-fase-6.md) | Esteira SRT |
| [Instalação](docs/instalacao.md) · [Dependências](docs/dependencias-python.md) | Ambiente |
| [Guia de execução](docs/guia-de-execucao.md) | Comandos e pastas |
| [Logs](docs/logs-e-auditoria.md) · [Problemas](docs/solucao-de-problemas.md) | Operação |

---

## 📄 Licença

[LICENSE](LICENSE)

---

<div align="center">

  <p>
    <strong>Construído por</strong>
    <a href="https://github.com/carmipa"><strong>Paulo André Carminati</strong></a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
    <img src="https://img.shields.io/badge/Antigravity-FF6B35?style=flat-square" alt="Antigravity"/>
    <img src="https://img.shields.io/badge/Cursor_IDE-000000?style=flat-square&logo=cursor&logoColor=white" alt="Cursor IDE"/>
    <img src="https://img.shields.io/badge/Gemini-4285F4?style=flat-square&logo=google&logoColor=white" alt="Gemini"/>
    <img src="https://img.shields.io/badge/Claude-CC785C?style=flat-square" alt="Claude"/>
  </p>

  <p><sub>Pipeline industrial de tradução local · Maio 2026</sub></p>

</div>
