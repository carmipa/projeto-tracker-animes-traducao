#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: cura_gundam_mkv.py
Extrai, corrige (cura offline de tags) e remuxa de volta os episódios do Gundam Unicorn
que já estão multiplexados e contêm o erro de 'TAG' nas legendas embutidas.

Suporta dois modos:
1. Cura com correspondência (Perfeita): Se as legendas ENG originais forem fornecidas.
2. Cura Cega (Blind Remedy): Se você não tiver as legendas ENG. Limpa cirurgicamente a palavra 'TAG'
   do início e do meio dos diálogos em português diretamente.

Author: Antigravity
Data: Junho 2026
"""

import os
import re
import sys
import json
import shutil
import subprocess
from colorama import init, Fore, Style

init(autoreset=True)


def achar_mkvtoolnix():
    for folder in [r"C:\Program Files\MKVToolNix", r"C:\Program Files (x86)\MKVToolNix"]:
        ext_path = os.path.join(folder, "mkvextract.exe")
        merge_path = os.path.join(folder, "mkvmerge.exe")
        if os.path.exists(ext_path) and os.path.exists(merge_path):
            return ext_path, merge_path
    
    ext_path = shutil.which("mkvextract")
    merge_path = shutil.which("mkvmerge")
    return ext_path, merge_path


MKVEXTRACT_PATH, MKVMERGE_PATH = achar_mkvtoolnix()


def obter_diretorio_obrigatorio(mensagem_prompt, padrao_caminho=None):
    while True:
        sufixo_padrao = f" (ENTER = {padrao_caminho})" if padrao_caminho else ""
        entrada = input(f"{Fore.YELLOW}{mensagem_prompt}{sufixo_padrao}: {Style.RESET_ALL}").strip()
        entrada = entrada.strip('"').strip("'")
        if not entrada and padrao_caminho:
            return padrao_caminho
        if not entrada:
            continue
        if not os.path.isdir(entrada):
            print(f"{Fore.RED}[ERRO] Diretório não existe: {entrada}")
            continue
        return entrada


def obter_diretorio_opcional(mensagem_prompt, padrao_caminho=None):
    sufixo_padrao = f" (ENTER = {padrao_caminho})" if padrao_caminho else ""
    entrada = input(f"{Fore.YELLOW}{mensagem_prompt}{sufixo_padrao}: {Style.RESET_ALL}").strip()
    entrada = entrada.strip('"').strip("'")
    if not entrada and padrao_caminho:
        return padrao_caminho
    if entrada and os.path.isdir(entrada):
        return entrada
    return None


def obter_track_id_legenda(mkv_path):
    """Descobre o ID da trilha de legenda de texto ASS no arquivo MKV."""
    try:
        cmd = [MKVMERGE_PATH, "-J", mkv_path]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        if res.returncode != 0:
            return -1
        dados = json.loads(res.stdout)
        for track in dados.get("tracks", []):
            if track.get("type") == "subtitles":
                codec_id = track.get("properties", {}).get("codec_id", "")
                if "S_TEXT/ASS" in codec_id:
                    return track.get("id")
        return -1
    except Exception:
        return -1


def curar_linha_cega(texto_t):
    """Cura cega: Remove a palavra 'TAG' ou '_TAG_' do início/meio sem legenda ENG."""
    # Limpa sublinhados ao redor de TAG
    texto_t = re.sub(r'_{1,3}TAG_{1,3}', 'TAG', texto_t)
    texto_t = re.sub(r'_{1,3}tag_{1,3}', 'tag', texto_t)

    # Caso 1: TAG colado no início (ex: TAGPor que...)
    if texto_t.startswith("TAG"):
        return texto_t[3:]
    if texto_t.startswith("tag"):
        return texto_t[3:]

    # Caso 2: TAG com espaços ou solto
    texto_t = texto_t.replace("TAG ", "").replace("tag ", "")
    texto_t = texto_t.replace(" TAG", "").replace(" tag", "")
    
    # Caso 3: TAG no meio colado
    texto_t = texto_t.replace("TAG", "").replace("tag", "")

    return texto_t


def curar_linha_alinhada(texto_t, texto_o, tags_o):
    """Cura perfeita: Recoloca as tags ASS originais nos locais correspondentes."""
    texto_t_limpo = re.sub(r'_{1,3}TAG_{1,3}', 'TAG', texto_t)
    texto_refeito = texto_t_limpo

    for idx_tag, tag in enumerate(tags_o):
        if tag in texto_refeito:
            continue

        if 'TAG' in texto_refeito:
            texto_refeito = texto_refeito.replace('TAG', tag, 1)
        elif 'tag' in texto_refeito:
            texto_refeito = texto_refeito.replace('tag', tag, 1)
        else:
            # Fallback para tags no início
            if idx_tag == 0 and texto_o.startswith(tag) and not texto_refeito.startswith(tag):
                if texto_refeito.startswith("TAG") or texto_refeito.startswith("tag"):
                    texto_refeito = tag + texto_refeito[3:]
                else:
                    texto_refeito = tag + texto_refeito
    return texto_refeito


def executar_remux_gundam():
    print("=" * 80)
    print(f"{Fore.CYAN}    EXTRATOR + CURADOR + MULTIPLEXADOR AUTOMÁTICO DE GUNDAM UNICORN")
    print("=" * 80)

    if not MKVEXTRACT_PATH or not MKVMERGE_PATH:
        print(f"{Fore.RED}[ERRO] Binários mkvextract ou mkvmerge não encontrados no sistema.")
        return

    # 1. Obter Pastas
    caminho_padrao_videos = r"E:\animes\GUNDAM\GUNDAM UC\UC 0096 - UNICORN\COmpleto"
    pasta_videos = obter_diretorio_obrigatorio("Pasta com os MKVs finais do Gundam (com erro)", caminho_padrao_videos)

    caminho_padrao_eng = r"C:\TRACKER-ANIMES\animes\unicornio\Mobile Suit Gundam Unicorn Re0096 (2016) [Season 1] [BD 1080p HEVC OPUS] [Dual-Audio]\Season 1\legendas_eng"
    # Se a pasta padrão do drive C: não existir, tenta nula
    if not os.path.exists(caminho_padrao_eng):
        caminho_padrao_eng = None
    pasta_originais_eng = obter_diretorio_opcional("Pasta com legendas originais ENG (ENTER para CURA CEGA sem inglês)", caminho_padrao_eng)

    modo_cura = "PERFEITA (com alinhamento ENG)" if pasta_originais_eng else "CEGA (limpeza local offline)"
    print(f"\n{Fore.GREEN}[INFO] Modo de cura selecionado: {Fore.YELLOW}{modo_cura}")

    # Cria pastas auxiliares
    pasta_temp = os.path.join(pasta_videos, "temp_remux")
    pasta_saida = os.path.join(pasta_videos, "corrigidos")
    os.makedirs(pasta_temp, exist_ok=True)
    os.makedirs(pasta_saida, exist_ok=True)

    arquivos_mkv = sorted([f for f in os.listdir(pasta_videos) if f.lower().endswith('.mkv')])
    print(f"{Fore.GREEN}[OK] Localizados {len(arquivos_mkv)} arquivos MKV para processamento.")

    total_curas_geral = 0

    for idx, nome_mkv in enumerate(arquivos_mkv, 1):
        caminho_mkv = os.path.join(pasta_videos, nome_mkv)
        print(f"\n[{idx}/{len(arquivos_mkv)}] Processando: {nome_mkv}...")

        # 1. Identificar trilha de legenda ASS
        track_id = obter_track_id_legenda(caminho_mkv)
        if track_id == -1:
            print(f"  {Fore.RED}[AVISO] Nenhuma legenda ASS embutida encontrada no MKV. Pulando.")
            continue

        # 2. Extrair legenda ASS com erro
        legenda_extraida = os.path.join(pasta_temp, f"temp_{idx}_PTBR.ass")
        print(f"  ↳ Extraindo legenda interna (Trilha ID {track_id})...")
        cmd_extract = [MKVEXTRACT_PATH, "tracks", caminho_mkv, f"{track_id}:{legenda_extraida}"]
        res = subprocess.run(cmd_extract, capture_output=True)
        if res.returncode != 0 or not os.path.exists(legenda_extraida):
            print(f"  {Fore.RED}[ERRO] Falha ao extrair legenda do MKV. Pulando.")
            continue

        # 3. Aplicar Cura
        with open(legenda_extraida, 'r', encoding='utf-8', errors='replace') as f:
            linhas_pt = f.readlines()

        linhas_curadas = []
        curas_no_arquivo = 0

        # Se no modo perfeito, carrega arquivo em inglês correspondente
        linhas_eng = None
        if pasta_originais_eng:
            # Pareamento pelo episódio: ex "S01E01"
            m_ep = re.search(r'S\d+E\d+', nome_mkv, re.I)
            if m_ep:
                tag_ep = m_ep.group(0).lower()
                arquivos_eng = os.listdir(pasta_originais_eng)
                match_eng = [f for f in arquivos_eng if tag_ep in f.lower() and f.lower().endswith('.ass')]
                if match_eng:
                    caminho_eng = os.path.join(pasta_originais_eng, match_eng[0])
                    with open(caminho_eng, 'r', encoding='utf-8', errors='replace') as f:
                        linhas_eng = f.readlines()

            if not linhas_eng:
                print(f"  {Fore.YELLOW}[AVISO] Legenda original ENG correspondente não encontrada. Aplicando CURA CEGA.")

        # Processamento linha a linha
        for i in range(len(linhas_pt)):
            linha_pt = linhas_pt[i]
            
            if linha_pt.startswith("Dialogue:"):
                partes_pt = linha_pt.split(",", 9)
                if len(partes_pt) == 10:
                    metadados_pt = ",".join(partes_pt[:9]) + ","
                    texto_pt = partes_pt[9].rstrip("\n")

                    if linhas_eng and i < len(linhas_eng) and linhas_eng[i].startswith("Dialogue:"):
                        partes_eng = linhas_eng[i].split(",", 9)
                        if len(partes_eng) == 10:
                            texto_eng = partes_eng[9].rstrip("\n")
                            tags_o = re.findall(r'\{[^}]+\}', texto_eng)
                            if tags_o:
                                texto_curado = curar_linha_alinhada(texto_pt, texto_eng, tags_o)
                                if texto_curado != texto_pt:
                                    curas_no_arquivo += 1
                                    linha_pt = f"{metadados_pt}{texto_curado}\n"
                                    linhas_curadas.append(linha_pt)
                                    continue
                    
                    # Cura cega (se não tiver arquivo ENG correspondente ou sem tags no original)
                    if any(x in texto_pt for x in ["TAG", "tag"]):
                        texto_curado = curar_linha_cega(texto_pt)
                        if texto_curado != texto_pt:
                            curas_no_arquivo += 1
                            linha_pt = f"{metadados_pt}{texto_curado}\n"

            linhas_curadas.append(linha_pt)

        # Salva a legenda ASS curada
        legenda_curada = os.path.join(pasta_temp, f"curada_{idx}_PTBR.ass")
        with open(legenda_curada, 'w', encoding='utf-8') as f:
            f.writelines(linhas_curadas)

        # 4. Remuxing
        caminho_saida_mkv = os.path.join(pasta_saida, nome_mkv)
        print(f"  ↳ Re-multiplexando vídeo com legenda curada...")
        
        cmd_merge = [
            MKVMERGE_PATH,
            "-o", caminho_saida_mkv,
            "--no-subtitles",       # remove a trilha PT-BR com erro
            caminho_mkv,            # vídeo e áudio originais
            "--language", "0:por",
            "--track-name", "0:Português (Gemma 4B - Curada)",
            "--default-track", "0:yes",
            legenda_curada          # legenda curada sem erros
        ]
        
        res = subprocess.run(cmd_merge, capture_output=True)
        if res.returncode == 0 and os.path.exists(caminho_saida_mkv):
            print(f"  {Fore.GREEN}[SUCESSO] Episódio multiplexado! Corrigidas {curas_no_arquivo} falhas de tags.")
            total_curas_geral += curas_no_arquivo
        else:
            print(f"  {Fore.RED}[ERRO] Falha no mkvmerge para {nome_mkv}.")

    # Limpeza
    try:
        shutil.rmtree(pasta_temp)
    except Exception:
        pass

    print("\n" + "=" * 80)
    print(f"{Fore.GREEN}[SUCESSO GERAL] Remuxer de cura finalizado!")
    print(f"{Fore.GREEN}Vídeos corrigidos salvos na pasta: {pasta_saida}")
    print(f"{Fore.GREEN}Total de tags curadas na temporada: {total_curas_geral}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        executar_remux_gundam()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[AVISO] Interrompido pelo operador.")
        sys.exit(0)
