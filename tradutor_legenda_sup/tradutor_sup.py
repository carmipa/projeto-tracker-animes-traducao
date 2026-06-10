#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: tradutor_sup.py
Esteira industrial completa:
1. Realiza OCR em arquivos de legenda PGS (.sup) usando o Subtitle Edit (CLI)
2. Lê o arquivo SRT gerado pelo OCR
3. Traduz via IA local (LM Studio / Gemma 4B) em lotes
4. Salva a legenda final traduzida em PT-BR (.srt)
"""

import os
import sys
import re
import json
import time
import subprocess
import datetime
import shutil
import traceback
import requests

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    print("ERRO: colorama não instalado. Instale com: pip install colorama")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    print("ERRO: tqdm não instalado. Instale com: pip install tqdm")
    sys.exit(1)

if sys.platform == "win32":
    import winreg


def achar_subtitle_edit():
    """
    Tenta localizar o executável do Subtitle Edit no sistema.
    """
    caminho = shutil.which("SubtitleEdit")
    if caminho and os.path.exists(caminho):
        return caminho

    if sys.platform == "win32":
        for hkey in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                caminho_registro = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\SubtitleEdit.exe"
                with winreg.OpenKey(hkey, caminho_registro) as key:
                    val, _ = winreg.QueryValueEx(key, "")
                    if val and os.path.exists(val):
                        return val
            except WindowsError:
                pass

    caminhos_padrao = [
        r"C:\Program Files\Subtitle Edit\SubtitleEdit.exe",
        r"C:\Program Files (x86)\Subtitle Edit\SubtitleEdit.exe",
        r"C:\ProgramData\chocolatey\bin\SubtitleEdit.exe",
    ]
    for caminho in caminhos_padrao:
        if os.path.exists(caminho):
            return caminho

    return None


class GerenciadorLogs:
    """
    Sistema de log estruturado para a esteira de OCR e Tradução de legendas SUP.
    """
    def __init__(self):
        self.pasta_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(self.pasta_log, exist_ok=True)
        
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.caminho_log = os.path.join(self.pasta_log, f"pipeline_sup_ocr_trad_{self.timestamp}.log")
        self.f_log = open(self.caminho_log, 'w', encoding='utf-8')
        
        header = (
            f"{'='*80}\n"
            f"ESTEIRA SUP (OCR + TRADUÇÃO) - INICIALIZADA EM {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"{'='*80}\n\n"
        )
        self.f_log.write(header)
        self.f_log.flush()

    def _escrever(self, nivel, mensagem, cor_terminal=None):
        ts = datetime.datetime.now().strftime('%H:%M:%S')
        linha = f"[{ts}] [{nivel:6s}] {mensagem}"
        self.f_log.write(linha + "\n")
        self.f_log.flush()
        if cor_terminal:
            tqdm.write(f"{cor_terminal}{linha}{Style.RESET_ALL}")
        else:
            tqdm.write(linha)

    def info(self, msg): self._escrever("INFO", msg, Fore.WHITE)
    def sucesso(self, msg): self._escrever("OK", msg, Fore.GREEN + Style.BRIGHT)
    def aviso(self, msg): self._escrever("AVISO", msg, Fore.YELLOW)
    def erro(self, msg): self._escrever("ERRO", msg, Fore.RED + Style.BRIGHT)
    def debug(self, msg): self._escrever("DEBUG", msg, Fore.CYAN)

    def fechar(self, resumo):
        self.f_log.write(f"\n\n{'='*80}\n{resumo}\n{'='*80}\n")
        self.f_log.close()


API_URL = "http://127.0.0.1:1234/v1/chat/completions"
DEFAULT_BATCH = 20
ENCODINGS_FALLBACK = ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1', 'iso-8859-1']

SYSTEM_PROMPT = """You are an expert subtitler and translator for Japanese anime, specializing in Sci-Fi, military mecha, and idol music genres. 
Translate the following English subtitle lines into precise, natural Brazilian Portuguese (PT-BR).

Strict Rules:
1. Maintain the exact same subtitle indexes and SRT format. Do NOT skip any lines or merge them.
2. Use military and space sci-fi terminology for the Macross franchise (keep: Fold Quartz, Reaction Bullet, Valkyrie, Rune, Windermere, Delta Flight).
3. Song lyrics (lines with musical notes like '♪') must be translated poetically, retaining emotional meaning.
4. Return ONLY the translated SRT content. Zero notes or explanations."""


def validar_lm_studio(logger):
    logger.info("Validando conexão com o LM Studio...")
    try:
        r = requests.get("http://127.0.0.1:1234/v1/models", timeout=5)
        if r.status_code == 200:
            modelos = r.json().get('data', [])
            logger.sucesso(f"LM Studio OK - {len(modelos)} modelo(s) detectado(s)")
            return True
        logger.erro(f"LM Studio retornou código {r.status_code}")
        return False
    except requests.exceptions.ConnectionError:
        logger.erro("LM Studio offline - Certifique-se de que o servidor local está rodando na porta 1234")
        return False


def executar_ocr(caminho_sup, se_path, logger):
    """
    Chama o Subtitle Edit para fazer o OCR do arquivo SUP para SRT.
    Retorna o caminho do arquivo SRT gerado ou None.
    """
    logger.info(f"Iniciando OCR do arquivo SUP: {os.path.basename(caminho_sup)}")
    
    caminho_srt = caminho_sup.replace(".sup", ".srt").replace(".SUP", ".srt")
    
    if os.path.exists(caminho_srt):
        try:
            os.remove(caminho_srt)
        except Exception as e:
            logger.aviso(f"Não foi possível remover o SRT antigo: {e}")
            
    cmd = [se_path, "/convert", caminho_sup, "srt"]
    
    try:
        logger.info("Executando o OCR pelo Subtitle Edit. Isso pode levar de 1 a 5 minutos dependendo da duração do vídeo...")
        resultado = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        if os.path.exists(caminho_srt) and os.path.getsize(caminho_srt) > 0:
            logger.sucesso(f"OCR concluído com sucesso! Gerado: {os.path.basename(caminho_srt)}")
            return caminho_srt
        else:
            logger.erro("O arquivo SRT de saída não foi gerado pelo OCR.")
            if resultado.stderr:
                logger.erro(f"Detalhes do erro: {resultado.stderr.strip()}")
            return None
    except Exception as e:
        logger.erro(f"Falha ao rodar o Subtitle Edit: {e}")
        return None


def ler_srt_com_encoding(srt_path, logger):
    for enc in ENCODINGS_FALLBACK:
        try:
            with open(srt_path, 'r', encoding=enc) as f:
                conteudo = f.read()
            logger.debug(f"Leitura de SRT bem-sucedida usando encoding: {enc.upper()}")
            return conteudo, enc
        except UnicodeDecodeError:
            continue

    logger.aviso("Falha na cadeia de decodificação. Forçando UTF-8 com substituição.")
    with open(srt_path, 'r', encoding='utf-8', errors='replace') as f:
        conteudo = f.read()
    return conteudo, 'utf-8-bypass'


def traduzir_lote_ia(lote_blocos, logger, batch_num):
    payload_texto = "\n\n".join(lote_blocos)
    payload = {
        "model": "local-model",
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
        logger.erro(f"Erro API - Lote {batch_num} - Status {response.status_code}: {response.text[:200]}")
        return None
    except requests.exceptions.Timeout:
        logger.erro(f"Lote {batch_num}: Timeout (120s) no LM Studio")
        return None
    except Exception as e:
        logger.erro(f"Lote {batch_num}: Falha de conexão - {e}")
        return None


def traduzir_arquivo_srt(caminho_srt, logger):
    """
    Lê a legenda SRT, envia os blocos em lotes para tradução e grava o resultado final.
    """
    logger.info(f"Traduzindo arquivo SRT: {os.path.basename(caminho_srt)}")
    
    # Se o arquivo terminar com _Track3_eng.srt ou similar, remove o sufixo de idioma
    caminho_saida = re.sub(r'(_Track\d+)?_(eng|english)\.srt$', '_PTBR.srt', caminho_srt, flags=re.IGNORECASE)
    if caminho_saida == caminho_srt:
        caminho_saida = caminho_srt.replace(".srt", "_PTBR.srt")
        
    conteudo_bruto, enc = ler_srt_com_encoding(caminho_srt, logger)
    blocos = re.split(r'\n\s*\n', conteudo_bruto.strip())
    blocos = [b.strip() for b in blocos if b.strip()]
    total_blocos = len(blocos)

    logger.info(f"Total de blocos detectados para tradução: {total_blocos}")
    
    legendas_traduzidas = []
    stats = {'requisicoes': 0, 'linhas_traduzidas': 0, 'erros_traducao': 0}

    num_lotes = (total_blocos + DEFAULT_BATCH - 1) // DEFAULT_BATCH
    
    with tqdm(total=total_blocos, desc="Traduzindo Lotes", unit="bloco",
              bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} blocos [{elapsed}<{remaining}]") as pbar:

        for i in range(0, total_blocos, DEFAULT_BATCH):
            lote = blocos[i:i + DEFAULT_BATCH]
            batch_num = (i // DEFAULT_BATCH) + 1

            resultado = traduzir_lote_ia(lote, logger, batch_num)

            if resultado:
                legendas_traduzidas.append(resultado)
                stats['requisicoes'] += 1
                stats['linhas_traduzidas'] += len(lote)
            else:
                logger.erro(f"Lote {batch_num}/{num_lotes} falhou criticamente na tradução.")
                stats['erros_traducao'] += 1
                legendas_traduzidas.append("\n\n".join(lote))

            pbar.update(len(lote))

    conteudo_final = "\n\n".join(legendas_traduzidas)
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        f.write(conteudo_final)

    logger.sucesso(f"Tradução finalizada e salva em: {os.path.basename(caminho_saida)}")
    return caminho_saida, stats


def main():
    print("=" * 80)
    print(f"{Fore.CYAN}       ESTEIRA SUP (OCR COM SUBTITLE EDIT + TRADUÇÃO COM IA)")
    print("=" * 80)

    logger = GerenciadorLogs()

    subtitle_edit_path = achar_subtitle_edit()
    if not subtitle_edit_path:
        logger.erro("Subtitle Edit não encontrado.")
        logger.info("Por favor, instale o Subtitle Edit no Windows para usar a esteira.")
        sys.exit(1)
        
    logger.sucesso(f"Subtitle Edit localizado em: {subtitle_edit_path}")

    # Validação do LM Studio
    if not validar_lm_studio(logger):
        logger.erro("LM Studio offline. Inicie o servidor local na porta 1234 e tente novamente.")
        sys.exit(1)

    arquivos_sup = []

    if len(sys.argv) > 1:
        # Modo argumentos / Drag & Drop
        argumentos = [arg.strip('"\'') for arg in sys.argv[1:]]
        for arg in argumentos:
            if os.path.isfile(arg) and arg.lower().endswith('.sup'):
                arquivos_sup.append(os.path.abspath(arg))
            elif os.path.isdir(arg):
                sup_na_pasta = sorted([
                    os.path.abspath(os.path.join(arg, f))
                    for f in os.listdir(arg)
                    if f.lower().endswith('.sup')
                ])
                arquivos_sup.extend(sup_na_pasta)
            else:
                logger.aviso(f"Caminho ignorado (não é um arquivo SUP ou pasta): {arg}")
        
        # Remove duplicados
        arquivos_sup = list(dict.fromkeys(arquivos_sup))
    else:
        # Modo interativo
        caminho_usuario = input(f"\n{Fore.YELLOW}Digite o caminho da pasta ou arquivo SUP: {Style.RESET_ALL}").strip('"\'')
        if not caminho_usuario:
            logger.erro("Nenhum caminho fornecido.")
            sys.exit(1)

        if os.path.isfile(caminho_usuario):
            if caminho_usuario.lower().endswith('.sup'):
                arquivos_sup.append(os.path.abspath(caminho_usuario))
            else:
                logger.erro("O arquivo informado não é um SUP válido.")
                sys.exit(1)
        elif os.path.isdir(caminho_usuario):
            arquivos_sup = sorted([
                os.path.abspath(os.path.join(caminho_usuario, f))
                for f in os.listdir(caminho_usuario)
                if f.lower().endswith('.sup')
            ])
        else:
            logger.erro("Caminho inválido ou inexistente.")
            sys.exit(1)

    # Filtrar apenas legendas em inglês se possível, já que japonês precisa de dicionário extra no OCR
    # No entanto, vamos processar o que foi passado.
    if not arquivos_sup:
        logger.erro("Nenhum arquivo .sup encontrado para processamento.")
        sys.exit(1)

    logger.sucesso(f"Encontrado(s) {len(arquivos_sup)} arquivo(s) .sup para processar.")

    total_processados = 0
    total_erros = 0

    print("\n" + "=" * 80)
    logger.info(f"Iniciando esteira para {len(arquivos_sup)} arquivo(s)...")

    for idx, caminho_sup in enumerate(arquivos_sup, 1):
        nome_sup = os.path.basename(caminho_sup)
        logger.info(f"[{idx}/{len(arquivos_sup)}] Processando: {nome_sup}")

        # Passo 1: Executa OCR
        caminho_srt = executar_ocr(caminho_sup, subtitle_edit_path, logger)
        if not caminho_srt:
            logger.erro(f"Pulando tradução para {nome_sup} devido a falha no OCR.")
            total_erros += 1
            continue

        # Passo 2: Traduz o SRT gerado
        try:
            caminho_final, stats = traduzir_arquivo_srt(caminho_srt, logger)
            logger.sucesso(f"Episódio concluído! Legenda final: {os.path.basename(caminho_final)}")
            total_processados += 1
            
            # Limpeza opcional do SRT em inglês temporário gerado pelo OCR
            # Se desejar manter o SRT em inglês, comente a linha abaixo
            try:
                os.remove(caminho_srt)
                logger.debug(f"Arquivo intermediário em inglês removido: {os.path.basename(caminho_srt)}")
            except Exception as e:
                logger.aviso(f"Não pôde remover o SRT intermediário: {e}")

        except Exception as e:
            logger.erro(f"Falha na tradução de {caminho_srt}: {e}")
            traceback.print_exc()
            total_erros += 1

    resumo = (
        f"RESUMO DA OPERAÇÃO SUP (OCR + TRADUÇÃO):\n"
        f"  Total de arquivos analisados: {len(arquivos_sup)}\n"
        f"  Concluídos com sucesso      : {total_processados}\n"
        f"  Falhas                      : {total_erros}"
    )

    logger.fechar(resumo)
    print("\n" + "=" * 80)
    print(f"{Fore.GREEN}[CONCLUÍDO] Esteira finalizada!")
    print(resumo)
    print(f"{Fore.CYAN}Log salvo em: {logger.caminho_log}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}[CANCELADO] Operação cancelada pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}[ERRO CRÍTICO] {str(e)}")
        traceback.print_exc()
        sys.exit(1)
