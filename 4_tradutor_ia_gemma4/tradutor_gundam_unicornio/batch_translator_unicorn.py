#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MODULO: batch_translator_unicorn.py (Batch Mode v4)
Otimizado para Ryzen 7 5800X3D + RX 7800 XT + 64GB RAM.
Traduz BATCH_SIZE linhas por chamada de API, reduzindo o numero de requisicoes
de ~400 para ~40 por episodio e maximizando a utilizacao da GPU.

Author: Paulo + Claude
Data: Maio 2026
"""

import os
import re
import sys
import time
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from colorama import init, Fore, Style

init(autoreset=True)

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
LM_STUDIO_MODELS_URL = "http://localhost:1234/v1/models"
MAX_THREADS = 2   # threads paralelos (reduzido de 4 para 2 para dar mais memoria de contexto por slot)
BATCH_SIZE = 8   # Reduzido para 8 linhas por chamada para evitar estouro de tokens individuais
MODELO_ATIVO = "local-model"  # Selecionado dinamicamente no barramento local

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_INFO = os.path.join(PASTA_SCRIPT, "info.txt")
DEBUG_FILE = os.path.join(PASTA_SCRIPT, "debug_last_failure.txt")
_debug_salvo = False  # salva apenas o primeiro batch falho para analise

SYSTEM_PROMPT = (
    "You are an expert subtitler for Japanese anime, specializing in the Gundam Universal Century timeline.\n"
    "Translate the following numbered subtitle lines from English to Brazilian Portuguese (PT-BR).\n"
    "CRITICAL RULES:\n"
    "1. Keep intact: 'Psychoframe', 'Mobile Suit', 'Gundam', 'Newtype', 'Zeon', 'Neo Zeon', "
    "'Vist Foundation', 'Londo Bell', 'Anaheim Electronics', 'Federation'.\n"
    "2. Translate idioms naturally ('Roger' -> 'Copiado', 'Party' -> 'Grupo').\n"
    "3. Do NOT modify ASS tags in curly braces (e.g., {\\an8}, {\\i1}, {\\i0}).\n"
    "4. Return ONLY the numbered translations in the same format. No notes, no explanations."
)


def verificar_lm_studio():
    global MODELO_ATIVO
    print(f"{Fore.CYAN}[CHECK] Verificando LM Studio em {LM_STUDIO_MODELS_URL} ...")
    try:
        resposta = requests.get(LM_STUDIO_MODELS_URL, timeout=5)
        if resposta.status_code == 200:
            dados = resposta.json()
            modelos = [m.get("id", "desconhecido") for m in dados.get("data", [])]
            if modelos:
                print(f"{Fore.GREEN}[OK] LM Studio online. Modelo(s): {', '.join(modelos)}")
                # Filtra e escolhe o primeiro modelo de chat (evitando embeddings se possível)
                modelos_chat = [m for m in modelos if "embed" not in m.lower()]
                if modelos_chat:
                    MODELO_ATIVO = modelos_chat[0]
                else:
                    MODELO_ATIVO = modelos[0]
                print(f"{Fore.GREEN}[INFO] Modelo ativo selecionado: {MODELO_ATIVO}")
            else:
                print(f"{Fore.YELLOW}[AVISO] LM Studio online mas sem modelo carregado.")
                sys.exit(1)
        else:
            print(f"{Fore.RED}[ERRO] LM Studio HTTP {resposta.status_code}.")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"{Fore.RED}[ERRO] LM Studio nao esta rodando em localhost:1234.")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"{Fore.RED}[ERRO] LM Studio timeout (5s).")
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
            print(f"{Fore.RED}[ERRO] Diretorio nao existe: {entrada}")
            continue
        return entrada


def _limpar_markdown(texto):
    """Remove formatacao markdown que o thinking model pode adicionar."""
    texto = re.sub(r'\*+', '', texto)   # remove ** e *
    texto = re.sub(r'_+', '', texto)    # remove __ e _
    return texto.strip().strip('"').strip("'")


def _parsear_resposta_numerada(conteudo, n_esperado):
    """Extrai N linhas de uma resposta numerada do modelo."""
    linhas = []
    for linha in conteudo.split('\n'):
        m = re.match(r'^\d+[.)]\s*(.+)', linha.strip())
        if m:
            linhas.append(_limpar_markdown(m.group(1)))
    if len(linhas) >= n_esperado:
        return linhas[:n_esperado]
    # fallback: linhas brutas nao-vazias sem preamble do modelo
    linhas_raw = [
        _limpar_markdown(l)
        for l in conteudo.split('\n')
        if l.strip() and not re.match(r'^(here|sure|translation|below|ok)', l.strip(), re.I)
    ]
    return linhas_raw[:n_esperado]


def _salvar_debug(input_texto, output_bruto, traducoes_parsed):
    global _debug_salvo
    if _debug_salvo:
        return
    _debug_salvo = True
    with open(DEBUG_FILE, "w", encoding="utf-8") as f:
        f.write("=== INPUT ENVIADO AO MODELO ===\n")
        f.write(input_texto + "\n\n")
        f.write("=== RESPOSTA BRUTA DO MODELO ===\n")
        f.write(output_bruto + "\n\n")
        f.write(f"=== PARSED ({len(traducoes_parsed)} linhas) ===\n")
        for i, t in enumerate(traducoes_parsed):
            f.write(f"  {i+1}. {t}\n")
    print(f"\n{Fore.YELLOW}[DEBUG] Resposta do modelo salva em: {DEBUG_FILE}")


def traduzir_bloco_ia(bloco):
    """
    Traduz um bloco de linhas em uma unica chamada de API.
    bloco = list of (index, metadados, texto_limpo, tags_encontradas)
    Retorna list of (index, linha_final, usou_fallback).
    """
    # Separa linhas vazias (nao precisam de traducao)
    resultados_vazios = {}
    bloco_util = []
    for item in bloco:
        idx, meta, texto, tags = item
        if not texto.strip():
            resultados_vazios[idx] = (idx, f"{meta}{texto}\n", False)
        else:
            bloco_util.append(item)

    if not bloco_util:
        return list(resultados_vazios.values())

    indices_u = [x[0] for x in bloco_util]
    metadados_u = [x[1] for x in bloco_util]
    textos_u = [x[2] for x in bloco_util]
    tags_u = [x[3] for x in bloco_util]

    texto_numerado = "\n".join(f"{i+1}. {t}" for i, t in enumerate(textos_u))

    payload = {
        "model": MODELO_ATIVO,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Translate these {len(textos_u)} lines to PT-BR. Return ONLY numbered translations:\n{texto_numerado}"}
        ],
        "temperature": 0.1,
        "max_tokens": 4000 # Espaco suficiente para o raciocinio e para as 10 linhas traduzidas
    }

    max_tentativas = 3
    tentativa = 0

    while tentativa < max_tentativas:
        try:
            resposta = requests.post(LM_STUDIO_URL, json=payload, timeout=120)
            if resposta.status_code != 200:
                tentativa += 1
                if tentativa < max_tentativas:
                    tempo_espera = tentativa * 5
                    print(f"\n{Fore.YELLOW}[AVISO] Erro HTTP {resposta.status_code} no bloco {indices_u[0]}-{indices_u[-1]}. Tentativa {tentativa}/{max_tentativas}. Aguardando {tempo_espera}s...")
                    time.sleep(tempo_espera)
                    continue
                else:
                    _salvar_debug(texto_numerado, f"HTTP {resposta.status_code}\n{resposta.text}", [])
                    raise Exception(f"HTTP {resposta.status_code} - {resposta.text[:200]}")

            conteudo = resposta.json()['choices'][0]['message']['content'].strip()
            traducoes = _parsear_resposta_numerada(conteudo, len(textos_u))

            if len(traducoes) < len(textos_u):
                tentativa += 1
                if tentativa < max_tentativas:
                    tempo_espera = tentativa * 3
                    print(f"\n{Fore.YELLOW}[AVISO] Resposta incompleta ({len(traducoes)}/{len(textos_u)} linhas) no bloco {indices_u[0]}-{indices_u[-1]}. Tentativa {tentativa}/{max_tentativas}. Aguardando {tempo_espera}s...")
                    time.sleep(tempo_espera)
                    continue
                else:
                    _salvar_debug(texto_numerado, conteudo, traducoes)

            resultados = list(resultados_vazios.values())
            for i, (idx, meta, texto_orig, tags) in enumerate(zip(indices_u, metadados_u, textos_u, tags_u)):
                if i < len(traducoes) and traducoes[i] and traducoes[i].lower() != texto_orig.lower():
                    trad = traducoes[i]
                    for tag in tags:
                        trad = trad.replace('___TAG___', tag, 1)
                    resultados.append((idx, f"{meta}{trad}\n", False))
                else:
                    resultados.append((idx, f"{meta}[ERRO_TRADUCAO: {texto_orig}]\n", True))
            return resultados

        except Exception as e:
            tentativa += 1
            if tentativa < max_tentativas:
                tempo_espera = tentativa * 5
                print(f"\n{Fore.YELLOW}[AVISO] Excecao no bloco {indices_u[0]}-{indices_u[-1]}: {e}. Tentativa {tentativa}/{max_tentativas}. Aguardando {tempo_espera}s...")
                time.sleep(tempo_espera)
            else:
                print(f"\n{Fore.RED}[FALHA] Bloco idx {indices_u[0]}-{indices_u[-1]} falhou definitivamente apos {max_tentativas} tentativas: {e}")
                _salvar_debug(texto_numerado, str(e), [])
                resultados = list(resultados_vazios.values())
                for idx, meta, texto, _ in zip(indices_u, metadados_u, textos_u, tags_u):
                    resultados.append((idx, f"{meta}[ERRO_TRADUCAO: {texto}]\n", True))
                return resultados


def executar_pipeline_lote():
    print("=" * 80)
    print(f"{Fore.CYAN}    ESTEIRA BATCH {BATCH_SIZE}L/CHAMADA | THREADS={MAX_THREADS} | ASS -> ASS PTBR")
    print("=" * 80)

    verificar_lm_studio()

    caminho_padrao_origem = (
        r"C:\TRACKER-ANIMES\animes\unicornio"
        r"\Mobile Suit Gundam Unicorn Re0096 (2016) [Season 1] [BD 1080p HEVC OPUS] [Dual-Audio]"
        r"\Season 1\legendas_eng"
    )
    pasta_origem = obter_diretorio_operador("Pasta com legendas ENG", caminho_padrao_origem)

    caminho_padrao_saida = (
        r"C:\TRACKER-ANIMES\animes\unicornio"
        r"\Mobile Suit Gundam Unicorn Re0096 (2016) [Season 1] [BD 1080p HEVC OPUS] [Dual-Audio]"
        r"\Season 1\traduzidos"
    )
    pasta_saida = obter_diretorio_operador("Pasta de saida PT-BR", caminho_padrao_saida)

    os.makedirs(pasta_saida, exist_ok=True)
    arquivos_ass = sorted([f for f in os.listdir(pasta_origem) if f.lower().endswith('.ass')])

    if not arquivos_ass:
        print(f"{Fore.RED}[ERRO] Nenhum .ass em: {pasta_origem}")
        return

    print(f"{Fore.GREEN}[OK] {len(arquivos_ass)} arquivos carregados | batch={BATCH_SIZE} | threads={MAX_THREADS}")

    linhas_relatorio = [
        "RELATORIO DE TRADUCAO BATCH - BATCH TRANSLATOR UNICORN",
        f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Batch size: {BATCH_SIZE} linhas/chamada | Threads: {MAX_THREADS}",
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
            tqdm.write(f"\n{Fore.YELLOW}[{idx+1}/{len(arquivos_ass)}] -> {arquivo}")

            with open(caminho_entrada, 'r', encoding='utf-8') as f:
                linhas_originais = f.readlines()

            mapa_linhas_finais: list[str | None] = [None] * len(linhas_originais)
            blocos = []
            bloco_atual = []
            fallbacks_arquivo = 0
            total_dialogos = 0

            for i, linha in enumerate(linhas_originais):
                if linha.startswith("Dialogue:"):
                    total_dialogos += 1
                    partes = linha.split(",", 9)
                    if len(partes) == 10:
                        metadados = ",".join(partes[:9]) + ","
                        texto_bruto = partes[9].rstrip("\n")
                        tags = re.findall(r'\{[^}]+\}', texto_bruto)
                        texto_limpo = re.sub(r'\{[^}]+\}', '___TAG___', texto_bruto)
                        bloco_atual.append((i, metadados, texto_limpo, tags))
                        if len(bloco_atual) == BATCH_SIZE:
                            blocos.append(bloco_atual)
                            bloco_atual = []
                    else:
                        mapa_linhas_finais[i] = linha
                else:
                    mapa_linhas_finais[i] = linha

            if bloco_atual:
                blocos.append(bloco_atual)

            total_chamadas = len(blocos)
            tqdm.write(f"  {Fore.CYAN}Dialogos: {total_dialogos} | Chamadas API: {total_chamadas} (reducao {total_dialogos//max(total_chamadas,1)}x)")

            with tqdm(total=total_chamadas, desc=f"  Ep {idx+1:02d} batches", unit="bat", colour="cyan", ncols=80, position=1, leave=False) as barra_micro:
                with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                    futuros = {executor.submit(traduzir_bloco_ia, bloco): bloco for bloco in blocos}
                    for futuro in as_completed(futuros):
                        for orig_idx, linha_proc, usou_fallback in futuro.result():
                            mapa_linhas_finais[orig_idx] = linha_proc
                            if usou_fallback:
                                fallbacks_arquivo += 1
                        barra_micro.update(1)

            with open(caminho_saida, 'w', encoding='utf-8') as f:
                f.writelines(l for l in mapa_linhas_finais if l is not None)

            tqdm.write(f"{Fore.GREEN}  [SALVO] {nome_saida_ptbr} | Chamadas: {total_chamadas} | Fallbacks: {fallbacks_arquivo}")
            linhas_relatorio.append(
                f"{nome_saida_ptbr} | Dialogos: {total_dialogos} | Chamadas: {total_chamadas} | Fallbacks: {fallbacks_arquivo}"
            )
            total_fallbacks_geral += fallbacks_arquivo
            total_dialogos_geral += total_dialogos
            barra_macro.update(1)

    linhas_relatorio.append("=" * 80)
    linhas_relatorio.append(
        f"TOTAL: {len(arquivos_ass)} arquivos | {total_dialogos_geral} dialogos | {total_fallbacks_geral} fallbacks"
    )

    with open(ARQUIVO_INFO, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_relatorio) + "\n")

    print("\n" + "=" * 80)
    print(f"{Fore.GREEN}[SUCESSO] Pipeline batch concluido!")
    print(f"{Fore.GREEN}Legendas PT-BR em: {pasta_saida}")
    print(f"{Fore.CYAN}Relatorio: {ARQUIVO_INFO}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        executar_pipeline_lote()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[AVISO] Interrompido pelo operador (Ctrl+C).")
        sys.exit(0)
