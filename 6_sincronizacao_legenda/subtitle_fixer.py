import os
import sys
import subprocess
import datetime
from pathlib import Path

# Inicialização do colorama para terminal colorido (se disponível)
try:
    from colorama import Fore, Back, Style, init
    init(autoreset=True)
    cor_sucesso = Fore.GREEN
    cor_erro = Fore.RED
    cor_info = Fore.CYAN
    cor_alerta = Fore.YELLOW
    cor_destaque = Fore.MAGENTA
except ImportError:
    class EmptyStyle:
        def __getattr__(self, name):
            return ""
    Fore = Back = Style = EmptyStyle()
    cor_sucesso = cor_erro = cor_info = cor_alerta = cor_destaque = ""

def exibir_cabecalho():
    print(f"\n{cor_destaque}" + "=" * 80)
    print(f"{cor_info}{Back.BLACK}             CORRETOR E SINCRONIZADOR DE LEGENDAS (MKV)             {Style.RESET_ALL}")
    print(f"{cor_destaque}" + "=" * 80 + "\n")

def solicitar_caminho_arquivo():
    while True:
        print(f"{cor_info}COMO DESEJA LOCALIZAR O ARQUIVO OU PASTA?{Style.RESET_ALL}")
        print("  1. Digitar/colar o caminho completo manualmente")
        print("  2. Abrir janela para LOCALIZAR um ARQUIVO (Explorer)")
        print("  3. Abrir janela para LOCALIZAR uma PASTA (Explorer)")
        print("-" * 50)
        
        opcao = input(f"{cor_alerta}Escolha uma opção (1-3) ou cole o caminho diretamente: {Style.RESET_ALL}").strip()
        
        # Remove aspas caso o usuário tenha colado com elas
        caminho_limpo = opcao.replace('"', '').replace("'", "")
        
        # Se o input for um caminho de arquivo/pasta existente, aceita direto (comportamento inteligente)
        if caminho_limpo and Path(caminho_limpo).exists():
            return Path(caminho_limpo)
            
        if opcao == '1':
            caminho_input = input(f"\n{cor_info}Digite o caminho completo: {Style.RESET_ALL}").strip().replace('"', '').replace("'", "")
            caminho = Path(caminho_input)
            if caminho.exists():
                return caminho
            else:
                print(f"{cor_erro}Erro: O caminho informado não existe. Tente novamente.{Style.RESET_ALL}\n")
        elif opcao == '2':
            print(f"{cor_info}Abrindo janela de seleção de arquivo...{Style.RESET_ALL}")
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                # Tenta colocar a janela no topo para não ficar escondida atrás do terminal
                root.attributes("-topmost", True)
                caminho_selecionado = filedialog.askopenfilename(
                    title="Selecione o arquivo de vídeo (.mkv)",
                    filetypes=[("Arquivos MKV", "*.mkv"), ("Todos os Arquivos", "*.*")]
                )
                root.destroy()
                if caminho_selecionado:
                    caminho = Path(caminho_selecionado)
                    print(f"{cor_sucesso}Selecionado: {caminho.name}{Style.RESET_ALL}")
                    return caminho
                else:
                    print(f"{cor_alerta}Seleção cancelada pelo usuário.{Style.RESET_ALL}\n")
            except Exception as e:
                print(f"{cor_erro}Erro ao abrir a janela de busca: {e}{Style.RESET_ALL}")
                print("Por favor, forneça o caminho manualmente.")
        elif opcao == '3':
            print(f"{cor_info}Abrindo janela de seleção de pasta...{Style.RESET_ALL}")
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                caminho_selecionado = filedialog.askdirectory(
                    title="Selecione a pasta dos vídeos"
                )
                root.destroy()
                if caminho_selecionado:
                    caminho = Path(caminho_selecionado)
                    print(f"{cor_sucesso}Selecionada: {caminho}{Style.RESET_ALL}")
                    return caminho
                else:
                    print(f"{cor_alerta}Seleção cancelada pelo usuário.{Style.RESET_ALL}\n")
            except Exception as e:
                print(f"{cor_erro}Erro ao abrir a janela de busca: {e}{Style.RESET_ALL}")
                print("Por favor, forneça o caminho manualmente.")
        else:
            if not opcao:
                print(f"{cor_erro}Erro: Opção inválida. Digite 1, 2, 3 ou cole o caminho.{Style.RESET_ALL}\n")
            else:
                print(f"{cor_erro}Erro: O caminho ou opção '{opcao}' não é válido ou não existe.{Style.RESET_ALL}\n")

def obter_faixas_legenda(caminho_video):
    """
    Retorna uma lista de dicionários contendo informações das faixas de legenda encontradas no vídeo.
    """
    try:
        comando = [
            "ffprobe", "-v", "error", 
            "-select_streams", "s", 
            "-show_entries", "stream=index,codec_name:stream_tags=language,title", 
            "-of", "csv=p=0", 
            str(caminho_video)
        ]
        result = subprocess.run(comando, capture_output=True, text=True)
        if result.returncode != 0 or not result.stdout.strip():
            return []
            
        faixas = []
        linhas = result.stdout.strip().split("\n")
        for relative_idx, linha in enumerate(linhas):
            partes = [p.strip() for p in linha.split(",")]
            if not partes or partes[0] == "":
                continue
            
            absolute_index = partes[0]
            codec = partes[1] if len(partes) > 1 else "desconhecido"
            idioma = partes[2] if len(partes) > 2 and partes[2] else "Desconhecido"
            titulo = ",".join(partes[3:]) if len(partes) > 3 else "Sem título"
            if not titulo:
                titulo = "Sem título"
                
            faixas.append({
                "relative_index": relative_idx,
                "absolute_index": absolute_index,
                "codec": codec,
                "idioma": idioma,
                "titulo": titulo
            })
        return faixas
    except Exception:
        return []

def salvar_log_processamento(caminho_base, arquivo_nome, delay_ms, status, detalhes=""):
    """
    Salva o log de processamento em um arquivo txt.
    """
    caminho_log = Path(caminho_base) / "processamento_log.txt"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha_log = f"[{timestamp}] Arquivo: {arquivo_nome} | Atraso: {delay_ms} ms | Status: {status} | Detalhes: {detalhes}\n"
    
    try:
        with open(caminho_log, "a", encoding="utf-8") as f:
            f.write(linha_log)
    except Exception as e:
        print(f"{cor_erro}Aviso: Não foi possível gravar log em {caminho_log}: {e}{Style.RESET_ALL}")

def processar_arquivo(caminho):
    caminho = Path(caminho)
    pasta_raiz = caminho if caminho.is_dir() else caminho.parent
    
    # Se for pasta, pega todos os .mkv dentro dela
    if caminho.is_dir():
        print(f"\n{cor_info}Processando pasta: {caminho}{Style.RESET_ALL}")
        arquivos = sorted(list(caminho.glob("*.mkv")))
        if not arquivos:
            print(f"{cor_alerta}Nenhum arquivo .mkv encontrado nesta pasta.{Style.RESET_ALL}")
            return
    else:
        arquivos = [caminho]
        
    print(f"\n{cor_sucesso}Total de arquivos a processar: {len(arquivos)}{Style.RESET_ALL}")
    
    # Escolha do modo de sincronização
    print(f"\n{cor_info}ESCOLHA O MODO DE AJUSTE DE SINCRONIA:{Style.RESET_ALL}")
    print("  1. Atraso Constante (Simple Offset) - Desloca a legenda inteira (mkvmerge)")
    print("  2. Estiramento de Tempo (Time Stretch) - Corrige FPS mismatch (Python puro)")
    print("-" * 50)
    
    modo = input(f"{cor_alerta}Escolha uma opção (1-2) ou Pressione Enter para usar o padrão [1]: {Style.RESET_ALL}").strip()
    if not modo:
        modo = '1'
        
    delay = "0"
    fps_de = "25"
    fps_para = "23.976"
    offset_s = 0.0
    
    if modo == '1':
        delay_input = input(f"\n{cor_alerta}Digite o atraso/sincronia em milissegundos (Ex: -25000 para -25s). Pressione Enter para usar o padrão [-25000]: {Style.RESET_ALL}").strip()
        if not delay_input:
            delay = "-25000"
        else:
            delay = delay_input
        print(f"{cor_info}Usando atraso de: {delay} ms{Style.RESET_ALL}\n")
    elif modo == '2':
        # Estiramento via python puro - não requer busca por binários do Subtitle Edit
        print(f"\n{cor_info}SELECIONE A CONVERSÃO DE TAXA DE QUADROS (FPS):{Style.RESET_ALL}")
        print("  1. 25.000 -> 23.976 fps (PAL para NTSC Film - Mais comum)")
        print("  2. 23.976 -> 25.000 fps (NTSC Film para PAL)")
        print("  3. 24.000 -> 23.976 fps")
        print("  4. 23.976 -> 24.000 fps")
        print("  5. Inserir FPS de origem e destino manualmente")
        print("-" * 50)
        
        preset = input(f"{cor_alerta}Escolha uma opção (1-5) ou Pressione Enter para usar o padrão [1]: {Style.RESET_ALL}").strip()
        if not preset:
            preset = '1'
            
        if preset == '1':
            fps_de, fps_para = "25", "23.976"
        elif preset == '2':
            fps_de, fps_para = "23.976", "25"
        elif preset == '3':
            fps_de, fps_para = "24", "23.976"
        elif preset == '4':
            fps_de, fps_para = "23.976", "24"
        elif preset == '5':
            fps_de = input(f"{cor_info}Digite o FPS de ORIGEM (Ex: 25): {Style.RESET_ALL}").strip()
            fps_para = input(f"{cor_info}Digite o FPS de DESTINO (Ex: 23.976): {Style.RESET_ALL}").strip()
            
        print(f"{cor_info}Configurado estiramento de: {fps_de} fps -> {fps_para} fps{Style.RESET_ALL}\n")
        
        offset_input = input(f"{cor_alerta}Digite o atraso/offset inicial em milissegundos (Ex: -25000 para -25s). Pressione Enter para usar o padrão [0]: {Style.RESET_ALL}").strip()
        if not offset_input:
            offset_s = 0.0
        else:
            try:
                offset_s = float(offset_input) / 1000.0
            except ValueError:
                print(f"{cor_erro}Entrada inválida. Usando offset de 0.0s.{Style.RESET_ALL}")
                offset_s = 0.0
        print(f"{cor_info}Configurado offset inicial de: {offset_s:.3f} s{Style.RESET_ALL}\n")

    # Variáveis para controle de faixa no lote
    idioma_preferido_lote = None
    indice_preferido_lote = None

    for i, arquivo in enumerate(arquivos, 1):
        print(f"{cor_destaque}=" * 80)
        print(f"{cor_info}[{i}/{len(arquivos)}] Processando: {arquivo.name}{Style.RESET_ALL}")
        print(f"{cor_destaque}=" * 80)
        
        try:
            # Obter faixas de legenda do arquivo de vídeo
            faixas = obter_faixas_legenda(arquivo)
            faixa_selecionada = None
            
            if not faixas:
                map_arg = "0:s:0"
                ext = ".srt"
                titulo_novo = "Português (Sincronizado)"
                print(f"{cor_alerta}Aviso: Nenhuma faixa de legenda detectada pelo ffprobe. Tentando extrair a primeira faixa padrão.{Style.RESET_ALL}")
            else:
                if len(faixas) > 1:
                    if i == 1:
                        print(f"\n{cor_info}Múltiplas faixas de legenda encontradas em '{arquivo.name}':{Style.RESET_ALL}")
                        for idx, f in enumerate(faixas):
                            print(f"  [{idx}] Faixa #{f['relative_index']} (Codec: {f['codec']}) - Idioma: {f['idioma']} - Título: {f['titulo']}")
                        print("-" * 50)
                        
                        sugestao = 0
                        for idx, f in enumerate(faixas):
                            if any(pt in f['idioma'].lower() for pt in ['por', 'pt', 'bra', 'port']):
                                sugestao = idx
                                break
                        
                        escolha_input = input(f"{cor_alerta}Escolha o índice da legenda para sincronizar (Padrão [{sugestao}]): {Style.RESET_ALL}").strip()
                        if not escolha_input:
                            escolha = sugestao
                        else:
                            try:
                                escolha = int(escolha_input)
                                if escolha < 0 or escolha >= len(faixas):
                                    escolha = sugestao
                            except ValueError:
                                    escolha = sugestao
                                
                        faixa_selecionada = faixas[escolha]
                        idioma_preferido_lote = faixa_selecionada['idioma']
                        indice_preferido_lote = faixa_selecionada['relative_index']
                    else:
                        # Tenta obter a mesma correspondência nos próximos do lote
                        for f in faixas:
                            if f['idioma'] == idioma_preferido_lote:
                                faixa_selecionada = f
                                break
                        if not faixa_selecionada:
                            for f in faixas:
                                if f['relative_index'] == indice_preferido_lote:
                                    faixa_selecionada = f
                                    break
                        if not faixa_selecionada:
                            faixa_selecionada = faixas[0]
                else:
                    faixa_selecionada = faixas[0]
                    
                map_arg = f"0:s:{faixa_selecionada['relative_index']}"
                codec = faixa_selecionada['codec']
                ext = ".ass" if "ass" in codec.lower() else ".srt"
                titulo_novo = f"{faixa_selecionada['titulo']} (Sincronizado)"
                print(f"{cor_info}Usando legenda #{faixa_selecionada['relative_index']} [{faixa_selecionada['idioma']}] ({codec}){Style.RESET_ALL}")

            # 1. Extrair legenda
            legenda_srt = arquivo.parent / f"temp_{arquivo.stem}_legenda{ext}"
            print(f"{cor_info}[1/3] Extraindo legenda da faixa {map_arg}...{Style.RESET_ALL}")
            
            result_extrair = subprocess.run(
                ["ffmpeg", "-y", "-i", str(arquivo), "-map", map_arg, str(legenda_srt)],
                capture_output=True,
                text=True
            )
            
            if result_extrair.returncode != 0:
                erro_msg = f"Erro na extração da legenda. Code: {result_extrair.returncode}."
                print(f"{cor_erro}{erro_msg}{Style.RESET_ALL}")
                salvar_log_processamento(pasta_raiz, arquivo.name, delay if modo == '1' else f"Stretch {fps_de}->{fps_para}", "FALHA", erro_msg)
                continue
            
            # Se modo == 2, estica a legenda usando o subtitle_stretcher antes de multiplexar
            if modo == '2':
                print(f"{cor_info}[1.5/3] Aplicando estiramento de tempo (Time Stretch {fps_de} -> {fps_para} com offset {offset_s:+.3f}s) via subtitle_stretcher...{Style.RESET_ALL}")
                try:
                    # Importa localmente o motor de estiramento
                    try:
                        from subtitle_stretcher import stretch_file
                    except ImportError:
                        import sys
                        sys.path.append(str(Path(__file__).parent))
                        from subtitle_stretcher import stretch_file
                    
                    ratio = float(fps_de) / float(fps_para)
                    stretch_file(str(legenda_srt), str(legenda_srt), ratio, offset_s)
                except Exception as e:
                    erro_msg = f"Erro no estiramento da legenda: {str(e)}"
                    print(f"{cor_erro}{erro_msg}{Style.RESET_ALL}")
                    salvar_log_processamento(pasta_raiz, arquivo.name, f"Stretch {fps_de}->{fps_para} (offset {offset_s:+.3f}s)", "FALHA", erro_msg)
                    if legenda_srt.exists():
                        legenda_srt.unlink()
                    continue

            # 2. Sincronizar / Multiplexar (mkvmerge)
            saida = arquivo.parent / f"{arquivo.stem}_FIXED.mkv"
            print(f"{cor_info}[2/3] Criando arquivo sincronizado com mkvmerge...{Style.RESET_ALL}")
            
            # Comando mkvmerge básico
            comando_mkvmerge = [
                "mkvmerge", "-o", str(saida),
                "--no-subtitles", str(arquivo)
            ]
            
            # Se for atraso constante (modo 1), adiciona a flag --sync correspondente
            if modo == '1':
                comando_mkvmerge.extend([
                    "--sync", f"0:{delay}",
                    "--language", "0:por",
                    "--track-name", f"0:{titulo_novo}",
                    str(legenda_srt)
                ])
            else:
                # Estiramento de tempo já foi aplicado ao arquivo temporário de legenda
                comando_mkvmerge.extend([
                    "--language", "0:por",
                    "--track-name", f"0:{titulo_novo}",
                    str(legenda_srt)
                ])
            
            result_sinc = subprocess.run(comando_mkvmerge, capture_output=True, text=True)
            
            if result_sinc.returncode != 0:
                erro_msg = f"Erro no mkvmerge. Code: {result_sinc.returncode}. Stderr: {result_sinc.stderr.strip()}"
                print(f"{cor_erro}{erro_msg}{Style.RESET_ALL}")
                salvar_log_processamento(pasta_raiz, arquivo.name, delay if modo == '1' else f"Stretch {fps_de}->{fps_para} (offset {offset_s:+.3f}s)", "FALHA", erro_msg)
                if legenda_srt.exists():
                    legenda_srt.unlink()
                continue
            
            # 3. Limpeza
            print(f"{cor_info}[3/3] Limpando arquivos temporários...{Style.RESET_ALL}")
            if legenda_srt.exists():
                legenda_srt.unlink()
                
            print(f"{cor_sucesso}[OK] Sucesso! Arquivo gerado com sucesso:{Style.RESET_ALL}")
            print(f"   {cor_info}{saida.name}{Style.RESET_ALL}\n")
            
            log_atraso = delay if modo == '1' else f"Stretch {fps_de}->{fps_para} (offset {offset_s:+.3f}s)"
            salvar_log_processamento(pasta_raiz, arquivo.name, log_atraso, "SUCESSO", f"Legenda extraída como {ext} e sincronizada.")
            
        except Exception as e:
            erro_msg = f"Erro inesperado: {str(e)}"
            print(f"{cor_erro}{erro_msg}{Style.RESET_ALL}\n")
            salvar_log_processamento(pasta_raiz, arquivo.name, delay if modo == '1' else f"Stretch {fps_de}->{fps_para} (offset {offset_s:+.3f}s)", "FALHA", erro_msg)

if __name__ == "__main__":
    exibir_cabecalho()
    try:
        caminho = solicitar_caminho_arquivo()
        processar_arquivo(caminho)
    except KeyboardInterrupt:
        print(f"\n\n{cor_alerta}Operação cancelada pelo usuário.{Style.RESET_ALL}")
        sys.exit(0)