#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import glob
import re

PASTA_ALVO = r"E:\animes\GUNDAM\GUNDAM UC\UC 0068 - ORIGIN\Mobile_Suit_Gundam_The_Origin_Advent_of_the_Red_Comet\legendas_eng"

SUBSTITUICOES_TEXTUAIS = {
    "L'inimigo": "O inimigo",
    "l'inimigo": "o inimigo",
    "L'inimiga": "A inimiga",
    "l'inimiga": "a inimiga",
    "appontagem": "pouso",
    "Appontagem": "Pouso",
    "estra nos": "está nos",
    "Estra nos": "Está nos",
    "deployar": "enviar",
    "Deployar": "Enviar",
    "Demande vetor": "Solicito vetor",
    "demande vetor": "solicito vetor",
    "Euh...": "É..."
}

def higienizar_texto(texto):
    # Correção do erro de barra (\N com espaço ou minúsculo)
    texto = texto.replace('\\N ', '\\N')
    texto = texto.replace(' \\N', '\\N')
    texto = texto.replace('\\n ', '\\N')
    texto = texto.replace(' \\n', '\\N')
    texto = texto.replace('\\n', '\\N')
    
    # Barra invertida perdida seguida de espaço
    texto = texto.replace('\\ ', ' ')
    
    # Francesismos e erros
    for errado, correto in SUBSTITUICOES_TEXTUAIS.items():
        texto = texto.replace(errado, correto)
        
    return texto

def processar_arquivos():
    arquivos = glob.glob(os.path.join(glob.escape(PASTA_ALVO), '*_PTBR_ENG.ass'))
    alvos = [arq for arq in arquivos if 'S01E11' in arq or 'S01E12' in arq or 'S01E13' in arq]
    
    if not alvos:
        print("Nenhum arquivo E11, E12 ou E13 encontrado!")
        return

    padrao_dialogo = re.compile(r'^(Dialogue:\s*[^,]*(?:,[^,]*){8},)(.*)$')

    for arq in alvos:
        print(f"Processando: {os.path.basename(arq)}")
        
        with open(arq, 'r', encoding='utf-8-sig') as f:
            linhas = f.readlines()
            
        modificacoes = 0
        
        for i, linha in enumerate(linhas):
            match = padrao_dialogo.match(linha)
            if match:
                prefixo = match.group(1)
                texto = match.group(2).strip()
                
                texto_limpo = higienizar_texto(texto)
                
                if texto != texto_limpo:
                    linhas[i] = prefixo + texto_limpo + "\n"
                    modificacoes += 1
                    
        if modificacoes > 0:
            with open(arq, 'w', encoding='utf-8') as f:
                f.writelines(linhas)
            print(f"  -> {modificacoes} falhas corrigidas e salvas.")
        else:
            print("  -> Nenhuma falha detectada.")

if __name__ == "__main__":
    processar_arquivos()
