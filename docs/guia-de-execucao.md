# ▶️ Guia de execução

[← Índice](README.md) · [Instalação](instalacao.md)

---

## Esteira A — Episódios MKV (Fases 0 → 1 → 2)

### Fase 0 — Auditoria (opcional)

```powershell
python .\1_analisador_de_midia\media_analyzer.py "C:\TRACKER-ANIMES\animes\Macross Delta"
```

**Saída:** `relatorio/{arquivo}_{timestamp}.txt` — [Detalhes](modulo-fase-0.md)

---

### Fase 1 — Extração e tradução ASS

```powershell
python .\2_tradutor_ia_gemma4\sub_extractor.py
```

| Item | Local |
|:---|:---|
| Entrada | Pasta com `.mkv` |
| Saída | `traducao\*_PTBR.ass` |

[Detalhes](modulo-fase-1.md)

---

### Fase 2 — Multiplexação

```powershell
python .\3_juntar_legendas_filmes\batch_remuxer.py
```

| Prompt | Exemplo |
|:---|:---|
| Pasta `.mkv` | `C:\TRACKER-ANIMES\animes\Macross Delta` |
| Pasta `.ass` | `...\Macross Delta\traducao` |

**Saída:** `mkv_final_ptbr\*_PTBR.mkv` — [Detalhes](modulo-fase-2.md)

---

## Esteira B — Filme / SRT externo (Fases 5 → 6 → 2)

Visão completa: [Pipeline SRT](pipeline-srt.md)

### Fase 5 — Tradução SRT direta

```powershell
python .\5_tradutor_de_legenda\tradutor_srt_direto.py
```

| Prompt | Exemplo |
|:---|:---|
| Pasta ou arquivo `.srt` | `C:\TRACKER-ANIMES\animes\md-2\legenda` |
| Tamanho do lote | ENTER = 20 |

**Saída:** `*_PTBR.srt` na mesma pasta — [Detalhes](modulo-fase-5.md)

---

### Fase 6 — Conversão SRT → ASS + sync FPS

```powershell
python .\6-conversor_str_ass\conversor_srt_para_ass.py
```

| Prompt | Padrão no script |
|:---|:---|
| Pasta SRT (`*_PTBR.srt`) | `...\md-2\legenda` |
| Pasta saída ASS | `...\md-2\traducao` |

**Saída:** `{nome_filme}_PTBR.ass` — ajuste `nome_base_filme` no código se necessário — [Detalhes](modulo-fase-6.md)

---

### Fase 2 — Remux (mesmo comando)

```powershell
python .\3_juntar_legendas_filmes\batch_remuxer.py
```

Aponte o `.mkv` do filme e a pasta `traducao\` com o `.ass` gerado na Fase 6.

---

## Layout de pastas

### Episódios (esteira MKV)

```text
C:\TRACKER-ANIMES\animes\Macross Delta\
├── episodio_01.mkv
├── traducao\              ← Fase 1
│   └── episodio_01_PTBR.ass
└── mkv_final_ptbr\        ← Fase 2
    └── episodio_01_PTBR.mkv
```

### Filme (esteira SRT)

```text
C:\TRACKER-ANIMES\animes\md-2\
├── filme.mkv
├── legenda\
│   ├── filme-en.srt
│   └── filme_PTBR.srt     ← Fase 5
├── traducao\
│   └── filme_PTBR.ass     ← Fase 6
└── mkv_final_ptbr\
    └── filme_PTBR.mkv     ← Fase 2
```

---

[← Índice](README.md) · [Logs →](logs-e-auditoria.md)
