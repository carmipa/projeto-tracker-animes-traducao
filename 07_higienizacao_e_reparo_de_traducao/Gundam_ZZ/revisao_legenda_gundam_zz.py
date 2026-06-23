#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Revisão extrema — Mobile Suit Gundam ZZ (PT-BR)
Restaura karaokê romaji/japonês do ENG, corrige lore, tags ASS e gafes de LLM/Mistral.
Opcional: remux mkvmerge com legendas corrigidas.

Uso:
  python revisao_legenda_gundam_zz.py
  python revisao_legenda_gundam_zz.py --entrada PASTA_PTBR --eng PASTA_ENG --saida SAIDA
  python revisao_legenda_gundam_zz.py --arquivo ep01_PTBR.ass --eng PASTA_ENG --saida SAIDA
"""

import os
import re
import sys
import json
import time
import shutil
import argparse
import subprocess
from datetime import datetime

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class _EmptyColor:
        def __getattr__(self, _name):
            return ""
    Fore = Style = _EmptyColor()

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    except (OSError, ValueError):
        pass

PASTA_ANIME_PADRAO = r"C:\animes\Gundam_ZZ"
SUBPASTAS_LEGENDA = ("legendas_ptbr", "legendas_eng", "legendas_ptbr_corrigidas")

# Limite por arquivo .ass (evita leitura acidental de arquivos enormes)
MAX_ASS_BYTES = 8 * 1024 * 1024
# Timeout por remux mkvmerge (segundos)
MKVMERGE_TIMEOUT = 3600
EXTENSOES_LEGENDA = (".ass",)
EXTENSOES_VIDEO = (".mkv",)

PATRON_DIALOGUE = re.compile(r"^(Dialogue:\s*[^,]*(?:,[^,]*){8},)(.*)$")

ESTILOS_KARAOKE_ROMAJI = {
    s.lower() for s in (
        "New Frontier",
        "Jiyuu na Uta",
        "ED4 JAP",
        "OP2 JAP",
        "Romaji Karaoke",
        "Kanji Karaoke",
        "Romaji Karaoke op",
        "Kanji Karaoke op",
        "OP JAP",
        "ED JAP",
        "Anime Ja Nai",
        "Silent Voice",
        "Issenman-Nen Ginga",
        "Jidai ga Naiteiru",
    )
}

SUBSTITUICOES_LORE = [
    # Facções e Organizações
    (re.compile(r"\bNova Zeon\b", re.I), "Neo Zeon"),
    (re.compile(r"\bNovo Zeon\b", re.I), "Neo Zeon"),
    (re.compile(r"\bZeon Novo\b", re.I), "Neo Zeon"),
    (re.compile(r"\bZeon Nova\b", re.I), "Neo Zeon"),
    (re.compile(r"\bA\.E\.U\.G\b", re.I), "A.E.U.G."),
    (re.compile(r"\bEletrônica Anaheim\b", re.I), "Anaheim Electronics"),
    (re.compile(r"\bEletrônicos Anaheim\b", re.I), "Anaheim Electronics"),
    
    # Locais
    (re.compile(r"\bShangri-la\b", re.I), "Shangri-La"),
    (re.compile(r"\bO Eixo\b", re.I), "Axis"),
    (re.compile(r"\bau Eixo\b", re.I), "a Axis"),
    (re.compile(r"\bdo Eixo\b", re.I), "de Axis"),
    (re.compile(r"\bno Eixo\b", re.I), "em Axis"),
    (re.compile(r"\beixo\b", re.IGNORECASE), "Axis"),  # Pegará "o eixo", "ao eixo", "Eixo", etc. Em Gundam ZZ "eixo" quase 100% refere-se a Axis.
    (re.compile(r"\bLua-Lua\b", re.I), "Moon-Moon"),
    (re.compile(r"\bMundo da Lua\b", re.I), "Moon-Moon"),

    # Personagens A.E.U.G. / Aliados / Neutros
    (re.compile(r"\bJudau\s+Ashta\b", re.I), "Judau Ashta"),
    (re.compile(r"\bJudau\s+Asta\b", re.I), "Judau Ashta"),
    (re.compile(r"\bRoux\s+Louka\b", re.I), "Roux Louka"),
    (re.compile(r"\bRu\s+Luka\b", re.I), "Roux Louka"),
    (re.compile(r"\bBeecha\s+Oleg\b", re.I), "Beecha Oleg"),
    (re.compile(r"\bBicha\s+Oleg\b", re.I), "Beecha Oleg"), # Evitar gafe de grafia
    (re.compile(r"\bIino\s+Abbav\b", re.I), "Iino Abbav"),
    (re.compile(r"\bIno\s+Abav\b", re.I), "Iino Abbav"),
    (re.compile(r"\bMondo\s+Agake\b", re.I), "Mondo Agake"),
    (re.compile(r"\bElle\s+Vianno\b", re.I), "Elle Vianno"),
    (re.compile(r"\bLeina\s+Ashta\b", re.I), "Leina Ashta"),
    (re.compile(r"\bBrilhante\s+Noa\b", re.I), "Bright Noa"), # "Brilhante Noa" é clássico
    (re.compile(r"\bAstonaige\s+Medoz\b", re.I), "Astonaige Medoz"),
    (re.compile(r"\bHayato\s+Kobayashi\b", re.I), "Hayato Kobayashi"),
    (re.compile(r"\bKamille\s+Bidan\b", re.I), "Kamille Bidan"),
    (re.compile(r"\bCamille\s+Bidan\b", re.I), "Kamille Bidan"),
    (re.compile(r"\bFa\s+Yuiry\b", re.I), "Fa Yuiry"),
    (re.compile(r"\bEmary\s+Ounce\b", re.I), "Emary Ounce"),

    # Personagens Neo Zeon / Inimigos
    (re.compile(r"\bHaman\s+Karn\b", re.I), "Haman Karn"),
    (re.compile(r"\bHaman\s+Kan\b", re.I), "Haman Karn"),
    (re.compile(r"\bSenhorita\s+Haman\b", re.I), "Lady Haman"),
    (re.compile(r"\bMashymre\s+Cello\b", re.I), "Mashymre Cello"),
    (re.compile(r"\bMashimar\b", re.I), "Mashymre"),
    (re.compile(r"\bChara\s+Soon\b", re.I), "Chara Soon"),
    (re.compile(r"\bChara\s+Sun\b", re.I), "Chara Soon"),
    (re.compile(r"\bGlemy\s+Toto\b", re.I), "Glemy Toto"),
    (re.compile(r"\bGlemi\s+Toto\b", re.I), "Glemy Toto"),
    (re.compile(r"\bElpeo\s+Ple\b", re.I), "Elpeo Ple"),
    (re.compile(r"\bElpeo\s+Puru\b", re.I), "Elpeo Ple"),
    (re.compile(r"\bPle\s+Two\b", re.I), "Ple Two"),
    (re.compile(r"\bPuru\s+Two\b", re.I), "Ple Two"),
    (re.compile(r"\bPuru\s+Dois\b", re.I), "Ple Two"),
    (re.compile(r"\bGottn\s+Goh\b", re.I), "Gottn Goh"),
    (re.compile(r"\bGemon\s+Bajack\b", re.I), "Gemon Bajack"),
    (re.compile(r"\bRakan\s+Dahkaran\b", re.I), "Rakan Dahkaran"),
    (re.compile(r"\bAugust\s+Gidan\b", re.I), "August Gidan"),
    (re.compile(r"\bIllia\s+Pazom\b", re.I), "Illia Pazom"),

    # Naves e Peças
    (re.compile(r"\bArgama\b", re.I), "Argama"),
    (re.compile(r"\bNahel\s+Argama\b", re.I), "Nahel Argama"),
    (re.compile(r"\bNael\s+Argama\b", re.I), "Nahel Argama"),
    (re.compile(r"\bEndra\b", re.I), "Endra"),
    (re.compile(r"\bSadalahn\b", re.I), "Sadalahn"),
    (re.compile(r"\bGwanban\b", re.I), "Gwanban"),
    (re.compile(r"\bTopo do Núcleo\b", re.I), "Core Top"),
    (re.compile(r"\bBase do Núcleo\b", re.I), "Core Base"),
    (re.compile(r"\bLutador do Núcleo\b", re.I), "Core Fighter"),
    (re.compile(r"\bCaça do Núcleo\b", re.I), "Core Fighter"),
    (re.compile(r"\bCavaleiro Mega\b", re.I), "Mega Rider"),

    # Mobile Suits A.E.U.G.
    (re.compile(r"\bDouble\s+Zeta\b", re.I), "Double Zeta"),
    (re.compile(r"\bZeta\s+Duplo\b", re.I), "Double Zeta"),
    (re.compile(r"\bZeta\s+Gundam\b", re.I), "Zeta Gundam"),
    (re.compile(r"\bHyaku[ -]Shiki\b", re.I), "Hyaku Shiki"),
    (re.compile(r"\bCem\s+Estilos\b", re.I), "Hyaku Shiki"), # Erro raro, mas possível
    (re.compile(r"\bMk-II\b", re.I), "Mk-II"),
    (re.compile(r"\bMarca\s+Dois\b", re.I), "Mk-II"),

    # Mobile Suits Neo Zeon
    (re.compile(r"\bQubeley\b", re.I), "Qubeley"),
    (re.compile(r"\bQuebeley\b", re.I), "Qubeley"),
    (re.compile(r"\bZaku\b", re.I), "Zaku"),
    (re.compile(r"\bBawoo\b", re.I), "Bawoo"),
    (re.compile(r"\bDreissen\b", re.I), "Dreissen"),
    (re.compile(r"\bDöven\s+Wolf\b", re.I), "Doven Wolf"),
    (re.compile(r"\bDoven\s+Wolf\b", re.I), "Doven Wolf"),
    (re.compile(r"\bLobo\s+Doven\b", re.I), "Doven Wolf"),
    (re.compile(r"\bQuin\s+Mantha\b", re.I), "Queen Mansa"), # Ajustado para Queen Mansa que é mais legível, ou Quin Mantha dependendo do purismo. Vamos de Quin Mantha que é o oficial do kit
    (re.compile(r"\bRainha\s+Mansa\b", re.I), "Quin Mantha"),
    (re.compile(r"\bQueen\s+Mansa\b", re.I), "Quin Mantha"),
    (re.compile(r"\bGeymalk\b", re.I), "Geymalk"),
    (re.compile(r"\bZssa\b", re.I), "Zssa"),
    (re.compile(r"\bGalluss-J\b", re.I), "Galluss-J"),
    (re.compile(r"\bHamma-Hamma\b", re.I), "Hamma-Hamma"),
    (re.compile(r"\bR-Jarja\b", re.I), "R-Jarja"),
    (re.compile(r"\bGaza-C\b", re.I), "Gaza-C"),
    (re.compile(r"\bGaza-D\b", re.I), "Gaza-D"),
    (re.compile(r"\bJamru\s+Fin\b", re.I), "Jamru Fin"),
]

GRAMATICA_E_GAFES = {
    "Eu vejo.": "Entendo.",
    "Eu vejo que": "Percebo que",
    "eu vejo que": "percebo que",
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
    "vou estar fazendo": "vou fazer",
    "vou estar indo": "vou",
    ", mais eu ": ", mas eu ",
    ", mais você ": ", mas você ",
    ", mais ele ": ", mas ele ",
    ", mais ela ": ", mas ela ",
    "Tu tem": "Você tem",
    "Tu tens": "Você tem",
    "Você tens": "Você tem",
    "Tu está": "Você está",
    "Tu vais": "Você vai",
    "Você vais": "Você vai",
    "Roger that": "Entendido",
    "Roger.": "Copiado.",
    "Copy that": "Entendido",
}

# Correções cirúrgicas: chave = número da linha no arquivo .ass (1-indexed)
CORRECOES_ESPECIFICAS = {}


def _emit(msg="", *, end="\n"):
    print(msg, end=end, flush=True)


def normalizar_caminho(caminho):
    if not caminho:
        return ""
    caminho = caminho.strip().strip('"').strip("'")
    if "\0" in caminho:
        raise ValueError("Caminho inválido: contém caractere nulo.")
    return caminho


def validar_arquivo_legenda(caminho, extensao=".ass"):
    caminho = os.path.abspath(os.path.normpath(normalizar_caminho(caminho)))
    if not os.path.isfile(caminho):
        raise ValueError(f"Arquivo não encontrado: {caminho}")
    if not caminho.lower().endswith(extensao.lower()):
        raise ValueError(f"Extensão inválida (use {extensao}): {caminho}")
    return caminho


def caminho_saida_relativo(pasta_entrada, caminho_arq, pasta_saida):
    """Espelha subpastas da entrada na saída."""
    pasta_entrada = os.path.abspath(pasta_entrada)
    caminho_arq = os.path.abspath(caminho_arq)
    pasta_saida = os.path.abspath(pasta_saida)
    rel = os.path.relpath(os.path.dirname(caminho_arq), pasta_entrada)
    destino_dir = pasta_saida if rel == "." else os.path.join(pasta_saida, rel)
    return os.path.join(destino_dir, os.path.basename(caminho_arq))


def gravar_arquivo_atomico(caminho, linhas):
    caminho_tmp = caminho + ".tmp"
    with open(caminho_tmp, "w", encoding="utf-8-sig") as f:
        f.writelines(linhas)
    os.replace(caminho_tmp, caminho)


def formatar_eta(segundos_restantes):
    if segundos_restantes < 0 or segundos_restantes > 86400:
        return "?"
    m, s = divmod(int(segundos_restantes), 60)
    return f"{m}m{s:02d}s" if m else f"{s}s"


def validar_pasta(caminho, rotulo="Pasta"):
    """Resolve e valida diretório informado pelo operador."""
    caminho = normalizar_caminho(caminho)
    if not caminho:
        raise ValueError(f"{rotulo}: caminho vazio.")
    caminho_abs = os.path.abspath(os.path.normpath(caminho))
    if not os.path.isdir(caminho_abs):
        raise ValueError(f"{rotulo} não encontrada: {caminho_abs}")
    return caminho_abs


def caminho_dentro_de(base, alvo):
    """Garante que alvo resolvido permanece dentro de base (anti path traversal)."""
    base_abs = os.path.normcase(os.path.abspath(os.path.normpath(base)))
    alvo_abs = os.path.normcase(os.path.abspath(os.path.normpath(alvo)))
    try:
        comum = os.path.commonpath([base_abs, alvo_abs])
    except ValueError:
        return False
    return comum == base_abs


def nome_arquivo_seguro(nome):
    """Rejeita nomes com separadores de path ou reservados."""
    base = os.path.basename(nome)
    if not base or base in (".", ".."):
        return None
    if base != nome.strip():
        return None
    return base


def validar_executavel_mkvmerge(caminho):
    if not caminho or not os.path.isfile(caminho):
        return False
    return os.path.basename(caminho).lower() in ("mkvmerge.exe", "mkvmerge")


def _compilar_dicionario(dicionario):
    compilado = []
    for frase, correto in dicionario.items():
        nucleo = re.escape(frase)
        prefixo = r"\b" if frase[0].isalnum() else ""
        sufixo = r"\b" if frase[-1].isalnum() else ""
        compilado.append((re.compile(prefixo + nucleo + sufixo, re.IGNORECASE), correto))
    return compilado


def _preservar_caixa(correto, encontrado):
    if encontrado[:1].isupper():
        return correto[:1].upper() + correto[1:]
    return correto[:1].lower() + correto[1:]


def _balancear_tag(texto, abre, fecha):
    if texto.count(abre) > texto.count(fecha):
        texto += fecha * (texto.count(abre) - texto.count(fecha))
    return texto


_GRAMATICA_COMPILADO = _compilar_dicionario(GRAMATICA_E_GAFES)


def achar_mkvtoolnix():
    for folder in (r"C:\Program Files\MKVToolNix", r"C:\Program Files (x86)\MKVToolNix"):
        merge_path = os.path.join(folder, "mkvmerge.exe")
        if os.path.exists(merge_path):
            return merge_path
    return shutil.which("mkvmerge")


MKVMERGE_PATH = achar_mkvtoolnix()


def obter_chave_episodio(nome_arquivo):
    nome_lower = nome_arquivo.lower()
    m = re.search(r"-\s*(\d+)", nome_lower)
    if m:
        return f"ep_{int(m.group(1))}"
    return "desconhecido"


def ler_arquivo_legenda(caminho):
    caminho = os.path.abspath(caminho)
    if not os.path.isfile(caminho):
        raise OSError(f"Arquivo não encontrado: {caminho}")
    tamanho = os.path.getsize(caminho)
    if tamanho > MAX_ASS_BYTES:
        raise OSError(
            f"Arquivo .ass acima do limite ({tamanho} > {MAX_ASS_BYTES} bytes): {caminho}"
        )
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            with open(caminho, "r", encoding=encoding) as f:
                return f.readlines(), encoding
        except UnicodeDecodeError:
            continue
    with open(caminho, "r", encoding="utf-8", errors="replace") as f:
        return f.readlines(), "utf-8-replace"


def parse_dialogue(linha):
    m = PATRON_DIALOGUE.match(linha.strip())
    if not m:
        return None
    prefixo = m.group(1)
    texto = m.group(2).strip()
    partes = prefixo.rstrip(",").split(",", 9)
    estilo = partes[3].strip() if len(partes) > 3 else ""
    return prefixo, texto, estilo


def indexar_dialogos_eng(linhas):
    """Lista de textos ENG na ordem dos eventos Dialogue (para karaoke)."""
    dialogos = []
    for linha in linhas:
        parsed = parse_dialogue(linha)
        if parsed:
            dialogos.append(parsed[1])
    return dialogos


def achar_legenda_eng(caminho_ptbr, pasta_eng, pasta_ptbr_base=None):
    if not pasta_eng:
        return None
    nome_ptbr = nome_arquivo_seguro(os.path.basename(caminho_ptbr))
    if not nome_ptbr:
        return None
    pasta_eng = os.path.abspath(pasta_eng)
    candidatos = [
        nome_ptbr.replace("_PTBR.ass", "_ENG.ass"),
        nome_ptbr.replace("_PTBR.ass", ".ass"),
        nome_ptbr.replace("_ptbr.ass", "_ENG.ass"),
    ]

    if pasta_ptbr_base:
        try:
            rel_dir = os.path.relpath(os.path.dirname(os.path.abspath(caminho_ptbr)), os.path.abspath(pasta_ptbr_base))
        except ValueError:
            rel_dir = "."
        if rel_dir != ".":
            for nome in candidatos:
                nome = nome_arquivo_seguro(nome)
                if not nome:
                    continue
                caminho = os.path.join(pasta_eng, rel_dir, nome)
                if os.path.isfile(caminho) and caminho_dentro_de(pasta_eng, caminho):
                    return caminho

    for nome in candidatos:
        nome = nome_arquivo_seguro(nome)
        if not nome:
            continue
        caminho = os.path.join(pasta_eng, nome)
        if os.path.isfile(caminho) and caminho_dentro_de(pasta_eng, caminho):
            return caminho

    prefixo = nome_ptbr.split("_PTBR")[0].split("_ptbr")[0]
    for dirpath, _dirnames, filenames in os.walk(pasta_eng):
        if not caminho_dentro_de(pasta_eng, dirpath):
            continue
        for nome in filenames:
            seguro = nome_arquivo_seguro(nome)
            if not seguro:
                continue
            if seguro.lower().endswith(".ass") and seguro.startswith(prefixo):
                caminho = os.path.join(dirpath, seguro)
                if os.path.isfile(caminho) and caminho_dentro_de(pasta_eng, caminho):
                    return caminho
    return None


def listar_arquivos_ass(pasta):
    """Lista .ass recursivamente, preservando estrutura de subpastas."""
    pasta = os.path.abspath(pasta)
    arquivos = []
    vistos = set()
    for dirpath, _dirnames, filenames in os.walk(pasta):
        if not caminho_dentro_de(pasta, dirpath):
            continue
        for nome in filenames:
            seguro = nome_arquivo_seguro(nome)
            if not seguro or not seguro.lower().endswith(".ass"):
                continue
            caminho = os.path.join(dirpath, seguro)
            if not caminho_dentro_de(pasta, caminho):
                continue
            chave = os.path.normcase(caminho)
            if chave not in vistos:
                vistos.add(chave)
                arquivos.append(caminho)
    return sorted(arquivos)


def _normalizar_barras_tag_ass(texto):
    def _fix_bloco(match):
        bloco = match.group(0)
        return re.sub(r"\\\\([a-zA-Z])", r"\\\1", bloco)

    return re.sub(r"\{[^{}]*\}", _fix_bloco, texto)


def _estilo_karaoke(estilo):
    return estilo.strip().lower() in ESTILOS_KARAOKE_ROMAJI


def higienizar_texto(texto, eh_grafico=False):
    t = texto

    t = _normalizar_barras_tag_ass(t)
    t = re.sub(r"\bnh[aã]o\b", "não", t, flags=re.I)
    t = re.sub(r"\bnh[aã]oes\b", "nões", t, flags=re.I)

    if not eh_grafico:
        t = t.replace("\\N ", "\\N").replace(" \\N", "\\N")
        t = t.replace("\\n ", "\\N").replace(" \\n", "\\N").replace("\\n", "\\N")
        t = t.replace("\\ ", " ")
    else:
        t = t.replace("\\n", "\\N")

    t = t.replace("\\Net ", "\\N e ").replace("\\NEt ", "\\N E ")
    t = t.replace("\\NIl ", "\\N Ele ")
    t = t.replace("\\Nune ", "\\N uma ").replace("\\Nun ", "\\N um ")
    t = re.sub(r"\beuh\.\.\.", "hã...", t, flags=re.IGNORECASE)

    t = re.sub(r"\\N\s*$", "", t)
    t = re.sub(r"\\N\s*([.!?;:])\s*$", r"\1", t)
    t = re.sub(r"\\N([a-zA-ZáéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ])", r"\\N \1", t)

    t = re.sub(r"(\{[^{}]+\})\1+", r"\1", t)
    t = re.sub(r"\[T\d+\]", "", t)

    if not eh_grafico:
        t = re.sub(r" {2,}", " ", t)
        t = re.sub(r" +([,.!?;:])(?!\.\.)", r"\1", t)
        t = re.sub(r"\.{4,}", "...", t)
        t = re.sub(r"(?<!\.)\.\.(?!\.)", "...", t)
    else:
        t = re.sub(r" {2,}", " ", t)

    t = re.sub(r"Tradução revisada:\s*", "", t, flags=re.I)
    t = re.sub(r"Traduction:\s*", "", t, flags=re.I)
    t = re.sub(r"\bÉPISODE\b", "EPISÓDIO", t, flags=re.I)
    t = re.sub(r"\bEPISODE\b", "EPISÓDIO", t, flags=re.I)

    for padrao, subst in SUBSTITUICOES_LORE:
        t = padrao.sub(subst, t)

    for padrao, correto in _GRAMATICA_COMPILADO:
        t = padrao.sub(lambda m, c=correto: _preservar_caixa(c, m.group(0)), t)

    t = _balancear_tag(t, "{\\i1}", "{\\i0}")
    t = _balancear_tag(t, "{\\b1}", "{\\b0}")

    return t


def processar_legendas(
    pasta_ptbr_in,
    pasta_eng_in,
    pasta_ptbr_out,
    dry_run=False,
    permitir_in_place=False,
    pular_existentes=False,
    arquivos_ptbr=None,
):
    pasta_ptbr_in = validar_pasta(pasta_ptbr_in, "Pasta PT-BR")
    if pasta_eng_in:
        pasta_eng_in = validar_pasta(pasta_eng_in, "Pasta ENG")
    os.makedirs(pasta_ptbr_out, exist_ok=True)
    pasta_ptbr_out = os.path.abspath(os.path.normpath(pasta_ptbr_out))

    if os.path.normcase(pasta_ptbr_in) == os.path.normcase(pasta_ptbr_out):
        if not permitir_in_place:
            _emit(
                f"{Fore.RED}[ERRO] Saída igual à entrada ({pasta_ptbr_in}). "
                f"Use pasta diferente ou --in-place com confirmação explícita."
            )
            return False, None
        _emit(f"{Fore.YELLOW}[AVISO] Modo in-place: sobrescrevendo legendas PT-BR na origem.")

    _emit(f"\n{Fore.CYAN}=== REVISÃO EXTREMA GUNDAM ZZ ===")
    _emit(f"Originais (ENG) : {pasta_eng_in}")
    _emit(f"Traduzidas (PT) : {pasta_ptbr_in}")
    _emit(f"Destino (PT-COR): {pasta_ptbr_out}")
    if dry_run:
        _emit(f"{Fore.YELLOW}[DRY-RUN] Nenhuma alteração será gravada.")

    if arquivos_ptbr:
        jobs = []
        for caminho in arquivos_ptbr:
            caminho = validar_arquivo_legenda(caminho)
            if not caminho_dentro_de(pasta_ptbr_in, caminho):
                _emit(f"{Fore.YELLOW}[AVISO] Arquivo fora da pasta PT-BR: {caminho}")
            if permitir_in_place:
                caminho_saida = caminho
            elif caminho_dentro_de(pasta_ptbr_in, caminho):
                caminho_saida = caminho_saida_relativo(pasta_ptbr_in, caminho, pasta_ptbr_out)
            else:
                caminho_saida = os.path.join(pasta_ptbr_out, os.path.basename(caminho))
            jobs.append((caminho, caminho_saida))
    else:
        jobs = [
            (caminho, caminho_saida_relativo(pasta_ptbr_in, caminho, pasta_ptbr_out))
            for caminho in listar_arquivos_ass(pasta_ptbr_in)
        ]

    _emit(f"Encontrados {len(jobs)} arquivo(s) .ass\n{'-' * 80}")

    log_modificacoes = []
    stats = {
        "arquivos_processados": 0,
        "arquivos_pulados": 0,
        "linhas_modificadas": 0,
        "karaoke_restaurado": 0,
        "lore_corrigido": 0,
        "higienizacao_geral": 0,
        "correcoes_manuais": 0,
    }

    tempo_inicio = time.time()
    pulados = 0

    for num_arq, (caminho_ptbr_in, caminho_ptbr_out) in enumerate(jobs, 1):
        if not caminho_dentro_de(pasta_ptbr_in, caminho_ptbr_in) and not arquivos_ptbr:
            _emit(f"{Fore.YELLOW}[AVISO] Ignorando caminho fora da pasta de entrada: {caminho_ptbr_in}")
            continue

        arq = os.path.basename(caminho_ptbr_in)
        os.makedirs(os.path.dirname(caminho_ptbr_out) or ".", exist_ok=True)

        if pular_existentes and os.path.isfile(caminho_ptbr_out) and not permitir_in_place:
            pulados += 1
            stats["arquivos_pulados"] += 1
            _emit(f"{Fore.CYAN}[{num_arq}/{len(jobs)}] Pulando (já existe): {os.path.basename(caminho_ptbr_out)}")
            continue

        if not caminho_dentro_de(pasta_ptbr_out, caminho_ptbr_out) and not permitir_in_place:
            _emit(f"{Fore.RED}[ERRO] Caminho de saída inválido (path traversal): {caminho_ptbr_out}")
            continue

        caminho_eng_in = achar_legenda_eng(caminho_ptbr_in, pasta_eng_in, pasta_ptbr_in)
        chave_ep = obter_chave_episodio(arq)

        decorrido = time.time() - tempo_inicio
        processados = num_arq - 1 - pulados
        sufixo_eta = ""
        if processados > 0:
            media = decorrido / processados
            restantes = len(jobs) - num_arq + 1
            sufixo_eta = f" | ETA: {formatar_eta(media * restantes)}"

        _emit(f"{Fore.CYAN}[{num_arq}/{len(jobs)}] {arq} (chave: {chave_ep}){sufixo_eta}")
        _emit(f"  Entrada: {caminho_ptbr_in}")
        _emit(f"  Saída  : {caminho_ptbr_out}")

        try:
            linhas_ptbr, _ = ler_arquivo_legenda(caminho_ptbr_in)
        except OSError as e:
            _emit(f"  {Fore.RED}[ERRO] Leitura: {e}")
            continue
        dialogos_eng = []
        if caminho_eng_in:
            try:
                linhas_eng, _ = ler_arquivo_legenda(caminho_eng_in)
                dialogos_eng = indexar_dialogos_eng(linhas_eng)
            except OSError as e:
                _emit(f"  {Fore.YELLOW}[AVISO] ENG ilegível ({e}) — karaoke desativado.")
        else:
            _emit(f"  {Fore.YELLOW}[AVISO] ENG não encontrado — karaoke desativado para este arquivo.")

        linhas_novas = []
        modificacoes_arquivo = 0
        stats["arquivos_processados"] += 1
        indice_dialogo = 0

        for idx_linha, linha in enumerate(linhas_ptbr, 1):
            parsed = parse_dialogue(linha)
            if not parsed:
                linhas_novas.append(linha)
                continue

            prefixo, texto_ptbr, estilo = parsed
            texto_original = texto_ptbr
            texto_final = texto_ptbr
            modificada = False
            motivo = ""
            tipo = ""

            eh_grafico = any(tag in texto_ptbr for tag in ("\\pos", "\\move", "\\clip", "\\org", "{\\p", "|"))
            eh_karaoke = _estilo_karaoke(estilo)

            # 1) Karaokê: restaurar texto ENG pelo índice do evento Dialogue (não linha do arquivo)
            if eh_karaoke and indice_dialogo < len(dialogos_eng):
                texto_eng = dialogos_eng[indice_dialogo]
                if texto_ptbr != texto_eng:
                    texto_final = texto_eng
                    modificada = True
                    motivo = f"Karaokê restaurado (estilo: {estilo})"
                    tipo = "KARAOKE"

            # 2) Correção manual por linha do arquivo
            elif chave_ep in CORRECOES_ESPECIFICAS and idx_linha in CORRECOES_ESPECIFICAS[chave_ep]:
                subst = CORRECOES_ESPECIFICAS[chave_ep][idx_linha]
                if texto_ptbr != subst:
                    texto_final = subst
                    modificada = True
                    motivo = "Correção cirúrgica manual"
                    tipo = "MANUAL"

            # 3) Higienização geral (não karaoke)
            elif not eh_karaoke:
                texto_hig = higienizar_texto(texto_ptbr, eh_grafico=eh_grafico)
                if texto_hig != texto_ptbr:
                    contem_lore = any(p.search(texto_ptbr) for p, _ in SUBSTITUICOES_LORE)
                    texto_final = texto_hig
                    modificada = True
                    if contem_lore:
                        motivo = "Correção de lore Gundam ZZ"
                        tipo = "LORE"
                    else:
                        motivo = "Higienização estrutural / gramática"
                        tipo = "HIGIENIZACAO"

            indice_dialogo += 1

            if modificada:
                modificacoes_arquivo += 1
                stats["linhas_modificadas"] += 1
                stats[{"KARAOKE": "karaoke_restaurado", "LORE": "lore_corrigido",
                       "HIGIENIZACAO": "higienizacao_geral", "MANUAL": "correcoes_manuais"}[tipo]] += 1

                _emit(f"  {Fore.YELLOW}#{stats['linhas_modificadas']} L{idx_linha} D{indice_dialogo} — {motivo}")
                _emit(f"    {Fore.RED}Antes : {texto_original}")
                _emit(f"    {Fore.GREEN}Depois: {texto_final}")

                log_modificacoes.append({
                    "arquivo": arq,
                    "linha_arquivo": idx_linha,
                    "dialogo": indice_dialogo,
                    "motivo": motivo,
                    "antes": texto_original,
                    "depois": texto_final,
                })

            linhas_novas.append(f"{prefixo}{texto_final}\n")

        if not dry_run:
            gravar_arquivo_atomico(caminho_ptbr_out, linhas_novas)

        if modificacoes_arquivo:
            status = "SIMULADO" if dry_run else "SALVO"
            _emit(f"  {Fore.GREEN}[OK] {modificacoes_arquivo} correção(ões) — {status}")
        else:
            _emit("  [OK] Nenhuma correção necessária.")
        _emit("-" * 50)

    _salvar_log(log_modificacoes, stats, dry_run, pasta_ptbr_in, pasta_eng_in, pasta_ptbr_out)
    return True, stats


def _salvar_log(log_modificacoes, stats, dry_run, pasta_ptbr=None, pasta_eng=None, pasta_out=None):
    pasta_logs = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(pasta_logs, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    modo = "DRY-RUN" if dry_run else "PRODUÇÃO"

    caminho_json = os.path.join(pasta_logs, f"stats_gundam_zz_{ts}.json")
    payload = {
        "timestamp": ts,
        "modo": modo,
        "pastas": {
            "ptbr": pasta_ptbr,
            "eng": pasta_eng,
            "saida": pasta_out,
        },
        "stats": stats,
        "total_modificacoes": len(log_modificacoes),
    }
    try:
        with open(caminho_json, "w", encoding="utf-8") as fj:
            json.dump(payload, fj, indent=2, ensure_ascii=False)
        _emit(f"{Fore.GREEN}✓ Stats JSON: {caminho_json}")
    except OSError as e:
        _emit(f"{Fore.YELLOW}[AVISO] Falha ao gravar stats JSON: {e}")

    if not log_modificacoes:
        return

    caminho_log = os.path.join(pasta_logs, f"revisao_gundam_zz_{ts}.txt")
    try:
        with open(caminho_log, "w", encoding="utf-8") as fl:
            fl.write(f"RELATÓRIO REVISÃO EXTREMA GUNDAM ZZ ({modo})\n")
            fl.write(f"Executado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            if pasta_ptbr:
                fl.write(f"PT-BR : {pasta_ptbr}\n")
            if pasta_eng:
                fl.write(f"ENG   : {pasta_eng}\n")
            if pasta_out:
                fl.write(f"Saída : {pasta_out}\n")
            for chave, valor in stats.items():
                fl.write(f"  {chave}: {valor}\n")
            fl.write("=" * 100 + "\n\n")
            for item in log_modificacoes:
                fl.write(
                    f"[{item['arquivo']} L{item['linha_arquivo']} D{item['dialogo']}] {item['motivo']}\n"
                )
                fl.write(f"  Antes : {item['antes']}\n")
                fl.write(f"  Depois: {item['depois']}\n")
                fl.write("-" * 100 + "\n")
        _emit(f"{Fore.GREEN}✓ Log: {caminho_log}")
    except OSError as e:
        _emit(f"{Fore.YELLOW}[AVISO] Falha ao gravar log: {e}")


def _nomes_combinam(nome_video, nome_legenda):
    """Compara nome base do vídeo com a legenda evitando prefixo ambíguo
    (ex.: 'Episodio_1' não deve combinar com 'Episodio_10')."""
    base_leg = nome_legenda.split("_PTBR")[0]
    for candidato in (nome_legenda, base_leg):
        if candidato == nome_video:
            return True
        if candidato.startswith(nome_video):
            resto = candidato[len(nome_video):]
            if resto and not resto[0].isdigit():
                return True
    return False


def remuxar_mkv(pasta_mkv, pasta_legendas_corrigidas):
    _emit(f"\n{Fore.CYAN}=== REMUX MKV ===")
    if not validar_executavel_mkvmerge(MKVMERGE_PATH):
        _emit(f"{Fore.RED}[ERRO] mkvmerge não encontrado ou executável inválido.")
        return False

    pasta_mkv = validar_pasta(pasta_mkv, "Pasta MKV")
    pasta_legendas_corrigidas = validar_pasta(pasta_legendas_corrigidas, "Pasta legendas corrigidas")

    pasta_saida = os.path.join(pasta_mkv, "corrigidos")
    os.makedirs(pasta_saida, exist_ok=True)
    pasta_saida = os.path.abspath(pasta_saida)

    videos = sorted(
        nome_arquivo_seguro(f)
        for f in os.listdir(pasta_mkv)
        if f.lower().endswith(".mkv") and nome_arquivo_seguro(f)
    )
    legendas = [
        nome_arquivo_seguro(f)
        for f in os.listdir(pasta_legendas_corrigidas)
        if f.lower().endswith(".ass") and nome_arquivo_seguro(f)
    ]

    if not videos:
        _emit(f"{Fore.YELLOW}[AVISO] Nenhum .mkv em {pasta_mkv}")
        return False

    _emit(f"{len(videos)} MKV → saída em {pasta_saida}\n{'-' * 80}")

    for idx, video in enumerate(videos, 1):
        nome_base = video[:-4]
        legenda = None
        for leg in legendas:
            if _nomes_combinam(nome_base, leg):
                legenda = leg
                break
        if not legenda:
            _emit(f"{Fore.RED}[{idx}/{len(videos)}] Sem legenda para {video} — pulando.")
            continue

        caminho_mkv = os.path.join(pasta_mkv, video)
        caminho_leg = os.path.join(pasta_legendas_corrigidas, legenda)
        caminho_out = os.path.join(pasta_saida, video)

        if not (
            caminho_dentro_de(pasta_mkv, caminho_mkv)
            and caminho_dentro_de(pasta_legendas_corrigidas, caminho_leg)
            and caminho_dentro_de(pasta_saida, caminho_out)
        ):
            _emit(f"{Fore.RED}[{idx}/{len(videos)}] Caminho inválido — pulando {video}.")
            continue

        if not os.path.isfile(caminho_mkv) or not os.path.isfile(caminho_leg):
            _emit(f"{Fore.RED}[{idx}/{len(videos)}] Arquivo ausente — pulando {video}.")
            continue

        _emit(f"[{idx}/{len(videos)}] {video} + {legenda}")

        cmd = [
            MKVMERGE_PATH, "-o", caminho_out,
            "--no-subtitles", caminho_mkv,
            "--language", "0:por",
            "--track-name", "0:Português (Mistral)",
            "--default-track", "0:yes",
            "--forced-display-flag", "0:no",
            caminho_leg,
        ]
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=MKVMERGE_TIMEOUT,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            _emit(f"  {Fore.RED}[ERRO] mkvmerge excedeu {MKVMERGE_TIMEOUT}s para {video}")
            continue
        if res.returncode == 0 and os.path.isfile(caminho_out):
            _emit(f"  {Fore.GREEN}[OK] corrigidos\\{video}")
        else:
            _emit(f"  {Fore.RED}[ERRO] mkvmerge falhou (code {res.returncode})")
            if res.stderr:
                _emit(f"  {res.stderr[:300]}")
    return True


def obter_pasta_operador(mensagem, padrao=None):
    """Pergunta pasta ao operador; ENTER aceita o padrão."""
    while True:
        sufixo = f" (ENTER = {padrao})" if padrao else ""
        try:
            entrada = input(f"{Fore.YELLOW}{mensagem}{sufixo}: {Style.RESET_ALL}").strip()
        except (KeyboardInterrupt, EOFError):
            _emit(f"\n{Fore.YELLOW}Cancelado.")
            sys.exit(0)
        try:
            caminho = normalizar_caminho(entrada) if entrada else (padrao or "")
            if not caminho:
                _emit(f"{Fore.RED}[ERRO] Informe um caminho válido.")
                continue
            return validar_pasta(caminho, mensagem)
        except ValueError as e:
            _emit(f"{Fore.RED}[ERRO] {e}")


def deduzir_pasta_eng(pasta_ptbr, raiz_anime=None):
    """Tenta achar legendas ENG: irmã legendas_eng ou mesma pasta com _ENG."""
    pai = os.path.dirname(os.path.abspath(pasta_ptbr))
    candidatos = [
        os.path.join(pai, "legendas_eng"),
        os.path.join(pai, "legendas_ENG"),
    ]
    if raiz_anime:
        candidatos.extend([
            os.path.join(raiz_anime, "legendas_eng"),
            os.path.join(raiz_anime, "legendas_ENG"),
        ])
    for caminho in candidatos:
        if os.path.isdir(caminho):
            return caminho
    return os.path.join(pai, "legendas_eng")


def deduzir_pasta_saida(pasta_ptbr, raiz_anime=None):
    pai = os.path.dirname(os.path.abspath(pasta_ptbr))
    candidatos = [
        os.path.join(pai, "legendas_ptbr_corrigidas"),
        os.path.join(pai, "legendas_ptbr_revisadas"),
    ]
    if raiz_anime:
        candidatos.append(os.path.join(raiz_anime, "legendas_ptbr_corrigidas"))
    for caminho in candidatos:
        if os.path.isdir(caminho):
            return caminho
    return os.path.join(pai, "legendas_ptbr_corrigidas")


def resolver_caminhos(args):
    """Resolve pastas via CLI, --arquivo, argumento posicional ou prompts interativos."""
    try:
        raiz_anime = validar_pasta(args.pasta_anime, "Pasta anime") if args.pasta_anime else None
    except ValueError as e:
        _emit(f"{Fore.RED}[ERRO] {e}")
        sys.exit(1)

    interativo = sys.stdin.isatty() and not args.sem_prompt
    arquivos_cli = []

    if args.arquivo:
        for caminho in args.arquivo:
            try:
                arquivos_cli.append(validar_arquivo_legenda(caminho))
            except ValueError as e:
                _emit(f"{Fore.RED}[ERRO] {e}")
                sys.exit(1)

    try:
        pasta_ptbr = normalizar_caminho(args.entrada) or normalizar_caminho(args.pasta_ptbr)
    except ValueError as e:
        _emit(f"{Fore.RED}[ERRO] {e}")
        sys.exit(1)

    if arquivos_cli and not pasta_ptbr:
        pasta_ptbr = os.path.dirname(arquivos_cli[0])

    if not pasta_ptbr and interativo:
        padrao_pt = os.path.join(PASTA_ANIME_PADRAO, "legendas_ptbr")
        _emit(f"\n{Fore.CYAN}Informe as pastas das legendas a revisar.{Style.RESET_ALL}")
        pasta_ptbr = obter_pasta_operador("Pasta das legendas PT-BR traduzidas (.ass)", padrao_pt)
    elif not pasta_ptbr:
        raiz = raiz_anime or PASTA_ANIME_PADRAO
        pasta_ptbr = os.path.join(raiz, "legendas_ptbr")

    try:
        pasta_ptbr = validar_pasta(pasta_ptbr, "Pasta PT-BR")
    except ValueError as e:
        _emit(f"{Fore.RED}[ERRO] {e}")
        sys.exit(1)

    if args.eng:
        if os.path.isdir(args.eng):
            pasta_eng = os.path.abspath(args.eng)
        else:
            _emit(f"{Fore.YELLOW}[AVISO] Pasta ENG não encontrada: {args.eng}")
            pasta_eng = None
    elif interativo:
        # Pula validação chata interativa se não achar nada
        _deduzida = deduzir_pasta_eng(pasta_ptbr, raiz_anime)
        if os.path.isdir(_deduzida):
            pasta_eng = obter_pasta_operador(
                "Pasta das legendas ENG originais (.ass)",
                _deduzida,
            )
        else:
            _emit(f"{Fore.YELLOW}[AVISO] Pasta ENG deduzida não existe. Ignorando ENG.")
            pasta_eng = None
    else:
        _deduzida = deduzir_pasta_eng(pasta_ptbr, raiz_anime)
        if os.path.isdir(_deduzida):
            pasta_eng = os.path.abspath(_deduzida)
        else:
            pasta_eng = None

    if args.saida:
        pasta_out = os.path.abspath(os.path.normpath(normalizar_caminho(args.saida)))
    elif interativo:
        pasta_out = obter_pasta_operador(
            "Pasta de saída (legendas corrigidas)",
            deduzir_pasta_saida(pasta_ptbr, raiz_anime),
        )
    else:
        pasta_out = os.path.abspath(os.path.normpath(deduzir_pasta_saida(pasta_ptbr, raiz_anime)))

    os.makedirs(pasta_out, exist_ok=True)

    if args.pasta_mkv:
        try:
            pasta_mkv = validar_pasta(args.pasta_mkv, "Pasta MKV")
        except ValueError as e:
            _emit(f"{Fore.RED}[ERRO] {e}")
            sys.exit(1)
    else:
        pasta_mkv = raiz_anime or os.path.dirname(pasta_ptbr)
        try:
            pasta_mkv = validar_pasta(pasta_mkv, "Pasta MKV")
        except ValueError as e:
            _emit(f"{Fore.RED}[ERRO] {e}")
            sys.exit(1)

    return pasta_ptbr, pasta_eng, pasta_out, pasta_mkv, arquivos_cli or None

def main():
    parser = argparse.ArgumentParser(
        description="Revisão extrema Gundam ZZ — lore, karaoke, tags ASS",
        epilog=(
            "Exemplos:\n"
            "  python revisao_legenda_gundam_zz.py\n"
            "  python revisao_legenda_gundam_zz.py \"C:\\animes\\Gundam_ZZ\\legendas_ptbr\"\n"
            "  python revisao_legenda_gundam_zz.py --entrada PT --eng ENG --saida SAIDA\n"
            "  python revisao_legenda_gundam_zz.py --arquivo ep01_PTBR.ass --eng ENG --saida SAIDA\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "pasta_ptbr",
        nargs="?",
        help="Pasta com legendas PT-BR (.ass) — atalho para --entrada",
    )
    parser.add_argument(
        "--entrada", "--pasta",
        dest="entrada",
        help="Pasta das legendas PT-BR traduzidas",
    )
    parser.add_argument(
        "--arquivo",
        nargs="+",
        metavar="CAMINHO",
        help="Um ou mais arquivos .ass específicos (ignora varredura de pasta)",
    )
    parser.add_argument("--eng", help="Pasta das legendas ENG originais")
    parser.add_argument("--saida", help="Pasta de saída das legendas corrigidas")
    parser.add_argument(
        "--pasta-anime",
        default=None,
        help=f"Raiz do anime (MKV); padrão interativo: {PASTA_ANIME_PADRAO}",
    )
    parser.add_argument(
        "--pasta-mkv",
        default=None,
        help="Pasta com arquivos .mkv para remux (default: pasta pai das legendas PT-BR)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Simula sem gravar")
    parser.add_argument("--no-remux", action="store_true", help="Não perguntar/remuxar MKV")
    parser.add_argument("--remux", action="store_true", help="Remux automático (sem prompt)")
    parser.add_argument(
        "--pular-existentes",
        action="store_true",
        help="Não reprocessa se a saída já existir",
    )
    parser.add_argument(
        "--sem-prompt",
        action="store_true",
        help="Não perguntar pastas — usa defaults automáticos",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Permite gravar na mesma pasta de entrada (sobrescreve PT-BR original)",
    )
    args = parser.parse_args()

    pasta_ptbr, pasta_eng, pasta_out, pasta_mkv, arquivos_cli = resolver_caminhos(args)

    _emit("=" * 80)
    _emit(f"{Fore.CYAN}  REVISÃO EXTREMA — GUNDAM ZZ")
    _emit("=" * 80)
    _emit(f"{Fore.WHITE}PT-BR (entrada): {pasta_ptbr}")
    _emit(f"{Fore.WHITE}ENG  (origem) : {pasta_eng}")
    _emit(f"{Fore.WHITE}Saída         : {pasta_out}")
    if arquivos_cli:
        _emit(f"{Fore.WHITE}Modo arquivo  : {len(arquivos_cli)} legenda(s)")
    if args.remux or not args.no_remux:
        _emit(f"{Fore.WHITE}MKV  (remux)  : {pasta_mkv}")

    ok, stats = processar_legendas(
        pasta_ptbr,
        pasta_eng,
        pasta_out,
        dry_run=args.dry_run,
        permitir_in_place=args.in_place,
        pular_existentes=args.pular_existentes,
        arquivos_ptbr=arquivos_cli,
    )

    if ok and stats:
        _emit("\n" + "=" * 80)
        _emit(f"{Fore.CYAN}ESTATÍSTICAS:")
        _emit(f"  Arquivos processados     : {stats['arquivos_processados']}")
        if stats.get("arquivos_pulados"):
            _emit(f"  Arquivos pulados         : {stats['arquivos_pulados']}")
        _emit(f"  Linhas modificadas       : {Fore.YELLOW}{stats['linhas_modificadas']}")
        _emit(f"    Karaokê restaurados    : {stats['karaoke_restaurado']}")
        _emit(f"    Lore corrigido         : {stats['lore_corrigido']}")
        _emit(f"    Higienização / gramática: {stats['higienizacao_geral']}")
        _emit(f"    Correções manuais      : {stats['correcoes_manuais']}")
        _emit("=" * 80)

        if not args.dry_run and not args.no_remux:
            fazer_remux = args.remux
            if not fazer_remux and sys.stdin.isatty() and not args.sem_prompt:
                try:
                    opcao = input(
                        f"\n{Fore.YELLOW}Remuxar legendas nos MKV? (s/n): {Style.RESET_ALL}"
                    ).strip().lower()
                    fazer_remux = opcao == "s"
                except (KeyboardInterrupt, EOFError):
                    _emit(f"\n{Fore.YELLOW}Remux cancelado.")
            if fazer_remux:
                remuxar_mkv(pasta_mkv, pasta_out)

    _emit(f"\n{Fore.GREEN}[FIM] Operação finalizada.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        _emit(f"\n{Fore.YELLOW}[AVISO] Interrompido pelo operador.")
        sys.exit(0)
    except Exception as e:
        _emit(f"\n{Fore.RED}[ERRO CRÍTICO] Falha inesperada: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
