#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: batch_translator_unicorn.py (Modo Concorrente Multithread v3)
Otimizado para Ryzen 7 5800X3D e 64GB RAM. Dispara traduções paralelas
utilizando ThreadPoolExecutor para eliminar o gargalo síncrono de rede local.

Author: Paulo + Gemini
Data: Maio 2026
Status: HIGH-PERFORMANCE PARALLEL PIPELINE ENGAGED
"""

import os
import re
import sys
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from colorama import init, Fore, Style

init(autoreset=True)

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
LM_STUDIO_MODELS_URL = "http://localhost:1234/v1/models"
MAX_THREADS = 4  # Número de traduções simultâneas. 4 a 6 é o ideal para não estourar a VRAM da RX 7800 XT.

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_INFO = os.path.join(PASTA_SCRIPT, "info.txt")

SYSTEM_PROMPT = (
    "You are an expert subtitler and translator for Japanese anime, specializing in Sci-Fi, military mecha, and the Gundam Universal Century timeline.\n"
    "Translate the following subtitle lines from English to Brazilian Portuguese (PT-BR) preserving character flavor, military urgency, and natural dialogue flow.\n"
    "CRITICAL RULES:\n"
    "1. Keep professional sci-fi/military terminology intact. NEVER translate proper names or military nouns like: 'Psychoframe', 'Mobile Suit', 'Gundam', 'Newtype', 'Zeon', 'Neo Zeon', 'Vist Foundation', 'Londo Bell', 'Anaheim Electronics', 'Federation'.\n"
    "2. Avoid literal translations: Translate gaming/combat terms properly (e.g., 'Party' becomes 'Grupo', 'Roger' becomes 'Copiado' or 'Entendido').\n"
    "3. Do NOT modify, remove, or translate ANY ASS tags enclosed in curly braces (e.g., {\\an8}, {\\i1}, {\\i0}). Keep them exactly where they are in the sentence.\n"
    "4. Return ONLY the translated line text, with no explanations, no notes, and no prefix."
)


def verificar_lm_studio():
    """Verifica se o LM Studio está online antes de iniciar o pipeline."""
    print(f"{Fore.CYAN}[CHECK] Verificando LM Studio em {LM_STUDIO_MODELS_URL} ...")
    try:
        resposta = requests.get(LM_STUDIO_MODELS_URL, timeout=5)
        if resposta.status_code == 200:
            dados = resposta.json()
            modelos = [m.get("id", "desconhecido") for m in dados.get("data", [])]
            if modelos:
                print(f"{Fore.GREEN}[OK] LM Studio online. Modelo(s) carregado(s): {', '.join(modelos)}")
            else:
                print(f"{Fore.YELLOW}[AVISO] LM Studio online mas nenhum modelo carregado. Carregue o Gemma 4B antes de continuar.")
                sys.exit(1)
        else:
            print(f"{Fore.RED}[ERRO] LM Studio respondeu HTTP {resposta.status_code}. Verifique o servidor.")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"{Fore.RED}[ERRO] LM Studio não está rodando em localhost:1234.")
        print(f"{Fore.RED}        Inicie o LM Studio, carregue o Gemma 4B e ative o servidor local antes de rodar este script.")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"{Fore.RED}[ERRO] LM Studio não respondeu em 5 segundos. Verifique se o servidor está travado.")
        sys.exit(1)


def obter_diretorio_operador(mensagem_prompt, padrao_caminho=None):
    while True:
        sufixo_padrao = f" (ENTER = {padrao_caminho})" if padrao_caminho else ""
        entrada = input(f"{Fore.YELLOW}{mensagem_prompt}{sufixo_padrao}: {Style.RESET_ALL}").strip()
        entrada = entrada.strip('"').strip("'")
        if not entrada and padrao_caminho:
            return padrao_caminho
        if not entrada:
            continue
        if not os.path.isdir(entrada):
            print(f"{Fore.RED}[ERRO] O diretório especificado não existe: {entrada}")
            continue
        return entrada


def traduzir_linha_ia(index, metadados, texto_linha, tags_encontradas):
    """Trabalhador síncrono com validação rigorosa para evitar fallback silencioso."""
    if not texto_linha.strip():
        return index, f"{metadados}{texto_linha}\n", False

    payload = {
        "model": "gemma-4b",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Translate this line to PT-BR:\n{texto_linha}"}
        ],
        "temperature": 0.1,
        "max_tokens": 150
    }

    try:
        resposta = requests.post(LM_STUDIO_URL, json=payload, timeout=60)
        if resposta.status_code == 200:
            resultado_json = resposta.json()
            traducao = resultado_json['choices'][0]['message']['content'].strip()
            texto_traduzido = traducao.strip('"').strip("'")

            if texto_traduzido.lower() == texto_linha.lower() and len(texto_linha) > 5:
                raise ValueError("IA retornou texto original - falha de tradução")

            for tag in tags_encontradas:
                texto_traduzido = texto_traduzido.replace('___TAG___', tag, 1)

            return index, f"{metadados}{texto_traduzido}\n", False
        else:
            raise Exception(f"Erro HTTP {resposta.status_code}")

    except Exception as e:
        print(f"\n{Fore.RED}[FALHA] IA não traduziu linha {index}: {str(e)}")
        return index, f"{metadados}[ERRO_TRADUCAO: {texto_linha}]\n", True


def executar_pipeline_lote():
    print("=" * 80)
    print(f"{Fore.CYAN}    ESTEIRA MULTITHREAD DE ALTA PERFORMANCE (RYZEN 5800X3D): ASS -> ASS PTBR")
    print("=" * 80)

    verificar_lm_studio()

    caminho_padrao_origem = r"C:\TRACKER-ANIMES\animes\unicornio\Mobile Suit Gundam Unicorn Re0096 (2016) [Season 1] [BD 1080p HEVC OPUS] [Dual-Audio]\Season 1\legendas_eng"
    pasta_origem = obter_diretorio_operador("Digite a pasta onde estão as legendas ENG de origem", caminho_padrao_origem)

    caminho_padrao_saida = r"C:\TRACKER-ANIMES\animes\unicornio\Mobile Suit Gundam Unicorn Re0096 (2016) [Season 1] [BD 1080p HEVC OPUS] [Dual-Audio]\Season 1\traduzidos"
    pasta_saida = obter_diretorio_operador("Digite a pasta onde deseja salvar os arquivos ASS traduzidos", caminho_padrao_saida)

    os.makedirs(pasta_saida, exist_ok=True)
    arquivos_ass = sorted([f for f in os.listdir(pasta_origem) if f.lower().endswith('.ass')])

    if not arquivos_ass:
        print(f"{Fore.RED}[ERRO] Nenhum arquivo .ass localizado em: {pasta_origem}")
        return

    print(f"{Fore.GREEN}[OK] {len(arquivos_ass)} arquivos carregados no barramento de tradução.")

    linhas_relatorio = [
        "RELATÓRIO DE TRADUÇÃO MULTITHREAD — BATCH TRANSLATOR UNICORN",
        f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 80,
    ]
    total_fallbacks_geral = 0
    total_dialogos_geral = 0

    with tqdm(total=len(arquivos_ass), desc="Temporada Completa", unit="arq", colour="green", ncols=80, position=0) as barra_macro:
        for idx, arquivo in enumerate(arquivos_ass):
            caminho_entrada = os.path.join(pasta_origem, arquivo)
            nome_saida_ptbr = arquivo.replace("_ENG.ass", "_PTBR.ass")
            caminho_saida = os.path.join(pasta_saida, nome_saida_ptbr)

            barra_macro.set_postfix_str(arquivo[:35])
            tqdm.write(f"\n{Fore.YELLOW}[{idx+1}/{len(arquivos_ass)}] ➔ {arquivo}")

            with open(caminho_entrada, 'r', encoding='utf-8') as f:
                linhas_originais = f.readlines()

            mapa_linhas_finais = [None] * len(linhas_originais)
            tarefas_paralelas = {}
            fallbacks_arquivo = 0
            total_dialogos = 0

            with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                for i, linha in enumerate(linhas_originais):
                    if linha.startswith("Dialogue:"):
                        total_dialogos += 1
                        partes = linha.split(",", 9)
                        if len(partes) == 10:
                            metadados = ",".join(partes[:9]) + ","
                            texto_bruto_eng = partes[9].rstrip("\n")

                            tags_encontradas = re.findall(r'\{[^}]+\}', texto_bruto_eng)
                            texto_limpo = re.sub(r'\{[^}]+\}', '___TAG___', texto_bruto_eng)

                            futuro = executor.submit(traduzir_linha_ia, i, metadados, texto_limpo, tags_encontradas)
                            tarefas_paralelas[futuro] = i
                        else:
                            mapa_linhas_finais[i] = linha
                    else:
                        mapa_linhas_finais[i] = linha

                with tqdm(total=total_dialogos, desc=f"  Ep {idx+1:02d} paralelos", unit="lin", colour="cyan", ncols=80, position=1, leave=False) as barra_micro:
                    for futuro in as_completed(tarefas_paralelas):
                        origem_idx, linha_processada, usou_fallback = futuro.result()
                        mapa_linhas_finais[origem_idx] = linha_processada
                        if usou_fallback:
                            fallbacks_arquivo += 1
                        barra_micro.update(1)

            with open(caminho_saida, 'w', encoding='utf-8') as f:
                f.writelines(mapa_linhas_finais)

            tqdm.write(f"{Fore.GREEN}  [SALVO] traduzidos\\{nome_saida_ptbr} | Diálogos: {total_dialogos} | Fallbacks: {fallbacks_arquivo}")
            linhas_relatorio.append(f"{nome_saida_ptbr} | Diálogos: {total_dialogos} | Fallbacks: {fallbacks_arquivo}")
            total_fallbacks_geral += fallbacks_arquivo
            total_dialogos_geral += total_dialogos
            barra_macro.update(1)

    linhas_relatorio.append("=" * 80)
    linhas_relatorio.append(f"TOTAL: {len(arquivos_ass)} arquivos | {total_dialogos_geral} diálogos | {total_fallbacks_geral} fallbacks")

    with open(ARQUIVO_INFO, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_relatorio) + "\n")

    print("\n" + "=" * 80)
    print(f"{Fore.GREEN}[SUCESSO TOTAL] Pipeline multithread concluído!")
    print(f"{Fore.GREEN}Legendas PT-BR geradas em: {pasta_saida}")
    print(f"{Fore.CYAN}Relatório salvo em: {ARQUIVO_INFO}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        executar_pipeline_lote()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[AVISO] Execução interrompida pelo operador (Ctrl+C).")
        sys.exit(0)
