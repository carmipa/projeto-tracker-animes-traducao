# ⚠️ Solução de problemas

[← Índice](README.md)

---

## Erros comuns

| Sintoma | Causa provável | Ação |
|:---|:---|:---|
| `mkvextract.exe não encontrados` | MKVToolNix ausente | Reinstale em `C:\Program Files\MKVToolNix\` |
| `LM Studio não responde` | Servidor parado | Porta **1234** + modelo carregado |
| `Nenhuma faixa S_TEXT/ASS` | Legenda PGS/hardsub | [Fase 0](modulo-fase-0.md) — PGS não é texto |
| Episódio ignorado no remux | Nome da legenda incorreto | Deve ser `{base}_PTBR.ass` em `traducao\` |
| Caracteres estranhos | Encoding legado | Ver `stats_*.json` → `encodings_detectados` |
| `pymediainfo nao esta instalado` | Pacote ou DLL | `pip install pymediainfo` + [MediaInfo](https://mediaarea.net/en/MediaInfo/Download) |

---

## Stack resumida

| Camada | Tecnologia |
|:---|:---|
| Orquestração | Python 3.10+ |
| Container Matroska | MKVToolNix |
| Metadados | pymediainfo + MediaInfo |
| Tradução | LM Studio + Gemma 4B |
| Terminal | colorama + tqdm |
| Legenda | ASS (`S_TEXT/ASS`) |

---

[← Logs](logs-e-auditoria.md) · [Instalação](instalacao.md)
