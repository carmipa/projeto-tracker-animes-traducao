#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import glob
import re

PASTA_ALVO = r"E:\animes\GUNDAM\GUNDAM UC\UC 0068 - ORIGIN\Mobile_Suit_Gundam_The_Origin_Advent_of_the_Red_Comet\legendas_eng"

# O "Cérebro do Antigravity" - Dicionário de Correção Contextual de Francês para PT-BR Nativo
DICIONARIO_GRAMATICAL = {
    # Erros militares / Expressões
    "À ordens.": "Às ordens.",
    "À ordens!": "Às ordens!",
    "Reme para bombordo!": "Vire para bombordo!",
    "Reme à bombordo": "Vire a bombordo",
    "À ataque!": "Ao ataque!",
    "Você quem eu sou?": "Sabe quem eu sou?",
    "afetado ao QG": "designado ao QG",
    "na primeira linha\\NPara cobrir-me de glória!": "na linha de frente\\Npara cobrir-me de glória!",
    "que droga!": "uma ova!",
    "intervenientes no local": "civis no local",
    "Vamos, essa é": "Ora, essa é",
    "oficial reserva como eu": "oficial da reserva como eu",
    
    # Concordância / Preposições / Pronomes
    "Você sugere que seria ele\\Nde deter a frota": "Você sugere que seria ele\\Na deter a frota",
    "eses absurdos": "esses absurdos",
    "aque o filho": "aquele filho",
    "Nm as prometo": "Nmas não prometo",
    "capa\\Dos oficiais": "capa\\Ndos oficiais",
    "é\\O comandante": "é\\No comandante",
    "inutilmente\\Nresistir-nos.": "inutilmente\\Na resistir-nos.",
    "eliminar\\A resistência": "eliminar\\Na resistência",
    "gênero humano\\Niria a ódio": "gênero humano\\Nlevaria a ódio",
    "\\La guerra deve continuar.": "\\NA guerra deve continuar.",
    "tomar\\Nriscos da Terra.": "tomar\\No controle da Terra.",
    "de ele é o filho": "de que ele é o filho",
    "não tenho muito Gihren...\\Nno meu coração.": "não vou com a cara...\\Nde Gihren.",
    "me deixa para segui-lo.": "me deixe para segui-lo.",
    "descansar sua oferta.": "recusar sua oferta.",
    "Não arranque nossos oficiais.": "Não roube nossos oficiais.",
    "a uniforme": "um uniforme",
    "L'Ave Azul": "A Ave Azul",
    "em gaiola": "na gaiola",
    "Peguemos rumo": "Tomemos rumo",
    "Aquela que destruiu": "Aquele que destruiu",
    "\\NE mesmo sendo": "\\Nmesmo sendo",
    "Sua bolsa com as memórias.": "Sua pasta com os dados.",
    "mal... traí... te...": "mal... trata... ram...",
    "juro de dedicar": "juro dedicar",
    "diante a ditadura!": "diante da ditadura!",
    "Zéon é incapaz": "Zeon é incapaz",
    "de levar um conflito a longo prazo!": "de travar um conflito de longo prazo!",
    "Igore a noite": "Ignore a noite"
}

def corrigir_texto(texto):
    for errado, correto in DICIONARIO_GRAMATICAL.items():
        if errado in texto:
            texto = texto.replace(errado, correto)
    return texto

def processar():
    arquivos = glob.glob(os.path.join(glob.escape(PASTA_ALVO), '*_PTBR_ENG.ass'))
    alvos = [arq for arq in arquivos if 'S01E11' in arq or 'S01E12' in arq or 'S01E13' in arq]
    
    padrao_dialogo = re.compile(r'^(Dialogue:\s*[^,]*(?:,[^,]*){8},)(.*)$')

    for arq in alvos:
        print(f"Inspecionando e corrigindo: {os.path.basename(arq)}")
        
        with open(arq, 'r', encoding='utf-8-sig') as f:
            linhas = f.readlines()
            
        modificacoes = 0
        
        for i, linha in enumerate(linhas):
            match = padrao_dialogo.match(linha)
            if match:
                prefixo = match.group(1)
                texto = match.group(2).strip()
                
                texto_limpo = corrigir_texto(texto)
                
                if texto != texto_limpo:
                    linhas[i] = prefixo + texto_limpo + "\n"
                    modificacoes += 1
                    print(f"   [+] Corrigido: {texto} -> {texto_limpo}")
                    
        if modificacoes > 0:
            with open(arq, 'w', encoding='utf-8') as f:
                f.writelines(linhas)
            print(f"  -> {modificacoes} falhas gramaticais profundas consertadas.\n")
        else:
            print("  -> Nenhuma falha detectada nesta varredura.\n")

if __name__ == "__main__":
    processar()
