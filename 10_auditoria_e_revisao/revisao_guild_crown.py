#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: revisao_guild_crown.py
Revisa e corrige erros de tradução em diálogos (ex: Funerária -> Sepolcro),
expurga notas de tradutor (chaves {...}) e padroniza as letras das músicas
de abertura e encerramento de todos os 22 episódios de Guilty Crown.

Author: Antigravity
Data: Junho 2026
"""

import os
import re
import sys
import shutil
import subprocess
from colorama import init, Fore, Style

# Inicializa o colorama
init(autoreset=True)

# Força codificação UTF-8 na saída padrão do Windows
if sys.version_info >= (3, 7):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Caminhos padrão
PASTA_ANIME = r"E:\animes\GUILTY CROWN\1080p"
PASTA_LEGENDA = os.path.join(PASTA_ANIME, "legendas_ptbr")
PASTA_VIDEO_OUT = os.path.join(PASTA_ANIME, "corrigidos")

def achar_mkvtoolnix():
    for folder in [r"C:\Program Files\MKVToolNix", r"C:\Program Files (x86)\MKVToolNix"]:
        ext_path = os.path.join(folder, "mkvextract.exe")
        merge_path = os.path.join(folder, "mkvmerge.exe")
        if os.path.exists(ext_path) and os.path.exists(merge_path):
            return ext_path, merge_path
    
    ext_path = shutil.which("mkvextract")
    merge_path = shutil.which("mkvmerge")
    return ext_path, merge_path

MKVEXTRACT_PATH, MKVMERGE_PATH = achar_mkvtoolnix()

# Dicionários de mapeamento para as músicas
EUTERPE_PT = [
    ("saita", "Flor que desabrocha no campo"),
    ("aa douka", "Ah, por favor, me diga"),
    ("kizutsukeatte", "Por que as pessoas se machucam"),
    ("arasou no", "E lutam umas contra as outras?"),
    ("rin to saku", "Flor que floresce com elegância"),
    ("nani ga mieru", "O que você consegue ver de onde está?"),
    ("yurushiau", "Por que as pessoas não conseguem"),
    ("dekinai", "Perdoar umas às outras?"),
    ("ame ga sugite", "A chuva passou e o verão refletiu o azul"),
    ("hitotsu ni", "Tornando-se um só"),
    ("yureta", "Balançando suavemente"),
    ("watashi no mae", "Diante de mim"),
    ("nani mo iwazu", "Sem dizer uma única palavra"),
    ("karete yuku", "Para os amigos que estão definhando"),
    ("nani wo omou", "O que você pensa?"),
    ("kotoba wo motanu", "Com essas folhas que não possuem palavras"),
    ("ai wo tsutaeru", "Como você transmite o amor?"),
    ("natsu no hi", "O dia de verão escureceu"),
    ("kaze ga nabiita", "O vento agitou-se"),
    ("futatsu kasanatte", "Dois se sobrepuseram"),
    ("ikita akashi", "Eu cantarei a prova da existência"),
    ("na mo naki", "Para aquele que não tem nome"),
    ("blooming", "Flor que desabrocha no campo"),
    ("flor selvagem", "Flor que desabrocha no campo"),
    ("por favor, me diga", "Ah, por favor, me diga"),
    ("lutam e machucam", "Por que as pessoas se machucam e lutam umas contra as outras?"),
    ("floresce com valor", "Flor que floresce com elegância"),
    ("floresce com v", "Flor que floresce com elegância"),
    ("consigue ver", "O que você consegue ver de onde está?"),
    ("consegue ver", "O que você consegue ver de onde está?"),
    ("se perdoar", "Por que as pessoas não conseguem perdoar umas às outras?"),
    ("perdoar umas", "Por que as pessoas não conseguem perdoar umas às outras?"),
    ("verão refletiu", "A chuva passou e o verão refletiu o azul"),
    ("verao refletiu", "A chuva passou e o verão refletiu o azul"),
    ("suavemente", "Balançando suavemente"),
    ("sem dizer", "Sem dizer uma única palavra"),
    ("definhando", "Para os amigos que estão definhando"),
    ("estão morrendo", "Para os amigos que estão definhando"),
    ("folhas", "Com essas folhas que não possuem palavras"),
    ("como você", "Como você transmite o amor?"),
    ("como voce", "Como você transmite o amor?"),
    ("escureceu", "O dia de verão escureceu"),
    ("vento soprou", "O vento agitou-se"),
    ("prova da", "Eu cantarei a prova da existência"),
    ("sem nome", "Para aquele que não tem nome")
]

EUTERPE_ROMA = [
    ("saita", "Saita no no hana yo"),
    ("aa douka", "Aa douka oshiete okure"),
    ("kizutsukeatte", "Hito wa naze kizutsukeatte"),
    ("arasou no", "Arasou no deshou"),
    ("rin to saku", "Rin to saku hana yo"),
    ("nani ga mieru", "Soko kara nani ga mieru"),
    ("yurushiau", "Hito wa naze yurushiau koto"),
    ("dekinai", "Dekinai no deshou"),
    ("ame ga sugite", "Ame ga sugite natsu wa"),
    ("aoi wo", "Aoi wo utsushita"),
    ("hitotsu ni", "Hitotsu ni natte"),
    ("yureta", "Chiisaku yureta"),
    ("watashi no mae", "Watashi no mae de"),
    ("nani mo iwazu", "Nani mo iwazu ni"),
    ("karete yuku", "Karete yuku tomo ni"),
    ("nani wo omou", "Omae wa nani wo omou"),
    ("kotoba wo motanu", "Kotoba wo motanu sono ha de"),
    ("ai wo tsutaeru", "Nanto ai wo tsutaeru"),
    ("natsu no hi", "Natsu no hi wa kagette"),
    ("kaze ga nabiita", "Kaze ga nabiita"),
    ("futatsu kasanatte", "Futatsu kasanatte"),
    ("ikita akashi", "Ikita akashi wo watashi wa utaou"),
    ("na mo naki", "Na mo naki mono no tame"),
    ("flor selvagem", "Saita no no hana yo"),
    ("me diga", "Aa douka oshiete okure"),
    ("lutam e se", "Hito wa naze kizutsukeatte arasou no deshou"),
    ("flores desabrochando", "Rin to saku hana no you ni"),
    ("se vê dali", "Soko kara nani ga mieru"),
    ("perdoar umas", "Hito wa naze yurushiau koto dekinai no deshou"),
    ("refletiu azul", "Ame wa agari natsu wa aoku utsuru"),
    ("tornando-se um", "Hitotsu ni natte"),
    ("watashi no mae", "watashi no mae de"),
    ("nani mo iwazu", "nani mo iwazu ni"),
    ("nada de", "Na mo naki mono no tame")
]

MY_DEAREST_PT = [
    ("tudoquemefazinteiro", "Então, tudo que me completa"),
    ("everything that makes me whole", "Então, tudo que me completa"),
    ("completa", "Então, tudo que me completa"),
    ("completo", "Então, tudo que me completa"),
    ("makes me whole", "Então, tudo que me completa"),
    ("eusouseu", "Eu sou sua"),
    ("i'm yours", "Eu sou sua"),
    ("sou sua", "Eu sou sua"),
    ("sou seu", "Eu sou sua"),
    ("sorrir assim", "Ei, ter conseguido sorrir assim"),
    ("waraeta", "Ei, ter conseguido sorrir assim"),
    ("primeira vez", "É a primeira vez na minha vida"),
    ("hajimete", "É a primeira vez na minha vida"),
    ("frio e na", "Se você estiver no frio e na solidão"),
    ("kogoesou", "Se você estiver no frio e na solidão"),
    ("fogo para te", "Eu vou me tornar o fogo para te aquecer"),
    ("tomoshibi", "Eu vou me tornar o fogo para te aquecer"),
    ("não se perca", "Para que você não se perca"),
    ("mayoenai", "Para que você não se perca"),
    ("felicidade", "Diga, há tanta felicidade neste mundo, não é?"),
    ("shiawase", "Diga, há tanta felicidade neste mundo, não é?"),
    ("se estivermos juntos", "Um dia, se formos nós dois..."),
    ("formos nós dois", "Um dia, se formos nós dois..."),
    ("itsuka futari", "Um dia, se formos nós dois..."),
    ("alguém mentiroso", "Mesmo se alguém mentiroso"),
    ("calls you a liar", "Mesmo se alguém mentiroso"),
    ("dareka ga", "Mesmo se alguém mentiroso"),
    ("ferir você com", "Tentar te machucar com palavras cruéis"),
    ("kizutsukeyou", "Tentar te machucar com palavras cruéis"),
    ("palavras cruéis", "Tentar te machucar com palavras cruéis"),
    ("mundo não tente", "Mesmo que o mundo inteiro não acredite em você"),
    ("shinjiyou to", "Mesmo que o mundo inteiro não acredite em você"),
    ("acredite em você", "Mesmo que o mundo inteiro não acredite em você"),
    ("imponha uma coroa", "E coloque uma coroa de espinhos em sua cabeça"),
    ("coroa de espinhos", "E coloque uma coroa de espinhos em sua cabeça"),
    ("ibara", "E coloque uma coroa de espinhos em sua cabeça"),
    ("ao seu lado, e somente", "Eu estarei do seu lado, e de mais ninguém"),
    ("estarei do seu lado", "Eu estarei do seu lado, e de mais ninguém"),
    ("mikata da yo", "Eu estarei do seu lado, e de mais ninguém"),
    ("sua dor e solidão", "Eu conheço a sua dor e solidão"),
    ("itami mo kodoku", "Eu conheço a sua dor e solidão")
]

MY_DEAREST_ROMA = [
    ("dedicar a você", "I'm yours"),
    ("dedico a você", "I'm yours"),
    ("i'm yours", "I'm yours"),
    ("não este mundo", "Nee, kono sekai ni wa takusan no shiawase ga aru nda yo, ne?"),
    ("kono sekai", "Nee, kono sekai ni wa takusan no shiawase ga aru nda yo, ne?"),
    ("se for só nós", "Itsuka futari de"),
    ("itsuka futari", "Itsuka futari de"),
    ("funerária", "Itsuka futari de"),
    ("funeraria", "Itsuka futari de"),
    ("chama de mentira", "Tatoe dareka ga kimi wo"),
    ("tatoe dareka", "Tatoe dareka ga kimi wo"),
    ("machuque com palavras", "Hidoi kotoba de kizutsukeyou to shite mo"),
    ("hidoi kotoba", "Hidoi kotoba de kizutsukeyou to shite mo"),
    ("sem o mundo", "Sekai ga kimi wo shinjiyou to shinakute mo"),
    ("sekai ga kimi", "Sekai ga kimi wo shinjiyou to shinakute mo"),
    ("use a coroa", "Ibara no kanmuri wo noseyo to shite mo"),
    ("ibara no kanmuri", "Ibara no kanmuri wo noseyo to shite mo"),
    ("único para você", "Watashi dake wa kimi no mikata da yo"),
    ("mikata da yo", "Watashi dake wa kimi no mikata da yo"),
    ("dor solitária", "Kimi no itami mo kodoku mo shitte iru kara"),
    ("itami mo kodoku", "Kimi no itami mo kodoku mo shitte iru kara"),
    ("everything that", "So, everything that makes me whole / I'm yours")
]

DEPARTURES_PT = [
    ("não preciso", "Eu já não preciso que você me ame,"),
    ("me ame", "Eu já não preciso que você me ame,"),
    ("aisareru", "Eu já não preciso que você me ame,"),
    ("necessária", "Não sou mais necessária para você."),
    ("necessário", "Não sou mais necessária para você."),
    ("hitsuyou", "Não sou mais necessária para você."),
    ("exatamente assim", "E assim, exatamente assim... Eu estou sozinha..."),
    ("sozinha", "E assim, exatamente assim... Eu estou sozinha..."),
    ("hitoribocchi", "E assim, exatamente assim... Eu estou sozinha..."),
    ("aquela época", "O que foi que você disse naquela época?"),
    ("naquele momento", "O que foi que você disse naquela época?"),
    ("itta no", "O que foi que você disse naquela época?"),
    ("inalcançáveis", "As palavras inalcançáveis flutuam no ar"),
    ("mau", "As palavras inalcançáveis flutuam no ar"),
    ("sabendo disso", "Mesmo sabendo disso, hoje eu me pego fazendo de novo"),
    ("me pego", "Mesmo sabendo disso, hoje eu me pego fazendo de novo"),
    ("shimau", "Mesmo sabendo disso, hoje eu me pego fazendo de novo"),
    ("desejo impossível", "Desejando um desejo impossível."),
    ("negaigoto", "Desejando um desejo impossível."),
    ("não me solte", "Não me solte,"),
    ("hanasanaide", "Não me solte,"),
    ("mão bem forte", "Segure minha mão bem forte."),
    ("nigitteite", "Segure minha mão bem forte."),
    ("nós dois continuaremos", "Diga que nós dois continuaremos juntos."),
    ("tsuzuku", "Diga que nós dois continuaremos juntos."),
    ("quente e gentil", "A mão que você segurou era quente e gentil."),
    ("atatakakute", "A mão que você segurou era quente e gentil.")
]

DEPARTURES_ROMA = [
    ("nem mesmo ser amado", "Mou anata kara aisareru koto mo"),
    ("aisareru", "Mou anata kara aisareru koto mo"),
    ("é necessário", "Hitsuyou to sareru koto mo nai"),
    ("hitsuyou", "Hitsuyou to sareru koto mo nai"),
    ("estou aqui sozinha", "Soshite watashi wa koushite hitoribocchi de"),
    ("hitoribocchi", "Soshite watashi wa koushite hitoribocchi de"),
    ("disse naquela", "Ano toki anata wa nante itta no?"),
    ("itta no", "Ano toki anata wa nante itta no?"),
    ("inalcançáveis", "Todokanai kotoba wa chuu wo mau"),
    ("mau", "Todokanai kotoba wa chuu wo mau"),
    ("sabendo", "Wakatteru no ni kyou mo shite shimau"),
    ("shimau", "Wakatteru no ni kyou mo shite shimau"),
    ("desejo", "Kanawanu negaigoto wo"),
    ("negaigoto", "Kanawanu negaigoto wo"),
    ("solte", "Hanasanaide"),
    ("hanasanaide", "Hanasanaide"),
    ("forte", "Gyutto te wo nigitteite"),
    ("nigitteite", "Gyutto te wo nigitteite"),
    ("dois", "Anata to futari tsuzuku to itte"),
    ("tsuzuku", "Anata to futari tsuzuku to itte"),
    ("quente", "Tsunaida sono te wa atatakakute yasashikatta"),
    ("atatakakute", "Tsunaida sono te wa atatakakute yasashikatta")
]

OP2_PT = [
    ("realidade da destruição", "A realidade da destruição ao nosso redor preenche nossa mente"),
    ("realidadastrudo", "A realidade da destruição ao nosso redor preenche nossa mente"),
    ("Houkai", "A realidade da destruição ao nosso redor preenche nossa mente"),
    ("chuva", "A chuva torrencial soa como uma tempestade de lágrimas"),
    ("lágrimas", "A chuva torrencial soa como uma tempestade de lágrimas"),
    ("tempestadedefloren", "A chuva torrencial soa como uma tempestade de lágrimas"),
    ("torrencial", "A chuva torrencial soa como uma tempestade de lágrimas"),
    ("notice", "Perceba"),
    ("notar", "Perceba"),
    ("perceba", "Perceba"),
    ("seus olhos foram", "que seus olhos foram dados a você para se aceitarem,"),
    ("queseus", "que seus olhos foram dados a você para se aceitarem,"),
    ("reconhecer", "que seus olhos foram dados a você para se aceitarem,"),
    ("sua voz foi", "que sua voz foi dada a você para dizer aos outros como você se sente"),
    ("dizer aos outros", "que sua voz foi dada a você para dizer aos outros como você se sente"),
    ("sente", "que sua voz foi dada a você para dizer aos outros como você se sente"),
    ("suas mãos foram dadas", "e que suas mãos foram dadas para segurar quem você ama"),
    ("umamão", "e que suas mãos foram dadas para segurar quem você ama"),
    ("segurar", "e que suas mãos foram dadas para segurar quem você ama"),
    ("seres vivos", "Todos os seres vivos que podem ouvir esta canção,"),
    ("inochi", "Todos os seres vivos que podem ouvir esta canção,"),
    ("canção", "Todos os seres vivos que podem ouvir esta canção,"),
    ("canto", "Todos os seres vivos que podem ouvir esta canção,"),
    ("coração contém", "Sua verdade está dentro do seu coração"),
    ("mune", "Sua verdade está dentro do seu coração"),
    ("verdade", "Sua verdade está dentro do seu coração"),
    ("tempestades", "Mesmo ao cruzar um mar tempestuoso,"),
    ("arashi", "Mesmo ao cruzar um mar tempestuoso,"),
    ("mar", "Mesmo ao cruzar um mar tempestuoso,"),
    ("coincidência", "Ela te dará força que nunca vacilará"),
    ("tsuyosa", "Ela te dará força que nunca vacilará"),
    ("força", "Ela te dará força que nunca vacilará"),
    ("on it", "e nela,"),
    ("nela", "e nela,"),
    ("rely", "confie."),
    ("confie", "confie.")
]

OP2_ROMA = [
    ("sinfonia do void", "Houkai no symphony ga narihibiite"),
    ("houkai", "Houkai no symphony ga narihibiite"),
    ("velha chuva", "Furu ame wa marude namida no neiro"),
    ("furu ame", "Furu ame wa marude namida no neiro"),
    ("kizuite", "Kizuite"),
    ("perceba", "Kizuite"),
    ("esses olhos", "Sono me wa tagai wo mitomeru tame"),
    ("mitomeru", "Sono me wa tagai wo mitomeru tame"),
    ("essa voz", "Sono koe wa omoi wo tsutaeru tame"),
    ("tsutaeru", "Sono koe wa omoi wo tsutaeru tame"),
    ("sonotewa", "Sono te wa daiji na hito to tsunagu tame ni aru"),
    ("tsunagu", "Sono te wa daiji na hito to tsunagu tame ni aru"),
    ("ouvir esta", "Kono uta ga kikoeteru"),
    ("kikoeteru", "Kono uta ga kikoeteru"),
    ("vida", "Inochi aru subete no mono yo"),
    ("inochi", "Inochi aru subete no mono yo"),
    ("verdade", "Shinjitsu wa anata no mune no naka ni aru"),
    ("shinjitsu", "Shinjitsu wa anata no mune no naka ni aru"),
    ("tempestuoso", "Arashi no umi wo yuku toki mo"),
    ("arashi", "Arashi no umi wo yuku toki mo"),
    ("apagada", "Kesshite okusuru koto no nai tsuyosa wo kureru kara"),
    ("tsuyosa", "Kesshite okusuru koto no nai tsuyosa wo kureru kara")
]

ED2_PT = [
    ("deixado para trás", "Deixado para trás em um mundo assim,"),
    ("sozinho neste mundo", "Deixado para trás em um mundo assim,"),
    ("alone", "Deixado para trás em um mundo assim,"),
    ("devo sentir", "O que eu deveria pensar sozinho?"),
    ("omoeba", "O que eu deveria pensar sozinho?"),
    ("tempo se acumula", "O tempo se acumula,"),
    ("spend", "O tempo se acumula,"),
    ("toki", "O tempo se acumula,"),
    ("sentimentos", "Estando sempre tão perto assim,"),
    ("sussurrei", "Estando sempre tão perto assim,"),
    ("chikaku", "Estando sempre tão perto assim,"),
    ("garantido", "Mas agora que você se foi,"),
    ("se foi", "Mas agora que você se foi,"),
    ("inaku", "Mas agora que você se foi,"),
    ("dor", "Eu finalmente percebi o peso da sua ausência."),
    ("bear", "Eu finalmente percebi o peso da sua ausência."),
    ("omosa", "Eu finalmente percebi o peso da sua ausência."),
    ("se eu não tivesse", "Se eu não tivesse soltado sua mão naquele dia"),
    ("deixou", "Se eu não tivesse soltado sua mão naquele dia"),
    ("hanasazu", "Se eu não tivesse soltado sua mão naquele dia"),
    ("segurado com força", "E a tivesse segurado com força..."),
    ("tsukamae", "E a tivesse segurado com força..."),
    ("interesse próprio", "No final, eu só estava satisfazendo meu próprio ego"),
    ("ego", "No final, eu só estava satisfazendo meu próprio ego"),
    ("manzoku", "No final, eu só estava satisfazendo meu próprio ego"),
    ("mentiroso", "É como se eu fosse um mentiroso,"),
    ("usotsuki", "É como se eu fosse um mentiroso,"),
    ("por você", "Dizendo que estava fazendo tudo por você."),
    ("tame", "Dizendo que estava fazendo tudo por você."),
    ("icchatte", "Dizendo que estava fazendo tudo por você."),
    ("não te deixar", "Essas palavras sussurradas nem sequer te alcançam..."),
    ("alcançam", "Essas palavras sussurradas nem sequer te alcançam..."),
    ("todoka", "Essas palavras sussurradas nem sequer te alcançam..."),
    ("corra", "Corra até onde você está!"),
    ("encontrar", "Corra até onde você está!"),
    ("moto", "Corra até onde você está!"),
    ("cairei", "Eu cairei quantas vezes for preciso!"),
    ("nando", "Eu cairei quantas vezes for preciso!"),
    ("koronde", "Eu cairei quantas vezes for preciso!"),
    ("espere", "Espere por mim, pois estou indo te encontrar agora!"),
    ("sugu", "Espere por mim, pois estou indo te encontrar agora!"),
    ("dificuldades", "Não importa quais dificuldades me esperem lá!"),
    ("esperem", "Não importa quais dificuldades me esperem lá!"),
    ("konnan", "Não importa quais dificuldades me esperem lá!")
]

ED2_ROMA = [
    ("boku wa", "Sonna sekai ni nokosareta boku wa,"),
    ("nokosareta", "Sonna sekai ni nokosareta boku wa,"),
    ("hitori nani", "Hitori nani wo omoeba ii?"),
    ("omoeba ii", "Hitori nani wo omoeba ii?"),
    ("toki wo", "Toki wo kasane"),
    ("kasane", "Toki wo kasane"),
    ("omoi wo", "Omoi wo kasane"),
    ("chikaku", "Sou yatte zutto chikaku ni ite"),
    ("zutto", "Sou yatte zutto chikaku ni ite"),
    ("inaku natte", "Atarimae datta kimi ga inaku natte"),
    ("atarimae", "Atarimae datta kimi ga inaku natte"),
    ("shittanda", "Sono omosa wo shittanda"),
    ("omosa", "Sono omosa wo shittanda"),
    ("hanasazu", "Ano hi sono te wo hanasazu"),
    ("sono te", "Ano hi sono te wo hanasazu"),
    ("tsukamae", "Tsuyoku tsukamaetetara"),
    ("manzoku", "Boku wa kekkyoku hitori de jikou manzoku shitaita dake"),
    ("jikou", "Boku wa kekkyoku hitori de jikou manzoku shitaita dake"),
    ("usotsuki", "Maru de kore ja usotsuki da"),
    ("taka", "Kimi no tame toka icchatte"),
    ("icchatte", "Kimi no tame toka icchatte"),
    ("todoka", "Sou tsubuyaita kotoba wa sae todokanakute"),
    ("tsubuyaita", "Sou tsubuyaita kotoba wa sae todokanakute"),
    ("hashire", "Hashire kimi no moto e"),
    ("moto e", "Hashire kimi no moto e"),
    ("koronde", "Boku wa nando datte koronde yaru"),
    ("nando", "Boku wa nando datte koronde yaru"),
    ("matteite", "Matteite ima sugu ni iku kara"),
    ("sugu", "Matteite ima sugu ni iku kara"),
    ("konnan", "Donna konnan ga soko ni atte mo"),
    ("donna", "Donna konnan ga soko ni atte mo")
]

def extrair_numero_episodio(nome_arquivo):
    m = re.search(r'_-_(\d+)_', nome_arquivo)
    if m:
        return int(m.group(1))
    return None

def limpar_tags_ass(texto):
    return re.sub(r"\{[^}]*\}", "", texto)

def corrigir_musica(texto_dialogo, style):
    # Preserva todas as tags ASS iniciais consecutivas
    m_tags = re.match(r"^((?:\{[^}]*\})+)(.*)$", texto_dialogo)
    if m_tags:
        tags, rest = m_tags.groups()
    else:
        tags, rest = "", texto_dialogo
        
    rest_clean = limpar_tags_ass(rest).strip()
    rest_lower = rest_clean.lower()
    
    # 1. OP (Euterpe no EP1, My Dearest nos EPs 2-12)
    if style == "OP" or style == "Other songs":
        # Se for Euterpe
        for pat, rep in EUTERPE_PT:
            if pat in rest_lower:
                return f"{tags}{rep}"
        # Se for My Dearest
        for pat, rep in MY_DEAREST_PT:
            if pat in rest_lower:
                return f"{tags}{rep}"
                
    # 2. OP Roma (Euterpe no EP1, My Dearest nos EPs 2-12)
    elif style == "OP Roma":
        # Se for Euterpe
        for pat, rep in EUTERPE_ROMA:
            if pat in rest_lower:
                return f"{tags}{rep}"
        # Se for My Dearest
        for pat, rep in MY_DEAREST_ROMA:
            if pat in rest_lower:
                return f"{tags}{rep}"
                
    # 3. ED (Departures nos EPs 1-12)
    elif style == "ED":
        for pat, rep in DEPARTURES_PT:
            if pat in rest_lower:
                return f"{tags}{rep}"
                
    # 4. ED Roma L1 (Departures nos EPs 1-12)
    elif style == "ED Roma L1":
        for pat, rep in DEPARTURES_ROMA:
            if pat in rest_lower:
                return f"{tags}{rep}"
                
    # 5. OP_S2 (The Everlasting Guilty Crown nos EPs 13-22)
    elif style == "OP_S2":
        for pat, rep in OP2_PT:
            if pat in rest_lower:
                return f"{tags}{rep}"
                
    # 6. OP_S2_roma (The Everlasting Guilty Crown nos EPs 13-22)
    elif style == "OP_S2_roma":
        for pat, rep in OP2_ROMA:
            if pat in rest_lower:
                return f"{tags}{rep}"
                
    # 7. ED_S2 (Kokuhaku nos EPs 13-22)
    elif style == "ED_S2":
        for pat, rep in ED2_PT:
            if pat in rest_lower:
                return f"{tags}{rep}"
                
    # 8. ED_S2_roma (Kokuhaku nos EPs 13-22)
    elif style == "ED_S2_roma":
        for pat, rep in ED2_ROMA:
            if pat in rest_lower:
                return f"{tags}{rep}"
                
    return texto_dialogo

def aplicar_correcoes_linha(texto, style):
    original = texto
    
    # 1. Expurgo de Notas de Tradutor em Chaves {}
    # Remove qualquer bloco de chaves que não contenha barra invertida \
    texto = re.sub(r'\{[^\\]*?\}', '', texto)
    
    # 2. Se for estilo de música, trata as substituições padrão
    if style in ["OP", "OP Roma", "ED", "ED Roma L1", "OP_S2", "ED_S2", "OP_S2_roma", "ED_S2_roma", "Other songs"]:
        texto = corrigir_musica(texto, style)
        return texto, texto != original
        
    # 3. Correção de Diálogos: Funerária/Funerários -> Sepolcro/membros do Sepolcro
    # Tratando as contrações e variações gramaticais
    texto = re.sub(r"\bda\s+Funerária\b", "do Sepolcro", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bà\s+Funerária\b", "ao Sepolcro", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\ba\s+Funerária\b", "o Sepolcro", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bna\s+Funerária\b", "no Sepolcro", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bpela\s+Funerária\b", "pelo Sepolcro", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bde\s+Funerária\b", "do Sepolcro", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bpara\s+a\s+Funerária\b", "para o Sepolcro", texto, flags=re.IGNORECASE)

    texto = re.sub(r"\bdos\s+Funerários\b", "dos membros do Sepolcro", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bos\s+Funerários\b", "os membros do Sepolcro", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bde\s+um\s+Funerário\b", "de um membro do Sepolcro", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bum\s+Funerário\b", "um membro do Sepolcro", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bo\s+Funerário\b", "o Sepolcro", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\bO\s+Funerário\b", "O Sepolcro", texto)

    # Termos isolados
    texto = re.sub(r"\bFunerários\b", "membros do Sepolcro", texto)
    texto = re.sub(r"\bfunerários\b", "membros do sepulcro", texto)
    texto = re.sub(r"\bFunerário\b", "membro do Sepolcro", texto)
    texto = re.sub(r"\bfunerário\b", "membro do sepulcro", texto)
    texto = re.sub(r"\bFunerária\b", "Sepolcro", texto)
    texto = re.sub(r"\bfunerária\b", "sepolcro", texto)
    
    # Pequenas correções adicionais de digitação encontradas
    texto = re.sub(r"\bRappongi\b", "Roppongi", texto)
    texto = re.sub(r"\bParees\b", "Parece", texto)
    
    return texto, texto != original

def ler_arquivo_legenda(caminho):
    encodings = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
    for encoding in encodings:
        try:
            with open(caminho, 'r', encoding=encoding) as f:
                return f.readlines(), encoding
        except UnicodeDecodeError:
            continue
    with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
        return f.readlines(), "utf-8-replace"

def processar_legendas():
    print(f"\n{Fore.CYAN}=== INICIANDO REVISÃO DE LEGENDAS DO GUILTY CROWN ===")
    if not os.path.exists(PASTA_LEGENDA):
        print(f"{Fore.RED}[ERRO] Diretório de legendas não existe: {PASTA_LEGENDA}")
        return False

    arquivos = [f for f in os.listdir(PASTA_LEGENDA) if f.lower().endswith(".ass") and not f.lower().endswith("_ptbr.ass")]
    arquivos.sort()

    print(f"Localizados {len(arquivos)} arquivos de legenda para processamento.")
    print("-" * 80)

    total_correcoes = 0

    for arq in arquivos:
        ep_num = extrair_numero_episodio(arq)
        if ep_num is None:
            print(f"{Fore.YELLOW}[AVISO] Não foi possível deduzir o número do episódio para: {arq}. Pulando.")
            continue

        caminho_in = os.path.join(PASTA_LEGENDA, arq)
        # Substitui _PTBR_PTBR_ENG.ass, _PTBR_ENG.ass ou _ENG.ass por _PTBR.ass
        nome_saida = arq.replace("_PTBR_PTBR_ENG.ass", "_PTBR.ass").replace("_PTBR_ENG.ass", "_PTBR.ass").replace("_ENG.ass", "_PTBR.ass")
        caminho_out = os.path.join(PASTA_LEGENDA, nome_saida)

        linhas, encoding = ler_arquivo_legenda(caminho_in)
        linhas_novas = []
        correcoes_arq = 0

        for line in linhas:
            if line.startswith("Dialogue:"):
                parts = line.split(",", 9)
                if len(parts) == 10:
                    metadados = ",".join(parts[:9]) + ","
                    style = parts[3].strip()
                    texto_dialogo = parts[9].rstrip("\n")

                    texto_corrigido, modificado = aplicar_correcoes_linha(texto_dialogo, style)
                    if modificado:
                        correcoes_arq += 1
                        line = f"{metadados}{texto_corrigido}\n"

            linhas_novas.append(line)

        # Salva o arquivo corrigido na mesma pasta em UTF-8 com BOM
        with open(caminho_out, "w", encoding="utf-8-sig") as f:
            f.writelines(linhas_novas)

        if correcoes_arq > 0:
            print(f"{Fore.GREEN}[OK] Processado EP {ep_num:02d} | {correcoes_arq} modificações salvas em: {nome_saida}")
            total_correcoes += correcoes_arq
        else:
            print(f"[OK] Processado EP {ep_num:02d} | Nenhuma modificação necessária.")

    print(f"\n{Fore.GREEN}[FIM] Revisão finalizada! Total de {total_correcoes} correções aplicadas nos {len(arquivos)} arquivos.")
    return True

def remuxar_videos():
    print(f"\n{Fore.CYAN}=== INICIANDO RE-MULTIPLEXAÇÃO DOS VÍDEOS ===")
    if not MKVMERGE_PATH:
        print(f"{Fore.RED}[ERRO] mkvmerge não encontrado. Remuxing abortado.")
        return False

    os.makedirs(PASTA_VIDEO_OUT, exist_ok=True)

    videos_mkv = sorted([f for f in os.listdir(PASTA_ANIME) if f.lower().endswith(".mkv")])
    if not videos_mkv:
        print(f"{Fore.YELLOW}[AVISO] Nenhum arquivo .mkv localizado na pasta: {PASTA_ANIME}")
        return False

    print(f"[OK] Encontrados {len(videos_mkv)} arquivos MKV originais.")
    print(f"Os vídeos com a nova legenda corrigida serão salvos em: {PASTA_VIDEO_OUT}")
    print("-" * 80)

    legendas_corrigidas = [f for f in os.listdir(PASTA_LEGENDA) if f.lower().endswith("_ptbr.ass")]

    for idx, video in enumerate(videos_mkv, 1):
        ep_num = extrair_numero_episodio(video)
        if ep_num is None:
            print(f"{Fore.YELLOW}[AVISO] Não foi possível identificar o número do episódio em: {video}. Pulando remux.")
            continue

        # Encontra a legenda corrigida correspondente
        legenda_correta = None
        for leg in legendas_corrigidas:
            leg_ep = extrair_numero_episodio(leg)
            if leg_ep == ep_num:
                legenda_correta = leg
                break

        if not legenda_correta:
            print(f"{Fore.RED}[ERRO] Legenda corrigida para o EP {ep_num:02d} não encontrada. Pulando remux.")
            continue

        caminho_mkv_in = os.path.join(PASTA_ANIME, video)
        caminho_legenda = os.path.join(PASTA_LEGENDA, legenda_correta)
        if video.lower().endswith("_ptbr_ptbr.mkv"):
            nome_mkv_out = video.replace("_PTBR_PTBR.mkv", "_PTBR.mkv")
        elif video.lower().endswith("_ptbr.mkv"):
            nome_mkv_out = video
        else:
            nome_mkv_out = video.replace(".mkv", "_PTBR.mkv")
        caminho_mkv_out = os.path.join(PASTA_VIDEO_OUT, nome_mkv_out)

        print(f"[{idx}/{len(videos_mkv)}] Remuxando EP {ep_num:02d}...")
        print(f"  ↳ Origem: {video}")
        print(f"  ↳ Legenda: {legenda_correta}")

        cmd = [
            MKVMERGE_PATH,
            "-o", caminho_mkv_out,
            "--no-subtitles",            # Remove legendas antigas que continham erros
            caminho_mkv_in,
            "--language", "0:por",
            "--track-name", "0:Português (Revisada - Sepolcro & Músicas)",
            "--default-track", "0:yes",
            caminho_legenda
        ]

        res = subprocess.run(cmd, capture_output=True)
        if res.returncode == 0 and os.path.exists(caminho_mkv_out):
            print(f"  {Fore.GREEN}[SUCESSO] Multiplexado! Salvo em: corrigidos\\{os.path.basename(caminho_mkv_out)}")
        else:
            print(f"  {Fore.RED}[ERRO] Falha ao executar o mkvmerge para {video}.")
        print("-" * 50)

    print(f"\n{Fore.GREEN}[OK] Processo de remuxing finalizado com sucesso!")
    return True

def main():
    print("=" * 80)
    print(f"{Fore.CYAN}    REVISÃO DE LEGENDAS E REMUX DE VÍDEOS: GUILTY CROWN")
    print("=" * 80)

    # 1. Processar a correção de legendas
    sucesso_legendas = processar_legendas()

    if sucesso_legendas:
        # 2. Perguntar se deseja remuxar os vídeos
        print("\n" + "=" * 80)
        opcao = input(f"{Fore.YELLOW}Deseja multiplexar (remux) as novas legendas nos arquivos .mkv originais? (s/n): {Style.RESET_ALL}").strip().lower()
        if opcao == "s":
            remuxar_videos()

    print("\n" + "=" * 80)
    print(f"{Fore.GREEN}[FIM] Operação finalizada!")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[AVISO] Interrompido pelo operador.")
        sys.exit(0)
