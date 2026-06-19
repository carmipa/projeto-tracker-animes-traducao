#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: batch_translator_ass.py (Batch Mode v4 - ASS Translation Edition)
Otimizado para RTX 5600 8GB VRAM (LM Studio com 2 concorrências max / max precision).
Traduz em lotes usando threads em paralelo para velocidade máxima sem perda de tags ASS.

Author: Paulo + Antigravity
Data: Junho 2026
"""

import os
import re
import sys
import time
import logging
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from colorama import init, Fore, Style

init(autoreset=True)

LARANJA_LM_OFFLINE = "\033[38;5;208m"  # ANSI 256 cores (via colorama) - destaca quedas do LM Studio das demais mensagens

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
LM_STUDIO_MODELS_URL = "http://localhost:1234/v1/models"
MAX_THREADS = 2   # Coincide com as 2 concorrências máximas configuradas no LM Studio para a GPU de 8GB
BATCH_SIZE = 8    # Linhas por chamada para evitar estouro de tokens e truncamento de respostas
MODELO_ATIVO = "local-model"

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_INFO = None   # Definido dentro da pasta de saída em executar_pipeline_lote()
DEBUG_FILE = None     # Definido dentro da pasta de saída em executar_pipeline_lote()
_debug_salvo = False

logger = logging.getLogger("ass_translator")
logger.setLevel(logging.DEBUG)


def _configurar_logger(pasta_saida, timestamp_execucao):
    """Liga um FileHandler dentro da pasta de saída para registrar, com detalhe, cada
    chamada à API (erros HTTP, quedas de conexão, tokens/s, fallbacks). Não duplica no console."""
    caminho_log = os.path.join(pasta_saida, f"log_traducao_ass_{timestamp_execucao}.log")
    handler = logging.FileHandler(caminho_log, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False
    return caminho_log

SYSTEM_PROMPT = (
    "Você é um tradutor especialista em animes de ficção científica, robôs gigantes (mechas) e aventura espacial.\n"
    "Sua tarefa é traduzir as linhas de legendas numeradas enviadas do inglês para o português do Brasil (PT-BR) de forma fluida e natural.\n"
    "REGRAS CRÍTICAS:\n"
    "1. Mantenha a coerência terminológica de Gundam (ex: 'Photon Battery' -> 'Bateria de Fótons', 'Regild Century' -> 'Século Regild', 'Capital Territory' -> 'Território da Capital', 'Capital Guard' -> 'Guarda da Capital'). Nomes de robôs mechas/Mobile Suits devem permanecer em inglês (ex: G-Self, G-Arcane, G-Lucifer).\n"
    "2. Traduza gírias e expressões militares de forma natural (ex: 'Roger' -> 'Copiado', 'Copy that' -> 'Entendido').\n"
    "3. Nunca modifique ou remova marcadores de formatação como '[T0]', '[T1]', '[T2]'... Eles representam tags da legenda e devem retornar EXATAMENTE na mesma posição e formato no texto traduzido.\n"
    "4. Retorne APENAS as traduções numeradas no mesmo formato (ex: '1. tradução'). Não inclua notas, explicações ou saudações."
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
                # Filtra e escolhe o primeiro modelo de chat
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
    texto = re.sub(r'\*+', '', texto)
    texto = re.sub(r'_+', '', texto)
    return texto.strip().strip('"').strip("'")


def _parsear_resposta_numerada(conteudo, n_esperado):
    linhas = []
    for linha in conteudo.split('\n'):
        m = re.match(r'^\d+(?:\.|\)| -|:)\s*(.+)', linha.strip())
        if m:
            linhas.append(_limpar_markdown(m.group(1)))
    if len(linhas) >= n_esperado:
        return linhas[:n_esperado]
    
    linhas_raw = [
        _limpar_markdown(l)
        for l in conteudo.split('\n')
        if l.strip() and not re.match(r'^(here|sure|translation|below|ok|claro|aqui|esta |segue|abaixo)', l.strip(), re.I)
    ]
    return list(dict.fromkeys(linhas_raw))[:n_esperado]  # Remove duplicatas consecutivas e corta no esperado


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


def traduzir_bloco_ia(bloco, nome_arquivo="?"):
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
            {"role": "user", "content": f"Traduza estas {len(textos_u)} linhas para PT-BR. Retorne APENAS as traduções numeradas:\n{texto_numerado}"}
        ],
        "temperature": 0.1,
        "max_tokens": 800
    }

    max_tentativas = 3
    tentativa = 0
    tentativas_offline = 0
    max_tentativas_offline = 4  # LM Studio caído pode levar bem mais que 15s para religar o modelo na VRAM

    while tentativa < max_tentativas:
        try:
            t_inicio = time.perf_counter()
            resposta = requests.post(LM_STUDIO_URL, json=payload, timeout=120)
            elapsed = time.perf_counter() - t_inicio
            if resposta.status_code != 200:
                logger.error(f"[{nome_arquivo}] Bloco {indices_u[0]}-{indices_u[-1]} | HTTP {resposta.status_code} em {elapsed:.1f}s | corpo: {resposta.text[:300]}")
                tentativa += 1
                if tentativa < max_tentativas:
                    tempo_espera = tentativa * 5
                    print(f"\n{Fore.YELLOW}[AVISO] Erro HTTP {resposta.status_code} no bloco {indices_u[0]}-{indices_u[-1]}. Tentativa {tentativa}/{max_tentativas}. Aguardando {tempo_espera}s...")
                    time.sleep(tempo_espera)
                    continue
                else:
                    _salvar_debug(texto_numerado, f"HTTP {resposta.status_code}\n{resposta.text}", [])
                    raise Exception(f"HTTP {resposta.status_code} - {resposta.text[:200]}")

            dados_resposta = resposta.json()
            conteudo = dados_resposta['choices'][0]['message']['content'].strip()
            traducoes = _parsear_resposta_numerada(conteudo, len(textos_u))

            usage = dados_resposta.get('usage', {})
            tokens_resp = usage.get('completion_tokens')
            tok_s = f"{tokens_resp / elapsed:.1f} tok/s" if tokens_resp and elapsed > 0 else "N/D"
            logger.info(f"[{nome_arquivo}] Bloco {indices_u[0]}-{indices_u[-1]} | {len(textos_u)} linhas | {elapsed:.1f}s | {tokens_resp or '?'} tokens | {tok_s} | tentativa {tentativa + 1}")

            if len(traducoes) < len(textos_u):
                logger.warning(f"[{nome_arquivo}] Bloco {indices_u[0]}-{indices_u[-1]} | resposta incompleta: {len(traducoes)}/{len(textos_u)} linhas parseadas | conteúdo bruto: {conteudo[:300]!r}")
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
                    # Recoloca as tags nos marcadores correspondentes [T0], [T1]...
                    for idx_tag, tag in enumerate(tags):
                        marcador = f"[T{idx_tag}]"
                        if marcador in trad:
                            trad = trad.replace(marcador, tag, 1)
                        else:
                            # Fallback tolerante a grafias alteradas pela IA
                            trad = re.sub(rf'\[?[Tt]{idx_tag}\]?', tag, trad, count=1)
                    resultados.append((idx, f"{meta}{trad}\n", False))
                else:
                    # Se falhou ou retornou o mesmo texto, aplica tag de erro para auditoria
                    resultados.append((idx, f"{meta}[ERRO_TRADUCAO: {texto_orig}]\n", True))
            return resultados

        except requests.exceptions.ConnectionError as e:
            # Causa real observada em debug_last_failure: o processo do LM Studio caiu/recarregou
            # o modelo (estouro de VRAM ou reinício manual) e a porta para de responder por um tempo.
            # Isso NÃO é um erro HTTP 400 - a conexão é recusada no nível de socket. Por isso usamos
            # um backoff bem maior aqui do que nos outros erros: religar o modelo na GPU pode levar
            # bem mais que os 5-15s do backoff padrão.
            tentativas_offline += 1
            if tentativas_offline < max_tentativas_offline:
                tempo_espera = tentativas_offline * 20
                logger.error(f"[{nome_arquivo}] Bloco {indices_u[0]}-{indices_u[-1]} | LM Studio OFFLINE (conexão recusada) | tentativa offline {tentativas_offline}/{max_tentativas_offline} | aguardando {tempo_espera}s")
                print(f"\n{LARANJA_LM_OFFLINE}[LM STUDIO OFFLINE] Conexão recusada no bloco {indices_u[0]}-{indices_u[-1]}. O servidor pode estar reiniciando/recarregando o modelo na VRAM. Tentativa {tentativas_offline}/{max_tentativas_offline}. Aguardando {tempo_espera}s...")
                time.sleep(tempo_espera)
            else:
                logger.error(f"[{nome_arquivo}] Bloco {indices_u[0]}-{indices_u[-1]} | LM Studio permaneceu OFFLINE após {max_tentativas_offline} tentativas | {e}")
                print(f"\n{Fore.RED}[FALHA] LM Studio não voltou a responder no bloco {indices_u[0]}-{indices_u[-1]} após {max_tentativas_offline} tentativas: {e}")
                _salvar_debug(texto_numerado, str(e), [])
                resultados = list(resultados_vazios.values())
                for idx, meta, texto, _ in zip(indices_u, metadados_u, textos_u, tags_u):
                    resultados.append((idx, f"{meta}[ERRO_TRADUCAO: {texto}]\n", True))
                return resultados

        except Exception as e:
            tentativa += 1
            logger.error(f"[{nome_arquivo}] Bloco {indices_u[0]}-{indices_u[-1]} | exceção: {e!r} | tentativa {tentativa}/{max_tentativas}")
            if tentativa < max_tentativas:
                tempo_espera = tentativa * 5
                print(f"\n{Fore.YELLOW}[AVISO] Exceção no bloco {indices_u[0]}-{indices_u[-1]}: {e}. Tentativa {tentativa}/{max_tentativas}. Aguardando {tempo_espera}s...")
                time.sleep(tempo_espera)
            else:
                print(f"\n{Fore.RED}[FALHA] Bloco idx {indices_u[0]}-{indices_u[-1]} falhou definitivamente após {max_tentativas} tentativas: {e}")
                _salvar_debug(texto_numerado, str(e), [])
                resultados = list(resultados_vazios.values())
                for idx, meta, texto, _ in zip(indices_u, metadados_u, textos_u, tags_u):
                    resultados.append((idx, f"{meta}[ERRO_TRADUCAO: {texto}]\n", True))
                return resultados


def executar_pipeline_lote():
    print("=" * 80)
    print(f"{Fore.CYAN}    ESTEIRA BATCH {BATCH_SIZE}L/CHAMADA | THREADS={MAX_THREADS} | ASS -> ASS PTBR (GUNDAM EDITION)")
    print("=" * 80)

    verificar_lm_studio()

    caminho_padrao_origem = r"D:\PROJETOS-OPEN\animes\reconquista\reconsquista-1"
    pasta_origem = obter_diretorio_operador("Pasta com legendas ENG (.ass)", caminho_padrao_origem)

    caminho_padrao_saida = r"D:\PROJETOS-OPEN\animes\reconquista\reconsquista-1\traducao"
    pasta_saida = obter_diretorio_operador("Pasta de saída PT-BR", caminho_padrao_saida)

    os.makedirs(pasta_saida, exist_ok=True)
    arquivos_ass = sorted([f for f in os.listdir(pasta_origem) if f.lower().endswith('.ass')])

    if not arquivos_ass:
        print(f"{Fore.RED}[ERRO] Nenhum .ass em: {pasta_origem}")
        return

    global ARQUIVO_INFO, DEBUG_FILE
    timestamp_execucao = datetime.now().strftime('%Y%m%d_%H%M%S')
    ARQUIVO_INFO = os.path.join(pasta_saida, "info_traducao_ass.txt")
    DEBUG_FILE = os.path.join(pasta_saida, "debug_last_failure_ass.txt")
    caminho_log = _configurar_logger(pasta_saida, timestamp_execucao)
    logger.info(f"=== INÍCIO DA EXECUÇÃO | modelo={MODELO_ATIVO} | batch={BATCH_SIZE} | threads={MAX_THREADS} | origem={pasta_origem} | saida={pasta_saida} ===")

    print(f"{Fore.GREEN}[OK] {len(arquivos_ass)} arquivos carregados | batch={BATCH_SIZE} | threads={MAX_THREADS}")
    print(f"{Fore.CYAN}[LOG] Detalhes de cada chamada (erros, quedas de conexão, tokens/s) em: {caminho_log}")

    linhas_relatorio = [
        "RELATÓRIO DE TRADUÇÃO BATCH - BATCH TRANSLATOR ASS",
        f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Batch size: {BATCH_SIZE} linhas/chamada | Threads: {MAX_THREADS}",
        "=" * 80,
    ]
    total_fallbacks_geral = 0
    total_dialogos_geral = 0
    t_execucao_inicio = time.perf_counter()

    with tqdm(total=len(arquivos_ass), desc="Série Completa", unit="arq", colour="green", ncols=80, position=0) as barra_macro:
        for idx, arquivo in enumerate(arquivos_ass):
            caminho_entrada = os.path.join(pasta_origem, arquivo)
            nome_saida_ptbr = arquivo.replace("_ENG.ass", "_PTBR.ass")
            caminho_saida = os.path.join(pasta_saida, nome_saida_ptbr)

            barra_macro.set_postfix_str(arquivo[:35])
            tqdm.write(f"\n{Fore.YELLOW}[{idx+1}/{len(arquivos_ass)}] -> {arquivo}")

            with open(caminho_entrada, 'r', encoding='utf-8', errors='replace') as f:
                linhas_originais = f.readlines()

            mapa_linhas_finais = [None] * len(linhas_originais)
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
                        # Ignora linhas com excesso de tags (karaokê/efeitos complexos) para evitar estouro de tokens
                        if len(tags) > 8:
                            mapa_linhas_finais[i] = linha
                            continue
                        # Substitui cada tag por um marcador numérico seguro [T0], [T1]...
                        texto_limpo = texto_bruto
                        for idx_tag, tag in enumerate(tags):
                            texto_limpo = texto_limpo.replace(tag, f"[T{idx_tag}]", 1)
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
            tqdm.write(f"  {Fore.CYAN}Diálogos: {total_dialogos} | Chamadas API: {total_chamadas} (redução {total_dialogos//max(total_chamadas,1)}x)")
            t_episodio_inicio = time.perf_counter()

            with tqdm(total=total_chamadas, desc=f"  Ep {idx+1:02d} batches", unit="bat", colour="cyan", ncols=80, position=1, leave=False) as barra_micro:
                with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                    futuros = {executor.submit(traduzir_bloco_ia, bloco, arquivo): bloco for bloco in blocos}
                    for futuro in as_completed(futuros):
                        for orig_idx, linha_proc, usou_fallback in futuro.result():
                            mapa_linhas_finais[orig_idx] = linha_proc
                            if usou_fallback:
                                fallbacks_arquivo += 1
                        barra_micro.update(1)

            with open(caminho_saida, 'w', encoding='utf-8') as f:
                f.writelines(l for l in mapa_linhas_finais if l is not None)

            elapsed_episodio = time.perf_counter() - t_episodio_inicio
            tqdm.write(f"{Fore.GREEN}  [SALVO] {nome_saida_ptbr} | Chamadas: {total_chamadas} | Fallbacks: {fallbacks_arquivo} | Tempo: {elapsed_episodio:.1f}s")
            logger.info(f"[{arquivo}] concluído | diálogos={total_dialogos} | chamadas={total_chamadas} | fallbacks={fallbacks_arquivo} ({fallbacks_arquivo/max(total_dialogos,1)*100:.1f}%) | tempo={elapsed_episodio:.1f}s")
            linhas_relatorio.append(
                f"{nome_saida_ptbr} | Diálogos: {total_dialogos} | Chamadas: {total_chamadas} | Fallbacks: {fallbacks_arquivo} | Tempo: {elapsed_episodio:.1f}s"
            )
            total_fallbacks_geral += fallbacks_arquivo
            total_dialogos_geral += total_dialogos
            barra_macro.update(1)

    elapsed_total = time.perf_counter() - t_execucao_inicio
    linhas_relatorio.append("=" * 80)
    linhas_relatorio.append(
        f"TOTAL: {len(arquivos_ass)} arquivos | {total_dialogos_geral} diálogos | {total_fallbacks_geral} fallbacks | Tempo total: {elapsed_total/60:.1f}min"
    )

    with open(ARQUIVO_INFO, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_relatorio) + "\n")

    logger.info(f"=== FIM DA EXECUÇÃO | {len(arquivos_ass)} arquivos | {total_dialogos_geral} diálogos | {total_fallbacks_geral} fallbacks | {elapsed_total/60:.1f}min ===")

    print("\n" + "=" * 80)
    print(f"{Fore.GREEN}[SUCESSO] Pipeline batch concluído em {elapsed_total/60:.1f}min!")
    print(f"{Fore.GREEN}Legendas PT-BR em: {pasta_saida}")
    print(f"{Fore.CYAN}Relatório: {ARQUIVO_INFO}")
    print(f"{Fore.CYAN}Log detalhado: {caminho_log}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        executar_pipeline_lote()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[AVISO] Interrompido pelo operador (Ctrl+C).")
        sys.exit(0)
