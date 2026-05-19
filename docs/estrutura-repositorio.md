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
├── 1_analisador_de_midia/             # Fase 0
│   └── media_analyzer.py
│
├── 2_tradutor_ia_gemma4/              # Fase 1 — MKV + ASS
│   ├── sub_extractor.py
│   └── logs/
│
├── 3_juntar_legendas_filmes/          # Fase 2 — remux (ambas esteiras)
│   └── batch_remuxer.py
│
├── 5_tradutor_de_legenda/             # Fase 5 — SRT direto
│   ├── tradutor_srt_direto.py
│   └── logs/
│
├── 6-conversor_str_ass/               # Fase 6 — SRT → ASS + FPS
│   └── conversor_srt_para_ass.py
│
├── multiplexar/logs/                  ← logs do remuxer
└── relatorio/                         ← relatórios Fase 0
```

> As fases **3** e **4** não existem no repositório — numeração salta de 2 para 5 por evolução do projeto.

Layout de mídia do usuário: [Guia de execução](guia-de-execucao.md#layout-de-pastas).

---

[← Índice](README.md)
