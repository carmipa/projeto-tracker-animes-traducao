#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import glob
import re
from colorama import init, Fore, Style

init(autoreset=True)

PASTA_ALVO = r"E:\animes\GUNDAM\GUNDAM UC\UC 0096 - UNICORN\Mobile Suit Gundam Unicorn Re0096\legendas_eng"

# Termos de lore/marca: sempre normalizados para a grafia oficial,
# em QUALQUER caixa e posição na frase.
LORE_PROPRIO = {
    "Traje Móvel": "Mobile Suit",
    "Trajes Móveis": "Mobile Suits",
    "Novo Tipo": "Newtype",
    "Novos Tipos": "Newtypes",
    "Federação da Terra": "Federação Terrestre",

    # Correções específicas achadas em auditoria real (gênero/encoding corrompidos)
    "da Tenente Riddhe": "do Tenente Riddhe",
    "A General Revil": "O General Revil",
    "Operao V": "Operação V",
    "mais rpido": "mais rápido",
    
    # Correção da facção Sleeves (evita tradução literal "Mangas")
    "as Mangas": "os Sleeves",
    "das Mangas": "dos Sleeves",
    "nas Mangas": "nos Sleeves",
    "as mangas": "os Sleeves",
    "das mangas": "dos Sleeves",
    "nas mangas": "nos Sleeves",
    
    # Correção do meteorito/facção Axis (evita tradução literal "Eixo")
    "ao Eixo": "a Axis",
    "do Eixo": "de Axis",
    "no Eixo": "em Axis",
    "o Eixo": "Axis",
    "o eixo": "Axis",
}

# Francesismos residuais (pipeline tem fonte francesa), gafes de tradução literal,
# esquizofrenia Tu/Você, concordância e redundâncias.
# A caixa da primeira letra do trecho ORIGINAL é preservada na troca.
GRAMATICA_E_GAFES = {
    # ----------------------------------------------------
    # CORREÇÃO NARRATIVA ESPECÍFICA (gênero corrompido em fala sobre personagem)
    # ----------------------------------------------------
    "Sela parece": "Ele parece",

    # ----------------------------------------------------
    # GAFES DE TRADUÇÃO DIRETA DO INGLÊS/FRANCÊS (LLMs)
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

    eh_grafico = any(tag in t for tag in ["\\pos", "\\move", "\\clip", "\\iclip", "\\org", "{\\p", "|"])

    # 1. Resolver as infames barras erráticas e quebra de ASS, e franglês residual
    if not eh_grafico:
        t = t.replace('\\N ', '\\N').replace(' \\N', '\\N')
        t = t.replace('\\n ', '\\N').replace(' \\n', '\\N').replace('\\n', '\\N')
        t = t.replace('\\ ', ' ')
    else:
        # Se for grafico/efeito, normaliza apenas a quebra de linha minuscula basica sem mexer no espacamento do \N
        t = t.replace('\\n', '\\N')

    t = t.replace('\\Net ', '\\N e ').replace('\\NEt ', '\\N E ')
    t = t.replace('\\NIl ', '\\N Ele ')
    # A regra de substituir \\Nmais por \\N mas foi deletada por ser incorreta em PT-BR
    t = t.replace('\\Nune ', '\\N uma ').replace('\\Nun ', '\\N um ')
    t = re.sub(r'\beuh\.\.\.', 'hã...', t, flags=re.IGNORECASE)

    # 2. Remoção de QUALQUER tag ASS duplicada consecutiva
    t = re.sub(r'(\\{\\[^{}]+\\})\\1+', r'\\1', t)

    # 3. Normalização de espaçamento e pontuação (somente se não for gráfico/desenho)
    if not eh_grafico:
        t = re.sub(r' {2,}', ' ', t)
        t = re.sub(r' +([,.!?;:])(?!\\.\\.)', r'\\1', t)
        # Normaliza 4 ou mais pontos seguidos para exatamente 3 pontos (reticências)
        t = re.sub(r'\\.\\{4,}', '...', t)
        # Normaliza exatamente 2 pontos isolados para exatamente 3 pontos (reticências)
        t = re.sub(r'(?<!\\.)\\.\\.(?!\\.)', '...', t)
    else:
        # Para graficos, apenas normaliza espacos duplos comuns para nao quebrar a diagramacao
        t = re.sub(r' {2,}', ' ', t)

    # 4. Alucinações de pipeline (marcações do LLM que escaparam para a legenda)
    t = re.sub(r'Tradução revisada:\s*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'Traduction:\s*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\bÉPISODE\b', 'EPISÓDIO', t, flags=re.IGNORECASE)
    t = re.sub(r'\bEPISODE\b', 'EPISÓDIO', t, flags=re.IGNORECASE)

    # 5. Dicionário de Lore (grafia oficial fixa, qualquer caixa/posição na frase)
    for padrao, correto in _LORE_COMPILADO:
        t = padrao.sub(lambda m, c=correto: c, t)

    # 6. Dicionário de Gramática/Gafes (preserva a caixa do trecho original)
    for padrao, correto in _GRAMATICA_COMPILADO:
        t = padrao.sub(lambda m, c=correto: _preservar_caixa(c, m.group(0)), t)

    # 7. CORREÇÃO AVANÇADA DE TAGS ÓRFÃS (itálico e negrito)
    t = _balancear_tag(t, "{\\i1}", "{\\i0}")
    t = _balancear_tag(t, "{\\b1}", "{\\b0}")

    return t, t != texto_original


def obter_pasta_alvo():
    """Pergunta a pasta a higienizar; ENTER aceita o caminho padrão (PASTA_ALVO)."""
    while True:
        entrada = input(
            f"{Fore.CYAN}Pasta com as legendas .ass de Unicorn (ENTER = {PASTA_ALVO}): {Style.RESET_ALL}"
        ).strip().strip('"').strip("'")

        if not entrada:
            entrada = PASTA_ALVO

        if not os.path.isdir(entrada):
            print(f"{Fore.RED}[ERRO] O diretório especificado não existe: {entrada}")
            continue

        return entrada


def varrer_tudo():
    print(Fore.MAGENTA + "="*50)
    print(Fore.MAGENTA + " MÁQUINA DE JUÍZO FINAL: GUNDAM UNICORN (V3 - MOTOR REGEX)")
    print(Fore.MAGENTA + "="*50)

    pasta_alvo = obter_pasta_alvo()

    arquivos = glob.glob(os.path.join(glob.escape(pasta_alvo), '*.ass'))
    for sub in ["legendas_eng", "traducao", "legendas-traduzidas", "legendas_ptbr"]:
        sub_dir = os.path.join(pasta_alvo, sub)
        if os.path.isdir(sub_dir):
            arquivos.extend(glob.glob(os.path.join(glob.escape(sub_dir), '*.ass')))
            
    vistos = set()
    arquivos_unicos = []
    for arq in arquivos:
        if arq not in vistos:
            vistos.add(arq)
            arquivos_unicos.append(arq)

    alvos = [arq for arq in arquivos_unicos if not arq.endswith('_REVISADO.ass')]
    alvos.sort()

    if not alvos:
        print(f"{Fore.YELLOW}[AVISO] Nenhum arquivo .ass encontrado na pasta.")
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
            print(f"{Fore.GREEN}[ARQUIVO] {nome_ep}: {modificacoes_ep} anomalias aniquiladas.")
        else:
            print(f"{Fore.CYAN}[ARQUIVO] {nome_ep}: Legenda cristalina. Sem erros.")

    print(Fore.MAGENTA + "="*50)
    print(f"{Fore.MAGENTA} TOTAL DE ANOMALIAS DESTRUÍDAS: {total_correcoes}")
    print(Fore.MAGENTA + "="*50)


if __name__ == "__main__":
    varrer_tudo()
