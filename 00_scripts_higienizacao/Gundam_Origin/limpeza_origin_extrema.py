#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import glob
import re
from colorama import init, Fore, Style

init(autoreset=True)

PASTA_ALVO = r"E:\animes\GUNDAM\GUNDAM UC\UC 0068 - ORIGIN\Mobile_Suit_Gundam_The_Origin_Advent_of_the_Red_Comet\legendas_eng"

# Termos de lore/marca: sempre normalizados para a grafia oficial,
# em QUALQUER caixa e posição na frase.
LORE_PROPRIO = {
    "Traje Móvel": "Mobile Suit",
    "Trajes Móveis": "Mobile Suits",
    "Novo Tipo": "Newtype",
    "Novos Tipos": "Newtypes",
    "Base Branca": "White Base",
    "Três Estrelas Negras": "Black Tri-Stars",
    "Cometa Rubro": "Cometa Vermelho",
    "vaso almirante": "nave capitânia",
    "vaso de guerra": "nave de guerra",
    "Federação da Terra": "Federação Terrestre",
    "Colocar na bochecha": "Mirar",
}

# Francesismos residuais, gafes de tradução literal do inglês, correções narrativas
# específicas (achadas em auditoria real dos EP 11-13 e varredura completa S01),
# esquizofrenia Tu/Você, concordância e redundâncias.
# A caixa da primeira letra do trecho ORIGINAL é preservada na troca.
GRAMATICA_E_GAFES = {
    # ----------------------------------------------------
    # FRANCESISMOS RESIDUAIS E VOCABULÁRIO (pipeline tem fonte francesa)
    # ----------------------------------------------------
    "L'inimigo": "O inimigo", "l'inimigo": "o inimigo",
    "L'inimiga": "A inimiga", "l'inimiga": "a inimiga",
    "L'Ave Azul": "A Ave Azul",
    "appontagem": "pouso",
    "estra nos": "está nos",
    "deployar": "enviar",
    "Demande vetor": "Solicito vetor",
    "Euh...": "É...",
    "Zéon": "Zeon",

    # ----------------------------------------------------
    # CORREÇÕES NARRATIVAS ESPECÍFICAS (EP 11 a 13 e varredura S01)
    # ----------------------------------------------------
    "À ordens.": "Às ordens.", "À ordens!": "Às ordens!",
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
    "em gaiola": "na gaiola",
    "Peguemos rumo": "Tomemos rumo",
    "Aquela que destruiu": "Aquele que destruiu",
    "\\NE mesmo sendo": "\\Nmesmo sendo",
    "Sua bolsa com as memórias.": "Sua pasta com os dados.",
    "mal... traí... te...": "mal... trata... ram...",
    "juro de dedicar": "juro dedicar",
    "diante a ditadura!": "diante da ditadura!",
    "de levar um conflito a longo prazo!": "de travar um conflito de longo prazo!",
    "Igore a noite": "Ignore a noite",

    # ----------------------------------------------------
    # GAFES DE TRADUÇÃO DIRETA DO INGLÊS (LLMs)
    # ----------------------------------------------------
    "Eu vejo.": "Entendo.",
    "Olhe fora!": "Cuidado!",
    "Você é direito": "Você tem razão",
    "Que o inferno": "Que diabos",
    "Que inferno": "Que diabos",
    "Merda sagrada": "Puta merda",
    "Oh meu Deus": "Meu Deus",

    # ----------------------------------------------------
    # ESQUIZOFRENIA TU/VOCÊ - VERBOS
    # ----------------------------------------------------
    "Tu tem": "Você tem", "Tu tens": "Você tem", "Você tens": "Você tem",
    "Tu está": "Você está", "Tu estás": "Você está", "Você estás": "Você está",
    "Tu vem": "Você vem", "Tu vens": "Você vem", "Você vens": "Você vem",
    "Tu foi": "Você foi", "Tu foste": "Você foi", "Você foste": "Você foi",
    "Tu deve": "Você deve", "Tu deves": "Você deve", "Você deves": "Você deve",
    "Tu sabe": "Você sabe", "Tu sabes": "Você sabe", "Você sabes": "Você sabe",
    "Tu quer": "Você quer", "Tu queres": "Você quer", "Você queres": "Você quer",
    "Tu vai": "Você vai", "Tu vais": "Você vai", "Você vais": "Você vai",
    "Tu consegue": "Você consegue", "Tu consegues": "Você consegue", "Você consegues": "Você consegue",
    "Tu fez": "Você fez", "Tu fizeste": "Você fez", "Você fizeste": "Você fez",
    "Tu é": "Você é", "Tu és": "Você é", "Você és": "Você é",
    "Tu pode": "Você pode", "Tu podes": "Você pode", "Você podes": "Você pode",
    "Tu faz": "Você faz", "Tu fazes": "Você faz", "Você fazes": "Você faz",

    # ----------------------------------------------------
    # ESQUIZOFRENIA TU/VOCÊ - PRONOMES E PREPOSIÇÕES
    # ----------------------------------------------------
    "pra tu": "para você", "para tu": "para você", "com tu": "com você",
    "teu": "seu", "tua": "sua", "teus": "seus", "tuas": "suas",

    # ----------------------------------------------------
    # CONCORDÂNCIA DE GÊNERO - SUBSTANTIVOS MASCULINOS TERMINADOS EM "-A"
    # ----------------------------------------------------
    "a problema": "o problema", "uma problema": "um problema",
    "a sistema": "o sistema", "uma sistema": "um sistema",
    "a programa": "o programa", "uma programa": "um programa",
    "a mapa": "o mapa", "uma mapa": "um mapa",
    "a clima": "o clima", "uma clima": "um clima",
    "a tema": "o tema", "uma tema": "um tema",
    "a esquema": "o esquema", "uma esquema": "um esquema",
    "a fantasma": "o fantasma", "uma fantasma": "um fantasma",
    "a drama": "o drama", "uma drama": "um drama",
    "a dilema": "o dilema", "uma dilema": "um dilema",

    # ----------------------------------------------------
    # REDUNDÂNCIAS E ERROS GRAMATICAIS BÁSICOS
    # ----------------------------------------------------
    "há muitos anos atrás": "muitos anos atrás",
    "encarar de frente": "encarar",
    "entrar para dentro": "entrar",
    "subir para cima": "subir",
}


def _compilar_dicionario(dicionario):
    compilado = []
    for frase, correto in dicionario.items():
        nucleo = re.escape(frase)
        prefixo = r'\b' if frase[0].isalnum() else ''
        sufixo = r'\b' if frase[-1].isalnum() else ''
        compilado.append((re.compile(prefixo + nucleo + sufixo, re.IGNORECASE), correto))
    return compilado


def _preservar_caixa(correto, encontrado):
    if encontrado[:1].isupper():
        return correto[:1].upper() + correto[1:]
    return correto[:1].lower() + correto[1:]


def _balancear_tag(t, abre, fecha):
    aberturas = t.count(abre)
    fechamentos = t.count(fecha)
    if aberturas > fechamentos:
        t += fecha * (aberturas - fechamentos)
    return t


_LORE_COMPILADO = _compilar_dicionario(LORE_PROPRIO)
_GRAMATICA_COMPILADO = _compilar_dicionario(GRAMATICA_E_GAFES)


def higienizar_linha(texto):
    texto_original = texto
    t = texto

    # 1. Resolver as infames barras erráticas e quebra de ASS
    t = t.replace('\\N ', '\\N').replace(' \\N', '\\N')
    t = t.replace('\\n ', '\\N').replace(' \\n', '\\N').replace('\\n', '\\N')
    t = t.replace('\\ ', ' ')

    # 2. Remoção de QUALQUER tag ASS duplicada consecutiva
    t = re.sub(r'(\{\\[^{}]+\})\1+', r'\1', t)

    # 3. Normalização de espaçamento e pontuação (preserva "..." de propósito)
    t = re.sub(r' {2,}', ' ', t)
    t = re.sub(r' +([,.!?;:])(?!\.\.)', r'\1', t)

    # 4. Dicionário de Lore (grafia oficial fixa, qualquer caixa/posição na frase)
    for padrao, correto in _LORE_COMPILADO:
        t = padrao.sub(lambda m, c=correto: c, t)

    # 5. Dicionário de Gramática/Gafes/Francesismos (preserva a caixa do trecho original)
    for padrao, correto in _GRAMATICA_COMPILADO:
        t = padrao.sub(lambda m, c=correto: _preservar_caixa(c, m.group(0)), t)

    # 6. CORREÇÃO AVANÇADA DE TAGS ÓRFÃS (itálico e negrito)
    t = _balancear_tag(t, "{\\i1}", "{\\i0}")
    t = _balancear_tag(t, "{\\b1}", "{\\b0}")

    return t, t != texto_original


def obter_pasta_alvo():
    """Pergunta a pasta a higienizar; ENTER aceita o caminho padrão (PASTA_ALVO)."""
    while True:
        entrada = input(
            f"{Fore.CYAN}Pasta com as legendas .ass de Origin (ENTER = {PASTA_ALVO}): {Style.RESET_ALL}"
        ).strip().strip('"').strip("'")

        if not entrada:
            entrada = PASTA_ALVO

        if not os.path.isdir(entrada):
            print(f"{Fore.RED}[ERRO] O diretório especificado não existe: {entrada}")
            continue

        return entrada


def varrer_tudo():
    print(Fore.MAGENTA + "="*50)
    print(Fore.MAGENTA + " VARREDURA EXTREMA: GUNDAM ORIGIN (V3 - MOTOR REGEX)")
    print(Fore.MAGENTA + "="*50)

    pasta_alvo = obter_pasta_alvo()

    arquivos = glob.glob(os.path.join(glob.escape(pasta_alvo), '*_PTBR_ENG.ass'))
    alvos = [arq for arq in arquivos if 'S01' in arq and not arq.endswith('_REVISADO.ass')]
    alvos.sort()

    if not alvos:
        print(f"{Fore.YELLOW}[AVISO] Nenhum arquivo *_PTBR_ENG.ass de S01 encontrado na pasta.")
        return

    padrao_dialogo = re.compile(r'^(Dialogue:\s*[^,]*(?:,[^,]*){8},)(.*)$')

    total_correcoes = 0

    for arq in alvos:
        nome_ep = os.path.basename(arq)
        print(f"{Fore.CYAN}\n--- Lendo: {nome_ep} ---")

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
                    print(f"   {Fore.RED}[ORIGINAL] : {texto}")
                    print(f"   {Fore.GREEN}[CORRIGIDO]: {texto_limpo}{Style.RESET_ALL}\n")

        if modificacoes_ep > 0:
            with open(arq, 'w', encoding='utf-8') as f:
                f.writelines(linhas)
            print(f"{Fore.GREEN}[ARQUIVO] {nome_ep}: {modificacoes_ep} novos fantasmas exorcizados.")
        else:
            print(f"{Fore.CYAN}[ARQUIVO] {nome_ep}: Legenda blindada. Nenhuma anomalia.")

    print(Fore.MAGENTA + "="*50)
    print(f"{Fore.MAGENTA} TOTAL DE FANTASMAS DESTRUÍDOS: {total_correcoes}")
    print(Fore.MAGENTA + "="*50)


if __name__ == "__main__":
    varrer_tudo()
