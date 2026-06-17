#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: revisao_86.py
Revisa as legendas traduzidas de Eighty-Six (Part 1 & Part 2), corrige
alucinações residuais (como [T0] não restaurado) e padroniza termos.
Por fim, realiza o remux com mkvmerge gerando arquivos limpos *_PTBR.mkv.

Author: Antigravity
Data: Junho 2026
"""

import os
import sys
import re
import shutil
import subprocess
try:
    from colorama import init, Fore, Style
    # Inicializa o colorama
    init(autoreset=True)
except ImportError:
    class DummyColor:
        def __getattr__(self, name):
            return ""
    Fore = DummyColor()
    Style = DummyColor()
    def init(*args, **kwargs):
        pass

# Força codificação UTF-8 na saída padrão do Windows
if sys.version_info >= (3, 7):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Configurações de Pastas
PASTAS = [
    {
        "nome": "86 Part 1",
        "pasta_video": r"C:\animes\86\86 Part1\anime",
        "pasta_legenda": r"C:\animes\86\86 Part1\anime\legendas_eng\traducao",
        "pasta_saida": r"C:\animes\86\86 Part1\anime\corrigidos"
    },
    {
        "nome": "86 Part 2",
        "pasta_video": r"C:\animes\86\86 Part 2\anime",
        "pasta_legenda": r"C:\animes\86\86 Part 2\anime\legendas_eng\traducao",
        "pasta_saida": r"C:\animes\86\86 Part 2\anime\corrigidos"
    }
]

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

def aplicar_correcoes_linha(texto):
    original = texto

    # 1. Remove alucinações residuais de tag masking (ex: [T0], [T1])
    texto = re.sub(r"^\[T\d+\]\s*", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\[T\d+\]", "", texto, flags=re.IGNORECASE)

    # 2. Correções pontuais e padronizações da Legião
    texto = re.sub(r"\balgumas\s+Legion\b", "algumas unidades da Legião", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bum\s+Legion\b", "uma unidade da Legião", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bLegion\b", "Legião", texto)

    # 3. Correções específicas de tradução pendente (Episódio 11)
    if "I'll fight until the very end." in texto:
        texto = texto.replace("I'll fight until the very end.", "Eu lutarei até o fim.")
    
    # Substitui a frase sem se importar se tem barra simples ou dupla na quebra de linha do Aegisub (\N)
    if "I kept calling to you and made \\Nyou come all the way here." in texto:
        texto = texto.replace("I kept calling to you and made \\Nyou come all the way here.", "Eu continuei chamando por você e fiz \\Nvocê vir até aqui.")

    # 4. Correções de estática de comunicação (ruído/interferência) no Episódio 5
    if "Isso não é estático." in texto:
        texto = texto.replace("Isso não é estático.", "Isso não é estática.")
    if "Não está estático." in texto:
        texto = texto.replace("Não está estático.", "Não é estática.")

    return texto, texto != original

def processar_legendas(pasta_legenda):
    print(f"\n{Fore.CYAN}=== REVISANDO LEGENDAS EM: {pasta_legenda} ===")
    if not os.path.exists(pasta_legenda):
        print(f"{Fore.RED}[ERRO] Diretório de legendas não existe: {pasta_legenda}")
        return False

    arquivos = [f for f in os.listdir(pasta_legenda) if f.lower().endswith("_ptbr.ass")]
    arquivos.sort()

    print(f"Localizados {len(arquivos)} arquivos de legenda PT-BR para revisão.")
    total_correcoes = 0

    for arq in arquivos:
        caminho_file = os.path.join(pasta_legenda, arq)
        
        # Leitura resiliente
        linhas = []
        try:
            with open(caminho_file, 'r', encoding='utf-8-sig') as f:
                linhas = f.readlines()
        except UnicodeDecodeError:
            with open(caminho_file, 'r', encoding='utf-8', errors='ignore') as f:
                linhas = f.readlines()

        linhas_novas = []
        correcoes_arq = 0

        for line in linhas:
            if line.startswith("Dialogue:"):
                parts = line.split(",", 9)
                if len(parts) == 10:
                    metadados = ",".join(parts[:9]) + ","
                    texto_dialogo = parts[9].rstrip("\n")

                    texto_corrigido, modificado = aplicar_correcoes_linha(texto_dialogo)
                    if modificado:
                        correcoes_arq += 1
                        line = f"{metadados}{texto_corrigido}\n"

            linhas_novas.append(line)

        if correcoes_arq > 0:
            with open(caminho_file, "w", encoding="utf-8-sig") as f:
                f.writelines(linhas_novas)
            print(f"{Fore.GREEN}  [OK] {arq} | {correcoes_arq} modificações salvas.")
            total_correcoes += correcoes_arq
        else:
            print(f"  [OK] {arq} | Nenhuma correção necessária.")

    print(f"{Fore.GREEN}Revisão concluída! Total de {total_correcoes} correções aplicadas nesta pasta.")
    return True

def remuxar_videos(pasta_video, pasta_legenda, pasta_saida):
    print(f"\n{Fore.CYAN}=== INICIANDO REMUX DOS VÍDEOS EM: {pasta_video} ===")
    if not MKVMERGE_PATH:
        print(f"{Fore.RED}[ERRO] mkvmerge não encontrado. Remuxing abortado.")
        return False

    os.makedirs(pasta_saida, exist_ok=True)

    videos_mkv = sorted([f for f in os.listdir(pasta_video) if f.lower().endswith(".mkv")])
    if not videos_mkv:
        print(f"{Fore.YELLOW}[AVISO] Nenhum arquivo .mkv localizado na pasta: {pasta_video}")
        return False

    print(f"Encontrados {len(videos_mkv)} arquivos MKV originais.")
    print("-" * 80)

    for idx, video in enumerate(videos_mkv, 1):
        nome_base = os.path.splitext(video)[0]
        legenda_nome = f"{nome_base}_PTBR.ass"
        caminho_legenda = os.path.join(pasta_legenda, legenda_nome)

        if not os.path.exists(caminho_legenda):
            print(f"{Fore.RED}[ERRO] Legenda corrigida '{legenda_nome}' não encontrada. Pulando remux para este arquivo.")
            continue

        caminho_mkv_in = os.path.join(pasta_video, video)
        caminho_mkv_out = os.path.join(pasta_saida, f"{nome_base}_PTBR.mkv")

        print(f"[{idx}/{len(videos_mkv)}] Remuxando {video}...")
        
        cmd = [
            MKVMERGE_PATH,
            "-o", caminho_mkv_out,
            "--no-subtitles",            # Remove legendas antigas em inglês
            caminho_mkv_in,
            "--language", "0:por",
            "--track-name", "0:Português (Revisada - Gemma)",
            "--default-track", "0:yes",
            caminho_legenda
        ]

        res = subprocess.run(cmd, capture_output=True)
        if res.returncode == 0 and os.path.exists(caminho_mkv_out):
            print(f"  {Fore.GREEN}[SUCESSO] Salvo em: {os.path.basename(caminho_mkv_out)}")
        else:
            print(f"  {Fore.RED}[ERRO] Falha ao executar o mkvmerge para {video}.")
            print(f"  Stderr: {res.stderr.decode('utf-8', errors='ignore')[:300]}")
        print("-" * 50)

    print(f"\n{Fore.GREEN}[OK] Processo de remuxing finalizado para esta pasta!")
    return True

def main():
    print("=" * 80)
    print(f"{Fore.CYAN}          REVISÃO E REMUX DE LEGENDAS: 86 (EIGHTY-SIX)")
    print("=" * 80)

    # 1. Processar a revisão de todas as legendas PT-BR
    for config in PASTAS:
        processar_legendas(config["pasta_legenda"])

    # 2. Perguntar se deseja remuxar
    print("\n" + "=" * 80)
    opcao = input(f"{Fore.YELLOW}Deseja multiplexar (remux) as novas legendas nos arquivos .mkv originais? (s/n): {Style.RESET_ALL}").strip().lower()
    
    if opcao == "s":
        for config in PASTAS:
            remuxar_videos(config["pasta_video"], config["pasta_legenda"], config["pasta_saida"])

    print("\n" + "=" * 80)
    print(f"{Fore.GREEN}[FIM] Operação finalizada com sucesso!")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[AVISO] Interrompido pelo operador.")
        sys.exit(0)
