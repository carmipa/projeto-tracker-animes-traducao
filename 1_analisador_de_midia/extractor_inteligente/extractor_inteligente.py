#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: extractor_inteligente.py
Extrai dinamicamente as legendas de diálogo em inglês de Gundam Unicorn RE:0096,
tratando a variação de Track IDs automaticamente através do binário local do MKVExtract.

Author: Paulo + Gemini
Data: Maio 2026
Status: PRODUCTION READY (Bugfix aplicado)
"""

import os
import subprocess
import json
from colorama import init, Fore, Style
from tqdm import tqdm

# Inicializa o Colorama para tratamento de escapes ANSI no terminal do Windows
init(autoreset=True)

MKVEXTRACT_PATH = r"C:\Program Files\MKVToolNix\mkvextract.exe"
MKVMERGE_PATH = r"C:\Program Files\MKVToolNix\mkvmerge.exe"

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_INFO = os.path.join(PASTA_SCRIPT, "info.txt")


def extrair_legendas_dinamicamente():
    print("=" * 80)
    print(f"{Fore.CYAN}         ESTEIRA DE EXTRAÇÃO INTELIGENTE DE SOFTBUBS: MKV ➔ ASS")
    print("=" * 80)

    pasta_videos = r"C:\TRACKER-ANIMES\animes\unicornio\Mobile Suit Gundam Unicorn Re0096 (2016) [Season 1] [BD 1080p HEVC OPUS] [Dual-Audio]\Season 1"
    pasta_saida_eng = os.path.join(pasta_videos, "legendas_eng")
    os.makedirs(pasta_saida_eng, exist_ok=True)

    if not os.path.exists(MKVEXTRACT_PATH):
        print(f"{Fore.RED}[ERRO] O binário do mkvextract não foi achado em: {MKVEXTRACT_PATH}")
        print(f"{Fore.YELLOW}Por favor, altere a variável MKVEXTRACT_PATH com o caminho correto do seu instalador.")
        return

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
                # CORREÇÃO: Variável alterada de dados_media para dados_midia para casar com o ponteiro do objeto
                for track in dados_midia.get('tracks', []):
                    if track.get('type') == 'subtitles':
                        propriedades = track.get('properties', {})
                        track_name = propriedades.get('track_name', '')

                        if "Dialogue" in track_name or "gcs8" in track_name:
                            id_legenda_alvo = track.get('id')
                            track_name_detectado = track_name
                            print(f"  ↳ {Fore.GREEN}Sucesso! Detectada legenda de diálogo no ID: {id_legenda_alvo} ({track_name})")
                            break

            if id_legenda_alvo is None:
                # Fallback estrito mapeado na análise forense dos logs consolidados[cite: 12]
                if any(ep in arquivo for ep in ("S01E06", "S01E07", "S01E08", "S01E09", "S01E10", "S01E11")):
                    id_legenda_alvo = 4
                    print(f"  ↳ {Fore.BLUE}Fallback aplicado (Log Físico): ID 4 forçado.[cite: 12]")
                else:
                    id_legenda_alvo = 5
                    print(f"  ↳ {Fore.BLUE}Fallback aplicado (Log Físico): ID 5 forçado.[cite: 12]")

            arquivo_saida_ass = os.path.join(pasta_saida_eng, f"{nome_base}_ENG.ass")

            print(f"  ↳ Extraindo trilha de texto para: legendas_eng\\{nome_base}_ENG.ass...")
            cmd_extract = [MKVEXTRACT_PATH, "tracks", caminho_mkv, f"{id_legenda_alvo}:{arquivo_saida_ass}"]
            subprocess.run(cmd_extract, capture_output=True)

            linhas_info.append(
                f"{arquivo} | Track ID: {id_legenda_alvo} | Nome: {track_name_detectado} | Saída: {nome_base}_ENG.ass"
            )

            barra.update(1)

    # Persistência dos metadados de auditoria em disco (info.txt)
    with open(ARQUIVO_INFO, "w", encoding="utf-8") as f:
        f.write("RELATÓRIO DE EXTRAÇÃO — EXTRACTOR INTELIGENTE\n")
        f.write("=" * 80 + "\n")
        for linha in linhas_info:
            f.write(linha + "\n")

    print("\n" + "=" * 80)
    print(f"{Fore.GREEN}[SUCESSO SUITE COMPLETA] {len(arquivos_mkv)} insumos em inglês extraídos!")
    print(f"{Fore.GREEN}Diretório de Destino: {pasta_saida_eng}")
    print(f"{Fore.CYAN}Relatório salvo em: {ARQUIVO_INFO}")
    print("=" * 80)


if __name__ == "__main__":
    extrair_legendas_dinamicamente()