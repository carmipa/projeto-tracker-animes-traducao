#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import glob
import re

PASTA_ALVO = r"E:\animes\GUNDAM\GUNDAM UC\UC 0068 - ORIGIN\Mobile_Suit_Gundam_The_Origin_Advent_of_the_Red_Comet\legendas_eng"

DICIONARIO_TOTAL = {
    # Francesismos & Vocabulário
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
    "Euh...": "É...",
    
    # Concordância e Militares
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
    "Você sugere que seria ele\\Nde deter a frota": "Você sugere que seria ele\\Na deter a frota",
    "eses absurdos": "esses absurdos",
    "aque o filho": "aquele filho",
    "Nm as prometo": "Nmas não prometo",
    "capa\\Dos oficiais": "capa\\Ndos oficiais",
    "é\\O comandante": "é\\No comandante",
    "inutilmente\\Nresistir-nos.": "inutilmente\\Na resistir-nos.",
    "eliminar\\A resistência": "eliminar\\Na resistência",
    "gênero humano\\Niria a ódio": "gênero humano\\Nlevaria ao ódio",
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

def higienizar_linha(texto):
    # 1. Resolver as barras \N espalhadas com espaço
    texto = texto.replace('\\N ', '\\N')
    texto = texto.replace(' \\N', '\\N')
    texto = texto.replace('\\n ', '\\N')
    texto = texto.replace(' \\n', '\\N')
    texto = texto.replace('\\n', '\\N')
    
    # 2. Barra solitária solta com espaço (sem N)
    texto = texto.replace('\\ ', ' ')
    
    # 3. Dicionário Unificado
    for errado, correto in DICIONARIO_TOTAL.items():
        if errado in texto:
            texto = texto.replace(errado, correto)
            
    return texto

def varrer_tudo():
    arquivos = glob.glob(os.path.join(glob.escape(PASTA_ALVO), '*_PTBR_ENG.ass'))
    alvos = [arq for arq in arquivos if 'S01' in arq and not arq.endswith('_REVISADO.ass')]
    
    alvos.sort()

    padrao_dialogo = re.compile(r'^(Dialogue:\s*[^,]*(?:,[^,]*){8},)(.*)$')

    total_correcoes = 0

    print("="*50)
    print(" VARREDURA TOTAL: ORIGIN (EP 01 a 13)")
    print("="*50)

    for arq in alvos:
        nome_ep = os.path.basename(arq).split("S01")[1].split(" ")[0]
        
        with open(arq, 'r', encoding='utf-8-sig') as f:
            linhas = f.readlines()
            
        modificacoes_ep = 0
        
        for i, linha in enumerate(linhas):
            match = padrao_dialogo.match(linha)
            if match:
                prefixo = match.group(1)
                texto = match.group(2).strip()
                
                texto_limpo = higienizar_linha(texto)
                
                if texto != texto_limpo:
                    linhas[i] = prefixo + texto_limpo + "\n"
                    modificacoes_ep += 1
                    total_correcoes += 1
                    
        if modificacoes_ep > 0:
            with open(arq, 'w', encoding='utf-8') as f:
                f.writelines(linhas)
            print(f"[EPISÓDIO {nome_ep}]: {modificacoes_ep} falhas consertadas.")
        else:
            print(f"[EPISÓDIO {nome_ep}]: Legenda impecável. Nenhuma anomalia.")

    print("="*50)
    print(f" TOTAL DE ANOMALIAS EXPURGADAS NA SÉRIE: {total_correcoes}")
    print("="*50)

if __name__ == "__main__":
    varrer_tudo()
