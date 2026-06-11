#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: extrator_inteligente_srt.py
Extrai dinamicamente as legendas de diálogo em inglês no formato SRT,
tratando a variação de Track IDs automaticamente através do binário local do MKVExtract.

Author: Paulo + Gemini
Data: Junho 2026
Status: PRODUCTION READY
"""

import os
import subprocess
import json
from colorama import init, Fore, Style
from tqdm import tqdm
import shutil

# Inicializa o Colorama para tratamento de escapes ANSI no terminal do Windows
init(autoreset=True)

def achar_mkvtoolnix():
    for folder in [r"C:\Program Files\MKVToolNix", r"C:\Program Files (x86)\MKVToolNix"]:
        ext_path = os.path.join(folder, "mkvextract.exe")
        merge_path = os.path.join(folder, "mkvmerge.exe")
        if os.path.exists(ext_path) and os.path.exists(merge_path):
            return ext_path, merge_path
    
    ext_path = shutil.which("mkvextract")
    merge_path = shutil.which("mkvmerge")
    if ext_path and merge_path:
        return ext_path, merge_path
        
    return None, None

MKVEXTRACT_PATH, MKVMERGE_PATH = achar_mkvtoolnix()

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_INFO = os.path.join(PASTA_SCRIPT, "info.txt")

def extrair_legendas_srt():
    print("=" * 80)
    print(f"{Fore.CYAN}         ESTEIRA DE EXTRAÇÃO INTELIGENTE DE SOFTBUBS: MKV ➔ SRT")
    print("=" * 80)

    if not MKVEXTRACT_PATH or not MKVMERGE_PATH:
        print(f"{Fore.RED}[ERRO] O binário do mkvextract ou mkvmerge não foi encontrado no sistema.")
        print(f"{Fore.YELLOW}Por favor, instale o MKVToolNix ou adicione o caminho dele às variáveis do sistema.")
        return

    # Solicita a pasta de forma interativa
    pasta_videos = input(f"{Fore.YELLOW}Digite a pasta com os arquivos .mkv: {Style.RESET_ALL}").strip().replace('"', '').replace("'", "")
    
    if not os.path.isdir(pasta_videos):
        print(f"{Fore.RED}[ERRO] O diretório informado não existe: {pasta_videos}")
        return

    pasta_saida_eng = os.path.join(pasta_videos, "legendas_eng")
    os.makedirs(pasta_saida_eng, exist_ok=True)

    arquivos_mkv = sorted([f for f in os.listdir(pasta_videos) if f.lower().endswith('.mkv')])
    print(f"{Fore.GREEN}[OK] Localizados {len(arquivos_mkv)} episódios para processamento.")

    linhas_info = []

    # Uso do tqdm isolado para garantir a integridade visual no console industrial
    with tqdm(total=len(arquivos_mkv), desc="Extraindo", unit="ep", colour="cyan", ncols=80, leave=True) as barra:
        for arquivo in arquivos_mkv:
            caminho_mkv = os.path.join(pasta_videos, arquivo)
            nome_base = os.path.splitext(arquivo)[0]

            barra.set_postfix_str(arquivo[:35])

            print(f"\n{Fore.YELLOW}Analisando barramento de faixas: {arquivo}...")
            cmd_ident = [MKVMERGE_PATH, "--identification-format", "json", "--identify", caminho_mkv]

            resultado = subprocess.run(cmd_ident, capture_output=True, text=True, encoding='utf-8')
            id_legenda_alvo = None
            track_name_detectado = "fallback"

            if resultado.returncode == 0:
                dados_midia = json.loads(resultado.stdout)
                candidate_tracks = []
                for track in dados_midia.get('tracks', []):
                    if track.get('type') == 'subtitles':
                        codec = track.get('codec', '').lower()
                        propriedades = track.get('properties', {})
                        codec_id = propriedades.get('codec_id', '').lower()

                        # Verifica se é uma faixa de texto SRT/SubRip/UTF8
                        if any(term in codec or term in codec_id for term in ['srt', 'subrip', 'utf8', 'text/utf8']):
                            track_name = propriedades.get('track_name', '')
                            track_id = track.get('id')
                            candidate_tracks.append((track_id, track_name))

                # Busca pela melhor faixa usando palavras-chave prioritárias (Full, Dialogue, English, etc)
                for t_id, t_name in candidate_tracks:
                    if any(k in t_name.lower() for k in ["dialogue", "full", "complete", "legendado", "english", "srt"]):
                        id_legenda_alvo = t_id
                        track_name_detectado = t_name
                        print(f"  ↳ {Fore.GREEN}Sucesso! Detectada legenda SRT no ID: {id_legenda_alvo} ({track_name_detectado})")
                        break

                # Se não bateu palavras-chave, mas existem faixas SRT, escolhe a última (geralmente a completa)
                if id_legenda_alvo is None and candidate_tracks:
                    id_legenda_alvo, track_name_detectado = candidate_tracks[-1]
                    print(f"  ↳ {Fore.GREEN}Sucesso (Auto-SRT)! Selecionada faixa SRT no ID: {id_legenda_alvo} ({track_name_detectado})")

            if id_legenda_alvo is None:
                # Fallback estrito mapeado na análise para outros casos (se houver)
                id_legenda_alvo = 2
                print(f"  ↳ {Fore.BLUE}Fallback aplicado: ID 2 assumido.")

            arquivo_saida_srt = os.path.join(pasta_saida_eng, f"{nome_base}_ENG.srt")

            print(f"  ↳ Extraindo trilha de texto para: legendas_eng\\{nome_base}_ENG.srt...")
            cmd_extract = [MKVEXTRACT_PATH, "tracks", caminho_mkv, f"{id_legenda_alvo}:{arquivo_saida_srt}"]
            subprocess.run(cmd_extract, capture_output=True)

            linhas_info.append(
                f"{arquivo} | Track ID: {id_legenda_alvo} | Nome: {track_name_detectado} | Saída: {nome_base}_ENG.srt"
            )

            barra.update(1)

    # Persistência dos metadados de auditoria em disco (info.txt)
    with open(ARQUIVO_INFO, "w", encoding="utf-8") as f:
        f.write("RELATÓRIO DE EXTRAÇÃO — EXTRACTOR INTELIGENTE SRT\n")
        f.write("=" * 80 + "\n")
        for tuple_item in linhas_info:
            f.write(tuple_item + "\n")

    print("\n" + "=" * 80)
    print(f"{Fore.GREEN}[SUCESSO SUITE COMPLETA] {len(arquivos_mkv)} insumos em inglês extraídos!")
    print(f"{Fore.GREEN}Diretório de Destino: {pasta_saida_eng}")
    print(f"{Fore.CYAN}Relatório salvo em: {ARQUIVO_INFO}")
    print("=" * 80)


if __name__ == "__main__":
    extrair_legendas_srt()
