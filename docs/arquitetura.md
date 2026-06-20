# 🏗️ Arquitetura do Pipeline

[← Índice da documentação](README.md) · [README principal](../README.md)

<p>
  <img src="https://img.shields.io/badge/Fases-00_a_12-blueviolet?style=flat-square" alt="Fases 00 a 12"/>
  <img src="https://img.shields.io/badge/Esteiras-A_a_N-9146FF?style=flat-square" alt="Esteiras A-N"/>
  <img src="https://img.shields.io/badge/100%25-Offline-success?style=flat-square" alt="Offline"/>
  <img src="https://img.shields.io/badge/Remux-Sem_Re--encode-blue?style=flat-square" alt="Remux sem re-encode"/>
</p>

O projeto é organizado em **fases prefixadas de `00` a `12`** (a Fase 05 tem três variantes de motor de IA: `05a`, `05b`, `05c`, mais uma irmã `05c-2` que compartilha o prefixo de pasta com `05c`). Cada **esteira** (fluxo de trabalho) usa um subconjunto dessas fases, dependendo do formato de origem da legenda (ASS embutido, SRT externo, PGS bitmap, ASS chinês), do idioma de origem (inglês, francês, chinês simplificado) e do título específico.

---

## Mapa de fases

| Fase | Pasta | Função | Doc |
|:---:|:---|:---|:---|
| **00** | `00_scripts_higienizacao/` | Normalização de lore/gramática por título (pós-tradução) | [Fase 00](modulo-fase-00.md) |
| **01** | `01_analisador_midia/` | Audita mídia: codecs, faixas, sincronia | [Fase 01](modulo-fase-01.md) |
| **02** | `02_extrator_legenda/` | Extrai legenda original (ASS/SRT/PGS) do `.mkv` | [Fase 02](modulo-fase-02.md) |
| **03** | `03_decodificador_caracteres/` | Auxiliar: recomprime vídeo (HEVC/NVENC) | [Fase 03](modulo-fase-03.md) |
| **04** | `04_conversor_srt_ass/` | Converte `*_PTBR.srt` → `*_PTBR.ass` com sync de FPS | [Fase 04](modulo-fase-04.md) |
| **05a** | `05a_tradutor_llm_gemma4/` | 🤖 Tradução via LM Studio + Gemma 4B (multi-título, inglês) | [Fase 05a](modulo-fase-05a.md) |
| **05b** | `05b_tradutor_llm_mistral_nemo/` | 🇫🇷 Tradução via LM Studio + Mistral Nemo 2407 (francês + inglês) | [Fase 05b](modulo-fase-05b.md) |
| **05c** | `05c_tradutor_llm_qwen2/` | 🐉 Tradução via LM Studio + Qwen2.5-7B (chinês simplificado) | [Fase 05c](modulo-fase-05c.md) |
| **05c-2** | `05c_tradutor_llm_translategemma/` | 🌐 Tradução/revisão via LM Studio + TranslateGemma 12B (inglês) | [Fase 05c-2](modulo-fase-05c2.md) |
| **06** | `06_cura_legendas/` | 🩹 Auxiliar: cura offline de tags ASS corrompidas | [Fase 06](modulo-fase-06.md) |
| **07** | `07_reparo_traducao/` | 🩹 Reparo avulso (batch=1) de `[ERRO_TRADUCAO:]` via IA | [Fase 07](modulo-fase-07.md) |
| **08** | `08_sincronizacao_legenda/` | ⏱️ Auxiliar: audita/corrige dessincronia áudio×legenda | [Fase 08](modulo-fase-08.md) |
| **09** | `09_injetor_musicas/` | 🎵 Injeta karaokê OP/ED/Insert Songs de fansubs | [Fase 09](modulo-fase-09.md) |
| **10** | `10_auditoria_e_revisao/` | 🔬 Revisão/correção final por título (lore, resíduos, remux) | [Fase 10](modulo-fase-10.md) |
| **11** | `11_correcao_projetos_legados/` | 🎨 Correção offline de cores/marcadores em legendas antigas | [Fase 11](modulo-fase-11.md) |
| **12** | `12_remuxer_mkvmerge/` | 🎬 Remux: junta vídeo + legenda PT-BR | [Fase 12](modulo-fase-12.md) |

As fases **00, 01, 03, 06, 07, 08, 09, 11** são **auxiliares/transversais** — usadas conforme necessário, em qualquer esteira. A **Fase 00** é um caso especial: o prefixo `00` é só ordenação alfabética, não posição real no fluxo — ela normaliza lore/gramática de uma legenda **já traduzida** (roda em paralelo às fases 06/07/10/11). As fases **02, 04, 05x e 12** formam o núcleo de extração/tradução/remux de cada esteira. As fases **05a, 05b, 05c e 05c-2** não são sequenciais entre si — são **variantes de motor de IA** do mesmo papel (extrai + traduz), escolhidas pelo idioma de origem e pelo título: Gemma 4B (05a) para a maioria dos títulos em inglês, Mistral Nemo Instruct 2407 (05b) para francês e alguns títulos em inglês, Qwen2.5-7B (05c) para chinês simplificado, e TranslateGemma 12B (05c-2) para Gundam Zeta/ZZ e revisão gramatical de PT-BR. As fases **06, 07 e 11** são **reparos pós-tradução**. A **Fase 10** é o catálogo de **scripts de QA por título**, aplicado depois (ou antes, conforme o script) do remux, para corrigir erros de lore e remultiplexar o `.mkv` final.

---

## Visão geral — todas as esteiras

```mermaid
flowchart LR
    MKV["Vídeo .mkv"] --> F1["Fase 01<br/>Analisador (opcional)"]

    F1 -->|"ASS embutido EN, Eighty-Six"| A05A["Fase 05a<br/>86/sub_extractor.py"]
    F1 -->|"ASS embutido EN, Sidonia"| N05A["Fase 05a<br/>tradutor_ass/batch_translator_sidonia.py"]
    F1 -->|"ASS embutido EN, lote pré-extraído"| E02["Fase 02<br/>extrator_inteligente_ass.py"]
    F1 -->|"ASS embutido EN, Gundam Zeta"| K05C2["Fase 05c-2<br/>Gundam_Zeta/script_tradutor_en_gundam_zeta.py"]
    F1 -->|"ASS embutido EN, Gundam ZZ"| L05C2["Fase 05c-2<br/>Gundam_ZZ/script_tradutor_en_gundam_zz.py"]
    F1 -->|"ASS embutido EN, Detonator Orgun"| M05B["Fase 05b<br/>Detonator_Orgun/script_tradutor_en_detonator_orgun.py"]
    F1 -->|"ASS embutido FR, Macross Delta"| D05B["Fase 05b<br/>frances_para_ptbr/macross_deslta.py"]
    F1 -->|"ASS embutido FR, Gundam Origin"| J05B["Fase 05b<br/>frances_para_ptbr/script_tradutor_fr_gundam_origin.py"]
    F1 -->|"ASS chinês CHS, Gundam The Origin"| I05C["Fase 05c<br/>batch_translator_origin_zh.py"]
    F1 -->|"SRT externo, filme"| B05A["Fase 05a<br/>5_tradutor_de_legenda/tradutor_srt_direto.py"]
    F1 -->|"PGS bitmap, filme/Blu-ray"| C02["Fase 02<br/>extrator_inteligente_pgs.py"]

    E02 --> E05A["Fase 05a<br/>tradutor_ass/batch_translator_ass.py<br/>(Gundam Reconguista)"]
    E02 --> G05A["Fase 05a<br/>tradutor_gundam_unicornio/batch_translator_unicorn.py<br/>(Gundam Unicorn)"]
    E02 --> H05A["Fase 05a<br/>tradutor_ass<br/>(Guilty Crown)"]

    G05A -.->|"se TAG corrompido"| F06["Fase 06<br/>Cura de legendas"]
    H05A -.->|"Guilty Crown"| F11["Fase 11<br/>Correção offline (cores/marcadores)"]

    C02 --> OCR["OCR externo<br/>Subtitle Edit + Tesseract"]
    OCR --> F04["Fase 04<br/>conversor_srt_para_ass.py"]
    B05A --> F04

    A05A --> HYG["Fase 00<br/>Higienização por título"]
    N05A --> HYG
    E05A --> HYG
    G05A --> HYG
    H05A --> HYG
    F06 --> HYG
    F11 --> HYG
    D05B --> HYG
    J05B --> HYG
    I05C --> HYG
    K05C2 --> HYG
    L05C2 --> HYG
    M05B --> HYG
    F04 --> HYG

    HYG -.->|"se restar ERRO_TRADUCAO"| F07["Fase 07<br/>Reparo avulso via IA"]
    F07 --> F10["Fase 10<br/>Revisão final (opcional)"]
    HYG --> F10

    F10 --> F12["Fase 12<br/>batch_remuxer.py"]
    F12 --> OUT["mkv_final_ptbr/*_PTBR.mkv"]

    OUT -.->|"opcional"| F08["Fase 08<br/>Sincronização"]
    OUT -.->|"opcional, arquivo grande"| F03["Fase 03<br/>Otimização GPU"]
    OUT -.->|"karaokê OP/ED"| F09["Fase 09<br/>Injetor de músicas"]

    style F1 fill:#2d3748,stroke:#00E5FF,color:#fff
    style HYG fill:#6b21a8,stroke:#d946ef,color:#fff
    style F10 fill:#2d3748,stroke:#00E5FF,color:#fff
    style F12 fill:#1e4620,stroke:#32CD32,color:#fff
    style OUT fill:#1e4620,stroke:#32CD32,color:#fff
    style F06 fill:#5c1010,stroke:#ff4444,color:#fff
    style F07 fill:#5c1010,stroke:#ff4444,color:#fff
    style F11 fill:#5c1010,stroke:#ff4444,color:#fff
    style OCR fill:#5c1010,stroke:#ff4444,color:#fff
    style D05B fill:#4B0082,stroke:#00E5FF,color:#fff
    style J05B fill:#4B0082,stroke:#00E5FF,color:#fff
    style M05B fill:#4B0082,stroke:#00E5FF,color:#fff
    style I05C fill:#4B0082,stroke:#00E5FF,color:#fff
    style K05C2 fill:#4B0082,stroke:#00E5FF,color:#fff
    style L05C2 fill:#4B0082,stroke:#00E5FF,color:#fff
```

---

## Esteira A — Eighty-Six (ASS embutido, inglês)

Fluxo padrão para episódios de série com legenda `S_TEXT/ASS` em inglês embutida no `.mkv`. Implementação: **Eighty-Six (86)**, via `05a_tradutor_llm_gemma4/86/sub_extractor.py`.

```mermaid
flowchart LR
    A_MKV["episodios/*.mkv"] --> A_F1["Fase 01 - opcional<br/>media_analyzer.py"]
    A_F1 --> A_F05A["Fase 05a<br/>86/sub_extractor.py<br/>(extrai + traduz)"]
    A_F05A --> A_ASS["traducao/*_PTBR.ass"]
    A_ASS -.->|"opcional"| A_HYG["Fase 00<br/>86_Eighty_Six/limpeza_geral_86.py"]
    A_HYG -.->|"opcional"| A_F10["Fase 10<br/>revisao_86.py"]
    A_MKV --> A_F12["Fase 12<br/>batch_remuxer.py"]
    A_ASS --> A_F12
    A_F10 -.-> A_F12
    A_F12 --> A_OUT["mkv_final_ptbr/*_PTBR.mkv"]

    style A_F05A fill:#4B0082,stroke:#00E5FF,color:#fff
    style A_HYG fill:#6b21a8,stroke:#d946ef,color:#fff
    style A_F10 fill:#2d3748,stroke:#00E5FF,color:#fff
    style A_F12 fill:#1e4620,stroke:#32CD32,color:#fff
```

```powershell
python ".\01_analisador_midia\media_analyzer.py"          # opcional
python ".\05a_tradutor_llm_gemma4\86\sub_extractor.py"
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
python ".\10_auditoria_e_revisao\revisao_86.py"           # opcional, corrige alucinações residuais + remux
```

---

## Esteira B — Filme com SRT externo (inglês)

Para filmes/releases cuja legenda em inglês vem **separada** em um `.srt`. Detalhes completos: [Pipeline SRT](pipeline-srt.md).

```mermaid
flowchart LR
    B_SRT["legenda/*.srt EN"] --> B_F05A["Fase 05a<br/>tradutor_srt_direto.py"]
    B_F05A --> B_SRTPT["legenda/*_PTBR.srt"]
    B_SRTPT --> B_F04["Fase 04<br/>conversor_srt_para_ass.py"]
    B_F04 --> B_ASS["traducao/*_PTBR.ass"]
    B_MKV["filme.mkv"] --> B_F12["Fase 12<br/>batch_remuxer.py"]
    B_ASS --> B_F12
    B_F12 --> B_OUT["mkv_final_ptbr/*_PTBR.mkv"]

    style B_F05A fill:#4B0082,stroke:#00E5FF,color:#fff
    style B_F04 fill:#2d3748,stroke:#00E5FF,color:#fff
    style B_F12 fill:#1e4620,stroke:#32CD32,color:#fff
```

```powershell
python ".\05a_tradutor_llm_gemma4\5_tradutor_de_legenda\tradutor_srt_direto.py"
python ".\04_conversor_srt_ass\conversor_srt_para_ass.py"
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
```

---

## Esteira C — Legenda PGS (Bluray bitmap)

Para releases Blu-ray cuja legenda é uma imagem (`S_HDMV/PGS`), sem texto extraível diretamente — exige OCR externo. Exemplo de título: **Sword Art Online — Filme 2**.

```mermaid
flowchart LR
    C_MKV["filme.mkv (PGS)"] --> C_F02["Fase 02<br/>extrator_inteligente_pgs.py"]
    C_F02 --> C_SUP["extraidos_sup/*.sup"]
    C_SUP --> C_OCR["OCR externo<br/>Subtitle Edit + Tesseract"]
    C_OCR --> C_SRTPT["legenda/*_PTBR.srt"]
    C_SRTPT --> C_F04["Fase 04<br/>conversor_srt_para_ass.py"]
    C_F04 --> C_ASS["traducao/*_PTBR.ass"]
    C_MKV --> C_F12["Fase 12<br/>batch_remuxer.py"]
    C_ASS --> C_F12
    C_F12 --> C_OUT["mkv_final_ptbr/*_PTBR.mkv"]

    style C_OCR fill:#5c1010,stroke:#ff4444,color:#fff
    style C_F04 fill:#2d3748,stroke:#00E5FF,color:#fff
    style C_F12 fill:#1e4620,stroke:#32CD32,color:#fff
```

```powershell
python ".\02_extrator_legenda\extrator_inteligente_pgs.py"
# OCR externo (Subtitle Edit + Tesseract) -> *_PTBR.srt
python ".\04_conversor_srt_ass\conversor_srt_para_ass.py"
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
```

> O OCR `.sup → .srt` **não faz parte** deste repositório.

---

## Esteira D — Macross Delta TV (Tradução Francês → PT-BR)

ASS embutido em francês, multi-thread (2 threads), glossário e cache persistente próprios.

```mermaid
flowchart LR
    D_MKV["episodios/*.mkv (FR)"] --> D_F05B["Fase 05b<br/>frances_para_ptbr/macross_deslta.py<br/>(extrai + traduz, 2 threads)"]
    D_F05B --> D_ASS["traducao/*_PTBR.ass"]
    D_ASS -.->|"opcional"| D_HYG["Fase 00<br/>Macross_Delta/limpeza_geral_macross.py"]
    D_HYG -.->|"opcional"| D_F10["Fase 10<br/>revisao_legenda_macross_delta.py"]
    D_MKV --> D_F12["Fase 12<br/>batch_remuxer.py"]
    D_ASS --> D_F12
    D_F10 -.-> D_F12
    D_F12 --> D_OUT["mkv_final_ptbr/*_PTBR.mkv"]

    style D_F05B fill:#4B0082,stroke:#00E5FF,color:#fff
    style D_HYG fill:#6b21a8,stroke:#d946ef,color:#fff
    style D_F10 fill:#2d3748,stroke:#00E5FF,color:#fff
    style D_F12 fill:#1e4620,stroke:#32CD32,color:#fff
```

```powershell
# Pré-requisito: LM Studio na porta 1234 com Mistral Nemo Instruct 2407 (GGUF) carregado
python ".\05b_tradutor_llm_mistral_nemo\frances_para_ptbr\macross_deslta.py"
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
python ".\10_auditoria_e_revisao\revisao_legenda_macross_delta.py"   # opcional, lore + tags ASS
```

---

## Esteira E — Macross Delta Filme 2 (Francês)

Mesmo motor da Esteira D, com revisão final dedicada ao filme.

```mermaid
flowchart LR
    E_MKV["filme2.mkv (FR)"] --> E_F05B["Fase 05b<br/>frances_para_ptbr/macross_deslta.py"]
    E_F05B --> E_ASS["traducao/*_PTBR.ass"]
    E_ASS --> E_HYG["Fase 00<br/>Macross_Delta_Filme_2/limpeza_macross_filme2_extrema.py"]
    E_HYG --> E_F10["Fase 10<br/>micross_delta_filme2.py<br/>(lore + remux)"]
    E_MKV --> E_F12["Fase 12<br/>batch_remuxer.py"]
    E_ASS --> E_F12
    E_F10 -.-> E_F12
    E_F12 --> E_OUT["mkv_final_ptbr/*_PTBR.mkv"]

    style E_F05B fill:#4B0082,stroke:#00E5FF,color:#fff
    style E_HYG fill:#6b21a8,stroke:#d946ef,color:#fff
    style E_F10 fill:#2d3748,stroke:#00E5FF,color:#fff
    style E_F12 fill:#1e4620,stroke:#32CD32,color:#fff
```

```powershell
python ".\05b_tradutor_llm_mistral_nemo\frances_para_ptbr\macross_deslta.py"
python ".\00_scripts_higienizacao\Macross_Delta_Filme_2\limpeza_macross_filme2_extrema.py"
python ".\10_auditoria_e_revisao\micross_delta_filme2.py"
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
```

---

## Esteira F — Lote ASS pré-extraído (Gundam Reconguista)

Para releases que exigem extração explícita antes da tradução (sem script dedicado por título).

```mermaid
flowchart LR
    F_MKV["episodios/*.mkv (EN)"] --> F_F02["Fase 02<br/>extrator_inteligente_ass.py"]
    F_F02 --> F_ENG["legendas_eng/*_ENG.ass"]
    F_ENG --> F_F05A["Fase 05a<br/>tradutor_ass/batch_translator_ass.py"]
    F_F05A --> F_ASS["traducao/*_PTBR.ass"]
    F_MKV --> F_F12["Fase 12<br/>batch_remuxer.py"]
    F_ASS --> F_F12
    F_F12 --> F_OUT["mkv_final_ptbr/*_PTBR.mkv"]

    style F_F05A fill:#4B0082,stroke:#00E5FF,color:#fff
    style F_F12 fill:#1e4620,stroke:#32CD32,color:#fff
```

```powershell
python ".\02_extrator_legenda\extrator_inteligente_ass.py"
python ".\05a_tradutor_llm_gemma4\tradutor_ass\batch_translator_ass.py"
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
```

---

## Esteira G — Gundam Unicorn (especializada)

Pipeline com cura de legendas (corrupção conhecida da palavra `TAG`) e revisão final por episódio.

```mermaid
flowchart LR
    G_MKV["episodios/*.mkv (EN)"] --> G_F02["Fase 02<br/>extrator_inteligente_ass.py"]
    G_F02 --> G_ENG["legendas_eng/*_ENG.ass"]
    G_ENG --> G_F05A["Fase 05a<br/>tradutor_gundam_unicornio/batch_translator_unicorn.py"]
    G_F05A --> G_ASS["traducao/*_PTBR.ass"]
    G_ASS -.->|"se TAG corrompido"| G_F06["Fase 06<br/>cura_legendas_tag.py"]
    G_F06 -.-> G_CURADA["traducao_curada/*_PTBR.ass"]
    G_ASS -.->|"opcional"| G_HYG["Fase 00<br/>Gundam_Unicorn/limpeza_geral_unicorn.py"]
    G_HYG -.->|"opcional"| G_F10["Fase 10<br/>revisao_legenda_gundam_unicornio.py"]
    G_MKV --> G_F12["Fase 12<br/>batch_remuxer.py"]
    G_ASS --> G_F12
    G_CURADA -.-> G_F12
    G_F10 -.-> G_F12
    G_F12 --> G_OUT["mkv_final_ptbr/*_PTBR.mkv"]
    G_OUT -.->|"se TAG sobreviveu ao remux"| G_F06B["Fase 06<br/>cura_gundam_mkv.py"]

    style G_F05A fill:#4B0082,stroke:#00E5FF,color:#fff
    style G_F06 fill:#5c1010,stroke:#ff4444,color:#fff
    style G_F06B fill:#5c1010,stroke:#ff4444,color:#fff
    style G_HYG fill:#6b21a8,stroke:#d946ef,color:#fff
    style G_F10 fill:#2d3748,stroke:#00E5FF,color:#fff
    style G_F12 fill:#1e4620,stroke:#32CD32,color:#fff
```

```powershell
python ".\02_extrator_legenda\extrator_inteligente_ass.py"
python ".\05a_tradutor_llm_gemma4\tradutor_gundam_unicornio\batch_translator_unicorn.py"
python ".\06_cura_legendas\cura_legendas_tag.py"           # se necessário (TAG corrompido)
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
python ".\10_auditoria_e_revisao\revisao_legenda_gundam_unicornio.py"   # opcional, ep.1 + letras OP/ED + remux
```

---

## Esteira H — Guilty Crown (correção de nomes e cores de músicas)

```mermaid
flowchart LR
    H_MKV["episodios/*.mkv (EN)"] --> H_F02["Fase 02<br/>extrator_inteligente_ass.py"]
    H_F02 --> H_ENG["legendas_eng/*_ENG.ass"]
    H_ENG --> H_F05A["Fase 05a<br/>tradutor_ass/batch_translator_ass.py"]
    H_F05A --> H_RAW["legendas_eng/*_PTBR.ass<br/>(com ERRO_TRADUCAO)"]
    H_RAW --> H_F11A["Fase 11<br/>corrigir_guilty_crown.py"]
    H_F11A --> H_PTBR["legendas_ptbr/*_PTBR.ass"]
    H_PTBR --> H_F11B["Fase 11<br/>corrigir_cores_musicas.py<br/>(cores/tags OP-ED)"]
    H_F11B -.->|"opcional"| H_HYG["Fase 00<br/>Guilty_Crown/limpeza_geral_guilty.py"]
    H_HYG -.->|"opcional"| H_F10["Fase 10<br/>revisao_guild_crown.py"]
    H_MKV --> H_F12["Fase 12<br/>batch_remuxer.py"]
    H_F11B --> H_F12
    H_F10 -.-> H_F12
    H_F12 --> H_OUT["mkv_final_ptbr/*_PTBR.mkv"]

    style H_F05A fill:#4B0082,stroke:#00E5FF,color:#fff
    style H_F11A fill:#5c1010,stroke:#ff4444,color:#fff
    style H_F11B fill:#5c1010,stroke:#ff4444,color:#fff
    style H_HYG fill:#6b21a8,stroke:#d946ef,color:#fff
    style H_F10 fill:#2d3748,stroke:#00E5FF,color:#fff
    style H_F12 fill:#1e4620,stroke:#32CD32,color:#fff
```

```powershell
python ".\02_extrator_legenda\extrator_inteligente_ass.py"
python ".\05a_tradutor_llm_gemma4\tradutor_ass\batch_translator_ass.py"   # ou variante adequada
python ".\11_correcao_projetos_legados\corrigir_guilty_crown.py"          # remove [ERRO_TRADUCAO:]
python ".\11_correcao_projetos_legados\corrigir_cores_musicas.py"         # cores/tags OP-ED
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
python ".\10_auditoria_e_revisao\revisao_guild_crown.py"                  # opcional, diálogos + letras OP/ED + remux
```

---

## Esteira I — Gundam The Origin, legenda chinesa (CHS)

```mermaid
flowchart LR
    I_MKV["episodios/*.mkv (CHS embutido)"] --> I_F02["Fase 02<br/>extrator_inteligente_ass.py"]
    I_F02 --> I_CHS["*.chs.ass"]
    I_CHS --> I_F05C["Fase 05c<br/>batch_translator_origin_zh.py"]
    I_F05C --> I_PTBR["legendas_ptbr/*_PTBR.ass"]
    I_PTBR -.->|"se ERRO_TRADUCAO"| I_REP["Fase 05c<br/>repara_erros_origin_zh.py"]
    I_REP -.-> I_PTBR
    I_PTBR -.->|"opcional"| I_HYG["Fase 00<br/>Gundam_The_Origin/limpeza_geral_origin.py"]
    I_HYG -.->|"opcional"| I_F10["Fase 10<br/>revisao_legenda_origin.py"]
    I_MKV --> I_F12["Fase 12<br/>batch_remuxer.py"]
    I_PTBR --> I_F12
    I_F10 -.-> I_F12
    I_F12 --> I_OUT["mkv_final_ptbr/*_PTBR.mkv"]

    style I_F05C fill:#4B0082,stroke:#00E5FF,color:#fff
    style I_REP fill:#5c1010,stroke:#ff4444,color:#fff
    style I_HYG fill:#6b21a8,stroke:#d946ef,color:#fff
    style I_F10 fill:#2d3748,stroke:#00E5FF,color:#fff
    style I_F12 fill:#1e4620,stroke:#32CD32,color:#fff
```

```powershell
python ".\02_extrator_legenda\extrator_inteligente_ass.py"
# Pré-requisito: LM Studio na porta 1234 com Qwen2.5-7B-Instruct carregado
python ".\05c_tradutor_llm_qwen2\batch_translator_origin_zh.py" --entrada "<pasta_chs_ass>" --saida "<pasta_saida>"
python ".\05c_tradutor_llm_qwen2\repara_erros_origin_zh.py" --originais "<pasta_chs_ass>" --traduzidas "<pasta_ptbr>"  # se necessário
python ".\10_auditoria_e_revisao\revisao_legenda_origin.py"        # opcional, lore + cache + remux
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
```

---

## Esteira J — Gundam Origin, legenda francesa (SUBFRENCH)

Rota alternativa para Gundam Origin quando o release disponível tem legenda francesa embutida em vez da chinesa (Esteira I).

```mermaid
flowchart LR
    J_MKV["episodios/*.mkv (FR, SUBFRENCH)"] --> J_F05B["Fase 05b<br/>frances_para_ptbr/script_tradutor_fr_gundam_origin.py"]
    J_F05B --> J_ASS["traducao/*_PTBR.ass"]
    J_ASS -.->|"opcional"| J_F07["Fase 07<br/>refina_traducao_fr.py"]
    J_F07 -.-> J_ASS
    J_ASS -.->|"opcional"| J_HYG["Fase 00<br/>Gundam_Origin/limpeza_origin_*.py (4 scripts)"]
    J_MKV --> J_F12["Fase 12<br/>batch_remuxer.py"]
    J_ASS --> J_F12
    J_HYG -.-> J_F12
    J_F12 --> J_OUT["mkv_final_ptbr/*_PTBR.mkv"]

    style J_F05B fill:#4B0082,stroke:#00E5FF,color:#fff
    style J_F07 fill:#5c1010,stroke:#ff4444,color:#fff
    style J_HYG fill:#6b21a8,stroke:#d946ef,color:#fff
    style J_F12 fill:#1e4620,stroke:#32CD32,color:#fff
```

```powershell
# Pré-requisito: LM Studio na porta 1234 com Mistral Nemo Instruct 2407 (GGUF) carregado
python ".\05b_tradutor_llm_mistral_nemo\frances_para_ptbr\script_tradutor_fr_gundam_origin.py"
python ".\07_reparo_traducao\refina_traducao_fr.py"        # opcional, revisão via engenharia reversa do cache FR
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
```

---

## Esteira K — Gundam Zeta

```mermaid
flowchart LR
    K_MKV["episodios/*.mkv (EN)"] --> K_F05C2["Fase 05c-2<br/>Gundam_Zeta/script_tradutor_en_gundam_zeta.py"]
    K_F05C2 --> K_ASS["traducao/*_PTBR.ass"]
    K_ASS -.->|"opcional"| K_HYG["Fase 00<br/>Gundam_Zeta/limpeza_zeta_extrema.py"]
    K_MKV --> K_F12["Fase 12<br/>batch_remuxer.py"]
    K_ASS --> K_F12
    K_HYG -.-> K_F12
    K_F12 --> K_OUT["mkv_final_ptbr/*_PTBR.mkv"]

    style K_F05C2 fill:#4B0082,stroke:#00E5FF,color:#fff
    style K_HYG fill:#6b21a8,stroke:#d946ef,color:#fff
    style K_F12 fill:#1e4620,stroke:#32CD32,color:#fff
```

```powershell
# Pré-requisito: LM Studio na porta 1234 com TranslateGemma 12B carregado
python ".\05c_tradutor_llm_translategemma\Gundam_Zeta\script_tradutor_en_gundam_zeta.py"
python ".\00_scripts_higienizacao\Gundam_Zeta\limpeza_zeta_extrema.py"
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
```

---

## Esteira L — Gundam ZZ

```mermaid
flowchart LR
    L_MKV["episodios/*.mkv (EN)"] --> L_F05C2["Fase 05c-2<br/>Gundam_ZZ/script_tradutor_en_gundam_zz.py"]
    L_F05C2 --> L_ASS["traducao/*_PTBR.ass"]
    L_MKV --> L_F12["Fase 12<br/>batch_remuxer.py"]
    L_ASS --> L_F12
    L_F12 --> L_OUT["mkv_final_ptbr/*_PTBR.mkv"]

    style L_F05C2 fill:#4B0082,stroke:#00E5FF,color:#fff
    style L_F12 fill:#1e4620,stroke:#32CD32,color:#fff
```

```powershell
# Pré-requisito: LM Studio na porta 1234 com TranslateGemma 12B carregado
python ".\05c_tradutor_llm_translategemma\Gundam_ZZ\script_tradutor_en_gundam_zz.py"
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
```

> Gundam ZZ ainda **não tem** script dedicado em `00_scripts_higienizacao/` — é o título mais recente adicionado ao pipeline.

---

## Esteira M — Detonator Orgun

```mermaid
flowchart LR
    M_SRC["episodios/*.mkv ou *.srt (EN)"] --> M_F05B["Fase 05b<br/>Detonator_Orgun/script_tradutor_en_detonator_orgun.py"]
    M_F05B --> M_ASS["traducao/*_PTBR.ass"]
    M_ASS -.->|"opcional"| M_HYG["Fase 00<br/>Detonator_Orgun/limpeza_geral_orgun.py"]
    M_SRC --> M_F12["Fase 12<br/>batch_remuxer.py"]
    M_ASS --> M_F12
    M_HYG -.-> M_F12
    M_F12 --> M_OUT["mkv_final_ptbr/*_PTBR.mkv"]

    style M_F05B fill:#4B0082,stroke:#00E5FF,color:#fff
    style M_HYG fill:#6b21a8,stroke:#d946ef,color:#fff
    style M_F12 fill:#1e4620,stroke:#32CD32,color:#fff
```

```powershell
# Pré-requisito: LM Studio na porta 1234 com Mistral Nemo Instruct 2407 (GGUF) carregado
python ".\05b_tradutor_llm_mistral_nemo\Detonator_Orgun\script_tradutor_en_detonator_orgun.py"
python ".\00_scripts_higienizacao\Detonator_Orgun\limpeza_geral_orgun.py"
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
```

---

## Esteira N — Knights of Sidonia

```mermaid
flowchart LR
    N_MKV["episodios/*.mkv (EN)"] --> N_F02["Fase 02<br/>extrator_inteligente_ass.py"]
    N_F02 --> N_ENG["legendas_eng/*_ENG.ass"]
    N_ENG --> N_F05A["Fase 05a<br/>tradutor_ass/batch_translator_sidonia.py"]
    N_F05A --> N_ASS["traducao/*_PTBR.ass"]
    N_ASS -.->|"opcional"| N_HYG["Fase 00<br/>Knights_of_Sidonia/limpeza_sidonia_extrema.py"]
    N_MKV --> N_F12["Fase 12<br/>batch_remuxer.py"]
    N_ASS --> N_F12
    N_HYG -.-> N_F12
    N_F12 --> N_OUT["mkv_final_ptbr/*_PTBR.mkv"]

    style N_F05A fill:#4B0082,stroke:#00E5FF,color:#fff
    style N_HYG fill:#6b21a8,stroke:#d946ef,color:#fff
    style N_F12 fill:#1e4620,stroke:#32CD32,color:#fff
```

```powershell
python ".\02_extrator_legenda\extrator_inteligente_ass.py"
python ".\05a_tradutor_llm_gemma4\tradutor_ass\batch_translator_sidonia.py"
python ".\00_scripts_higienizacao\Knights_of_Sidonia\limpeza_sidonia_extrema.py"
python ".\12_remuxer_mkvmerge\batch_remuxer.py"
```

---

[← Índice da documentação](README.md) · [README principal](../README.md)
