# 📦 Estrutura do repositório

[← Índice](README.md)

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
│   ├── modulo-fase-1.md … modulo-fase-12.md
│   ├── instalacao.md
│   ├── dependencias-python.md
│   ├── guia-de-execucao.md
│   ├── logs-e-auditoria.md
│   └── solucao-de-problemas.md
│
├── 1_analisador_de_midia/                 # Fase 1 — Análise e Auditoria de Mídia
│   ├── media_analyzer.py
│   └── relatorio/                         # saída: relatorios *.txt
│
├── 2_extrator_legenda/                    # Fase 2 — Extração de Legendas (ASS, SRT, PGS)
│   ├── extrator_inteligente_ass.py        # -> legendas_eng/*_ENG.ass
│   ├── extrator_inteligente_srt.py        # -> legendas_eng/*_ENG.srt
│   ├── extrator_inteligente_pgs.py        # -> extraidos_sup/*.sup
│   ├── extrator_texto_bruto/
│   │   └── extrator_texto_bruto.py        # utilitário: dump numerado do roteiro p/ revisão manual
│   ├── por_tipo/                          # resíduo de execução antiga (apenas info.txt)
│   └── info.txt                           # log de auditoria das extrações
│
├── 3-conversor_str_ass/                   # Fase 3 — Conversor SRT → ASS (sync FPS)
│   ├── conversor_srt_para_ass.py
│   └── verificador.py                     # placeholder (vazio)
│
├── 4_tradutor_ia_gemma4/                  # Fase 4 — Tradução via LLM Local (LM Studio + Gemma), 1 script por título
│   ├── 86/
│   │   ├── sub_extractor.py               # MKV (EN) -> traducao/*_PTBR.ass — Eighty-Six
│   │   └── traducao_cache_86.json
│   ├── frances_para_ptbr/
│   │   ├── macross_deslta.py              # MKV (FR) -> traducao/*_PTBR.ass — Macross Delta
│   │   └── script_tradutor_fr_gundam_origin.py  # MKV (FR, SUBFRENCH) -> traducao/*_PTBR.ass — Gundam Origin
│   ├── logs/                              # logs (pipeline_fr_*, erros_fr_*, config_fr_*, stats_fr_*)
│   ├── tradutor_ass/
│   │   └── batch_translator_ass.py        # *_ENG.ass -> *_PTBR.ass (lote, Gundam Reconguista)
│   ├── tradutor_gundam_unicornio/
│   │   └── batch_translator_unicorn.py    # *_ENG.ass -> *_PTBR.ass (lote, Gundam Unicorn)
│   └── 5_tradutor_de_legenda/
│       ├── tradutor_srt_direto.py         # *.srt (EN) -> *_PTBR.srt — Macross (filmes)
│       └── logs/
│
├── 5_juntar_legendas_filmes/              # Fase 5 — Remux (MKVMerge)
│   └── batch_remuxer.py                   # .mkv + traducao/*.ass -> mkv_final_ptbr/*_PTBR.mkv
│
├── 6_sincronizacao_legenda/                # Fase 6 — Sincronização (auxiliar)
│   ├── subtitle_fixer.py                  # shift de legenda embutida no .mkv (FFprobe)
│   ├── subtitle_stretcher.py              # time-stretch + offset em .srt/.ass
│   └── auditor_sicronia/
│       └── auditor_sincronia.py           # audita drift via FFprobe
│
├── 7_decodificador/                       # Fase 7 — Otimização de vídeo (auxiliar)
│   ├── gpu_video_optimizer.py             # recomprime para HEVC/NVENC -> otimizados/*.mkv
│   └── optimizer_log.txt
│
├── 8_cura_legendas/                       # Fase 8 — Cura de legendas (auxiliar)
│   ├── cura_gundam_mkv.py                 # repara TAG corrompido em .mkv remuxado
│   └── cura_legendas_tag.py               # repara TAG via casamento ENG/PTBR -> traducao_curada/
│
├── 9_reparo_de_traducao/                  # Fase 9 — Reparo de falhas [ERRO_TRADUCAO:] via IA (Gemma)
│   ├── repara_erros_traducao.py           # retraduz avulso (batch=1) via LM Studio
│   ├── limpa_erros_residuais.py           # limpeza offline (sem IA) dos resíduos
│   └── relatorio_reparo.txt               # relatório da última execução
│
├── 10_correcao_guilty_crown/              # Fase 10 — Correção offline (Guilty Crown)
│   ├── corrigir_guilty_crown.py           # remove [ERRO_TRADUCAO:] -> legendas_ptbr/*_PTBR.ass
│   ├── corrigir_cores_musicas.py          # corrige cores/tags de músicas (OP/ED)
│   ├── relatorio_correcao.txt             # relatório de corrigir_guilty_crown.py
│   └── relatorio_cores_musicas.txt        # relatório de corrigir_cores_musicas.py
│
├── 11_chines_LLM_alibaba_qwen2/           # Fase 11 — Tradução chinês (CHS) via Qwen2.5, Gundam Origin
│   ├── batch_translator_origin_zh.py      # *.chs.ass -> *_PTBR.ass (lote, cache, fallback resiliente)
│   ├── repara_erros_origin_zh.py          # retraduz avulso (batch=1) [ERRO_TRADUCAO:]
│   ├── test_reparo.py                     # utilitário de depuração manual (fora do pipeline)
│   ├── traducao_cache_origin_zh.json      # cache persistente (+ .json.bak)
│   ├── info.txt                           # métricas por arquivo (último lote)
│   ├── debug_last_failure.txt             # debug da última falha de lote
│   └── relatorio_reparo_origin_zh.txt     # relatório do reparo avulso
│
├── 12_revisao_legenda/                    # Fase 12 — Revisão/correção final por título (QA + remux opcional)
│   ├── revisao_legenda_origin.py          # Gundam The Origin (Esteira H) — lore + cache + remux
│   ├── revisao_guild_crown.py             # Guilty Crown (Esteira G) — diálogos + letras OP/ED + remux
│   ├── revisao_legenda_gundam_unicornio.py  # Gundam Unicorn (Esteira F) — ep.1 + letras OP/ED + remux
│   ├── revisao_legenda_macross_delta.py   # Macross Delta TV (Esteira D) — lore + tags ASS
│   ├── micross_delta_filme2.py            # Macross Delta Filme 2 — lore + resíduos de francês + remux
│   ├── revisao_86.py                      # Eighty-Six Parts 1 & 2 (Esteira A) — alucinações residuais + remux
│   └── _dialogos_eng_brutos.txt           # roteiro de referência (gerado por extrator_texto_bruto.py)
│
├── multiplexar/
│   └── logs/                              # logs de saída de batch_remuxer.py (Fase 5)
│
└── _tmp_test_srt/                         # pasta de teste manual (Fase 11/Esteira H) — não faz parte do pipeline
```

> As pastas estão numeradas de **1 a 12** seguindo a ordem das fases descritas em [Arquitetura](arquitetura.md), o que também facilita a ordenação no explorador de arquivos do sistema.

---

## Correção de documentação — Fase 4 não usa mais scripts genéricos na raiz

Versões anteriores desta documentação (e do README) citavam `4_tradutor_ia_gemma4/sub_extractor.py` e `4_tradutor_ia_gemma4/script_tradutor_fr.py` na **raiz** da pasta, como scripts genéricos reaproveitáveis para qualquer título. Isso não reflete mais o repositório: o projeto migrou para **um script dedicado por título**, cada um em sua própria subpasta, com glossário, cache e caminhos padrão próprios:

| Script citado nas versões antigas | Caminho real atual | Título |
|:---|:---|:---|
| `4_tradutor_ia_gemma4/sub_extractor.py` | `4_tradutor_ia_gemma4/86/sub_extractor.py` | Eighty-Six |
| `4_tradutor_ia_gemma4/script_tradutor_fr.py` | `4_tradutor_ia_gemma4/frances_para_ptbr/macross_deslta.py` | Macross Delta |
| *(não existia)* | `4_tradutor_ia_gemma4/frances_para_ptbr/script_tradutor_fr_gundam_origin.py` | Gundam The Origin (francês) |

Veja a tabela completa e atualizada em [Fase 4](modulo-fase-4.md).

---

## Pastas legadas (não usadas pelo pipeline atual)

Restos de reorganizações anteriores do projeto. Mantidas apenas por compatibilidade local — **não são referenciadas pela documentação atual** e podem ser removidas com segurança:

| Pasta | Conteúdo residual | Substituída por |
|:---|:---|:---|
| `2_tradutor_ia_gemma4/` | apenas `__pycache__/` | `4_tradutor_ia_gemma4/86/sub_extractor.py` |
| `3_juntar_legendas_filmes/` | apenas `__pycache__/` | `5_juntar_legendas_filmes/batch_remuxer.py` |
| `8_sincronizacao_legenda/` | `__pycache__/`, `auditor_sicronia/` | `6_sincronizacao_legenda/` |
| `extrator_legenda_PGS/` | `__pycache__/`, `log/` | `2_extrator_legenda/extrator_inteligente_pgs.py` |
| `2_extrator_legenda/por_tipo/` | apenas `info.txt` residual | `2_extrator_legenda/info.txt` |
| `_tmp_test_srt/` | `.chs.ass` de teste + saída avulsa | testes manuais da Fase 11 — pode ser apagada |

---

## Pastas de mídia do usuário (fora do repositório)

O pipeline opera sobre pastas de animes/filmes que ficam **fora** do repositório (ex.: `C:\TRACKER-ANIMES\animes\...`, ou em outros discos como `E:\animes\...`, `D:\PROJETOS-OPEN\animes\...`, conforme o título). Layout típico gerado durante o processamento:

```text
C:\TRACKER-ANIMES\animes\<titulo>\
├── episodio_01.mkv
├── legendas_eng\          ← saída da Fase 2 (também usada como entrada das Fases 9/10)
├── legenda\                ← entrada/saída SRT (Esteira B/C)
├── extraidos_sup\          ← saída da Fase 2 (PGS)
├── traducao\                ← saída das Fases 3 e 4 (*_PTBR.ass)
├── traducao_curada\         ← saída da Fase 8
├── legendas_ptbr\           ← saída das Fases 9/10/11 (*_PTBR.ass corrigido) e entrada/saída da Fase 12
├── corrigidos\               ← saída de remux da Fase 12 (quando habilitado)
├── mkv_final_ptbr\          ← saída da Fase 5
└── otimizados\              ← saída da Fase 7
```

> **Fases 9, 10 e 11** operam sobre `legendas_eng\*_ENG.ass` (ou `*.chs.ass`) + `legendas_ptbr\*_PTBR.ass` (traduzido com `[ERRO_TRADUCAO:]`), sobrescrevendo este último em-place. A **Fase 12** lê o resultado final em `legendas_ptbr\` e, se o usuário confirmar o remux, grava o `.mkv` corrigido em `corrigidos\`.

Layout detalhado por esteira: [Guia de execução](guia-de-execucao.md#layout-de-pastas).

---

[← Índice](README.md)
