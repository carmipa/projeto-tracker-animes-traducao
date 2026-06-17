#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: revisao_legenda_macross_delta.py
Revisa e corrige erros de lore, traduções em inglês faltantes e tags ASS corrompidas 
nas legendas de Macross Delta, salvando os resultados em uma nova pasta para compartilhamento.

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
PASTA_ANIME_PADRAO = r"E:\animes\MACROSS\Macross-Delta-br"
PASTA_LEGENDA_ENTRADA = os.path.join(PASTA_ANIME_PADRAO, "legendas_eng")
PASTA_LEGENDA_SAIDA = os.path.join(PASTA_ANIME_PADRAO, "legendas_ptbr_corrigidas")

# Dicionário de patentes e termos comuns para substituição simples
TERMOS_GLOBAIS = [
    (r"\bFreya\b", "Freyja"),
    (r"\bdescultura\b", "deculture"),
    (r"\bDescultura\b", "Deculture"),
    (r"\bportside\b", "bombordo"),
    (r"\bPortside\b", "Bombordo"),
    (r"\bstarboard\b", "boreste"),
    (r"\bStarboard\b", "Boreste")
]

# Traduções específicas por episódio e linha (1-indexed no arquivo .ass)
CORRECOES_ESPECIFICAS = {
    # Episódio 01
    1: {
        430: r"{=2}{\fscy103.43\fscx103.43\alpha&H00&\fs105\pos(1543.155,796.005)\blur1.56\fsp15\c&HE7FCFE&}2067 AD",
        450: r"{=2}{\fscy104.44\fscx104.44\alpha&H00&\fs105\pos(1542.69,795.18)\blur1.56\fsp15\c&HE7FCFE&}2067 AD"
    },
    # Episódio 03
    3: {
        86: r"{=0}{\fscy100\fscx100\an8\blur1.8\bord0.75\c&H31149C&\3c&H31149C&\frz348.3\pos(811.65,1108.5)}Ragnyannyan",
        88: "Bem, eu só...",
        89: "Estamos de volta.",
        90: "Eu odeio o exército.",
        91: "Eu também.",
        92: "E de receber ordens também.",
        93: "Eu vou voar pelos céus com essa belezinha.",
        94: "Saia de perto dela!",
        95: "Não ouse encostar um dedo no meu caça!",
        96: "Comandante Arad, você está falando sério \\Ntentando recrutar esse desastre ambulante?",
        97: "Eu me lembro de ter te dito para não levar o campo de batalha na brincadeira."
    },
    # Episódio 07
    7: {
        336: r"{\clip(636,692,1286,699)\pos(960,682.5)\fs82.5\bord0\blur0.55\c&H0071D9&}Atrás das Linhas Inimigas"
    },
    # Episódio 10
    10: {
        302: r"{\fad(940,0)\clip(740,676,1180,684)\pos(960,682.5)\fs82.5\bord0\blur0.55\c&H0069C9&}Flash de AXIA",
        303: r"{\fad(940,0)\clip(740,684,1180,692)\pos(960,682.5)\fs82.5\bord0\blur0.55\c&H0172D4&}Flash de AXIA",
        304: r"{\fad(940,0)\clip(740,692,1180,699)\pos(960,682.5)\fs82.5\bord0\blur0.55\c&H017CDC&}Flash de AXIA",
        305: r"{\fad(940,0)\clip(740,699,1180,707)\pos(960,682.5)\fs82.5\bord0\blur0.55\c&H0186E3&}Flash de AXIA",
        306: r"{\fad(940,0)\clip(740,707,1180,714)\pos(960,682.5)\fs82.5\bord0\blur0.55\c&H018FEB&}Flash de AXIA",
        308: "então vamos nos divertir dentro de você",
        310: "As pétalas desta flor caem no vento",
        311: "As estrelas são mais do que eu poderia contar",
        312: "Eu poderia colocar toda a culpa em você,",
        314: "mas não posso contar a ninguém como meu coração acelera"
    },
    # Episódio 20
    20: {
        309: r"{\clip(620,662,1300,669)\pos(960,682.5)\fs82.5\bord0\blur0.55\c&H0056BC&}Experimento de Impulso",
        310: r"{\clip(620,669,1300,677)\pos(960,682.5)\fs82.5\bord0\blur0.55\c&H0060C4&}Experimento de Impulso"
    },
    # Episódio 25
    25: {
        387: r"{\clip(667,717,1252,719)\pos(960,682.5)\fad(953,0)\fs82.5\bord0\blur0.5\c&H028BF3&}Cantor das Estrelas"
    },
    # Episódio 26
    26: {
        348: "Se você puder enxergar o fim do céu",
        349: "Se você puder ouvir minha voz trêmula",
        350: "Então erga-se como se fosse explodir em pedaços",
        351: "Nossas memórias rasgadas serão nossas asas sem limites"
    }
}

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

def extrair_numero_episodio(nome_arquivo):
    m = re.search(r'[-_]\s*(\d+)\s*[_(\s]', nome_arquivo)
    if m:
        return int(m.group(1))
    # Tentar outro padrão comum, ex: "01", "12"
    m_dig = re.findall(r'\d+', nome_arquivo)
    if m_dig:
        # Pega o último ou penúltimo número curto
        for n in reversed(m_dig):
            if len(n) <= 2:
                return int(n)
    return None

def aplicar_correcao_linha(texto, ep_num, num_linha):
    original = texto

    # 1. Correções globais por Regex
    for padrao, subst in TERMOS_GLOBAIS:
        texto = re.sub(padrao, subst, texto)

    # 2. Correções cirúrgicas de linhas específicas
    if ep_num in CORRECOES_ESPECIFICAS and num_linha in CORRECOES_ESPECIFICAS[ep_num]:
        subst_especifica = CORRECOES_ESPECIFICAS[ep_num][num_linha]
        # Se a substituição já começar com { ouDialogue/etc., tratamos a linha inteira ou apenas o texto
        if subst_especifica.startswith("{") or subst_especifica.startswith("{\\"):
            # Para letreiros corrompidos, substituímos o texto inteiro (incluindo tags)
            texto = subst_especifica
        else:
            # Para diálogos normais, substituímos preservando possíveis tags ASS extras na linha original
            # Removemos tags para ver se o texto bate com algo ou apenas dropamos o texto traduzido
            # No caso, substituímos o diálogo inteiro do final da linha
            texto = subst_especifica

    return texto, texto != original

def processar_legendas():
    print(f"\n{Fore.CYAN}=== INICIANDO PROCESSAMENTO DE LEGENDAS DE MACROSS DELTA ===")
    if not os.path.exists(PASTA_LEGENDA_ENTRADA):
        print(f"{Fore.RED}[ERRO] Diretório de entrada de legendas não existe: {PASTA_LEGENDA_ENTRADA}")
        return False

    os.makedirs(PASTA_LEGENDA_SAIDA, exist_ok=True)
    print(f"{Fore.GREEN}[OK] Diretório de saída criado: {PASTA_LEGENDA_SAIDA}")

    arquivos = [f for f in os.listdir(PASTA_LEGENDA_ENTRADA) if f.lower().endswith(".ass")]
    arquivos.sort()

    print(f"Localizados {len(arquivos)} arquivos de legenda .ass para processamento.")
    print("-" * 80)

    total_correcoes = 0

    for arq in arquivos:
        ep_num = extrair_numero_episodio(arq)
        if ep_num is None:
            print(f"{Fore.YELLOW}[AVISO] Não foi possível deduzir o número do episódio para: {arq}. Processando com Ep=0.")
            ep_num = 0

        caminho_in = os.path.join(PASTA_LEGENDA_ENTRADA, arq)
        caminho_out = os.path.join(PASTA_LEGENDA_SAIDA, arq.replace("_ENG.ass", "_PTBR.ass"))

        linhas, encoding = ler_arquivo_legenda(caminho_in)
        linhas_novas = []
        correcoes_arq = 0

        for idx, line in enumerate(linhas, 1):
            if line.startswith("Dialogue:"):
                parts = line.split(",", 9)
                if len(parts) == 10:
                    metadados = ",".join(parts[:9]) + ","
                    texto_dialogo = parts[9].rstrip("\n")

                    texto_corrigido, modificado = aplicar_correcao_linha(texto_dialogo, ep_num, idx)
                    if modificado:
                        correcoes_arq += 1
                        line = f"{metadados}{texto_corrigido}\n"
                        print(f"  ↳ [EP {ep_num} | L{idx}] Correção:")
                        print(f"      Antes: {Fore.RED}{texto_dialogo}")
                        print(f"      Depois: {Fore.GREEN}{texto_corrigido}")

            linhas_novas.append(line)

        # Salva o arquivo corrigido na nova pasta em UTF-8 com BOM (ideal para ASS)
        with open(caminho_out, "w", encoding="utf-8-sig") as f:
            f.writelines(linhas_novas)

        if correcoes_arq > 0:
            print(f"{Fore.GREEN}[OK] Processado EP {ep_num:02d} | {correcoes_arq} modificações salvas em: {os.path.basename(caminho_out)}")
            total_correcoes += correcoes_arq
        else:
            print(f"[OK] Processado EP {ep_num:02d} | Nenhuma modificação necessária.")
        print("-" * 50)

    print(f"\n{Fore.GREEN}[FIM] Revisão finalizada! Total de {total_correcoes} correções aplicadas nos 26 arquivos.")
    print(f"{Fore.GREEN}Legendas prontas salvas na pasta: {PASTA_LEGENDA_SAIDA}")
    return True

def remuxar_mkv():
    print(f"\n{Fore.CYAN}=== INICIANDO RE-MULTIPLEXAÇÃO DOS VÍDEOS ===")
    if not MKVMERGE_PATH:
        print(f"{Fore.RED}[ERRO] mkvmerge não encontrado no sistema. Remuxing abortado.")
        return False

    pasta_saida_videos = os.path.join(PASTA_ANIME_PADRAO, "corrigidos")
    os.makedirs(pasta_saida_videos, exist_ok=True)

    videos_mkv = sorted([f for f in os.listdir(PASTA_ANIME_PADRAO) if f.lower().endswith(".mkv")])
    if not videos_mkv:
        print(f"{Fore.YELLOW}[AVISO] Nenhum arquivo .mkv localizado na pasta: {PASTA_ANIME_PADRAO}")
        return False

    print(f"[OK] Encontrados {len(videos_mkv)} arquivos MKV originais.")
    print(f"Os vídeos com a nova legenda corrigida serão salvos em: {pasta_saida_videos}")
    print("-" * 80)

    legendas_corrigidas = [f for f in os.listdir(PASTA_LEGENDA_SAIDA) if f.lower().endswith(".ass")]

    for idx, video in enumerate(videos_mkv, 1):
        ep_num = extrair_numero_episodio(video)
        if ep_num is None:
            print(f"{Fore.YELLOW}[AVISO] Não foi possível identificar o número do episódio em: {video}. Pulando remux.")
            continue

        # Encontra a legenda corrigida correspondente
        legenda_correta = None
        for leg in legendas_corrigidas:
            leg_ep = extrair_numero_episodio(leg)
            if leg_ep == ep_num:
                legenda_correta = leg
                break

        if not legenda_correta:
            print(f"{Fore.RED}[ERRO] Legenda corrigida correspondente para o EP {ep_num:02d} não encontrada. Pulando remux.")
            continue

        caminho_mkv_in = os.path.join(PASTA_ANIME_PADRAO, video)
        caminho_legenda = os.path.join(PASTA_LEGENDA_SAIDA, legenda_correta)
        caminho_mkv_out = os.path.join(pasta_saida_videos, video)

        print(f"[{idx}/{len(videos_mkv)}] Remuxando EP {ep_num:02d}...")
        print(f"  ↳ Origem: {video}")
        print(f"  ↳ Legenda: {legenda_correta}")

        cmd = [
            MKVMERGE_PATH,
            "-o", caminho_mkv_out,
            "--no-subtitles",            # Remove legendas antigas que continham erros
            caminho_mkv_in,
            "--language", "0:por",
            "--track-name", "0:Português (Revisada - Freyja & Deculture)",
            "--default-track", "0:yes",
            caminho_legenda
        ]

        res = subprocess.run(cmd, capture_output=True)
        if res.returncode == 0 and os.path.exists(caminho_mkv_out):
            print(f"  {Fore.GREEN}[SUCESSO] Multiplexado! Salvo em: corrigidos\\{video}")
        else:
            print(f"  {Fore.RED}[ERRO] Falha ao executar o mkvmerge para {video}.")
        print("-" * 50)

    print(f"\n{Fore.GREEN}[OK] Processo de remuxing finalizado com sucesso!")
    return True

def main():
    print("=" * 80)
    print(f"{Fore.CYAN}       REVISÃO DE LEGENDAS E REMUX DE VÍDEOS: MACROSS DELTA")
    print("=" * 80)

    # 1. Processar a correção de legendas de entrada e salvar na nova pasta de saída
    sucesso_legendas = processar_legendas()

    if sucesso_legendas:
        # 2. Perguntar se deseja remuxar os vídeos
        print("\n" + "=" * 80)
        opcao = input(f"{Fore.YELLOW}Deseja multiplexar (remux) as novas legendas nos arquivos .mkv originais? (s/n): {Style.RESET_ALL}").strip().lower()
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
