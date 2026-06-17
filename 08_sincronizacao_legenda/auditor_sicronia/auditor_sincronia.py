#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: auditor_sincronia.py
Realiza uma auditoria avançada e inteligente de sincronia entre os fluxos de vídeo 
e as legendas embutidas em arquivos de vídeo (como MKV), calculando drift (desvio),
identificando FPS mismatch e sugerindo a correção adequada.
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path

# Inicialização do colorama para terminal colorido
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

EXTENSOES_VIDEO = ['.mkv', '.mp4', '.avi', '.mov', '.flv', '.wmv', '.webm', '.m4v']

def exibir_cabecalho():
    print(f"\n{cor_destaque}" + "=" * 80)
    print(f"{cor_info}{Back.BLACK}                 AUDITOR DE SINCRONIA DE LEGENDAS (FFPROBE)                {Style.RESET_ALL}")
    print(f"{cor_destaque}" + "=" * 80 + "\n")

def parse_duration_str(dur_str):
    """Converte string de duração (HH:MM:SS.mmm) ou segundos em float."""
    if not dur_str:
        return None
    try:
        dur_str = dur_str.replace(',', '.')
        partes = dur_str.split(':')
        if len(partes) == 3:
            h = float(partes[0])
            m = float(partes[1])
            s = float(partes[2])
            return h * 3600 + m * 60 + s
        elif len(partes) == 2:
            m = float(partes[0])
            s = float(partes[1])
            return m * 60 + s
        else:
            return float(dur_str)
    except Exception:
        return None

def format_seconds(seconds):
    """Formata segundos em HH:MM:SS.mmm."""
    if seconds is None:
        return "N/A"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"

def solicitar_caminho_usuario():
    """Solicita interativamente o caminho de arquivo ou pasta do usuário."""
    while True:
        print(f"{cor_info}COMO DESEJA LOCALIZAR O ARQUIVO OU PASTA PARA AUDITORIA?{Style.RESET_ALL}")
        print("  1. Digitar/colar o caminho completo manualmente")
        print("  2. Abrir janela para LOCALIZAR um ARQUIVO (Explorer)")
        print("  3. Abrir janela para LOCALIZAR uma PASTA (Explorer)")
        print("-" * 50)
        
        opcao = input(f"{cor_alerta}Escolha uma opção (1-3) ou cole o caminho diretamente: {Style.RESET_ALL}").strip()
        caminho_limpo = opcao.replace('"', '').replace("'", "")
        
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
                root.attributes("-topmost", True)
                caminho_selecionado = filedialog.askopenfilename(
                    title="Selecione o arquivo de vídeo para auditoria",
                    filetypes=[("Arquivos de Vídeo", "*.mkv;*.mp4;*.avi;*.mov;*.wmv;*.webm"), ("Todos os Arquivos", "*.*")]
                )
                root.destroy()
                if caminho_selecionado:
                    return Path(caminho_selecionado)
                else:
                    print(f"{cor_alerta}Seleção cancelada pelo usuário.{Style.RESET_ALL}\n")
            except Exception as e:
                print(f"{cor_erro}Erro ao abrir a janela de busca: {e}{Style.RESET_ALL}")
        elif opcao == '3':
            print(f"{cor_info}Abrindo janela de seleção de pasta...{Style.RESET_ALL}")
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                caminho_selecionado = filedialog.askdirectory(
                    title="Selecione a pasta com vídeos para auditoria"
                )
                root.destroy()
                if caminho_selecionado:
                    return Path(caminho_selecionado)
                else:
                    print(f"{cor_alerta}Seleção cancelada pelo usuário.{Style.RESET_ALL}\n")
            except Exception as e:
                print(f"{cor_erro}Erro ao abrir a janela de busca: {e}{Style.RESET_ALL}")
        else:
            if not opcao:
                print(f"{cor_erro}Erro: Opção inválida.{Style.RESET_ALL}\n")
            else:
                print(f"{cor_erro}Erro: Caminho ou opção '{opcao}' não é válido ou não existe.{Style.RESET_ALL}\n")

def obter_timestamps_legenda_via_pacotes(caminho_video, index_relativo):
    """
    Executa ffprobe nos pacotes do fluxo de legenda especificado para determinar
    a duração real do fluxo de legenda baseada no tempo do último pacote.
    """
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-select_streams", f"s:{index_relativo}",
            "-show_entries", "packet=pts_time,duration_time", "-of", "json", str(caminho_video)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0 or not res.stdout.strip():
            return None, None
        
        dados = json.loads(res.stdout)
        pacotes = dados.get("packets", [])
        if not pacotes:
            return None, None
            
        first_pts = None
        last_pts = None
        
        # Encontra o primeiro pacote com pts_time válido
        for p in pacotes:
            pts = parse_duration_str(p.get("pts_time"))
            if pts is not None:
                first_pts = pts
                break
                
        # Encontra o último pacote com pts_time válido e adiciona sua duração se disponível
        for p in reversed(pacotes):
            pts = parse_duration_str(p.get("pts_time"))
            if pts is not None:
                dur = parse_duration_str(p.get("duration_time")) or 0.0
                last_pts = pts + dur
                break
                
        return first_pts, last_pts
    except Exception:
        return None, None

def auditar_arquivo(caminho_video):
    """Analisa o arquivo de vídeo e audita todas as suas faixas de legenda."""
    print(f"{cor_info}Analisando arquivo: {caminho_video.name}{Style.RESET_ALL}")
    
    # 1. Obter informações de streams e formato via ffprobe
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(caminho_video)
    ]
    try:
        resultado = subprocess.run(cmd, capture_output=True, text=True)
        if resultado.returncode != 0:
            print(f"  {cor_erro}Erro ao executar ffprobe no arquivo.{Style.RESET_ALL}")
            return False
        dados = json.loads(resultado.stdout)
    except Exception as e:
        print(f"  {cor_erro}Erro ao ler metadados do arquivo: {e}{Style.RESET_ALL}")
        return False
        
    streams = dados.get("streams", [])
    formato = dados.get("format", {})
    
    # Encontra fluxo de vídeo principal
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    if not video_stream:
        print(f"  {cor_erro}Erro: Nenhum fluxo de vídeo encontrado.{Style.RESET_ALL}")
        return False
        
    # Extrai duração do vídeo (prioriza tags do stream de vídeo, depois duration da stream, depois duration do container)
    duracao_video = None
    if video_stream.get("tags"):
        duracao_video = parse_duration_str(video_stream.get("tags", {}).get("DURATION"))
    if not duracao_video:
        duracao_video = parse_duration_str(video_stream.get("duration"))
    if not duracao_video:
        duracao_video = parse_duration_str(formato.get("duration"))
        
    if not duracao_video:
        print(f"  {cor_erro}Erro: Não foi possível obter a duração do vídeo.{Style.RESET_ALL}")
        return False
        
    # Extrai fps do vídeo
    r_frame_rate = video_stream.get("r_frame_rate", "N/A")
    fps = "N/A"
    try:
        if "/" in r_frame_rate:
            num, den = map(float, r_frame_rate.split("/"))
            fps = num / den if den > 0 else "N/A"
        else:
            fps = float(r_frame_rate)
    except Exception:
        pass
        
    print(f"  Duracao do Video: {cor_info}{format_seconds(duracao_video)}{Style.RESET_ALL} | FPS: {cor_info}{fps if isinstance(fps, str) else f'{fps:.3f}'}{Style.RESET_ALL}")
    
    # Filtra fluxos de legenda
    sub_streams = [s for s in streams if s.get("codec_type") == "subtitle"]
    if not sub_streams:
        print(f"  {cor_alerta}Aviso: Nenhuma faixa de legenda encontrada no arquivo.{Style.RESET_ALL}\n")
        return True
        
    for idx_rel, sub in enumerate(sub_streams):
        codec = sub.get("codec_name", "desconhecido")
        idioma = sub.get("tags", {}).get("language", "desconhecido")
        titulo = sub.get("tags", {}).get("title", "Sem titulo")
        index_absoluto = sub.get("index")
        
        print(f"\n  {cor_destaque}Faixa de Legenda #{idx_rel} (Index FFmpeg: {index_absoluto}) [{idioma}] ({codec}) - \"{titulo}\":{Style.RESET_ALL}")
        
        # Tenta obter a duracao da legenda pelo metadado da stream
        duracao_legenda = parse_duration_str(sub.get("tags", {}).get("DURATION"))
        if not duracao_legenda:
            duracao_legenda = parse_duration_str(sub.get("duration"))
            
        metodo_duracao = "Metadados"
        first_pts, last_pts = None, None
        
        # Se a duracao for igual a do video/container (muitas vezes e copiada) ou estiver ausente,
        # fazemos a leitura de pacotes por seguranca.
        if not duracao_legenda or abs(duracao_legenda - duracao_video) < 0.01:
            first_pts, last_pts = obter_timestamps_legenda_via_pacotes(caminho_video, idx_rel)
            if last_pts is not None:
                duracao_legenda = last_pts
                metodo_duracao = "Analise de Pacotes (ffprobe)"
                
        if not duracao_legenda:
            print(f"    {cor_erro}Nao foi possivel calcular a duracao desta faixa de legenda.{Style.RESET_ALL}")
            continue
            
        # Calcula metricas de sincronia
        diferenca = duracao_video - duracao_legenda
        diff_abs = abs(diferenca)
        duracao_horas = duracao_video / 3600.0
        drift_ratio = diff_abs / duracao_horas if duracao_horas > 0 else 0.0
        
        print(f"    Duracao Legenda: {cor_info}{format_seconds(duracao_legenda)}{Style.RESET_ALL} (via {metodo_duracao})")
        if first_pts is not None:
            print(f"    Primeira fala:   {cor_info}{format_seconds(first_pts)}{Style.RESET_ALL} | Ultima fala: {cor_info}{format_seconds(last_pts)}{Style.RESET_ALL}")
            
        print(f"    Diferenca Fim:   {cor_info}{diferenca:+.3f}s{Style.RESET_ALL} (Video - Legenda)")
        print(f"    Taxa de Drift:   {cor_info}{drift_ratio:.3f} s/hora{Style.RESET_ALL}")
        
        # Decisao de veredito baseada em limites matematicos
        # Se for muito curta (e.g., menor que 50% da duracao do video), provavelmente e faixa parcial (forced/comentarios)
        if duracao_legenda < (duracao_video * 0.5):
            print(f"    {cor_alerta}NOTA: Legenda muito curta (tamanho < 50% do video).{Style.RESET_ALL}")
            print(f"    {cor_alerta}Provavel legenda parcial (songs/forced) ou comentarios.{Style.RESET_ALL}")
            print(f"    Veredito: {cor_sucesso}Legenda Parcial Muxed (Sem necessidade de alteracao de sync global){Style.RESET_ALL}")
        elif diff_abs <= 1.5:
            print(f"    Veredito: {cor_sucesso}Legenda Sincronizada! (Diferenca de {diff_abs:.2f}s esta dentro da margem segura){Style.RESET_ALL}")
        else:
            # Avalia se a razao de tempos e proxima a uma conversao de FPS padrao
            # Relacoes comuns de FPS:
            # 25.0 -> 23.976 (ratio ~1.0427)
            # 23.976 -> 25.0 (ratio ~0.9590)
            # 24.0 -> 23.976 (ratio ~1.0010)
            # 23.976 -> 24.0 (ratio ~0.9990)
            ratio = duracao_video / duracao_legenda
            fps_mismatch = False
            fps_destino = ""
            
            ratios_fps = [
                (1.042709, "25.000 -> 23.976 fps (Estiramento PAL para NTSC)"),
                (0.959040, "23.976 -> 25.000 fps (Estiramento NTSC para PAL)"),
                (1.001001, "24.000 -> 23.976 fps"),
                (0.999000, "23.976 -> 24.000 fps")
            ]
            
            for target_ratio, label in ratios_fps:
                if abs(ratio - target_ratio) < 0.0015:
                    fps_mismatch = True
                    fps_destino = label
                    break
                    
            if fps_mismatch:
                print(f"    Veredito: {cor_erro}Legenda Desalinhada - Necessita Estiramento de Tempo!{Style.RESET_ALL}")
                print(f"    Diagnostico: {cor_alerta}Provavel incompatibilidade de taxa de quadros (FPS mismatch).{Style.RESET_ALL}")
                print(f"    Sugestao: Aplicar estiramento de tempo (Time Stretch): {cor_info}{fps_destino}{Style.RESET_ALL}")
            else:
                # Se nao for FPS mismatch e a primeira legenda comecar deslocada, pode ser apenas offset simples
                print(f"    Veredito: {cor_erro}Legenda Desalinhada - Possivel atraso constante!{Style.RESET_ALL}")
                print(f"    Diagnostico: Diferenca de fim acumulada de {diff_abs:.2f}s.")
                # Sugere o valor de delay para o subtitle_fixer
                sugerido_ms = int(diferenca * 1000)
                print(f"    Sugestao: Executar 'subtitle_fixer.py' e usar um atraso de {cor_alerta}{sugerido_ms} ms{Style.RESET_ALL}")
                
    print("-" * 80 + "\n")
    return True

def main():
    exibir_cabecalho()
    
    parser = argparse.ArgumentParser(description="Auditor de Sincronia de Legendas via FFprobe")
    parser.add_argument("caminho", nargs="?", help="Caminho do arquivo de vídeo ou pasta")
    args = parser.parse_args()
    
    caminho = None
    if args.caminho:
        caminho = Path(args.caminho.strip('"\''))
    else:
        caminho = solicitar_caminho_usuario()
        
    if not caminho or not caminho.exists():
        print(f"{cor_erro}Caminho inválido ou inexistente.{Style.RESET_ALL}")
        sys.exit(1)
        
    arquivos = []
    if caminho.is_dir():
        print(f"{cor_info}Escaneando pasta por arquivos de vídeo...{Style.RESET_ALL}")
        for ext in EXTENSOES_VIDEO:
            arquivos.extend(caminho.glob(f"*{ext}"))
            arquivos.extend(caminho.glob(f"*{ext.upper()}"))
        arquivos = sorted(list(set(arquivos)))
    else:
        arquivos = [caminho]
        
    if not arquivos:
        print(f"{cor_erro}Nenhum arquivo de vídeo suportado encontrado.{Style.RESET_ALL}")
        sys.exit(1)
        
    print(f"{cor_sucesso}Total de arquivos para auditar: {len(arquivos)}{Style.RESET_ALL}\n")
    
    sucessos = 0
    for arq in arquivos:
        if auditar_arquivo(arq):
            sucessos += 1
            
    print(f"{cor_sucesso}Auditoria finalizada. Sucesso em {sucessos}/{len(arquivos)} arquivos.{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{cor_alerta}Operação cancelada pelo usuário.{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{cor_erro}Erro inesperado: {e}{Style.RESET_ALL}")
        sys.exit(1)