import os
import sys
import json
import time
import shutil
import logging
import signal
import subprocess
from datetime import datetime
from tqdm import tqdm
from colorama import Fore, Style, init

# Inicializa o Colorama para controle de cores ANSI no PowerShell do Windows
init(autoreset=True)

class IndustrialRemuxerV2:
    def __init__(self):
        # 1. Configuração Estrita de Caminhos e Infraestrutura
        self.mkvmerge_path = r"C:\Program Files\MKVToolNix\mkvmerge.exe"
        self.pasta_raiz = r"C:\TRACKER-ANIMES\animes\Macross Delta"
        self.pasta_legendas = os.path.join(self.pasta_raiz, "traducao")
        self.pasta_saida = os.path.join(self.pasta_raiz, "mkv_final_ptbr")
        self.pasta_logs = r"C:\TRACKER-ANIMES\projeto-tracker-animes-traducao\multiplexar\logs"
        
        # 2. Carimbo de Data/Hora Único para esta Sessão de Produção
        self.timestamp_sessao = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # 3. Nomes dos Arquivos de Relatório Forense
        self.log_pipeline_nome = f"remux_pipeline_{self.timestamp_sessao}.txt"
        self.log_erros_nome = f"remux_erros_{self.timestamp_sessao}.txt"
        self.log_stats_nome = f"remux_stats_{self.timestamp_sessao}.json"
        self.log_config_nome = f"remux_config_{self.timestamp_sessao}.txt"
        
        # 4. Caminhos Absolutos dos Logs
        self.caminho_log_pipeline = os.path.join(self.pasta_logs, self.log_pipeline_nome)
        self.caminho_log_erros = os.path.join(self.pasta_logs, self.log_erros_nome)
        self.caminho_log_stats = os.path.join(self.pasta_logs, self.log_stats_nome)
        self.caminho_log_config = os.path.join(self.pasta_logs, self.log_config_nome)

        # 5. Inicialização da Estrutura de Métricas de Auditoria
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

        # 6. Criação de Segurança dos Diretórios
        os.makedirs(self.pasta_logs, exist_ok=True)
        os.makedirs(self.pasta_saida, exist_ok=True)
        
        self.configurar_sistema_logging()
        self.registrar_captura_sinais()

    def configurar_sistema_logging(self):
        """Configura o mecanismo principal do logger nativo do Python para gravação assíncrona"""
        self.logger = logging.getLogger("IndustrialRemuxer")
        self.logger.setLevel(logging.DEBUG)
        
        # Evita duplicação de handlers caso o script seja reinicializado na mesma thread
        if not self.logger.handlers:
            file_handler = logging.FileHandler(self.caminho_log_pipeline, encoding='utf-8')
            formatter = logging.Formatter('[%(asctime)s.%(msecs)03d] [%(levelname)-8s] %(message)s', datefmt='%H:%M:%S')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def registrar_captura_sinais(self):
        """Intercepta sinais de interrupção do sistema operacional (Ctrl + C) para desligamento limpo"""
        signal.signal(signal.SIGINT, self.manipular_interrupcao_sistema)
        signal.signal(signal.SIGTERM, self.manipular_interrupcao_sistema)

    def manipular_interrupcao_sistema(self, signum, frame):
        """Trata o fechamento forçado garantindo a persistência dos logs parciais e limpando travas de I/O"""
        print(f"\n\n{Fore.RED}{'!'*80}\n{'INTERRUPÇÃO DETECTADA PELO USUÁRIO (CTRL+C)':^80}\n{'!'*80}")
        self.logger.warning("Execução abortada manualmente pelo usuário via sinal de interrupção.")
        self.console_log("AVISO", "Fechando buffers de arquivos e salvando telemetria parcial em disco...")
        self.salvar_relatorio_estatistico_json()
        self.console_log("SUCESSO", "Estatísticas parciais persistidas. Encerrando thread.")
        sys.exit(0)

    def console_log(self, tipo, mensagem):
        """Camada de abstração visual para coloração ANSI no console e espelhamento no arquivo de log"""
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
        """Grava falhas críticas e dumps de Stack Trace em um arquivo isolado de erros"""
        with open(self.caminho_log_erros, "a", encoding="utf-8") as f:
            f.write(f"='+'= AUDITORIA DE ERRO: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ='+'=\n")
            f.write(f"Contexto: {mensagem_erro}\n")
            f.write(f"Traceback Computacional:\n{traceback_str}\n")
            f.write(f"{'='*80}\n\n")

    def gerar_arquivo_configuracao_inicial(self):
        """Gera uma fotografia imutável das configurações e caminhos antes do processamento"""
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
        """Dump definitivo da estrutura de dicionário em formato estruturado JSON"""
        try:
            self.stats["data_hora_fim"] = datetime.now().isoformat()
            with open(self.caminho_log_stats, "w", encoding="utf-8") as f:
                json.dump(self.stats, f, indent=4, ensure_ascii=False)
            self.console_log("DEBUG", f"Dicionário estatístico persistido: {self.log_stats_nome}")
        except Exception as e:
            self.console_log("ERRO", f"Falha ao salvar dump JSON de estatísticas: {str(e)}")

    def validar_infraestrutura_sistema(self):
        """Executa checagens profundas de existência e permissões de escrita antes de abrir a fila"""
        print(f"\n{Fore.CYAN}{'='*80}\n{Fore.CYAN}{'VALIDAÇÃO DE INFRAESTRUTURA DE MÍDIA':^80}\n{Fore.CYAN}{'='*80}")
        
        self.console_log("DEBUG", f"Testando conectividade e acesso ao binário mkvmerge...")
        if not os.path.exists(self.mkvmerge_path):
            self.console_log("ERRO", f"mkvmerge.exe não localizado no caminho do sistema operacional: {self.mkvmerge_path}")
            self.stats["erros_infraestrutura"] += 1
            return False
            
        try:
            # Executa uma chamada leve de versão para atestar o funcionamento do binário externo
            resultado = subprocess.run([self.mkvmerge_path, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            self.console_log("SUCESSO", f"mkvmerge funcional: {resultado.stdout.strip()}")
        except Exception as e:
            self.console_log("ERRO", f"Falha de execução ao chamar mkvmerge: {str(e)}")
            self.stats["erros_infraestrutura"] += 1
            return False

        self.console_log("DEBUG", f"Validando caminhos de diretórios locais...")
        if not os.path.exists(self.pasta_raiz):
            self.console_log("ERRO", f"Diretório raiz de vídeos indisponível: {self.pasta_raiz}")
            self.stats["erros_infraestrutura"] += 1
            return False
            
        if not os.path.exists(self.pasta_legendas):
            self.console_log("ERRO", f"Diretório de legendas traduzidas ausente: {self.pasta_legendas}")
            self.stats["erros_infraestrutura"] += 1
            return False

        self.console_log("SUCESSO", "✓ Toda a infraestrutura e permissões foram validadas com sucesso!")
        return True

    def construir_fila_processamento(self):
        """Varre os diretórios pareando de forma determinística os containers com as subs traduzidas"""
        print(f"\n{Fore.CYAN}{'='*80}\n{Fore.CYAN}{'INPUTS E PAREAMENTO DE ARQUIVOS':^80}\n{Fore.CYAN}{'='*80}")
        self.console_log("DEBUG", f"Escaneando diretório: {self.pasta_raiz}")
        
        try:
            arquivos_diretorio = os.listdir(self.pasta_raiz)
            videos_mkv = sorted([f for f in arquivos_diretorio if f.endswith('.mkv')])
            self.stats["mkv_detectados"] = len(videos_mkv)
            
            self.console_log("INFO", f"Encontrados {len(videos_mkv)} arquivos de vídeo com extensão .mkv.")
            self.console_log("DEBUG", "Iniciando verificação de correspondência na pasta \\traducao...")
            
            fila_trabalho = []
            
            for mkv in videos_mkv:
                caminho_mkv_completo = os.path.join(self.pasta_raiz, mkv)
                nome_base = os.path.splitext(mkv)[0]
                
                # Casamento estrito com o padrão de saída do tradutor local
                legenda_nome_esperado = f"{nome_base}_PTBR.ass"
                caminho_legenda_completo = os.path.join(self.pasta_legendas, legenda_nome_esperado)
                
                caminho_saida_final = os.path.join(self.pasta_saida, f"{nome_base}_PTBR.mkv")
                
                if os.path.exists(caminho_legenda_completo):
                    self.stats["legendas_pareadas"] += 1
                    fila_trabalho.append({
                        "mkv_nome": mkv,
                        "caminho_mkv": caminho_mkv_completo,
                        "caminho_legenda": caminho_legenda_completo,
                        "caminho_saida": caminho_saida_final
                    })
                    self.console_log("DEBUG", f"  ↳ Pareado com sucesso: {mkv} ➔ {legenda_nome_esperado}")
                else:
                    self.stats["arquivos_ignorados"] += 1
                    self.console_log("AVISO", f"  ↳ Legenda traduzida ausente para: {mkv}. Este arquivo não será multiplexado.")
                    
            return fila_trabalho
            
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.console_log("ERRO", f"Erro fatal ao tentar ler a estrutura de diretórios: {str(e)}")
            self.registrar_excecao_forense("construir_fila_processamento", tb)
            return []

    def executar_operacao_remux(self):
        """Gerencia o loop principal da esteira de processamento chamando o multiplexador em lote"""
        self.gerar_arquivo_configuracao_inicial()
        
        if not self.validar_infraestrutura_sistema():
            self.console_log("ERRO", "Falha na validação de ambiente de hardware/software. Abortando pipeline.")
            self.salvar_relatorio_estatistico_json()
            sys.exit(1)

        fila = self.construct_fila_processamento() if "construct_fila_processamento" in dir(self) else self.construir_fila_processamento()
        total_fila = len(fila)

        if total_fila == 0:
            self.console_log("AVISO", "A fila de processamento está vazia. Nenhuma ação será tomada.")
            self.salvar_relatorio_estatistico_json()
            return

        print(f"\n{Fore.CYAN}{'='*80}\n{Fore.CYAN}{'PROCESSAMENTO MULTIPLEXAR EM SEGUNDO PLANO':^80}\n{Fore.CYAN}{'='*80}")
        self.console_log("INFO", f"Esteira trancada. Processando {total_fila} episódios em lote via mkvmerge.")

        # Inicialização da Barra de Progresso TQDM Integrada
        with tqdm(total=total_fila, desc=f"{Fore.CYAN}Progresso Remux{Style.RESET_ALL}", unit="ep", leave=True) as pbar:
            for indice, item in enumerate(fila, 1):
                self.console_log("INFO", f"[{indice}/{total_fila}] Multiplexando container Matroska: {item['mkv_nome']}")
                
                # Montagem explícita do vetor de argumentos para o subprocesso do sistema operacional
                comando_mkvmerge = [
                    self.mkvmerge_path,
                    "-o", item['caminho_saida'],
                    item['caminho_mkv'],
                    "--language", "0:por",
                    "--track-name", "0:Português (Gemma 4B)",
                    "--default-track", "0:yes",
                    item['caminho_legenda']
                ]

                start_time_arquivo = time.time()
                
                try:
                    self.console_log("DEBUG", "  ↳ Despachando chamada para o kernel do Windows...")
                    
                    # Executa a operação capturando pipes de memória para evitar poluição visual
                    resultado = subprocess.run(
                        comando_mkvmerge,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True
                    )
                    
                    tempo_gasto = time.time() - start_time_arquivo
                    
                    # Extração do tamanho do arquivo gerado para auditoria de I/O de disco
                    if os.path.exists(item['caminho_saida']):
                        tamanho_bytes = os.path.getsize(item['caminho_saida'])
                        self.stats["bytes_mkv_gerados_total"] += tamanho_bytes
                        tamanho_mb = tamanho_bytes / (1024 * 1024)
                        self.console_log("SUCESSO", f"  ↳ Concluído ({tamanho_mb:.2f} MB) em {tempo_gasto:.2f}s! Legenda adicionada.")
                    else:
                        self.console_log("AVISO", "  ↳ mkvmerge finalizou sem erros, mas o arquivo de saída não foi detectado no armazenamento local.")
                    
                    self.stats["mkv_processados_sucesso"] += 1
                    
                except subprocess.CalledProcessError as e:
                    import traceback
                    tb = traceback.format_exc()
                    self.stats["erros_mkvmerge_runtime"] += 1
                    self.console_log("ERRO", f"  ↳ Erro interno do mkvmerge no arquivo {item['mkv_nome']}. Verifique o log de erros.")
                    self.registrar_excecao_forense(f"CalledProcessError no arquivo: {item['mkv_nome']}\nLog Stdout:\n{e.stdout}", f"Log Stderr:\n{e.stderr}\n\n{tb}")
                    continue
                    
                except PermissionError as e:
                    import traceback
                    tb = traceback.format_exc()
                    self.stats["erros_permissao_io"] += 1
                    self.console_log("ERRO", f"  ↳ Permissão de escrita/leitura negada pelo sistema operacional no arquivo: {item['mkv_nome']}")
                    self.registrar_excecao_forense(f"PermissionError no arquivo: {item['mkv_nome']}", tb)
                    continue
                    
                except Exception as e:
                    import traceback
                    tb = traceback.format_exc()
                    self.stats["erros_inesperados"] += 1
                    self.console_log("ERRO", f"  ↳ Exceção de alto nível não interceptada no processamento de: {item['mkv_nome']}")
                    self.registrar_excecao_forense(f"Exception inesperada no arquivo: {item['mkv_nome']} | Detalhes: {str(e)}", tb)
                    continue
                finally:
                    # Incrementa a barra visual do TQDM
                    pbar.update(1)

        self.exibir_relatorio_final_producao()

    def exibir_relatorio_final_producao(self):
        """Renderiza o bloco de estatísticas finais idêntico ao relatório do tradutor local"""
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
        print(f"  📁 Diretório dos Logs Físicos: {self.pasta_logs}")
        print(f"  📄 Log de Auditoria do Fluxo : {self.log_pipeline_nome}")
        print(f"  ⚠️  Isolamento de Dumps de Erro: {self.log_erros_nome}")
        print(f"  📊 Metadados de Telemetria    : {self.log_stats_nome}")
        print(f"{'='*80}")
        self.console_log("SUCESSO", "Esteira finalizada e consolidada com sucesso!")

if __name__ == "__main__":
    remuxer = IndustrialRemuxerV2()
    remuxer.executar_operacao_remux()