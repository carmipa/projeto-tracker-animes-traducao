# ⚠️ Solução de problemas

[← Índice](README.md) · [Logs](logs-e-auditoria.md)

---

## Geral (todas as esteiras)

| Sintoma | Causa provável | Ação |
|:---|:---|:---|
| `mkvextract.exe`/`mkvmerge.exe não encontrados` | MKVToolNix ausente | Instale em `C:\Program Files\MKVToolNix\` |
| `LM Studio não responde` / `LM Studio offline` | Servidor parado ou modelo não carregado | Inicie LM Studio na porta **1234** com `google/gemma-4-e4b` |
| `pymediainfo nao esta instalado` | Pacote/DLL ausente | `pip install pymediainfo` + instale [MediaInfo](https://mediaarea.net/en/MediaInfo/Download) |
| Caracteres estranhos na legenda traduzida | Encoding legado (Latin-1/CP1252) mal detectado | Verifique `encodings_detectados` em `stats_*.json` (Fase 4) |

---

## Esteira A/D — Episódios MKV (Fases 4 → 5)

| Sintoma | Causa provável | Ação |
|:---|:---|:---|
| `Nenhuma faixa S_TEXT/ASS encontrada` | Legenda é PGS (bitmap) ou hardsub | Use [Esteira C](#esteira-c--pgs-fases-2--ocr--3--5) ou audite com [Fase 1](modulo-fase-1.md) |
| Episódio ignorado no remux (Fase 5) | Nome do `.ass` não casa com o `.mkv` | Garanta `{base}_PTBR.ass` em `traducao\` com o mesmo nome base do vídeo |
| Tradução muito lenta (Esteira D) | Multi-thread limitado a 2 | Esperado — `script_tradutor_fr.py` usa `ThreadPoolExecutor(max_workers=2)` |

---

## Esteira B — Filme / SRT externo (Fases 4 → 3 → 5)

| Sintoma | Causa provável | Ação |
|:---|:---|:---|
| `Nenhum arquivo .srt localizado` | Pasta vazia ou caminho errado | Confira o caminho informado ao `tradutor_srt_direto.py` |
| `Nenhuma legenda *_PTBR.srt` (Fase 3) | Fase 4 não rodou ou saída sem sufixo `_PTBR` | Execute a Fase 4 (tradução SRT) primeiro |
| Legenda dessincronizada no filme final | FPS 25 vs 23.976 | Fase 3 aplica `FATOR_SINCRO = 1.042709`; ajuste no script se a fonte tiver outro FPS |
| Remux sem par (Fase 5) | Nome `.ass` ≠ nome `.mkv` | Edite `nome_base_filme` em `conversor_srt_para_ass.py` (Fase 3) |
| Múltiplos `.srt` na pasta | Ambiguidade no prompt | Selecione o número correto no menu interativo da Fase 4 |

---

## Esteira C — PGS (Fases 2 → OCR → 3 → 5)

| Sintoma | Causa provável | Ação |
|:---|:---|:---|
| `Nenhuma faixa S_HDMV/PGS encontrada` | Release não tem legenda PGS | Use Esteira A/B/D conforme o formato real |
| OCR com muitos erros de caractere | Fonte PGS de baixa resolução | Ajuste o motor/idioma do OCR (Subtitle Edit + Tesseract) antes da Fase 3 |
| Fase 3 não encontra `*_PTBR.srt` | OCR não gerou sufixo correto | Renomeie a saída do OCR para `{base}_PTBR.srt` |

---

## Esteira E/F — Lote ASS / Gundam (Fases 2 → 4 → [8] → 5)

| Sintoma | Causa provável | Ação |
|:---|:---|:---|
| `[ABORTO]` ao extrair faixa (Fase 2) | Track IDs 4/5 não existem nesse release | Ajuste os IDs de fallback em `extrator_inteligente_ass.py` |
| Tags `\N`, `{\i1}` etc. quebradas após tradução | Falha no mascaramento `[T0]`/`[T1]` ou `___TAG___` | Rode [Fase 8](modulo-fase-8.md) (`cura_legendas_tag.py` ou `cura_gundam_mkv.py`) |
| Texto "TAG" literal aparecendo no MKV final (Gundam) | Corrupção conhecida do `batch_translator_unicorn.py` | `cura_gundam_mkv.py` — modo perfect-match (com `*_ENG.ass`) ou regex cego |
| Retry constante / poucas respostas da IA | Lote (`batch`) grande demais para o contexto do modelo | Reduza o tamanho do lote no script (`batch_translator_ass.py` / `_unicorn.py`) |

---

## Fase 6 — Sincronização

| Sintoma | Causa provável | Ação |
|:---|:---|:---|
| `ffprobe não encontrado` | FFmpeg não está no PATH | Adicione `ffmpeg.exe`/`ffprobe.exe` ao PATH ([instalação](instalacao.md#ffmpeg--ffprobe)) |
| Drift reportado pelo `auditor_sincronia.py` | Legenda gerada com FPS diferente do vídeo | Use `subtitle_fixer.py` (shift) ou `subtitle_stretcher.py` (ratio+offset) |
| Diálogo de seleção de arquivo não abre | `tkinter` ausente (raro) | Reinstale Python com "tcl/tk" marcado no instalador oficial |

---

## Fase 7 — Otimização de vídeo (GPU)

| Sintoma | Causa provável | Ação |
|:---|:---|:---|
| `hevc_nvenc não disponível` | GPU sem suporte NVENC ou driver desatualizado | `ffmpeg -encoders \| Select-String nvenc`; atualize driver NVIDIA |
| Vídeo não recomprimido | Não atende critério (já é H.264 ≤3Mbps, não Hi10P) | Comportamento esperado — script só recomprime H.264 Hi10P ou bitrate >3Mbps |
| Saída maior que o original | `maxrate` não respeitado por preset | Ajuste `preset`/`maxrate` em `gpu_video_optimizer.py` |

---

## Qual esteira usar?

| Cenário | Esteira | Fases |
|:---|:---|:---|
| Legenda **ASS embutida** (inglês) | A | 4 → 5 |
| Legenda **SRT externa** (inglês) | B | 4 → 3 → 5 |
| Legenda **PGS** (Blu-ray bitmap) | C | 2 → OCR → 3 → 5 |
| Legenda **ASS embutida** (francês) | D | 4 → 5 |
| Lote ASS pré-extraído (Gundam Reconguista) | E | 2 → 4 → 5 |
| Gundam Unicorn (especializada) | F | 2 → 4 → 8 → 5 |

[Arquitetura](arquitetura.md) · [Pipeline SRT](pipeline-srt.md)

---

## Stack resumida

| Camada | Tecnologia | Fases |
|:---|:---|:---|
| Orquestração | Python 3.10+ | Todas |
| Container/Remux | MKVToolNix | 2, 4, 5, 8 |
| Metadados | pymediainfo + MediaInfo | 1 |
| Tradução IA | LM Studio + Gemma 4B | 4 |
| Conversão legenda | SRT → ASS + sync FPS | 3 |
| Sincronização/Otimização | FFmpeg/FFprobe (NVENC) | 6, 7 |
| Terminal | colorama + tqdm | Todas |

---

[← Logs](logs-e-auditoria.md) · [Instalação](instalacao.md)
