<div align="center">

  <img src="icone.png?v=2" alt="Ícone do Projeto" width="220"/>

  <h1>🌌 Tracker Animes — Pipeline de Tradução & Multiplexação</h1>

  <p><strong>Esteira industrial local (on-premises) para auditar mídia, traduzir legendas ASS com IA e remuxar episódios em PT-BR</strong></p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
    <img src="https://img.shields.io/badge/Windows-10%2F11-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows"/>
    <img src="https://img.shields.io/badge/LM_Studio-IA_Local-FF6B35?style=for-the-badge&logo=openai&logoColor=white" alt="LM Studio"/>
    <img src="https://img.shields.io/badge/MKVToolNix-Essencial-4B0082?style=for-the-badge&logo=ffmpeg&logoColor=white" alt="MKVToolNix"/>
    <img src="https://img.shields.io/badge/Gemma_4B-LLM-00E5FF?style=for-the-badge&logo=google&logoColor=white" alt="Gemma 4B"/>
  </p>

  <p>
    <img src="https://img.shields.io/badge/100%25-Offline-success?style=flat-square" alt="Offline"/>
    <img src="https://img.shields.io/badge/Remux-Sem_Re--encode-blue?style=flat-square" alt="Remux"/>
    <img src="https://img.shields.io/badge/Logs-Auditáveis-informational?style=flat-square" alt="Logs"/>
  </p>

</div>

> **Nota:** O pipeline foi desenhado para temporadas completas de anime em `.mkv` (caso de uso inicial: *Macross Delta*), mas funciona com qualquer pasta de episódios que siga a convenção de nomes descrita abaixo.

---

## 📋 Índice

| | |
|---|---|
| [🚀 Visão Geral](#-visão-geral) | [📦 Estrutura do Repositório](#-estrutura-do-repositório) |
| [🏗️ Arquitetura do Pipeline](#️-arquitetura-do-pipeline) | [🛠️ Módulos (1 → 2 → 3)](#️-módulos-1--2--3) |
| [✅ Pré-requisitos & Instalação](#-pré-requisitos--instalação) | [▶️ Como Executar](#️-como-executar) |
| [📂 Layout de Pastas de Mídia](#-layout-de-pastas-de-mídia) | [📊 Auditoria e Logs](#-auditoria-e-logs) |
| [⚠️ Solução de Problemas](#️-solução-de-problemas) | [📄 Licença](#-licença) |

---

## 🚀 Visão Geral

Este repositório orquestra **três etapas sequenciais** em Python. O interpretador **não re-encoda vídeo** — ele delega operações de container ao **MKVToolNix** e a tradução ao **LM Studio** (API compatível com OpenAI em `localhost:1234`).

| Etapa | Pasta | Script | Função |
|:---:|:---|:---|:---|
| **0** | `1_analisador_de_midia/` | `media_analyzer.py` | Auditoria técnica de vídeo/áudio/legendas (opcional, recomendado antes do pipeline) |
| **1** | `2_tradutor_ia_gemma4/` | `sub_extractor.py` | Extrai `.ass` do `.mkv` → traduz via Gemma 4B → salva `*_PTBR.ass` |
| **2** | `3_juntar_legendas_filmes/` | `batch_remuxer.py` | Injeta a legenda PT-BR no container → gera `*_PTBR.mkv` |

<table>
  <tr>
    <td align="center">⚡ <b>Velocidade (remux)</b><br/>~1,5 s por episódio</td>
    <td align="center">🔒 <b>Privacidade</b><br/>LLM 100% local</td>
    <td align="center">📺 <b>Saída</b><br/>Legenda PT-BR como faixa padrão</td>
  </tr>
</table>

---

## 🏗️ Arquitetura do Pipeline

Fluxo determinístico: **análise (opcional) → extração/tradução → multiplexação**.

```mermaid
flowchart TB
    subgraph F0["Fase 0 — Auditoria (opcional)"]
        A0["📂 Pasta de .mkv"] --> B0["media_analyzer.py<br/>pymediainfo"]
        B0 --> C0["📄 relatorio/*.txt"]
    end

    subgraph F1["Fase 1 — Tradução"]
        A1["📂 Episódios .mkv"] --> B1["mkvmerge -J<br/>Detecta track S_TEXT/ASS"]
        B1 --> C1["mkvextract.exe<br/>Legenda .ass original"]
        C1 --> D1{"Filtros Regex"}
        D1 -->|"> 2000 chars"| E1["🗑️ Descarta fontes Base64"]
        D1 -->|"Dialogue:"| F1["📝 Lotes de 20 linhas"]
        F1 --> G1["🧠 LM Studio :1234<br/>Gemma 4B"]
        G1 --> H1["🇧🇷 traducao/*_PTBR.ass"]
    end

    subgraph F2["Fase 2 — Multiplexação"]
        A2[".mkv original"] --> I2["batch_remuxer.py"]
        H1 --> I2
        I2 --> J2["mkvmerge.exe<br/>--default-track 0:yes"]
        J2 --> K2["🎬 mkv_final_ptbr/*_PTBR.mkv"]
    end

    F0 -.->|"valida faixas"| F1
    F1 --> F2

    style G1 fill:#4B0082,stroke:#00E5FF,color:#fff
    style K2 fill:#006400,stroke:#32CD32,color:#fff
    style H1 fill:#1a1a2e,stroke:#00E5FF,color:#fff
```

### Binários externos (Windows)

O Python **orquestra**; a manipulação de Matroska é feita pelos executáveis do MKVToolNix:

| Executável | Usado em | Caminho padrão |
|:---|:---|:---|
| `mkvmerge.exe` | Identificar tracks (`-J`) e remuxar | `C:\Program Files\MKVToolNix\` |
| `mkvextract.exe` | Extrair faixa de legenda `.ass` | `C:\Program Files\MKVToolNix\` |

> Instale o [MKVToolNix](https://mkvtoolnix.download/downloads.html) e confirme que ambos os `.exe` existem no diretório acima (ou em `Program Files (x86)` — o código tenta os dois caminhos na Fase 1).

### Servidor de IA

| Componente | Papel |
|:---|:---|
| **[LM Studio](https://lmstudio.ai/)** | Runtime on-premises: HTTP na porta **1234**, gerencia Prompt Cache e carrega o modelo na VRAM |
| **Gemma 4B** (`google/gemma-4-e4b`) | Modelo recomendado para ficção científica / mecha / termos militares |

Antes da Fase 1: abra o LM Studio → carregue o modelo → **Start Server** na porta `1234`.

---

## 📦 Estrutura do Repositório

```text
projeto-tracker-animes-traducao/
├── icone.png
├── requirements.txt
├── README.md
│
├── 1_analisador_de_midia/
│   └── media_analyzer.py          # Fase 0 — auditoria pymediainfo
│
├── 2_tradutor_ia_gemma4/
│   ├── sub_extractor.py           # Fase 1 — extração + tradução
│   └── logs/                      # pipeline, erros, stats, config
│
├── 3_juntar_legendas_filmes/
│   └── batch_remuxer.py           # Fase 2 — remux em lote
│
├── multiplexar/logs/              # logs do remuxer (sessões anteriores)
└── relatorio/                     # relatórios .txt da Fase 0
```

---

## 🛠️ Módulos (1 → 2 → 3)

### `1_analisador_de_midia/media_analyzer.py` — Fase 0 (opcional)

Varredura recursiva de `.mkv`, `.mp4`, `.avi`, etc. Gera relatório por arquivo em `relatorio/` com:

- Container, duração, bitrate geral  
- Fluxos de vídeo (codec, resolução, FPS)  
- Fluxos de áudio (idioma, canais)  
- **Legendas:** distingue `ASS/SSA`, `SRT` e **`PGS` (bitmap — não extraível)**

> Use esta fase para confirmar que o episódio tem legenda **texto** (`S_TEXT/ASS`) antes de gastar tempo na tradução.

---

### `2_tradutor_ia_gemma4/sub_extractor.py` — Fase 1

| Recurso | Detalhe |
|:---|:---|
| **Autodetecção de track** | `mkvmerge -J` → primeira faixa `subtitles` com `S_TEXT/ASS` |
| **Encoding resiliente** | Cadeia: `utf-8` → `utf-8-sig` → `cp1252` → `latin-1` → `iso-8859-1` → bypass |
| **Regex industrial** | `^(Dialogue:\s*[^,]*(?:,[^,]*){8},)(.*)$` — ignora metadados ASS |
| **Filtro de bloat** | Linhas &gt; 2000 caracteres (fontes Base64 embutidas) |
| **Tradução em lote** | 20 diálogos por requisição HTTP |
| **Cache em memória** | Evita retraduzir lotes idênticos |
| **Saída** | `{pasta_episodios}/traducao/{nome}_PTBR.ass` |

---

### `3_juntar_legendas_filmes/batch_remuxer.py` — Fase 2

| Recurso | Detalhe |
|:---|:---|
| **Pareamento estrito** | `{base}.mkv` ↔ `traducao/{base}_PTBR.ass` |
| **Sem re-encode** | Apenas remux — I/O intensivo em NVMe |
| **Metadados da faixa** | `--language 0:por`, `--track-name "0:Português (Gemma 4B)"`, `--default-track 0:yes` |
| **Resiliência** | `Ctrl+C` salva estatísticas parciais em JSON |
| **Saída** | `{pasta_videos}/mkv_final_ptbr/{base}_PTBR.mkv` |

---

## ✅ Pré-requisitos & Instalação

### Checklist rápido

| # | Tipo | Item | Obrigatório para |
|:---:|:---|:---|:---|
| 1 | **SO** | [MKVToolNix](https://mkvtoolnix.download/downloads.html) (`mkvextract` + `mkvmerge`) | Fases 1 e 2 |
| 2 | **SO** | [MediaInfo](https://mediaarea.net/en/MediaInfo/Download) (DLL usada pelo `pymediainfo`) | Fase 0 |
| 3 | **SO** | [LM Studio](https://lmstudio.ai/) + modelo Gemma 4B na porta **1234** | Fase 1 |
| 4 | **Python** | 3.10+ | Todas |
| 5 | **pip** | Pacotes do `requirements.txt` | Todas |

### 1. Dependência de sistema — MKVToolNix

```text
C:\Program Files\MKVToolNix\
├── mkvextract.exe    ← extração de legendas (Fase 1)
└── mkvmerge.exe      ← identificação de tracks e remux (Fases 1 e 2)
```

### 2. Dependências Python

Recomendado: ambiente virtual na raiz do projeto.

```powershell
cd C:\TRACKER-ANIMES\projeto-tracker-animes-traducao
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

| Pacote | Função no projeto |
|:---|:---|
| **`colorama`** | Cores ANSI no PowerShell/CMD — blocos `[SUCESSO]`, `[AVISO]`, `[ERRO]` |
| **`tqdm`** | Barras de progresso (tradução e remux) |
| **`requests`** | Cliente HTTP para API do LM Studio |
| **`pymediainfo`** | Leitura de metadados na Fase 0 |

Instalação mínima manual (se não usar `requirements.txt`):

```powershell
pip install colorama tqdm requests pymediainfo
```

### 3. Servidor de IA — LM Studio

1. Baixe e instale o LM Studio.  
2. Carregue o modelo **`google/gemma-4-e4b`** (ou equivalente Gemma 4B).  
3. Inicie o servidor local em **`http://127.0.0.1:1234`**.  
4. O `sub_extractor.py` valida `GET /v1/models` antes de processar.

Com **MKVToolNix no caminho padrão**, **`colorama` + `tqdm` no venv** e **LM Studio ativo**, a esteira tem todos os pré-requisitos para rodar sem exceções de dependência.

---

## ▶️ Como Executar

Execute as fases **na ordem**. Cada script pede caminhos interativamente (aspas ao arrastar pastas no PowerShell são aceitas).

### Fase 0 — Auditoria (opcional)

```powershell
python .\1_analisador_de_midia\media_analyzer.py "C:\TRACKER-ANIMES\animes\Macross Delta"
```

Ou modo interativo (sem argumentos):

```powershell
python .\1_analisador_de_midia\media_analyzer.py
```

Relatórios em: `relatorio/{arquivo}_{timestamp}.txt`

---

### Fase 1 — Extração e tradução

```powershell
python .\2_tradutor_ia_gemma4\sub_extractor.py
```

Quando solicitado, informe a pasta dos `.mkv`, por exemplo:

```text
C:\TRACKER-ANIMES\animes\Macross Delta
```

**Resultado:** subpasta `traducao\` com arquivos `*_PTBR.ass`  
**Artefato temporário:** `*_extracted.ass` na pasta dos vídeos (removido ao fim de cada episódio)

---

### Fase 2 — Multiplexação (remux)

```powershell
python .\3_juntar_legendas_filmes\batch_remuxer.py
```

| Prompt | Exemplo |
|:---|:---|
| Pasta com vídeos `.mkv` | `C:\TRACKER-ANIMES\animes\Macross Delta` |
| Pasta com legendas `.ass` | `C:\TRACKER-ANIMES\animes\Macross Delta\traducao` |

**Resultado:** subpasta `mkv_final_ptbr\` com `*_PTBR.mkv`

---

## 📂 Layout de Pastas de Mídia

Convenção esperada pelo pipeline (crie as subpastas automaticamente ou manualmente):

```text
C:\TRACKER-ANIMES\
├── animes\
│   └── Macross Delta\
│       ├── [Cleo]Macross_Delta_-_01.mkv
│       ├── [Cleo]Macross_Delta_-_02.mkv
│       │
│       ├── traducao\                              ← gerado na Fase 1
│       │   ├── [Cleo]Macross_Delta_-_01_PTBR.ass
│       │   └── [Cleo]Macross_Delta_-_02_PTBR.ass
│       │
│       └── mkv_final_ptbr\                        ← gerado na Fase 2
│           ├── [Cleo]Macross_Delta_-_01_PTBR.mkv
│           └── [Cleo]Macross_Delta_-_02_PTBR.mkv
│
└── projeto-tracker-animes-traducao\             ← este repositório
```

---

## 📊 Auditoria e Logs

Cada execução das Fases 1 e 2 gera **quatro artefatos** com timestamp `YYYY-MM-DD_HH-MM-SS`:

| Arquivo | Conteúdo |
|:---|:---|
| `pipeline_*.txt` / `remux_pipeline_*.txt` | Fluxo completo da execução |
| `config_*.txt` / `remux_config_*.txt` | Snapshot de caminhos e infraestrutura |
| `erros_*.txt` / `remux_erros_*.txt` | Erros e stack traces isolados |
| `stats_*.json` / `remux_stats_*.json` | Telemetria estruturada (contagens, bytes, encodings) |

| Módulo | Pasta de logs |
|:---|:---|
| Fase 1 | `2_tradutor_ia_gemma4/logs/` |
| Fase 2 | `multiplexar/logs/` (configurado em `batch_remuxer.py`) |

### Níveis no console (colorama)

| Tag | Cor | Significado |
|:---:|:---:|:---|
| `[SUCESSO]` | 🟢 Verde | Operação concluída |
| `[INFO]` / `[DEBUG]` | ⚪ / 🔵 | Fluxo normal / detalhe |
| `[AVISO]` | 🟡 Amarelo | Situação recuperável |
| `[ERRO]` / `[CRÍTICO]` | 🔴 Vermelho | Falha ou aborto |

---

## ⚠️ Solução de Problemas

| Sintoma | Causa provável | Ação |
|:---|:---|:---|
| `mkvextract.exe não encontrados` | MKVToolNix ausente ou fora do caminho padrão | Reinstale em `C:\Program Files\MKVToolNix\` |
| `LM Studio não responde` | Servidor parado ou porta errada | Inicie o servidor na porta **1234** |
| `Nenhuma faixa S_TEXT/ASS` | Legenda PGS/hardsub | Use a Fase 0 — PGS não é extraível como texto |
| Episódio ignorado no remux | Legenda com nome diferente de `{base}_PTBR.ass` | Confira a pasta `traducao\` |
| Caracteres estranhos na legenda | Encoding legado | O tradutor já tenta múltiplos encodings; verifique `stats_*.json` → `encodings_detectados` |
| `pymediainfo nao esta instalado` | Pacote ou MediaInfo DLL ausente | `pip install pymediainfo` + instale o MediaInfo |

---

## ⚙️ Stack resumida

| Camada | Tecnologia |
|:---|:---|
| Orquestração | Python 3.10+ |
| Container Matroska | MKVToolNix (`mkvmerge`, `mkvextract`) |
| Metadados de mídia | pymediainfo + MediaInfo |
| Tradução | LM Studio + Gemma 4B (API OpenAI-compatible) |
| UX no terminal | colorama + tqdm |
| Formato de legenda | ASS (`S_TEXT/ASS`) |

---

## 📄 Licença

Consulte o arquivo [LICENSE](LICENSE) neste repositório.

---

<hr/>

<div align="center">

  <p>Construído por <strong>Paulo</strong> & <strong>Antigravity</strong> 🚀</p>
  <p><sub>Pipeline industrial de tradução local · Maio 2026</sub></p>

</div>
