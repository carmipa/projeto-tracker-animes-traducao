#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: subtitle_stretcher.py
Realiza o estiramento de tempo (Time Stretch) matemático de arquivos de legenda (SRT e ASS)
em Python puro, sem dependências de binários ou programas externos.
"""

import os
import sys
import re
import argparse

# Inicialização de cores do terminal
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    cor_sucesso = Fore.GREEN
    cor_erro = Fore.RED
    cor_info = Fore.CYAN
    cor_alerta = Fore.YELLOW
except ImportError:
    class EmptyStyle:
        def __getattr__(self, name):
            return ""
    Fore = Style = EmptyStyle()
    cor_sucesso = cor_erro = cor_info = cor_alerta = ""

def srt_to_seconds(ts):
    """Converte timestamp SRT (HH:MM:SS,mmm) em segundos (float)."""
    try:
        h, m, s_ms = ts.split(':')
        s, ms = s_ms.split(',')
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0
    except Exception:
        raise ValueError(f"Formato de timestamp SRT inválido: '{ts}'")

def seconds_to_srt(secs):
    """Converte segundos (float) em timestamp SRT (HH:MM:SS,mmm)."""
    is_neg = False
    if secs < 0:
        is_neg = True
        secs = abs(secs)
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = int(secs % 60)
    ms = int(round((secs % 1) * 1000))
    if ms >= 1000:
        s += 1
        ms -= 1000
    if s >= 60:
        m += 1
        s -= 60
    if m >= 60:
        h += 1
        m -= 60
    sign = "-" if is_neg else ""
    return f"{sign}{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def ass_to_seconds(ts):
    """Converte timestamp ASS (H:MM:SS.cs) em segundos (float)."""
    try:
        ts = ts.strip()
        h, m, s_cs = ts.split(':')
        s, cs = s_cs.split('.')
        return int(h) * 3600 + int(m) * 60 + int(s) + int(cs) / 100.0
    except Exception:
        raise ValueError(f"Formato de timestamp ASS inválido: '{ts}'")

def seconds_to_ass(secs):
    """Converte segundos (float) em timestamp ASS (H:MM:SS.cs)."""
    is_neg = False
    if secs < 0:
        is_neg = True
        secs = abs(secs)
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = int(secs % 60)
    cs = int(round((secs % 1) * 100))
    if cs >= 100:
        s += 1
        cs -= 100
    if s >= 60:
        m += 1
        s -= 60
    if m >= 60:
        h += 1
        m -= 60
    sign = "-" if is_neg else ""
    return f"{sign}{h:d}:{m:02d}:{s:02d}.{cs:02d}"

def stretch_srt_content(content, ratio, offset=0.0):
    """Estica os timestamps em um conteúdo SRT e aplica um offset (deslocamento)."""
    pattern = re.compile(r'^(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})')
    lines = content.splitlines()
    new_lines = []
    
    for line in lines:
        match = pattern.match(line.strip())
        if match:
            start_ts, end_ts = match.groups()
            try:
                start_sec = srt_to_seconds(start_ts)
                end_sec = srt_to_seconds(end_ts)
                
                new_start_sec = start_sec * ratio + offset
                new_end_sec = end_sec * ratio + offset
                
                new_start_ts = seconds_to_srt(new_start_sec)
                new_end_ts = seconds_to_srt(new_end_sec)
                
                new_lines.append(f"{new_start_ts} --> {new_end_ts}")
            except Exception as e:
                print(f"{cor_alerta}Aviso: Falha ao processar linha de timestamp SRT '{line}': {e}{Style.RESET_ALL}")
                new_lines.append(line)
        else:
            new_lines.append(line)
            
    return "\n".join(new_lines) + "\n"

def stretch_ass_content(content, ratio, offset=0.0):
    """Estica os timestamps em um conteúdo ASS e aplica um offset (deslocamento)."""
    lines = content.splitlines()
    new_lines = []
    
    for line in lines:
        if line.strip().startswith("Dialogue:"):
            try:
                parts = line.split(',', 9)
                if len(parts) >= 3:
                    start_ts = parts[1]
                    end_ts = parts[2]
                    
                    start_sec = ass_to_seconds(start_ts)
                    end_sec = ass_to_seconds(end_ts)
                    
                    new_start_sec = start_sec * ratio + offset
                    new_end_sec = end_sec * ratio + offset
                    
                    parts[1] = seconds_to_ass(new_start_sec)
                    parts[2] = seconds_to_ass(new_end_sec)
                    
                    new_lines.append(",".join(parts))
                else:
                    new_lines.append(line)
            except Exception as e:
                print(f"{cor_alerta}Aviso: Falha ao processar linha de diálogo ASS '{line}': {e}{Style.RESET_ALL}")
                new_lines.append(line)
        else:
            new_lines.append(line)
            
    return "\n".join(new_lines) + "\n"

def stretch_file(input_path, output_path, ratio, offset=0.0):
    """Lê, aplica o estiramento + offset e salva o arquivo de legenda."""
    ext = os.path.splitext(input_path)[1].lower()
    
    try:
        with open(input_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(input_path, 'r', encoding='cp1252') as f:
            content = f.read()
            
    if ext == '.srt':
        new_content = stretch_srt_content(content, ratio, offset)
    elif ext == '.ass':
        new_content = stretch_ass_content(content, ratio, offset)
    else:
        raise ValueError(f"Extensão de arquivo de legenda não suportada: {ext}")
        
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

def main():
    parser = argparse.ArgumentParser(description="Subtitle Time Stretcher — Ajuste de Sincronia de FPS")
    parser.add_argument("--input", required=True, help="Caminho do arquivo de legenda (.srt ou .ass)")
    parser.add_argument("--output", help="Caminho do arquivo de saída (padrão: sobrescrever entrada)")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ratio", type=float, help="Fator de escala de estiramento (ex: 1.0427)")
    group.add_argument("--video-duration", type=float, help="Duração do vídeo em segundos para cálculo automático da escala")
    
    parser.add_argument("--sub-duration", type=float, help="Duração da legenda em segundos (obrigatório se usar --video-duration)")
    parser.add_argument("--offset", type=float, default=0.0, help="Deslocamento/atraso em segundos a ser somado aos tempos (Ex: -25.0)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"{cor_erro}Erro: Arquivo de entrada não existe: {args.input}{Style.RESET_ALL}")
        sys.exit(1)
        
    ratio = args.ratio
    if args.video_duration:
        if not args.sub_duration:
            print(f"{cor_erro}Erro: --sub-duration é obrigatório ao usar --video-duration.{Style.RESET_ALL}")
            sys.exit(1)
        ratio = args.video_duration / args.sub_duration
        print(f"{cor_info}Razão de estiramento calculada automaticamente: {ratio:.6f}{Style.RESET_ALL}")
        
    output_path = args.output if args.output else args.input
    
    try:
        stretch_file(args.input, output_path, ratio, args.offset)
        print(f"{cor_sucesso}Legenda ajustada com sucesso usando o fator {ratio:.6f} e offset {args.offset:+.3f}s!{Style.RESET_ALL}")
        print(f"Salva em: {output_path}")
    except Exception as e:
        print(f"{cor_erro}Erro ao esticar arquivo de legenda: {e}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
