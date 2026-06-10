#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: extrator_pgs.py
Responsável por escanear arquivos MKV, identificar faixas de legenda PGS (imagem/bitmap)
e extraí-las automaticamente para arquivos .sup usando o mkvextract.
"""

import os
import sys
import json
import subprocess
import datetime
import shutil
import traceback

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

# Se estiver no Windows, podemos tentar o winreg para achar o MKVToolNix
if sys.platform == "win32":
    import winreg


def achar_ferramenta(nome_executavel):
    """
    Tenta localizar um executável do MKVToolNix no sistema:
    1. Usando shutil.which (verifica no PATH do sistema).
    2. Buscando no Registro do Windows (se aplicável).
    3. Buscando em caminhos padrão no Windows.
    """
    # 1. Tenta achar no PATH
    caminho = shutil.which(nome_executavel)
    if caminho and os.path.exists(caminho):
        return caminho

    # 2. Tenta achar no Registro do Windows
    if sys.platform == "win32":
        para_buscar = f"{nome_executavel}.exe"
        for hkey in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                # Tenta abrir o caminho do aplicativo registrado
                caminho_registro = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{para_buscar}"
                with winreg.OpenKey(hkey, caminho_registro) as key:
                    val, _ = winreg.QueryValueEx(key, "")
                    if val and os.path.exists(val):
                        return val
            except WindowsError:
                pass
            
            try:
                # Tenta abrir a chave de instalação do MKVToolNix
                with winreg.OpenKey(hkey, r"SOFTWARE\MKVToolNix") as key:
                    val, _ = winreg.QueryValueEx(key, "InstallDirectory")
                    if val:
                        caminho_completo = os.path.join(val, para_buscar)
                        if os.path.exists(caminho_completo):
                            return caminho_completo
            except WindowsError:
                pass

    # 3. Tenta caminhos padrão conhecidos
    caminhos_padrao = [
        rf"C:\Program Files\MKVToolNix\{nome_executavel}.exe",
        rf"C:\Program Files (x86)\MKVToolNix\{nome_executavel}.exe",
        rf"C:\ProgramData\chocolatey\bin\{nome_executavel}.exe",
    ]
    for caminho in caminhos_padrao:
        if os.path.exists(caminho):
            return caminho

    return None


class GerenciadorLogs:
    """
    Sistema de log simplificado e resiliente para a esteira de extração de legendas PGS.
    Salva logs formatados na pasta 'log' ao lado do script.
    """
    def __init__(self):
        self.pasta_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log")
        os.makedirs(self.pasta_log, exist_ok=True)
        
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.caminho_log = os.path.join(self.pasta_log, f"extracao_pgs_{self.timestamp}.log")
        
        # Abre o arquivo de log
        self.f_log = open(self.caminho_log, 'w', encoding='utf-8')
        
        header = (
            f"{'='*80}\n"
            f"ESTEIRA DE EXTRAÇÃO PGS - INICIALIZADA EM {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"{'='*80}\n\n"
        )
        self.f_log.write(header)
        self.f_log.flush()

    def _escrever(self, nivel, mensagem, cor_terminal=None):
        ts = datetime.datetime.now().strftime('%H:%M:%S')
        linha = f"[{ts}] [{nivel:6s}] {mensagem}"
        
        # Grava no log sem cores
        self.f_log.write(linha + "\n")
        self.f_log.flush()
        
        # Imprime no terminal com cores usando tqdm.write para não quebrar a barra de progresso
        if cor_terminal:
            tqdm.write(f"{cor_terminal}{linha}{Style.RESET_ALL}")
        else:
            tqdm.write(linha)

    def info(self, msg):
        self._escrever("INFO", msg, Fore.WHITE)

    def sucesso(self, msg):
        self._escrever("OK", msg, Fore.GREEN + Style.BRIGHT)

    def aviso(self, msg):
        self._escrever("AVISO", msg, Fore.YELLOW)

    def erro(self, msg):
        self._escrever("ERRO", msg, Fore.RED + Style.BRIGHT)

    def fechar(self, resumo):
        self.f_log.write(f"\n\n{'='*80}\n{resumo}\n{'='*80}\n")
        self.f_log.close()


def obter_faixas_pgs(caminho_mkv, mkvmerge_path, log):
    """
    Executa o mkvmerge --identify no formato JSON para mapear todas as trilhas
    de legenda do tipo PGS no arquivo de vídeo.
    Retorna uma lista de dicionários com as propriedades das faixas encontradas.
    """
    cmd = [mkvmerge_path, "--identification-format", "json", "--identify", caminho_mkv]

    try:
        resultado = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if resultado.returncode != 0:
            log.erro(f"Falha ao identificar faixas no arquivo: {os.path.basename(caminho_mkv)}")
            return []

        dados = json.loads(resultado.stdout)
        faixas_pgs = []

        for track in dados.get("tracks", []):
            if track.get("type") == "subtitles":
                codec = track.get("codec", "").upper()
                properties = track.get("properties", {})
                codec_id = properties.get("codec_id", "").upper()

                # Identifica se é PGS
                if "PGS" in codec or "PGS" in codec_id or "S_HDMV/PGS" in codec_id:
                    faixas_pgs.append({
                        "id": track.get("id"),
                        "idioma": properties.get("language", "und"),
                        "titulo": properties.get("track_name") or "Sem Título",
                        "codec": track.get("codec")
                    })

        return faixas_pgs
    except json.JSONDecodeError as e:
        log.erro(f"JSON inválido retornado pelo mkvmerge para {os.path.basename(caminho_mkv)}: {e}")
        return []
    except Exception as e:
        log.erro(f"Falha ao analisar o arquivo {os.path.basename(caminho_mkv)}: {str(e)}")
        return []


def extrair_faixa_pgs(caminho_mkv, faixa_id, caminho_saida_sup, mkvextract_path, log):
    """Executa o mkvextract para extrair a faixa PGS especificada para o formato .sup."""
    cmd = [
        mkvextract_path,
        caminho_mkv,
        "tracks",
        f"{faixa_id}:{caminho_saida_sup}"
    ]

    try:
        resultado = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if resultado.returncode == 0:
            return True
        else:
            log.erro(f"mkvextract falhou com código {resultado.returncode}: {resultado.stderr.strip()}")
            return False
    except Exception as e:
        log.erro(f"Exceção durante a extração: {str(e)}")
        return False


def main():
    print("=" * 80)
    print(f"{Fore.CYAN}       ESTEIRA DE EXTRAÇÃO DE LEGENDAS PGS (MKV -> SUP)")
    print("=" * 80)

    # Inicializa o logger
    logger = GerenciadorLogs()

    # Localizar ferramentas
    mkvextract_path = achar_ferramenta("mkvextract")
    mkvmerge_path = achar_ferramenta("mkvmerge")

    if not mkvextract_path or not mkvmerge_path:
        logger.erro("Não foi possível encontrar o mkvextract ou mkvmerge.")
        logger.info("Por favor, instale o MKVToolNix e certifique-se de que ele está no PATH ou no caminho padrão.")
        sys.exit(1)

    logger.sucesso(f"MKVExtract encontrado em: {mkvextract_path}")
    logger.sucesso(f"MKVMerge encontrado em: {mkvmerge_path}")

    # Processamento de argumentos
    arquivos_mkv = []

    if len(sys.argv) > 1:
        # Modo não-interativo ou Drag & Drop de múltiplos arquivos/pastas
        argumentos = [arg.strip('"\'') for arg in sys.argv[1:]]
        for arg in argumentos:
            if os.path.isfile(arg) and arg.lower().endswith('.mkv'):
                arquivos_mkv.append(os.path.abspath(arg))
            elif os.path.isdir(arg):
                mkv_na_pasta = sorted([
                    os.path.abspath(os.path.join(arg, f))
                    for f in os.listdir(arg)
                    if f.lower().endswith('.mkv')
                ])
                arquivos_mkv.extend(mkv_na_pasta)
            else:
                logger.aviso(f"Caminho ignorado (não é um arquivo MKV ou pasta): {arg}")
        
        # Remove duplicados mantendo a ordem
        arquivos_mkv = list(dict.fromkeys(arquivos_mkv))
        
        if not arquivos_mkv:
            logger.erro("Nenhum arquivo MKV válido foi encontrado nos argumentos informados.")
            sys.exit(1)
            
        logger.info(f"Modo de argumentos / Arrastar-e-Soltar detectado. {len(arquivos_mkv)} arquivo(s) carregado(s).")
        # No modo de drag and drop, definimos por padrão salvar na subpasta 'extraidos_sup' relativa a cada arquivo original
        opcao_saida = "1"
    else:
        # Modo interativo com o usuário
        caminho_usuario = input(f"\n{Fore.YELLOW}Digite o caminho da pasta ou arquivo MKV: {Style.RESET_ALL}").strip('"\'')
        if not caminho_usuario:
            logger.erro("Nenhum caminho fornecido.")
            sys.exit(1)

        if os.path.isfile(caminho_usuario):
            if caminho_usuario.lower().endswith('.mkv'):
                arquivos_mkv.append(os.path.abspath(caminho_usuario))
            else:
                logger.erro("O arquivo informado não é um MKV válido.")
                sys.exit(1)
        elif os.path.isdir(caminho_usuario):
            arquivos_mkv = sorted([
                os.path.abspath(os.path.join(caminho_usuario, f))
                for f in os.listdir(caminho_usuario)
                if f.lower().endswith('.mkv')
            ])
            if not arquivos_mkv:
                logger.erro("Nenhum arquivo MKV encontrado no diretório informado.")
                sys.exit(1)
        else:
            logger.erro("Caminho inválido ou inexistente.")
            sys.exit(1)

        logger.sucesso(f"Encontrado(s) {len(arquivos_mkv)} arquivo(s) MKV para processamento.")
        
        # Pergunta onde salvar as legendas
        print(f"\n{Fore.CYAN}Onde deseja salvar as legendas extraídas (.sup)?")
        print(f"  [1] Em uma pasta 'extraidos_sup' ao lado de cada arquivo MKV original (Recomendado)")
        print(f"  [2] Diretamente na pasta do arquivo MKV original (sem subpasta)")
        print(f"  [3] Em uma pasta 'extraidos_sup' global ao lado deste script")
        
        opcao_saida = input(f"{Fore.YELLOW}Opção (padrão: 1): {Style.RESET_ALL}").strip()
        if opcao_saida not in ("1", "2", "3"):
            opcao_saida = "1"

    # Estatísticas
    total_mkv = len(arquivos_mkv)
    total_extraidos = 0
    total_falhas = 0
    total_sem_pgs = 0

    pasta_script = os.path.dirname(os.path.abspath(__file__))

    print("\n" + "=" * 80)
    logger.info(f"Iniciando processamento de {total_mkv} arquivo(s) MKV...")

    with tqdm(total=total_mkv, desc="Progresso", unit="mkv", colour="green", ncols=90) as pbar:
        for idx, caminho_mkv in enumerate(arquivos_mkv, 1):
            nome_mkv = os.path.basename(caminho_mkv)
            dir_mkv = os.path.dirname(caminho_mkv)
            nome_base = os.path.splitext(nome_mkv)[0]

            pbar.set_postfix_str(f"Extraindo: {nome_mkv[:20]}...")
            logger.info(f"[{idx}/{total_mkv}] Analisando: {nome_mkv}")

            # Define a pasta de saída para este arquivo específico
            if opcao_saida == "1":
                pasta_saida = os.path.join(dir_mkv, "extraidos_sup")
            elif opcao_saida == "2":
                pasta_saida = dir_mkv
            else:  # Opção 3
                pasta_saida = os.path.join(pasta_script, "extraidos_sup")

            os.makedirs(pasta_saida, exist_ok=True)

            faixas = obter_faixas_pgs(caminho_mkv, mkvmerge_path, logger)

            if not faixas:
                logger.aviso(f"  -> Nenhuma legenda PGS (bitmap) encontrada em: {nome_mkv}")
                total_sem_pgs += 1
                pbar.update(1)
                continue

            logger.info(f"  Encontrada(s) {len(faixas)} faixa(s) PGS:")
            for f in faixas:
                logger.info(f"    · ID {f['id']} | Idioma: {f['idioma']} | Título: {f['titulo']}")

                nome_saida_sup = f"{nome_base}_Track{f['id']}_{f['idioma']}.sup"
                caminho_saida_sup = os.path.join(pasta_saida, nome_saida_sup)

                # Mostra o caminho relativo ou basename para ficar legível no terminal
                caminho_exibicao = os.path.join(os.path.basename(pasta_saida), nome_saida_sup) if opcao_saida != "2" else nome_saida_sup
                logger.info(f"      -> Extraindo para: {caminho_exibicao} ...")

                if extrair_faixa_pgs(caminho_mkv, f['id'], caminho_saida_sup, mkvextract_path, logger):
                    logger.sucesso(f"      -> Extraído com sucesso!")
                    total_extraidos += 1
                else:
                    logger.erro(f"      -> FALHA na extração da faixa ID {f['id']}.")
                    total_falhas += 1

            pbar.update(1)

    # Resumo final
    resumo_final = (
        f"RESUMO DO PROCESSAMENTO:\n"
        f"  Total de arquivos MKV analisados: {total_mkv}\n"
        f"  Arquivos sem legendas PGS      : {total_sem_pgs}\n"
        f"  Legendas PGS extraídas (.sup)  : {total_extraidos}\n"
        f"  Falhas de extração             : {total_falhas}"
    )

    logger.fechar(resumo_final)

    print("\n" + "=" * 80)
    print(f"{Fore.GREEN}[CONCLUÍDO] Processamento finalizado!")
    print(resumo_final)
    print(f"{Fore.CYAN}Log da execução salvo em: {logger.caminho_log}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}[CANCELADO] Operação cancelada pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}[ERRO INESPERADO] {str(e)}")
        traceback.print_exc()
        sys.exit(1)
