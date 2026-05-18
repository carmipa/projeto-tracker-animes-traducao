# 📚 Documentação — Tracker Animes

Índice central da documentação. O [README principal](../README.md) na raiz traz visão rápida e links para esta pasta.

---

## 🗂️ Guias

| Documento | Conteúdo |
|:---|:---|
| [Estrutura do repositório](estrutura-repositorio.md) | Árvore de pastas e scripts |
| [Arquitetura do pipeline](arquitetura.md) | Diagramas Mermaid, MKVToolNix, LM Studio |
| [Módulo — Fase 0 (Analisador)](modulo-fase-0.md) | `media_analyzer.py`, diagramas, entradas/saídas |
| [Módulo — Fase 1 (Tradutor)](modulo-fase-1.md) | `sub_extractor.py`, IA local, diagramas |
| [Módulo — Fase 2 (Remuxer)](modulo-fase-2.md) | `batch_remuxer.py`, multiplexação |
| [Instalação e pré-requisitos](instalacao.md) | Checklist SO, venv, MKVToolNix, LM Studio |
| [Dependências Python](dependencias-python.md) | Pacotes do `requirements.txt` |
| [Guia de execução](guia-de-execucao.md) | Comandos por fase + layout de pastas de mídia |
| [Logs e auditoria](logs-e-auditoria.md) | Artefatos de log, níveis colorama |
| [Solução de problemas](solucao-de-problemas.md) | Erros comuns + stack resumida |

---

## 🔄 Ordem recomendada de leitura

1. [Instalação](instalacao.md) → [Dependências Python](dependencias-python.md)  
2. [Arquitetura](arquitetura.md)  
3. [Guia de execução](guia-de-execucao.md)  
4. Módulos por fase (0 → 1 → 2)  
5. [Logs](logs-e-auditoria.md) · [Troubleshooting](solucao-de-problemas.md)

---

[← Voltar ao README principal](../README.md)
