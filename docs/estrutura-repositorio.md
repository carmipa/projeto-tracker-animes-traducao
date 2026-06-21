# 📦 Estrutura do repositório

[← Índice](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/README.md)

```text
projeto-tracker-animes-traducao/
├── README.md
├── icone.png
├── requirements.txt
├── LICENSE
│
├── docs/                                  ← documentação
│   ├── README.md
│   ├── arquitetura.md                     ← visão geral + diagramas de todas as esteiras
│   ├── estrutura-repositorio.md           ← este arquivo
│   ├── pipeline-srt.md                    ← Esteira B (filme / SRT externo)
│   ├── modulo-fase-01.md … modulo-fase-12.md
│   ├── instalacao.md
│   ├── dependencias-python.md
│   ├── guia-de-execucao.md
│   ├── logs-e-auditoria.md
│   └── solucao-de-problemas.md
│
├── 01_analisador_midia/                    # Fase 01 — Análise e Auditoria de Mídia
│   ├── media_analyzer.py
│   └── relatorio/                          # saída: relatórios *.txt por título/execução
│
├── 02_extrator_legenda/                    # Fase 02 — Extração de Legendas (ASS, SRT, PGS)
│   ├── extrator_inteligente_ass.py         # -> legendas_eng/*_ENG.ass
│   ├── extrator_inteligente_srt.py         # -> legendas_eng/*_ENG.srt
│   ├── extrator_inteligente_pgs.py         # -> extraidos_sup/*.sup
│   ├── extrator_texto_bruto/
│   │   └── extrator_texto_bruto.py         # utilitário: dump numerado do roteiro p/ revisão manual
│   ├── por_tipo/                           # resíduo de execução antiga (apenas info.txt)
│   └── info.txt                            # log de auditoria das extrações
│
├── 03_decodificador_caracteres/            # Fase 03 — Otimização de vídeo (GPU, auxiliar)
│   ├── gpu_video_optimizer.py              # recomprime para HEVC/NVENC -> otimizados/*.mkv
│   └── optimizer_log.txt
│
├── 04_conversor_srt_ass/                   # Fase 04 — Conversor SRT → ASS (sync FPS)
│   ├── conversor_srt_para_ass.py
│   └── verificador.py                      # placeholder (sem docstring)
│
├── 05a_tradutor_llm_gemma4/                 # Fase 05a — Tradução via LM Studio + Gemma 4B
│   ├── 86/
│   │   ├── sub_extractor.py                # MKV (EN) -> traducao/*_PTBR.ass — Eighty-Six (Esteira A)
│   │   ├── traducao_cache_86.json
│   │   └── logs/                           # pipeline_86_*, config_86_*, erros_86_*, stats_86_*
│   ├── 5_tradutor_de_legenda/
│   │   ├── tradutor_srt_direto.py          # *.srt (EN) -> *_PTBR.srt — Esteira B (filme)
│   │   └── logs/                           # pipeline_direct_srt_*
│   ├── chines_para_pt_br/                  # residual — sem scripts (apenas __pycache__)
│   ├── logs/                               # logs herdados (config_*, erros_*, pipeline_*, stats_*; alguns "_fr_" anteriores à migração p/ Fase 05b)
│   ├── tradutor_ass/
│   │   ├── batch_translator_ass.py         # *_ENG.ass -> *_PTBR.ass (lote, Gundam Reconguista — Esteira F)
│   │   ├── batch_translator_sidonia.py     # *_ENG.ass -> *_PTBR.ass (lote, Knights of Sidonia — Esteira N)
│   │   ├── info_traducao_ass.txt
│   │   ├── info_traducao_sidonia_ass.txt
│   │   └── debug_last_failure_sidonia_ass.txt
│   └── tradutor_gundam_unicornio/
│       ├── batch_translator_unicorn.py     # *_ENG.ass -> *_PTBR.ass (lote, Gundam Unicorn — Esteira G)
│       ├── info.txt
│       └── debug_last_failure.txt
│
├── 05b_tradutor_llm_mistral_nemo/           # Fase 05b — Tradução via LM Studio + Mistral Nemo Instruct 2407 (GGUF)
│   ├── Detonator_Orgun/
│   │   ├── script_tradutor_en_detonator_orgun.py  # MKV/SRT (EN) -> PT-BR — Esteira M
│   │   ├── traducao_cache_orgun_en.json
│   │   └── logs/                           # pipeline_en_orgun_*, erros_en_orgun_*, stats_en_orgun_*
│   └── frances_para_ptbr/
│       ├── macross_deslta.py               # MKV (FR) -> traducao/*_PTBR.ass — Macross Delta TV (Esteira D)
│       ├── script_tradutor_fr_gundam_origin.py  # MKV (FR, SUBFRENCH) -> traducao/*_PTBR.ass — Gundam Origin (Esteira J)
│       ├── traducao_cache_fr.json
│       └── logs/                           # pipeline_fr_*, erros_fr_*, config_fr_*, stats_fr_*, traducoes_detalhadas_fr_*
│
├── 05c_tradutor_llm_qwen2/                  # Fase 05c — Tradução via LM Studio + Qwen2.5-7B-Instruct (chinês)
│   ├── batch_translator_origin_zh.py       # *.chs.ass -> *_PTBR.ass (lote, Gundam The Origin — Esteira I)
│   ├── repara_erros_origin_zh.py           # retraduz avulso (batch=1) [ERRO_TRADUCAO:]
│   ├── test_reparo.py                      # utilitário de depuração manual (fora do pipeline)
│   ├── traducao_cache_origin_zh.json       # cache persistente (+ .json.bak)
│   ├── info.txt                            # métricas por arquivo (último lote)
│   ├── debug_last_failure.txt              # debug da última falha de lote
│   ├── debug_test.txt                      # recriado a cada execução de test_reparo.py
│   └── relatorio_reparo_origin_zh.txt      # relatório do reparo avulso
│
├── 05c_tradutor_llm_translategemma/         # Fase 05c-2 — Tradução/revisão via LM Studio + TranslateGemma 12B
│   ├── Gundam_Origin/
│   │   └── script_revisor_ptbr_gundam_origin.py  # revisão gramatical de PT-BR já traduzido (corretor ortográfico)
│   ├── Gundam_ZZ/
│   │   ├── script_tradutor_en_gundam_zz.py # MKV (EN) -> PT-BR — Gundam ZZ (Esteira L)
│   │   ├── traducao_cache_gundam_zz_en.json
│   │   └── logs/stats_en_gundam_zz_*.json
│   └── Gundam_Zeta/
│       ├── script_tradutor_en_gundam_zeta.py  # MKV (EN) -> PT-BR — Gundam Zeta (Esteira K)
│       ├── traducao_cache_gundam_zeta_en.json
│       └── logs/stats_en_gundam_zeta_*.json
│
├── 06_cura_legendas/                        # Fase 06 — Cura de legendas (auxiliar)
│   ├── cura_gundam_mkv.py                  # repara TAG corrompido em .mkv já remuxado (Gundam Unicorn)
│   └── cura_legendas_tag.py                # repara TAG via casamento ENG/PTBR -> traducao_curada/
│
├── 07_higienizacao_e_reparo_de_traducao/    # Fase 07 — Higienização por título + Reparo de tradução
│   ├── 86_Eighty_Six/
│   │   ├── audit_86.py                     # auditoria de patentes/jargões de 86
│   │   └── limpeza_geral_86.py             # normalização de termos de lore
│   ├── Detonator_Orgun/limpeza_geral_orgun.py
│   ├── Guilty_Crown/limpeza_geral_guilty.py
│   ├── Gundam_Origin/                      # 4 scripts — pipeline francês (Esteira J)
│   │   ├── limpeza_origin_extrema.py
│   │   ├── limpeza_origin_finais.py        # correção de barra \N mal formatada
│   │   ├── limpeza_origin_gramatica_profunda.py # dicionário contextual FR→PT-BR
│   │   └── limpeza_origin_total.py         # francesismos & vocabulário
│   ├── Gundam_The_Origin/limpeza_geral_origin.py # pipeline chinês (Esteira I)
│   ├── Gundam_Unicorn/limpeza_geral_unicorn.py
│   ├── Gundam_Zeta/limpeza_zeta_extrema.py
│   ├── Knights_of_Sidonia/limpeza_sidonia_extrema.py
│   ├── Macross_Delta/limpeza_geral_macross.py
│   ├── Macross_Delta_Filme_1/limpeza_macross_filme1_extrema.py
│   ├── Macross_Delta_Filme_2/limpeza_macross_filme2_extrema.py
│   ├── Sword_Art_Online_Filme_2/limpeza_sao_filme2_extrema.py
│   ├── refino_frances_origin/              # scripts de refino de tradução francesa
│   │   ├── aplica_linhas_revisadas.py
│   │   ├── extrai_linhas_suspeitas.py
│   │   └── refina_traducao_fr.py
│   ├── limpa_erros_residuais.py            # limpeza offline rápida de falhas
│   ├── relatorio_reparo.txt                # relatório da última execução de reparo
│   └── repara_erros_traducao.py            # reparo de erros via IA (LM Studio)
│
├── 08_sincronizacao_legenda/                 # Fase 08 — Sincronização (auxiliar)
│   ├── subtitle_fixer.py                   # shift de legenda embutida no .mkv (FFprobe)
│   ├── subtitle_stretcher.py               # time-stretch + offset em .srt/.ass
│   └── auditor_sicronia/
│       └── auditor_sincronia.py            # audita drift via FFprobe
│
├── 09_injetor_musicas/                      # Fase 09 — Injetor de músicas (karaokê)
│   └── injetor_de_musicas.py               # extrai OP/ED/Insert Songs de fansub e injeta na legenda oficial
│
├── 10_auditoria_e_revisao/                  # Fase 10 — Revisão/correção final por título (QA + remux opcional)
│   ├── revisao_legenda_origin.py           # Gundam The Origin (Esteira I) — lore + cache + remux
│   ├── revisao_guild_crown.py              # Guilty Crown (Esteira H) — diálogos + letras OP/ED + remux
│   ├── revisao_legenda_gundam_unicornio.py # Gundam Unicorn (Esteira G) — ep.1 + letras OP/ED + remux
│   ├── revisao_legenda_macross_delta.py    # Macross Delta TV (Esteira D) — lore + tags ASS
│   ├── micross_delta_filme2.py             # Macross Delta Filme 2 (Esteira E) — lore + resíduos FR + remux
│   ├── revisao_86.py                       # Eighty-Six (Esteira A) — alucinações residuais + remux
│   └── _dialogos_eng_brutos.txt            # roteiro de referência (gerado por extrator_texto_bruto.py)
│
├── 11_correcao_projetos_legados/            # Fase 11 — Correção offline de cores/marcadores (Guilty Crown — Esteira H)
│   ├── corrigir_guilty_crown.py            # remove [ERRO_TRADUCAO:] -> legendas_ptbr/*_PTBR.ass
│   ├── corrigir_cores_musicas.py           # corrige cores/tags de músicas (OP/ED)
│   ├── relatorio_correcao.txt              # relatório de corrigir_guilty_crown.py
│   └── relatorio_cores_musicas.txt         # relatório de corrigir_cores_musicas.py
│
├── 12_remuxer_mkvmerge/                     # Fase 12 — Remuxer (MKVMerge)
│   ├── batch_remuxer.py                    # .mkv + traducao/*.ass -> mkv_final_ptbr/*_PTBR.mkv
│   └── logs/                               # resíduo de execuções antigas — ver nota abaixo
│
├── multiplexar/
│   └── logs/                                # logs reais de batch_remuxer.py (Fase 12): remux_pipeline_*, remux_config_*, remux_erros_*, remux_stats_*
│
└── legendas-traduzidas-ptbr/                 # saídas compartilháveis já finalizadas, por título
    ├── 86_ptbr/{temporada_1,temporada_2}/
    ├── Detonator_orgun_ptbr/
    ├── Guilty_Crown_ptbr/
    ├── Gundam_Origim_advent_of_the_red_comet_ptbr/
    ├── Gundam_Unicorn_Re0096_ptbr/
    ├── Gundam_Zeta_ptbr/
    ├── Kniigthts_of_sidonia_ptbr/{anime,filme}/
    ├── Macross_delta_anime_ptbr/
    └── SAO_filme_2_ptbr/
```

> As pastas de fase estão prefixadas `01` a `12` (com variantes `a`/`b`/`c` na Fase 05) seguindo a ordem descrita em [Arquitetura](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/arquitetura.md), o que também facilita a ordenação no explorador de arquivos do sistema.

---

## Nota — logs de remux duplicados (`12_remuxer_mkvmerge/logs/` vs `multiplexar/logs/`)

O `batch_remuxer.py` grava seus logs em `multiplexar/logs/` (caminho hardcoded no script, relativo à raiz do projeto — `self.pasta_logs = os.path.join(pasta_raiz_projeto, "multiplexar", "logs")`), **não** em `12_remuxer_mkvmerge/logs/`. A pasta `12_remuxer_mkvmerge/logs/` contém apenas registros residuais de execuções anteriores a uma reorganização de pastas e pode ser ignorada — a fonte de verdade para auditoria de remux é sempre `multiplexar/logs/`. Detalhes: [Logs e auditoria](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/logs-e-auditoria.md#fase-12--remuxer).

---

## Pastas de mídia do usuário (fora do repositório)

O pipeline opera sobre pastas de animes/filmes que ficam **fora** do repositório (ex.: `C:\TRACKER-ANIMES\animes\...`, ou em outros discos como `E:\animes\...`, conforme o título). Layout típico gerado durante o processamento:

```text
C:\TRACKER-ANIMES\animes\<titulo>\
├── episodio_01.mkv
├── legendas_eng\          ← saída da Fase 02 (também usada como entrada das Fases 07/11)
├── legenda\                ← entrada/saída SRT (Esteira B/C)
├── extraidos_sup\          ← saída da Fase 02 (PGS)
├── traducao\                ← saída das Fases 04 e 05a/05b/05c (*_PTBR.ass)
├── traducao_curada\         ← saída da Fase 06
├── legendas_ptbr\           ← saída das Fases 07/11 (*_PTBR.ass corrigido) e entrada/saída da Fase 10
├── corrigidos\               ← saída de remux da Fase 10 (quando habilitado)
├── mkv_final_ptbr\          ← saída da Fase 12
└── otimizados\               ← saída da Fase 03
```

> **Fases 07 e 11** operam sobre `legendas_eng\*_ENG.ass` (ou `*.chs.ass`) + `legendas_ptbr\*_PTBR.ass` (traduzido com `[ERRO_TRADUCAO:]`), sobrescrevendo este último em-place. A **Fase 10** lê o resultado final em `legendas_ptbr\` e, se o usuário confirmar o remux, grava o `.mkv` corrigido em `corrigidos\`. A **Fase 07** roda sobre o conteúdo de `legendas_ptbr\` (ou direto sobre o `.ass` final), normalizando lore/gramática por título (higienização) e reparando erros via IA.

Layout detalhado por esteira: [Guia de execução](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/guia-de-execucao.md#layout-de-pastas).

---

[← Índice](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/README.md)
