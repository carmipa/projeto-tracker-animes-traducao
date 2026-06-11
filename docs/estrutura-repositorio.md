# 📦 Estrutura do repositório

[← Índice](README.md)

```text
projeto-tracker-animes-traducao/
├── README.md
├── icone.png
├── requirements.txt
├── LICENSE
│
├── docs/                              ← documentação
│   ├── README.md
│   ├── arquitetura.md
│   ├── pipeline-srt.md                ← esteira 5→6→2
│   ├── modulo-fase-0.md … modulo-fase-2.md
│   ├── modulo-fase-5.md               ← NOVO
│   ├── modulo-fase-6.md               ← NOVO
│   ├── instalacao.md
│   ├── dependencias-python.md
│   ├── guia-de-execucao.md
│   ├── logs-e-auditoria.md
│   ├── solucao-de-problemas.md
│   └── estrutura-repositorio.md
│
├── 1_analisador_de_midia/             # Fase 0 — Análise e Auditoria de Mídia
│   ├── media_analyzer.py
│   └── extractor_inteligente/         # Módulo original de extração de legendas
│
├── 2_extrator_legenda/                # Fase 1 — Extração de Legendas (ASS, SRT, PGS)
│   ├── extrator_inteligente_ass.py
│   ├── extrator_inteligente_srt.py
│   └── extrator_inteligente_pgs.py
│
├── 3-conversor_str_ass/               # Fase 6 — Conversor SRT → ASS + FPS
│   └── conversor_srt_para_ass.py
│
├── 4_tradutor_ia_gemma4/              # Fase 1 / 5 — Tradução via LLM Local (Gemma)
│   ├── sub_extractor.py
│   ├── batch_translator_guilty_crown.py
│   ├── cura_legendas_tag.py
│   └── 5_tradutor_de_legenda/         # Tradução Direta de SRT Externo
│       └── tradutor_srt_direto.py
│
├── 5_juntar_legendas_filmes/          # Fase 2 — Remux (MKVMerge)
│   └── batch_remuxer.py
│
├── 6_sincronizacao_legenda/           # Fase Auxiliar — Sincronia de legendas
│   └── subtitle_stretcher.py
│
└── 7_decodificador/                   # Decodificação e pós-processamento
```

> As pastas estão numeradas de **1 a 7** sequencialmente para fins de ordenação no explorador de arquivos do sistema.

Layout de mídia do usuário: [Guia de execução](guia-de-execucao.md#layout-de-pastas).

---

[← Índice](README.md)
