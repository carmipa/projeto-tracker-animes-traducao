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

> **Documentação completa:** pasta [`docs/`](docs/README.md) — guias separados por tema para melhor leitura no GitHub.

---

## 🚀 Visão geral

Pipeline em **três etapas** (Python orquestra; **MKVToolNix** manipula vídeo; **LM Studio** traduz em `localhost:1234`):

| Etapa | Pasta | Script | Função |
|:---:|:---|:---|:---|
| **0** | `1_analisador_de_midia/` | `media_analyzer.py` | Auditoria de mídia *(opcional)* |
| **1** | `2_tradutor_ia_gemma4/` | `sub_extractor.py` | Extrai `.ass` → traduz → `*_PTBR.ass` |
| **2** | `3_juntar_legendas_filmes/` | `batch_remuxer.py` | Remux → `*_PTBR.mkv` |

| ⚡ Remux ~1,5 s/ep. | 🔒 LLM 100% local | 📺 Legenda PT-BR como faixa padrão |
|:---:|:---:|:---:|

---

## ⚡ Início rápido

```powershell
# 1. Ambiente
cd C:\TRACKER-ANIMES\projeto-tracker-animes-traducao
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. LM Studio: modelo Gemma 4B na porta 1234

# 3. Pipeline (na ordem)
python .\1_analisador_de_midia\media_analyzer.py    # opcional
python .\2_tradutor_ia_gemma4\sub_extractor.py
python .\3_juntar_legendas_filmes\batch_remuxer.py
```

Pré-requisitos (MKVToolNix, MediaInfo, LM Studio): **[docs/instalacao.md](docs/instalacao.md)**

---

## 📚 Documentação (`docs/`)

| Guia | Descrição |
|:---|:---|
| **[📖 Índice completo](docs/README.md)** | Hub de toda a documentação |
| [Estrutura do repositório](docs/estrutura-repositorio.md) | Pastas, scripts e `docs/` |
| [Arquitetura](docs/arquitetura.md) | Diagramas e camadas do sistema |
| [Fase 0 — Analisador](docs/modulo-fase-0.md) | `media_analyzer.py` |
| [Fase 1 — Tradutor](docs/modulo-fase-1.md) | `sub_extractor.py` + IA |
| [Fase 2 — Remuxer](docs/modulo-fase-2.md) | `batch_remuxer.py` |
| [Instalação](docs/instalacao.md) | Checklist SO + venv |
| [Dependências Python](docs/dependencias-python.md) | `requirements.txt` |
| [Guia de execução](docs/guia-de-execucao.md) | Comandos e layout de mídia |
| [Logs e auditoria](docs/logs-e-auditoria.md) | Artefatos de log |
| [Solução de problemas](docs/solucao-de-problemas.md) | Troubleshooting |

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

</motion>
