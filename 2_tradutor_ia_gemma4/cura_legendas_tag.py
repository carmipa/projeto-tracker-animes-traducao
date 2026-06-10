#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: cura_legendas_tag.py
Corrige de forma offline e instantânea o erro em que a palavra 'TAG' (ou '_TAG_')
aparece grudada no início ou no meio das legendas traduzidas, restaurando as tags ASS originais.
Processamento 100% offline, sem uso de IA (segundos para a temporada completa).

Author: Antigravity
Data: Junho 2026
"""

import os
import re
import sys
from colorama import init, Fore, Style

init(autoreset=True)


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
            print(f"{Fore.RED}[ERRO] Diretorio nao existe: {entrada}")
            continue
        return entrada


def obter_diretorio_saida(mensagem_prompt, padrao_caminho=None):
    sufixo_padrao = f" (ENTER = {padrao_caminho})" if padrao_caminho else ""
    entrada = input(f"{Fore.YELLOW}{mensagem_prompt}{sufixo_padrao}: {Style.RESET_ALL}").strip()
    entrada = entrada.strip('"').strip("'")
    if not entrada and padrao_caminho:
        return padrao_caminho
    return entrada


def curar_arquivos():
    print("=" * 80)
    print(f"{Fore.CYAN}       SCRIPT DE CURA DE TAGS OFFLINE (REMEDY TAGS) — GUILTY CROWN")
    print("=" * 80)

    # 1. Obter pastas
    caminho_padrao_traduzidos = r"D:\PROJETOS-OPEN\animes\Guilty Crown\traducao"
    pasta_traduzidos = obter_diretorio("Pasta com as legendas traduzidas (com erro de 'TAG')", caminho_padrao_traduzidos)

    caminho_padrao_originais = r"D:\PROJETOS-OPEN\animes\Guilty Crown\legendas_eng"
    pasta_originais = obter_diretorio("Pasta com as legendas originais em inglês (ENG)", caminho_padrao_originais)

    caminho_padrao_saida = r"D:\PROJETOS-OPEN\animes\Guilty Crown\traducao_curada"
    pasta_saida = obter_diretorio_saida("Pasta onde deseja salvar as legendas corrigidas", caminho_padrao_saida)

    os.makedirs(pasta_saida, exist_ok=True)

    arquivos_traduzidos = sorted([f for f in os.listdir(pasta_traduzidos) if f.lower().endswith('.ass')])

    if not arquivos_traduzidos:
        print(f"{Fore.RED}[ERRO] Nenhum arquivo .ass encontrado na pasta de traduzidos.")
        return

    print(f"\n{Fore.GREEN}[OK] Encontrados {len(arquivos_traduzidos)} arquivos para processar.")

    total_curas_geral = 0

    for idx, arquivo in enumerate(arquivos_traduzidos, 1):
        caminho_trad = os.path.join(pasta_traduzidos, arquivo)
        
        # O arquivo original em inglês deve ter o mesmo nome base mas terminar com _ENG.ass
        # Ex: [DB]Guilty Crown_-_01_PTBR.ass -> [DB]Guilty Crown_-_01_ENG.ass
        nome_original = arquivo.replace("_PTBR.ass", "_ENG.ass")
        caminho_orig = os.path.join(pasta_originais, nome_original)

        if not os.path.exists(caminho_orig):
            # Tenta um pareamento alternativo se a nomenclatura variar
            # Ex: Se o traduzido mantém o nome original
            nome_original_alt = arquivo.replace("_PTBR.ass", ".ass")
            caminho_orig_alt = os.path.join(pasta_originais, nome_original_alt)
            if os.path.exists(caminho_orig_alt):
                caminho_orig = caminho_orig_alt
            else:
                print(f"{Fore.YELLOW}[AVISO] Pulando {arquivo} (Legenda original correspondente não encontrada).")
                continue

        print(f"\n[{idx}/{len(arquivos_traduzidos)}] Processando: {arquivo} ...")

        with open(caminho_orig, 'r', encoding='utf-8', errors='replace') as f:
            linhas_orig = f.readlines()

        with open(caminho_trad, 'r', encoding='utf-8', errors='replace') as f:
            linhas_trad = f.readlines()

        # Garante que o número de linhas seja idêntico para alinhar pelo índice físico
        if len(linhas_orig) != len(linhas_trad):
            print(f"  {Fore.RED}[ERRO] Desalinhamento físico de linhas! (ENG: {len(linhas_orig)}, PTBR: {len(linhas_trad)}). Pulando arquivo.")
            continue

        linhas_curadas = []
        curas_no_arquivo = 0

        for i in range(len(linhas_trad)):
            linha_t = linhas_trad[i]
            linha_o = linhas_orig[i]

            if linha_t.startswith("Dialogue:") and linha_o.startswith("Dialogue:"):
                partes_o = linha_o.split(",", 9)
                partes_t = linha_t.split(",", 9)

                if len(partes_o) == 10 and len(partes_t) == 10:
                    metadados_t = ",".join(partes_t[:9]) + ","
                    texto_o = partes_o[9].rstrip("\n")
                    texto_t = partes_t[9].rstrip("\n")

                    # Captura as tags originais do inglês
                    tags_o = re.findall(r'\{[^}]+\}', texto_o)

                    if tags_o:
                        # Limpa possíveis sublinhados residuais do marcador anterior (ex: ___TAG___ ou _TAG_ para TAG)
                        texto_t_limpo = re.sub(r'_{1,3}TAG_{1,3}', 'TAG', texto_t)

                        contem_erro = any(x in texto_t_limpo for x in ["TAG", "tag"]) or (texto_o.startswith(tags_o[0]) and not texto_t_limpo.startswith(tags_o[0]))

                        if contem_erro:
                            texto_refeito = texto_t_limpo
                            for idx_tag, tag in enumerate(tags_o):
                                # Se a tag já está presente na linha traduzida de forma correta, não duplica
                                if tag in texto_refeito:
                                    continue

                                # Substitui a primeira ocorrência do erro 'TAG'
                                if 'TAG' in texto_refeito:
                                    texto_refeito = texto_refeito.replace('TAG', tag, 1)
                                elif 'tag' in texto_refeito:
                                    texto_refeito = texto_refeito.replace('tag', tag, 1)
                                else:
                                    # Fallback: se a tag estava no início do original e a tradução não tem, recoloca no início
                                    if idx_tag == 0 and texto_o.startswith(tag) and not texto_refeito.startswith(tag):
                                        # Remove 'TAG' residual colada se existir no início
                                        if texto_refeito.startswith("TAG"):
                                            texto_refeito = tag + texto_refeito[3:]
                                        elif texto_refeito.startswith("tag"):
                                            texto_refeito = tag + texto_refeito[3:]
                                        else:
                                            texto_refeito = tag + texto_refeito

                            if texto_refeito != texto_t:
                                curas_no_arquivo += 1
                                linha_t = f"{metadados_t}{texto_refeito}\n"

            linhas_curadas.append(linha_t)

        # Salva o arquivo corrigido ou copiado na nova pasta de saída
        caminho_saida_arquivo = os.path.join(pasta_saida, arquivo)
        with open(caminho_saida_arquivo, 'w', encoding='utf-8') as f:
            f.writelines(linhas_curadas)

        if curas_no_arquivo > 0:
            print(f"  {Fore.GREEN}[CURADO] Salvo em: {os.path.basename(caminho_saida_arquivo)} ({curas_no_arquivo} correções aplicadas).")
            total_curas_geral += curas_no_arquivo
        else:
            print(f"  {Fore.BLUE}[COPIADO] Salvo em: {os.path.basename(caminho_saida_arquivo)} (sem alterações necessárias).")

    print("\n" + "=" * 80)
    print(f"{Fore.GREEN}[SUCESSO GERAL] Script de cura finalizado!")
    print(f"{Fore.GREEN}Total de linhas corrigidas na temporada: {total_curas_geral}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        curar_arquivos()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[AVISO] Interrompido pelo operador.")
        sys.exit(0)
