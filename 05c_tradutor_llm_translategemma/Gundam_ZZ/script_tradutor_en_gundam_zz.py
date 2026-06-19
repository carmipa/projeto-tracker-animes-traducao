#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PIPELINE INDUSTRIAL UNIFICADO - VERSÃO INGLÊS (EN -> PT-BR)
Alvo: Mobile Suit Gundam ZZ (1986)
Motor: TranslateGemma 12B (Otimizado para preservação de Tags/Lore)
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
PASTA_ENTRADA = input("Digite o caminho da pasta de legendas originais: ").strip(' "\'')
PASTA_SAIDA = input("Digite o caminho da pasta para salvar as legendas PTBR: ").strip(' "\'')

if not PASTA_SAIDA:
    PASTA_SAIDA = os.path.join(os.path.dirname(PASTA_ENTRADA), "legendas_ptbr")

LM_STUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
ARQUIVO_CACHE = os.path.join(BASE_DIR, "traducao_cache_gundam_zz_en.json")
ARQUIVO_STATS = os.path.join(LOGS_DIR, f"stats_en_gundam_zz_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json")

# Regex de Estrutura ASS/SRT (para separar tempo/formatação do texto)
PADRAO_LINHA_FALA = re.compile(r"^(Dialogue:\s*[^,]*(?:,[^,]*){8},)(.*)$")
PADRAO_SRT_TEMPO = re.compile(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$')
PADRAO_SRT_INDICE = re.compile(r'^\d+$')

# Validador Anti-Alucinação Inglês
PADRAO_RESIDUO_INGLES = re.compile(r'\b(you|are|what|there|the|is|and|to|it|that|this)\b', re.IGNORECASE)

# ==========================================
# GESTÃO DE ESTADO & LOGS
# ==========================================
os.makedirs(PASTA_SAIDA, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

cache_traducoes = {}
estatisticas = {
    "total_solicitacoes": 0,
    "sucessos": 0,
    "erros": 0,
    "alucinacoes_bloqueadas": 0,
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
        log_terminal("INFO", f"Cache carregado: {len(cache_traducoes)} traduções.")

def salvar_cache():
    with open(ARQUIVO_CACHE, 'w', encoding='utf-8') as f:
        json.dump(cache_traducoes, f, ensure_ascii=False, indent=2)

def salvar_estatisticas():
    estatisticas["tempo_fim"] = datetime.now().isoformat()
    with open(ARQUIVO_STATS, 'w', encoding='utf-8') as f:
        json.dump(estatisticas, f, ensure_ascii=False, indent=4)

# ==========================================
# MOTOR LLM (TRANSLATEGEMMA 12B)
# ==========================================

SYSTEM_PROMPT = """You are an elite English to Brazilian Portuguese translator explicitly programmed to preserve absolute structure.
You will receive raw subtitle lines (.ass or .srt format).
Your strict instructions:
1. Translate ONLY the English dialogue into natural, grammatically flawless Brazilian Portuguese (pt-BR).
2. DO NOT modify, translate, or remove ANY technical tags. You MUST return them exactly where they were.
   - Example tags to preserve: \\N, \\n, {\\an8}, <i>, </i>, [T1], [T2].
3. DO NOT translate proper nouns or terms from the Universal Century. KEEP THEM IN ENGLISH:
   - Factions/Ships: AEUG, Neo Zeon, Titans, Karaba, Argama, Endra, Nahel Argama, Axis.
   - Characters: Judau Ashta, Haman Karn, Mashymre Cello, Roux Louka, Elpeo Ple, Ple Two, Glemy Toto, Bright Noa, Yazan Gable, Chara Soon, Leina Ashta.
   - Lore: Mobile Suit, Newtype, Minovsky, Gundam Team, ZZ Gundam, Zeta Gundam, Hyaku Shiki, Qubeley, Core Fighter, Shangri-La.
4. Output NOTHING but the final translated text. No pleasantries, no notes."""

def valida_estrutura_tags(original, traduzido):
    tags_orig = re.findall(r'(\\[Nn]|{\\[^}]+}|<[^>]+>|\[T\d+\])', original)
    tags_trad = re.findall(r'(\\[Nn]|{\\[^}]+}|<[^>]+>|\[T\d+\])', traduzido)
    if sorted(tags_orig) != sorted(tags_trad):
        return False, f"Desalinhamento de tags estruturais: {tags_orig} vs {tags_trad}"
    return True, ""

def formatar_prompt(trechos):
    user_msg = "Translate the following lines:\n"
    for i, trecho in enumerate(trechos):
        user_msg += f"[{i}] {trecho}\n"
    return user_msg

def pedir_traducao_lmstudio(trechos):
    if not trechos:
        return []

    # Checa Cache
    resultados = [None] * len(trechos)
    trechos_para_traduzir = []
    indices_mapeamento = []

    for i, trecho in enumerate(trechos):
        if not trecho.strip() or re.fullmatch(r'[ \t]+', trecho):
            resultados[i] = trecho
            continue
        if trecho in cache_traducoes:
            resultados[i] = cache_traducoes[trecho]
            continue
        
        trechos_para_traduzir.append(trecho)
        indices_mapeamento.append(i)

    if not trechos_para_traduzir:
        return resultados

    user_prompt = formatar_prompt(trechos_para_traduzir)
    payload = {
        "model": "local-model",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 1.0,
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
                log_terminal("AVISO", f"Falha de rede/timeout na API. Retentando em 5s... Erro: {e}")
                time.sleep(5)
            else:
                estatisticas["erros"] += 1
                return ["[ERRO_TRADUCAO] " + t for t in trechos]

    try:
        # Parse robusto das respostas TranslateGemma
        linhas_traduzidas = texto_traduzido.split('\n')
        dict_traducoes = {}
        for linha in linhas_traduzidas:
            match = re.match(r'^\[(\d+)\]\s*(.*)$', linha.strip())
            if match:
                idx_bloco = int(match.group(1))
                texto_pt = match.group(2).strip()
                dict_traducoes[idx_bloco] = texto_pt

        for idx_local, trecho_orig in enumerate(trechos_para_traduzir):
            idx_global = indices_mapeamento[idx_local]
            texto_pt = dict_traducoes.get(idx_local, "").strip()

            if not texto_pt:
                resultados[idx_global] = "[ERRO_TRADUCAO] " + trecho_orig
                estatisticas["erros"] += 1
                continue

            # Anti-Alucinação (Resíduo Inglês)
            if PADRAO_RESIDUO_INGLES.search(texto_pt):
                estatisticas["alucinacoes_bloqueadas"] += 1
                resultados[idx_global] = "[ERRO_TRADUCAO] " + trecho_orig
                continue
                
            # Anti-Alucinação (Quebra de Tags)
            tags_ok, erro_tag = valida_estrutura_tags(trecho_orig, texto_pt)
            if not tags_ok:
                estatisticas["erros_tag_bloqueados"] += 1
                resultados[idx_global] = "[ERRO_TRADUCAO] " + trecho_orig
                continue

            cache_traducoes[trecho_orig] = texto_pt
            resultados[idx_global] = texto_pt
            estatisticas["sucessos"] += 1

        salvar_cache()
        return resultados

    except Exception as e:
        estatisticas["erros"] += 1
        return ["[ERRO_TRADUCAO] " + t for t in trechos]

def traduzir_arquivo(arquivo_origem):
    nome_arquivo = os.path.basename(arquivo_origem)
    is_srt = nome_arquivo.lower().endswith('.srt')
    novo_nome = nome_arquivo.replace("_ENG", "_PTBR") if "_ENG" in nome_arquivo else nome_arquivo.replace(".ass", "_PTBR.ass").replace(".srt", "_PTBR.srt")
    caminho_saida = os.path.join(PASTA_SAIDA, novo_nome)

    if os.path.exists(caminho_saida):
        log_terminal("DEBUG", f"Pulando arquivo já existente: {novo_nome}")
        return

    try:
        with open(arquivo_origem, 'r', encoding='utf-8-sig', errors='replace') as f:
            linhas = f.readlines()

        textos_extraidos = []
        mapeamento_linhas = []

        for num_linha, linha in enumerate(linhas):
            if is_srt:
                texto_limpo = linha.strip()
                if not texto_limpo or PADRAO_SRT_TEMPO.match(texto_limpo) or PADRAO_SRT_INDICE.match(texto_limpo):
                    continue
                textos_extraidos.append(texto_limpo)
                mapeamento_linhas.append(num_linha)
            else:
                match = PADRAO_LINHA_FALA.match(linha)
                if match:
                    textos_extraidos.append(match.group(2).strip())
                    mapeamento_linhas.append(num_linha)

        tamanho_lote = 15
        traducoes_finais = []
        
        desc_bar = f"{'TranslateGemma 12B'}"
        with tqdm(total=len(textos_extraidos), desc=f"Traduzindo via {desc_bar} ({len(textos_extraidos)} trechos)", unit="trecho") as pbar:
            for i in range(0, len(textos_extraidos), tamanho_lote):
                lote = textos_extraidos[i : i + tamanho_lote]
                traducoes = pedir_traducao_lmstudio(lote)
                traducoes_finais.extend(traducoes)
                pbar.update(len(lote))

        for idx, num_linha in enumerate(mapeamento_linhas):
            texto_traduzido = traducoes_finais[idx]
            if is_srt:
                linhas[num_linha] = texto_traduzido + "\n"
            else:
                match = PADRAO_LINHA_FALA.match(linhas[num_linha])
                if match:
                    linhas[num_linha] = match.group(1) + texto_traduzido + "\n"

        with open(caminho_saida, 'w', encoding='utf-8') as f:
            f.writelines(linhas)

        log_terminal("SUCESSO", f"Arquivo salvo: {caminho_saida}")

    except Exception as e:
        log_terminal("ERRO", f"Falha catastrófica no arquivo {nome_arquivo}: {e}")

def main():
    print("\n\033[94m" + " "*26 + "VALIDAÇÃO DE INFRAESTRUTURA\n" + " "*21 + "="*30 + "\033[0m")
    log_terminal("DEBUG", f"Testando LM Studio em {LM_STUDIO_URL}...")
    try:
        r = requests.get(LM_STUDIO_URL.replace("/chat/completions", "/models"), timeout=3)
        if r.status_code == 200:
            log_terminal("SUCESSO", "LM Studio OK.")
    except Exception:
        log_terminal("AVISO", "LM Studio offline. Inicie o servidor antes de rodar.")
        sys.exit(1)

    carregar_cache()

    if not os.path.exists(PASTA_ENTRADA):
        log_terminal("ERRO", f"Pasta de entrada não encontrada: {PASTA_ENTRADA}")
        sys.exit(1)

    arquivos = glob.glob(os.path.join(glob.escape(PASTA_ENTRADA), '*_ENG.ass')) + glob.glob(os.path.join(glob.escape(PASTA_ENTRADA), '*_ENG.srt'))
    arquivos = sorted(list(set(arquivos)))

    print("\n\033[94m" + " "*29 + "PROCESSAMENTO EM LOTE\n" + " "*24 + "="*30 + "\033[0m")

    for arq in arquivos:
        if os.path.basename(arq).endswith('_PTBR.ass') or os.path.basename(arq).endswith('_PTBR.srt'):
            continue
        log_terminal("INFO", f"Processando: {os.path.basename(arq)}")
        traduzir_arquivo(arq)

    salvar_estatisticas()
    log_terminal("DEBUG", f"Stats salvo: {os.path.basename(ARQUIVO_STATS)}")
    log_terminal("INFO", f"Finalizado. Sucessos: {estatisticas['sucessos']}, Bloqueios Anti-Alucinação: {estatisticas['alucinacoes_bloqueadas']}, Falhas de Tags: {estatisticas['erros_tag_bloqueados']}")

if __name__ == '__main__':
    main()
