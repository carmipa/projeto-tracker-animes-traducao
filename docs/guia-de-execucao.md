# ▶️ Guia de execução

[← Índice](README.md) · [Instalação](instalacao.md) · [Arquitetura](arquitetura.md)

<p>
  <img src="https://img.shields.io/badge/Esteiras-A_a_G-9146FF?style=flat-square" alt="Esteiras A-G"/>
</p>

Comandos por esteira (A–G), na ordem de execução. Pré-requisitos detalhados em [instalacao.md](instalacao.md).

---

## Fase 1 — Auditoria (opcional, qualquer esteira)

```powershell
python ".\1_analisador_de_midia\media_analyzer.py" "C:\TRACKER-ANIMES\animes\Macross Delta"
```

**Saída:** `relatorio/{arquivo}_{timestamp}.txt` — [Detalhes](modulo-fase-1.md)

---

## Esteira A — Episódios MKV (ASS embutido, inglês) — Fases 4 → 5

```powershell
# Pré-requisito: LM Studio na porta 1234
python ".\4_tradutor_ia_gemma4\sub_extractor.py"
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
```

| Item | Local |
|:---|:---|
| Entrada | Pasta com `.mkv` (legenda `S_TEXT/ASS` em inglês embutida) |
| Saída Fase 4 | `traducao\*_PTBR.ass` |
| Saída Fase 5 | `mkv_final_ptbr\*_PTBR.mkv` |

[Fase 4](modulo-fase-4.md) · [Fase 5](modulo-fase-5.md) · [Diagrama](arquitetura.md#esteira-a--episódio-mkv-com-ass-embutido-inglês)

---

## Esteira B — Filme / SRT externo (inglês) — Fases 4 → 3 → 5

Visão completa: [Pipeline SRT](pipeline-srt.md)

```powershell
# Pré-requisito: LM Studio na porta 1234
python ".\4_tradutor_ia_gemma4\5_tradutor_de_legenda\tradutor_srt_direto.py"
python ".\3-conversor_str_ass\conversor_srt_para_ass.py"
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
```

| Prompt | Exemplo |
|:---|:---|
| Pasta ou arquivo `.srt` (Fase 4) | `C:\TRACKER-ANIMES\animes\md-2\legenda` |
| Tamanho do lote (Fase 4) | ENTER = 20 |
| Pasta SRT `*_PTBR.srt` (Fase 3) | `...\md-2\legenda` |
| Pasta saída ASS (Fase 3) | `...\md-2\traducao` |
| Pasta `.mkv` / pasta `.ass` (Fase 5) | `...\md-2` / `...\md-2\traducao` |

[Fase 4 (item 5)](modulo-fase-4.md#5--tradutor_srt_diretopy-srt-externo) · [Fase 3](modulo-fase-3.md) · [Fase 5](modulo-fase-5.md) · [Diagrama](arquitetura.md#esteira-b--filme-com-srt-externo-inglês)

---

## Esteira C — Legenda PGS (Blu-ray bitmap) — Fases 2 → OCR externo → 3 → 5

```powershell
python ".\2_extrator_legenda\extrator_inteligente_pgs.py"
# OCR externo (Subtitle Edit + Tesseract) -> *_PTBR.srt
python ".\3-conversor_str_ass\conversor_srt_para_ass.py"
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
```

> O OCR `.sup → .srt` **não faz parte** deste repositório (use Subtitle Edit + Tesseract ou similar).

[Fase 2](modulo-fase-2.md) · [Fase 3](modulo-fase-3.md) · [Fase 5](modulo-fase-5.md) · [Diagrama](arquitetura.md#esteira-c--legenda-pgs-bluray-bitmap)

---

## Esteira D — Episódios MKV (ASS embutido, francês) — Fase 4 → 5

```powershell
# Pré-requisito: LM Studio na porta 1234
python ".\4_tradutor_ia_gemma4\script_tradutor_fr.py"
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
```

Multi-thread (2 threads), glossário e cache persistente (`traducao_cache_fr.json`).

[Fase 4 (item 2)](modulo-fase-4.md) · [Fase 5](modulo-fase-5.md) · [Diagrama](arquitetura.md#esteira-d--tradução-francês--pt-br-multi-thread)

---

## Esteira E — Lote ASS pré-extraído (Gundam Reconguista) — Fases 2 → 4 → 5

```powershell
python ".\2_extrator_legenda\extrator_inteligente_ass.py"
python ".\4_tradutor_ia_gemma4\tradutor_ass\batch_translator_ass.py"
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
```

[Fase 2](modulo-fase-2.md) · [Fase 4 (item 3)](modulo-fase-4.md) · [Fase 5](modulo-fase-5.md) · [Diagrama](arquitetura.md#esteira-e--lote-ass-pré-extraído-gundam-reconguista)

---

## Esteira F — Gundam Unicorn (especializada) — Fases 2 → 4 → 8 → 5

```powershell
python ".\2_extrator_legenda\extrator_inteligente_ass.py"
python ".\4_tradutor_ia_gemma4\tradutor_gundam_unicornio\batch_translator_unicorn.py"
python ".\8_cura_legendas\cura_legendas_tag.py"          # se necessário (TAG corrompido)
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
```

[Fase 2](modulo-fase-2.md) · [Fase 4 (item 4)](modulo-fase-4.md) · [Fase 8](modulo-fase-8.md) · [Fase 5](modulo-fase-5.md) · [Diagrama](arquitetura.md#esteira-f--gundam-unicorn-especializada)

---

## Esteira G — Guilty Crown (correção de nomes e cores) — Fases 2 → 4 → 10 → 5

```powershell
python ".\2_extrator_legenda\extrator_inteligente_ass.py"
python ".\4_tradutor_ia_gemma4\tradutor_ass\batch_translator_ass.py"   # ou variante adequada
python ".\10_correcao_guilty_crown\corrigir_guilty_crown.py"           # remove [ERRO_TRADUCAO:]
python ".\10_correcao_guilty_crown\corrigir_cores_musicas.py"          # cores/tags OP-ED
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
```

| Prompt | Exemplo |
|:---|:---|
| Pasta com legendas + erros (`corrigir_guilty_crown.py`) | `E:\animes\GUILTY CROWN\1080p\legendas_eng` |
| Pasta de saída corrigida (`corrigir_guilty_crown.py`) | `E:\animes\GUILTY CROWN\1080p\legendas_ptbr` |
| Pasta com legendas PT-BR (`corrigir_cores_musicas.py`) | `E:\animes\GUILTY CROWN\1080p\legendas_ptbr` |

[Fase 2](modulo-fase-2.md) · [Fase 4](modulo-fase-4.md) · [Fase 10](modulo-fase-10.md) · [Fase 5](modulo-fase-5.md) · [Diagrama](arquitetura.md#esteira-g--guilty-crown-correção-de-nomes-e-cores-de-músicas)

---

## Pós-processamento — Reparo de `[ERRO_TRADUCAO:]` (Fases 9 e 10, opcionais)

Quando a **Fase 4** deixa marcadores `[ERRO_TRADUCAO: <texto>]` em `traducao\*_PTBR.ass`, rode **antes** da Fase 5:

```powershell
# Fase 9 — reparo via IA (requer LM Studio na porta 1234)
python ".\9_reparo_de_traducao\repara_erros_traducao.py" "<legendas_eng>" "<legendas_ptbr>"
python ".\9_reparo_de_traducao\limpa_erros_residuais.py" "<legendas_eng>" "<legendas_ptbr>"   # falhas persistentes (sem IA)

# Fase 10 — correção 100% offline (especializada para Guilty Crown)
python ".\10_correcao_guilty_crown\corrigir_guilty_crown.py"
python ".\10_correcao_guilty_crown\corrigir_cores_musicas.py"
```

[Fase 9](modulo-fase-9.md) · [Fase 10](modulo-fase-10.md)

---

## Fases auxiliares (pós-remux, opcionais)

```powershell
# Fase 6 — sincronização (corrige drift de áudio/legenda)
python ".\6_sincronizacao_legenda\auditor_sicronia\auditor_sincronia.py"
python ".\6_sincronizacao_legenda\subtitle_fixer.py"

# Fase 7 — otimização de vídeo (HEVC/NVENC)
python ".\7_decodificador\gpu_video_optimizer.py"
```

[Fase 6](modulo-fase-6.md) · [Fase 7](modulo-fase-7.md)

---

## Layout de pastas

### Esteira A/D — Episódios MKV

```text
C:\TRACKER-ANIMES\animes\Macross Delta\
├── episodio_01.mkv
├── traducao\              ← Fase 4
│   └── episodio_01_PTBR.ass
└── mkv_final_ptbr\        ← Fase 5
    └── episodio_01_PTBR.mkv
```

### Esteira B — Filme / SRT externo

```text
C:\TRACKER-ANIMES\animes\md-2\
├── filme.mkv
├── legenda\
│   ├── filme-en.srt
│   └── filme_PTBR.srt     ← Fase 4
├── traducao\
│   └── filme_PTBR.ass     ← Fase 3
└── mkv_final_ptbr\
    └── filme_PTBR.mkv     ← Fase 5
```

### Esteira C — PGS

```text
C:\TRACKER-ANIMES\animes\filme-bluray\
├── filme.mkv (PGS)
├── extraidos_sup\          ← Fase 2
│   └── filme.sup
├── legenda\
│   └── filme_PTBR.srt      ← OCR externo
├── traducao\
│   └── filme_PTBR.ass      ← Fase 3
└── mkv_final_ptbr\
    └── filme_PTBR.mkv      ← Fase 5
```

### Esteira E/F — Lote ASS (Gundam)

```text
C:\TRACKER-ANIMES\animes\Gundam Reconguista\
├── episodio_01.mkv
├── legendas_eng\           ← Fase 2
│   └── episodio_01_ENG.ass
├── traducao\               ← Fase 4
│   └── episodio_01_PTBR.ass
├── traducao_curada\        ← Fase 8 (apenas Esteira F, se necessário)
│   └── episodio_01_PTBR.ass
├── legendas_ptbr\          ← Fase 9 (opcional, reparo [ERRO_TRADUCAO:] via IA)
│   └── episodio_01_PTBR.ass
└── mkv_final_ptbr\         ← Fase 5
    └── episodio_01_PTBR.mkv
```

### Esteira G — Guilty Crown

```text
E:\animes\GUILTY CROWN\1080p\
├── episodio_01.mkv
├── legendas_eng\            ← Fase 2 + saída da Fase 4 (com [ERRO_TRADUCAO:])
│   └── episodio_01_ENG.ass
├── legendas_ptbr\           ← Fase 10a (corrigir_guilty_crown.py) e Fase 10b (cores OP/ED)
│   └── episodio_01_PTBR.ass
└── mkv_final_ptbr\          ← Fase 5
    └── episodio_01_PTBR.mkv
```

### Saídas auxiliares (Fases 6 e 7)

```text
C:\TRACKER-ANIMES\animes\<titulo>\
├── mkv_final_ptbr\
│   └── episodio_01_PTBR.mkv
└── otimizados\             ← Fase 7
    └── episodio_01_PTBR.mkv
```

---

[← Índice](README.md) · [Logs →](logs-e-auditoria.md)
