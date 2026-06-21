#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: aplica_linhas_revisadas.py
Lê as linhas corrigidas em linhas_revisadas.json e as grava de volta
nos arquivos .ass correspondentes, além de atualizar o cache global.

Author: Antigravity
Data: Junho 2026
"""

import os
import re
import json
import sys

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PASTA_RAIZ = os.path.dirname(os.path.dirname(PASTA_SCRIPT))
CAMINHO_CACHE = os.path.join(PASTA_RAIZ, "05b_tradutor_llm_mistral_nemo", "frances_para_ptbr", "traducao_cache_fr.json")
PASTA_LEGENDAS = r"C:\animes\Mobile_Suit_Gundam_The_Origin_Advent_of_the_Red_Comet\legendas_ptbr"

CAMINHO_REVISADAS = os.path.join(PASTA_SCRIPT, "linhas_revisadas.json")
CAMINHO_PARA_REVISAR = os.path.join(PASTA_SCRIPT, "linhas_para_revisar.json")

def limpar_saida_para_cache(texto: str) -> str:
    """Limpa e formata a saída para salvar no cache."""
    texto = texto.strip()
    texto = re.sub(r"^\s*[-–•]\s*", "", texto)
    texto = re.sub(r"\[\s*[Tt]\s*(\d+)\s*\]", r"[T\1]", texto)
    texto = re.sub(r"\\\s*([Nnh])", r"\\\1", texto)
    texto = texto.replace("/N", r"\N").replace("/n", r"\n")
    return texto

def aplicar():
    if not os.path.exists(CAMINHO_REVISADAS):
        print(f"[ERRO] Arquivo de revisões não encontrado: {CAMINHO_REVISADAS}")
        return

    # 1. Carrega as correções
    with open(CAMINHO_REVISADAS, 'r', encoding='utf-8') as f:
        corricoes = json.load(f)

    # 2. Carrega o mapeamento original para obter o francês
    mapeamento_fr = {}
    if os.path.exists(CAMINHO_PARA_REVISAR):
        with open(CAMINHO_PARA_REVISAR, 'r', encoding='utf-8') as f:
            itens_para_revisar = json.load(f)
        for item in itens_para_revisar:
            key = (item["arquivo"], item["linha_idx"])
            mapeamento_fr[key] = item["original_fr"]

    # 3. Carrega o cache
    if os.path.exists(CAMINHO_CACHE):
        with open(CAMINHO_CACHE, 'r', encoding='utf-8') as f:
            cache_original = json.load(f)
    else:
        cache_original = {}

    print(f"[INFO] Aplicando {len(corricoes)} correções...")

    # Agrupar correções por arquivo .ass
    corricoes_por_arquivo = {}
    for c in corricoes:
        arq = c["arquivo"]
        if arq not in corricoes_por_arquivo:
            corricoes_por_arquivo[arq] = []
        corricoes_por_arquivo[arq].append(c)

    pat_dialogue = re.compile(r"^(Dialogue:\s*[^,]*(?:,[^,]*){8},)(.*)$")
    total_aplicado = 0

    for arquivo, lista_c in corricoes_por_arquivo.items():
        caminho_file = os.path.join(PASTA_LEGENDAS, arquivo)
        if not os.path.exists(caminho_file):
            print(f"[AVISO] Arquivo de legenda não encontrado: {caminho_file}")
            continue

        # Ler arquivo com assinatura UTF-8 (utf-8-sig)
        with open(caminho_file, 'r', encoding='utf-8-sig') as f:
            linhas = f.readlines()

        modificado = False
        for c in lista_c:
            idx = c["linha_idx"]
            novo_texto = c["texto_pt"]

            if idx >= len(linhas):
                print(f"[ERRO] Índice de linha {idx} inválido para {arquivo}")
                continue

            linha = linhas[idx]
            m = pat_dialogue.match(linha.strip())
            if m:
                prefixo = m.group(1)
                texto_antigo = m.group(2).strip()

                if texto_antigo != novo_texto:
                    linhas[idx] = f"{prefixo}{novo_texto}\n"
                    modificado = True
                    total_aplicado += 1
                    print(f"  [{arquivo} L{idx+1}]:\n    Antes : {texto_antigo}\n    Depois: {novo_texto}")

                    # Atualizar o cache de tradução
                    key = (arquivo, idx)
                    original_fr = mapeamento_fr.get(key)
                    if original_fr:
                        fr_limpo = limpar_saida_para_cache(original_fr)
                        pt_limpo = limpar_saida_para_cache(novo_texto)
                        cache_original[fr_limpo] = pt_limpo

        if modificado:
            # Salvar de volta com assinatura utf-8-sig
            with open(caminho_file, 'w', encoding='utf-8-sig') as f:
                f.writelines(linhas)
            print(f"[SALVO] {arquivo} atualizado.")

    # 4. Salvar cache atualizado
    if cache_original:
        try:
            with open(CAMINHO_CACHE, 'w', encoding='utf-8') as f:
                json.dump(cache_original, f, indent=2, ensure_ascii=False)
            print(f"[SALVO] Cache de tradução atualizado em {CAMINHO_CACHE}")
        except Exception as e:
            print(f"[ERRO] Falha ao salvar cache de tradução: {e}")

    print(f"[CONCLUÍDO] Total de {total_aplicado} correções aplicadas em {len(corricoes_por_arquivo)} episódios.")

if __name__ == "__main__":
    aplicar()
