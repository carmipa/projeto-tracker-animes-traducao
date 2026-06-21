# 🧹/🩹 Fase 07 — Higienização e Reparo de Tradução

[← Índice](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/README.md) · [Arquitetura](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/arquitetura.md) · [Guia de execução](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/guia-de-execucao.md)

**Pasta:** [`07_higienizacao_e_reparo_de_traducao/`](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/07_higienizacao_e_reparo_de_traducao/)

---

## O que faz

Esta fase unifica duas etapas vitais de pós-processamento de legendas já traduzidas (geralmente saídas das Fases 05a/05b/05c/05c-2):

1. **Higienização de Lore e Gramática por Título:** Normalização de termos específicos, jargões, patentes, marcas e formatação de tags ASS de forma personalizada por anime/filme (anteriormente Fase 00).
2. **Reparo de Falhas via IA:** Correção automatizada de tags corrompidas ou falhas marcadas com `[ERRO_TRADUCAO: ...]` usando o LM Studio, além de ferramentas de refino manual e offline (por exemplo, para resíduos de tradução em francês).

---

## Estrutura de Arquivos e Diretórios

Na pasta principal, os scripts e subpastas estão organizados da seguinte forma:

```
07_higienizacao_e_reparo_de_traducao/
├── 86_Eighty_Six/                      # Higienização de Eighty-Six
├── Detonator_Orgun/                    # Higienização de Detonator Orgun
├── Guilty_Crown/                       # Higienização de Guilty Crown
├── Gundam_Origin/                      # Higienização de Gundam Origin (Francês)
├── Gundam_The_Origin/                  # Higienização de Gundam The Origin (Chinês)
├── Gundam_Unicorn/                     # Higienização de Gundam Unicorn
├── Gundam_Zeta/                        # Higienização de Gundam Zeta
├── Knights_of_Sidonia/                 # Higienização de Knights of Sidonia
├── Macross_Delta/                      # Higienização de Macross Delta TV
├── Macross_Delta_Filme_1/              # Higienização de Macross Delta Filme 1
├── Macross_Delta_Filme_2/              # Higienização de Macross Delta Filme 2
├── Sword_Art_Online_Filme_2/           # Higienização de SAO Filme 2
├── refino_frances_origin/              # Scripts de refino de tradução francesa
│   ├── aplica_linhas_revisadas.py
│   ├── extrai_linhas_suspeitas.py
│   └── refina_traducao_fr.py
├── limpa_erros_residuais.py            # Limpeza offline rápida de falhas
└── repara_erros_traducao.py            # Reparo de erros via IA (LM Studio)
```

---

## 1. Scripts de Reparo Geral

Usados para corrigir as marcações `[ERRO_TRADUCAO:]` geradas pelos tradutores automáticos quando um lote ou linha falha no processamento da LLM.

| Script | Entrada | Saída | Função |
|:---|:---|:---|:---|
| [repara_erros_traducao.py](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/07_higienizacao_e_reparo_de_traducao/repara_erros_traducao.py) | `legendas_eng/*_ENG.ass` + `legendas_ptbr/*_PTBR.ass` com erros | Mesmo arquivo PT-BR, editado em-place | Retradução cirúrgica linha por linha (lote unitário/batch=1) via LM Studio com CoT (Chain of Thought), preservando tags ASS. |
| [limpa_erros_residuais.py](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/07_higienizacao_e_reparo_de_traducao/limpa_erros_residuais.py) | Mesmo que acima | Mesmo arquivo PT-BR, editado em-place | Substitui as marcações de falha pelo texto em inglês original (sem IA) como um fallback rápido para termos protegidos ou nomes próprios. |

### Exemplo de execução:
```powershell
# Requer LM Studio rodando localmente na porta 1234 (Gemma 4B / TranslateGemma)
python ".\07_higienizacao_e_reparo_de_traducao\repara_erros_traducao.py" "<caminho_legendas_eng>" "<caminho_legendas_ptbr>"

# Para limpeza offline rápida dos erros remanescentes
python ".\07_higienizacao_e_reparo_de_traducao\limpa_erros_residuais.py" "<caminho_legendas_eng>" "<caminho_legendas_ptbr>"
```

> [!NOTE]
> Se o script `repara_erros_traducao.py` exibir `[ABORTADO] 5 falhas consecutivas`, significa que o servidor do LM Studio está offline ou instável. As linhas já corrigidas são gravadas no arquivo em tempo real, portanto, basta restaurar o servidor e reexecutar o script.

---

## 2. Refino de Francês (Gundam The Origin)

Scripts específicos localizados na subpasta [`refino_frances_origin/`](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/07_higienizacao_e_reparo_de_traducao/refino_frances_origin/) para o pipeline de tradução francesa de Gundam Origin.

| Script | Entrada | Saída | Função |
|:---|:---|:---|:---|
| [refina_traducao_fr.py](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/07_higienizacao_e_reparo_de_traducao/refino_frances_origin/refina_traducao_fr.py) | `legendas_ptbr/*_ENG.ass` (traduzido) + `traducao_cache_fr.json` | Arquivos ASS refinados + relatório | Efetua revisão de gênero, concordância e patentes aplicando engenharia reversa do cache francês. |
| [extrai_linhas_suspeitas.py](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/07_higienizacao_e_reparo_de_traducao/refino_frances_origin/extrai_linhas_suspeitas.py) | Legendas traduzidas em PT-BR | `linhas_para_revisar.json` | Varre as legendas e exporta as falas suspeitas que necessitam de avaliação humana. |
| [aplica_linhas_revisadas.py](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/07_higienizacao_e_reparo_de_traducao/refino_frances_origin/aplica_linhas_revisadas.py) | `linhas_revisadas.json` (editado pelo usuário) | Legendas ASS atualizadas | Insere as falas corrigidas de volta nas legendas finais e atualiza os caches globais. |

### Exemplo de execução:
```powershell
# Execução na subpasta específica
cd "D:\PROJETOS-OPEN\projeto-tracker-animes-traducao\07_higienizacao_e_reparo_de_traducao\refino_frances_origin"
python .\refina_traducao_fr.py
```

---

## 3. Scripts de Higienização por Título

Esses scripts executam substituições de dicionário e expressões regulares (regex) baseadas nas diretrizes de lore de cada série.

| Pasta de Trabalho | Scripts Principais | Título / Alvo | Detalhes da Limpeza |
|:---|:---|:---|:---|
| [`86_Eighty_Six/`](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/07_higienizacao_e_reparo_de_traducao/86_Eighty_Six/) | `audit_86.py`, `limpeza_geral_86.py` | Eighty-Six (Esteira A) | Normalização de patentes militares, jargões específicos e auditoria de marcas. |
| [`Detonator_Orgun/`](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/07_higienizacao_e_reparo_de_traducao/Detonator_Orgun/) | `limpeza_geral_orgun.py` | Detonator Orgun (Esteira M) | Correção ortográfica e consistência de marcas do universo de Orgun. |
| [`Guilty_Crown/`](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/07_higienizacao_e_reparo_de_traducao/Guilty_Crown/) | `limpeza_geral_guilty.py` | Guilty Crown (Esteira H) | Roda logo após a aplicação das cores da Fase 11. |
| [`Gundam_Origin/`](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/07_higienizacao_e_reparo_de_traducao/Gundam_Origin/) | `limpeza_origin_extrema.py`, `limpeza_origin_finais.py`, `limpeza_origin_gramatica_profunda.py`, `limpeza_origin_total.py` | Gundam Origin (Esteira J) | Conjunto de 4 scripts para arrumar quebras `\N` inválidas e resolver francesismos/vocabulário do cache. |
| [`Gundam_The_Origin/`](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/07_higienizacao_e_reparo_de_traducao/Gundam_The_Origin/) | `limpeza_geral_origin.py` | Gundam The Origin (Esteira I) | Higienização focada na tradução oriunda de caracteres chineses. |
| [`Gundam_Unicorn/`](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/07_higienizacao_e_reparo_de_traducao/Gundam_Unicorn/) | `limpeza_geral_unicorn.py` | Gundam Unicorn (Esteira G) | Higienização ortográfica e lore pós-tradução de Unicorn. |
| [`Gundam_Zeta/`](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/07_higienizacao_e_reparo_de_traducao/Gundam_Zeta/) | `limpeza_zeta_extrema.py` | Gundam Zeta (Esteira K) | Motor regex `\b` case-insensitive para lore e balanceamento de tags de itálico/negrito. |
| [`Knights_of_Sidonia/`](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/07_higienizacao_e_reparo_de_traducao/Knights_of_Sidonia/) | `limpeza_sidonia_extrema.py` | Knights of Sidonia (Esteira N) | Ajustes gramaticais e jargões espaciais (Ex: Gardes, Kabizashi). |
| [`Macross_Delta/`](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/07_higienizacao_e_reparo_de_traducao/Macross_Delta/) | `limpeza_geral_macross.py` | Macross Delta TV (Esteira D) | Ajuste de termos de música/lore. |
| [`Macross_Delta_Filme_1/`](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/07_higienizacao_e_reparo_de_traducao/Macross_Delta_Filme_1/) | `limpeza_macross_filme1_extrema.py` | Macross Delta Filme 1 | Higienização de lore para o primeiro filme da série Delta. |
| [`Macross_Delta_Filme_2/`](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/07_higienizacao_e_reparo_de_traducao/Macross_Delta_Filme_2/) | `limpeza_macross_filme2_extrema.py` | Macross Delta Filme 2 (Esteira E) | Higienização do lore específico do filme. |
| [`Sword_Art_Online_Filme_2/`](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/07_higienizacao_e_reparo_de_traducao/Sword_Art_Online_Filme_2/) | `limpeza_sao_filme2_extrema.py` | SAO Filme 2 (Esteira C) | Correções estruturais de termos específicos de SAO Ordinal Scale. |

### Exemplo de execução:
```powershell
python ".\07_higienizacao_e_reparo_de_traducao\Gundam_Zeta\limpeza_zeta_extrema.py"
```

---

## Relação com outras fases

- **Precedência:** Roda obrigatoriamente depois das Fases **05a/05b/05c/05c-2** (exige legendas já traduzidas).
- **Interação com Fase 10 (Revisão):** Pode rodar antes ou depois da Fase 10 (não há ordem de dependência rígida, dependendo do que o script de QA do título necessitar).
- **Conserto de Erros Estruturais:** Atua como fase de fallback antes do remux final ([Fase 12](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-12.md)).

---

[← Fase 06](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-06.md) · [Índice](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/README.md) · [Fase 08 →](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/docs/modulo-fase-08.md)
