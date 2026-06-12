#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MODULO: limpa_erros_residuais.py
Faz uma varredura nas legendas PT-BR em busca de marcadores "[ERRO_TRADUCAO: ...]"
remanescentes. Como esses erros persistentes geralmente são compostos por termos
protegidos e números (cujo correto é ser idêntico ao inglês), este script substitui
diretamente o erro pelo texto original com as tags ASS restauradas, sem chamar a IA.

Author: Antigravity + Paulo
Data: Junho 2026
"""

import os
import re
import sys
from colorama import init, Fore

init(autoreset=True)


def restaurar_tags(traducao, tags):
    """Recoloca as tags ASS nos placeholders [T0], [T1]... de forma segura."""
    for idx_tag, tag in enumerate(tags):
        marcador = f"[T{idx_tag}]"
        if marcador in traducao:
            traducao = traducao.replace(marcador, tag, 1)
            continue

        # Usa lambda no re.sub para evitar erros com barras invertidas e referências de grupo (\1, etc.)
        nova_traducao = re.sub(rf'\[?[Tt]{idx_tag}\]?', lambda m: tag, traducao, count=1)
        if nova_traducao != traducao:
            traducao = nova_traducao
        elif traducao.count(tag) < tags.count(tag):
            traducao = tag + traducao
    return traducao


def executar_limpeza():
    print("=" * 80)
    print(f"{Fore.CYAN}    SCRIPT DE LIMPEZA DIRETA DE ERROS RESIDUAIS (PENTE FINO)")
    print("=" * 80)

    if len(sys.argv) >= 3:
        pasta_originais = sys.argv[1]
        pasta_traduzidos = sys.argv[2]
    else:
        pasta_originais = (
            r"D:\PROJETOS-OPEN\animes"
            r"\Mobile Suit Gundam Unicorn Re0096 (2016) [Season 1] [BD 1080p HEVC OPUS] [Dual-Audio]"
            r"\Season 1\legendas_eng"
        )
        pasta_traduzidos = (
            r"D:\PROJETOS-OPEN\animes"
            r"\Mobile Suit Gundam Unicorn Re0096 (2016) [Season 1] [BD 1080p HEVC OPUS] [Dual-Audio]"
            r"\Season 1\legendas_ptbr"
        )

    if not os.path.exists(pasta_originais) or not os.path.exists(pasta_traduzidos):
        print(f"{Fore.RED}[ERRO] Pastas de legendas não encontradas.")
        return

    arquivos_ptbr = sorted([f for f in os.listdir(pasta_traduzidos) if f.lower().endswith('.ass')])

    if not arquivos_ptbr:
        print(f"{Fore.YELLOW}[AVISO] Nenhum arquivo .ass em: {pasta_traduzidos}")
        return

    total_limpezas = 0

    for arquivo in arquivos_ptbr:
        caminho_pt = os.path.join(pasta_traduzidos, arquivo)
        nome_eng = arquivo.replace("_PTBR.ass", "_ENG.ass")
        caminho_eng = os.path.join(pasta_originais, nome_eng)

        if not os.path.exists(caminho_eng):
            continue

        with open(caminho_pt, 'r', encoding='utf-8', errors='replace') as f:
            linhas_pt = f.readlines()

        with open(caminho_eng, 'r', encoding='utf-8', errors='replace') as f:
            linhas_eng = f.readlines()

        if len(linhas_pt) != len(linhas_eng):
            continue

        linhas_corrigidas = list(linhas_pt)
        limpezas_no_arquivo = 0

        for i in range(len(linhas_pt)):
            linha_pt = linhas_pt[i]
            # Detecta o marcador de erro residual
            if linha_pt.startswith("Dialogue:") and "[ERRO_TRADUCAO:" in linha_pt:
                linha_eng = linhas_eng[i]
                partes_pt = linha_pt.split(",", 9)
                partes_eng = linha_eng.split(",", 9)

                if len(partes_pt) != 10 or len(partes_eng) != 10:
                    continue

                metadados = ",".join(partes_pt[:9]) + ","
                texto_original = partes_eng[9].rstrip("\n")

                # Extrai tags e gera placeholders temporários
                tags = re.findall(r'\{[^}]+\}', texto_original)
                texto_limpo = texto_original
                for idx_tag, tag in enumerate(tags):
                    texto_limpo = texto_limpo.replace(tag, f"[T{idx_tag}]", 1)

                # Restaura as tags no texto limpo de forma segura
                texto_final = restaurar_tags(texto_limpo, tags)

                linhas_corrigidas[i] = f"{metadados}{texto_final}\n"
                limpezas_no_arquivo += 1
                total_limpezas += 1
                print(f"  -> [{arquivo}] Linha {i+1} limpa: '{texto_original}'")

        if limpezas_no_arquivo > 0:
            with open(caminho_pt, 'w', encoding='utf-8') as f:
                f.writelines(linhas_corrigidas)
            print(f"{Fore.GREEN}[SALVO] {arquivo} | {limpezas_no_arquivo} erro(s) residual(is) corrigido(s).")

    print("\n" + "=" * 80)
    print(f"{Fore.GREEN}[CONCLUÍDO] Limpeza finalizada! Total de erros limpos: {total_limpezas}")
    print("=" * 80)


if __name__ == "__main__":
    executar_limpeza()
