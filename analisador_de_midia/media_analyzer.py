#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: media_analyzer.py
Responsável por realizar uma auditoria técnica profunda em arquivos de vídeo (MKV, MP4, etc).
Ele utiliza a biblioteca pymediainfo para ler os metadados do container, fluxos de vídeo, 
áudio e legendas (incluindo detecção de legendas embudidas como PGS vs ASS).
Gera relatórios de texto detalhados na pasta 'relatorio'.
"""

import os
import sys
import time
import argparse
import datetime

try:
    from pymediainfo import MediaInfo
except ImportError:
    print("ERRO: pymediainfo nao esta instalado!")
    print("Execute: pip install pymediainfo")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    print("ERRO: tqdm nao esta instalado!")
    print("Execute: pip install tqdm")
    sys.exit(1)

try:
    from colorama import Fore, Back, Style, init
    init(autoreset=True)
except ImportError:
    print("ERRO: colorama nao esta instalado!")
    print("Execute: pip install colorama")
    sys.exit(1)


# Extensoes de video suportadas
EXTENSOES_VIDEO = ['.mkv', '.mp4', '.avi', '.mov', '.flv', '.wmv', '.webm', '.m4v', '.ts', '.m2ts']

# Pasta de relatorios
PASTA_RELATORIOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'relatorio')


def criar_pasta_relatorio():
    """
    Verifica se o diretório de relatórios existe e o cria caso necessário.
    Retorna o caminho absoluto da pasta.
    """
    if not os.path.exists(PASTA_RELATORIOS):
        os.makedirs(PASTA_RELATORIOS)
        print(f"{Fore.GREEN}Pasta de relatorios criada: {PASTA_RELATORIOS}{Style.RESET_ALL}")
    return PASTA_RELATORIOS


def encontrar_videos(caminho):
    """
    Faz a varredura (scan) recursiva de um diretório em busca de arquivos de vídeo 
    suportados (ignorando maiúsculas e minúsculas).
    Retorna uma lista ordenada com os caminhos absolutos dos vídeos encontrados.
    """
    
    if not os.path.isdir(caminho):
        print(f"{Fore.RED}Erro: Caminho nao eh uma pasta valida{Style.RESET_ALL}")
        return []
    
    arquivos_video = []
    extensoes_lower = [ext.lower() for ext in EXTENSOES_VIDEO]
    
    print(f"{Fore.CYAN}Procurando em: {caminho}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Extensoes aceitas: {', '.join(EXTENSOES_VIDEO)}{Style.RESET_ALL}\n")
    
    # Usa os.walk para ser mais robusto e case-insensitive
    for root, dirs, files in os.walk(caminho):
        for arquivo in files:
            _, ext = os.path.splitext(arquivo)
            if ext.lower() in extensoes_lower:
                caminho_completo = os.path.join(root, arquivo)
                arquivos_video.append(caminho_completo)
    
    return sorted(arquivos_video) if arquivos_video else []


def analisar_arquivo_midia(caminho_arquivo, relatorio_txt=None):
    """
    Lê a estrutura interna de um arquivo de vídeo usando MediaInfo.
    Analisa faixas de vídeo (resolução, bitrate, fps), áudio (canais, codec) 
    e legendas (tipo, idioma). Imprime o resultado formatado e colorido no terminal 
    e retorna o conteúdo estruturado para ser salvo em arquivo.
    """
    
    # Conteudo do relatorio (sem cores)
    relatorio_linhas = []
    
    # Funcao para adicionar linha ao relatorio e print colorido
    def adicionar_linha(linha_texto, cor=None, bold=False):
        relatorio_linhas.append(linha_texto)
        if cor:
            print(f"{cor}{linha_texto}{Style.RESET_ALL}")
        else:
            print(linha_texto)
    
    # Header
    print("\n" + "=" * 80)
    adicionar_linha("=" * 80)
    adicionar_linha(f"INICIANDO AUDITORIA TECNICA: {os.path.basename(caminho_arquivo)}")
    print(f"{Fore.CYAN}{Back.BLACK}INICIANDO AUDITORIA TECNICA: {os.path.basename(caminho_arquivo)}{Style.RESET_ALL}")
    adicionar_linha("=" * 80)
    print("=" * 80)
    
    # Validacao 1: Arquivo existe?
    if not os.path.exists(caminho_arquivo):
        adicionar_linha("\nERRO CRITICO: Arquivo nao encontrado")
        print(f"\n{Fore.RED}ERRO CRITICO: Arquivo nao encontrado{Style.RESET_ALL}")
        adicionar_linha(f"Caminho: {caminho_arquivo}")
        print(f"{Fore.YELLOW}Caminho: {caminho_arquivo}{Style.RESET_ALL}")
        return False, relatorio_linhas
    
    # Validacao 2: eh um arquivo?
    if not os.path.isfile(caminho_arquivo):
        adicionar_linha("\nERRO: O caminho informado nao eh um arquivo valido")
        print(f"\n{Fore.RED}ERRO: O caminho informado nao eh um arquivo valido{Style.RESET_ALL}")
        adicionar_linha(caminho_arquivo)
        print(f"{Fore.YELLOW}{caminho_arquivo}{Style.RESET_ALL}")
        return False, relatorio_linhas
    
    # Validacao 3: Arquivo tem permissao de leitura?
    if not os.access(caminho_arquivo, os.R_OK):
        adicionar_linha("\nERRO: Sem permissao para ler o arquivo")
        print(f"\n{Fore.RED}ERRO: Sem permissao para ler o arquivo{Style.RESET_ALL}")
        adicionar_linha("Verifique as permissoes de acesso")
        print(f"{Fore.YELLOW}Verifique as permissoes de acesso{Style.RESET_ALL}")
        return False, relatorio_linhas
    
    # Validacao 4: Tamanho do arquivo
    try:
        tamanho_bytes = os.path.getsize(caminho_arquivo)
        tamanho_mb = tamanho_bytes / (1024**2)
        tamanho_gb = tamanho_bytes / (1024**3)
        
        if tamanho_mb < 1:
            adicionar_linha(f"\nAVISO: Arquivo muito pequeno ({tamanho_mb:.2f} MB)")
            print(f"\n{Fore.YELLOW}AVISO: Arquivo muito pequeno ({tamanho_mb:.2f} MB){Style.RESET_ALL}")
            adicionar_linha("Pode nao ser um arquivo de midia valido")
            print(f"{Fore.YELLOW}Pode nao ser um arquivo de midia valido{Style.RESET_ALL}")
        
        adicionar_linha("\nValidacao OK")
        print(f"\n{Fore.GREEN}Validacao OK{Style.RESET_ALL}")
        adicionar_linha(f"Tamanho: {tamanho_gb:.2f} GiB ({tamanho_mb:.0f} MB)")
        print(f"{Fore.CYAN}Tamanho: {tamanho_gb:.2f} GiB ({tamanho_mb:.0f} MB){Style.RESET_ALL}")
        
    except Exception as e:
        adicionar_linha(f"\nERRO ao verificar tamanho: {str(e)}")
        print(f"\n{Fore.RED}ERRO ao verificar tamanho: {str(e)}{Style.RESET_ALL}")
        return False, relatorio_linhas
    
    # LEITURA E PARSING DO ARQUIVO
    adicionar_linha("\nLendo metadados do arquivo...")
    print(f"\n{Fore.CYAN}Lendo metadados do arquivo...{Style.RESET_ALL}")
    
    try:
        with tqdm(total=100, desc="Parsing", bar_format='{l_bar}{bar}| {n_fmt}%', ncols=80) as pbar:
            for i in range(40):
                time.sleep(0.01)
                pbar.update(1)
            
            media_info = MediaInfo.parse(caminho_arquivo)
            
            for i in range(60):
                time.sleep(0.01)
                pbar.update(1)
        
        adicionar_linha("Arquivo lido com sucesso\n")
        print(f"{Fore.GREEN}Arquivo lido com sucesso{Style.RESET_ALL}\n")
        
    except Exception as e:
        adicionar_linha(f"\nERRO ao ler arquivo: {str(e)}")
        print(f"\n{Fore.RED}ERRO ao ler arquivo: {str(e)}{Style.RESET_ALL}")
        adicionar_linha("Arquivo pode estar corrompido ou nao eh um arquivo de midia valido")
        print(f"{Fore.YELLOW}Arquivo pode estar corrompido ou nao eh um arquivo de midia valido{Style.RESET_ALL}")
        return False, relatorio_linhas
    
    # VALIDACAO DE FAIXAS
    if not media_info.tracks:
        adicionar_linha("ERRO: Nenhuma faixa encontrada no arquivo")
        print(f"{Fore.RED}ERRO: Nenhuma faixa encontrada no arquivo{Style.RESET_ALL}")
        adicionar_linha("Arquivo pode estar vazio ou corrompido")
        print(f"{Fore.YELLOW}Arquivo pode estar vazio ou corrompido{Style.RESET_ALL}")
        return False, relatorio_linhas
    
    total_tracks = len(media_info.tracks)
    adicionar_linha(f"{total_tracks} faixa(s) detectada(s)\n")
    print(f"{Fore.GREEN}{total_tracks} faixa(s) detectada(s){Style.RESET_ALL}\n")
    
    # ANALISE DAS FAIXAS
    adicionar_linha("Analisando faixas de midia...\n")
    print(f"{Fore.CYAN}Analisando faixas de midia...{Style.RESET_ALL}\n")
    
    faixas_geral = []
    faixas_video = []
    faixas_audio = []
    faixas_legendas = []
    
    try:
        with tqdm(total=total_tracks, desc="Analise", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}', ncols=80) as pbar:
            for track in media_info.tracks:
                try:
                    if track.track_type == "General":
                        faixas_geral.append(track)
                    elif track.track_type == "Video":
                        faixas_video.append(track)
                    elif track.track_type == "Audio":
                        faixas_audio.append(track)
                    elif track.track_type == "Text":
                        faixas_legendas.append(track)
                except Exception as e:
                    adicionar_linha(f"Aviso - Erro ao processar faixa: {str(e)}")
                    print(f"{Fore.YELLOW}Aviso - Erro ao processar faixa: {str(e)}{Style.RESET_ALL}")
                
                pbar.update(1)
    
    except Exception as e:
        adicionar_linha(f"\nERRO durante analise: {str(e)}")
        print(f"\n{Fore.RED}ERRO durante analise: {str(e)}{Style.RESET_ALL}")
        return False, relatorio_linhas
    
    # EXIBICAO FORMATADA DOS DADOS
    
    print("\n" + "=" * 80)
    adicionar_linha("\n" + "=" * 80)
    adicionar_linha("ESTRUTURA GERAL")
    print(f"{Fore.MAGENTA}{Back.BLACK}ESTRUTURA GERAL{Style.RESET_ALL}")
    adicionar_linha("=" * 80)
    print("=" * 80)
    
    if faixas_geral:
        track = faixas_geral[0]
        try:
            adicionar_linha("\nFormato do Conteiner")
            print(f"\n{Fore.CYAN}Formato do Conteiner{Style.RESET_ALL}")
            adicionar_linha(f"  {track.format if track.format else 'N/A'}")
            print(f"  {Fore.WHITE}{track.format if track.format else 'N/A'}{Style.RESET_ALL}")
            
            adicionar_linha("\nTamanho do Arquivo")
            print(f"\n{Fore.CYAN}Tamanho do Arquivo{Style.RESET_ALL}")
            tamanho_gib = track.file_size / (1024**3) if track.file_size else None
            if tamanho_gib:
                adicionar_linha(f"  {tamanho_gib:.2f} GiB")
                print(f"  {Fore.WHITE}{tamanho_gib:.2f} GiB{Style.RESET_ALL}")
            else:
                adicionar_linha("  N/A")
                print("  N/A")
            
            adicionar_linha("\nDuracao Total")
            print(f"\n{Fore.CYAN}Duracao Total{Style.RESET_ALL}")
            duracao = track.other_duration[0] if track.other_duration else 'N/A'
            adicionar_linha(f"  {duracao}")
            print(f"  {Fore.WHITE}{duracao}{Style.RESET_ALL}")
            
            adicionar_linha("\nBitrate Geral")
            print(f"\n{Fore.CYAN}Bitrate Geral{Style.RESET_ALL}")
            bitrate = track.overall_bit_rate / 1000 if track.overall_bit_rate else None
            if bitrate:
                adicionar_linha(f"  {bitrate:.0f} kbps")
                print(f"  {Fore.WHITE}{bitrate:.0f} kbps{Style.RESET_ALL}")
            else:
                adicionar_linha("  N/A")
                print("  N/A")
            
            adicionar_linha("\nAplicacao de Escrita")
            print(f"\n{Fore.CYAN}Aplicacao de Escrita{Style.RESET_ALL}")
            app = track.writing_application if track.writing_application else 'Desconhecida'
            adicionar_linha(f"  {app}")
            print(f"  {Fore.WHITE}{app}{Style.RESET_ALL}")
        except Exception as e:
            adicionar_linha(f"  Aviso - Erro ao processar: {str(e)}")
            print(f"  {Fore.YELLOW}Aviso - Erro ao processar: {str(e)}{Style.RESET_ALL}")
    else:
        adicionar_linha("\n  Nenhuma informacao geral encontrada")
        print(f"\n  {Fore.YELLOW}Nenhuma informacao geral encontrada{Style.RESET_ALL}")
    
    # FLUXOS DE VIDEO
    
    print("\n" + "=" * 80)
    adicionar_linha("\n" + "=" * 80)
    adicionar_linha("FLUXOS DE VIDEO")
    print(f"{Fore.MAGENTA}{Back.BLACK}FLUXOS DE VIDEO{Style.RESET_ALL}")
    adicionar_linha("=" * 80)
    print("=" * 80)
    
    if faixas_video:
        for idx, track in enumerate(faixas_video, 1):
            try:
                adicionar_linha(f"\n  Fluxo {idx} (Track ID: {track.track_id if track.track_id else 'N/A'})")
                print(f"\n  {Fore.LIGHTBLUE_EX}Fluxo {idx} (Track ID: {track.track_id if track.track_id else 'N/A'}){Style.RESET_ALL}")
                
                codec_id = track.codec_id if track.codec_id else 'N/A'
                codec_format = track.format if track.format else 'N/A'
                adicionar_linha(f"    Codec: {codec_id} ({codec_format})")
                print(f"    {Fore.CYAN}Codec:{Style.RESET_ALL} {Fore.WHITE}{codec_id} ({codec_format}){Style.RESET_ALL}")
                
                if track.width and track.height:
                    adicionar_linha(f"    Resolucao: {track.width}x{track.height}p")
                    print(f"    {Fore.CYAN}Resolucao:{Style.RESET_ALL} {Fore.WHITE}{track.width}x{track.height}p{Style.RESET_ALL}")
                else:
                    adicionar_linha("    Resolucao: N/A")
                    print(f"    {Fore.CYAN}Resolucao:{Style.RESET_ALL} N/A")
                
                if track.bit_depth:
                    adicionar_linha(f"    Profundidade de Cor: {track.bit_depth} bits")
                    print(f"    {Fore.CYAN}Profundidade de Cor:{Style.RESET_ALL} {Fore.WHITE}{track.bit_depth} bits{Style.RESET_ALL}")
                else:
                    adicionar_linha("    Profundidade de Cor: N/A")
                    print(f"    {Fore.CYAN}Profundidade de Cor:{Style.RESET_ALL} N/A")
                
                if track.frame_rate:
                    adicionar_linha(f"    Taxa de Quadros (FPS): {track.frame_rate} fps")
                    print(f"    {Fore.CYAN}Taxa de Quadros (FPS):{Style.RESET_ALL} {Fore.WHITE}{track.frame_rate} fps{Style.RESET_ALL}")
                else:
                    adicionar_linha("    Taxa de Quadros (FPS): N/A")
                    print(f"    {Fore.CYAN}Taxa de Quadros (FPS):{Style.RESET_ALL} N/A")
                
                if track.display_aspect_ratio:
                    adicionar_linha(f"    Aspect Ratio: {track.display_aspect_ratio}")
                    print(f"    {Fore.CYAN}Aspect Ratio:{Style.RESET_ALL} {Fore.WHITE}{track.display_aspect_ratio}{Style.RESET_ALL}")
                else:
                    adicionar_linha("    Aspect Ratio: N/A")
                    print(f"    {Fore.CYAN}Aspect Ratio:{Style.RESET_ALL} N/A")
                
                if track.bit_rate:
                    bitrate_video = track.bit_rate / 1000
                    adicionar_linha(f"    Bitrate: {bitrate_video:.0f} kbps")
                    print(f"    {Fore.CYAN}Bitrate:{Style.RESET_ALL} {Fore.WHITE}{bitrate_video:.0f} kbps{Style.RESET_ALL}")
                else:
                    adicionar_linha("    Bitrate: N/A")
                    print(f"    {Fore.CYAN}Bitrate:{Style.RESET_ALL} N/A")
            except Exception as e:
                adicionar_linha(f"    Aviso - Erro ao processar video: {str(e)}")
                print(f"    {Fore.YELLOW}Aviso - Erro ao processar video: {str(e)}{Style.RESET_ALL}")
    else:
        adicionar_linha("\n  Nenhum fluxo de video encontrado")
        print(f"\n  {Fore.YELLOW}Nenhum fluxo de video encontrado{Style.RESET_ALL}")
    
    # FLUXOS DE AUDIO
    
    print("\n" + "=" * 80)
    adicionar_linha("\n" + "=" * 80)
    adicionar_linha("FLUXOS DE AUDIO")
    print(f"{Fore.MAGENTA}{Back.BLACK}FLUXOS DE AUDIO{Style.RESET_ALL}")
    adicionar_linha("=" * 80)
    print("=" * 80)
    
    if faixas_audio:
        for idx, track in enumerate(faixas_audio, 1):
            try:
                adicionar_linha(f"\n  Fluxo {idx} (Track ID: {track.track_id if track.track_id else 'N/A'})")
                print(f"\n  {Fore.LIGHTGREEN_EX}Fluxo {idx} (Track ID: {track.track_id if track.track_id else 'N/A'}){Style.RESET_ALL}")
                
                idioma = track.language if track.language else 'Desconhecido'
                adicionar_linha(f"    Idioma: {idioma}")
                print(f"    {Fore.CYAN}Idioma:{Style.RESET_ALL} {Fore.WHITE}{idioma}{Style.RESET_ALL}")
                
                codec = track.format if track.format else 'N/A'
                adicionar_linha(f"    Codec/Formato: {codec}")
                print(f"    {Fore.CYAN}Codec/Formato:{Style.RESET_ALL} {Fore.WHITE}{codec}{Style.RESET_ALL}")
                
                canais = track.channel_s if track.channel_s else 'N/A'
                adicionar_linha(f"    Canais: {canais}")
                print(f"    {Fore.CYAN}Canais:{Style.RESET_ALL} {Fore.WHITE}{canais}{Style.RESET_ALL}")
                
                if track.sampling_rate:
                    taxa_amostragem = track.sampling_rate / 1000
                    adicionar_linha(f"    Taxa de Amostragem: {taxa_amostragem:.1f} kHz")
                    print(f"    {Fore.CYAN}Taxa de Amostragem:{Style.RESET_ALL} {Fore.WHITE}{taxa_amostragem:.1f} kHz{Style.RESET_ALL}")
                else:
                    adicionar_linha("    Taxa de Amostragem: N/A")
                    print(f"    {Fore.CYAN}Taxa de Amostragem:{Style.RESET_ALL} N/A")
                
                if track.bit_rate:
                    bitrate_audio = track.bit_rate / 1000
                    adicionar_linha(f"    Bitrate: {bitrate_audio:.0f} kbps")
                    print(f"    {Fore.CYAN}Bitrate:{Style.RESET_ALL} {Fore.WHITE}{bitrate_audio:.0f} kbps{Style.RESET_ALL}")
                else:
                    adicionar_linha("    Bitrate: N/A")
                    print(f"    {Fore.CYAN}Bitrate:{Style.RESET_ALL} N/A")
                
                if track.title:
                    adicionar_linha(f"    Titulo: {track.title}")
                    print(f"    {Fore.CYAN}Titulo:{Style.RESET_ALL} {Fore.WHITE}{track.title}{Style.RESET_ALL}")
                else:
                    adicionar_linha("    Titulo: (Sem titulo)")
                    print(f"    {Fore.CYAN}Titulo:{Style.RESET_ALL} (Sem titulo)")
            except Exception as e:
                adicionar_linha(f"    Aviso - Erro ao processar audio: {str(e)}")
                print(f"    {Fore.YELLOW}Aviso - Erro ao processar audio: {str(e)}{Style.RESET_ALL}")
    else:
        adicionar_linha("\n  Nenhum fluxo de audio encontrado")
        print(f"\n  {Fore.YELLOW}Nenhum fluxo de audio encontrado{Style.RESET_ALL}")
    
    # FAIXAS DE LEGENDAS
    
    print("\n" + "=" * 80)
    adicionar_linha("\n" + "=" * 80)
    adicionar_linha("FAIXAS DE LEGENDAS")
    print(f"{Fore.MAGENTA}{Back.BLACK}FAIXAS DE LEGENDAS{Style.RESET_ALL}")
    adicionar_linha("=" * 80)
    print("=" * 80)
    
    if faixas_legendas:
        for idx, track in enumerate(faixas_legendas, 1):
            try:
                adicionar_linha(f"\n  Legenda {idx} (Track ID: {track.track_id if track.track_id else 'N/A'})")
                print(f"\n  {Fore.LIGHTYELLOW_EX}Legenda {idx} (Track ID: {track.track_id if track.track_id else 'N/A'}){Style.RESET_ALL}")
                
                idioma = track.language if track.language else 'Desconhecido'
                adicionar_linha(f"    Idioma: {idioma}")
                print(f"    {Fore.CYAN}Idioma:{Style.RESET_ALL} {Fore.WHITE}{idioma}{Style.RESET_ALL}")
                
                formato = track.format if track.format else 'N/A'
                adicionar_linha(f"    Formato: {formato}")
                print(f"    {Fore.CYAN}Formato:{Style.RESET_ALL} {Fore.WHITE}{formato}{Style.RESET_ALL}")
                
                codec_id = track.codec_id if track.codec_id else 'N/A'
                
                if codec_id == 'S_TEXT/ASS' or codec_id == 'S_TEXT/SSA':
                    tipo = 'ASS/SSA (Estilizada com cores e posicionamento)'
                    cor_tipo = Fore.YELLOW
                elif codec_id == 'S_TEXT/UTF8' or codec_id == 'S_TEXT/SUBRIP' or 'SRT' in formato.upper():
                    tipo = 'SRT/SubRip (Simples - Recomendado para traducao)'
                    cor_tipo = Fore.GREEN
                elif codec_id and 'PGS' in codec_id.upper():
                    tipo = 'PGS (Bitmap - Hardsub - Nao extraivel)'
                    cor_tipo = Fore.RED
                elif codec_id == 'In_Screen':
                    tipo = 'Hardsub (Queimada na tela - Nao extraivel)'
                    cor_tipo = Fore.RED
                else:
                    tipo = 'Desconhecido'
                    cor_tipo = Fore.WHITE
                
                adicionar_linha(f"    Tipo: {tipo}")
                print(f"    {Fore.CYAN}Tipo:{Style.RESET_ALL} {cor_tipo}{tipo}{Style.RESET_ALL}")
                adicionar_linha(f"    Codec ID: {codec_id}")
                print(f"    {Fore.CYAN}Codec ID:{Style.RESET_ALL} {Fore.WHITE}{codec_id}{Style.RESET_ALL}")
                
                if track.title:
                    adicionar_linha(f"    Titulo: {track.title}")
                    print(f"    {Fore.CYAN}Titulo:{Style.RESET_ALL} {Fore.WHITE}{track.title}{Style.RESET_ALL}")
                else:
                    adicionar_linha("    Titulo: (Sem titulo)")
                    print(f"    {Fore.CYAN}Titulo:{Style.RESET_ALL} (Sem titulo)")
            except Exception as e:
                adicionar_linha(f"    Aviso - Erro ao processar legenda: {str(e)}")
                print(f"    {Fore.YELLOW}Aviso - Erro ao processar legenda: {str(e)}{Style.RESET_ALL}")
    else:
        adicionar_linha("\n    NENHUMA LEGENDA ENCONTRADA")
        print(f"\n    {Fore.RED}NENHUMA LEGENDA ENCONTRADA{Style.RESET_ALL}")
        adicionar_linha("    - Arquivo eh uma RAW (sem legenda)")
        print(f"    {Fore.YELLOW}- Arquivo eh uma RAW (sem legenda){Style.RESET_ALL}")
        adicionar_linha("    - Ou a legenda esta com HARDSUB (queimada na imagem)")
        print(f"    {Fore.YELLOW}- Ou a legenda esta com HARDSUB (queimada na imagem){Style.RESET_ALL}")
        adicionar_linha("    - Verifique o arquivo antes de usar no pipeline")
        print(f"    {Fore.YELLOW}- Verifique o arquivo antes de usar no pipeline{Style.RESET_ALL}")
    
    # RESUMO FINAL
    
    print("\n" + "=" * 80)
    adicionar_linha("\n" + "=" * 80)
    adicionar_linha("RESUMO FINAL")
    print(f"{Fore.MAGENTA}{Back.BLACK}RESUMO FINAL{Style.RESET_ALL}")
    adicionar_linha("=" * 80)
    print("=" * 80)
    
    adicionar_linha(f"\n  Total de Faixas: {total_tracks}")
    print(f"\n  {Fore.CYAN}Total de Faixas:{Style.RESET_ALL} {Fore.WHITE}{total_tracks}{Style.RESET_ALL}")
    adicionar_linha(f"    Video(s): {len(faixas_video)}")
    print(f"    {Fore.LIGHTBLUE_EX}Video(s):{Style.RESET_ALL} {Fore.WHITE}{len(faixas_video)}{Style.RESET_ALL}")
    adicionar_linha(f"    Audio(s): {len(faixas_audio)}")
    print(f"    {Fore.LIGHTGREEN_EX}Audio(s):{Style.RESET_ALL} {Fore.WHITE}{len(faixas_audio)}{Style.RESET_ALL}")
    adicionar_linha(f"    Legenda(s): {len(faixas_legendas)}")
    print(f"    {Fore.LIGHTYELLOW_EX}Legenda(s):{Style.RESET_ALL} {Fore.WHITE}{len(faixas_legendas)}{Style.RESET_ALL}")
    
    print("\n" + "=" * 80)
    adicionar_linha("\n" + "=" * 80)
    adicionar_linha("Auditoria finalizada com sucesso!")
    print(f"{Fore.GREEN}Auditoria finalizada com sucesso!{Style.RESET_ALL}")
    adicionar_linha("=" * 80)
    print("=" * 80 + "\n")
    
    return True, relatorio_linhas


def salvar_relatorio(relatorio_linhas, nome_arquivo):
    """
    Grava as linhas geradas pelo 'analisar_arquivo_midia' em um arquivo de texto 
    na pasta de relatórios, incluindo um timestamp no nome para evitar sobrescrita.
    """
    
    pasta = criar_pasta_relatorio()
    
    # Cria nome do arquivo com timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_base = os.path.splitext(nome_arquivo)[0]
    arquivo_relatorio = os.path.join(pasta, f"{nome_base}_{timestamp}.txt")
    
    try:
        with open(arquivo_relatorio, 'w', encoding='utf-8') as f:
            f.write('\n'.join(relatorio_linhas))
        
        print(f"{Fore.GREEN}Relatorio salvo em:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{arquivo_relatorio}{Style.RESET_ALL}\n")
        return arquivo_relatorio
        
    except Exception as e:
        print(f"{Fore.RED}Erro ao salvar relatorio: {str(e)}{Style.RESET_ALL}\n")
        return None


def main():
    """
    Ponto de entrada do script. Lida com argumentos de linha de comando ou 
    pede o caminho interativamente. Controla o loop de processamento para 
    análise em lote de vários arquivos.
    """
    
    parser = argparse.ArgumentParser(
        description='Media Analyzer - Analisador de arquivos de midia',
        add_help=True
    )
    
    parser.add_argument(
        'caminho',
        nargs='?',
        default=None,
        help='Caminho do arquivo OU pasta com videos'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Modo verbose com mais detalhes'
    )
    
    args = parser.parse_args()
    
    caminho_usuario = None
    arquivos_analisar = []
    
    if args.caminho:
        caminho_usuario = args.caminho.strip('"\'')
        print("\n" + "=" * 80)
        print(f"{Fore.CYAN}{Back.BLACK}MEDIA ANALYZER - Modo: Linha de Comando{Style.RESET_ALL}")
        print("=" * 80)
        if args.verbose:
            print(f"{Fore.YELLOW}Caminho recebido: {caminho_usuario}{Style.RESET_ALL}")
    else:
        print("\n" + "=" * 80)
        print(f"{Fore.CYAN}{Back.BLACK}MEDIA ANALYZER - Modo: Interativo{Style.RESET_ALL}")
        print("=" * 80)
        print(f"\n{Fore.YELLOW}Dica: python media_analyzer.py \"C:\\caminho\\pasta_ou_arquivo\"{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}      python media_analyzer.py \"C:\\caminho\\arquivo.mkv\"{Style.RESET_ALL}\n")
        
        caminho_usuario = input(f"{Fore.CYAN}Digite o caminho da pasta ou arquivo:{Style.RESET_ALL} ").strip('"\'')
    
    if not caminho_usuario or caminho_usuario.strip() == '':
        print(f"\n{Fore.RED}ERRO: Nenhum caminho fornecido!{Style.RESET_ALL}")
        sys.exit(1)
    
    # Verifica se eh pasta ou arquivo
    if os.path.isdir(caminho_usuario):
        print(f"\n{Fore.GREEN}Pasta detectada{Style.RESET_ALL}\n")
        
        arquivos_analisar = encontrar_videos(caminho_usuario)
        
        if not arquivos_analisar:
            print(f"\n{Fore.RED}ERRO: Nenhum arquivo de video encontrado na pasta!{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Extensoes suportadas: {', '.join(EXTENSOES_VIDEO)}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Caminho procurado: {caminho_usuario}{Style.RESET_ALL}")
            sys.exit(1)
        
        print(f"\n{Fore.GREEN}Encontrados {len(arquivos_analisar)} arquivo(s) de video:{Style.RESET_ALL}\n")
        for idx, arquivo in enumerate(arquivos_analisar, 1):
            print(f"  {Fore.CYAN}{idx}.{Style.RESET_ALL} {Fore.WHITE}{os.path.basename(arquivo)}{Style.RESET_ALL}")
        print()
        
    elif os.path.isfile(caminho_usuario):
        print(f"\n{Fore.GREEN}Arquivo detectado:{Style.RESET_ALL} {Fore.CYAN}{os.path.basename(caminho_usuario)}{Style.RESET_ALL}\n")
        arquivos_analisar = [caminho_usuario]
        
    else:
        print(f"\n{Fore.RED}ERRO: Caminho nao eh um arquivo ou pasta valida!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Caminho: {caminho_usuario}{Style.RESET_ALL}")
        sys.exit(1)
    
    # Analisa cada arquivo
    total_arquivos = len(arquivos_analisar)
    
    for idx, arquivo in enumerate(arquivos_analisar, 1):
        print(f"\n{Fore.MAGENTA}[{idx}/{total_arquivos}] Analisando...{Style.RESET_ALL}")
        sucesso, relatorio_linhas = analisar_arquivo_midia(arquivo)
        
        # Salva relatorio se analise foi sucesso
        if sucesso:
            salvar_relatorio(relatorio_linhas, os.path.basename(arquivo))
        
        if not sucesso and total_arquivos == 1:
            sys.exit(1)
        
        if idx < total_arquivos:
            input(f"{Fore.CYAN}Pressione Enter para analisar o proximo arquivo...{Style.RESET_ALL}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Analise cancelada pelo usuario{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}ERRO INESPERADO: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)