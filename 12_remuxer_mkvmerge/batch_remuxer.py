#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: batch_remuxer.py (Fase 2 do Pipeline — Otimizado)
Responsável por orquestrar o processo de multiplexação (remuxing) em lote.
Ele recebe os arquivos de vídeo originais (.mkv) e as legendas traduzidas (.ass),
e utiliza o mkvmerge para uni-los sem re-encodar o vídeo ou áudio.
As novas legendas são definidas como faixa padrão (Default Track) em Português.

Author: Paulo + Gemini
Data: Maio 2026
Status: PRODUCTION READY (High Performance)
"""
import os
import sys
import json
import time
import logging
import signal
import traceback
import subprocess
import shutil
from datetime import datetime
from tqdm import tqdm
from colorama import Fore, Style, init

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

init(autoreset=True)


class IndustrialRemuxerV2:
    def __init__(self, pasta_videos, pasta_legendas):
        self.mkvmerge_path = self._achar_mkvmerge()
        self.pasta_raiz = pasta_videos
        self.pasta_legendas = pasta_legendas
        self.pasta_saida = os.path.join(self.pasta_raiz, "mkv_final_ptbr")
        
        # Pasta de logs dinâmica na raiz do projeto
        pasta_raiz_projeto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.pasta_logs = os.path.join(pasta_raiz_projeto, "multiplexar", "logs")

        self.timestamp_sessao = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        self.log_pipeline_nome = f"remux_pipeline_{self.timestamp_sessao}.txt"
        self.log_erros_nome = f"remux_erros_{self.timestamp_sessao}.txt"
        self.log_stats_nome = f"remux_stats_{self.timestamp_sessao}.json"
        self.log_config_nome = f"remux_config_{self.timestamp_sessao}.txt"

        self.caminho_log_pipeline = os.path.join(self.pasta_logs, self.log_pipeline_nome)
        self.caminho_log_erros = os.path.join(self.pasta_logs, self.log_erros_nome)
        self.caminho_log_stats = os.path.join(self.pasta_logs, self.log_stats_nome)
        self.caminho_log_config = os.path.join(self.pasta_logs, self.log_config_nome)

        self.stats = {
            "timestamp": self.timestamp_sessao,
            "data_hora_inicio": datetime.now().isoformat(),
            "mkv_detectados": 0,
            "mkv_processados_sucesso": 0,
            "legendas_pareadas": 0,
            "erros_infraestrutura": 0,
            "erros_mkvmerge_runtime": 0,
            "erros_permissao_io": 0,
            "erros_inesperados": 0,
            "bytes_mkv_gerados_total": 0,
            "arquivos_ignorados": 0
        }

        # Cria a pasta de logs preemptivamente para evitar exceção no FileHandler
        os.makedirs(self.pasta_logs, exist_ok=True)

        self.configurar_sistema_logging()
        self.registrar_captura_sinais()

    def _achar_mkvmerge(self):
        caminhos_padrao = [
            r"C:\Program Files\MKVToolNix\mkvmerge.exe",
            r"C:\Program Files (x86)\MKVToolNix\mkvmerge.exe",
        ]
        for caminho in caminhos_padrao:
            if os.path.exists(caminho):
                return caminho
        
        via_path = shutil.which("mkvmerge")
        if via_path:
            return via_path
            
        return r"C:\Program Files\MKVToolNix\mkvmerge.exe"

    def configurar_sistema_logging(self):
        self.logger = logging.getLogger("IndustrialRemuxer")
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.handlers:
            file_handler = logging.FileHandler(self.caminho_log_pipeline, encoding='utf-8')
            formatter = logging.Formatter('[%(asctime)s.%(msecs)03d] [%(levelname)-8s] %(message)s', datefmt='%H:%M:%S')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def registrar_captura_sinais(self):
        signal.signal(signal.SIGINT, self.manipular_interrupcao_sistema)
        signal.signal(signal.SIGTERM, self.manipular_interrupcao_sistema)

    def manipular_interrupcao_sistema(self, signum, frame):
        print(f"\n\n{Fore.RED}{'!'*80}\n{'INTERRUPÇÃO DETECTADA PELO OPERADOR (CTRL+C)':^80}\n{'!'*80}")
        self.logger.warning("Execução abortada manualmente pelo usuário via sinal de interrupção.")
        self.console_log("AVISO", "Fechando buffers de arquivos e salvando telemetria parcial em disco...")
        self.salvar_relatorio_estatistico_json()
        self.console_log("SUCESSO", "Estatísticas parciais persistidas. Encerrando thread.")
        sys.exit(0)

    def console_log(self, tipo, mensagem):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if tipo == "DEBUG":
            print(f"[{timestamp}] [{Fore.WHITE}DEBUG   {Style.RESET_ALL}] {mensagem}")
            self.logger.debug(mensagem)
        elif tipo == "INFO":
            print(f"[{timestamp}] [{Fore.BLUE}INFO    {Style.RESET_ALL}] {mensagem}")
            self.logger.info(mensagem)
        elif tipo == "SUCESSO":
            print(f"[{timestamp}] [{Fore.GREEN}SUCESSO {Style.RESET_ALL}] {Fore.GREEN}{mensagem}{Style.RESET_ALL}")
            self.logger.info(f"SUCESSO: {mensagem}")
        elif tipo == "AVISO":
            print(f"[{timestamp}] [{Fore.YELLOW}AVISO   {Style.RESET_ALL}] {Fore.YELLOW}{mensagem}{Style.RESET_ALL}")
            self.logger.warning(mensagem)
        elif tipo == "ERRO":
            print(f"[{timestamp}] [{Fore.RED}ERRO    {Style.RESET_ALL}] {Fore.RED}{mensagem}{Style.RESET_ALL}")
            self.logger.error(mensagem)

    def registrar_excecao_forense(self, mensagem_erro, traceback_str):
        with open(self.caminho_log_erros, "a", encoding="utf-8") as f:
            f.write(f"='+'= AUDITORIA DE ERRO: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ='+'=\n")
            f.write(f"Contexto: {mensagem_erro}\n")
            f.write(f"Traceback Computacional:\n{traceback_str}\n")
            f.write(f"{'='*80}\n\n")

    def gerar_arquivo_configuracao_inicial(self):
        try:
            with open(self.caminho_log_config, "w", encoding="utf-8") as f:
                f.write(f"{'='*80}\nCONFIGURAÇÃO DA INFRAESTRUTURA DE PRODUÇÃO\n{'='*80}\n")
                f.write(f"Data/Hora de Inicialização : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Binário mkvmerge Mapeado  : {self.mkvmerge_path}\n")
                f.write(f"Diretório de Vídeos Origem : {self.pasta_raiz}\n")
                f.write(f"Diretório de Legendas Subs : {self.pasta_legendas}\n")
                f.write(f"Diretório de Destino Final : {self.pasta_saida}\n")
                f.write(f"Hardware Ativo de Destino  : Armazenamento Local NVMe\n")
                f.write(f"{'='*80}\n")
            self.console_log("DEBUG", f"Arquivo de configuração gerado com sucesso: {self.log_config_nome}")
        except Exception as e:
            self.console_log("AVISO", f"Incapaz de gerar arquivo de configuração inicial: {str(e)}")

    def salvar_relatorio_estatistico_json(self):
        try:
            self.stats["data_hora_fim"] = datetime.now().isoformat()
            with open(self.caminho_log_stats, "w", encoding="utf-8") as f:
                json.dump(self.stats, f, indent=4, ensure_ascii=False)
            self.console_log("DEBUG", f"Dicionário estatístico persistido: {self.log_stats_nome}")
        except Exception as e:
            self.console_log("ERRO", f"Falha ao salvar dump JSON de estatísticas: {str(e)}")

    def validar_infraestrutura_sistema(self):
        print(f"\n{Fore.CYAN}{'='*80}\n{Fore.CYAN}{'VALIDAÇÃO DE INFRAESTRUTURA DE MÍDIA':^80}\n{Fore.CYAN}{'='*80}")

        self.console_log("DEBUG", "Testando conectividade e acesso ao binário mkvmerge...")
        if not os.path.exists(self.mkvmerge_path):
            self.console_log("ERRO", f"mkvmerge.exe não localizado no caminho do sistema operacional: {self.mkvmerge_path}")
            self.stats["erros_infraestrutura"] += 1
            return False

        try:
            resultado = subprocess.run([self.mkvmerge_path, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            self.console_log("SUCESSO", f"mkvmerge funcional: {resultado.stdout.strip()}")
        except Exception as e:
            self.console_log("ERRO", f"Falha de execução ao chamar mkvmerge: {str(e)}")
            self.stats["erros_infraestrutura"] += 1
            return False

        self.console_log("DEBUG", "Validando caminhos de diretórios locais...")
        if not os.path.exists(self.pasta_raiz):
            self.console_log("ERRO", f"Diretório raiz de vídeos indisponível: {self.pasta_raiz}")
            self.stats["erros_infraestrutura"] += 1
            return False

        if not os.path.exists(self.pasta_legendas):
            self.console_log("ERRO", f"Diretório de legendas traduzidas ausente: {self.pasta_legendas}")
            self.stats["erros_infraestrutura"] += 1
            return False

        os.makedirs(self.pasta_saida, exist_ok=True)
        self.console_log("SUCESSO", "[OK] Toda a infraestrutura e permissões foram validadas com sucesso!")
        return True

    def construir_fila_processamento(self):
        print(f"\n{Fore.CYAN}{'='*80}\n{Fore.CYAN}{'INPUTS E PAREAMENTO DE ARQUIVOS':^80}\n{Fore.CYAN}{'='*80}")
        self.console_log("DEBUG", f"Escaneando diretório: {self.pasta_raiz}")

        try:
            arquivos_diretorio = os.listdir(self.pasta_raiz)
            videos_mkv = sorted([f for f in arquivos_diretorio if f.endswith('.mkv')])
            self.stats["mkv_detectados"] = len(videos_mkv)

            self.console_log("INFO", f"Encontrados {len(videos_mkv)} arquivos de vídeo com extensão .mkv.")
            self.console_log("DEBUG", "Iniciando verificação de correspondência na pasta de legendas...")

            fila_trabalho = []

            for mkv in videos_mkv:
                caminho_mkv_completo = os.path.join(self.pasta_raiz, mkv)
                nome_base = os.path.splitext(mkv)[0]

                # Identifica variantes de sufixos de legendas comuns no ecossistema
                nome_limpo_legenda = nome_base.replace("_PTBR", "").replace("_ENG", "")
                
                tentativas = [
                    f"{nome_limpo_legenda}_PTBR_ENG.ass",
                    f"{nome_limpo_legenda}_PTBR_PTBR.ass",
                    f"{nome_limpo_legenda}_PTBR.ass",
                    f"{nome_base}.ass",
                    f"{nome_base}_ENG.ass",
                    f"{nome_base}_PTBR.ass"
                ]
                
                caminho_legenda_completo = None
                for tentativa in tentativas:
                    caminho = os.path.join(self.pasta_legendas, tentativa)
                    if os.path.exists(caminho):
                        caminho_legenda_completo = caminho
                        legenda_nome_esperado = tentativa
                        break
                        
                if not caminho_legenda_completo:
                    legenda_nome_esperado = f"{nome_limpo_legenda}_PTBR.ass"
                    caminho_legenda_completo = os.path.join(self.pasta_legendas, legenda_nome_esperado)

                caminho_saida_final = os.path.join(self.pasta_saida, f"{nome_limpo_legenda}_PTBR.mkv")

                if os.path.exists(caminho_legenda_completo):
                    self.stats["legendas_pareadas"] += 1
                    fila_trabalho.append({
                        "mkv_nome": mkv,
                        "caminho_mkv": caminho_mkv_completo,
                        "caminho_legenda": caminho_legenda_completo,
                        "caminho_saida": caminho_saida_final
                    })
                    self.console_log("DEBUG", f"  Pareado com sucesso: {mkv} -> {legenda_nome_esperado}")
                else:
                    self.stats["arquivos_ignorados"] += 1
                    self.console_log("AVISO", f"  Legenda ausente para: {mkv} (esperado: {legenda_nome_esperado})")

            return fila_trabalho

        except Exception as e:
            tb = traceback.format_exc()
            self.console_log("ERRO", f"Erro fatal ao tentar ler a estrutura de diretórios: {str(e)}")
            self.registrar_excecao_forense("construir_fila_processamento", tb)
            return []

    def executar_operacao_remux(self):
        self.gerar_arquivo_configuracao_inicial()

        if not self.validar_infraestrutura_sistema():
            self.console_log("ERRO", "Falha na validação de ambiente de hardware/software. Abortando pipeline.")
            self.salvar_relatorio_estatistico_json()
            sys.exit(1)

        fila = self.construir_fila_processamento()
        total_fila = len(fila)

        if total_fila == 0:
            self.console_log("AVISO", "A fila de processamento está vazia. Nenhuma ação será tomada.")
            self.salvar_relatorio_estatistico_json()
            return

        print(f"\n{Fore.CYAN}{'='*80}\n{Fore.CYAN}{'PROCESSAMENTO MULTIPLEXAR EM SEGUNDO PLANO':^80}\n{Fore.CYAN}{'='*80}")
        self.console_log("INFO", f"Esteira trancada. Processando {total_fila} episódios em lote via mkvmerge.")

        with tqdm(total=total_fila, desc=f"{Fore.CYAN}Progresso Remux{Style.RESET_ALL}", unit="ep", leave=True) as pbar:
            for indice, item in enumerate(fila, 1):
                self.console_log("INFO", f"[{indice}/{total_fila}] Multiplexando container Matroska: {item['mkv_nome']}")

                comando_mkvmerge = [
                    self.mkvmerge_path,
                    "-o", item['caminho_saida'],
                    "--no-subtitles",
                    item['caminho_mkv'],
                    "--language", "0:por",
                    "--track-name", "0:Português (Gemma 4B)",
                    "--default-track", "0:yes",
                    item['caminho_legenda']
                ]

                start_time_arquivo = time.time()

                try:
                    self.console_log("DEBUG", "  Despachando chamada para o kernel do Windows...")

                    resultado = subprocess.run(
                        comando_mkvmerge,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True
                    )

                    tempo_gasto = time.time() - start_time_arquivo

                    if os.path.exists(item['caminho_saida']):
                        tamanho_bytes = os.path.getsize(item['caminho_saida'])
                        self.stats["bytes_mkv_gerados_total"] += tamanho_bytes
                        tamanho_gb = tamanho_bytes / (1024 * 1024 * 1024)
                        self.console_log("SUCESSO", f"  Concluido ({tamanho_gb:.3f} GB) em {tempo_gasto:.2f}s! Legenda adicionada.")
                    else:
                        self.console_log("AVISO", "  mkvmerge finalizou sem erros, mas o arquivo de saída não foi detectado no armazenamento local.")

                    self.stats["mkv_processados_sucesso"] += 1

                except subprocess.CalledProcessError as e:
                    tb = traceback.format_exc()
                    self.stats["erros_mkvmerge_runtime"] += 1
                    self.console_log("ERRO", f"  Erro interno do mkvmerge no arquivo {item['mkv_nome']}. Verifique o log de erros.")
                    self.registrar_excecao_forense(f"CalledProcessError no arquivo: {item['mkv_nome']}\nLog Stdout:\n{e.stdout}", f"Log Stderr:\n{e.stderr}\n\n{tb}")
                    continue

                except PermissionError as e:
                    tb = traceback.format_exc()
                    self.stats["erros_permissao_io"] += 1
                    self.console_log("ERRO", f"  Permissão de escrita/leitura negada pelo sistema operacional no arquivo: {item['mkv_nome']}")
                    self.registrar_excecao_forense(f"PermissionError no arquivo: {item['mkv_nome']}", tb)
                    continue

                except Exception as e:
                    tb = traceback.format_exc()
                    self.stats["erros_inesperados"] += 1
                    self.console_log("ERRO", f"  Exceção de alto nível não interceptada no processamento de: {item['mkv_nome']}")
                    self.registrar_excecao_forense(f"Exception inesperada no arquivo: {item['mkv_nome']} | Detalhes: {str(e)}", tb)
                    continue

                finally:
                    pbar.update(1)

        self.exibir_relatorio_final_producao()

    def exibir_relatorio_final_producao(self):
        self.salvar_relatorio_estatistico_json()
        tamanho_total_gb = self.stats["bytes_mkv_gerados_total"] / (1024 * 1024 * 1024)

        print(f"\n{Fore.GREEN}{'='*80}\n{Fore.GREEN}{'RELATÓRIO FINAL DE MULTIPLEXAÇÃO INDUSTRIAL':^80}\n{Fore.GREEN}{'='*80}")
        print(f"  Arquivos MKV Detectados     : {self.stats['mkv_detectados']}")
        print(f"  Legendas PTBR Encontradas   : {self.stats['legendas_pareadas']}")
        print(f"  Multiplexados com Sucesso   : {Fore.GREEN}{self.stats['mkv_processados_sucesso']}{Style.RESET_ALL}")
        print(f"  Arquivos Ignorados (Sem Sub): {Fore.YELLOW}{self.stats['arquivos_ignorados']}{Style.RESET_ALL}")
        print(f"  Volume de Dados Gravados    : {tamanho_total_gb:.3f} GB")
        print(f"{'='*80}")
        print(f"  {Fore.RED}Erros de Infraestrutura     : {self.stats['erros_infraestrutura']}")
        print(f"  {Fore.RED}Erros de Mkvmerge Runtime   : {self.stats['erros_mkvmerge_runtime']}")
        print(f"  {Fore.RED}Erros de Permissão de I/O   : {self.stats['erros_permissao_io']}")
        print(f"  {Fore.RED}Erros Inesperados/Hardware  : {self.stats['erros_inesperados']}")
        print(f"{'='*80}")
        print(f"  Diretório dos Logs Físicos : {self.pasta_logs}")
        print(f"  Log de Auditoria do Fluxo  : {self.log_pipeline_nome}")
        print(f"  Isolamento de Dumps de Erro: {self.log_erros_nome}")
        print(f"  Metadados de Telemetria    : {self.log_stats_nome}")
        print(f"{'='*80}")
        self.console_log("SUCESSO", "Esteira finalizada e consolidada com sucesso!")


def obter_diretorio_operador(mensagem_prompt, padrao_caminho=None):
    """Captura e valida a entrada de diretórios fornecida pelo usuário via console."""
    while True:
        sufixo_padrao = f" (ENTER = {padrao_caminho})" if padrao_caminho else ""
        entrada = input(f"{Fore.CYAN}{mensagem_prompt}{sufixo_padrao}: {Style.RESET_ALL}").strip()
        entrada = entrada.strip('"').strip("'")
        
        if not entrada and padrao_caminho:
            return padrao_caminho
            
        if not entrada:
            print(f"{Fore.RED}[ERRO] O caminho não pode ser vazio.")
            continue
            
        if not os.path.isdir(entrada):
            print(f"{Fore.RED}[ERRO] O diretório especificado não existe fisicamente: {entrada}")
            continue
            
        return entrada


if __name__ == "__main__":
    print(f"\n{Fore.CYAN}{'='*80}\n{Fore.CYAN}{'CONFIGURAÇÃO DE DIRETÓRIOS':^80}\n{Fore.CYAN}{'='*80}")

    caminho_padrao_videos = (
        r"D:\PROJETOS-OPEN\animes"
        r"\Mobile Suit Gundam Unicorn Re0096 (2016) [Season 1] [BD 1080p HEVC OPUS] [Dual-Audio]"
        r"\Season 1"
    )
    pasta_videos = obter_diretorio_operador("Pasta com os vídeos originais (.mkv)", caminho_padrao_videos)

    # Tenta detectar qual subpasta de tradução existe na pasta selecionada
    caminho_padrao_legendas = os.path.join(pasta_videos, "legendas_ptbr")
    if not os.path.exists(caminho_padrao_legendas):
        caminho_padrao_legendas = os.path.join(pasta_videos, "traduzidos")
    if not os.path.exists(caminho_padrao_legendas):
        caminho_padrao_legendas = os.path.join(pasta_videos, "traducao")

    pasta_legendas = obter_diretorio_operador("Pasta com as legendas (.ass)", caminho_padrao_legendas)

    remuxer = IndustrialRemuxerV2(pasta_videos, pasta_legendas)
    remuxer.executar_operacao_remux()