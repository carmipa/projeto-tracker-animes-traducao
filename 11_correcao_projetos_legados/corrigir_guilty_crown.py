#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: corrigir_guilty_crown.py
Remove de forma offline e instantânea os marcadores "[ERRO_TRADUCAO: ...]" das
legendas traduzidas de Guilty Crown, restaurando o texto original (geralmente nomes
próprios) e preservando a estrutura da legenda.

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
RELATORIO_FILE = os.path.join(PASTA_SCRIPT, "relatorio_correcao.txt")


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


def obter_diretorio_saida(mensagem_prompt, padrao_caminho=None):
    sufixo_padrao = f" (ENTER = {padrao_caminho})" if padrao_caminho else ""
    entrada = input(f"{Fore.YELLOW}{mensagem_prompt}{sufixo_padrao}: {Style.RESET_ALL}").strip()
    entrada = entrada.strip('"').strip("'")
    if not entrada and padrao_caminho:
        return padrao_caminho
    return entrada


def executar_correcao():
    print("=" * 80)
    print(f"{Fore.CYAN}       SCRIPT DE CORREÇÃO OFFLINE DE ERROS DE TRADUÇÃO - GUILTY CROWN")
    print("=" * 80)

    # 1. Definir caminhos padrões baseados na estrutura do usuário
    caminho_padrao_origem = r"E:\animes\GUILTY CROWN\1080p\legendas_eng"
    caminho_padrao_destino = r"E:\animes\GUILTY CROWN\1080p\legendas_ptbr"

    # 2. Obter pastas do operador
    pasta_origem = obter_diretorio("Pasta com as legendas extraídas (com erros de tradução)", caminho_padrao_origem)
    pasta_destino = obter_diretorio_saida("Pasta onde deseja salvar as legendas corrigidas", caminho_padrao_destino)

    os.makedirs(pasta_destino, exist_ok=True)

    # 3. Ler arquivos .ass
    arquivos_ass = sorted([f for f in os.listdir(pasta_origem) if f.lower().endswith('.ass')])

    if not arquivos_ass:
        print(f"{Fore.RED}[ERRO] Nenhum arquivo .ass encontrado na pasta de origem: {pasta_origem}")
        return

    print(f"\n{Fore.GREEN}[OK] Localizados {len(arquivos_ass)} arquivos .ass para processamento.")
    print(f"{Fore.CYAN}Iniciando correções instantâneas...\n")

    total_correcoes_geral = 0
    total_linhas_processadas = 0
    inicio_tempo = time.time()

    linhas_relatorio = [
        "RELATÓRIO DE CORREÇÃO DE LEGENDAS - GUILTY CROWN",
        f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Pasta Origem: {pasta_origem}",
        f"Pasta Destino: {pasta_destino}",
        "=" * 80,
    ]

    # Expressão regular para capturar [ERRO_TRADUCAO: texto]
    # Usando non-greedy (.*?) para caso haja múltiplas tags ou fechamento de colchetes posterior
    regex_erro = re.compile(r'\[ERRO_TRADUCAO:\s*(.*?)\s*\]')

    with tqdm(total=len(arquivos_ass), desc="Arquivos", unit="arq", colour="cyan", ncols=80) as barra:
        for arquivo in arquivos_ass:
            caminho_entrada = os.path.join(pasta_origem, arquivo)
            
            # Ajusta o nome do arquivo de saída se necessário
            # Se vier da extração com final _ENG.ass, muda para _PTBR.ass
            nome_saida = arquivo
            if nome_saida.endswith("_ENG.ass"):
                nome_saida = nome_saida.replace("_ENG.ass", "_PTBR.ass")
            elif not nome_saida.endswith("_PTBR.ass"):
                nome_saida = nome_saida.replace(".ass", "_PTBR.ass")
                
            caminho_saida = os.path.join(pasta_destino, nome_saida)

            with open(caminho_entrada, 'r', encoding='utf-8', errors='replace') as f:
                linhas = f.readlines()

            linhas_corrigidas = []
            correcoes_no_arquivo = 0

            for idx_linha, linha in enumerate(linhas, 1):
                total_linhas_processadas += 1
                if linha.startswith("Dialogue:") and "[ERRO_TRADUCAO:" in linha:
                    # Substitui a tag pelo conteúdo original usando lambda para evitar problemas com backslashes
                    nova_linha, n_sub = regex_erro.subn(lambda m: m.group(1), linha)
                    if n_sub > 0:
                        linha = nova_linha
                        correcoes_no_arquivo += n_sub
                
                linhas_corrigidas.append(linha)

            # Grava o arquivo corrigido na pasta de destino
            with open(caminho_saida, 'w', encoding='utf-8') as f:
                f.writelines(linhas_corrigidas)

            total_correcoes_geral += correcoes_no_arquivo
            barra.set_postfix_str(f"Corrigidos: {correcoes_no_arquivo}")
            barra.update(1)

            if correcoes_no_arquivo > 0:
                tqdm.write(f"  {Fore.GREEN}[CORRIGIDO] {arquivo} -> {nome_saida} | {correcoes_no_arquivo} tag(s) resolvida(s)")
                linhas_relatorio.append(f"{arquivo} -> {nome_saida} | Correções: {correcoes_no_arquivo}")
            else:
                tqdm.write(f"  {Fore.BLUE}[SEM ERROS] {arquivo} -> {nome_saida} | Copiado sem alterações")
                linhas_relatorio.append(f"{arquivo} -> {nome_saida} | Sem erros de tradução")

    fim_tempo = time.time()
    tempo_decorrido = fim_tempo - inicio_tempo

    linhas_relatorio.append("=" * 80)
    linhas_relatorio.append(
        f"TOTAL GERAL: {len(arquivos_ass)} arquivos processados | {total_linhas_processadas} linhas lidas | "
        f"{total_correcoes_geral} correções aplicadas | Tempo: {tempo_decorrido:.2f}s"
    )

    # Gravar o relatório de auditoria
    with open(RELATORIO_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_relatorio) + "\n")

    print("\n" + "=" * 80)
    print(f"{Fore.GREEN}[SUCESSO] Correção concluída com êxito!")
    print(f"{Fore.GREEN}Arquivos Processados: {len(arquivos_ass)}")
    print(f"{Fore.GREEN}Total de Correções Realizadas: {total_correcoes_geral}")
    print(f"{Fore.CYAN}Legendas salvas em: {pasta_destino}")
    print(f"{Fore.CYAN}Relatório de auditoria em: {RELATORIO_FILE}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        executar_correcao()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[AVISO] Interrompido pelo operador (Ctrl+C).")
        sys.exit(0)
