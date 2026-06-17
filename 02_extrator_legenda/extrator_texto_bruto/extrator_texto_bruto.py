#!/usr/bin/env python3
"""
Extrator de Texto Bruto com Numeração de Linhas (versão inteligente)
=====================================================================
Este script percorre uma pasta contendo arquivos ``.mkv``,
extrai o texto das legendas já geradas pelo *extrator inteligente*
(`extrator_inteligente_ass.py`) e salva, **na mesma pasta do vídeo**,
um arquivo chamado ``texto_bruto_extraido_<nome_do_capítulo>.txt``
com cada linha numerada e o total de linhas ao final.

Uso:
    python extrator_texto_bruto.py -p <pasta_videos>

Se a pasta não for informada, o script solicitará interativamente.
"""

import os
import sys
from pathlib import Path
from colorama import init, Fore, Style

# Inicializa o Colorama (necessário no Windows)
init(autoreset=True)

def encontrar_legenda(base_path: Path, nome_base: str) -> Path | None:
    """Procura a legenda já extraída (``*_ENG.ass`` ou ``*_ENG.srt``).

    O *extrator inteligente* salva as legendas em ``legendas_eng`` dentro da
    mesma pasta que contém os arquivos ``.mkv``.  Esta função verifica se
    existe algum desses dois formatos e devolve o caminho completo ou ``None``.
    """
    pasta_legendas = base_path / "legendas_eng"
    if not pasta_legendas.is_dir():
        return None
    # Possíveis extensões geradas pelo extrator inteligente
    for ext in [".ass", ".srt"]:
        candidato = pasta_legendas / f"{nome_base}_ENG{ext}"
        if candidato.is_file():
            return candidato
    return None

def numerar_arquivo(arquivo_entrada: Path, arquivo_saida: Path) -> None:
    """Lê *arquivo_entrada* e grava *arquivo_saida* com linhas numeradas.

    Cada linha tem o formato ``<numero>: <texto>``.  Ao final, adiciona‑se a
    linha ``Total de linhas: N``.
    """
    try:
        with arquivo_entrada.open("r", encoding="utf-8") as f:
            linhas = f.readlines()
    except Exception as e:
        sys.stderr.write(f"{Fore.RED}[ERRO] Não foi possível ler {arquivo_entrada}: {e}\n")
        return

    # Mantém as linhas originais sem renumerar, apenas adiciona o total ao final
    linhas = [l.rstrip('\n') for l in linhas]
    total = len(linhas)
    linhas.append(f"Total de linhas: {total}")
    # Garante que a pasta de destino exista
    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)
    with arquivo_saida.open("w", encoding="utf-8") as f:
        for line in linhas:
            f.write(line + "\n")
    print(f"{Fore.GREEN}{arquivo_saida.name} criado com {total} linhas.")

def processar_pasta(pasta_videos: Path) -> None:
    """Processa todos os arquivos ``.mkv`` encontrados em *pasta_videos*.

    Para cada vídeo, busca a legenda já extraída e cria o arquivo numerado
    ``texto_bruto_extraido_<nome_do_capítulo>.txt`` ao lado do vídeo.
    """
    if not pasta_videos.is_dir():
        sys.stderr.write(f"{Fore.RED}[ERRO] Pasta não encontrada: {pasta_videos}\n")
        sys.exit(1)

    arquivos_mkv = sorted([f for f in pasta_videos.iterdir() if f.suffix.lower() == ".mkv"])
    if not arquivos_mkv:
        print(f"{Fore.YELLOW}⚠️ Nenhum arquivo .mkv encontrado em {pasta_videos}\n")
        return

    print(f"{Fore.CYAN}Processando {len(arquivos_mkv)} arquivos .mkv em {pasta_videos}\n")
    for mkv in arquivos_mkv:
        nome_base = mkv.stem  # nome sem extensão
        legenda_path = encontrar_legenda(pasta_videos, nome_base)
        if legenda_path is None:
            print(f"{Fore.RED}⚠️ Legenda não encontrada para {mkv.name}. Pulando...\n")
            continue
        # Cria subpasta para arquivos de texto bruto numerado
        pasta_texto_bruto = pasta_videos / "texto_bruto_extraido"
        pasta_texto_bruto.mkdir(parents=True, exist_ok=True)
        saida_path = pasta_texto_bruto / f"texto_bruto_extraido_{nome_base}.txt"
        numerar_arquivo(legenda_path, saida_path)

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Numera linhas de legendas extraídas (texto bruto).")
    parser.add_argument("-p", "--pasta", help="Pasta onde estão os arquivos .mkv.")
    args = parser.parse_args()

    if args.pasta:
        pasta = Path(args.pasta).expanduser().resolve()
    else:
        pasta_input = input(f"{Fore.YELLOW}Digite a pasta contendo os arquivos .mkv: {Style.RESET_ALL}").strip()
        pasta = Path(pasta_input).expanduser().resolve()
    processar_pasta(pasta)

if __name__ == "__main__":
    main()
