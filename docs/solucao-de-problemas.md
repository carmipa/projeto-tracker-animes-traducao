# ⚠️ Solução de problemas

[← Índice](README.md)

---

## Esteira MKV (Fases 0–2)

| Sintoma | Causa provável | Ação |
|:---|:---|:---|
| `mkvextract.exe não encontrados` | MKVToolNix ausente | `C:\Program Files\MKVToolNix\` |
| `LM Studio não responde` | Servidor parado | Porta **1234** + modelo carregado |
| `Nenhuma faixa S_TEXT/ASS` | PGS/hardsub | [Fase 0](modulo-fase-0.md) |
| Episódio ignorado no remux | Nome incorreto | `{base}_PTBR.ass` em `traducao\` |
| Caracteres estranhos | Encoding legado | `stats_*.json` → `encodings_detectados` |
| `pymediainfo nao esta instalado` | Pacote/DLL | `pip install pymediainfo` + MediaInfo |

---

## Esteira SRT (Fases 5–6–2)

| Sintoma | Causa provável | Ação |
|:---|:---|:---|
| `LM Studio offline` | Servidor inativo | Inicie na porta **1234** antes da Fase 5 |
| `Nenhum arquivo .srt localizado` | Pasta vazia ou caminho errado | Confira pasta em `tradutor_srt_direto.py` |
| `Nenhuma legenda *_PTBR.srt` (Fase 6) | Fase 5 não rodou ou nome sem `_PTBR` | Execute Fase 5 primeiro |
| Legenda dessincronizada no filme | FPS 25 vs 23.976 | Fase 6 aplica `FATOR_SINCRO 1.042709`; ajuste no script se necessário |
| Remux sem par | Nome `.ass` ≠ nome `.mkv` | Edite `nome_base_filme` em `conversor_srt_para_ass.py` |
| `[ABORTO] Falha na GPU` (Fase 5) | Timeout 120s ou lote grande | Reduza tamanho do lote no prompt interativo |
| Múltiplos `.srt` na pasta | Ambiguidade | Selecione o número correto no menu da Fase 5 |

---

## Qual esteira usar?

| Cenário | Esteira |
|:---|:---|
| Legenda **dentro** do `.mkv` (ASS) | 0 → 1 → 2 |
| Arquivo **`.srt` separado** | 5 → 6 → 2 |

[Pipeline SRT](pipeline-srt.md)

---

## Stack resumida

| Camada | Tecnologia | Fases |
|:---|:---|:---|
| Orquestração | Python 3.10+ | Todas |
| Container | MKVToolNix | 1, 2 |
| Metadados | pymediainfo + MediaInfo | 0 |
| Tradução IA | LM Studio + Gemma 4B | 1, 5 |
| Conversão legenda | SRT → ASS + sync FPS | 6 |
| Terminal | colorama + tqdm | Todas |

---

[← Logs](logs-e-auditoria.md) · [Instalação](instalacao.md)
