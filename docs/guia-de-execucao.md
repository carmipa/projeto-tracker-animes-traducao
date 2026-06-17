# ▶️ Guia de execução

[← Índice](README.md) · [Instalação](instalacao.md) · [Arquitetura](arquitetura.md)

<p>
  <img src="https://img.shields.io/badge/Esteiras-A_a_I-9146FF?style=flat-square" alt="Esteiras A-I"/>
</p>

Comandos por esteira (A–I), na ordem de execução. Pré-requisitos detalhados em [instalacao.md](instalacao.md).

---

## Fase 1 — Auditoria (opcional, qualquer esteira)

```powershell
python ".\1_analisador_de_midia\media_analyzer.py" "C:\TRACKER-ANIMES\animes\Macross Delta"
```

**Saída:** `relatorio/{arquivo}_{timestamp}.txt` — [Detalhes](modulo-fase-1.md)

---

## Esteira A — Eighty-Six, MKV (ASS embutido, inglês) — Fases 4 → [12] → 5

```powershell
# Pré-requisito: LM Studio na porta 1234 (Gemma 4B)
python ".\4_tradutor_ia_gemma4\86\sub_extractor.py"
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
python ".\12_revisao_legenda\revisao_86.py"          # opcional, corrige alucinações residuais + remux
```

| Item | Local |
|:---|:---|
| Entrada | Pasta com `.mkv` (legenda `S_TEXT/ASS` em inglês embutida) |
| Saída Fase 4 | `traducao\*_PTBR.ass` |
| Saída Fase 5 | `mkv_final_ptbr\*_PTBR.mkv` |
| Saída Fase 12 (opcional) | `corrigidos\*_PTBR.mkv` |

[Fase 4](modulo-fase-4.md) · [Fase 5](modulo-fase-5.md) · [Fase 12](modulo-fase-12.md) · [Diagrama](arquitetura.md#esteira-a--episódio-mkv-com-ass-embutido-inglês)

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

[Fase 4 (item 4)](modulo-fase-4.md#4--tradutor_srt_diretopy-srt-externo) · [Fase 3](modulo-fase-3.md) · [Fase 5](modulo-fase-5.md) · [Diagrama](arquitetura.md#esteira-b--filme-com-srt-externo-inglês)

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

## Esteira D — Macross Delta, MKV (ASS embutido, francês) — Fase 4-B → [12] → 5

```powershell
# Pré-requisito: LM Studio na porta 1234 com Mistral Nemo Instruct 2407 (GGUF) carregado
python ".\4_b_mistrall_nemo_instruct_2407_GGUF_tradutor\frances_para_ptbr\macross_deslta.py"
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
python ".\12_revisao_legenda\revisao_legenda_macross_delta.py"   # opcional, lore + tags ASS
```

Multi-thread (2 threads), glossário e cache persistente (`traducao_cache_fr.json`). Filme avulso (Macross Delta — Filme 2): mesmos passos, revisão final com `12_revisao_legenda\micross_delta_filme2.py`.

[Fase 4-B](modulo-fase-4b.md) · [Fase 5](modulo-fase-5.md) · [Fase 12](modulo-fase-12.md) · [Diagrama](arquitetura.md#esteira-d--macross-delta-tradução-francês--pt-br-multi-thread)

---

## Esteira I — Gundam Origin, MKV (ASS embutido, francês — SUBFRENCH) — Fase 4-B → 5

```powershell
# Pré-requisito: LM Studio na porta 1234 com Mistral Nemo Instruct 2407 (GGUF) carregado
python ".\4_b_mistrall_nemo_instruct_2407_GGUF_tradutor\frances_para_ptbr\script_tradutor_fr_gundam_origin.py"
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
```

Rota alternativa para Gundam Origin quando o release disponível tem legenda francesa embutida em vez da chinesa (Esteira H). Mesmo glossário Universal Century usado na Esteira F/E, adaptado para francês.

[Fase 4-B](modulo-fase-4b.md) · [Fase 5](modulo-fase-5.md) · [Diagrama](arquitetura.md#esteira-i--gundam-origin-legenda-francesa-subfrench)

---

## Esteira E — Lote ASS pré-extraído (Gundam Reconguista) — Fases 2 → 4 → 5

```powershell
python ".\2_extrator_legenda\extrator_inteligente_ass.py"
python ".\4_tradutor_ia_gemma4\tradutor_ass\batch_translator_ass.py"
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
```

[Fase 2](modulo-fase-2.md) · [Fase 4 (item 2)](modulo-fase-4.md) · [Fase 5](modulo-fase-5.md) · [Diagrama](arquitetura.md#esteira-e--lote-ass-pré-extraído-gundam-reconguista)

---

## Esteira F — Gundam Unicorn (especializada) — Fases 2 → 4 → 8 → [12] → 5

```powershell
python ".\2_extrator_legenda\extrator_inteligente_ass.py"
python ".\4_tradutor_ia_gemma4\tradutor_gundam_unicornio\batch_translator_unicorn.py"
python ".\8_cura_legendas\cura_legendas_tag.py"          # se necessário (TAG corrompido)
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
python ".\12_revisao_legenda\revisao_legenda_gundam_unicornio.py"   # opcional, ep.1 + letras OP/ED + remux
```

[Fase 2](modulo-fase-2.md) · [Fase 4 (item 3)](modulo-fase-4.md) · [Fase 8](modulo-fase-8.md) · [Fase 12](modulo-fase-12.md) · [Fase 5](modulo-fase-5.md) · [Diagrama](arquitetura.md#esteira-f--gundam-unicorn-especializada)

---

## Esteira G — Guilty Crown (correção de nomes e cores) — Fases 2 → 4 → 10 → [12] → 5

```powershell
python ".\2_extrator_legenda\extrator_inteligente_ass.py"
python ".\4_tradutor_ia_gemma4\tradutor_ass\batch_translator_ass.py"   # ou variante adequada
python ".\10_correcao_guilty_crown\corrigir_guilty_crown.py"           # remove [ERRO_TRADUCAO:]
python ".\10_correcao_guilty_crown\corrigir_cores_musicas.py"          # cores/tags OP-ED
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
python ".\12_revisao_legenda\revisao_guild_crown.py"                   # opcional, diálogos + letras OP/ED + remux
```

| Prompt | Exemplo |
|:---|:---|
| Pasta com legendas + erros (`corrigir_guilty_crown.py`) | `E:\animes\GUILTY CROWN\1080p\legendas_eng` |
| Pasta de saída corrigida (`corrigir_guilty_crown.py`) | `E:\animes\GUILTY CROWN\1080p\legendas_ptbr` |
| Pasta com legendas PT-BR (`corrigir_cores_musicas.py`) | `E:\animes\GUILTY CROWN\1080p\legendas_ptbr` |

[Fase 2](modulo-fase-2.md) · [Fase 4](modulo-fase-4.md) · [Fase 10](modulo-fase-10.md) · [Fase 12](modulo-fase-12.md) · [Fase 5](modulo-fase-5.md) · [Diagrama](arquitetura.md#esteira-g--guilty-crown-correção-de-nomes-e-cores-de-músicas)

---

## Esteira H — Gundam Origin, legenda chinesa (CHS, Qwen2.5) — Fases 2 → 11 → [12] → 5

```powershell
python ".\2_extrator_legenda\extrator_inteligente_ass.py"
# Pré-requisito: LM Studio na porta 1234 com Qwen2.5-7B-Instruct carregado
python ".\11_chines_LLM_alibaba_qwen2\batch_translator_origin_zh.py" --entrada "<pasta_chs_ass>" --saida "<pasta_saida>"
python ".\11_chines_LLM_alibaba_qwen2\repara_erros_origin_zh.py" --originais "<pasta_chs_ass>" --traduzidas "<pasta_ptbr>"  # se necessário
python ".\12_revisao_legenda\revisao_legenda_origin.py"        # opcional, lore + cache + remux
python ".\5_juntar_legendas_filmes\batch_remuxer.py"
```

[Fase 2](modulo-fase-2.md) · [Fase 11](modulo-fase-11.md) · [Fase 12](modulo-fase-12.md) · [Fase 5](modulo-fase-5.md) · [Diagrama](arquitetura.md#esteira-h--gundam-origin-legenda-chinesa-chs-qwen25)

---

## Pós-processamento — Reparo de `[ERRO_TRADUCAO:]` (Fases 9, 10 e 11, opcionais)

Quando a **Fase 4/11** deixa marcadores `[ERRO_TRADUCAO: <texto>]` em `traducao\*_PTBR.ass`, rode **antes** da Fase 5:

```powershell
# Fase 9 — reparo via IA/Gemma (requer LM Studio na porta 1234)
python ".\9_reparo_de_traducao\repara_erros_traducao.py" "<legendas_eng>" "<legendas_ptbr>"
python ".\9_reparo_de_traducao\limpa_erros_residuais.py" "<legendas_eng>" "<legendas_ptbr>"   # falhas persistentes (sem IA)

# Fase 10 — correção 100% offline (especializada para Guilty Crown)
python ".\10_correcao_guilty_crown\corrigir_guilty_crown.py"
python ".\10_correcao_guilty_crown\corrigir_cores_musicas.py"

# Fase 11 — reparo via IA/Qwen2.5 (requer LM Studio na porta 1234, Gundam Origin chinês)
python ".\11_chines_LLM_alibaba_qwen2\repara_erros_origin_zh.py" --originais "<chs_ass>" --traduzidas "<ptbr>"
```

[Fase 9](modulo-fase-9.md) · [Fase 10](modulo-fase-10.md) · [Fase 11](modulo-fase-11.md)

---

## Pós-processamento — Revisão final por título (Fase 12, opcional)

Depois do remux (ou antes dele, se o script oferecer remux próprio), rode o patch de QA do título correspondente:

```powershell
python ".\12_revisao_legenda\revisao_legenda_origin.py"               # Gundam Origin (Esteira H)
python ".\12_revisao_legenda\revisao_guild_crown.py"                   # Guilty Crown (Esteira G)
python ".\12_revisao_legenda\revisao_legenda_gundam_unicornio.py"      # Gundam Unicorn (Esteira F)
python ".\12_revisao_legenda\revisao_legenda_macross_delta.py"         # Macross Delta TV (Esteira D)
python ".\12_revisao_legenda\micross_delta_filme2.py"                  # Macross Delta Filme 2
python ".\12_revisao_legenda\revisao_86.py"                            # Eighty-Six (Esteira A)
```

[Fase 12](modulo-fase-12.md)

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
├── corrigidos\             ← Fase 12 (revisao_legenda_gundam_unicornio.py), se remux habilitado
│   └── episodio_01_PTBR.mkv
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
├── corrigidos\              ← Fase 12 (revisao_guild_crown.py), se remux habilitado
│   └── episodio_01_PTBR.mkv
└── mkv_final_ptbr\          ← Fase 5
    └── episodio_01_PTBR.mkv
```

### Esteira H — Gundam Origin (legenda chinesa, Qwen2.5)

```text
C:\TRACKER-ANIMES\animes\Gundam Origin (POPGO)\
├── episodio_01.mkv
├── episodio_01.chs.ass      ← Fase 2 (extrator_inteligente_ass.py)
├── legendas_ptbr\           ← Fase 11 (batch_translator_origin_zh.py / repara_erros_origin_zh.py)
│   └── episodio_01_PTBR.ass
├── corrigidos\              ← Fase 12 (revisao_legenda_origin.py), se remux habilitado
│   └── episodio_01_PTBR.mkv
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
