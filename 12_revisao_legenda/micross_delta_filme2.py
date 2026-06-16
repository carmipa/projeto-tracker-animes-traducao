#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: micross_delta_filme2.py
Revisa e corrige erros de lore, resíduos de francês e formatação na legenda do Filme 2
de Macross Delta, salvando a legenda limpa e re-multiplexando o vídeo MKV final.

Author: Antigravity + Paulo
Data: Junho 2026
"""

import os
import re
import sys
import shutil
import subprocess
from colorama import init, Fore, Style

# Inicializa o colorama para tratar escapes ANSI no console do Windows
init(autoreset=True)

# Força codificação UTF-8 na saída padrão do Windows
if sys.version_info >= (3, 7):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Caminhos padrão
PASTA_ANIME = r"D:\PROJETOS-OPEN\animes\Macross-Delta-Filme-2"
PASTA_LEGENDA = os.path.join(PASTA_ANIME, "legendas_ptbr")

# Arquivos de Entrada e Saída
ARQ_LEGENDA_IN = os.path.join(
    PASTA_LEGENDA, 
    "[Pikari-Teshima] Gekijouban Macross Delta Zettai LIVE!!!!!! VOSTFR [BD 1920x1080 x.265 10bits AAC]_PTBR_ENG.ass"
)
ARQ_LEGENDA_OUT = os.path.join(
    PASTA_LEGENDA, 
    "[Pikari-Teshima] Gekijouban Macross Delta Zettai LIVE!!!!!! VOSTFR [BD 1920x1080 x.265 10bits AAC]_PTBR.ass"
)

ARQ_VIDEO_IN = os.path.join(
    PASTA_ANIME,
    "[Pikari-Teshima] Gekijouban Macross Delta Zettai LIVE!!!!!! VOSTFR [BD 1920x1080 x.265 10bits AAC]_PTBR.mkv"
)
PASTA_VIDEO_OUT = os.path.join(PASTA_ANIME, "corrigidos")
ARQ_VIDEO_OUT = os.path.join(
    PASTA_VIDEO_OUT,
    "[Pikari-Teshima] Gekijouban Macross Delta Zettai LIVE!!!!!! VOSTFR [BD 1920x1080 x.265 10bits AAC]_PTBR.mkv"
)

# Substituições simples / Globais por regex
TERMOS_GLOBAIS = [
    # Lore & Ortografia
    (r"\bFreya\b", "Freyja"),
    (r"\bValkyrie\b", "Walküre"),
    (r"\bValkyries\b", "Walküres"),
    
    # Francês e Erros de Punctuation
    (r"\s+!", "!"),                  # Remove espaço antes de exclamação
    (r"\btudo o mundo\b", "todo mundo")
]

# Correções cirúrgicas de linhas específicas (1-indexed no arquivo .ass)
CORRECOES_ESPECIFICAS = {
    136: "estivessem aqui para sentir este vento.",
    176: r"Tudo que ela bebeu,\Né leite de maçã.",
    244: "S-Sim!",
    261: r"Que um dia, isso trará\Ndor para você e para Freyja.",
    273: r"Aquele no topo da colina,\Né o da minha mãe.",
    275: "Minha mãe se tornou uma com o vento",
    345: r"Théo!\NTodo mundo, espalhar!",
    376: r"Devemos perturbar as ondas\Ndo inimigo o máximo possível!",
    439: r"Padre Johann,\Ntodo mundo está seguro.",
    455: r"a divisão da Xaos de Listania?",
    521: r"Seu pingente.\NFui eu quem mandou para sua mãe.",
    538: r"Pois as relações entre Windermere\Ne o governo da U.N. se degradaram,",
    660: r"solicitado ao governo que suspenda\Na proibição da tecnologia proibida.",
    706: r"Isso é ruim,\Ntemos que cantar em uníssono!",
    715: "Ele não é como o Cavaleiro Branco ou o Messer.",
    730: r"E a vila de Freyja\Nestá em Windermere!",
    840: r"Perdemos o contato em 2016,\Ne não temos notícias desde...",
    1238: r"E aproveitar como se\Nfosse o nosso último!"
}

def achar_mkvtoolnix():
    for folder in [r"C:\Program Files\MKVToolNix", r"rC:\Program Files (x86)\MKVToolNix"]:
        ext_path = os.path.join(folder, "mkvextract.exe")
        merge_path = os.path.join(folder, "mkvmerge.exe")
        if os.path.exists(ext_path) and os.path.exists(merge_path):
            return ext_path, merge_path
    
    ext_path = shutil.which("mkvextract")
    merge_path = shutil.which("mkvmerge")
    return ext_path, merge_path

MKVEXTRACT_PATH, MKVMERGE_PATH = achar_mkvtoolnix()

def ler_arquivo_legenda(caminho):
    encodings = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
    for encoding in encodings:
        try:
            with open(caminho, 'r', encoding=encoding) as f:
                return f.readlines(), encoding
        except UnicodeDecodeError:
            continue
    with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
        return f.readlines(), "utf-8-replace"

def aplicar_correcoes_linha(texto, num_linha):
    original = texto
    
    # 1. Correções cirúrgicas de linhas específicas
    if num_linha in CORRECOES_ESPECIFICAS:
        texto = CORRECOES_ESPECIFICAS[num_linha]
    else:
        # 2. Correções globais por Regex
        for padrao, subst in TERMOS_GLOBAIS:
            texto = re.sub(padrao, subst, texto)
            
    return texto, texto != original

def processar_legenda():
    print(f"\n{Fore.CYAN}=== INICIANDO PROCESSAMENTO DE LEGENDA DO FILME 2 ===")
    if not os.path.exists(ARQ_LEGENDA_IN):
        print(f"{Fore.RED}[ERRO] Legenda de entrada não encontrada: {ARQ_LEGENDA_IN}")
        return False

    linhas, encoding = ler_arquivo_legenda(ARQ_LEGENDA_IN)
    linhas_novas = []
    total_correcoes = 0

    print(f"Legenda lida com codificação: {encoding}")
    print("-" * 80)

    for idx, line in enumerate(linhas, 1):
        if line.startswith("Dialogue:"):
            parts = line.split(",", 9)
            if len(parts) == 10:
                metadados = ",".join(parts[:9]) + ","
                texto_dialogo = parts[9].rstrip("\n")

                texto_corrigido, modificado = aplicar_correcoes_linha(texto_dialogo, idx)
                if modificado:
                    total_correcoes += 1
                    line = f"{metadados}{texto_corrigido}\n"
                    print(f"  ↳ [Linha {idx}] Correção:")
                    print(f"      Antes: {Fore.RED}{texto_dialogo}")
                    print(f"      Depois: {Fore.GREEN}{texto_corrigido}")

        linhas_novas.append(line)

    # Salva o arquivo corrigido na nova pasta em UTF-8 com BOM
    with open(ARQ_LEGENDA_OUT, "w", encoding="utf-8-sig") as f:
        f.writelines(linhas_novas)

    print(f"\n{Fore.GREEN}[FIM] Correções finalizadas! Total de {total_correcoes} linhas modificadas.")
    print(f"{Fore.GREEN}Legenda de saída salva em: {ARQ_LEGENDA_OUT}")
    return True

def remuxar_mkv():
    print(f"\n{Fore.CYAN}=== INICIANDO RE-MULTIPLEXAÇÃO DO FILME ===")
    if not MKVMERGE_PATH:
        print(f"{Fore.RED}[ERRO] mkvmerge não encontrado no sistema. Remuxing abortado.")
        return False

    if not os.path.exists(ARQ_VIDEO_IN):
        print(f"{Fore.RED}[ERRO] Vídeo original não encontrado em: {ARQ_VIDEO_IN}")
        return False

    os.makedirs(PASTA_VIDEO_OUT, exist_ok=True)

    print(f"  ↳ Remuxando {os.path.basename(ARQ_VIDEO_IN)}...")
    print(f"  ↳ Legenda utilizada: {os.path.basename(ARQ_LEGENDA_OUT)}")

    cmd = [
        MKVMERGE_PATH,
        "-o", ARQ_VIDEO_OUT,
        "--no-subtitles",            # Descarta legendas antigas que continham erros
        ARQ_VIDEO_IN,
        "--language", "0:por",
        "--track-name", "0:Português (Revisada - Walküre & Lore)",
        "--default-track", "0:yes",
        ARQ_LEGENDA_OUT
    ]

    res = subprocess.run(cmd, capture_output=True)
    if res.returncode == 0 and os.path.exists(ARQ_VIDEO_OUT):
        print(f"  {Fore.GREEN}[SUCESSO] Multiplexado! Salvo em: {ARQ_VIDEO_OUT}")
        return True
    else:
        print(f"  {Fore.RED}[ERRO] Falha ao executar o mkvmerge para o filme.")
        print(res.stderr.decode('utf-8', errors='replace'))
        return False

def main():
    print("=" * 80)
    print(f"{Fore.CYAN}       REVISÃO DE LEGENDA E REMUX: MACROSS DELTA - FILME 2")
    print("=" * 80)

    sucesso = processar_legenda()
    if sucesso:
        print("\n" + "=" * 80)
        opcao = input(f"{Fore.YELLOW}Deseja multiplexar (remux) a nova legenda no arquivo .mkv original? (s/n): {Style.RESET_ALL}").strip().lower()
        if opcao == "s":
            remuxar_mkv()

    print("\n" + "=" * 80)
    print(f"{Fore.GREEN}[FIM] Operação finalizada!")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[AVISO] Interrompido pelo operador.")
        sys.exit(0)
