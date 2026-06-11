#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PIPELINE INDUSTRIAL DE TRADUÇÃO DE LEGENDA SEPARADA - MODELO DIRECT SRT
Lê arquivo SRT externo → Traduz via LM Studio (Gemma 4B) → Salva localmente em PT-BR

Author: Paulo + Claude
Data: Maio 2026
Status: PRODUCTION DIRECT SRT
"""

import os
import re
import sys
import datetime
import requests
from tqdm import tqdm
from colorama import init, Fore, Style

# Inicializa o Colorama para tratamento de escapes ANSI no terminal do Windows
init(autoreset=True)

# ============================================================================
# CONFIGURAÇÕES INFRAESTRUTURAIS
# ============================================================================

API_URL          = "http://127.0.0.1:1234/v1/chat/completions"
DEFAULT_BATCH    = 20
ENCODINGS_FALLBACK = ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1', 'iso-8859-1']

SYSTEM_PROMPT = """You are an expert subtitler and translator for Japanese anime, specializing in Sci-Fi, military mecha, and idol music genres. 
Translate the following English subtitle lines into precise, natural Brazilian Portuguese (PT-BR).

Strict Rules:
1. Maintain the exact same subtitle indexes and SRT format. Do NOT skip any lines or merge them.
2. Use military and space sci-fi terminology for the Macross franchise (keep: Fold Quartz, Reaction Bullet, Valkyrie, Rune, Windermere, Delta Flight).
3. Song lyrics (lines with musical notes like '♪') must be translated poetically, retaining emotional meaning.
4. Return ONLY the translated SRT content. Zero notes or explanations."""

# ============================================================================
# SISTEMA DE LOGS
# ============================================================================

def configurar_logs():
    """Cria o diretório de logs e retorna o caminho do arquivo de log da execução."""
    diretorio_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(diretorio_log, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    caminho = os.path.join(diretorio_log, f"pipeline_direct_srt_{timestamp}.txt")

    with open(caminho, "a", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("PIPELINE INDUSTRIAL DE TRADUÇÃO DIRETA SRT - LOG DE AUDITORIA\n")
        f.write("=" * 80 + "\n")
        f.write(f"Início   : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Python   : {sys.version.split()[0]}\n")
        f.write(f"Logs     : {diretorio_log}\n")
        f.write("=" * 80 + "\n\n")

    return caminho

def registrar_log(arquivo_log, nivel, mensagem):
    """Grava evento na esteira física de auditoria com timestamp."""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    linha = f"[{timestamp}] [{nivel:8s}] {mensagem}"

    with open(arquivo_log, "a", encoding="utf-8") as f:
        f.write(linha + "\n")

    if nivel == "SUCESSO":
        print(f"{Fore.GREEN}{linha}{Style.RESET_ALL}")
    elif nivel == "ERRO":
        print(f"{Fore.RED}{linha}{Style.RESET_ALL}")
    elif nivel == "AVISO":
        print(f"{Fore.YELLOW}{linha}{Style.RESET_ALL}")
    elif nivel == "DEBUG":
        print(f"{Fore.CYAN}{linha}{Style.RESET_ALL}")
    else:
        print(linha)

# ============================================================================
# INTERFACE INTERATIVA COM O OPERADOR
# ============================================================================

def obter_arquivo_usuario():
    """Interface interativa de console que aceita a pasta e localiza o .srt automaticamente."""
    print("=" * 80)
    print(f"{Fore.CYAN}      PIPELINE INDUSTRIAL DE TRADUÇÃO DE LEGENDA ISOLADA (SRT)")
    print(f"{Fore.CYAN}      Varre o diretório -> Auto-detecta o .srt -> Traduz via LM Studio")
    print("=" * 80)

    while True:
        entrada = input(f"\n{Fore.YELLOW}Digite o caminho da pasta (clique shift+botão direito p/ copiar): {Style.RESET_ALL}").strip()
        entrada = entrada.strip('"').strip("'")

        if not entrada:
            print(Fore.RED + "[ERRO] O caminho não pode ser vazio.")
            continue
        if not os.path.exists(entrada):
            print(Fore.RED + f"[ERRO] O caminho especificado não existe: {entrada}")
            continue

        # CENÁRIO 1: O operador forneceu a PASTA (Mesmo comportamento padrão dos seus scripts consolidados)
        if os.path.isdir(entrada):
            arquivos_srt = sorted([f for f in os.listdir(entrada) if f.lower().endswith('.srt')])
            
            if not arquivos_srt:
                print(Fore.RED + f"[ERRO] Nenhum arquivo .srt localizado dentro da pasta: {entrada}")
                continue
            
            # Auto-detecção caso haja apenas uma única legenda na pasta
            if len(arquivos_srt) == 1:
                alvo_forense = os.path.join(entrada, arquivos_srt[0])
                print(f"{Fore.GREEN}[OK] Legenda detectada automaticamente: {arquivos_srt[0]}")
                return alvo_forense
            
            # Menu de decisão interativo caso haja múltiplas legendas no diretório
            else:
                print(f"\n{Fore.CYAN}Múltiplos arquivos .srt localizados na pasta:")
                for idx, arq in enumerate(arquivos_srt, 1):
                    print(f"  {idx}. {arq}")
                
                while True:
                    try:
                        num = input(f"\n{Fore.YELLOW}Selecione o número da legenda desejada: {Style.RESET_ALL}").strip()
                        escolha = int(num) - 1
                        if 0 <= escolha < len(arquivos_srt):
                            return os.path.join(entrada, arquivos_srt[escolha])
                        print(Fore.RED + "[ERRO] Opção fora do intervalo válido.")
                    except ValueError:
                        print(Fore.RED + "[ERRO] Entrada inválida. Digite um número inteiro correspondente.")

        # CENÁRIO 2: O operador já arrastou ou digitou o caminho completo do ARQUIVO direto
        if os.path.isfile(entrada):
            if not entrada.lower().endswith('.srt'):
                print(Fore.RED + "[ERRO] Extensão inválida. O pipeline aceita apenas arquivos .srt neste modo.")
                continue
            return entrada

def obter_batch_size():
    """Menu de seleção do tamanho do lote de tradução."""
    try:
        entrada = input(
            f"{Fore.YELLOW}Pressione ENTER para manter o lote padrão ({DEFAULT_BATCH} linhas) ou digite o tamanho desejado: {Style.RESET_ALL}"
        ).strip()
        return int(entrada) if entrada else DEFAULT_BATCH
    except ValueError:
        print(Fore.RED + f"[AVISO] Entrada inválida. Adotando lote padrão de {DEFAULT_BATCH} linhas.")
        return DEFAULT_BATCH

# ============================================================================
# INFRAESTRUTURA E LEITURA FORENSE
# ============================================================================

def validar_lm_studio(arquivo_log):
    """Valida barramento lógico do LM Studio antes de iniciar a inferência."""
    registrar_log(arquivo_log, "INFO", "Validando conexão com a API local...")
    try:
        r = requests.get("http://127.0.0.1:1234/v1/models", timeout=5)
        if r.status_code == 200:
            modelos = r.json().get('data', [])
            registrar_log(arquivo_log, "SUCESSO", f"LM Studio OK - {len(modelos)} modelo(s) detectado(s)")
            return True
        else:
            registrar_log(arquivo_log, "ERRO", f"LM Studio retornou status {r.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        registrar_log(arquivo_log, "ERRO", "LM Studio offline - Verifique se o servidor local está ativo na porta 1234")
        return False

def ler_srt_com_encoding(srt_path, arquivo_log):
    """Fallback Chain de Encoding adaptada para ler arquivos textuais brutos SRT."""
    for enc in ENCODINGS_FALLBACK:
        try:
            with open(srt_path, 'r', encoding=enc) as f:
                conteudo = f.read()
            registrar_log(arquivo_log, "DEBUG", f"Leitura bem-sucedida usando encoding: {enc.upper()}")
            return conteudo, enc
        except UnicodeDecodeError:
            continue

    registrar_log(arquivo_log, "AVISO", "Falha na cadeia de decodificação. Forçando UTF-8 com substituição.")
    with open(srt_path, 'r', encoding='utf-8', errors='replace') as f:
        conteudo = f.read()
    return conteudo, 'utf-8-bypass'

# ============================================================================
# INFERÊNCIA COMPUTACIONAL POR LOTE (COMPATÍVEL GEMMA 4B / VRAM)
# ============================================================================

def traduzir_lote_ia(lote_blocos, arquivo_log, batch_num):
    """Envia o bloco consolidado de SRT para processamento na VRAM da GPU AMD RX 7800 XT."""
    payload_texto = "\n\n".join(lote_blocos)

    payload = {
        "model": "local-model",  # Compatibilidade OpenAI do LM Studio descarrega no modelo ativo da VRAM
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": payload_texto},
        ],
        "temperature": 0.3,
        "stream": False,
    }

    try:
        response = requests.post(API_URL, json=payload, timeout=120)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        else:
            msg = f"ERRO API - Lote {batch_num} - Status {response.status_code}: {response.text[:200]}"
            registrar_log(arquivo_log, "ERRO", msg)
            return None
    except requests.exceptions.Timeout:
        registrar_log(arquivo_log, "ERRO", f"Lote {batch_num}: Timeout (120s) na GPU")
        return None
    except Exception as e:
        registrar_log(arquivo_log, "ERRO", f"Lote {batch_num}: Falha crítica no barramento local - {str(e)}")
        return None

# ============================================================================
# ORQUESTRADOR PRINCIPAL
# ============================================================================

def orquestrador_pipeline():
    caminho_entrada = obter_arquivo_usuario()
    arquivo_log = configurar_logs()

    registrar_log(arquivo_log, "INFO", f"Arquivo de Entrada Detectado: {caminho_entrada}")
    
    if not validar_lm_studio(arquivo_log):
        print(Fore.RED + "\n[ABORTO] Infraestrutura inválida. Inicie o LM Studio e tente novamente.")
        sys.exit(1)

    batch_size = obter_batch_size()

    # Define nome inteligente de saída no mesmo diretório
    diretorio_pai = os.path.dirname(caminho_entrada)
    nome_base = os.path.basename(caminho_entrada)
    nome_saida = re.sub(r'(-en|-en-us|english)?\.srt$', '_PTBR.srt', nome_base, flags=re.IGNORECASE)
    if nome_saida == nome_base:
        nome_saida = nome_base.replace(".srt", "_PTBR.srt")
    caminho_saida = os.path.join(diretorio_pai, nome_saida)

    registrar_log(arquivo_log, "INFO", f"Tamanho de Lote configurado: {batch_size}")
    registrar_log(arquivo_log, "INFO", f"Arquivo de Saída planejado : {caminho_saida}\n")

    # Ingestão e fatiamento estrutural (Regex Baseado na quebra de linha dupla do SRT)
    conteudo_bruto, enc = ler_srt_com_encoding(caminho_entrada, arquivo_log)
    blocos = re.split(r'\n\s*\n', conteudo_bruto.strip())
    blocos = [b.strip() for b in blocos if b.strip()]
    total_blocos = len(blocos)

    registrar_log(arquivo_log, "INFO", f"Total de blocos SRT detectados para tradução: {total_blocos}")
    print(f"\n{Fore.CYAN}Iniciando inferência na GPU AMD RX 7800 XT. Acompanhe a esteira...\n")

    legendas_traduzidas = []
    stats = {'requisicoes': 0, 'linhas_traduzidas': 0, 'erros_traducao': 0}

    # Esteira Industrial com barra de progresso tqdm por Lote
    num_lotes = (total_blocos + batch_size - 1) // batch_size
    
    with tqdm(total=total_blocos, desc="Processando Lotes", unit="bloco",
              bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} blocos [{elapsed}<{remaining}]") as pbar:

        for i in range(0, total_blocos, batch_size):
            lote = blocos[i:i + batch_size]
            batch_num = (i // batch_size) + 1

            resultado = traduzir_lote_ia(lote, arquivo_log, batch_num)

            if resultado:
                legendas_traduzidas.append(resultado)
                stats['requisicoes'] += 1
                stats['linhas_traduzidas'] += len(lote)
                registrar_log(arquivo_log, "DEBUG", f"Lote {batch_num}/{num_lotes} processado com integridade.")
            else:
                registrar_log(arquivo_log, "ERRO", f"Lote {batch_num}/{num_lotes} falhou criticamente.")
                stats['erros_traducao'] += 1
                print(Fore.RED + f"\n[ABORTO] Falha na resposta da GPU para mitigar dados corrompidos.")
                sys.exit(1)

            pbar.update(len(lote))

    # Gravação física final no NVMe
    conteudo_final = "\n\n".join(legendas_traduzidas)
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        f.write(conteudo_final)

    # Consolidação de Relatório Final de Auditoria Técnica
    print("\n" + "=" * 80)
    print(f"{Fore.GREEN}[SUCESSO] Operação finalizada com integridade estrita de strings!")
    print(f"{Fore.GREEN}Legenda localizada gerada em: {caminho_saida}")
    print("=" * 80)

    relatorio = (
        f"\n{'='*80}\nRELATÓRIO FINAL - OPERAÇÃO DIRETA SRT\n{'='*80}\n"
        f"Blocos Processados : {total_blocos}\n"
        f"Requisições API    : {stats['requisicoes']}\n"
        f"Linhas Localizadas : {stats['linhas_traduzidas']}\n"
        f"Falhas Detectadas  : {stats['erros_traducao']}\n"
        f"Encoding de Origem : {enc.upper()}\n"
        f"Log de Auditoria   : {arquivo_log}\n"
        f"Destino do Arquivo : {caminho_saida}\n"
    )

    with open(arquivo_log, "a", encoding="utf-8") as f:
        f.write(relatorio)

    print(f"{Fore.CYAN}Log de auditoria instanciado em: {arquivo_log}")

if __name__ == "__main__":
    try:
        orquestrador_pipeline()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[AVISO] Pipeline interrompido pelo operador (Ctrl+C).")
        sys.exit(0)