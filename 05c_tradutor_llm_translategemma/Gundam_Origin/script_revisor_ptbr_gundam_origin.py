#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PIPELINE INDUSTRIAL UNIFICADO - REVISÃO GRAMATICAL
Alvo: Mobile Suit Gundam Origin (Correção de PT-BR corrompido)
Motor: TranslateGemma 12B (Operando como Corretor Ortográfico)
"""

import os
import sys
import re
import json
import time
import requests
import traceback
import glob
from datetime import datetime

try:
    from tqdm import tqdm
except ImportError:
    print("Por favor, instale o tqdm: pip install tqdm")
    sys.exit(1)

# ==========================================
# CONFIGURAÇÃO GERAL
# ==========================================
PASTA_ENTRADA = r"E:\animes\GUNDAM\GUNDAM UC\UC 0068 - ORIGIN\Mobile_Suit_Gundam_The_Origin_Advent_of_the_Red_Comet\legendas_eng"

LM_STUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
ARQUIVO_CACHE = os.path.join(BASE_DIR, "revisao_cache_origin.json")
ARQUIVO_STATS = os.path.join(LOGS_DIR, f"stats_revisao_origin_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json")

PADRAO_LINHA_FALA = re.compile(r"^(Dialogue:\s*[^,]*(?:,[^,]*){8},)(.*)$")

os.makedirs(LOGS_DIR, exist_ok=True)

cache_traducoes = {}
estatisticas = {
    "total_solicitacoes": 0,
    "sucessos": 0,
    "erros": 0,
    "erros_tag_bloqueados": 0,
    "tempo_inicio": datetime.now().isoformat()
}

def log_terminal(tipo, mensagem):
    cores = {"INFO": "\033[94m", "SUCESSO": "\033[92m", "AVISO": "\033[93m", "ERRO": "\033[91m", "DEBUG": "\033[90m"}
    reset = "\033[0m"
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    tqdm.write(f"[{timestamp}] [{cores.get(tipo, '')}{tipo.ljust(7)}{reset}] {mensagem}")

def carregar_cache():
    global cache_traducoes
    if os.path.exists(ARQUIVO_CACHE):
        with open(ARQUIVO_CACHE, 'r', encoding='utf-8') as f:
            cache_traducoes = json.load(f)
        log_terminal("INFO", f"Cache carregado: {len(cache_traducoes)} blocos revisados.")

def salvar_cache():
    with open(ARQUIVO_CACHE, 'w', encoding='utf-8') as f:
        json.dump(cache_traducoes, f, ensure_ascii=False, indent=2)

def salvar_estatisticas():
    estatisticas["tempo_fim"] = datetime.now().isoformat()
    with open(ARQUIVO_STATS, 'w', encoding='utf-8') as f:
        json.dump(estatisticas, f, ensure_ascii=False, indent=4)

SYSTEM_PROMPT = """You are an elite Brazilian Portuguese proofreader.
You will receive raw subtitle lines (.ass format) in Brazilian Portuguese that contain grammatical errors (pronouns, verb conjugations, feminine/masculine gender mismatches).
Your strict instructions:
1. Proofread and CORRECT the grammatical errors in the text. Make it sound natural in pt-BR.
2. DO NOT change the structure, do not change the core meaning, just fix the grammar.
3. DO NOT translate proper nouns or terms from the Universal Century.
4. DO NOT modify, translate, or remove ANY technical tags like [T1], [T2]. You MUST return them exactly where they were.
5. Output NOTHING but the final corrected text. No pleasantries, no notes.
6. You MUST return each corrected line with its exact original index prefix (e.g., [0] <corrected text>)."""

def valida_estrutura_tags(original, traduzido):
    tags_orig = re.findall(r'(\\[Nn]|{\\[^}]+}|<[^>]+>|\[T\d+\])', original)
    tags_trad = re.findall(r'(\\[Nn]|{\\[^}]+}|<[^>]+>|\[T\d+\])', traduzido)
    if sorted(tags_orig) != sorted(tags_trad):
        return False, f"Desalinhamento de tags estruturais: {tags_orig} vs {tags_trad}"
    return True, ""

def mascarar_tags(texto):
    tags_encontradas = re.findall(r'(\\[Nn]|{\\[^}]+}|<[^>]+>)', texto)
    texto_mascarado = texto
    for i, tag in enumerate(tags_encontradas):
        texto_mascarado = texto_mascarado.replace(tag, f"[T{i}]")
    return texto_mascarado, tags_encontradas

def restaurar_tags(texto_traduzido, tags_encontradas):
    texto_restaurado = texto_traduzido
    for i, tag in enumerate(tags_encontradas):
        texto_restaurado = texto_restaurado.replace(f"[T{i}]", tag)
    return texto_restaurado

def formatar_prompt(trechos):
    user_msg = "Correct the following lines:\n"
    for i, trecho in enumerate(trechos):
        user_msg += f"[{i}] {trecho}\n"
    return user_msg

def pedir_revisao_lmstudio(trechos):
    if not trechos:
        return []

    resultados = [None] * len(trechos)
    trechos_para_traduzir = []
    indices_mapeamento = []
    tags_por_trecho = []

    for i, trecho in enumerate(trechos):
        if not trecho.strip() or re.fullmatch(r'[ \t]+', trecho):
            resultados[i] = trecho
            continue
        if trecho in cache_traducoes:
            resultados[i] = cache_traducoes[trecho]
            continue
        
        trecho_masc, tags = mascarar_tags(trecho)
        trechos_para_traduzir.append(trecho_masc)
        indices_mapeamento.append(i)
        tags_por_trecho.append(tags)

    if not trechos_para_traduzir:
        return resultados

    user_prompt = formatar_prompt(trechos_para_traduzir)
    payload = {
        "model": "local-model",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2, # Temperatura baixa garante menor nível de "invenção" e apenas revisão gramatical
        "max_tokens": 1024,
        "stream": False
    }

    for tentativa in range(2):
        try:
            if tentativa == 0:
                estatisticas["total_solicitacoes"] += 1
            resposta = requests.post(LM_STUDIO_URL, json=payload, timeout=120)
            resposta.raise_for_status()
            dados = resposta.json()
            texto_traduzido = dados['choices'][0]['message']['content'].strip()
            break
        except Exception as e:
            if tentativa == 0:
                log_terminal("AVISO", f"Falha de rede na API. Retentando em 5s... Erro: {e}")
                time.sleep(5)
            else:
                estatisticas["erros"] += 1
                # Em caso de falha definitiva de rede, mantemos a fala original quebrada
                return [t for t in trechos]

    try:
        linhas_traduzidas = texto_traduzido.split('\n')
        dict_traducoes = {}
        for linha in linhas_traduzidas:
            match = re.match(r'^\[(\d+)\]\s*(.*)$', linha.strip())
            if match:
                idx_bloco = int(match.group(1))
                texto_pt = match.group(2).strip()
                dict_traducoes[idx_bloco] = texto_pt

        for idx_local, trecho_orig_masc in enumerate(trechos_para_traduzir):
            idx_global = indices_mapeamento[idx_local]
            texto_pt_masc = dict_traducoes.get(idx_local, "").strip()

            if not texto_pt_masc:
                resultados[idx_global] = trechos[idx_global]
                estatisticas["erros"] += 1
                continue

            texto_pt = restaurar_tags(texto_pt_masc, tags_por_trecho[idx_local])

            tags_ok, erro_tag = valida_estrutura_tags(trechos[idx_global], texto_pt)
            if not tags_ok:
                estatisticas["erros_tag_bloqueados"] += 1
                resultados[idx_global] = trechos[idx_global]
                continue

            cache_traducoes[trechos[idx_global]] = texto_pt
            resultados[idx_global] = texto_pt
            estatisticas["sucessos"] += 1

        salvar_cache()
        return resultados

    except Exception as e:
        estatisticas["erros"] += 1
        return [t for t in trechos]

def traduzir_arquivo(arquivo_origem):
    nome_arquivo = os.path.basename(arquivo_origem)
    novo_nome = nome_arquivo.replace(".ass", "_REVISADO.ass")
    caminho_saida = os.path.join(PASTA_ENTRADA, novo_nome)

    if os.path.exists(caminho_saida):
        log_terminal("DEBUG", f"Pulando arquivo já existente: {novo_nome}")
        return

    try:
        with open(arquivo_origem, 'r', encoding='utf-8-sig', errors='replace') as f:
            linhas = f.readlines()

        textos_extraidos = []
        mapeamento_linhas = []

        for num_linha, linha in enumerate(linhas):
            match = PADRAO_LINHA_FALA.match(linha)
            if match:
                textos_extraidos.append(match.group(2).strip())
                mapeamento_linhas.append(num_linha)

        tamanho_lote = 15
        traducoes_finais = []
        
        with tqdm(total=len(textos_extraidos), desc=f"Revisando ({len(textos_extraidos)} trechos)", unit="trecho") as pbar:
            for i in range(0, len(textos_extraidos), tamanho_lote):
                lote = textos_extraidos[i : i + tamanho_lote]
                traducoes = pedir_revisao_lmstudio(lote)
                traducoes_finais.extend(traducoes)
                pbar.update(len(lote))

        for idx, num_linha in enumerate(mapeamento_linhas):
            texto_traduzido = traducoes_finais[idx]
            match = PADRAO_LINHA_FALA.match(linhas[num_linha])
            if match:
                linhas[num_linha] = match.group(1) + texto_traduzido + "\n"

        with open(caminho_saida, 'w', encoding='utf-8') as f:
            f.writelines(linhas)

        log_terminal("SUCESSO", f"Arquivo salvo com correção gramatical: {caminho_saida}")

    except Exception as e:
        log_terminal("ERRO", f"Falha catastrófica no arquivo {nome_arquivo}: {e}")

def main():
    print("\n\033[94m" + " "*26 + "VALIDAÇÃO DE INFRAESTRUTURA\n" + " "*21 + "="*30 + "\033[0m")
    try:
        r = requests.get(LM_STUDIO_URL.replace("/chat/completions", "/models"), timeout=3)
        if r.status_code == 200:
            log_terminal("SUCESSO", "LM Studio OK.")
    except Exception:
        log_terminal("AVISO", "LM Studio offline. Inicie o servidor antes de rodar.")
        sys.exit(1)

    carregar_cache()

    arquivos = glob.glob(os.path.join(glob.escape(PASTA_ENTRADA), '*_PTBR_ENG.ass'))
    alvos = [arq for arq in arquivos if 'S01E11' in arq or 'S01E12' in arq or 'S01E13' in arq]
    
    if not alvos:
        log_terminal("ERRO", "Nenhum arquivo encontrado para revisar.")
        sys.exit(1)

    print("\n\033[94m" + " "*29 + "CORREÇÃO GRAMATICAL EM LOTE\n" + " "*24 + "="*30 + "\033[0m")

    for arq in alvos:
        if os.path.basename(arq).endswith('_REVISADO.ass'):
            continue
        log_terminal("INFO", f"Revisando EPs: {os.path.basename(arq)}")
        traduzir_arquivo(arq)

    salvar_estatisticas()
    log_terminal("INFO", f"Finalizado. Sucessos Gramaticais: {estatisticas['sucessos']}")

if __name__ == '__main__':
    main()
