# 🇫🇷 Fase 05b — Tradução IA (LM Studio + Mistral Nemo Instruct 2407)

[← Índice](README.md) · [Arquitetura](arquitetura.md) · [Guia de execução](guia-de-execucao.md)

**Pasta:** [`05b_tradutor_llm_mistral_nemo/`](../05b_tradutor_llm_mistral_nemo/)

---

## O que faz

Motor de tradução via LM Studio + **Mistral Nemo Instruct 2407 (GGUF)** — substituiu o Gemma 4B para o par francês→português (qualidade muito superior) e também é usado em títulos em inglês que precisam de prompt mais controlado, como Detonator Orgun e Mobile Suit Gundam ZZ.

---

## Scripts

| Script | Entrada | Saída | Título / Esteira |
|:---|:---|:---|:---|
| `frances_para_ptbr/macross_deslta.py` | `.mkv` (ASS embutido FR) | `traducao/*_PTBR.ass` | Macross Delta TV (Esteira D) e Filme 2 (Esteira E) — extrai + traduz, multi-thread (2 threads) |
| `frances_para_ptbr/script_tradutor_fr_gundam_origin.py` | `.mkv` (ASS embutido FR, SUBFRENCH) | `traducao/*_PTBR.ass` | Gundam Origin, legenda francesa (Esteira J) |
| `Detonator_Orgun/script_tradutor_en_detonator_orgun.py` | `.mkv`/`.srt` (EN) | `traducao/*_PTBR.ass` | Detonator Orgun (Esteira M) — validador anti-alucinação em inglês |
| `Gundam_ZZ/tradutor_mistral_gundam_zz.py` | Pasta ou arquivos `.ass` (EN) | `*_PTBR.ass` em pasta indicada ou `TRADUZIDAS_ZZ/` | Gundam ZZ (Esteira L alternativa/recomendada) — prompt Universal Century, cache, auditoria, fallback individual e glossário ZZ |

Cada subpasta mantém seu próprio cache (`traducao_cache_fr.json`, `traducao_cache_orgun_en.json`, `traducao_cache_zz_en.json`).

---

## Uso típico

```powershell
# Pré-requisito: LM Studio na porta 1234 com mistralai/mistral-nemo-instruct-2407 (GGUF) carregado
python ".\05b_tradutor_llm_mistral_nemo\frances_para_ptbr\macross_deslta.py"
python ".\05b_tradutor_llm_mistral_nemo\frances_para_ptbr\script_tradutor_fr_gundam_origin.py"
python ".\05b_tradutor_llm_mistral_nemo\Detonator_Orgun\script_tradutor_en_detonator_orgun.py"
python ".\05b_tradutor_llm_mistral_nemo\Gundam_ZZ\tradutor_mistral_gundam_zz.py" "C:\animes\Gundam_ZZ\legendas_eng" --saida "C:\animes\Gundam_ZZ\legendas_ptbr"
```

---

## Gundam ZZ — melhorias incorporadas ao Mistral Nemo

`Gundam_ZZ/tradutor_mistral_gundam_zz.py` é o tradutor especializado de **Mobile Suit Gundam ZZ / Double Zeta (UC 0088)** via Mistral Nemo. Ele aceita a pasta de legendas pelo argumento posicional, por `--entrada`, `--pasta` ou `--origem`, e também permite arquivos específicos por `--arquivo`.

Exemplos:

```powershell
python ".\05b_tradutor_llm_mistral_nemo\Gundam_ZZ\tradutor_mistral_gundam_zz.py" "C:\animes\Gundam_ZZ\legendas_eng" --saida "C:\animes\Gundam_ZZ\legendas_ptbr"
python ".\05b_tradutor_llm_mistral_nemo\Gundam_ZZ\tradutor_mistral_gundam_zz.py" --entrada "C:\animes\Gundam_ZZ\legendas_eng" --saida "C:\animes\Gundam_ZZ\legendas_ptbr"
python ".\05b_tradutor_llm_mistral_nemo\Gundam_ZZ\tradutor_mistral_gundam_zz.py" --pasta "C:\animes\Gundam_ZZ\legendas_eng" --saida "C:\animes\Gundam_ZZ\legendas_ptbr"
python ".\05b_tradutor_llm_mistral_nemo\Gundam_ZZ\tradutor_mistral_gundam_zz.py" --origem "C:\animes\Gundam_ZZ\legendas_eng" --saida "C:\animes\Gundam_ZZ\legendas_ptbr"
python ".\05b_tradutor_llm_mistral_nemo\Gundam_ZZ\tradutor_mistral_gundam_zz.py" --arquivo ep01.ass ep02.ass --saida "C:\animes\Gundam_ZZ\legendas_ptbr"
```

Principais decisões registradas para a IA:

| Área | Regra / comportamento |
|:---|:---|
| Nome de saída | Sempre gerar `*_PTBR.ass`; arquivos sem `_ENG` também recebem `_PTBR`; evita sobrescrever a legenda inglesa. |
| Pasta de saída | `--saida` pode apontar para pasta ainda inexistente; o script cria a pasta. Sem `--saida`, usa `TRADUZIDAS_ZZ/` dentro da pasta de entrada. |
| Varredura | `listar_arquivos_ass()` percorre subpastas, ignora `logs` e `traduzidas_zz`; `caminho_saida_relativo()` preserva estrutura de subpastas. |
| CLI | `--arquivo` tem prioridade sobre pasta; no modo lote, a pasta pode ser posicional, `--entrada`, `--pasta` ou `--origem`; sem parâmetro, pergunta interativamente. |
| Tags ASS | Tags `{...}` são mascaradas em `[T0]`, `[T1]`, validadas e restauradas; `\N`/`\n` são preservados. |
| Resiliência | Lotes com resposta parcial acionam fallback individual; falhas definitivas viram `[ERRO_TRADUCAO: ...]` e entram em logs de auditoria. |
| Logs | Gera `pipeline_zz_en_*`, `erros_zz_en_*`, `falhas_zz_en_*`, `stats_zz_en_*` e `relatorio_zz_en_*`. |
| Integração | Expõe `SYSTEM_PROMPT = PipelineMistralZZ.PROMPT_SISTEMA` para uso pelo reparador genérico. |

Glossário e lore protegidos no prompt/pós-processamento:

| Categoria | Termos protegidos / normalizações |
|:---|:---|
| Facções e locais | `Neo Zeon`, `A.E.U.G.`, `Anaheim Electronics`, `Earth Federation`, `Karaba`, `Shangri-La`, `Axis`, `Moon-Moon`, `Granada`, `Dakar`, `Dublin`, `Side 1`, `Side 3`. |
| Tripulação/aliados | `Judau Ashta`, `Roux Louka`, `Beecha Oleg`, `Iino Abbav`, `Mondo Agake`, `Elle Vianno`, `Leina Ashta`, `Bright Noa`, `Astonaige Medoz`, `Hayato Kobayashi`, `Kamille Bidan`, `Fa Yuiry`, `Emary Ounce`, `Shinta`, `Qum`, `Sayla Mass`. |
| Neo Zeon | `Haman Karn`, `Lady Haman`, `Mashymre Cello`, `Chara Soon`, `Glemy Toto`, `Elpeo Ple`, `Ple Two`, `Gottn Goh`, `Gemon Bajack`, `Rakan Dahkaran`, `August Gidan`, `Illia Pazom`, `Mineva Lao Zabi`. |
| Mecha/naves | `Double Zeta`, `ZZ Gundam`, `Zeta Gundam`, `Hyaku Shiki`, `Mk-II`, `Core Top`, `Core Base`, `Core Fighter`, `Mega Rider`, `Qubeley`, `Bawoo`, `Dreissen`, `Doven Wolf`, `Quin Mantha`, `Geymalk`, `Zssa`, `Hamma-Hamma`, `R-Jarja`, `Gaza-C`, `Gaza-D`, `Galluss-J`, `Jamru Fin`, `Psycho Gundam Mk-II`, `Methuss`, `Argama`, `Nahel Argama`, `Endra`, `Sadalahn`, `Gwanban`. |
| Correções recorrentes | `Nova/Novo/Zeon Nova/Zeon Novo` → `Neo Zeon`; `Eixo` contextual → `Axis`; `Rainha/Queen/Quin Mansa` → `Quin Mantha`; `Puru Two/Puru Dois` → `Ple Two`; `Elpeo Puru` → `Elpeo Ple`; `Senhorita Haman` → `Lady Haman`; `Brilhante Noa` → `Bright Noa`; `Cem Estilos` → `Hyaku Shiki`; `Marca Dois` → `Mk-II`. |
| Estilo PT-BR | Evitar calques: `I see` como concordância → `Entendo`; `Look out!` → `Cuidado!`; `Roger/Copy that` → `Copiado`/`Entendido`; manter tom militar conciso. |

Validações feitas após a alteração:

```powershell
.\.venv\Scripts\python.exe -m py_compile ".\05b_tradutor_llm_mistral_nemo\Gundam_ZZ\tradutor_mistral_gundam_zz.py"
.\.venv\Scripts\python.exe ".\05b_tradutor_llm_mistral_nemo\Gundam_ZZ\tradutor_mistral_gundam_zz.py" --help
```

Teste funcional interno confirmou:

- `Mobile.Suit.ZZ.S01E01_ENG.ass` → `Mobile.Suit.ZZ.S01E01_PTBR.ass`.
- `Mobile.Suit.ZZ.S01E01.ass` → `Mobile.Suit.ZZ.S01E01_PTBR.ass`.
- `Rainha Mansa`, `Senhorita Haman`, `ao Eixo`, `Zeta Duplo` são normalizados para `Quin Mantha`, `Lady Haman`, `a Axis`, `Double Zeta`.

---

## Nota — rótulo de modelo desatualizado em `config_fr_*.txt`

O snapshot de configuração (`config_fr_*.txt`) ainda imprime "Modelo: Gemma 4B" em ambos os scripts de `frances_para_ptbr/`, resíduo da época em que esses scripts usavam Gemma 4B. **A tradução em si usa o modelo correto** (Mistral Nemo) — confira o modelo real na linha `Usando modelo: ...` do `pipeline_fr_*.txt`. Detalhes: [Solução de problemas](solucao-de-problemas.md#fase-05b--mistral-nemo-francês-e-inglês).

---

[← Fase 05a](modulo-fase-05a.md) · [Índice](README.md) · [Fase 05c →](modulo-fase-05c.md)
