#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import glob
import re

PASTA_ALVO = r"E:\animes\GUNDAM\GUNDAM UC\UC 0068 - ORIGIN\Mobile_Suit_Gundam_The_Origin_Advent_of_the_Red_Comet\legendas_eng"

DICIONARIO_TOTAL = {
    # ----------------------------------------------------
    # CORREÇÕES DE ORIGIN (EP 11 a 13 e Varredura Inicial)
    # ----------------------------------------------------
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
    "Igore a noite": "Ignore a noite",
    
    # ----------------------------------------------------
    # NOVAS CORREÇÕES EXTREMAS (LORE GUNDAM E FRANCESISMOS)
    # ----------------------------------------------------
    "Base Branca": "White Base",
    "base branca": "White Base",
    "Três Estrelas Negras": "Black Tri-Stars",
    "Cometa Rubro": "Cometa Vermelho",
    "vaso almirante": "nave capitânia",
    "Vaso almirante": "Nave capitânia",
    "vaso de guerra": "nave de guerra",
    "Vaso de guerra": "Nave de guerra",
    "Colocar na bochecha": "Mirar",
    "colocar na bochecha": "mirar",
    
    # ----------------------------------------------------
    # ESQUIZOFRENIA DE PRONOMES (TU / VOCÊ)
    # ----------------------------------------------------
    "Você tens": "Você tem",
    "Você estás": "Você está",
    "Você vens": "Você vem",
    "Tu tem": "Você tem",
    "Tu sabe": "Você sabe",
    "Tu quer": "Você quer",
    "Tu vai": "Você vai"
}

def higienizar_linha(texto):
    modificado = False
    texto_original = texto
    
    # 1. Resolver barras erráticas (já passamos isso, mas passaremos de novo para garantir)
    t = texto.replace('\\N ', '\\N').replace(' \\N', '\\N').replace('\\n ', '\\N').replace(' \\n', '\\N').replace('\\n', '\\N')
    t = t.replace('\\ ', ' ')
    
    # 2. Dicionário Unificado Massivo
    for errado, correto in DICIONARIO_TOTAL.items():
        if errado in t:
            t = t.replace(errado, correto)
            
    # 3. TAGS ÓRFÃS: Se abriu o itálico com {\i1} mas esqueceu de fechar com {\i0}
    if "{\\i1}" in t and "{\\i0}" not in t:
        t = t + "{\\i0}"
        
    if t != texto_original:
        modificado = True
        
    return t, modificado

def varrer_tudo():
    arquivos = glob.glob(os.path.join(glob.escape(PASTA_ALVO), '*_PTBR_ENG.ass'))
    alvos = [arq for arq in arquivos if 'S01' in arq and not arq.endswith('_REVISADO.ass')]
    alvos.sort()

    padrao_dialogo = re.compile(r'^(Dialogue:\s*[^,]*(?:,[^,]*){8},)(.*)$')

    total_correcoes = 0

    print("="*50)
    print(" VARREDURA EXTREMA: O PENTE-FINO DA LORE")
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
                
                texto_limpo, modificado = higienizar_linha(texto)
                
                if modificado:
                    linhas[i] = prefixo + texto_limpo + "\n"
                    modificacoes_ep += 1
                    total_correcoes += 1
                    
        if modificacoes_ep > 0:
            with open(arq, 'w', encoding='utf-8') as f:
                f.writelines(linhas)
            print(f"[EPISÓDIO {nome_ep}]: {modificacoes_ep} novos fantasmas exorcizados.")
        else:
            print(f"[EPISÓDIO {nome_ep}]: Legenda blindada. Nenhuma anomalia.")

    print("="*50)
    print(f" TOTAL DE FANTASMAS EXTRAS DESTRUÍDOS: {total_correcoes}")
    print("="*50)

if __name__ == "__main__":
    varrer_tudo()
