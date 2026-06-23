#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UTILITÁRIO: gerar_prompt_documentacao.py
Varre o projeto, lê o README.md raiz, todos os arquivos Markdown (.md) da pasta docs/,
carrega o mapa_projeto.md e gera 3 arquivos de prompt divididos para o LM Studio:
- docs/prompt_para_ia_parte_1.txt
- docs/prompt_para_ia_parte_2.txt
- docs/prompt_para_ia_parte_3.txt
"""

import os

def gerar_prompt():
    pasta_docs = os.path.dirname(os.path.abspath(__file__))
    pasta_raiz = os.path.dirname(pasta_docs)
    
    caminho_readme_raiz = os.path.join(pasta_raiz, "README.md")
    caminho_mapa_projeto = os.path.join(pasta_raiz, "mapa_projeto.md")
    
    # Equivalência de Fases
    mapeamento_fases = """
Equivalência de Fases e Estrutura de Pastas (De/Para):
--------------------------------------------------------------------------------
* FASE 01 (Antiga 1): '01_analisador_midia/' (Auditoria de codecs, faixas e metadados de vídeo)
* FASE 02 (Antiga 2): '02_extrator_legenda/' (Extração inteligente de legendas ASS/SRT/PGS do mkv)
* FASE 03 (Antiga 7): '03_decodificador_caracteres/' (Recompressão/Otimização de vídeo e ajustes de encoding/caracteres)
* FASE 04 (Antiga 3): '04_conversor_srt_ass/' (Conversão SRT -> ASS com compensação de frame rate/sync)
* FASE 05a (Antiga 4): '05a_tradutor_llm_gemma4/' (Tradução em lote/multithread via Gemma 4B)
* FASE 05b (Antiga 4-B): '05b_tradutor_llm_mistral_nemo/' (Tradução especializada via Mistral Nemo para francês e inglês com glossário por título)
* FASE 05c (Antiga 11): '05c_tradutor_llm_qwen2/' (Tradução do Chinês Simplificado via Qwen2.5)
* FASE 05c2 (Inédita): '05c_tradutor_llm_translategemma/' (Tradução e correção contextual via TranslateGemma; Gundam ZZ permanece como rota legada/alternativa)
* FASE 06 (Antiga 8): '06_cura_legendas/' (Cura offline ultra-rápida de tags corrompidas e strings 'TAG')
* FASE 07 (Antiga 9): '07_higienizacao_e_reparo_de_traducao/' (Higienização por título e módulo de reparo via IA)
* FASE 08 (Antiga 6): '08_sincronizacao_legenda/' (Auditoria de drifts de áudio/vídeo e estiramento de tempo)
* FASE 09 (Antiga 10): '09_injetor_musicas/' (Extração e injeção de karaokês OP/ED/Insert Songs de fansubs)
* FASE 10 (Antiga 12): '10_auditoria_e_revisao/' (Revisão final por título de lore, resíduos de tradução e controle de QA)
* FASE 11 (Inédita): '11_correcao_projetos_legados/' (Limpeza de tags de cores de músicas e marcadores em legendas antigas)
* FASE 12 (Antiga 5): '12_remuxer_mkvmerge/' (Multiplexação final rápida sem re-encode com mkvmerge)
--------------------------------------------------------------------------------
"""

    regras_design = """
Regras Técnicas, Visuais e de Design exigidas na Documentação:
1. Mantenha os Shields/Badges de tecnologias no cabeçalho dos documentos.
2. Todos os DIAGRAMAS DE ARQUITETURA (Mermaid) devem ser adaptados, atualizados e 100% formatados para renderização no GitHub Markdown. Use blocos de código específicos (```mermaid) e certifique-se de que a sintaxe Mermaid seja válida (use aspas duplas em rótulos de nós que contenham parênteses, caracteres especiais ou formatação de quebra de linha para evitar quebras de renderização no GitHub).
3. Faça uma análise profunda da ordem das etapas de processamento e das dependências entre scripts antes de desenhar os diagramas Mermaid.
4. Mantenha links funcionais locais para arquivos e scripts usando a sintaxe [nome_do_script](file:///d:/PROJETOS-OPEN/projeto-tracker-animes-traducao/...)
5. Adicione ícones elegantes (emojis) e tabelas informativas para facilitar a navegação do desenvolvedor.
6. Mantenha as explicações técnicas detalhadas de negócio e infraestrutura presentes na documentação antiga.
7. NÃO use placeholders ou resumos. Escreva o conteúdo completo de cada arquivo Markdown atualizado.
"""

    # ==========================================
    # PARTE 1: ESTRUTURA E MAPA DO PROJETO
    # ==========================================
    p1 = []
    p1.append("================================================================================")
    p1.append("PARTE 1 DE 3: ESTRUTURA FÍSICA E MAPEAMENTO DE ARQUITETURA")
    p1.append("================================================================================")
    p1.append("Você é um redator técnico sênior especializado em arquiteturas de pipelines de dados e IA.")
    p1.append("Este é o primeiro prompt de um processo de 3 etapas para atualizar a documentação do projeto.")
    p1.append("Nesta primeira etapa, assimile a nova estrutura física do projeto, as pastas e os scripts reais.")
    p1.append("")
    p1.append(mapeamento_fases)
    p1.append("")
    p1.append("Abaixo está o mapa estrutural com os scripts e docstrings atuais:")
    p1.append("--------------------------------------------------------------------------------")
    if os.path.exists(caminho_mapa_projeto):
        try:
            with open(caminho_mapa_projeto, 'r', encoding='utf-8') as f:
                p1.append(f.read())
        except Exception as e:
            p1.append(f"Erro ao ler mapa_projeto.md: {e}")
    else:
        p1.append("(Aviso: arquivo mapa_projeto.md não encontrado)")
    p1.append("--------------------------------------------------------------------------------")
    p1.append("")
    p1.append("INSTRUÇÃO DE RESPOSTA:")
    p1.append("Por favor, apenas responda confirmando que você assimilou a nova arquitetura física do projeto, ")
    p1.append("os scripts contidos em cada pasta (de 00_ a 12_) e que está pronto para receber a 'PARTE 2 DE 3'.")
    p1.append("Não gere nenhuma documentação ou resumo técnico ainda. Responda apenas com a confirmação curta.")
    
    # Grava Parte 1
    caminho_p1 = os.path.join(pasta_docs, "prompt_para_ia_parte_1.txt")
    with open(caminho_p1, 'w', encoding='utf-8') as f:
        f.write("\n".join(p1))
    print(f"[SUCESSO] Parte 1 gravada em: {caminho_p1}")

    # ==========================================
    # PARTE 2: DOCUMENTAÇÃO PRINCIPAL
    # ==========================================
    p2 = []
    p2.append("================================================================================")
    p2.append("PARTE 2 DE 3: REESCRITA DA DOCUMENTAÇÃO PRINCIPAL DO PROJETO")
    p2.append("================================================================================")
    p2.append("Agora que assimilou a estrutura física do projeto, vamos atualizar os arquivos centrais de documentação.")
    p2.append("Você deve reescrever e atualizar o README.md da raiz e os arquivos principais da pasta docs/ listados abaixo.")
    p2.append("")
    p2.append(regras_design)
    p2.append("")
    p2.append("Abaixo estão os arquivos antigos para sua referência:")
    p2.append("--------------------------------------------------------------------------------")
    p2.append("--- INÍCIO DE ARQUIVO: /README.md (Raiz do projeto antigo) ---")
    if os.path.exists(caminho_readme_raiz):
        try:
            with open(caminho_readme_raiz, 'r', encoding='utf-8') as f:
                p2.append(f.read())
        except Exception as e:
            p2.append(f"Erro ao ler README.md: {e}")
    p2.append("--- FIM DE ARQUIVO: /README.md ---\n")

    # Lê arquivos centrais do docs/ (excluindo os módulos individuais e prompts)
    arquivos_docs = sorted(os.listdir(pasta_docs))
    arquivos_centrais = [
        "README.md", "arquitetura.md", "guia-de-execucao.md", 
        "estrutura-repositorio.md", "instalacao.md", 
        "dependencias-python.md", "logs-e-auditoria.md", 
        "solucao-de-problemas.md", "pipeline-srt.md"
    ]
    
    for arq in arquivos_docs:
        if arq in arquivos_centrais:
            caminho_arq = os.path.join(pasta_docs, arq)
            p2.append(f"--- INÍCIO DE ARQUIVO: docs/{arq} ---")
            try:
                with open(caminho_arq, 'r', encoding='utf-8') as f:
                    p2.append(f.read())
            except Exception as e:
                p2.append(f"Erro ao ler {arq}: {e}")
            p2.append(f"--- FIM DE ARQUIVO: docs/{arq} ---\n")
            
    p2.append("--------------------------------------------------------------------------------")
    p2.append("TAREFAS ESPECÍFICAS DE REESCRITA (Gere estes arquivos na íntegra):")
    p2.append("1. REESCREVA o `/README.md` raiz adaptando as esteiras (A-N) e a tabela de fases para o padrão 01 a 12.")
    p2.append("   - Atualize o 'Diagrama geral' do Mermaid de forma que seja 100% renderizável e compatível com o GitHub.")
    p2.append("2. REESCREVA o `/docs/README.md` para servir de hub da documentação.")
    p2.append("3. REESCREVA o `/docs/arquitetura.md` atualizando os diagramas detalhados das esteiras.")
    p2.append("4. REESCREVA o `/docs/guia-de-execucao.md` com os novos caminhos e parâmetros de comandos.")
    p2.append("5. REESCREVA o `/docs/estrutura-repositorio.md` refletindo a nova árvore de diretórios.")
    p2.append("")
    p2.append("Por favor, responda com os arquivos reescritos inteiros, separados por blocos de código markdown.")
    
    # Grava Parte 2
    caminho_p2 = os.path.join(pasta_docs, "prompt_para_ia_parte_2.txt")
    with open(caminho_p2, 'w', encoding='utf-8') as f:
        f.write("\n".join(p2))
    print(f"[SUCESSO] Parte 2 gravada em: {caminho_p2}")

    # ==========================================
    # PARTE 3: MÓDULOS DE FASE INDIVIDUAIS
    # ==========================================
    p3 = []
    p3.append("================================================================================")
    p3.append("PARTE 3 DE 3: ATUALIZAÇÃO DOS DOCUMENTOS DE MÓDULOS DE FASE")
    p3.append("================================================================================")
    p3.append("Nesta última etapa, vamos atualizar os arquivos individuais que documentam cada fase.")
    p3.append("Com base nas equivalências de fases (De/Para) e nos scripts reais mapeados na Parte 1,")
    p3.append("reescreva as documentações de módulo.")
    p3.append("")
    p3.append(regras_design)
    p3.append("")
    p3.append("Abaixo estão os módulos de fase antigos para referência textual:")
    p3.append("--------------------------------------------------------------------------------")
    
    for arq in arquivos_docs:
        # Pega apenas os arquivos no formato modulo-fase-*.md
        if arq.startswith("modulo-fase-") and arq.endswith(".md"):
            caminho_arq = os.path.join(pasta_docs, arq)
            p3.append(f"--- INÍCIO DE REFERÊNCIA: docs/{arq} ---")
            try:
                with open(caminho_arq, 'r', encoding='utf-8') as f:
                    p3.append(f.read())
            except Exception as e:
                p3.append(f"Erro ao ler {arq}: {e}")
            p3.append(f"--- FIM DE REFERÊNCIA: docs/{arq} ---\n")
            
    p3.append("--------------------------------------------------------------------------------")
    p3.append("TAREFAS ESPECÍFICAS DE GERAÇÃO (Gere o conteúdo completo de cada um):")
    p3.append("Crie/reescreva os 15 arquivos Markdown de fase individuais detalhando quais scripts pertencem a cada uma:")
    p3.append("1. `docs/modulo-fase-01.md` (Fase 01: Analisador)")
    p3.append("2. `docs/modulo-fase-02.md` (Fase 02: Extrator)")
    p3.append("3. `docs/modulo-fase-03.md` (Fase 03: Decodificador/Otimizador)")
    p3.append("4. `docs/modulo-fase-04.md` (Fase 04: Conversor)")
    p3.append("5. `docs/modulo-fase-05a.md` (Fase 05a: Gemma4)")
    p3.append("6. `docs/modulo-fase-05b.md` (Fase 05b: Mistral Nemo)")
    p3.append("7. `docs/modulo-fase-05c.md` (Fase 05c: Qwen2)")
    p3.append("8. `docs/modulo-fase-05c2.md` (Fase 05c2: TranslateGemma)")
    p3.append("9. `docs/modulo-fase-06.md` (Fase 06: Cura)")
    p3.append("10. `docs/modulo-fase-07.md` (Fase 07: Higienização e Reparo)")
    p3.append("11. `docs/modulo-fase-08.md` (Fase 08: Sincronização)")
    p3.append("12. `docs/modulo-fase-09.md` (Fase 09: Injetor de Músicas)")
    p3.append("13. `docs/modulo-fase-10.md` (Fase 10: Auditoria e Revisão)")
    p3.append("14. `docs/modulo-fase-11.md` (Fase 11: Correção Legados)")
    p3.append("15. `docs/modulo-fase-12.md` (Fase 12: Remuxer)")
    p3.append("")
    p3.append("Por favor, forneça as documentações completas na íntegra, separadas por blocos de código Markdown.")
    
    # Grava Parte 3
    caminho_p3 = os.path.join(pasta_docs, "prompt_para_ia_parte_3.txt")
    with open(caminho_p3, 'w', encoding='utf-8') as f:
        f.write("\n".join(p3))
    print(f"[SUCESSO] Parte 3 gravada em: {caminho_p3}")

if __name__ == "__main__":
    gerar_prompt()
