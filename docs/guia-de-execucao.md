# ▶️ Guia de execução

[← Índice](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/README.md) · [Instalação](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/instalacao.md) · [Arquitetura](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/arquitetura.md)

<p>
  <img src="https://img.shields.io/badge/Esteiras-A_a_N-9146FF?style=flat-square" alt="Esteiras A-N"/>
</p>

Comandos por esteira (A–N), na ordem de execução. Pré-requisitos detalhados em [instalacao.md](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/instalacao.md).

---

## Fase 01 — Auditoria (opcional, qualquer esteira)

```powershell
python ".\01_analisador_midia\media_analyzer.py" "C:\TRACKER-ANIMES\animes\Macross Delta"
```

**Saída:** `relatorio/{arquivo}_{timestamp}.txt` — [Detalhes](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-01.md)

---

## Esteira A — Eighty-Six, MKV (ASS embutido, inglês) — Fases 05a → [07] → 12 → [10]

```powershell
# Pré-requisito: LM Studio na porta 1234 (Gemma 4B)
python ".\05a_tradutor_llm_gemma4\86\sub_extractor.py"
python ".\07_higienizacao_e_reparo_de_traducao\86_Eighty_Six\limpeza_geral_86.py"   # opcional, normaliza lore/patentes
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
python ".\10_auditoria_e_revisao\revisao_86.py"          # opcional, corrige alucinações residuais + remux
```

| Item | Local |
|:---|:---|
| Entrada | Pasta com `.mkv` (legenda `S_TEXT/ASS` em inglês embutida) |
| Saída Fase 05a | `traducao\*_PTBR.ass` |
| Saída Fase 07 (opcional) | `legendas_ptbr\*_PTBR.ass` (ou atualizado em-place conforme o script) |
| Saída Fase 12 | `mkv_final_ptbr\*_PTBR.mkv` |
| Saída Fase 10 (opcional) | `corrigidos\*_PTBR.mkv` |

[Fase 05a](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-05a.md) · [Fase 07](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-07.md) · [Fase 12](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-12.md) · [Fase 10](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-10.md) · [Diagrama](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/arquitetura.md#esteira-a--eighty-six-ass-embutido-inglês)

---

## Esteira B — Filme / SRT externo (inglês) — Fases 05a → 04 → 12

Visão completa: [Pipeline SRT](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/pipeline-srt.md)

```powershell
# Pré-requisito: LM Studio na porta 1234
python ".\05a_tradutor_llm_gemma4\5_tradutor_de_legenda\tradutor_srt_direto.py"
python ".\04_conversor_srt_ass\conversor_srt_para_ass.py"
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
```

| Prompt | Exemplo |
|:---|:---|
| Pasta ou arquivo `.srt` (Fase 05a) | `C:\TRACKER-ANIMES\animes\md-2\legenda` |
| Tamanho do lote (Fase 05a) | ENTER = 20 |
| Pasta SRT `*_PTBR.srt` (Fase 04) | `...\md-2\legenda` |
| Pasta saída ASS (Fase 04) | `...\md-2\traducao` |
| Pasta `.mkv` / pasta `.ass` (Fase 12) | `...\md-2` / `...\md-2\traducao` |

[Fase 05a](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-05a.md#tradutor_srt_diretopy-srt-externo) · [Fase 04](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-04.md) · [Fase 12](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-12.md) · [Diagrama](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/arquitetura.md#esteira-b--filme-com-srt-externo-inglês)

---

## Esteira C — Legenda PGS (Blu-ray bitmap) — Fases 02 → OCR externo → 04 → 12

```powershell
python ".\02_extrator_legenda\extrator_inteligente_pgs.py"
# OCR externo (Subtitle Edit + Tesseract) -> *_PTBR.srt
python ".\04_conversor_srt_ass\conversor_srt_para_ass.py"
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
```

> O OCR `.sup → .srt` **não faz parte** deste repositório (use Subtitle Edit + Tesseract ou similar). Exemplo de título: Sword Art Online — Filme 2.

[Fase 02](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-02.md) · [Fase 04](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-04.md) · [Fase 12](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-12.md) · [Diagrama](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/arquitetura.md#esteira-c--legenda-pgs-bluray-bitmap)

---

## Esteira D — Macross Delta TV, MKV (ASS embutido, francês) — Fase 05b → [07] → 12 → [10]

```powershell
# Pré-requisito: LM Studio na porta 1234 com Mistral Nemo Instruct 2407 (GGUF) carregado
python ".\05b_tradutor_llm_mistral_nemo\frances_para_ptbr\macross_deslta.py"
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
python ".\10_auditoria_e_revisao\revisao_legenda_macross_delta.py"   # opcional, lore + tags ASS
```

Multi-thread (2 threads), glossário e cache persistente (`traducao_cache_fr.json`).

[Fase 05b](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-05b.md) · [Fase 07](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-07.md) · [Fase 12](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-12.md) · [Fase 10](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-10.md) · [Diagrama](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/arquitetura.md#esteira-d--macross-delta-tv-tradução-francês--pt-br)

---

## Esteira E — Macross Delta Filme 2 (francês) — Fase 05b → 07 → 10 → 12

```powershell
python ".\05b_tradutor_llm_mistral_nemo\frances_para_ptbr\macross_deslta.py"
python ".\07_higienizacao_e_reparo_de_traducao\Macross_Delta_Filme_2\limpeza_macross_filme2_extrema.py"
python ".\10_auditoria_e_revisao\micross_delta_filme2.py"
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
```

Mesmo motor da Esteira D, com higienização e revisão final dedicadas ao filme.

[Fase 05b](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-05b.md) · [Fase 07](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-07.md) · [Fase 10](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-10.md) · [Diagrama](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/arquitetura.md#esteira-e--macross-delta-filme-2-francês)

---

## Esteira F — Lote ASS pré-extraído (Gundam Reconguista) — Fases 02 → 05a → [07] → 12

```powershell
python ".\02_extrator_legenda\extrator_inteligente_ass.py"
python ".\05a_tradutor_llm_gemma4\tradutor_ass\batch_translator_ass.py"
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
```

[Fase 02](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-02.md) · [Fase 05a](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-05a.md) · [Fase 07](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-07.md) · [Fase 12](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-12.md) · [Diagrama](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/arquitetura.md#esteira-f--lote-ass-pré-extraído-gundam-reconguista)

---

## Esteira G — Gundam Unicorn (especializada) — Fases 02 → 05a → [06] → [07] → 12 → [10]

```powershell
python ".\02_extrator_legenda\extrator_inteligente_ass.py"
python ".\05a_tradutor_llm_gemma4\tradutor_gundam_unicornio\batch_translator_unicorn.py"
python ".\06_cura_legendas\cura_legendas_tag.py"          # se necessário (TAG corrompido)
python ".\07_higienizacao_e_reparo_de_traducao\Gundam_Unicorn\limpeza_geral_unicorn.py" # Higienização de lore
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
python ".\10_auditoria_e_revisao\revisao_legenda_gundam_unicornio.py"   # opcional, ep.1 + letras OP/ED + remux
```

[Fase 02](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-02.md) · [Fase 05a](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-05a.md) · [Fase 06](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-06.md) · [Fase 07](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-07.md) · [Fase 10](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-10.md) · [Fase 12](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-12.md) · [Diagrama](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/arquitetura.md#esteira-g--gundam-unicorn-especializada)

---

## Esteira H — Guilty Crown (correção de nomes e cores) — Fases 02 → 05a → [07] → 11 → 12 → [10]

```powershell
python ".\02_extrator_legenda\extrator_inteligente_ass.py"
python ".\05a_tradutor_llm_gemma4\tradutor_ass\batch_translator_ass.py"
python ".\11_correcao_projetos_legados\corrigir_guilty_crown.py"          # remove [ERRO_TRADUCAO:]
python ".\11_correcao_projetos_legados\corrigir_cores_musicas.py"         # cores/tags OP-ED
python ".\07_higienizacao_e_reparo_de_traducao\Guilty_Crown\limpeza_geral_guilty.py"     # Higienização de lore
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
python ".\10_auditoria_e_revisao\revisao_guild_crown.py"                  # opcional, diálogos + letras OP/ED + remux
```

| Prompt | Exemplo |
|:---|:---|
| Pasta com legendas + erros (`corrigir_guilty_crown.py`) | `E:\animes\GUILTY CROWN\1080p\legendas_eng` |
| Pasta de saída corrigida (`corrigir_guilty_crown.py`) | `E:\animes\GUILTY CROWN\1080p\legendas_ptbr` |
| Pasta com legendas PT-BR (`corrigir_cores_musicas.py`) | `E:\animes\GUILTY CROWN\1080p\legendas_ptbr` |

[Fase 02](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-02.md) · [Fase 05a](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-05a.md) · [Fase 07](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-07.md) · [Fase 11](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-11.md) · [Fase 10](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-10.md) · [Fase 12](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-12.md) · [Diagrama](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/arquitetura.md#esteira-h--guilty-crown-correção-de-nomes-e-cores-de-músicas)

---

## Esteira I — Gundam The Origin, legenda chinesa (CHS, Qwen2.5) — Fases 02 → 05c → [07] → 12 → [10]

```powershell
python ".\02_extrator_legenda\extrator_inteligente_ass.py"
# Pré-requisito: LM Studio na porta 1234 com Qwen2.5-7B-Instruct carregado
python ".\05c_tradutor_llm_qwen2\batch_translator_origin_zh.py" --entrada "<pasta_chs_ass>" --saida "<pasta_saida>"
python ".\05c_tradutor_llm_qwen2\repara_erros_origin_zh.py" --originais "<pasta_chs_ass>" --traduzidas "<pasta_ptbr>"  # se necessário
python ".\07_higienizacao_e_reparo_de_traducao\Gundam_The_Origin\limpeza_geral_origin.py" # Higienização de lore
python ".\10_auditoria_e_revisao\revisao_legenda_origin.py"        # opcional, lore + cache + remux
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
```

[Fase 02](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-02.md) · [Fase 05c](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-05c.md) · [Fase 07](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-07.md) · [Fase 10](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-10.md) · [Fase 12](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-12.md) · [Diagrama](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/arquitetura.md#esteira-i--gundam-the-origin-legenda-chinesa-chs)

---

## Esteira J — Gundam Origin, legenda francesa (SUBFRENCH) — Fase 05b → [07] → 12

```powershell
# Pré-requisito: LM Studio na porta 1234 com Mistral Nemo Instruct 2407 (GGUF) carregado
python ".\05b_tradutor_llm_mistral_nemo\frances_para_ptbr\script_tradutor_fr_gundam_origin.py"
# Executando refino de concordância via cache francês
python ".\07_higienizacao_e_reparo_de_traducao\refino_frances_origin\refina_traducao_fr.py"
# Higienização de lore e barras
python ".\07_higienizacao_e_reparo_de_traducao\Gundam_Origin\limpeza_origin_total.py"
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
```

Rota alternativa para Gundam Origin quando o release disponível tem legenda francesa embutida em vez da chinesa (Esteira I). Mesmo glossário Universal Century usado nas Esteiras F/G, adaptado para francês.

[Fase 05b](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-05b.md) · [Fase 07](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-07.md) · [Fase 12](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-12.md) · [Diagrama](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/arquitetura.md#esteira-j--gundam-origin-legenda-francesa-subfrench)

---

## Esteira K — Gundam Zeta (TranslateGemma) — Fase 05c-2 → [07] → 12

```powershell
# Pré-requisito: LM Studio na porta 1234 com TranslateGemma 12B carregado
python ".\05c_tradutor_llm_translategemma\Gundam_Zeta\script_tradutor_en_gundam_zeta.py"
python ".\07_higienizacao_e_reparo_de_traducao\Gundam_Zeta\limpeza_zeta_extrema.py"
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
```

[Fase 05c-2](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-05c2.md) · [Fase 07](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-07.md) · [Fase 12](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-12.md) · [Diagrama](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/arquitetura.md#esteira-k--gundam-zeta)

---

## Esteira L — Gundam ZZ (TranslateGemma) — Fase 05c-2 → [07] → 12

```powershell
# Pré-requisito: LM Studio na porta 1234 com TranslateGemma 12B carregado
python ".\05c_tradutor_llm_translategemma\Gundam_ZZ\script_tradutor_en_gundam_zz.py"
# Se necessário reparar falhas com marcas [ERRO_TRADUCAO:]
python ".\07_higienizacao_e_reparo_de_traducao\repara_erros_traducao.py" "<legendas_eng>" "<legendas_ptbr>"
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
```

Sem script de higienização de lore dedicado ainda (título mais recente do pipeline).

[Fase 05c-2](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-05c2.md) · [Fase 07](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-07.md) · [Fase 12](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-12.md) · [Diagrama](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/arquitetura.md#esteira-l--gundam-zz)

---

## Esteira M — Detonator Orgun (Mistral Nemo, inglês) — Fase 05b → [07] → 12

```powershell
# Pré-requisito: LM Studio na porta 1234 com Mistral Nemo Instruct 2407 (GGUF) carregado
python ".\05b_tradutor_llm_mistral_nemo\Detonator_Orgun\script_tradutor_en_detonator_orgun.py"
python ".\07_higienizacao_e_reparo_de_traducao\Detonator_Orgun\limpeza_geral_orgun.py"
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
```

[Fase 05b](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-05b.md) · [Fase 07](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-07.md) · [Fase 12](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-12.md) · [Diagrama](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/arquitetura.md#esteira-m--detonator-orgun)

---

## Esteira N — Knights of Sidonia — Fases 02 → 05a → [07] → 12

```powershell
python ".\02_extrator_legenda\extrator_inteligente_ass.py"
python ".\05a_tradutor_llm_gemma4\tradutor_ass\batch_translator_sidonia.py"
python ".\07_higienizacao_e_reparo_de_traducao\Knights_of_Sidonia\limpeza_sidonia_extrema.py"
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
```

[Fase 02](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-02.md) · [Fase 05a](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-05a.md) · [Fase 07](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-07.md) · [Fase 12](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-12.md) · [Diagrama](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/arquitetura.md#esteira-n--knights-of-sidonia)

---

## Pós-processamento — Reparos e Higienização (Fase 07 e 11, opcionais)

Quando a Fase 05a/05b/05c deixa marcadores `[ERRO_TRADUCAO: <texto>]` ou necessita de higienização de lore e padronização, execute **antes** da Fase 12:

```powershell
# Fase 07 — reparo via IA (requer LM Studio na porta 1234)
python ".\07_higienizacao_e_reparo_de_traducao\repara_erros_traducao.py" "<legendas_eng>" "<legendas_ptbr>"
python ".\07_higienizacao_e_reparo_de_traducao\limpa_erros_residuais.py" "<legendas_eng>" "<legendas_ptbr>"   # falhas persistentes (sem IA)

# Fase 07 — refino de francês (engenharia reversa do cache, Gundam Origin/Macross Delta)
python ".\07_higienizacao_e_reparo_de_traducao\refino_frances_origin\refina_traducao_fr.py"

# Fase 07 — normalização de lore/gramática por título (roda sobre o .ass já traduzido)
python ".\07_higienizacao_e_reparo_de_traducao\86_Eighty_Six\limpeza_geral_86.py"
python ".\07_higienizacao_e_reparo_de_traducao\Gundam_Unicorn\limpeza_geral_unicorn.py"
python ".\07_higienizacao_e_reparo_de_traducao\Gundam_Zeta\limpeza_zeta_extrema.py"
# ... um script por título, ver modulo-fase-07.md para a lista completa

# Fase 11 — correção 100% offline (especializada para Guilty Crown)
python ".\11_correcao_projetos_legados\corrigir_guilty_crown.py"
python ".\11_correcao_projetos_legados\corrigir_cores_musicas.py"

# Fase 05c — reparo via IA/Qwen2.5 (requer LM Studio na porta 1234, Gundam The Origin chinês)
python ".\05c_tradutor_llm_qwen2\repara_erros_origin_zh.py" --originais "<chs_ass>" --traduzidas "<ptbr>"
```

[Fase 07](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-07.md) · [Fase 11](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-11.md) · [Fase 05c](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-05c.md)

---

## Pós-processamento — Revisão final e Remux (Fase 10, opcional)

Após a tradução e higienização, ou como etapa de QA dedicada:

```powershell
# Fase 10 — revisão final + remux opcional
python ".\10_auditoria_e_revisao\revisao_legenda_origin.py"               # Gundam The Origin (Esteira I)
python ".\10_auditoria_e_revisao\revisao_guild_crown.py"                   # Guilty Crown (Esteira H)
python ".\10_auditoria_e_revisao\revisao_legenda_gundam_unicornio.py"      # Gundam Unicorn (Esteira G)
python ".\10_auditoria_e_revisao\revisao_legenda_macross_delta.py"         # Macross Delta TV (Esteira D)
python ".\10_auditoria_e_revisao\micross_delta_filme2.py"                  # Macross Delta Filme 2 (Esteira E)
python ".\10_auditoria_e_revisao\revisao_86.py"                            # Eighty-Six (Esteira A)
```

[Fase 10](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-10.md)

---

## Fases auxiliares (pós-remux, opcionais)

```powershell
# Fase 08 — sincronização (corrige drift de áudio/legenda)
python ".\08_sincronizacao_legenda\auditor_sicronia\auditor_sincronia.py"
python ".\08_sincronizacao_legenda\subtitle_fixer.py"

# Fase 03 — otimização de vídeo (HEVC/NVENC)
python ".\03_decodificador_caracteres\gpu_video_optimizer.py"

# Fase 09 — injeção de karaokê OP/ED/Insert Songs (de fansub para a faixa oficial)
python ".\09_injetor_musicas\injetor_de_musicas.py"
```

[Fase 08](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-08.md) · [Fase 03](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-03.md) · [Fase 09](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-09.md)

---

## Layout de pastas

### Esteira A/D — Episódios MKV

```text
C:\TRACKER-ANIMES\animes\Macross Delta\
├── episodio_01.mkv
├── traducao\              ← Fase 05a/05b
│   └── episodio_01_PTBR.ass
└── mkv_final_ptbr\        ← Fase 12
    └── episodio_01_PTBR.mkv
```

### Esteira B — Filme / SRT externo

```text
C:\TRACKER-ANIMES\animes\md-2\
├── filme.mkv
├── legenda\
│   ├── filme-en.srt
│   └── filme_PTBR.srt     ← Fase 05a
├── traducao\
│   └── filme_PTBR.ass     ← Fase 04
└── mkv_final_ptbr\
    └── filme_PTBR.mkv     ← Fase 12
```

### Esteira C — PGS

```text
C:\TRACKER-ANIMES\animes\filme-bluray\
├── filme.mkv (PGS)
├── extraidos_sup\          ← Fase 02
│   └── filme.sup
├── legenda\
│   └── filme_PTBR.srt      ← OCR externo
├── traducao\
│   └── filme_PTBR.ass      ← Fase 04
└── mkv_final_ptbr\
    └── filme_PTBR.mkv      ← Fase 12
```

### Esteira F/G — Lote ASS (Gundam)

```text
C:\TRACKER-ANIMES\animes\Gundam Reconguista\
├── episodio_01.mkv
├── legendas_eng\           ← Fase 02
│   └── episodio_01_ENG.ass
├── traducao\               ← Fase 05a
│   └── episodio_01_PTBR.ass
├── traducao_curada\        ← Fase 06 (apenas Esteira G, se necessário)
│   └── episodio_01_PTBR.ass
├── legendas_ptbr\          ← Fase 07 (higienização de lore + reparo [ERRO_TRADUCAO:] via IA)
│   └── episodio_01_PTBR.ass
├── corrigidos\              ← Fase 10 (revisao_legenda_gundam_unicornio.py), se remux habilitado
│   └── episodio_01_PTBR.mkv
└── mkv_final_ptbr\         ← Fase 12
    └── episodio_01_PTBR.mkv
```

### Esteira H — Guilty Crown

```text
E:\animes\GUILTY CROWN\1080p\
├── episodio_01.mkv
├── legendas_eng\            ← Fase 02 + saída da Fase 05a (com [ERRO_TRADUCAO:])
│   └── episodio_01_ENG.ass
├── legendas_ptbr\           ← Fase 11a (corrigir_guilty_crown.py), Fase 11b (cores OP/ED) e Fase 07 (limpeza_geral_guilty.py)
│   └── episodio_01_PTBR.ass
├── corrigidos\              ← Fase 10 (revisao_guild_crown.py), se remux habilitado
│   └── episodio_01_PTBR.mkv
└── mkv_final_ptbr\          ← Fase 12
    └── episodio_01_PTBR.mkv
```

### Esteira I — Gundam The Origin (legenda chinesa, Qwen2.5)

```text
C:\TRACKER-ANIMES\animes\Gundam Origin (POPGO)\
├── episodio_01.mkv
├── episodio_01.chs.ass      ← Fase 02 (extrator_inteligente_ass.py)
├── legendas_ptbr\           ← Fase 05c (batch_translator_origin_zh.py / repara_erros_origin_zh.py) e Fase 07 (limpeza_geral_origin.py)
│   └── episodio_01_PTBR.ass
├── corrigidos\              ← Fase 10 (revisao_legenda_origin.py), se remux habilitado
│   └── episodio_01_PTBR.mkv
└── mkv_final_ptbr\          ← Fase 12
    └── episodio_01_PTBR.mkv
```

### Saídas auxiliares (Fases 03 e 08)

```text
C:\TRACKER-ANIMES\animes\<titulo>\
├── mkv_final_ptbr\
│   └── episodio_01_PTBR.mkv
└── otimizados\             ← Fase 03
    └── episodio_01_PTBR.mkv
```

---

[← Índice](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/README.md) · [Logs →](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/logs-e-auditoria.md)
