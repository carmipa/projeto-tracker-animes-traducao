#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: injetor_de_musicas.py
Extrai as linhas de karaokê (OP/ED/Insert Songs) de uma legenda fonte (ex: Fansub)
e injeta nas legendas de destino (ex: Tradução Oficial/Crunchyroll).
"""

import os
import re
import sys
from colorama import init, Fore, Style

init(autoreset=True)

# Regex para identificar os estilos musicais nas legendas do Fansub.
# Geralmente eles nomeiam os estilos de música com "OP", "ED", "Insert", "Karaoke", etc.
RE_ESTILO_MUSICA = re.compile(r'(?i)(?:OP|ED|Song|Lyric|Karaoke|Insert)')

def parse_ass_styles_and_dialogues(filepath):
    """Lê um arquivo ASS e retorna os estilos musicais e os diálogos musicais."""
    estilos_musicais = []
    dialogos_musicais = []
    nomes_estilos_musicais = set()

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        linhas = f.readlines()

    for linha in linhas:
        if linha.startswith("Style:"):
            # Exemplo: Style: OP_jp,Arial,20,&H00FFFFFF,...
            partes = linha.split(",", 1)
            if len(partes) > 1:
                nome_estilo = partes[0].replace("Style:", "").strip()
                if RE_ESTILO_MUSICA.search(nome_estilo):
                    estilos_musicais.append(linha)
                    nomes_estilos_musicais.add(nome_estilo)
        
        elif linha.startswith("Dialogue:"):
            # Exemplo: Dialogue: 0,0:01:00.00,0:01:05.00,OP_jp,,0,0,0,,Letra da musica
            partes = linha.split(",", 9)
            if len(partes) >= 4:
                estilo_dialogo = partes[3].strip()
                # Se o estilo do diálogo for um estilo musical, nós capturamos a linha inteira!
                if RE_ESTILO_MUSICA.search(estilo_dialogo) or estilo_dialogo in nomes_estilos_musicais:
                    dialogos_musicais.append(linha)

    return estilos_musicais, dialogos_musicais

def injetar_musicas(caminho_destino, estilos_musicais, dialogos_musicais):
    """Injeta os estilos e diálogos musicais e corrige a escala de 360p para 1080p se necessário."""
    with open(caminho_destino, 'r', encoding='utf-8', errors='replace') as f:
        linhas = f.readlines()

    novas_linhas = []
    injetou_estilos = False

    for linha in linhas:
        # 1. Escalar resoluções globais
        if linha.startswith("PlayResX:") or linha.startswith("LayoutResX:"):
            novas_linhas.append(f"{linha.split(':')[0]}: 1920\n")
            continue
        if linha.startswith("PlayResY:") or linha.startswith("LayoutResY:"):
            novas_linhas.append(f"{linha.split(':')[0]}: 1080\n")
            continue
            
        # 2. Escalar estilos originais da Crunchyroll (tamanho < 40)
        if linha.startswith("Style:"):
            partes = linha.split(",")
            if len(partes) >= 22:
                try:
                    fontsize = float(partes[2])
                    if fontsize < 40:
                        partes[2] = str(int(fontsize * 3))
                        partes[16] = str(int(float(partes[16]) * 3))
                        partes[17] = str(int(float(partes[17]) * 3))
                        partes[19] = str(int(float(partes[19]) * 3))
                        partes[20] = str(int(float(partes[20]) * 3))
                        partes[21] = str(int(float(partes[21]) * 3))
                        linha = ",".join(partes)
                except ValueError:
                    pass

        # 3. Escalar tags de tamanho inline no diálogo
        if linha.startswith("Dialogue:"):
            linha = re.sub(
                r'\\fs(\d+)',
                lambda m: f"\\fs{int(m.group(1))*3}" if int(m.group(1)) < 40 else m.group(0),
                linha
            )

        # 4. Injetar os novos estilos musicais antes dos diálogos
        if not injetou_estilos and linha.startswith("[Events]"):
            novas_linhas.extend(estilos_musicais)
            novas_linhas.append("\n")
            injetou_estilos = True

        novas_linhas.append(linha)

    # No final do arquivo, injetamos as linhas de diálogo (as letras das músicas)
    novas_linhas.extend(dialogos_musicais)

    with open(caminho_destino, 'w', encoding='utf-8') as f:
        f.writelines(novas_linhas)

def extrair_numero_ep(nome_arquivo):
    m = re.search(r'\[(\d+)\]', nome_arquivo)
    if not m:
        m = re.search(r'E(\d+)', nome_arquivo, re.I)
    return m.group(1) if m else None

def main():
    print(f"{Fore.MAGENTA}================================================================================")
    print("                    INJETOR DE MÚSICAS (OP/ED) EM LEGENDAS")
    print(f"================================================================================{Style.RESET_ALL}\n")
    print("Este script copia estilos e letras de músicas de uma legenda fonte e injeta em outra.\n")

    if len(sys.argv) >= 3:
        pasta_fonte = sys.argv[1]
        pasta_destino = sys.argv[2]
    else:
        pasta_fonte = input(f"{Fore.YELLOW}Pasta das legendas FONTE (Ex: Versão Chinesa que contém as Músicas)\n> {Style.RESET_ALL}").strip(' "\'')
        if not pasta_fonte:
            print(f"{Fore.RED}[ERRO] Operação cancelada.")
            return

        pasta_destino = input(f"{Fore.YELLOW}Pasta das legendas DESTINO (Ex: Versão Francesa/PT-BR)\n> {Style.RESET_ALL}").strip(' "\'')
        if not pasta_destino:
            print(f"{Fore.RED}[ERRO] Operação cancelada.")
            return

    if not os.path.isdir(pasta_fonte):
        print(f"{Fore.RED}[ERRO] A pasta FONTE não foi encontrada: {pasta_fonte}")
        return
        
    if not os.path.isdir(pasta_destino):
        print(f"{Fore.RED}[ERRO] A pasta DESTINO não foi encontrada: {pasta_destino}")
        return

    arquivos_fonte = [f for f in os.listdir(pasta_fonte) if f.lower().endswith('.ass')]
    arquivos_destino = [f for f in os.listdir(pasta_destino) if f.lower().endswith('.ass')]

    print("\nIniciando injeção...\n")
    sucessos = 0

    for arq_dest in arquivos_destino:
        ep_num = extrair_numero_ep(arq_dest)
        if not ep_num:
            continue
        
        # Busca o arquivo fonte correspondente
        arq_fonte_match = next((f for f in arquivos_fonte if extrair_numero_ep(f) == ep_num), None)
        
        if arq_fonte_match:
            caminho_f = os.path.join(pasta_fonte, arq_fonte_match)
            caminho_d = os.path.join(pasta_destino, arq_dest)
            
            estilos, dialogos = parse_ass_styles_and_dialogues(caminho_f)
            
            if dialogos:
                injetar_musicas(caminho_d, estilos, dialogos)
                print(f"  {Fore.GREEN}[OK] Ep {ep_num} -> Injetados {len(estilos)} estilos e {len(dialogos)} linhas de karaokê!")
                sucessos += 1
            else:
                print(f"  {Fore.YELLOW}[AVISO] Ep {ep_num} -> Nenhuma música encontrada no arquivo FONTE. ({arq_fonte_match})")
        else:
            print(f"  {Fore.RED}[ERRO] Ep {ep_num} -> Arquivo FONTE correspondente não encontrado.")

    print(f"\n{Fore.CYAN}================================================================================")
    print(f"Injeção concluída em {sucessos} arquivos!")
    print(f"Agora você pode rodar o revisao_legenda_origin.py de novo para remuxar o MKV!")
    print(f"================================================================================{Style.RESET_ALL}\n")

if __name__ == '__main__':
    main()
