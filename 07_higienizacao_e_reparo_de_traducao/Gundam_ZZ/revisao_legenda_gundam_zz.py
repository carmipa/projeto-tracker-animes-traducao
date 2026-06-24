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
from difflib import SequenceMatcher
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
        # Nome real do estilo de karaokê romaji nesta release (OP1/ED1, eps 1-25 e 47).
        # Sem esta entrada, o Mistral "traduzia" a letra romaji para português
        # (ex.: "aa jidai ga naiteiru" -> "a era está chorando"), e a varredura
        # de qualidade não pegava o erro pois o texto resultante parecia PT-BR normal.
        "Song JP",
    )
}

SUBSTITUICOES_LORE = [
    # Facções e Organizações
    (re.compile(r"\bNova Zeon\b", re.I), "Neo Zeon"),
    (re.compile(r"\bNovo Zeon\b", re.I), "Neo Zeon"),
    (re.compile(r"\bZeon Novo\b", re.I), "Neo Zeon"),
    (re.compile(r"\bZeon Nova\b", re.I), "Neo Zeon"),
    (re.compile(r"\bA\.E\.U\.G\.?\b", re.I), "A.E.U.G."),
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
    (re.compile(r"\bQuin\s+Mantha\b", re.I), "Quin Mantha"),
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
    (re.compile(r"\bPrincipauté de Zeon\b", re.I), "Principado de Zeon"),
]

GRAMATICA_E_GAFES = {
    "only be honest with yourself!": "Seja honesta consigo mesma!",
    "Kidnapping Mineva Zabi": "Sequestrar Mineva Zabi",
    "I can go back to the moon and see": "Posso voltar para a Lua e ver",
    "Nous terminaremos": "Nós terminaremos",
    "I decido": "eu decido",
    "Novo Tipos": "Newtypes",
    "Novo Tipo": "Newtype",
    "Tenente-Capital": "Tenente-Capitão",
    "mariône": "marionete",
    "Big Brother": "Irmãozão",
    "Grande Irmão": "Irmãozão",
    "Fool!": "idiota!",
    "Fool": "idiota",
    "Miss Milly": "Srta. Milly",
    "Mistress Chara": "Lady Chara",
    "Muitas unidades móveis": "Muitos mobile suits",
    "E-Escutado": "E-Entendido",
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

    # Falas que o Mistral deixou 100% em inglês (não pegas pela varredura de
    # qualidade porque eram curtas demais para os limiares antigos — ver
    # _parece_ingles_nao_traduzido / _parece_igual_ao_eng).
    "Turn on the holoscope.": "Ligue o holoscópio.",
    "E-Eu-It's the Bawoo!": "É-É o Bawoo!",
    "After you.": "Você primeiro.",
    "C-Can we help you? (sem tradução)": "P-Podemos ajudá-lo?",
    "C-Come on!": "V-Vamos!",
    "Damn you, just now...!": "Maldito, agora mesmo...!",
}

CORRECOES_REGEX_GERAIS = [
    (re.compile(r"(?i)\bonly\s+(Fique|Depressa|atraiam|fazendo|segure-o)\b"), r"\1"),
    (re.compile(r"(?i)\bonly\s+because\."), "Só por isso."),
    (re.compile(r"(?i)\bonly\s+needs to move\."), "Só precisa se mover."),
    (re.compile(r"(?i)\bonly\s+get dressed!"), "Vista-se logo!"),
    (re.compile(r"(?i)\bonly\s+shut up and come!"), "Cale a boca e venha!"),
    (re.compile(r"(?i)\bonly\s+shut up and get in!"), "Cale a boca e entre!"),
    (re.compile(r"(?i)\bonly\s+shut up!"), "Cale a boca!"),
    (re.compile(r"(?i)\bonly\s+relax, Leina\."), "Relaxe, Leina."),
    (re.compile(r"(?i)\bonly\s+leave him alone!"), "Deixe-o em paz!"),
    (re.compile(r"(?i)\bonly\s+you wait, Lady Haman!"), "Espere só, Lady Haman!"),
    (re.compile(r"(?i)\bonly\s+follow the boat da frente\."), "Siga o barco da frente."),
    (re.compile(r"(?i)\bonly\s+go make contact with the La Vie en Rose!"), "Vá fazer contato com a La Vie en Rose!"),
    (re.compile(r"(?i)\bonly\s+go!"), "Vá!"),
    (re.compile(r"(?i)\bonly\s+wait for a chance nossa\."), "Espere por uma chance nossa."),
    (re.compile(r"(?i)\bonly\s+children\?!"), "Só crianças?!"),
    (re.compile(r"(?i)\bonly\s+do what I say and seja meu, Zeta!"), "Faça só o que eu digo e seja meu, Zeta!"),
    (re.compile(r"(?i)\bonly\s+do it!"), "Faça isso!"),
    (re.compile(r"(?i)\bonly\s+proves\\Nque\b"), r"só prova\\Nque"),
    (re.compile(r"(?i)\bonly\s+watch\. I'm going to rescue\\NLeina on my own!"), r"Observe. Eu vou resgatar\\NLeina sozinho!"),
    (re.compile(r"(?i)\bonly\s+because you're Neo Zeon\.\.\.!"), "Só porque vocês são Neo Zeon...!"),
    (re.compile(r"(?i)\bonly\s+hang in there -> Fique firme!"), "Fique firme!"),
    (re.compile(r"(?i)\bonly\s+hang in there, Leina\."), "Fique firme, Leina."),
    (re.compile(r"(?i)\bonly\s+hurry up and dock!"), "Apresse-se e acople!"),
    (re.compile(r"(?i)\bonly\s+hurry\."), "Depressa."),
    (re.compile(r"(?i)\bonly\s+be careful!"), "Cuidado!"),
    (re.compile(r"(?i)\bonly\s+because you have a little\\Nskill de pilotagem de mobile suit!"), r"Só porque você tem um pouco de\\Nhabilidade pilotando mobile suits!"),
    (re.compile(r"(?i)\bonly\s+keep up the surveillance here,\\NTorres\."), r"Continue vigiando aqui,\\NTorres."),
    (re.compile(r"(?i)(^|\\N)only\s+fique quieto e assista!"), r"\1Fique quieto e assista!"),
    (re.compile(r"(?i)(^|\\N)only\s+não esqueça de sorrir\."), r"\1Não esqueça de sorrir."),
    (re.compile(r"(?i)(^|\\N)only\s+espere um pouco mais!"), r"\1Espere só mais um pouco!"),
    (re.compile(r"(?i)\\N\s*Fool!"), r"\\Nidiota!"),
    (re.compile(r"(?i)\\N\s*Miss Milly\b"), r"\\NSrta. Milly"),
    (re.compile(r"(?i)\\N\s*Captão Bright again!"), r"\\No Capitão Bright de novo!"),
    (re.compile(r"(?i)\bonly\s+hang in there\\Naté chegarmos ao Argama!"), r"Aguente firme\\Naté chegarmos ao Argama!"),
    (re.compile(r"(?i)\bonly\s+volta com o Argama para Dublin!"), "Volte com o Argama para Dublin!"),
    (re.compile(r"(?i)(^|\\N)only be honest with yourself!"), r"\1Seja honesta consigo mesma!"),
    (re.compile(r"(?i)(^|\\N)W-What\?!"), r"\1O-o quê?!"),
    (re.compile(r"(?i)Isso é exactly what I'm doing!"), "É exatamente isso que estou fazendo!"),
    (re.compile(r"(?i)exactly what I'm doing!"), "exatamente isso que estou fazendo!"),
    (re.compile(r"(?i)maybe we should come back here\\Nafter I get Leina back\."), r"talvez devêssemos voltar aqui\\Ndepois que eu trouxer Leina de volta."),
    (re.compile(r"(?i)(^|\\N)kidnapping Mineva Zabi"), r"\1Sequestrar Mineva Zabi"),
    (re.compile(r"(?i)(^|\\N)I can go back to the moon and see"), r"\1Posso voltar para a Lua e ver"),
    (re.compile(r"(?i)(^|\\N)Nous terminaremos"), r"\1Nós terminaremos"),
    (re.compile(r"(?i)(^|\\N)I decido"), r"\1Eu decido"),
    (re.compile(r"(?i)both my parents had to leave home to\\Nlook for work, thanks to the war\."), r"meus pais tiveram que sair de casa\\Nem busca de trabalho, por causa da guerra."),
    (re.compile(r"(?i)(^|\\N)At least let us put the hatch on!"), r"\1Pelo menos deixe-nos colocar a escotilha!"),
    (re.compile(r"(?i)Mobile suits make me\.\.\. Make me\.\.\.!"), "Mobile suits me deixam... me deixam...!"),
    (re.compile(r"(?i)exactly like we thought he was!"), "exatamente como pensávamos!"),
    (re.compile(r"(?i)\bI-It just grazed me!"), "S-Só passou de raspão!"),
    (re.compile(r"(?i)A-Are você trying to get us killed\?!"), "V-Você está tentando nos matar?!"),
    (re.compile(r"(?i)W-Wait a minute\.\.\. Do you want\\Nme to take my clothes off\?"), r"E-Espere um pouco... Você quer\\Nque eu tire a roupa?"),
    (re.compile(r"(?i)(^|\\N)I-Is he a friend of yours\?"), r"\1E-Ele é amigo seu?"),
    (re.compile(r"(?i)exactly the thing to get my body back in shape\."), "exatamente o que eu preciso para recuperar a forma."),
    (re.compile(r"(?i)(^|\\N)Hurry up and get on that bus!"), r"\1Depressa, entre naquele ônibus!"),
    (re.compile(r"(?i)(^|\\N)H-Hold on a sec!"), r"\1E-Espere um pouco!"),
    (re.compile(r"(?i)(^|\\N)Y-You're right\. If this works out,"), r"\1V-Você tem razão. Se isso der certo,"),
    (re.compile(r"\[ERRO_TRADUCAO:\s*It\s+\{\\i1\}is\{\\i0\}\s+you,\s+Roux Louka!\]", re.I), "É você, Roux Louka!"),
    (re.compile(r"\[ERRO_TRADUCAO:\s*(\{\\i1\})?Women are scary!\](\{\\i0\})?", re.I), r"\1Mulheres são assustadoras!\2"),
    (re.compile(r"\[ERRO_TRADUCAO:\s*(\{\\i1\})?Something's definitely wrong with Judau!\](\{\\i0\})?", re.I), r"\1Há algo muito errado com Judau!\2"),
    (re.compile(r"\[ERRO_TRADUCAO:\s*(.*?)\]", re.I), r"\1"),
    (re.compile(r"\bNext EPISÓDIO\b", re.I), "Próximo Episódio"),
    (re.compile(r"\bNext Episode\b", re.I), "Próximo Episódio"),
    (re.compile(r"\bBlue Corps\b", re.I), "Corpo Azul"),
    (re.compile(r"\(Part 1\)", re.I), "(Parte 1)"),
    (re.compile(r"\(Part 2\)", re.I), "(Parte 2)"),
    (re.compile(r"\bespaço\\Njerk\b", re.I), r"idiota\\Nespacial"),
    (re.compile(r"(^|\\N)Isto sou da Corpo Azul\b", re.I), r"\1Eu sou do Corpo Azul"),
    (re.compile(r"(^|\\N)Isto sou do Corpo Azul\b", re.I), r"\1Eu sou do Corpo Azul"),
    (re.compile(r"\bda Corpo Azul\b", re.I), "do Corpo Azul"),
    (re.compile(r"\ba Corpo Azul\b", re.I), "o Corpo Azul"),
    (re.compile(r"\bMalditos those da Argama\b", re.I), "Malditos sejam aqueles da Argama"),
    (re.compile(r"\bCom a ajuda do Corpo Azul,\\NI finalmente consegui me reunir com você\b", re.I), r"Com a ajuda do Corpo Azul,\\Nfinalmente consegui me reunir com você"),
    (re.compile(r"\bCorpo Azul espalhará\\Nnome Tuareg\b", re.I), r"Corpo Azul espalhará\\No nome Tuareg"),
    (re.compile(r"\bcidade Frank\b", re.I), "cidade franca"),
    (re.compile(r"\bo Corpo Azul esteja\\Ndestruindo uma cidade franca\b", re.I), r"o Corpo Azul esteja\\Ndestruindo uma cidade franca"),
    (re.compile(r"\bQue se danem o Corpo Azul\b", re.I), "Que se dane o Corpo Azul"),
    (re.compile(r"(^|\\N)Front de Independência Africano\b", re.I), r"\1Frente de Independência Africana"),
    (re.compile(r"\bCorpo Azul do\\NFrente\b", re.I), r"Corpo Azul da\\NFrente"),
    (re.compile(r"\bEu acredito que o Corpo Azul espalhará\\No nome Tuareg\b", re.I), r"Acredito que o Corpo Azul espalhará\\No nome dos Tuareg"),
    (re.compile(r"\bPor que está aliado com\\Na nau de guerra Frank\?!", re.I), r"Por que está aliado com\\Na nave de guerra dos Franks?!"),
    (re.compile(r"\bMesmo que o Corpo Azul esteja\\Ndestruindo uma cidade franca\b", re.I), r"Mesmo que o Corpo Azul esteja\\Ndestruindo uma cidade dos Franks"),
    (re.compile(r"\bQue duplicidade\.", re.I), "Que traição."),
    (re.compile(r"\bMerda pro Gadeb Jasin\b", re.I), "Maldito Gadeb Jasin"),
    (re.compile(r"\bO subordinado Glemy, August,\b", re.I), "August, subordinado de Glemy,"),
    (re.compile(r"(^|\\N)Cause para preocupação\b"), r"\1motivo de preocupação"),
    (re.compile(r"\bSide 1 immediately\b", re.I), "Side 1 imediatamente"),
    (re.compile(r"(?i)(^|\\N)W-Wait a minute\.\.\."), r"\1E-Espere um pouco..."),
    (re.compile(r"\bhatch de acesso\b", re.I), "escotilha de acesso"),
    (re.compile(r"(?i)exactly as expected from the Argama! Os boatos eram verdadeiros\."), "Exatamente como esperado da Argama! Os boatos eram verdadeiros."),
    (re.compile(r"(?i)exactly as expected from the Argama!\\NOs boatos eram verdadeiros\."), r"Exatamente como esperado da Argama!\\NOs boatos eram verdadeiros."),
    (re.compile(r"(?i)'Cause não podemos\b"), "Porque não podemos"),
    (re.compile(r"(?i)exactly como eu esperava\b"), "exatamente como eu esperava"),
    (re.compile(r"(?i)exactly como planejado\b"), "exatamente como planejado"),
    (re.compile(r"(?i)exactly como eu suspeitava\b"), "exatamente como eu suspeitava"),
    (re.compile(r"(?i)exactly como eu pressenti\b"), "exatamente como eu pressenti"),
    (re.compile(r"(?i)\bfique quieto e assista!"), "Fique quieto e assista!"),
    (re.compile(r"(?i)\bnão esqueça de sorrir\."), "Não esqueça de sorrir."),
    (re.compile(r"(?i)\bespere só mais um pouco!"), "Espere só mais um pouco!"),
    (re.compile(r"\bEste é um colônia espacial\b", re.I), "Esta é uma colônia espacial"),
    (re.compile(r"(^|\\N)ultimas nascidas\b", re.I), r"\1últimas criações"),
    (re.compile(r"\bE assim que se tornou conhecido que\b", re.I), "E assim que ficou claro que"),
    (re.compile(r"(^|\\N|\{\\i1\})a declarou independência\b", re.I), r"\1declarou independência"),
    (re.compile(r"\bprimeiro\\Nguerra\b", re.I), r"primeira\\Nguerra"),
    (re.compile(r"\bEu tenho que\b", re.I), "Preciso"),
    (re.compile(r"\beu tenho que\b", re.I), "preciso"),
    (re.compile(r", me recebe\?", re.I), ", está me ouvindo?"),
    (re.compile(r"\bMe recebe\?", re.I), "Está me ouvindo?"),
    (re.compile(r"\bme recebe\?", re.I), "está me ouvindo?"),
    (re.compile(r"\bAssistam enquanto eu derrota o Argama!", re.I), "Assistam enquanto eu derroto o Argama!"),
    (re.compile(r"\bEstou tomando responsabilidade do meu jeito!", re.I), "Estou assumindo a responsabilidade do meu jeito!"),
    (re.compile(r"\bEle tem lutado no deserto por eras\b", re.I), "Ele luta no deserto há eras"),
    (re.compile(r"(^|\\N)ele derrotaria os Gundams\b", re.I), r"\1derrotaria os Gundams"),
    (re.compile(r"\bÉ demonstrar nosso poder através do terror!", re.I), "Vamos demonstrar nosso poder através do terror!"),
    (re.compile(r"\bEu tenho que pagar Judau!", re.I), "Preciso retribuir ao Judau!"),
    (re.compile(r"\bPara parecer um aliado,\\Nvocê precisa igualar sua pele\b", re.I), r"Para parecer um aliado,\\Nvocê precisa combinar com eles"),
    (re.compile(r"\bvou cortar sua cabeça fora\b", re.I), "vou arrancar sua cabeça"),
    (re.compile(r"\bNão grita comigo!", re.I), "Não grite comigo!"),
    (re.compile(r"\bMinha cabeça dói! Deixa pra lá!", re.I), "Minha cabeça dói! Esqueça!"),
    (re.compile(r"\bEla é fria e honrada!", re.I), "Ela é fria e orgulhosa!"),
    (re.compile(r"\bMinha senhora Chara!", re.I), "Lady Chara!"),
    (re.compile(r"(^|\\N)I sinto-me alegre\b", re.I), r"\1sinto-me feliz"),
    (re.compile(r"\bVocê acha que isso vai me fazer virar o rabo e correr\?!", re.I), "Acha que isso vai me fazer fugir com o rabo entre as pernas?!"),
    (re.compile(r"\bIsto é uma tempestade de emoções!", re.I), "Isto é uma explosão de emoções!"),
    (re.compile(r"\bRegulamentações de entrada\b", re.I), "Regulamentos de entrada"),
    (re.compile(r"\bregulamentações\\Nde entrada\b", re.I), r"regulamentos\\Nde entrada"),
    (re.compile(r"\\N\s+ão\b", re.I), r"\\Nnão"),
    (re.compile(r"\b[Nn]ão\s+volte\b"), "não volte"),
    (re.compile(r"\\Ndo Federação\b", re.I), r"\\Nda Federação"),
    (re.compile(r"\\Nenão\b", re.I), r"\\Ne então"),
    (re.compile(r"\buma conceito\b", re.I), "um conceito"),
    (re.compile(r"\\Na um reino\b", re.I), r"\\Num reino"),
    (re.compile(r"pelo\\Na vontade\b", re.I), r"pela\\Nvontade"),
    (re.compile(r"\\NComo investidora\b"), r"\\Ncomo investidora"),
    (re.compile(r"\\NOnde ele está\b"), r"\\Nonde ele está"),
    (re.compile(r"\\NFicassem apenas\b"), r"\\Nficassem apenas"),
    (re.compile(r"\\NPara Lady Haman\b"), r"\\Npara Lady Haman"),
    (re.compile(r"\\NSob ordens\b"), r"\\Nsob ordens"),
    (re.compile(r"\\NDoou esta\b"), r"\\Ndoou esta"),
    (re.compile(r"\\NQue senti\b"), r"\\Nque senti"),
    (re.compile(r"\\NPoderei\b"), r"\\Npoderei"),
    (re.compile(r"\\NTer algum\b"), r"\\Nter algum"),
    (re.compile(r"\bHalloi Stampa\b", re.I), "Stampa Halloi"),
    (re.compile(r"\bseria\\Nelefante\b", re.I), r"seria\\Nelegante"),
    (re.compile(r"(^|\\N)sujeira sala\b", re.I), r"\1sala imunda"),
    (re.compile(r"\bquem\\Ne se aliaram a Glemy\b", re.I), r"quem\\Nse aliou a Glemy"),
    (re.compile(r"\bcortar sua cabeça limpa\b", re.I), "cortar sua cabeça fora"),
    (re.compile(r"(^|\\N)consigo cuidar do seu próprio mobile suit\b", re.I), r"\1consegue cuidar do próprio mobile suit"),
    (re.compile(r"\bO que se pode fazer se nem ao menos\\Nconsegue cuidar do próprio mobile suit\b", re.I), r"O que se pode fazer se ele nem ao menos\\Nconsegue cuidar do próprio mobile suit"),
    (re.compile(r"\bAinda não sei onde Haman está perto\b", re.I), "Ainda não sei onde Haman está"),
    (re.compile(r"(^|\\N)A mobilização de Stampa ataca-nos\b", re.I), r"\1Os homens de Stampa nos atacam"),
    (re.compile(r"\bVocê me recebe\?", re.I), "Está me ouvindo?"),
    (re.compile(r"\bMondo Agake! Gundam Mk-II, vou embora!", re.I), "Mondo Agake! Gundam Mk-II, saindo!"),
    (re.compile(r"(^|\\N)segure-o aí\b", re.I), r"\1Segure-o aí"),
    (re.compile(r"\bO imprinting que ele passou por esta situação é perfeito!", re.I), "O condicionamento dele para esta situação é perfeito!"),
    (re.compile(r"\bPrincipalmente porque já levantei minha mão\b", re.I), "Principalmente porque já ergui minha mão"),
    (re.compile(r"(^|\\N)Cabeça vai estourar!", re.I), r"\1Minha cabeça vai estourar!"),
    (re.compile(r"\bSai daquela mobile suit!", re.I), "Saia daquele mobile suit!"),
    (re.compile(r"\bChara Soon, volta!", re.I), "Chara Soon, volte!"),
    (re.compile(r"\bKamille não lutou porque\\Nsomente lhe ordenaram\.", re.I), r"Kamille não lutou porque\\Nrecebeu ordens."),
    (re.compile(r"\bnascido da tua intuição se torna\\Nteu motivo\b", re.I), r"nascida da sua intuição se torna\\Nseu motivo"),
    (re.compile(r"\bAs vontades\\Ndaqueles que morreram inutilmente em batalha!", re.I), r"A vontade\\Ndaqueles que morreram inutilmente em batalha!"),
    (re.compile(r"\bJudau está dizendo coisas legais para você\b", re.I), "Judau está falando coisas boas para você"),
    (re.compile(r"\b[Dd]a tão fácil\b"), "tão fácil"),
    (re.compile(r"\bque infiltrada em\b", re.I), "que se infiltrou em"),
    (re.compile(r"\btem\\Na um lugar\b", re.I), r"tem\\Num lugar"),
    (re.compile(r"\busar\\Na um traje\b", re.I), r"usar\\Num traje"),
    (re.compile(r"\\MAS\b"), r"\\NMas"),
    (re.compile(r"\\[Mm]as\b"), r"\\NMas"),
    (re.compile(r"\bA\.E\.U\.G\.{2,}"), "A.E.U.G."),
    (re.compile(r"(?i)(^|\\N)seja honesta consigo mesma!"), r"\1Seja honesta consigo mesma!"),
    (re.compile(r"(?i)Turn on the holoscope\.?"), "Ligue o holoscópio."),
    (re.compile(r"(?i)Turn on the holoscope!"), "Ligue o holoscópio!"),
    (re.compile(r"(?i)E-Eu-It's the Bawoo!"), "É-É o Bawoo!"),
    (re.compile(r"(?i)I-It's the Bawoo!"), "É-É o Bawoo!"),
    (re.compile(r"(?i)It's the Bawoo!"), "É o Bawoo!"),
    (re.compile(r"(?i)After you\.?"), "Depois de você."),
    (re.compile(r"(?i)C-Can we help you\?(\s*\(sem tradução\))?"), "P-Podemos ajudá-lo?"),
    (re.compile(r"(?i)Can we help you\?(\s*\(sem tradução\))?"), "Podemos ajudá-lo?"),
    (re.compile(r"(?i)C-Come on!"), "V-Vamos!"),
    (re.compile(r"(?i)Damn you, just now\.\.\.!"), "Maldito, agora mesmo...!"),
    (re.compile(r"(?i)Damn you, just now!"), "Maldito, agora mesmo!"),
]

PADRAO_RESIDUO_IDIOMA = re.compile(
    r"\b(only|kidnapping|can go back|moon and see|again|nous|i decido|"
    r"where|what|when|why|because|yourself|big brother|fool|miss milly|immediately|"
    r"women are scary|something's definitely wrong|space jerk|those da argama|i finally|"
    r"halloi stampa|grande irmão)\b",
    re.I,
)
PADRAO_FRAGMENTO_QUEBRADO = re.compile(
    r"(\\N\s+ão\b|\\MAS\b|A\.E\.U\.G\.{2,}|"
    r"\bI\s+[a-záéíóúâêôãõç]+\b|\b[Nn]ovo Tipos\b|"
    r"\\Ndo Federação\b|\\Nenão\b|\buma conceito\b|\\Na um reino\b|"
    r"\bseria\\Nelefante\b|\\Nsujeira sala\b|quem\\Ne se aliaram\b|"
    r"\bimprinting\b|\\NCabeça vai estourar|\\Nsomente lhe ordenaram|ERRO_TRADUCAO|"
    r"\bCause para preocupação\b|'Cause não podemos|\bexactly como\b|\bonly\s+(fique|não|espere)\b)",
    re.I,
)
PALAVRAS_INGLES_COMUNS = {
    "a", "about", "after", "again", "all", "alright", "am", "an", "and",
    "are", "as", "at", "back", "be", "because", "been", "before", "but",
    "by", "can", "come", "could", "damn", "did", "do", "does", "doing",
    "don't", "for", "from", "get", "go", "going", "gonna", "good", "got",
    "gotta", "had", "has", "have", "he", "hell", "her", "here", "him",
    "his", "how", "i", "if", "in", "is", "it", "just",
    "like", "me", "my", "no", "not", "now", "of", "on", "or", "our",
    "out", "please", "right", "see", "she", "so", "sorry", "stop", "that",
    "the", "their", "them",
    "then", "there", "they", "this", "to", "up", "us", "wait", "was", "we",
    "well", "were", "what", "when", "where", "who", "why", "will", "with",
    "would", "yeah", "you",
    "your",
}
PALAVRAS_PT_COMUNS = {
    "a", "ao", "aos", "as", "com", "como", "da", "das", "de", "do", "dos",
    "e", "ela", "ele", "em", "eu", "isso", "me", "meu", "minha", "na", "nas",
    "não", "no", "nos", "o", "os", "ou", "para", "por", "que", "se", "seu",
    "sua", "um", "uma", "você",
}
PALAVRAS_ROMAJI_COMUNS = {
    "da", "de", "ga", "iu", "ka", "kedo", "mada", "ni", "no", "sora", "to",
    "toki", "wa", "wo", "yo",
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
        if frase[0].isalnum():
            # \b sozinho falha quando a frase vem logo após "\N" (quebra de
            # linha ASS): "N" é caractere de palavra, então não há fronteira
            # entre "N" e a letra seguinte e o \b nunca casa ali. Aceita
            # também a posição logo após \N/\n como início válido.
            prefixo = r"(?:\b|(?<=\\N)|(?<=\\n))"
        else:
            prefixo = ""
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


def _remover_fechamento_sobrando(texto, abre, fecha):
    while texto.count(fecha) > texto.count(abre):
        texto = texto.replace(fecha, "", 1)
    return texto


_GRAMATICA_COMPILADO = _compilar_dicionario(GRAMATICA_E_GAFES)


def _texto_visivel_ass(texto):
    texto = re.sub(r"\{[^{}]*\}", "", texto)
    texto = texto.replace("\\N", " ").replace("\\n", " ")
    return texto.strip()


def _normalizar_para_comparacao(texto):
    texto = _texto_visivel_ass(texto).lower()
    texto = re.sub(r"[^0-9a-záéíóúâêôãõçüñ'\- ]+", " ", texto, flags=re.I)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def _tokens_texto(texto):
    return re.findall(r"[a-záéíóúâêôãõçüñ']+", _normalizar_para_comparacao(texto), re.I)


def _parece_ingles_nao_traduzido(texto):
    tokens = _tokens_texto(texto)
    # Ignora tokens de 1 letra: prefixos de gagueira ("C-Come", "E-Eu") quebram
    # no hífen e sobram como "c"/"e" soltos, que não existem em nenhum dos
    # dicionários e estragavam a proporção em falas curtas.
    tokens = [t for t in tokens if len(t) > 1]
    if len(tokens) < 2:
        return False
    ingles = sum(1 for token in tokens if token in PALAVRAS_INGLES_COMUNS)
    portugues = sum(1 for token in tokens if token in PALAVRAS_PT_COMUNS)
    if len(tokens) < 4:
        # Falas curtas ("After you.", "C-Come on!") nunca atingiam o limiar de
        # 4 tokens e passavam direto. Só sinaliza quando TODOS os tokens batem
        # com inglês e nenhum é uma palavra comum em português (evita falso
        # positivo em ambíguos como "no", "a", "e").
        return ingles == len(tokens) and portugues == 0
    return ingles >= 4 and ingles >= max(3, portugues * 2)


def _tem_fonte_reduzida(texto, limiar=55):
    """Detecta override \\fsNN menor que o normal dentro de um evento.

    Alguns releases reaproveitam o MESMO estilo de karaokê para a linha
    romaji grande e uma segunda linha de tradução menor por baixo (ex.: ED
    especial do ep. 47, onde \\fs60 = romaji e \\fs50 = tradução em inglês).
    Quando o evento ENG correspondente usa fonte reduzida, ele não é romaji
    a ser copiado verbatim — é a legenda de tradução duplicada.
    """
    valores = [int(v) for v in re.findall(r"\\fs(\d+)", texto)]
    return any(v <= limiar for v in valores)


def _segmentos_visiveis(texto):
    """Divide o texto visível (sem tags ASS) pelas quebras \\N/\\n."""
    sem_tags = re.sub(r"\{[^{}]*\}", "", texto)
    return [s.strip() for s in re.split(r"\\N|\\n", sem_tags) if s.strip()]


def _parece_romaji_karaoke(texto):
    tokens = _tokens_texto(texto)
    if len(tokens) < 5:
        return False
    romaji = sum(1 for token in tokens if token in PALAVRAS_ROMAJI_COMUNS)
    ingles = sum(1 for token in tokens if token in PALAVRAS_INGLES_COMUNS)
    return romaji >= 2 and ingles <= 2


def _parece_igual_ao_eng(texto_pt, texto_eng):
    if not texto_eng:
        return False
    if _parece_romaji_karaoke(texto_pt):
        return False
    pt = _normalizar_para_comparacao(texto_pt)
    eng = _normalizar_para_comparacao(texto_eng)
    if not pt or not eng or len(pt) < 4 or len(eng) < 4:
        return False
    tokens_pt = _tokens_texto(texto_pt)
    ingles = sum(1 for token in tokens_pt if token in PALAVRAS_INGLES_COMUNS)
    if pt == eng:
        return ingles >= 2 or _parece_ingles_nao_traduzido(texto_pt)
    if _parece_ingles_nao_traduzido(texto_pt):
        return SequenceMatcher(None, pt, eng).ratio() >= 0.82
    return False


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
    texto = re.sub(r"(\{[^{}]*\\pos\([^{}]*?\))(?=\\h)", r"\1}", texto)

    def _fix_bloco(match):
        bloco = match.group(0)
        return re.sub(r"\\\\([a-zA-Z])", r"\\\1", bloco)

    return re.sub(r"\{[^{}]*\}", _fix_bloco, texto)


def _normalizar_barras_texto_ass(texto):
    """Corrige barras soltas no texto visível sem alterar comandos dentro de tags ASS."""
    partes = re.split(r"(\{[^{}]*\})", texto)
    for i, parte in enumerate(partes):
        if not parte or parte.startswith("{"):
            continue
        parte = re.sub(r"\\\\+[Nn]", r"\\N", parte)
        parte = re.sub(r"\\([!?.,;:])", r"\1", parte)
        parte = re.sub(r"\\(?![Nnh])(?=\S)", r"\\N", parte)
        partes[i] = parte
    return "".join(partes)


def _estilo_karaoke(estilo):
    return estilo.strip().lower() in ESTILOS_KARAOKE_ROMAJI


def higienizar_texto(texto, eh_grafico=False):
    t = texto

    t = _normalizar_barras_tag_ass(t)
    t = _normalizar_barras_texto_ass(t)
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
    # Em ASS, "\Ntexto" é a forma limpa; inserir espaço depois do \N gera
    # milhares de alterações cosméticas e pode criar fragmentos como "\N ão".
    t = re.sub(r"\\N\s+", r"\\N", t)

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
    t = re.sub(r"(?<!\\)\\Para\b", r"\\Npara", t)
    t = re.sub(r"\\não\b", r"\\Nnão", t, flags=re.I)
    t = re.sub(r"\\+\s*$", "", t)
    t = re.sub(r"\?!!", "?!", t)
    t = re.sub(r"\\NSPara\b", r"\\NPara", t)
    t = re.sub(r"\\NMPorém\b", r"\\NPorém", t)
    t = re.sub(r"\\NEspace aéreo\b", r"\\Nespaço aéreo", t, flags=re.I)
    t = re.sub(r"\\NAo sei\b", r"\\NNão sei", t)

    for padrao, subst in SUBSTITUICOES_LORE:
        t = padrao.sub(subst, t)

    for padrao, correto in _GRAMATICA_COMPILADO:
        t = padrao.sub(lambda m, c=correto: _preservar_caixa(c, m.group(0)), t)

    for padrao, subst in CORRECOES_REGEX_GERAIS:
        t = padrao.sub(subst, t)

    t = re.sub(r"\bA\.E\.U\.G\.(?=\.)", "A.E.U.G", t)
    t = re.sub(r"(\{\\i1\})(.*?)(\{\\i1\})", r"\1\2", t)
    t = re.sub(r"!\s*(Aguente firme)", r"! \1", t)

    t = _remover_fechamento_sobrando(t, "{\\i1}", "{\\i0}")
    t = _remover_fechamento_sobrando(t, "{\\b1}", "{\\b0}")
    t = _balancear_tag(t, "{\\i1}", "{\\i0}")
    t = _balancear_tag(t, "{\\b1}", "{\\b0}")
    t = re.sub(r"\s*\{\\i1\}\{\\i0\}", "", t)
    t = re.sub(r"\s*\{\\b1\}\{\\b0\}", "", t)

    return t


def detectar_suspeita_qualidade(texto, texto_eng=None, eh_karaoke=False):
    """Retorna motivo de revisão manual quando a linha ainda parece problemática."""
    if eh_karaoke:
        # Texto de karaokê é JP/romaji por natureza (ou mistura inglês de
        # propósito em letras macarrônicas, ex. "Anime Ja Nai"). As heurísticas
        # de "não traduzido"/"fragmento" abaixo são pensadas para diálogo
        # comum em português e davam falso positivo aqui; a checagem própria
        # de karaokê já roda fora desta função (motivo_karaoke_suspeito).
        return ""
    if _parece_igual_ao_eng(texto, texto_eng):
        return "possível linha não traduzida (igual ou muito parecida com ENG)"
    if _parece_ingles_nao_traduzido(texto):
        return "possível linha não traduzida (inglês predominante)"
    if re.search(r"\bsem\s+tradu[çc][aã]o\b", texto, re.I):
        return "marcador de tradução pendente deixado no texto"
    # Linha com múltiplos segmentos (\N) onde só uma parte ficou em inglês —
    # o teste acima sobre o texto inteiro dilui a proporção e não pega isso
    # (ex.: "Irei fortalecer o moral da frota.\NTurn on the holoscope.").
    if not _parece_romaji_karaoke(texto):
        segmentos = _segmentos_visiveis(texto)
        if len(segmentos) > 1:
            for segmento in segmentos:
                if _parece_ingles_nao_traduzido(segmento):
                    return "possível trecho não traduzido (segmento em inglês dentro da linha)"
    if PADRAO_RESIDUO_IDIOMA.search(texto):
        return "possível resíduo de inglês/francês"
    if PADRAO_FRAGMENTO_QUEBRADO.search(texto):
        return "possível fragmento quebrado"
    return ""


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
        "linhas_suspeitas": 0,
        "linhas_possivelmente_nao_traduzidas": 0,
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
            texto_eng_ref = dialogos_eng[indice_dialogo] if indice_dialogo < len(dialogos_eng) else None
            motivo_karaoke_suspeito = ""

            # 1) Karaokê: restaurar texto ENG pelo índice do evento Dialogue (não linha do arquivo)
            if eh_karaoke and indice_dialogo < len(dialogos_eng):
                texto_eng = texto_eng_ref
                if texto_eng and _tem_fonte_reduzida(texto_eng):
                    # Alguns releases (ex.: ED especial do ep. 47) usam o MESMO
                    # estilo de karaokê tanto para a linha romaji grande quanto
                    # para uma legenda de tradução duplicada menor por baixo.
                    # Copiar verbatim sobrescreveria uma tradução se houver
                    # texto em inglês — não restaura, só sinaliza para revisão.
                    motivo_karaoke_suspeito = (
                        "estilo de karaokê, mas o evento ENG correspondente possui "
                        "fonte reduzida (possível legenda) — confirmar manualmente"
                    )
                elif texto_ptbr != texto_eng:
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

            motivo_suspeita = motivo_karaoke_suspeito or detectar_suspeita_qualidade(
                texto_final,
                None if (eh_karaoke or eh_grafico) else texto_eng_ref,
                eh_karaoke=eh_karaoke,
            )
            if motivo_suspeita:
                stats["linhas_suspeitas"] += 1
                if "não traduzida" in motivo_suspeita:
                    stats["linhas_possivelmente_nao_traduzidas"] += 1
                _emit(
                    f"  {Fore.MAGENTA}[REVISAR] L{idx_linha} D{indice_dialogo} — {motivo_suspeita}: {texto_final}"
                )
                log_modificacoes.append({
                    "arquivo": arq,
                    "linha_arquivo": idx_linha,
                    "dialogo": indice_dialogo,
                    "motivo": f"REVISAR: {motivo_suspeita}",
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
        _emit(f"    Linhas suspeitas       : {stats.get('linhas_suspeitas', 0)}")
        _emit(f"      Possível não traduzida: {stats.get('linhas_possivelmente_nao_traduzidas', 0)}")
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
