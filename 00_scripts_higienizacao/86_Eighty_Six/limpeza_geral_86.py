#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Higienização V3 — 86 Eighty-Six (PT-BR)
Corrige artefatos do LLM local: \\N órfão, \\n colado, tags ASS inválidas,
lore Spearhead, flexão Lena/handler e gafes gramaticais do Mistral/Gemma.
"""

import os
import sys
import glob
import re
import argparse
from colorama import init, Fore, Style

init(autoreset=True)

# Saída imediata no terminal (progresso em tempo real)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (OSError, ValueError):
        pass


def _emit(msg="", *, end="\n"):
    print(msg, end=end, flush=True)

PASTA_ALVO = r"C:\animes\86\86 Part1\legendas_eng"
SUBPASTAS_LEGENDA = ("legendas_eng", "traducao", "legendas-traduzidas", "legendas_ptbr")

# Termos de lore/marca: sempre normalizados para a grafia oficial,
# em QUALQUER caixa e posição na frase.
LORE_PROPRIO = {
    "Ponta de Lança": "Spearhead",
    "Esquadrão Vanguarda": "Esquadrão Spearhead",
    "esquadrão Vanguarda": "esquadrão Spearhead",
    "do Esquadrão Vanguarda": "do Esquadrão Spearhead",
    "Do Esquadrão Vanguarda": "Do Esquadrão Spearhead",
    "Processadores Lanceiros": "Processadores Spearhead",
    "Processador Lanceiro": "Processador Spearhead",
    "Cachorro Negro": "Black Dog",
    "cachorro negro": "Black Dog",
}
# Flexão de gênero para a Major Vladilena Milizé (Lena) e seu Handler — em 86 o
# protagonismo feminino é central e o LLM tende a usar artigos/flexões masculinas
# por padrão. Mantido caso-sensível e SEM IGNORECASE de propósito: cada variação de
# caixa já está listada explicitamente, então aplicar IGNORECASE aqui faria a primeira
# variante que casar (ex.: minúscula) sobrescrever a caixa de uma ocorrência capitalizada.
FLEXAO_GENERO_86 = {
    r'\bo major\b': r'a major',
    r'\bO major\b': r'A major',
    r'\bO Major\b': r'A Major',
    r'\bdo major\b': r'da major',
    r'\bDo major\b': r'Da major',
    r'\bDo Major\b': r'Da Major',
    r'\bao major\b': r'à major',
    r'\bAo major\b': r'À major',
    r'\bAo Major\b': r'À Major',
    r'\bum major\b': r'uma major',
    r'\bUm major\b': r'Uma major',
    r'\bUm Major\b': r'Uma Major',

    r'\bo handler\b': r'a handler',
    r'\bO handler\b': r'A handler',
    r'\bO Handler\b': r'A Handler',
    r'\bdo handler\b': r'da handler',
    r'\bDo handler\b': r'Da handler',
    r'\bDo Handler\b': r'Da Handler',
    r'\bao handler\b': r'à handler',
    r'\bAo handler\b': r'À handler',
    r'\bAo Handler\b': r'À Handler',
    r'\bum handler\b': r'uma handler',
    r'\bUm handler\b': r'Uma handler',
    r'\bUm Handler\b': r'Uma Handler',

    r'\bo Capitão Milizé\b': r'a Capitã Milizé',
    r'\bO Capitão Milizé\b': r'A Capitã Milizé',

    r'major ainda está vivo\?': r'major ainda está viva?',
    r'major está bem\?': r'major está bem?',
    
    r'\bvocê é o esquisito\b': r'você é a esquisita',
    r'\bVocê é o esquisito\b': r'Você é a esquisita',
    r'\bvocê é tão esquisito\b': r'você é tão esquisita',
    r'\bVocê é tão esquisito\b': r'Você é tão esquisita',
}
# Gafes de tradução literal do inglês, esquizofrenia Tu/Você, concordância e redundâncias.
# A caixa da primeira letra do trecho ORIGINAL é preservada na troca.
GRAMATICA_E_GAFES = {
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
    
    # ----------------------------------------------------
    # REMOÇÃO DE PARÊNTESES DE GÊNERO / TRADUÇÕES DO MISTRAL
    # ----------------------------------------------------
    "Obrigado(a)": "Obrigada",
    "obrigado(a)": "obrigada",
    "Obrigada(a)": "Obrigada",
    "estranho(a)": "estranha",
    "Estranho(a)": "Estranha",
    "realmente estranho(a)": "realmente estranha",
    "Realmente estranho(a)": "Realmente estranha",
    "com um espingarda": "com uma espingarda",
    "com o espingarda": "com uma espingarda",
    "um espingarda": "uma espingarda",
    "dezessete distrito": "décimo sétimo distrito",
    "dezessete ward": "décimo sétimo setor",
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


def _normalizar_barras_tag_ass(t):
    """Corrige barras duplicadas inválidas dentro de blocos ASS (ex.: \\\\fscx -> \\fscx)."""

    def _fix_bloco(match):
        bloco = match.group(0)
        bloco = re.sub(r'\\\\([a-zA-Z])', r'\\\1', bloco)
        return bloco

    return re.sub(r'\{[^{}]*\}', _fix_bloco, t)


def _inserir_espaco_apos_quebra_ass(t):
    """Separa \\N colado na palavra seguinte (\\Ndrones -> \\N drones). Não troca mais por mas."""
    return re.sub(
        r'\\N([a-zA-ZáéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ])',
        r'\\N \1',
        t,
    )


_LORE_COMPILADO = _compilar_dicionario(LORE_PROPRIO)
_GRAMATICA_COMPILADO = _compilar_dicionario(GRAMATICA_E_GAFES)


def higienizar_linha(texto):
    texto_original = texto
    t = texto

    eh_grafico = any(tag in t for tag in ["\\pos", "\\move", "\\clip", "\\iclip", "\\org", "{\\p", "|"])

    # 0. Tags ASS com barras duplicadas (signs/typesetting) — antes de outras regras
    t = _normalizar_barras_tag_ass(t)

    # 1. Resolver barras erráticas e quebra de ASS
    if not eh_grafico:
        t = t.replace('\\N ', '\\N').replace(' \\N', '\\N')
        t = t.replace('\\n ', '\\N').replace(' \\n', '\\N').replace('\\n', '\\N')
        t = t.replace('\\ ', ' ')
        t = _inserir_espaco_apos_quebra_ass(t)
    else:
        t = t.replace('\\n', '\\N')

    t = t.replace('\\Net ', '\\N e ').replace('\\NEt ', '\\N E ')
    t = t.replace('\\NIl ', '\\N Ele ')
    # Não substituir \\Nmais por \\N mas — corrompe PT-BR correto (ver vault 2026-06-20)
    t = t.replace('\\Nune ', '\\N uma ').replace('\\Nun ', '\\N um ')
    t = re.sub(r'\\beuh\.\.\.', 'hã...', t, flags=re.IGNORECASE)

    # Remove \\N órfão no final (ex.: "...frente leste.\\N")
    t = re.sub(r'\\N\s*$', '', t)
    t = re.sub(r'\\N\s*([.!?;:])\s*$', r'\1', t)

    # 2. Tags ASS duplicadas consecutivas (ex.: {\\an8}{\\an8})
    t = re.sub(r'(\{[^{}]+\})\1+', r'\1', t)

    # 3. Espaçamento e pontuação (preserva reticências em diálogo)
    if not eh_grafico:
        t = re.sub(r' {2,}', ' ', t)
        t = re.sub(r' +([,.!?;:])(?!\.\.)', r'\1', t)
        t = re.sub(r'\.{4,}', '...', t)
        t = re.sub(r'(?<!\.)\.\.(?!\.)', '...', t)
    else:
        t = re.sub(r' {2,}', ' ', t)

    # 4. Alucinações de pipeline
    t = re.sub(r'Tradução revisada:\s*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'Traduction:\s*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\bÉPISODE\b', 'EPISÓDIO', t, flags=re.IGNORECASE)
    t = re.sub(r'\bEPISODE\b', 'EPISÓDIO', t, flags=re.IGNORECASE)

    # 5. Lore
    for padrao, correto in _LORE_COMPILADO:
        t = padrao.sub(lambda m, c=correto: c, t)

    # 6. Flexão Lena/Handler (case-sensível)
    for old, new in FLEXAO_GENERO_86.items():
        t = re.sub(old, new, t)

    # 7. Gramática/gafes
    for padrao, correto in _GRAMATICA_COMPILADO:
        t = padrao.sub(lambda m, c=correto: _preservar_caixa(c, m.group(0)), t)

    # 8. Itálico/negrito órfãos
    t = _balancear_tag(t, "{\\i1}", "{\\i0}")
    t = _balancear_tag(t, "{\\b1}", "{\\b0}")

    return t, t != texto_original

def obter_pasta_alvo(pasta_cli=None):
    """Pasta via --pasta, argumento posicional ou prompt interativo."""
    if pasta_cli:
        pasta_cli = pasta_cli.strip().strip('"').strip("'")
        if os.path.isdir(pasta_cli):
            return pasta_cli
        print(f"{Fore.RED}[ERRO] O diretório especificado não existe: {pasta_cli}")
        sys.exit(1)

    while True:
        entrada = input(
            f"{Fore.CYAN}Pasta com as legendas .ass de 86 (ENTER = {PASTA_ALVO}): {Style.RESET_ALL}"
        ).strip().strip('"').strip("'")

        if not entrada:
            entrada = PASTA_ALVO

        if not os.path.isdir(entrada):
            print(f"{Fore.RED}[ERRO] O diretório especificado não existe: {entrada}")
            continue

        return entrada


def listar_arquivos_ass(pasta_alvo):
    """Lista .ass na raiz, subpastas conhecidas e um nível extra de profundidade."""
    arquivos = glob.glob(os.path.join(glob.escape(pasta_alvo), "*.ass"))
    for sub in SUBPASTAS_LEGENDA:
        sub_dir = os.path.join(pasta_alvo, sub)
        if os.path.isdir(sub_dir):
            arquivos.extend(glob.glob(os.path.join(glob.escape(sub_dir), "*.ass")))
            arquivos.extend(glob.glob(os.path.join(glob.escape(sub_dir), "*", "*.ass")))

    vistos = set()
    unicos = []
    for arq in arquivos:
        norm = os.path.normcase(os.path.abspath(arq))
        if norm not in vistos:
            vistos.add(norm)
            unicos.append(arq)
    return sorted(a for a in unicos if not a.endswith("_REVISADO.ass"))


def parse_args():
    parser = argparse.ArgumentParser(
        description="Higieniza legendas .ass de 86 Eighty-Six (artefatos do LLM local)."
    )
    parser.add_argument(
        "pasta",
        nargs="?",
        help=f"Pasta com legendas .ass (default interativo: {PASTA_ALVO})",
    )
    parser.add_argument(
        "--pasta",
        dest="pasta_flag",
        help="Alternativa à pasta posicional",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra correções sem gravar nos arquivos",
    )
    parser.add_argument(
        "--progresso-a-cada",
        type=int,
        default=25,
        metavar="N",
        help="Atualiza barra de progresso a cada N diálogos sem correção (0 = desliga)",
    )
    return parser.parse_args()


def varrer_tudo(pasta_alvo=None, dry_run=False, intervalo_progresso=25):
    _emit(Fore.MAGENTA + "=" * 50)
    _emit(Fore.MAGENTA + " MÁQUINA DE JUÍZO FINAL: 86 EIGHTY-SIX (V3 - MOTOR REGEX)")
    _emit(Fore.MAGENTA + "=" * 50)

    if pasta_alvo is None:
        pasta_alvo = obter_pasta_alvo()

    alvos = listar_arquivos_ass(pasta_alvo)
    if not alvos:
        _emit(f"{Fore.YELLOW}[AVISO] Nenhum arquivo .ass encontrado na pasta.")
        return

    padrao_dialogo = re.compile(r'^(Dialogue:\s*[^,]*(?:,[^,]*){8},)(.*)$')
    total_arquivos = len(alvos)
    total_correcoes = 0

    _emit(f"{Fore.CYAN}[INFO] {total_arquivos} arquivo(s) .ass na fila.{Style.RESET_ALL}\n")

    for indice_arq, arq in enumerate(alvos, start=1):
        nome_ep = os.path.basename(arq)
        _emit(
            f"{Fore.CYAN}[{indice_arq}/{total_arquivos}] Abrindo: {nome_ep}{Style.RESET_ALL}"
        )

        with open(arq, 'r', encoding='utf-8-sig') as f:
            linhas = f.readlines()

        total_dialogos = sum(1 for linha in linhas if padrao_dialogo.match(linha))
        modificacoes_ep = 0
        dialogos_vistos = 0
        em_linha_progresso = False

        for num_linha, linha in enumerate(linhas, start=1):
            match = padrao_dialogo.match(linha)
            if not match:
                continue

            dialogos_vistos += 1
            prefixo = match.group(1)
            texto = match.group(2).strip()

            texto_limpo, modificado = higienizar_linha(texto)

            if modificado:
                if em_linha_progresso:
                    _emit()
                    em_linha_progresso = False

                linhas[num_linha - 1] = prefixo + texto_limpo + "\n"
                modificacoes_ep += 1
                total_correcoes += 1
                _emit(
                    f"   {Fore.YELLOW}#{total_correcoes}{Style.RESET_ALL} "
                    f"{Fore.CYAN}L{num_linha}{Style.RESET_ALL} "
                    f"({dialogos_vistos}/{total_dialogos})"
                )
                _emit(f"   {Fore.RED}[ORIGINAL] : {texto}")
                _emit(f"   {Fore.GREEN}[CORRIGIDO]: {texto_limpo}{Style.RESET_ALL}\n")
            elif (
                intervalo_progresso > 0
                and (
                    dialogos_vistos % intervalo_progresso == 0
                    or dialogos_vistos == total_dialogos
                )
            ):
                pct = (dialogos_vistos * 100) // total_dialogos if total_dialogos else 100
                _emit(
                    f"   {Fore.BLUE}[{nome_ep}] {dialogos_vistos}/{total_dialogos} "
                    f"diálogos ({pct}%) — {modificacoes_ep} correção(ões) até agora{Style.RESET_ALL}",
                    end="\r",
                )
                em_linha_progresso = True

        if em_linha_progresso:
            _emit()

        if modificacoes_ep > 0:
            if dry_run:
                _emit(
                    f"{Fore.YELLOW}[DRY-RUN] {nome_ep}: {modificacoes_ep} correção(ões) "
                    f"detectadas (não gravado).{Style.RESET_ALL}"
                )
            else:
                with open(arq, 'w', encoding='utf-8') as f:
                    f.writelines(linhas)
                _emit(
                    f"{Fore.GREEN}[GRAVADO] {nome_ep}: {modificacoes_ep} anomalia(s) "
                    f"corrigida(s).{Style.RESET_ALL}"
                )
        else:
            _emit(f"{Fore.CYAN}[OK] {nome_ep}: nenhuma correção necessária.{Style.RESET_ALL}")

        _emit()

    _emit(Fore.MAGENTA + "=" * 50)
    modo = " (dry-run)" if dry_run else ""
    _emit(
        f"{Fore.MAGENTA} TOTAL: {total_correcoes} anomalia(s) em "
        f"{total_arquivos} arquivo(s){modo}{Style.RESET_ALL}"
    )
    _emit(Fore.MAGENTA + "=" * 50)


if __name__ == "__main__":
    args = parse_args()
    pasta = args.pasta_flag or args.pasta
    kwargs = dict(dry_run=args.dry_run, intervalo_progresso=max(0, args.progresso_a_cada))
    if pasta:
        varrer_tudo(pasta_alvo=obter_pasta_alvo(pasta), **kwargs)
    else:
        varrer_tudo(**kwargs)