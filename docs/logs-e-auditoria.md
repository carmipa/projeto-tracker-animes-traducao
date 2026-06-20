# 📊 Logs e auditoria

[← Índice](README.md) · [Guia de execução](guia-de-execucao.md)

<p>
  <img src="https://img.shields.io/badge/Fases-00_a_12-blueviolet?style=flat-square" alt="Fases 00-12"/>
  <img src="https://img.shields.io/badge/Auditoria-Logs_%2B_Relatórios-informational?style=flat-square" alt="Auditoria"/>
</p>

---

## Fase 01 — Analisador de mídia (`media_analyzer.py`)

| Local | Arquivo |
|:---|:---|
| `01_analisador_midia/relatorio/` | `{arquivo}_{timestamp}.txt` — relatório técnico por arquivo (codecs, faixas, sincronia) |
| `01_analisador_midia/relatorio/` | `consolidado_{titulo}_{timestamp}.txt` — relatório consolidado quando a pasta tem vários episódios |

---

## Fase 02 — Extração de legendas

| Script | Local | Arquivo |
|:---|:---|:---|
| `extrator_inteligente_ass.py` / `_srt.py` / `_pgs.py` | `02_extrator_legenda/` | `info.txt` — auditoria das extrações (arquivo, Track ID, nome da faixa, formato, saída) |
| — | `02_extrator_legenda/por_tipo/` | `info.txt` — resíduo de execução antiga |

---

## Fase 03 — Otimização de vídeo (GPU)

| Script | Local | Arquivo |
|:---|:---|:---|
| `gpu_video_optimizer.py` | `03_decodificador_caracteres/` | `optimizer_log.txt` |

---

## Fase 05a — Tradução IA (LM Studio/Gemma)

### `86/sub_extractor.py` (Eighty-Six)

Quatro artefatos por execução em `05a_tradutor_llm_gemma4/86/logs/`:

| Arquivo | Conteúdo |
|:---|:---|
| `pipeline_86_*.txt` | Fluxo completo da execução |
| `config_86_*.txt` | Snapshot de infraestrutura (binários, modelo, pastas) |
| `erros_86_*.txt` | Erros e stack traces |
| `stats_86_*.json` | Telemetria: encodings detectados, cache, requisições |

Persiste também `05a_tradutor_llm_gemma4/86/traducao_cache_86.json` (cache de traduções entre execuções).

### `5_tradutor_de_legenda/tradutor_srt_direto.py`

Um arquivo por execução em `05a_tradutor_llm_gemma4/5_tradutor_de_legenda/logs/`:

| Arquivo | Conteúdo |
|:---|:---|
| `pipeline_direct_srt_*.txt` | Auditoria completa: blocos, lotes, encoding, caminho de saída |

### `tradutor_ass/batch_translator_ass.py` e `batch_translator_sidonia.py`

| Local | Arquivo |
|:---|:---|
| `05a_tradutor_llm_gemma4/tradutor_ass/` | `info_traducao_ass.txt` / `info_traducao_sidonia_ass.txt` |
| `05a_tradutor_llm_gemma4/tradutor_ass/` | `debug_last_failure_sidonia_ass.txt` — dump da última falha de lote (Sidonia) |

### `tradutor_gundam_unicornio/batch_translator_unicorn.py`

| Local | Arquivo |
|:---|:---|
| `05a_tradutor_llm_gemma4/tradutor_gundam_unicornio/` | `info.txt`, `debug_last_failure.txt` |

> `05a_tradutor_llm_gemma4/logs/` (raiz da pasta) contém logs herdados de uma estrutura anterior — inclui artefatos `config_*`/`erros_*`/`pipeline_*`/`stats_*` e variantes `_fr_*` de antes da migração do francês para a Fase 05b. Mantidos por histórico; não são gerados por execuções atuais.

---

## Fase 05b — Tradução IA (LM Studio/Mistral Nemo)

### `frances_para_ptbr/macross_deslta.py` e `frances_para_ptbr/script_tradutor_fr_gundam_origin.py`

Artefatos por execução em `05b_tradutor_llm_mistral_nemo/frances_para_ptbr/logs/`:

| Arquivo | Conteúdo |
|:---|:---|
| `pipeline_fr_*.txt` | Fluxo completo da execução — inclui a linha `Usando modelo: <id>` com o modelo real detectado via `/v1/models` (ex.: `mistralai/mistral-nemo-instruct-2407`) |
| `config_fr_*.txt` | Snapshot de infraestrutura (binários, pastas) |
| `erros_fr_*.txt` | Erros e stack traces |
| `stats_fr_*.json` | Telemetria: encodings detectados, cache, requisições |
| `traducoes_detalhadas_fr_*.txt` | **Apenas em `script_tradutor_fr_gundam_origin.py`** — auditoria lado a lado: linha original em francês + tradução PT-BR (ou "MANTIDO ORIGINAL"), por diálogo, por episódio |

Persiste `05b_tradutor_llm_mistral_nemo/frances_para_ptbr/traducao_cache_fr.json` (cache compartilhado pelos dois scripts).

### `Detonator_Orgun/script_tradutor_en_detonator_orgun.py`

Artefatos por execução em `05b_tradutor_llm_mistral_nemo/Detonator_Orgun/logs/`:

| Arquivo | Conteúdo |
|:---|:---|
| `pipeline_en_orgun_*.txt` | Fluxo completo da execução |
| `erros_en_orgun_*.txt` | Erros e stack traces |
| `stats_en_orgun_*.json` | Telemetria |

Persiste `05b_tradutor_llm_mistral_nemo/Detonator_Orgun/traducao_cache_orgun_en.json`.

---

## Fase 05c — Tradução chinês (Qwen2.5, Gundam The Origin)

| Script | Local | Arquivo |
|:---|:---|:---|
| `batch_translator_origin_zh.py` | `05c_tradutor_llm_qwen2/` | `info.txt` — métricas por arquivo (diálogos, cache hits, chamadas, fallbacks, tempo); `debug_last_failure.txt` na primeira falha de lote |
| `repara_erros_origin_zh.py` | `05c_tradutor_llm_qwen2/` | `relatorio_reparo_origin_zh.txt` |
| `test_reparo.py` (dev/debug) | `05c_tradutor_llm_qwen2/` | `debug_test.txt` (recriado a cada execução) |

Ambos os scripts de tradução persistem `traducao_cache_origin_zh.json` (+ backup `.json.bak`).

---

## Fase 05c-2 — Tradução/Revisão IA (TranslateGemma)

| Script | Local | Arquivo |
|:---|:---|:---|
| `Gundam_ZZ/script_tradutor_en_gundam_zz.py` | `05c_tradutor_llm_translategemma/Gundam_ZZ/logs/` | `stats_en_gundam_zz_*.json` |
| `Gundam_Zeta/script_tradutor_en_gundam_zeta.py` | `05c_tradutor_llm_translategemma/Gundam_Zeta/logs/` | `stats_en_gundam_zeta_*.json` |

Cada um persiste seu próprio cache (`traducao_cache_gundam_zz_en.json` / `traducao_cache_gundam_zeta_en.json`). `Gundam_Origin/script_revisor_ptbr_gundam_origin.py` (revisão gramatical) opera apenas via console, sem log próprio.

---

## Fase 06 — Cura de legendas

`cura_gundam_mkv.py` e `cura_legendas_tag.py` não geram arquivo de log próprio — saída via console (`colorama`).

---

## Fase 07 — Reparo de tradução

| Script | Local | Arquivo |
|:---|:---|:---|
| `repara_erros_traducao.py` | `07_reparo_traducao/` | `relatorio_reparo.txt` — falhas encontradas/reparadas/persistentes por arquivo, linhas com falha, tempo total |
| `limpa_erros_residuais.py` | `07_reparo_traducao/` | Apenas console (sem relatório próprio) |
| `extrai_linhas_suspeitas.py` | `07_reparo_traducao/` | `linhas_para_revisar.json` |
| `aplica_linhas_revisadas.py` | `07_reparo_traducao/` | Lê `linhas_revisadas.json` (entrada manual) e atualiza o cache global |
| `refina_traducao_fr.py` | `07_reparo_traducao/` | Apenas console + relatório de alterações no terminal |

---

## Fase 08 — Sincronização

| Script | Local | Arquivo |
|:---|:---|:---|
| `subtitle_fixer.py` | `08_sincronizacao_legenda/` | `processamento_log.txt` (gerado por execução, não versionado) |
| `subtitle_stretcher.py` | — | apenas console |
| `auditor_sincronia.py` | `08_sincronizacao_legenda/auditor_sicronia/` | apenas console (relatório de drift via FFprobe) |

---

## Fase 09 — Injetor de músicas

`injetor_de_musicas.py` opera via console (`colorama`/`tqdm`), sem relatório próprio em disco.

---

## Fase 10 — Auditoria e revisão final

| Script | Local | Saída |
|:---|:---|:---|
| `revisao_legenda_origin.py` | `10_auditoria_e_revisao/` | Atualiza `traducao_cache_origin_zh.json`; opcional `_relatorio_sem_traducao.txt` (auditoria de resíduos) |
| `revisao_guild_crown.py` / `revisao_legenda_gundam_unicornio.py` / `revisao_legenda_macross_delta.py` / `micross_delta_filme2.py` / `revisao_86.py` | `10_auditoria_e_revisao/` | Apenas console (`colorama`); `.mkv` corrigido em `corrigidos/` quando o remux é confirmado |
| — | `10_auditoria_e_revisao/_dialogos_eng_brutos.txt` | Roteiro de referência (gerado por `extrator_texto_bruto.py`, Fase 02), usado como apoio manual de revisão |

---

## Fase 11 — Correção de projetos legados

| Script | Local | Arquivo |
|:---|:---|:---|
| `corrigir_guilty_crown.py` | `11_correcao_projetos_legados/` | `relatorio_correcao.txt` — arquivo de origem/destino e correções `[ERRO_TRADUCAO:]` aplicadas |
| `corrigir_cores_musicas.py` | `11_correcao_projetos_legados/` | `relatorio_cores_musicas.txt` — estilos OP/ED redefinidos, linhas com cor corrigida, resíduos `TAG` removidos |

---

## Fase 12 — Remuxer (`batch_remuxer.py`)

Quatro artefatos por execução em **`multiplexar/logs/`** (caminho hardcoded no script — `pasta_raiz_projeto/multiplexar/logs`):

| Arquivo | Conteúdo |
|:---|:---|
| `remux_pipeline_*.txt` | Fluxo do remux |
| `remux_config_*.txt` | Caminhos e binário `mkvmerge` |
| `remux_erros_*.txt` | Dumps de erro |
| `remux_stats_*.json` | Bytes gerados, pareamentos, falhas |

> A pasta `12_remuxer_mkvmerge/logs/` tem o mesmo padrão de nomes, porém é **resíduo de execuções antigas** — não é mais escrita pelo script atual. Veja [Estrutura do repositório](estrutura-repositorio.md#nota--logs-de-remux-duplicados-12_remuxer_mkvmergelogs-vs-multiplexarlogs).

---

## Níveis no console (colorama)

| Tag | Cor | Significado |
|:---:|:---:|:---|
| `[SUCESSO]` | 🟢 Verde | Operação concluída |
| `[INFO]` / `[DEBUG]` | ⚪ / 🔵 | Fluxo normal / detalhe |
| `[AVISO]` | 🟡 Amarelo | Situação recuperável |
| `[ERRO]` | 🔴 Vermelho | Falha ou aborto |

Esses níveis aparecem em praticamente todos os scripts (Fases 00–12).

---

[← Guia de execução](guia-de-execucao.md) · [Solução de problemas →](solucao-de-problemas.md)
