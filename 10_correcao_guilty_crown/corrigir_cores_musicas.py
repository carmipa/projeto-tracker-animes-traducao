#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: corrigir_cores_musicas.py
Corrige a coloração das músicas (OP/ED) de Guilty Crown nas legendas ASS,
alterando a cor principal das fontes para branco (\c&HFFFFFF&) e o contorno
para preto (\3c&H000000&) para máxima legibilidade na TV. Além disso, remove
os resíduos da palavra 'TAG' das letras das músicas.

Author: Antigravity
Data: Junho 2026
"""

import os
import re
import sys
import time
from datetime import datetime
from colorama import init, Fore, Style
from tqdm import tqdm

# Inicializa o colorama para o terminal do Windows
init(autoreset=True)

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
RELATORIO_FILE = os.path.join(PASTA_SCRIPT, "relatorio_cores_musicas.txt")


def obter_diretorio(mensagem_prompt, padrao_caminho=None):
    while True:
        sufixo_padrao = f" (ENTER = {padrao_caminho})" if padrao_caminho else ""
        entrada = input(f"{Fore.YELLOW}{mensagem_prompt}{sufixo_padrao}: {Style.RESET_ALL}").strip()
        entrada = entrada.strip('"').strip("'")
        if not entrada and padrao_caminho:
            return padrao_caminho
        if not entrada:
            continue
        if not os.path.isdir(entrada):
            print(f"{Fore.RED}[ERRO] O diretório não existe: {entrada}")
            continue
        return entrada


def limpar_tag_residuo(texto):
    """
    Remove a palavra 'TAG' ou 'tag' de fora dos blocos de estilização {...}.
    """
    partes = re.split(r'(\{[^}]+\})', texto)
    for i in range(len(partes)):
        if not partes[i].startswith('{'):
            # Remove ocorrências da palavra 'TAG' de forma case-insensitive
            partes[i] = re.sub(r'TAG', '', partes[i], flags=re.IGNORECASE)
    return "".join(partes)


def corrigir_cores_na_linha(texto):
    """
    Substitui tags de cores \c e \1c por branco (\c&HFFFFFF&) e \3c por preto (\3c&H000000&).
    """
    # Regex para capturar tags \c ou \1c de cores
    texto = re.sub(r'\\1?c&H?[0-9a-fA-F]+&', r'\\c&HFFFFFF&', texto)
    
    # Regex para capturar tags \3c de contorno
    texto = re.sub(r'\\3c&H?[0-9a-fA-F]+&', r'\\3c&H000000&', texto)
    
    # Corrige casos em que a tag está sem o 'H' e com formato antigo (ex: \3c&000000&)
    texto = re.sub(r'\\3c&000000&', r'\\3c&H000000&', texto)
    
    return texto


def processar_estilo(linha):
    """
    Ajusta a linha de definição de estilo para garantir cor primária branca
    e contorno preto para estilos relacionados a OP e ED.
    """
    partes = linha.split(',')
    if len(partes) > 6:
        # Pega o nome do estilo (ex: Style: OP_S2)
        estilo_nome = partes[0].split(':')[-1].strip()
        
        # Se for estilo de música
        if estilo_nome.upper().startswith('OP') or estilo_nome.upper().startswith('ED'):
            # Modifica a cor primária (PrimaryColour - campo 3)
            # ASS color format: &HAABBGGRR (onde AA é transparência, FFFFFF é branco)
            partes[3] = "&H00FFFFFF"
            
            # Modifica a cor do contorno (OutlineColour - campo 5)
            # Configura para preto (&H00000000)
            partes[5] = "&H00000000"
            
            return ",".join(partes)
            
    return linha


def executar_correcao_cores():
    print("=" * 80)
    print(f"{Fore.CYAN}    SCRIPT DE CORREÇÃO DE CORES E TAGS EM MÚSICAS (OP/ED) - GUILTY CROWN")
    print("=" * 80)

    # 1. Definir caminhos padrões
    caminho_padrao_ptbr = r"E:\animes\GUILTY CROWN\1080p\legendas_ptbr"

    # 2. Obter pasta
    pasta_legendas = obter_diretorio("Pasta com as legendas PT-BR corrigidas", caminho_padrao_ptbr)

    arquivos_ass = sorted([f for f in os.listdir(pasta_legendas) if f.lower().endswith('.ass')])

    if not arquivos_ass:
        print(f"{Fore.RED}[ERRO] Nenhum arquivo .ass encontrado na pasta: {pasta_legendas}")
        return

    print(f"\n{Fore.GREEN}[OK] Localizados {len(arquivos_ass)} arquivos para processamento.")
    print(f"{Fore.CYAN}Aplicando melhorias visuais nas músicas...\n")

    total_estilos_modificados = 0
    total_linhas_corrigidas = 0
    total_tags_removidas = 0
    inicio_tempo = time.time()

    linhas_relatorio = [
        "RELATÓRIO DE CORREÇÃO DE CORES/TAGS EM MÚSICAS - GUILTY CROWN",
        f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Pasta Processada: {pasta_legendas}",
        "=" * 80,
    ]

    with tqdm(total=len(arquivos_ass), desc="Músicas", unit="arq", colour="magenta", ncols=80) as barra:
        for arquivo in arquivos_ass:
            caminho_arquivo = os.path.join(pasta_legendas, arquivo)

            with open(caminho_arquivo, 'r', encoding='utf-8', errors='replace') as f:
                linhas = f.readlines()

            linhas_novas = []
            estilos_arquivo = 0
            linhas_arquivo = 0
            tags_arquivo = 0

            for linha in linhas:
                # 1. Processar estilos na seção [V4+ Styles]
                if linha.startswith("Style:"):
                    nova_linha = processar_estilo(linha)
                    if nova_linha != linha:
                        linha = nova_linha
                        estilos_arquivo += 1
                
                # 2. Processar diálogos na seção [Events]
                elif linha.startswith("Dialogue:") or linha.startswith("Comment:"):
                    partes = linha.split(",", 9)
                    if len(partes) == 10:
                        estilo = partes[3].strip()
                        # Se for linha de música (OP/ED)
                        if estilo.upper().startswith("OP") or estilo.upper().startswith("ED"):
                            texto_original = partes[9]
                            
                            # Remove resíduos da palavra 'TAG'
                            texto_limpo = limpar_tag_residuo(texto_original)
                            if texto_limpo != texto_original:
                                tags_arquivo += 1
                                
                            # Corrige cores internas
                            texto_final = corrigir_cores_na_linha(texto_limpo)
                            if texto_final != texto_original:
                                linhas_arquivo += 1
                            
                            partes[9] = texto_final
                            linha = ",".join(partes)

                linhas_novas.append(linha)

            # Grava o arquivo com as correções
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                f.writelines(linhas_novas)

            total_estilos_modificados += estilos_arquivo
            total_linhas_corrigidas += linhas_arquivo
            total_tags_removidas += tags_arquivo
            
            barra.set_postfix_str(f"Tags: {tags_arquivo}, Cores: {linhas_arquivo}")
            barra.update(1)

            tqdm.write(
                f"  {Fore.GREEN}[CORRIGIDO] {arquivo} | "
                f"Estilos: {estilos_arquivo} | Cores Lidas: {linhas_arquivo} | Tags Cured: {tags_arquivo}"
            )
            linhas_relatorio.append(
                f"{arquivo} | Estilos: {estilos_arquivo} | Cores Lidas: {linhas_arquivo} | Tags Cured: {tags_arquivo}"
            )

    fim_tempo = time.time()
    tempo_decorrido = fim_tempo - inicio_tempo

    linhas_relatorio.append("=" * 80)
    linhas_relatorio.append(
        f"TOTAL GERAL: {len(arquivos_ass)} arquivos processados | "
        f"{total_estilos_modificados} estilos redefinidos | {total_linhas_corrigidas} linhas de cores limpas | "
        f"{total_tags_removidas} resíduos de TAG removidos | Tempo: {tempo_decorrido:.2f}s"
    )

    with open(RELATORIO_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_relatorio) + "\n")

    print("\n" + "=" * 80)
    print(f"{Fore.GREEN}[SUCESSO] Otimização das músicas finalizada!")
    print(f"{Fore.GREEN}Estilos de OP/ED modificados: {total_estilos_modificados}")
    print(f"{Fore.GREEN}Linhas com correção de cores: {total_linhas_corrigidas}")
    print(f"{Fore.GREEN}Resíduos de 'TAG' limpos das letras: {total_tags_removidas}")
    print(f"{Fore.CYAN}Relatório em: {RELATORIO_FILE}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        executar_correcao_cores()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[AVISO] Interrompido pelo operador (Ctrl+C).")
        sys.exit(0)
