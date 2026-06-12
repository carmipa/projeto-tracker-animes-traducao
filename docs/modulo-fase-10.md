# 🎵 Módulo — Fase 10 (Correção Guilty Crown)

[← Índice](README.md) · [`10_correcao_guilty_crown/`](../10_correcao_guilty_crown/)

<p>
  <img src="https://img.shields.io/badge/Fase-10-4B0082?style=flat-square" alt="Fase 10"/>
  <img src="https://img.shields.io/badge/Tipo-Correção_offline-orange?style=flat-square" alt="Correção offline"/>
  <img src="https://img.shields.io/badge/100%25-Offline-success?style=flat-square" alt="100% Offline"/>
  <img src="https://img.shields.io/badge/Interativo-prompts_de_pasta-blue?style=flat-square" alt="Interativo"/>
  <img src="https://img.shields.io/badge/Especializado-Guilty_Crown-9146FF?style=flat-square" alt="Guilty Crown"/>
</p>

**Fases:** [1](modulo-fase-1.md) · [2](modulo-fase-2.md) · [3](modulo-fase-3.md) · [4](modulo-fase-4.md) · [5](modulo-fase-5.md) · [6](modulo-fase-6.md) · [7](modulo-fase-7.md) · [8](modulo-fase-8.md) · [9](modulo-fase-9.md) · **10**

**Especialização por série.** Pós-processamento **100% offline** (sem LM Studio) das legendas traduzidas de *Guilty Crown* (Esteira G): remove marcadores `[ERRO_TRADUCAO: ...]` residuais e ajusta cores/tags das músicas (OP/ED).

---

## Scripts

| Script | Atua sobre | Estratégia |
|:---|:---|:---|
| [`corrigir_guilty_crown.py`](../10_correcao_guilty_crown/corrigir_guilty_crown.py) | `.ass` traduzidos com `[ERRO_TRADUCAO: texto]` | Substitui o marcador pelo `texto` capturado via regex, instantâneo, sem IA |
| [`corrigir_cores_musicas.py`](../10_correcao_guilty_crown/corrigir_cores_musicas.py) | `.ass` corrigidos, linhas de estilo `OP*`/`ED*` | Normaliza cores (`\c`, `\1c`, `\3c`) para branco/preto e remove resíduos da palavra `TAG` |

---

## Diagrama de fluxo

```mermaid
flowchart TB
    A0(["legendas_eng/*.ass\ntraduzido com marcador ERRO_TRADUCAO"]) --> P1["corrigir_guilty_crown.py\nprompt: pasta origem / pasta destino"]

    P1 --> SCAN["Para cada Dialogue:\nregex captura o texto dentro do marcador ERRO_TRADUCAO"]
    SCAN --> REPL["Substitui o marcador\npelo texto capturado"]
    REPL --> RENAME["Renomeia arquivos de _ENG.ass para _PTBR.ass"]
    RENAME --> OUT1["legendas_ptbr/*_PTBR.ass\n+ relatorio_correcao.txt"]

    OUT1 --> P2["corrigir_cores_musicas.py\nprompt: pasta legendas_ptbr"]
    P2 --> STYLE{"Linha Style comeca\ncom OP ou ED?"}
    STYLE -->|Sim| FIXSTYLE["PrimaryColour = branco\nOutlineColour = preto"]
    STYLE -->|Nao| KEEP1["mantem estilo"]

    P2 --> DLG{"Dialogue ou Comment\ncom estilo OP/ED?"}
    DLG -->|Sim| CLEANTAG["remove residuo da palavra TAG\nfora das tags ASS"]
    CLEANTAG --> FIXCOLOR["normaliza tags de cor ASS:\nc e 1c para branco, 3c para preto"]
    DLG -->|Nao| KEEP2["mantem linha"]

    FIXSTYLE --> OUT2["legendas_ptbr/*.ass atualizado\n+ relatorio_cores_musicas.txt"]
    FIXCOLOR --> OUT2
    KEEP1 --> OUT2
    KEEP2 --> OUT2

    OUT2 --> NEXT["Fase 5 - Remux"]

    style P1 fill:#4B0082,stroke:#00E5FF,color:#fff
    style P2 fill:#4B0082,stroke:#00E5FF,color:#fff
    style OUT1 fill:#1e4620,stroke:#32CD32,color:#fff
    style OUT2 fill:#1e4620,stroke:#32CD32,color:#fff
```

---

## `corrigir_guilty_crown.py`

| Item | Detalhe |
|:---|:---|
| Entrada | Pasta com `.ass` traduzidos contendo `[ERRO_TRADUCAO: texto]` (padrão: `E:\animes\GUILTY CROWN\1080p\legendas_eng`) |
| Saída | Pasta de destino (padrão: `E:\animes\GUILTY CROWN\1080p\legendas_ptbr`), criada automaticamente |
| Processo | `regex_erro = r'\[ERRO_TRADUCAO:\s*(.*?)\s*\]'` — substitui cada ocorrência pelo grupo capturado (texto original, geralmente nomes próprios) |
| Renomeio | `*_ENG.ass` → `*_PTBR.ass`; outros nomes recebem sufixo `_PTBR` |
| Relatório | `relatorio_correcao.txt` — lista arquivos processados, correções por arquivo, total geral |
| Dependências | `colorama`, `tqdm` |

```powershell
python ".\10_correcao_guilty_crown\corrigir_guilty_crown.py"
# Prompts interativos:
#   Pasta com as legendas extraídas (com erros de tradução): [ENTER = padrão E:\animes\GUILTY CROWN\1080p\legendas_eng]
#   Pasta onde deseja salvar as legendas corrigidas:          [ENTER = padrão E:\animes\GUILTY CROWN\1080p\legendas_ptbr]
```

---

## `corrigir_cores_musicas.py`

| Item | Detalhe |
|:---|:---|
| Entrada | Pasta com `.ass` já corrigidos pela etapa anterior (padrão: `E:\animes\GUILTY CROWN\1080p\legendas_ptbr`) |
| Estilos `OP*`/`ED*` | Campo `PrimaryColour` → `&H00FFFFFF` (branco) e `OutlineColour` → `&H00000000` (preto) |
| Diálogos `OP*`/`ED*` | Remove resíduos da palavra `TAG`/`tag` fora de blocos `{...}`; normaliza `\c`/`\1c` → `\c&HFFFFFF&` e `\3c` → `\3c&H000000&` |
| Saída | Sobrescreve os `.ass` na mesma pasta + `relatorio_cores_musicas.txt` |
| Relatório | Estilos redefinidos, linhas com correção de cor, resíduos de `TAG` removidos, tempo total |
| Dependências | `colorama`, `tqdm` |

```powershell
python ".\10_correcao_guilty_crown\corrigir_cores_musicas.py"
# Prompt interativo:
#   Pasta com as legendas PT-BR corrigidas: [ENTER = padrão E:\animes\GUILTY CROWN\1080p\legendas_ptbr]
```

---

## Quando usar

- Série **Guilty Crown** (ou similar) cuja tradução em lote (Fase 4) deixou marcadores `[ERRO_TRADUCAO: ...]` que correspondem a **nomes próprios/termos que devem permanecer como no inglês** — não requer LM Studio, ao contrário da [Fase 9](modulo-fase-9.md).
- Músicas (OP/ED) com cores de fonte ilegíveis ou com a palavra `TAG` aparecendo na letra — rode `corrigir_cores_musicas.py` após `corrigir_guilty_crown.py`.
- Faz parte da **Esteira G**: ver [Arquitetura — Esteira G](arquitetura.md#esteira-g--guilty-crown-correção-de-nomes-e-cores-de-músicas).

---

[← Fase 9](modulo-fase-9.md) · [Arquitetura](arquitetura.md)
