# ▶️ Guia de execução

[← Índice](README.md) · [Instalação](instalacao.md)

Execute as fases **na ordem**. Caminhos podem ser colados com aspas no PowerShell.

---

## Fase 0 — Auditoria (opcional)

```powershell
python .\1_analisador_de_midia\media_analyzer.py "C:\TRACKER-ANIMES\animes\Macross Delta"
```

Modo interativo:

```powershell
python .\1_analisador_de_midia\media_analyzer.py
```

**Saída:** `relatorio/{arquivo}_{timestamp}.txt`

Detalhes: [Módulo Fase 0](modulo-fase-0.md)

---

## Fase 1 — Extração e tradução

```powershell
python .\2_tradutor_ia_gemma4\sub_extractor.py
```

Informe a pasta dos `.mkv`, por exemplo:

```text
C:\TRACKER-ANIMES\animes\Macross Delta
```

| Item | Local |
|:---|:---|
| Legendas PT-BR | `traducao\*_PTBR.ass` |
| Temporário (removido) | `*_extracted.ass` na pasta dos vídeos |

Detalhes: [Módulo Fase 1](modulo-fase-1.md)

---

## Fase 2 — Multiplexação (remux)

```powershell
python .\3_juntar_legendas_filmes\batch_remuxer.py
```

| Prompt | Exemplo |
|:---|:---|
| Pasta `.mkv` | `C:\TRACKER-ANIMES\animes\Macross Delta` |
| Pasta `.ass` | `C:\TRACKER-ANIMES\animes\Macross Delta\traducao` |

**Saída:** `mkv_final_ptbr\*_PTBR.mkv`

Detalhes: [Módulo Fase 2](modulo-fase-2.md)

---

## Layout de pastas de mídia

```text
C:\TRACKER-ANIMES\
├── animes\
│   └── Macross Delta\
│       ├── [Cleo]Macross_Delta_-_01.mkv
│       ├── [Cleo]Macross_Delta_-_02.mkv
│       │
│       ├── traducao\                    ← Fase 1
│       │   ├── ..._01_PTBR.ass
│       │   └── ..._02_PTBR.ass
│       │
│       └── mkv_final_ptbr\              ← Fase 2
│           ├── ..._01_PTBR.mkv
│           └── ..._02_PTBR.mkv
│
└── projeto-tracker-animes-traducao\    ← repositório
    ├── docs\                            ← documentação
    ├── 1_analisador_de_midia\
    ├── 2_tradutor_ia_gemma4\
    └── 3_juntar_legendas_filmes\
```

---

[← Índice](README.md) · [Logs →](logs-e-auditoria.md)
