# ⚠️ Solução de problemas

[← Índice](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/README.md) · [Logs](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/logs-e-auditoria.md)

<p>
  <img src="https://img.shields.io/badge/Esteiras-A_a_N-9146FF?style=flat-square" alt="Esteiras A-N"/>
  <img src="https://img.shields.io/badge/Troubleshooting-Geral_%2B_por_esteira-informational?style=flat-square" alt="Troubleshooting"/>
</p>

---

## Geral (todas as esteiras)

| Sintoma | Causa provável | Ação |
|:---|:---|:---|
| `mkvextract.exe`/`mkvmerge.exe não encontrados` | MKVToolNix ausente | Instale em `C:\Program Files\MKVToolNix\` |
| `LM Studio não responde` / `LM Studio offline` | Servidor parado ou modelo não carregado | Inicie LM Studio na porta **1234** com o modelo certo para a fase (Gemma 4B / Mistral Nemo 2407 / Qwen2.5-7B / TranslateGemma 12B) |
| `pymediainfo nao esta instalado` | Pacote/DLL ausente | `pip install pymediainfo` + instale [MediaInfo](https://mediaarea.net/en/MediaInfo/Download) |
| Caracteres estranhos na legenda traduzida | Encoding legado (Latin-1/CP1252) mal detectado | Verifique `encodings_detectados` em `stats_*.json` (Fase 05a/05b) |
| Modelo errado respondendo (ex.: Gemma respondeu numa esteira que precisa de Qwen2.5/Mistral Nemo/TranslateGemma) | LM Studio não foi recarregado ao trocar de esteira | Confira `GET /v1/models` ou a linha `Usando modelo: ...` no `pipeline_*` log antes de processar um lote grande |

---

## Esteiras A/D/K/L/M/N — Episódios MKV com extração + tradução integradas

Eighty-Six (05a), Macross Delta/Gundam Origin FR/Gundam ZZ/Detonator Orgun (05b), Gundam Zeta e rota legada de ZZ (05c-2), Knights of Sidonia (05a + 02).

| Sintoma | Causa provável | Ação |
|:---|:---|:---|
| `Nenhuma faixa S_TEXT/ASS encontrada` | Legenda é PGS (bitmap) ou hardsub | Use [Esteira C](#esteira-c--pgs-fases-02--ocr--04--12) ou audite com [Fase 01](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-01.md) |
| Episódio ignorado no remux (Fase 12) | Nome do `.ass` não casa com o `.mkv` | Garanta `{base}_PTBR.ass` em `traducao\` com o mesmo nome base do vídeo |
| Tradução muito lenta (Esteira D) | Multi-thread limitado a 2 | Esperado — `macross_deslta.py`/`script_tradutor_fr_gundam_origin.py` usam `ThreadPoolExecutor(max_workers=2)` |
| Faixa em inglês não detectada (Sidonia, Detonator Orgun) | Faixa `lang` diferente do esperado no release | Ajuste a lista de prioridade no script correspondente |

---

## Esteira B — Filme / SRT externo (Fases 05a → 04 → 12)

| Sintoma | Causa provável | Ação |
|:---|:---|:---|
| `Nenhum arquivo .srt localizado` | Pasta vazia ou caminho errado | Confira o caminho informado ao `tradutor_srt_direto.py` |
| `Nenhuma legenda *_PTBR.srt` (Fase 04) | Fase 05a não rodou ou saída sem sufixo `_PTBR` | Execute a Fase 05a (tradução SRT) primeiro |
| Legenda dessincronizada no filme final | FPS 25 vs 23.976 | Fase 04 aplica `FATOR_SINCRO = 1.042709`; ajuste no script se a fonte tiver outro FPS |
| Remux sem par (Fase 12) | Nome `.ass` ≠ nome `.mkv` | Edite `nome_base_filme` em `conversor_srt_para_ass.py` (Fase 04) |
| Múltiplos `.srt` na pasta | Ambiguidade no prompt | Selecione o número correto no menu interativo da Fase 05a |

---

## Esteira C — PGS (Fases 02 → OCR → 04 → 12)

| Sintoma | Causa provável | Ação |
|:---|:---|:---|
| `Nenhuma faixa S_HDMV/PGS encontrada` | Release não tem legenda PGS | Use Esteira A/B/D conforme o formato real |
| OCR com muitos erros de caractere | Fonte PGS de baixa resolução | Ajuste o motor/idioma do OCR (Subtitle Edit + Tesseract) antes da Fase 04 |
| Fase 04 não encontra `*_PTBR.srt` | OCR não gerou sufixo correto | Renomeie a saída do OCR para `{base}_PTBR.srt` |

---

## Esteira F/G — Lote ASS / Gundam (Fases 02 → 05a → [06] → [07] → 12)

| Sintoma | Causa provável | Ação |
|:---|:---|:---|
| `[ABORTO]` ao extrair faixa (Fase 02) | Track IDs 4/5 não existem nesse release | Ajuste os IDs de fallback em `extrator_inteligente_ass.py` |
| Tags `\N`, `{\i1}` etc. quebradas após tradução | Falha no mascaramento `[T0]`/`[T1]` ou `___TAG___` | Rode [Fase 06](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-06.md) (`cura_legendas_tag.py` or `cura_gundam_mkv.py`) |
| Texto "TAG" literal aparecendo no MKV final (Gundam Unicorn) | Corrupção conhecida do `batch_translator_unicorn.py` | `cura_gundam_mkv.py` — modo perfect-match (com `*_ENG.ass`) ou regex cego |
| Retry constante / poucas respostas da IA | Lote (`batch`) grande demais para o contexto do modelo | Reduza o tamanho do lote no script (`batch_translator_ass.py` / `_unicorn.py` / `_sidonia.py`) |

---

## Fase 05b — Mistral Nemo (francês e inglês)

| Sintoma | Causa provável | Ação |
|:---|:---|:---|
| `config_fr_*.txt` mostra "Modelo: Gemma 4B (google/gemma-4-e4b)" mas a tradução está correta | **Bug cosmético conhecido** — o rótulo do relatório está hardcoded e não foi atualizado na migração para Mistral Nemo | Ignore o rótulo; confira o modelo real na linha `Usando modelo: ...` do `pipeline_fr_*.txt` |
| Qualidade de tradução ruim/inconsistente em francês | Gemma 4B ainda carregado no LM Studio, em vez do Mistral Nemo | Carregue `mistralai/mistral-nemo-instruct-2407` (ou equivalente GGUF) no LM Studio antes de rodar os scripts de `05b_tradutor_llm_mistral_nemo/` |
| `VALIDAÇÃO REJEITOU idx N` no log (`script_tradutor_fr_gundam_origin.py`) | A tradução do LLM para aquela linha falhou a validação anti-resíduo/anti-alucinação | Normal em baixo volume — o fallback linha a linha tenta de novo; se persistir, revise o glossário/prompt para o termo específico |
| `RESPOSTA BRUTA DO LLM (FALHA DE EXTRAÇÃO/VALIDAÇÃO)` no log de erros | Nenhuma linha do lote pôde ser extraída/validada | Verifique se o modelo carregado é realmente o Mistral Nemo (não outro modelo incompatível com o formato de prompt indexado `[0]`, `[1]`...) |
| `macross_deslta.py` com qualidade inferior ao esperado | Esse script pode não ter recebido os mesmos ajustes de prompt feitos em `script_tradutor_fr_gundam_origin.py` | Compare os prompts dos dois scripts e replique os ajustes relevantes |
| `script_tradutor_en_detonator_orgun.py` falha de conexão (não HTTP 400) | LM Studio offline/instável durante o lote — erro de conexão mal-diagnosticado como erro de requisição | Confirme LM Studio rodando antes do lote; o script já tem backoff para reconexão |
| Gundam ZZ gera arquivo sem `_PTBR` ou sobrescreve o original | Versão antiga do `tradutor_mistral_gundam_zz.py` ou uso de saída manual inadequada | Use a versão atual da Fase 05b: ela cria `{base}_PTBR.ass`, preserva subpastas e aceita a pasta por argumento posicional, `--entrada`, `--pasta` ou `--origem` |

---

## Esteira I — Gundam The Origin, legenda chinesa (Fases 02 → 05c → [07] → 12 → [10])

| Sintoma | Causa provável | Ação |
|:---|:---|:---|
| `validar_traducao()` rejeita a saída (texto ainda com CJK) | Qwen2.5 não está carregado no LM Studio (outro modelo respondeu) | Confira o modelo active em `GET /v1/models`; carregue `qwen2.5-7b-instruct` |
| Tradução muito lenta ou travando | `MAX_THREADS = 2` é o limite seguro para 8GB VRAM | Reduza `--batch-size` ou rode com `--threads 1` se a GPU tiver pouca VRAM livre |
| Linhas `[ERRO_TRADUCAO: ...]` persistem após `repara_erros_origin_zh.py` | Termo protegido/nome próprio sem tradução válida em PT-BR | Corrija manualmente ou adicione a regra em [Fase 10](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-10.md#revisao_legenda_originpy) (`revisao_legenda_origin.py`) |
| Erro de lore conhecido (ex.: "Guerra de cem anos", "Gólgota"/"Lucifer") sobrevive à tradução | Falha recorrente do modelo para esses termos específicos | Rode [Fase 10](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-10.md) — já corrige esses casos e atualiza o cache |
| `test_reparo.py` não reflete o comportamento do pipeline real | Script é um utilitário de depuração isolado (3 linhas fixas) | Use apenas para validar rapidamente prompt/modelo; não é parte do pipeline regular |

---

## Esteira J — Gundam Origin, legenda francesa SUBFRENCH (Fase 05b → [07] → 12)

| Sintoma | Causa provável | Ação |
|:---|:---|:---|
| Nomes da família Deikun aparecem como "Daikun" | Grafia do release francês não normalizada | O script já normaliza via regex; se persistir, rode [Fase 07](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-07.md) (`Gundam_Origin/limpeza_origin_*.py`) ou verifique se está usando `script_tradutor_fr_gundam_origin.py` e não `macross_deslta.py` |
| Track francesa não detectada | Faixa `lang` diferente de `fre`/`fra`/`fr` no release | Ajuste a lista de prioridade em `script_tradutor_fr_gundam_origin.py` ou use a [Esteira I](#esteira-i--gundam-the-origin-legenda-chinesa-fases-02--05c--07--12--10) (legenda chinesa) como alternativa |
| Tradução com resíduos de francês/lore que sobrevivem ao 05b | Caso conhecido pré-higienização | Rode a higienização de lore da Fase 07 (4 scripts em `Gundam_Origin/`) ou o refino da Fase 07 (`refina_traducao_fr.py`) |

---

## Fase 10 — Revisão final por título (todas as esteiras com QA)

| Sintoma | Causa provável | Ação |
|:---|:---|:---|
| Script não encontra a pasta de legendas | `PASTA_ANIME`/`PASTA_LEGENDA` no topo do script apontam para a árvore de mídia do autor (`E:\animes\...`, `C:\TRACKER-ANIMES\...`) | Edite essas constantes no script para o caminho real do seu título |
| `mkvmerge não encontrado. Remuxing abortado` | MKVToolNix ausente ou fora do PATH | Instale MKVToolNix ou responda `n` ao prompt de remux para apenas corrigir a legenda |
| Correção não copia para um título diferente | Cada script tem a lista de patches (regex/dicionário) hardcoded para um título específico | Copie o script mais próximo (mesmo idioma/Esteira) e adapte os patches — não reaproveite entre séries diferentes sem revisar |

---

## Fases 07/11 — Higienização, Reparo de Tradução e Esteira H (Guilty Crown)

| Sintoma | Causa provável | Ação |
|:---|:---|:---|
| Linhas `[ERRO_TRADUCAO: ...]` em `traducao\*_PTBR.ass` | Fase 05a/05b/05c não conseguiu traduzir aquela linha dentro do lote | Rode o reparo de erros da [Fase 07](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-07.md#1-scripts-de-reparo-geral) (`repara_erros_traducao.py`, requer LM Studio) |
| `[ABORTADO] 5 falhas consecutivas` (Fase 07) | LM Studio offline/instável durante o reparo | Verifique LM Studio na porta 1234 e rode novamente — arquivos já reparados são preservados |
| Marcador `[ERRO_TRADUCAO:]` persiste após `repara_erros_traducao.py` | Termo protegido/nome próprio cuja tradução correta é igual ao inglês | Rode `limpa_erros_residuais.py` (sem IA) para restaurar o texto original com as tags |
| Desalinhamento físico de linhas com o original (Fase 07) | `.ass` traduzido tem nº de linhas diferente do `.ass` original (`_ENG.ass`) | Garanta que a Fase 05a não removeu/duplicou linhas; reextraia com [Fase 02](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-02.md) se necessário |
| Texto `TAG` nas letras de OP/ED (Guilty Crown) ou cores ilegíveis | Resíduo de mascaramento da Fase 05a + estilo `OP`/`ED` original | Rode [Fase 11](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-11.md) (`corrigir_cores_musicas.py`) |
| `corrigir_guilty_crown.py` não encontra `.ass` | Pasta de origem informada no prompt está errada | Confirme o caminho (padrão `E:\animes\GUILTY CROWN\1080p\legendas_eng`) |

---

## Fase 08 — Sincronização

| Sintoma | Causa provável | Ação |
|:---|:---|:---|
| `ffprobe não encontrado` | FFmpeg não está no PATH | Adicione `ffmpeg.exe`/`ffprobe.exe` ao PATH ([instalação](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/instalacao.md#ffmpeg--ffprobe)) |
| Drift reportado pelo `auditor_sincronia.py` | Legenda gerada com FPS diferente do vídeo | Use `subtitle_fixer.py` (shift) ou `subtitle_stretcher.py` (ratio+offset) |
| Diálogo de seleção de arquivo não abre | `tkinter` ausente (raro) | Reinstale Python com "tcl/tk" marcado no instalador oficial |

---

## Fase 03 — Otimização de vídeo (GPU)

| Sintoma | Causa provável | Ação |
|:---|:---|:---|
| `hevc_nvenc não disponível` | GPU sem suporte NVENC ou driver desatualizado | `ffmpeg -encoders \| Select-String nvenc`; atualize driver NVIDIA |
| Vídeo não recomprimido | Não atende critério (já é H.264 ≤3Mbps, não Hi10P) | Comportamento esperado — script só recomprime H.264 Hi10P ou bitrate >3Mbps |
| Saída maior que o original | `maxrate` não respeitado por preset | Ajuste `preset`/`maxrate` em `gpu_video_optimizer.py` |

---

## Qual esteira usar?

| Cenário | Esteira | Fases |
|:---|:---|:---|
| Legenda **ASS embutida** (inglês, Eighty-Six) | A | 05a → [07] → 12 → [10] |
| Legenda **SRT externa** (inglês) | B | 05a → 04 → 12 |
| Legenda **PGS** (Blu-ray bitmap) | C | 02 → OCR → 04 → 12 |
| Legenda **ASS embutida** (francês, Macross Delta TV) | D | 05b → [07] → 12 → [10] |
| Macross Delta Filme 2 (francês) | E | 05b → 07 → 10 → 12 |
| Lote ASS pré-extraído (Gundam Reconguista) | F | 02 → 05a → [07] → 12 |
| Gundam Unicorn (especializada) | G | 02 → 05a → [06] → [07] → 12 → [10] |
| Guilty Crown (correção de nomes e cores) | H | 02 → 05a → [07] → 11 → 12 → [10] |
| Gundam The Origin, legenda **chinesa** (Qwen2.5) | I | 02 → 05c → [07] → 12 → [10] |
| Gundam Origin, legenda **francesa** (SUBFRENCH) | J | 05b → [07] → 12 |
| Gundam Zeta (TranslateGemma) | K | 05c-2 → [07] → 12 |
| Gundam ZZ (Mistral Nemo recomendado; TranslateGemma legado) | L | 05b ou 05c-2 → [07] → 12 |
| Detonator Orgun (Mistral Nemo, inglês) | M | 05b → [07] → 12 |
| Knights of Sidonia | N | 05a → [07] → 12 |

Em qualquer esteira, se restarem `[ERRO_TRADUCAO:]` após a tradução, aplique a [Fase 07](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-07.md) (reparo via IA), [Fase 11](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-11.md) (offline, Guilty Crown) ou o reparo da [Fase 05c](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-05c.md#repara_erros_origin_zhpy) (Gundam The Origin chinês). Erros de lore residuais e gramática por título: [Fase 07](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-07.md) (higienização por título) e [Fase 10](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-10.md) (QA final).

[Arquitetura](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/arquitetura.md) · [Pipeline SRT](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/pipeline-srt.md)

---

## Stack resumida

| Camada | Tecnologia | Fases |
|:---|:---|:---|
| Orquestração | Python 3.10+ | Todas |
| Container/Remux | MKVToolNix | 02, 05a, 05b, 06, 12, 10 (opcional) |
| Metadados | pymediainfo + MediaInfo | 01 |
| Tradução IA (inglês) | LM Studio + Gemma 4B | 05a, 07 |
| Tradução IA (francês/inglês) | LM Studio + Mistral Nemo Instruct 2407 | 05b |
| Tradução IA (chinês) | LM Studio + Qwen2.5-7B-Instruct | 05c |
| Tradução/Revisão IA (inglês) | LM Studio + TranslateGemma 12B | 05c-2 |
| Conversão legenda | SRT → ASS + sync FPS | 04 |
| Higienização e Reparos | Regex/dicionário de lore + reparo de falhas (07 com IA, 11 offline) | 07, 11 |
| Sincronização/Otimização | FFmpeg/FFprobe (NVENC) | 08, 03 |
| Karaokê | Extração/injeção de linhas OP/ED entre legendas | 09 |
| Revisão final por título | Regex/dicionário hardcoded por série + remux opcional | 10 |
| Terminal | colorama + tqdm | Todas |

---

[← Logs](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/logs-e-auditoria.md) · [Instalação](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/instalacao.md)
