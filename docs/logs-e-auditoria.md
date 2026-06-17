# 📊 Logs e auditoria

[← Índice](README.md) · [Guia de execução](guia-de-execucao.md)

<p>
  <img src="https://img.shields.io/badge/Fases-1_a_12-blueviolet?style=flat-square" alt="Fases 1-12"/>
  <img src="https://img.shields.io/badge/Auditoria-Logs_%2B_Relatórios-informational?style=flat-square" alt="Auditoria"/>
</p>

---

## Fase 1 — Analisador de mídia (`media_analyzer.py`)

| Local | Arquivo |
|:---|:---|
| `1_analisador_de_midia/relatorio/` | `{arquivo}_{timestamp}.txt` — relatório técnico (codecs, faixas, sincronia) |

---

## Fase 2 — Extração de legendas

| Script | Local | Arquivo |
|:---|:---|:---|
| `extrator_inteligente_ass.py` / `_srt.py` / `_pgs.py` | `2_extrator_legenda/` | `info.txt` — auditoria das extrações (faixas detectadas, fallback usado) |
| `extrator_inteligente_pgs.py` | `2_extrator_legenda/log/` | `extracao_pgs_*.log` |

---

## Fase 4 — Tradução IA (LM Studio/Gemma)

### `86/sub_extractor.py` (Eighty-Six)

Quatro artefatos por execução em `4_tradutor_ia_gemma4/86/logs/`:

| Arquivo | Conteúdo |
|:---|:---|
| `pipeline_86_*.txt` | Fluxo completo da execução |
| `config_86_*.txt` | Snapshot de infraestrutura (binários, modelo, pastas) |
| `erros_86_*.txt` | Erros e stack traces |
| `stats_86_*.json` | Telemetria: encodings detectados, cache, requisições |

Persiste também `4_tradutor_ia_gemma4/86/traducao_cache_86.json` (cache de traduções entre execuções).

### `frances_para_ptbr/macross_deslta.py` e `frances_para_ptbr/script_tradutor_fr_gundam_origin.py`

Quatro artefatos por execução em `4_tradutor_ia_gemma4/logs/`:

| Arquivo | Conteúdo |
|:---|:---|
| `pipeline_fr_*.txt` | Fluxo completo da execução |
| `config_fr_*.txt` | Snapshot de infraestrutura (binários, modelo, pastas) |
| `erros_fr_*.txt` | Erros e stack traces |
| `stats_fr_*.json` | Telemetria: encodings detectados, cache, requisições |

Cada script persiste sua própria instância de `traducao_cache_fr.json` na pasta `frances_para_ptbr/` (cache de traduções entre execuções).

### `tradutor_srt_direto.py`

Um arquivo por execução em `4_tradutor_ia_gemma4/5_tradutor_de_legenda/logs/`:

| Arquivo | Conteúdo |
|:---|:---|
| `pipeline_direct_srt_*.txt` | Auditoria completa: blocos, lotes, encoding, caminho de saída |

### `batch_translator_ass.py` e `batch_translator_unicorn.py`

Saída via console (`tqdm` + `colorama`); retry logic registrado inline no terminal.

---

## Fase 5 — Remuxer (`batch_remuxer.py`)

Quatro artefatos em `multiplexar/logs/`:

| Arquivo | Conteúdo |
|:---|:---|
| `remux_pipeline_*.txt` | Fluxo do remux |
| `remux_config_*.txt` | Caminhos e binário `mkvmerge` |
| `remux_erros_*.txt` | Dumps de erro |
| `remux_stats_*.json` | Bytes gerados, pareamentos, falhas |

---

## Fase 6 — Sincronização

| Script | Local | Arquivo |
|:---|:---|:---|
| `subtitle_fixer.py` | `6_sincronizacao_legenda/` | `processamento_log.txt` |
| `subtitle_stretcher.py` | — | apenas console |
| `auditor_sincronia.py` | `6_sincronizacao_legenda/auditor_sicronia/` | apenas console (relatório de drift via FFprobe) |

---

## Fase 7 — Otimização de vídeo (GPU)

| Script | Local | Arquivo |
|:---|:---|:---|
| `gpu_video_optimizer.py` | `7_decodificador/` | `optimizer_log.txt` |

---

## Fase 8 — Cura de legendas

| Script | Local | Arquivo |
|:---|:---|:---|
| `cura_gundam_mkv.py` / `cura_legendas_tag.py` | `8_cura_legendas/` | `info.txt` |

---

## Fase 9 — Reparo de tradução

| Script | Local | Arquivo |
|:---|:---|:---|
| `repara_erros_traducao.py` | `9_reparo_de_traducao/` | `relatorio_reparo.txt` — falhas encontradas/reparadas/persistentes por arquivo, linhas com falha, tempo total |
| `limpa_erros_residuais.py` | `9_reparo_de_traducao/` | Apenas console (sem relatório próprio) |

---

## Fase 10 — Correção Guilty Crown

| Script | Local | Arquivo |
|:---|:---|:---|
| `corrigir_guilty_crown.py` | `10_correcao_guilty_crown/` | `relatorio_correcao.txt` — arquivo de origem/destino e correções `[ERRO_TRADUCAO:]` aplicadas |
| `corrigir_cores_musicas.py` | `10_correcao_guilty_crown/` | `relatorio_cores_musicas.txt` — estilos OP/ED redefinidos, linhas com cor corrigida, resíduos `TAG` removidos |

---

## Fase 11 — Tradução chinês (Qwen2.5, Gundam Origin)

| Script | Local | Arquivo |
|:---|:---|:---|
| `batch_translator_origin_zh.py` | `11_chines_LLM_alibaba_qwen2/` | `info.txt` — métricas por arquivo (diálogos, cache hits, chamadas, fallbacks, tempo); `debug_last_failure.txt` na primeira falha de lote |
| `repara_erros_origin_zh.py` | `11_chines_LLM_alibaba_qwen2/` | `relatorio_reparo_origin_zh.txt` |
| `test_reparo.py` (dev/debug) | `11_chines_LLM_alibaba_qwen2/` | `debug_test.txt` (recriado a cada execução) |

Ambos os scripts de tradução persistem `traducao_cache_origin_zh.json` (+ backup `.json.bak`).

---

## Fase 12 — Revisão final por título

| Script | Local | Saída |
|:---|:---|:---|
| `revisao_legenda_origin.py` | `12_revisao_legenda/` | Atualiza `traducao_cache_origin_zh.json`; opcional `_relatorio_sem_traducao.txt` (auditoria de resíduos) |
| `revisao_guild_crown.py` / `revisao_legenda_gundam_unicornio.py` / `revisao_legenda_macross_delta.py` / `micross_delta_filme2.py` / `revisao_86.py` | `12_revisao_legenda/` | Apenas console (`colorama`); `.mkv` corrigido em `corrigidos/` quando o remux é confirmado |

---

## Níveis no console (colorama)

| Tag | Cor | Significado |
|:---:|:---:|:---|
| `[SUCESSO]` | 🟢 Verde | Operação concluída |
| `[INFO]` / `[DEBUG]` | ⚪ / 🔵 | Fluxo normal / detalhe |
| `[AVISO]` | 🟡 Amarelo | Situação recuperável |
| `[ERRO]` | 🔴 Vermelho | Falha ou aborto |

Esses níveis aparecem em praticamente todos os scripts (Fases 1–12).

---

[← Guia de execução](guia-de-execucao.md) · [Solução de problemas →](solucao-de-problemas.md)
