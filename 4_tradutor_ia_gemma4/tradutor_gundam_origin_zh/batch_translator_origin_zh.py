#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MODULO: batch_translator_origin_zh.py (Batch Mode v5 - Resiliente)
Otimizado para tradução de Chinês Simplificado (CHS) para Português do Brasil (PT-BR)
usando o modelo local Qwen2.5 via LM Studio.
Inclui:
- Cache persistente em disco (traducao_cache_origin_zh.json) baseado em linhas mascaradas.
- Fallback resiliente automático linha por linha se a chamada em lote falhar.
- Limpeza avançada contra preâmbulos/postamblos conversacionais do LLM.
- Métricas de tempo detalhadas por arquivo e acumuladas.

Author: Paulo + Antigravity
Data: Junho 2026
"""

import os
import re
import sys
import json
import time
import argparse
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from colorama import init, Fore, Style

init(autoreset=True)

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
LM_STUDIO_MODELS_URL = "http://localhost:1234/v1/models"
MAX_THREADS = 2   # Threads paralelas no LM Studio
BATCH_SIZE = 8    # Diálogos por lote de tradução
MODELO_ATIVO = "local-model"
MAX_TAGS_POR_LINHA = 24

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_INFO = os.path.join(PASTA_SCRIPT, "info.txt")
DEBUG_FILE = os.path.join(PASTA_SCRIPT, "debug_last_failure.txt")
CAMINHO_CACHE = os.path.join(PASTA_SCRIPT, "traducao_cache_origin_zh.json")

CACHE = {}
_debug_salvo = False

SYSTEM_PROMPT = (
    "Você é um tradutor especialista de anime japonês, especializado na franquia Gundam e na linha temporal Universal Century (UC).\n"
    "Traduza as linhas de legenda numeradas fornecidas do Chinês Simplificado (CHS) para o Português do Brasil (PT-BR) de forma fluida e natural.\n\n"
    
    "REGRAS CRÍTICAS:\n"
    "1. Mantenha exatamente a mesma numeração, ordem e estrutura de linhas (ex: '1. tradução', '2. tradução').\n"
    "2. Responda APENAS com as linhas traduzidas numeradas. Não adicione observações, explicações, introduções ou comentários.\n"
    "3. Nunca mescle, divida, reordene, remova ou duplique as linhas numeradas.\n"
    "4. Mantenha intactos todos os marcadores e tags de legenda exatamente como recebidos, como '[T0]', '[T1]', '[T2]', '{\\an8}', '<i>', '</i>', etc. Eles devem permanecer na mesma posição.\n"
    "5. Converta a pontuação chinesa de largura total (como '，', '。', '！', '？', '“', '”') para a pontuação ocidental correspondente (',', '.', '!', '?', '\"', '\"').\n"
    "6. A saída final não pode conter caracteres chineses. Se houver créditos/fansub, traduza o sentido para PT-BR e preserve URLs/nomes romanizados.\n\n"
    
    "GLOSSÁRIO DE GUNDAM ORIGIN (MANTENHA OS NOMES OFICIAIS EM INGLÊS/PORTUGUÊS):\n"
    "Use a tradução correta para estes termos em chinês:\n"
    "- 联邦 (Liánbāng) ou 地球联邦 ➔ Federação da Terra (ou apenas Federação)\n"
    "- 地球圈 ➔ Esfera Terrestre, nunca 'Terra Sfera'\n"
    "- 吉翁 (Jíwēng) ou 吉翁公国 ➔ Zeon (ou Principado de Zeon)\n"
    "- 戴肯 (Dàikěn) / 吉翁·兹姆·戴肯 ➔ Deikun / Zeon Zum Deikun\n"
    "- 阿斯特莱雅 (Āsītèláiyǎ) ➔ Astraia Tor Deikun\n"
    "- 卡斯帕尔 (Kǎsīpà'ěr) ➔ Casval Rem Deikun (ou apenas Casval)\n"
    "- 阿尔黛西亚 (Ā'ěrdàixīyà) ➔ Artesia Som Deikun (ou apenas Artesia)\n"
    "- 爱德华·玛斯 / 爱德华 ➔ Édouard Mass / Édouard\n"
    "- 塞拉·玛斯 / 塞拉 ➔ Sayla Mass / Sayla\n"
    "- 夏亚·阿兹纳布尔 / 夏亚 ➔ Char Aznable / Char\n"
    "- 阿姆罗·雷 / 阿姆罗 ➔ Amuro Ray / Amuro\n"
    "- 兰巴·拉尔 / 兰巴 ➔ Ramba Ral / Ramba\n"
    "- 金巴·拉尔 / 金巴 ➔ Jimba Ral / Jimba\n"
    "- 哈蒙 / 克劳蕾·哈蒙 ➔ Hamon / Crowley Hamon\n"
    "- 德金·扎比 / 德金 ➔ Degwin Zabi / Degwin (ou Degwin Sodo Zabi)\n"
    "- 基连·扎比 / 基连 ➔ Gihren Zabi / Gihren\n"
    "- 萨斯罗·扎比 / 萨斯罗 ➔ Sasro Zabi / Sasro\n"
    "- 多兹鲁·扎比 / 多兹鲁 ➔ Dozle Zabi / Dozle\n"
    "- 基西莉亚·扎比 / 基西莉亚 ➔ Kycilia Zabi / Kycilia\n"
    "- 卡尔玛·扎比 / 卡尔玛 ➔ Garma Zabi / Garma\n"
    "- 米诺夫斯基 ➔ Minovsky\n"
    "- 米诺夫斯基粒子 ➔ Partículas Minovsky\n"
    "- 机动战士 ➔ Mobile Suit\n"
    "- 钢坦克 ➔ Guntank\n"
    "- 钢加农 ➔ Guncannon\n"
    "- 扎古 ➔ Zaku\n"
    "- 鲁姆战役 ➔ Batalha de Loum\n"
    "- 红色彗星 ➔ Cometa Vermelho\n"
    "- 白色基地 ➔ White Base\n"
    "- 路西法 ➔ Lucifer\n\n"
    "- 演讲 / 演讲稿 ➔ discurso / texto do discurso, nunca palestra em contexto político\n"
    "- 各各他 ➔ Gólgota\n"
    "- 十字架 ➔ cruz\n"
    "- 盖亚 ➔ Gaia\n\n"
    
    "DIRETRIZES DE ESTILO PARA LEGENDAS EM PT-BR:\n"
    "1. Evite traduções literais. Adapte para que soe natural em português brasileiro falado.\n"
    "2. Mantenha o tom sério, político e dramático de ficção científica militar do anime.\n"
    "3. Se uma linha for ambígua, use o contexto político e militar de Gundam.\n"
)

MAPA_PONTUACAO_CHINESA = str.maketrans({
    "，": ",",
    "。": ".",
    "！": "!",
    "？": "?",
    "：": ":",
    "；": ";",
    "“": '"',
    "”": '"',
    "‘": "'",
    "’": "'",
    "（": "(",
    "）": ")",
    "…": "...",
})

PADRAO_CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")

SUBSTITUICOES_POS_PROCESSAMENTO = [
    (re.compile(r"\bTerra Sfera\b", re.I), "Esfera Terrestre"),
    (re.compile(r"\bEssa palestra\b"), "Esse discurso"),
    (re.compile(r"\bessa palestra\b"), "esse discurso"),
    (re.compile(r"\bA palestra\b"), "O discurso"),
    (re.compile(r"\ba palestra\b"), "o discurso"),
    (re.compile(r"\bpalestra\b", re.I), "discurso"),
    (re.compile(r"\bGogltha\b", re.I), "Gólgota"),
    (re.compile(r"\bGolgotha\b", re.I), "Gólgota"),
    (re.compile(r"\bpregão de Gólgota\b", re.I), "lugar de execução do Gólgota"),
    (re.compile(r"\bcruzamento\b", re.I), "cruz"),
    (re.compile(r"\bao Federação\b", re.I), "à Federação"),
    (re.compile(r"\bdo Federação\b", re.I), "da Federação"),
    (re.compile(r"\bA Terra Federação\b", re.I), "A Federação da Terra"),
    (re.compile(r"\bComputador Shinjico\b", re.I), "Shinjico"),
    (re.compile(r"\bTurma do Conto\b", re.I), "Grupo de Legendas Manyuu"),
    (re.compile(r"\bmorrendo em extinção\b", re.I), "até serem exterminados"),
]

PADRAO_PREAMBULO_LLM = re.compile(
    r"^(aqui|claro|tradu[çc][aã]o|abaixo|ok|segue|segunda|resposta|espero|vou traduzir|as tradu[çc][oõ]es)",
    re.I,
)


# ============================================================================
# CACHE DE TRADUÇÃO PERSISTENTE EM DISCO
# ============================================================================

def carregar_cache():
    global CACHE
    if os.path.exists(CAMINHO_CACHE):
        try:
            with open(CAMINHO_CACHE, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            if not isinstance(dados, dict):
                raise ValueError("cache nao e um objeto JSON")

            cache_limpo = {}
            entradas_removidas = 0
            entradas_corrigidas = 0
            for original, traducao in dados.items():
                if not isinstance(original, str) or not isinstance(traducao, str):
                    entradas_removidas += 1
                    continue
                traducao_corrigida = post_processar_traducao(traducao)
                if not validar_traducao(original, traducao_corrigida):
                    entradas_removidas += 1
                    continue
                if traducao_corrigida != traducao:
                    entradas_corrigidas += 1
                cache_limpo[original] = traducao_corrigida

            CACHE = cache_limpo
            print(f"{Fore.GREEN}[CACHE] Carregado {len(CACHE)} traduções válidas do disco.")
            if entradas_removidas or entradas_corrigidas:
                print(
                    f"{Fore.YELLOW}[CACHE] Saneamento: {entradas_corrigidas} corrigidas, "
                    f"{entradas_removidas} removidas."
                )
                salvar_cache()
        except Exception as e:
            print(f"{Fore.YELLOW}[CACHE] Erro ao carregar cache, iniciando vazio: {e}")
            CACHE = {}
    else:
        CACHE = {}


def salvar_cache():
    try:
        caminho_tmp = CAMINHO_CACHE + ".tmp"
        with open(caminho_tmp, 'w', encoding='utf-8') as f:
            json.dump(CACHE, f, indent=2, ensure_ascii=False)
        os.replace(caminho_tmp, CAMINHO_CACHE)
    except Exception as e:
        print(f"{Fore.RED}[CACHE] Erro ao salvar cache em disco: {e}")


def post_processar_traducao(texto: str) -> str:
    """Normaliza pontuação e corrige erros recorrentes observados no cache."""
    if not texto:
        return ""

    texto = texto.translate(MAPA_PONTUACAO_CHINESA)
    texto = re.sub(r"\s+([,.!?;:])", r"\1", texto)
    texto = re.sub(r"([¿¡])\s+", r"\1", texto)
    texto = re.sub(r"[ \t]{2,}", " ", texto)

    for padrao, substituto in SUBSTITUICOES_POS_PROCESSAMENTO:
        texto = padrao.sub(substituto, texto)

    return texto.strip()


def validar_traducao(original: str, traducao: str) -> bool:
    """Evita cachear/usar saídas alucinadas, vazias ou ainda em chinês."""
    if not traducao or "[ERRO_TRADUCAO" in traducao:
        return False
    if PADRAO_CJK.search(traducao):
        return False
    if PADRAO_PREAMBULO_LLM.search(traducao.strip()):
        return False
    if len(traducao) > max(220, len(original) * 8):
        return False
    return True


# ============================================================================
# INFRA & DIRETÓRIOS
# ============================================================================

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
        print(f"{Fore.RED}[ERRO] LM Studio não está rodando em localhost:1234.")
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


def ler_arquivo_legenda(caminho):
    """Lê ASS chinês com fallback de encoding sem abortar o lote."""
    encodings = ("utf-8-sig", "utf-8", "gb18030", "big5", "cp936")
    for encoding in encodings:
        try:
            with open(caminho, 'r', encoding=encoding) as f:
                return f.readlines(), encoding
        except UnicodeDecodeError:
            continue

    with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
        return f.readlines(), "utf-8-replace"


# ============================================================================
# PROCESSAMENTO DE MASCARAMENTO & PARSE
# ============================================================================

def mascarar_tags(texto_bruto: str):
    """Substitui tags ASS {...} por placeholders numerados [T0], [T1], etc."""
    tags = re.findall(r'\{[^}]+\}', texto_bruto)
    texto_limpo = texto_bruto
    for idx_tag, tag in enumerate(tags):
        texto_limpo = texto_limpo.replace(tag, f"[T{idx_tag}]", 1)
    return texto_limpo, tags


def restaurar_tags(texto_traduzido: str, tags: list):
    """Reinsere as tags originais no lugar dos placeholders e remove alucinações."""
    trad = texto_traduzido
    for idx_tag, tag in enumerate(tags):
        marcador = f"[T{idx_tag}]"
        if marcador in trad:
            trad = trad.replace(marcador, tag, 1)
        else:
            # Fallback tolerante para variações de escrita de tag geradas pelo LLM
            trad = re.sub(rf'\[?[Tt]\s*{idx_tag}\]?', lambda _m: tag, trad, count=1)
    # Remove quaisquer marcadores extras [T...] que foram alucinados pelo LLM
    trad = re.sub(r'\[[Tt]\s*\d+\]', '', trad)
    for tag in tags:
        if tag not in trad:
            trad = f"{tag}{trad}"
    return trad


def _limpar_markdown(texto):
    """Remove formatações indesejadas que a IA possa introduzir no texto."""
    texto = re.sub(r'\*+', '', texto)   # remove ** e *
    texto = re.sub(r'_+', '', texto)    # remove __ e _
    texto = texto.strip().strip('"').strip("'")
    return post_processar_traducao(texto)


def _parsear_resposta_numerada(conteudo, n_esperado):
    """Filtra e extrai a tradução numerada da resposta bruta do LLM."""
    linhas = []
    for linha in conteudo.split('\n'):
        m = re.match(r'^\d+(?:\.|\)| -|:)\s*(.+)', linha.strip())
        if m:
            linhas.append(_limpar_markdown(m.group(1)))
    
    if len(linhas) >= n_esperado:
        return linhas[:n_esperado]
        
    # Fallback: captura linhas que não parecem conversação do LLM
    linhas_raw = [
        _limpar_markdown(l)
        for l in conteudo.split('\n')
        if l.strip() and not PADRAO_PREAMBULO_LLM.match(l.strip())
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
    print(f"\n{Fore.YELLOW}[DEBUG] Resposta do modelo salva para auditoria em: {DEBUG_FILE}")


# ============================================================================
# TRADUÇÃO COM FALLBACK INDIVIDUAL
# ============================================================================

def traduzir_lote(lote_textos: list, tentativa=1) -> dict:
    """Envia um lote de textos de forma estrita para a API do LM Studio."""
    texto_numerado = "\n".join(f"{i+1}. {t}" for i, t in enumerate(lote_textos))

    payload = {
        "model": MODELO_ATIVO,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Traduza estas {len(lote_textos)} linhas para PT-BR. Retorne APENAS as traduções numeradas:\n{texto_numerado}"}
        ],
        "temperature": 0.1,  # Baixa temperatura para manter a coerência do glossário
        "max_tokens": 4000
    }

    try:
        resposta = requests.post(LM_STUDIO_URL, json=payload, timeout=120)
        if resposta.status_code != 200:
            raise RuntimeError(f"HTTP {resposta.status_code} - {resposta.text[:100]}")
        
        conteudo = resposta.json()['choices'][0]['message']['content'].strip()
        traducoes = _parsear_resposta_numerada(conteudo, len(lote_textos))
        
        # Limpeza contra conversas de encerramento adicionais no final
        if traducoes:
            ultimo_idx = len(traducoes) - 1
            linhas_ultimo = traducoes[ultimo_idx].split('\n')
            if len(linhas_ultimo) > 1:
                linhas_limpas_ultimo = []
                for l in linhas_ultimo:
                    if re.search(r"^(espero|aqui está|aqui esta|se precisar|traduzido|espero que|bonne chance|voilà|espero ajudar)", l.strip(), re.IGNORECASE):
                        break
                    linhas_limpas_ultimo.append(l)
                traducoes[ultimo_idx] = "\n".join(linhas_limpas_ultimo).strip()

        # Retorna o dicionário com índice local -> texto traduzido
        resultado = {}
        for i, (original, traducao) in enumerate(zip(lote_textos, traducoes)):
            traducao = post_processar_traducao(traducao)
            if validar_traducao(original, traducao):
                resultado[i] = traducao

        if len(resultado) < len(lote_textos):
            _salvar_debug(texto_numerado, conteudo, traducoes)

        return resultado
    except Exception as e:
        if tentativa < 2:
            time.sleep(2 * tentativa)
            return traduzir_lote(lote_textos, tentativa + 1)
        raise e


def traduzir_lote_resiliente(lote_textos: list) -> dict:
    """
    Traduz o lote de diálogos. Caso ocorra erro de API ou corte nas linhas,
    inicia automaticamente o fallback traduzindo linha por linha.
    """
    try:
        resultado = traduzir_lote(lote_textos)
        if len(resultado) == len(lote_textos):
            return resultado
        raise RuntimeError(f"Tradução retornou apenas {len(resultado)}/{len(lote_textos)} linhas.")
    except Exception as e:
        # Fallback individual linha a linha
        print(f"\n{Fore.YELLOW}[AVISO] Lote falhou ({e}). Iniciando fallback resiliente linha a linha...")
        resultado_resiliente = {}
        for idx_local, texto in enumerate(lote_textos):
            sucesso_linha = False
            for tentativa in range(1, 4):
                try:
                    res_indiv = traduzir_lote([texto])
                    if 0 in res_indiv and validar_traducao(texto, res_indiv[0]):
                        resultado_resiliente[idx_local] = res_indiv[0]
                        sucesso_linha = True
                        break
                except Exception:
                    time.sleep(1)
            
            if not sucesso_linha:
                print(f"{Fore.RED}[FALHA] Não foi possível traduzir linha: '{texto[:35]}...'")
                resultado_resiliente[idx_local] = f"[ERRO_TRADUCAO: {texto}]"
        
        return resultado_resiliente


# ============================================================================
# TRADUÇÃO CONCORRENTE DA LEGENDA
# ============================================================================

def traduzir_bloco_ia(bloco):
    """
    Executa a tradução de um bloco de linhas (enviado via ThreadPoolExecutor).
    bloco = list of (index, metadados, texto_mascarado, tags)
    Retorna list of (index, linha_final_ass, usou_fallback).
    """
    resultados_vazios = {}
    bloco_util = []
    
    for item in bloco:
        idx_arq, meta, texto_masc, tags = item
        if not texto_masc.strip():
            # Linhas vazias são montadas diretamente sem chamar a IA
            resultados_vazios[idx_arq] = (idx_arq, f"{meta}{texto_masc}\n", False)
        else:
            bloco_util.append(item)

    if not bloco_util:
        return list(resultados_vazios.values())

    # Rastreabilidade
    indices_u = [x[0] for x in bloco_util]
    metadados_u = [x[1] for x in bloco_util]
    textos_u = [x[2] for x in bloco_util]
    tags_u = [x[3] for x in bloco_util]

    # Chama o tradutor resiliente
    resultado_lote = traduzir_lote_resiliente(textos_u)

    resultados_finais = list(resultados_vazios.values())
    for idx_local, (idx_arq, meta, texto_orig, tags) in enumerate(zip(indices_u, metadados_u, textos_u, tags_u)):
        usou_fallback = False
        if idx_local in resultado_lote:
            traducao_masc = resultado_lote[idx_local]
            if "[ERRO_TRADUCAO" in traducao_masc:
                usou_fallback = True
            
            # Reconstrói a linha unindo metadados + texto traduzido com as tags originais restauradas
            trad_restaurada = restaurar_tags(traducao_masc, tags)
            resultados_finais.append((idx_arq, f"{meta}{trad_restaurada}\n", usou_fallback))
        else:
            resultados_finais.append((idx_arq, f"{meta}[ERRO_TRADUCAO: {texto_orig}]\n", True))
            
    return resultados_finais


# ============================================================================
# PIPELINE CENTRAL
# ============================================================================

def formatar_tempo(segundos):
    """Formata um intervalo de tempo em segundos para a string representativa (Xm Ys)."""
    m, s = divmod(int(segundos), 60)
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Traduz legendas .chs.ass de Gundam The Origin para PT-BR via LM Studio."
    )
    parser.add_argument("--entrada", help="Pasta com arquivos .chs.ass")
    parser.add_argument("--saida", help="Pasta de saída para arquivos *_PTBR.ass")
    parser.add_argument(
        "--padrao",
        default=".chs.ass",
        help="Sufixo de legenda a processar (default: .chs.ass). Use .cht.ass para chinês tradicional.",
    )
    parser.add_argument("--threads", type=int, default=MAX_THREADS, help="Threads paralelas de chamada ao LM Studio")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="Quantidade de diálogos por chamada")
    parser.add_argument(
        "--limpar-cache",
        action="store_true",
        help="Descarta o cache atual antes de traduzir. Útil quando o glossário/prompt foi corrigido.",
    )
    return parser.parse_args()


def executar_pipeline_lote(args=None):
    global MAX_THREADS, BATCH_SIZE, CACHE
    args = args or parse_args()
    MAX_THREADS = max(1, args.threads)
    BATCH_SIZE = max(1, args.batch_size)

    print("=" * 80)
    print(f"{Fore.CYAN}    TRADUTOR GUNDAM THE ORIGIN ZH | BATCH {BATCH_SIZE}L/CHAMADA | THREADS={MAX_THREADS} | CACHE")
    print("=" * 80)

    verificar_lm_studio()
    carregar_cache()
    if args.limpar_cache:
        CACHE = {}
        salvar_cache()
        print(f"{Fore.YELLOW}[CACHE] Cache limpo por solicitação do operador.")

    caminho_padrao_origem = (
        r"D:\PROJETOS-OPEN\animes\[POPGO][Gundam_The_Origin_TV][MKV+ASS]"
        r"\[POPGO][Mobile_Suit_Gundam_The_Origin_Advent_of_the_Red_Comet][1080p][Webrip][ASS][CHS_CHT]"
    )
    pasta_origem = args.entrada or obter_diretorio_operador("Pasta com legendas CHS.ass", caminho_padrao_origem)

    caminho_padrao_saida = (
        r"D:\PROJETOS-OPEN\animes\[POPGO][Gundam_The_Origin_TV][MKV+ASS]"
        r"\legendas_ptbr"
    )
    pasta_saida = args.saida or obter_diretorio_operador("Pasta de saida PT-BR", caminho_padrao_saida)

    os.makedirs(pasta_saida, exist_ok=True)
    
    # Filtra os arquivos em chinês simplificado
    sufixo_legenda = args.padrao.lower()
    arquivos_ass = sorted([f for f in os.listdir(pasta_origem) if f.lower().endswith(sufixo_legenda)])

    if not arquivos_ass:
        print(f"{Fore.RED}[ERRO] Nenhum arquivo *{args.padrao} encontrado em: {pasta_origem}")
        return

    print(f"{Fore.GREEN}[OK] {len(arquivos_ass)} arquivo(s) *{args.padrao} localizado(s). Concorrência: {MAX_THREADS} threads.")

    linhas_relatorio = [
        "RELATORIO DE TRADUCAO BATCH - GUNDAM THE ORIGIN ZH -> PTBR",
        f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Modelo: {MODELO_ATIVO}",
        f"Batch size: {BATCH_SIZE} | Threads: {MAX_THREADS}",
        "=" * 80,
    ]
    
    total_fallbacks_geral = 0
    total_dialogos_geral = 0
    total_cache_hits_geral = 0
    
    # Inicia contador de tempo global
    tempo_inicio_global = time.time()

    with tqdm(total=len(arquivos_ass), desc="Temporada Completa", unit="arq", colour="green", ncols=80, position=0) as barra_macro:
        for idx_arq, arquivo in enumerate(arquivos_ass):
            tempo_inicio_arquivo = time.time()
            caminho_entrada = os.path.join(pasta_origem, arquivo)
            
            # Renomeia o sufixo da legenda chinesa para _PTBR.ass
            nome_saida_ptbr = re.sub(re.escape(args.padrao) + r'$', '_PTBR.ass', arquivo, flags=re.IGNORECASE)
            caminho_saida = os.path.join(pasta_saida, nome_saida_ptbr)

            barra_macro.set_postfix_str(arquivo[:35])
            tqdm.write(f"\n{Fore.YELLOW}[{idx_arq+1}/{len(arquivos_ass)}] -> {arquivo}")

            linhas_originais, encoding_detectado = ler_arquivo_legenda(caminho_entrada)
            tqdm.write(f"  {Fore.CYAN}Encoding: {encoding_detectado}")

            pat = re.compile(r"^(Dialogue:\s*[^,]*(?:,[^,]*){8},)(.*)$")

            mapa_linhas_finais: list[str | None] = [None] * len(linhas_originais)
            
            # Listas para rastreamento de diálogos que precisam ser enviados à IA (Cache misses)
            blocos_ia = []
            bloco_atual = []
            
            # Mapeamento do arquivo de saída
            total_dialogos = 0
            cache_hits_arquivo = 0
            fallbacks_arquivo = 0

            for i, linha in enumerate(linhas_originais):
                if linha.startswith("Dialogue:"):
                    total_dialogos += 1
                    partes = linha.split(",", 9)
                    if len(partes) == 10:
                        metadados = ",".join(partes[:9]) + ","
                        texto_bruto = partes[9].rstrip("\n")
                        
                        # Oculta tags para obter o texto limpo (usado como chave de cache)
                        texto_masc, tags = mascarar_tags(texto_bruto)
                        
                        # Ignora linhas com excesso de tags para evitar quebra de tokens no LLM
                        if len(tags) > MAX_TAGS_POR_LINHA:
                            mapa_linhas_finais[i] = linha
                            continue
                        
                        # Consulta no cache persistente
                        if texto_masc in CACHE and validar_traducao(texto_masc, CACHE[texto_masc]):
                            cache_hits_arquivo += 1
                            trad_cached = post_processar_traducao(CACHE[texto_masc])
                            # Restaura as tags exclusivas desta linha no texto recuperado do cache
                            trad_final = restaurar_tags(trad_cached, tags)
                            mapa_linhas_finais[i] = f"{metadados}{trad_final}\n"
                        else:
                            # Adiciona na fila de tradução da IA
                            bloco_atual.append((i, metadados, texto_masc, tags))
                            if len(bloco_atual) == BATCH_SIZE:
                                blocos_ia.append(bloco_atual)
                                bloco_atual = []
                    else:
                        mapa_linhas_finais[i] = linha
                else:
                    mapa_linhas_finais[i] = linha

            if bloco_atual:
                blocos_ia.append(bloco_atual)

            total_chamadas = len(blocos_ia)
            tqdm.write(f"  {Fore.CYAN}Diálogos: {total_dialogos} | Cache Hits: {cache_hits_arquivo} | Chamadas API: {total_chamadas}")

            # Se existirem novos blocos a traduzir
            if blocos_ia:
                with tqdm(total=total_chamadas, desc=f"  Ep {idx_arq+1:02d} batches", unit="bat", colour="cyan", ncols=80, position=1, leave=False) as barra_micro:
                    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                        futuros = {}
                        for bloco in blocos_ia:
                            f_submit = executor.submit(traduzir_bloco_ia, bloco)
                            futuros[f_submit] = bloco
                            
                        for futuro in as_completed(futuros):
                            orig_bloco = futuros[futuro]
                            try:
                                resultado_bloco = futuro.result()
                                for orig_idx, linha_proc, usou_fallback in resultado_bloco:
                                    mapa_linhas_finais[orig_idx] = linha_proc
                                    if usou_fallback:
                                        fallbacks_arquivo += 1
                                    
                                    # Salva o texto traduzido de forma limpa no cache em disco
                                    # Mapeia o texto mascarado de entrada com o texto mascarado retornado
                                    # Recuperamos a linha original
                                    m_orig = pat.match(linhas_originais[orig_idx].strip())
                                    m_proc = pat.match(linha_proc.strip())
                                    if m_orig and m_proc and not usou_fallback:
                                        original_txt = m_orig.group(2).strip()
                                        traduzido_txt = m_proc.group(2).strip()
                                        
                                        # Recria o texto limpo para o cache
                                        original_masc, _ = mascarar_tags(original_txt)
                                        traduzido_masc, _ = mascarar_tags(traduzido_txt)
                                        
                                        traduzido_masc = post_processar_traducao(traduzido_masc)
                                        if original_masc and validar_traducao(original_masc, traduzido_masc):
                                            CACHE[original_masc] = traduzido_masc
                                            
                            except Exception as e:
                                print(f"\n{Fore.RED}[ERRO] Erro crítico no lote de futuros: {e}")
                            barra_micro.update(1)

            # Grava a legenda final gerada em UTF-8
            with open(caminho_saida, 'w', encoding='utf-8') as f:
                f.writelines(l for l in mapa_linhas_finais if l is not None)

            # Grava o cache atualizado no disco a cada arquivo processado
            salvar_cache()

            tempo_fim_arquivo = time.time()
            duracao_arquivo = tempo_fim_arquivo - tempo_inicio_arquivo
            tempo_acumulado = tempo_fim_arquivo - tempo_inicio_global

            fmt_tempo_arq = formatar_tempo(duracao_arquivo)
            fmt_tempo_acum = formatar_tempo(tempo_acumulado)

            tqdm.write(
                f"{Fore.GREEN}  [CONCLUÍDO] {nome_saida_ptbr} | Cache Hits: {cache_hits_arquivo} | "
                f"Fallbacks: {fallbacks_arquivo} | Tempo: {Fore.YELLOW}{fmt_tempo_arq}{Fore.GREEN} (Acumulado: {Fore.CYAN}{fmt_tempo_acum}{Fore.GREEN})"
            )
            
            linhas_relatorio.append(
                f"{nome_saida_ptbr} | Diálogos: {total_dialogos} | Cache Hits: {cache_hits_arquivo} | "
                f"Chamadas: {total_chamadas} | Fallbacks: {fallbacks_arquivo} | Tempo: {fmt_tempo_arq}"
            )
            
            total_fallbacks_geral += fallbacks_arquivo
            total_dialogos_geral += total_dialogos
            total_cache_hits_geral += cache_hits_arquivo
            
            barra_macro.update(1)

    tempo_final_total = time.time() - tempo_inicio_global
    fmt_final_total = formatar_tempo(tempo_final_total)

    linhas_relatorio.append("=" * 80)
    linhas_relatorio.append(
        f"TOTAL: {len(arquivos_ass)} arquivos | {total_dialogos_geral} diálogos | "
        f"{total_cache_hits_geral} cache hits | {total_fallbacks_geral} fallbacks | Tempo total: {fmt_final_total}"
    )

    with open(ARQUIVO_INFO, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_relatorio) + "\n")

    print("\n" + "=" * 80)
    print(f"{Fore.GREEN}[SUCESSO] Tradutor em lote finalizado!")
    print(f"{Fore.GREEN}Legendas PT-BR salvas em: {pasta_saida}")
    print(f"{Fore.CYAN}Relatório salvo em: {ARQUIVO_INFO}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        executar_pipeline_lote()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[AVISO] Operação cancelada pelo operador (Ctrl+C).")
        sys.exit(0)
