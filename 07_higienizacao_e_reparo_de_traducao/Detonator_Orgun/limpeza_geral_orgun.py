#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import glob
import re
from colorama import init, Fore, Style

init(autoreset=True)

PASTA_ALVO = r"E:\animes\DETONATOR ORGUN\legendas_ptbr"

_PADRAO_TIMECODE_SRT = re.compile(r'-->')
_PADRAO_INDICE_SRT = re.compile(r'^\d+$')

# Termos de lore/marca: sempre normalizados para a grafia oficial,
# em QUALQUER caixa e posição na frase.
LORE_PROPRIO = {
    "Earth Defense Force": "E.D.F.",
    "EDF": "E.D.F.",
    "o Orgun": "Orgun",
    "do Orgun": "de Orgun",
    "ao Orgun": "a Orgun",
}

# Gafes de tradução literal do inglês, esquizofrenia Tu/Você, concordância e redundâncias.
# A caixa da primeira letra do trecho ORIGINAL é preservada na troca.
GRAMATICA_E_GAFES = {
    # ----------------------------------------------------
    # GAFES DE TRADUÇÃO DIRETA DO INGLÊS (LLMs)
    # ----------------------------------------------------
    "Eu vejo.": "Entendo.",
    "Olhe fora!": "Cuidado!",
    "Olha fora!": "Cuidado!",
    "Você é direito": "Você tem razão",
    "Você está direito": "Você tem razão",
    "Que o inferno": "Que diabos",
    "Que inferno": "Que diabos",
    "Merda sagrada": "Puta merda",
    "Oh meu Deus": "Meu Deus",
    "De nenhuma maneira": "De jeito nenhum",
    "Atualmente ": "Na verdade ",
    "atualmente ": "na verdade ",
    "Desgraçadamente": "Infelizmente",
    "desgraçadamente": "infelizmente",

    # ----------------------------------------------------
    # GERUNDISMOS E VÍCIOS DE TRADUÇÃO
    # ----------------------------------------------------
    "vou estar fazendo": "vou fazer",
    "vou estar indo": "vou",
    "vamos estar fazendo": "vamos fazer",
    "vou estar ajudando": "vou ajudar",

    # ----------------------------------------------------
    # MAIS VS MAS (CONFUSÕES COMUNS DO CONTEXTO DE TRADUÇÃO)
    # ----------------------------------------------------
    ", mais eu ": ", mas eu ",
    ", mais você ": ", mas você ",
    ", mais ele ": ", mas ele ",
    ", mais ela ": ", mas ela ",
    ", mais nós ": ", mas nós ",
    ", mais eles ": ", mas eles ",
    ", mais não ": ", mas não ",
    ", mais sim ": ", mas sim ",


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

    # 1. Resolver barras erráticas e quebra de ASS, e franglês residual
    t = t.replace('\\N ', '\\N').replace(' \\N', '\\N')
    t = t.replace('\\\\N', '\\N').replace('\\\\n', '\\N')
    t = re.sub(r'\\N\s+\\N', r'\\N', t)
    t = t.replace('\\Net ', '\\N e ').replace('\\NEt ', '\\N E ')
    t = re.sub(r'\[ERRO_TRADUCAO\]', '', t)

    # 2. Remoção de QUALQUER tag ASS duplicada consecutiva
    t = re.sub(r'(\{\\[^{}]+\})\1+', r'\1', t)

    # 3. Normalização de espaçamento e pontuação (preserva "..." de propósito)
    t = re.sub(r' {2,}', ' ', t)
    t = re.sub(r' +([,.!?;:])(?!\.\.)', r'\1', t)
    # Normaliza 4 ou mais pontos seguidos para exatamente 3 pontos (reticências)
    t = re.sub(r'\.{4,}', '...', t)
    # Normaliza exatamente 2 pontos isolados para exatamente 3 pontos (reticências)
    t = re.sub(r'(?<!\.)\.\.(?!\.)', '...', t)

    # 4. Sigla E.D.F. - normaliza 0, 1 ou vários pontos finais para exatamente um
    t = re.sub(r'\bE\.D\.F\.*(?!\w)', 'E.D.F.', t, flags=re.IGNORECASE)

    # 5. Dicionário de Lore (grafia oficial fixa, qualquer caixa/posição na frase)
    for padrao, correto in _LORE_COMPILADO:
        t = padrao.sub(lambda m, c=correto: c, t)

    # 6. Dicionário de Gramática/Gafes (preserva a caixa do trecho original)
    for padrao, correto in _GRAMATICA_COMPILADO:
        t = padrao.sub(lambda m, c=correto: _preservar_caixa(c, m.group(0)), t)

    # 7. CORREÇÃO AVANÇADA DE TAGS ÓRFÃS (itálico e negrito) - relevante só em .ass
    t = _balancear_tag(t, "{\\i1}", "{\\i0}")
    t = _balancear_tag(t, "{\\b1}", "{\\b0}")

    return t, t != texto_original


def _regra_de_ouro_ass(t):
    """Desgruda o \\N da palavra seguinte (só faz sentido em .ass)."""
    return re.sub(r'\\N([a-zA-ZáéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ])', r'\\N \1', t)


def obter_pasta_alvo():
    """Pergunta a pasta a higienizar; ENTER aceita o caminho padrão (PASTA_ALVO)."""
    while True:
        entrada = input(
            f"{Fore.CYAN}Pasta com as legendas .ass/.srt de Orgun (ENTER = {PASTA_ALVO}): {Style.RESET_ALL}"
        ).strip().strip('"').strip("'")

        if not entrada:
            entrada = PASTA_ALVO

        if not os.path.isdir(entrada):
            print(f"{Fore.RED}[ERRO] O diretório especificado não existe: {entrada}")
            continue

        return entrada


def _processar_ass(linhas):
    padrao_dialogo = re.compile(r'^(Dialogue:\s*[^,]*(?:,[^,]*){8},)(.*)$')
    modificacoes = 0
    for i, linha in enumerate(linhas):
        match = padrao_dialogo.match(linha)
        if not match:
            continue
        prefixo = match.group(1)
        texto = match.group(2).strip()
        texto_limpo, modificado = higienizar_linha(texto)
        texto_limpo = _regra_de_ouro_ass(texto_limpo)
        if texto_limpo != texto:
            modificado = True
        if modificado:
            linhas[i] = prefixo + texto_limpo + "\n"
            modificacoes += 1
            print(f"   {Fore.RED}[ORIGINAL] : {texto}")
            print(f"   {Fore.GREEN}[CORRIGIDO]: {texto_limpo}{Style.RESET_ALL}\n")
    return linhas, modificacoes


def _processar_srt(linhas):
    modificacoes = 0
    for i, linha in enumerate(linhas):
        texto = linha.rstrip('\n').rstrip('\r')
        if not texto.strip() or _PADRAO_INDICE_SRT.match(texto.strip()) or _PADRAO_TIMECODE_SRT.search(texto):
            continue
        texto_limpo, modificado = higienizar_linha(texto)
        if modificado:
            linhas[i] = texto_limpo + "\n"
            modificacoes += 1
            print(f"   {Fore.RED}[ORIGINAL] : {texto}")
            print(f"   {Fore.GREEN}[CORRIGIDO]: {texto_limpo}{Style.RESET_ALL}\n")
    return linhas, modificacoes


def varrer_tudo():
    print(Fore.MAGENTA + "="*50)
    print(Fore.MAGENTA + " MÁQUINA DE JUÍZO FINAL: DETONATOR ORGUN (V3 - MOTOR REGEX)")
    print(Fore.MAGENTA + "="*50)

    pasta_alvo = obter_pasta_alvo()

    arquivos = glob.glob(os.path.join(glob.escape(pasta_alvo), '*.ass')) + \
               glob.glob(os.path.join(glob.escape(pasta_alvo), '*.srt'))
    for sub in ["legendas_eng", "traducao", "legendas-traduzidas", "legendas_ptbr"]:
        sub_dir = os.path.join(pasta_alvo, sub)
        if os.path.isdir(sub_dir):
            arquivos.extend(glob.glob(os.path.join(glob.escape(sub_dir), '*.ass')))
            arquivos.extend(glob.glob(os.path.join(glob.escape(sub_dir), '*.srt')))
            
    vistos = set()
    arquivos_unicos = []
    for arq in arquivos:
        if arq not in vistos:
            vistos.add(arq)
            arquivos_unicos.append(arq)

    alvos = sorted(arq for arq in arquivos_unicos if not arq.endswith('_REVISADO.ass'))

    if not alvos:
        print(f"{Fore.YELLOW}[AVISO] Nenhum arquivo .ass ou .srt encontrado na pasta.")
        return

    total_correcoes = 0

    for arq in alvos:
        nome_ep = os.path.basename(arq)
        print(f"{Fore.CYAN}\n--- Lendo: {nome_ep} ---")

        with open(arq, 'r', encoding='utf-8', errors='replace') as f:
            linhas = f.readlines()

        if arq.lower().endswith('.ass'):
            linhas, modificacoes_ep = _processar_ass(linhas)
        else:
            linhas, modificacoes_ep = _processar_srt(linhas)

        total_correcoes += modificacoes_ep

        if modificacoes_ep > 0:
            with open(arq, 'w', encoding='utf-8') as f:
                f.writelines(linhas)
            print(f"{Fore.GREEN}[ARQUIVO] {nome_ep}: {modificacoes_ep} anomalias aniquiladas.")
        else:
            print(f"{Fore.CYAN}[ARQUIVO] {nome_ep}: Legenda cristalina. Sem erros.")

    print(Fore.MAGENTA + "="*50)
    print(f"{Fore.MAGENTA} TOTAL DE ANOMALIAS DESTRUÍDAS: {total_correcoes}")
    print(Fore.MAGENTA + "="*50)


if __name__ == "__main__":
    varrer_tudo()
