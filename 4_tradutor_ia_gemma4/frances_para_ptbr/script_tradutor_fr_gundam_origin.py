#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PIPELINE INDUSTRIAL UNIFICADO - VERSÃO FRANCÊS (FR -> PT-BR)
Extrai .ass dos .mkv → Detecta Encoding → Traduz do Francês via LM Studio → Salva

Sistema de Logs Auditável com Temporizadores de Precisão:
  Mede o tempo decorrido por arquivo e o tempo total de execução.
Otimizado com cache persistente em disco, mascaramento de tags ASS e concorrência multithread.
"""

import os
import sys
import re
import json
import time
import subprocess
import requests
import traceback
import shutil
from datetime import datetime

try:
    from tqdm import tqdm
except ImportError:
    print("ERRO: tqdm nao instalado. Execute: pip install tqdm")
    sys.exit(1)

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    print("ERRO: colorama nao instalado. Execute: pip install colorama")
    sys.exit(1)


# ============================================================================
# GERENCIADOR DE LOGS PROFISSIONAL
# ============================================================================

class GerenciadorLogs:
    """
    Sistema de logs auditável com 4 arquivos separados por execução.
    Cria pasta logs/ automaticamente ao lado do script.
    """

    CORES = {
        "SUCESSO": Fore.GREEN + Style.BRIGHT,
        "ERRO":    Fore.RED + Style.BRIGHT,
        "CRÍTICO": Fore.RED + Style.BRIGHT,
        "AVISO":   Fore.YELLOW,
        "INFO":    Fore.WHITE,
        "DEBUG":   Fore.CYAN,
    }

    def __init__(self):
        # Pasta logs/ ao lado do script
        self.pasta_logs = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "logs"
        )
        os.makedirs(self.pasta_logs, exist_ok=True)

        self.ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        # 4 arquivos de auditoria
        self.f_pipeline = open(
            os.path.join(self.pasta_logs, f"pipeline_fr_{self.ts}.txt"),
            'w', encoding='utf-8'
        )
        self.f_erros = open(
            os.path.join(self.pasta_logs, f"erros_fr_{self.ts}.txt"),
            'w', encoding='utf-8'
        )
        self.caminho_stats  = os.path.join(self.pasta_logs, f"stats_fr_{self.ts}.json")
        self.caminho_config = os.path.join(self.pasta_logs, f"config_fr_{self.ts}.txt")

        header = (
            f"\n{'='*80}\n"
            f"PIPELINE INDUSTRIAL DE TRADUÇÃO FRANCÊS - LOG DE AUDITORIA\n"
            f"{'='*80}\n"
            f"Início    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Python    : {sys.version.split()[0]}\n"
            f"Pasta logs: {self.pasta_logs}\n"
            f"{'='*80}\n\n"
        )
        for f in (self.f_pipeline, self.f_erros):
            f.write(header)
            f.flush()

    # ── helpers ──────────────────────────────────────────────────────────────

    def _gravar(self, nivel: str, mensagem: str):
        ts  = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        linha = f"[{ts}] [{nivel:8s}] {mensagem}"

        self.f_pipeline.write(linha + "\n")
        self.f_pipeline.flush()

        if nivel in ("ERRO", "CRÍTICO"):
            self.f_erros.write(linha + "\n")
            self.f_erros.flush()

        cor = self.CORES.get(nivel, Fore.WHITE)
        print(f"{cor}{linha}{Style.RESET_ALL}")

    def secao(self, titulo: str):
        bloco = f"\n{'='*80}\n{titulo.center(80)}\n{'='*80}\n"
        self.f_pipeline.write(bloco + "\n")
        self.f_pipeline.flush()
        print(f"\n{Fore.MAGENTA}{titulo.center(80)}{Style.RESET_ALL}\n")

    # ── níveis ────────────────────────────────────────────────────────────────

    def sucesso(self, msg): self._gravar("SUCESSO", msg)
    def info   (self, msg): self._gravar("INFO",    msg)
    def debug  (self, msg): self._gravar("DEBUG",   msg)
    def aviso  (self, msg): self._gravar("AVISO",   msg)

    def erro(self, msg, exc=None):
        self._gravar("ERRO", msg)
        if exc:
            self.f_erros.write(f"  Exceção: {exc}\n")
            self.f_erros.flush()

    def traceback_completo(self, contexto: str = ""):
        tb = traceback.format_exc()
        bloco = (
            f"\n{'='*80}\n"
            f"TRACEBACK COMPLETO\n"
            f"{'='*80}\n"
            f"Contexto : {contexto}\n\n"
            f"{tb}\n"
            f"{'-'*80}\n\n"
        )
        self.f_erros.write(bloco)
        self.f_erros.flush()
        print(f"{Fore.RED}{tb}{Style.RESET_ALL}")

    # ── arquivos de suporte ───────────────────────────────────────────────────

    def salvar_config(self, lm_url, pasta_entrada, track_id, pasta_saida):
        conteudo = (
            f"\n{'='*80}\nCONFIGURAÇÃO DA EXECUÇÃO\n{'='*80}\n\n"
            f"Data/Hora      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"LM Studio URL  : {lm_url}\n"
            f"Modelo         : Gemma 4B (google/gemma-4-e4b)\n"
            f"Hardware       : RTX 5600 (8 GB VRAM) / Contexto: 8000 / Threads: 2\n\n"
            f"Pasta entrada  : {pasta_entrada}\n"
            f"Track ID       : {track_id}\n"
            f"Pasta saída    : {pasta_saida}\n\n"
            f"Logs:\n"
            f"  Pipeline : pipeline_fr_{self.ts}.txt\n"
            f"  Erros    : erros_fr_{self.ts}.txt\n"
            f"  Stats    : stats_fr_{self.ts}.json\n"
            f"  Config   : config_fr_{self.ts}.txt\n"
        )
        with open(self.caminho_config, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        self.debug(f"Config salvo: {os.path.basename(self.caminho_config)}")

    def salvar_stats(self, stats: dict):
        payload = {
            "timestamp": self.ts,
            "data_hora":  datetime.now().isoformat(),
            "stats":      stats,
        }
        with open(self.caminho_stats, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        self.debug(f"Stats salvo: {os.path.basename(self.caminho_stats)}")

    def relatorio_final(self, stats: dict, pasta_saida: str, tempo_total_formatado: str):
        corpo = (
            f"\n{'='*80}\nRELATÓRIO FINAL\n{'='*80}\n\n"
            f"Tempo total de execução : {tempo_total_formatado}\n"
            f"Arquivos .mkv           : {stats.get('mkv_total', 0)}\n"
            f"Extraídos               : {stats.get('extraidos', 0)}\n"
            f"Traduzidos              : {stats.get('traduzidos', 0)}\n"
            f"Erros extração          : {stats.get('erros_extracao', 0)}\n"
            f"Erros tradução          : {stats.get('erros_traducao', 0)}\n"
            f"Requisições API         : {stats.get('requisicoes', 0)}\n"
            f"Cache hits              : {stats.get('cache_hits', 0)}\n"
            f"Linhas traduzidas       : {stats.get('linhas_traduzidas', 0)}\n"
            f"\nEncodings detectados:\n"
        )
        for enc, n in stats.get('encodings_detectados', {}).items():
            corpo += f"  {enc}: {n} arquivo(s)\n"
        corpo += (
            f"\nArquivos de log:\n"
            f"  📁  {self.pasta_logs}\n"
            f"  📄  pipeline_fr_{self.ts}.txt\n"
            f"  ⚠️   erros_fr_{self.ts}.txt\n"
            f"  📊  stats_fr_{self.ts}.json\n"
            f"  ⚙️   config_fr_{self.ts}.txt\n"
            f"\nLegendas salvas em: {pasta_saida}\n"
        )
        self.f_pipeline.write(corpo)
        self.f_pipeline.flush()
        print(corpo)

    def fechar(self):
        rodape = (
            f"\n{'='*80}\n"
            f"Execução finalizada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"{'='*80}\n"
        )
        for f in (self.f_pipeline, self.f_erros):
            f.write(rodape)
            f.close()

        print(f"\n{Fore.GREEN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ LOGS SALVOS EM: {self.pasta_logs}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*80}{Style.RESET_ALL}\n")
        for nome in [
            f"pipeline_fr_{self.ts}.txt",
            f"erros_fr_{self.ts}.txt",
            f"stats_fr_{self.ts}.json",
            f"config_fr_{self.ts}.txt",
        ]:
            print(f"  {nome}")
        print()


# ============================================================================
# FALLBACK CHAIN DE ENCODING
# ============================================================================

ENCODINGS_FALLBACK = [
    'utf-8-sig',
    'utf-8',
    'cp1252',
    'latin-1',
    'iso-8859-1',
]

def ler_arquivo_com_encoding(caminho: str, log: GerenciadorLogs):
    """
    Tenta ler o arquivo percorrendo a cadeia de encodings.
    """
    log.debug(f"Detectando encoding: {os.path.basename(caminho)}")

    for enc in ENCODINGS_FALLBACK:
        try:
            with open(caminho, 'r', encoding=enc) as f:
                linhas = f.readlines()
            log.sucesso(f"Encoding detectado: {enc.upper()}")
            return linhas, enc
        except UnicodeDecodeError:
            continue

    # Fallback absoluto
    log.aviso("Todos os encodings falharam. Usando utf-8 + errors='replace'")
    with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
        linhas = f.readlines()
    return list(linhas), 'utf-8-bypass'


# ============================================================================
# PIPELINE PRINCIPAL
# ============================================================================

class Pipeline:
    """
    Orquestrador principal da tradução do Francês para Português.
    """

    LM_URL  = "http://127.0.0.1:1234"
    API_URL = f"{LM_URL}/v1/chat/completions"

    # Tradutor do Francês para Português - Gundam The Origin
    PROMPT_SISTEMA = (
        """Você é um tradutor e localizador especialista em legendas de anime, ficção científica militar, mechas e no universo de Mobile Suit Gundam: The Origin / Universal Century.

TAREFA:
Traduza as linhas de legenda do Francês para Português do Brasil (PT-BR), mantendo naturalidade, impacto dramático e consistência de lore. A tradução deve soar como legenda profissional de anime: curta, fluida, humana e fácil de ler na tela.

REGRAS ABSOLUTAS DE SAÍDA:
1. Responda somente com as linhas traduzidas numeradas. Não explique, não cumprimente, não adicione notas.
2. Preserve os índices exatamente: se receber "[0] texto", responda "[0] tradução".
3. Preserve marcadores de formatação como [T0], [T1], [T2] exatamente no mesmo ponto lógico da frase. Nunca apague, renumere ou traduza esses marcadores.
4. Preserve quebras e escapes de legenda como \\N, \\n, \\h exatamente como aparecem. Nunca transforme \\N em quebra de linha real.
5. Preserve nomes próprios, siglas, códigos de modelo, nomes de naves e nomes de mobile suits, salvo tradução obrigatória no glossário.
6. Se uma linha for grito, ordem curta, transmissão de rádio ou frase incompleta, traduza como fala natural, sem completar com informações inventadas.

DIREÇÃO DE ESTILO:
- Use PT-BR natural, sem literalismo francês. Prefira "Você está bem?" a "Tu vais bem?", "Vamos!" a "Partamos!", quando o contexto for casual.
- Em cenas militares, use tom direto e profissional: "Copiado!", "Entendido!", "Afirmativo!", "Negativo!", "Fogo!", "Recuar!", "Alvo confirmado!".
- Em discursos políticos e cenas da família Zabi/Deikun, preserve solenidade: "independência", "soberania", "pátria", "sacrifício", "honra", "revolução", quando fizer sentido.
- Em cenas emocionais, priorize fala viva e simples. Não deixe a legenda rígida só para ficar literal.
- Não suavize insultos, ameaças ou tensão militar sem necessidade. Também não exagere palavrões se o francês original for moderado.
- Evite traduzir "vous" sempre como "senhor"; use "senhor/senhora" quando houver hierarquia, respeito formal ou contexto militar.

GLOSSÁRIO PRINCIPAL DE GUNDAM / UNIVERSAL CENTURY:
- Mobile Suit / Mobile Suits / MS -> Mobile Suit / Mobile Suits / MS
- Mobile Armor / MA -> Mobile Armor / MA
- Gundam -> Gundam
- Zaku / Zaku I / Zaku II -> Zaku / Zaku I / Zaku II
- Bugu -> Bugu
- Waff -> Waff
- Guntank -> Guntank
- Guncannon -> Guncannon
- Core Fighter -> Core Fighter
- Principauté de Zeon / Principality of Zeon -> Principado de Zeon
- République de Zeon / Republic of Zeon -> República de Zeon
- République autonome de Munzo -> República Autônoma de Munzo
- Fédération Terrestre / Earth Federation -> Federação Terrestre
- Forces de la Fédération Terrestre / Earth Federation Forces / EFF -> Forças da Federação Terrestre / EFF
- Armée de Zeon / Forces de Zeon -> Exército de Zeon / Forças de Zeon
- Zeon -> Zeon
- Fédération -> Federação
- Fédéraux / les Feds -> Federais
- Spacenoids / habitants de l'espace -> Spacenoids / habitantes do espaço
- Earthnoids / Terriens -> Earthnoids / terráqueos
- Universal Century / U.C. / UC / Siècle Universel -> Século Universal / U.C.
- One Year War / Guerre d'Un An -> Guerra de Um Ano
- Battle of Loum / Bataille de Loum -> Batalha de Loum
- Operation British / Opération British -> Operação British
- Colony Drop / chute de colonie -> Queda da Colônia
- Antarctic Treaty / Traité de l'Antarctique -> Tratado da Antártida
- Newtype / Newtypes -> Newtype / Newtypes
- Minovsky particles / particules Minovsky -> Partículas Minovsky
- Minovsky Physics -> Física Minovsky
- Mega Particle Cannon / canon à particules méga -> Canhão de Mega Partículas
- Beam Rifle -> Beam Rifle
- Beam Saber -> Beam Saber
- Heat Hawk -> Heat Hawk
- Bazooka -> bazuca
- Machine gun -> metralhadora
- Normal Suit -> Normal Suit
- Comms / communications / radio -> comunicações / rádio
- Launch / décollage -> lançamento / decolagem, conforme o contexto
- Sortie -> surtida, lançamento ou saída, conforme o contexto militar
- Stand by / standby -> em espera / a postos
- Roger / Copy that / Bien reçu -> Copiado! / Entendido!

PERSONAGENS E FAMÍLIAS:
- Char Aznable -> Char Aznable
- Casval Rem Deikun -> Casval Rem Deikun
- Édouard Mass / Edward Mass -> Édouard Mass
- Artesia Som Deikun -> Artesia Som Deikun
- Sayla Mass -> Sayla Mass
- Zeon Zum Deikun -> Zeon Zum Deikun
- Astraia Tor Deikun -> Astraia Tor Deikun
- Roselucia Deikun -> Roselucia Deikun
- Degwin Sodo Zabi -> Degwin Sodo Zabi
- Gihren Zabi -> Gihren Zabi
- Sasro Zabi -> Sasro Zabi
- Dozle Zabi -> Dozle Zabi
- Kycilia Zabi -> Kycilia Zabi
- Garma Zabi -> Garma Zabi
- Ramba Ral -> Ramba Ral
- Crowley Hamon -> Crowley Hamon
- Jimba Ral -> Jimba Ral
- Tachi O'Hara -> Tachi O'Hara
- Don Teabolo Mass -> Don Teabolo Mass
- Amuro Ray -> Amuro Ray
- Tem Ray -> Tem Ray
- Kamaria Ray -> Kamaria Ray
- Lalah Sune -> Lalah Sune
- Bright Noa -> Bright Noa
- Mirai Yashima -> Mirai Yashima
- Gaia -> Gaia
- Ortega -> Ortega
- Mash -> Mash
- Black Tri-Stars / Tri-Stars Noirs -> Black Tri-Stars
- Revil / Général Revil -> Revil / General Revil
- Família Zabi / famille Zabi -> família Zabi
- Família Deikun / famille Deikun -> família Deikun
- Comète Rouge / Red Comet -> Cometa Vermelho

LOCAIS, SIDES, BASES E EVENTOS:
- Terre -> Terra
- Lune -> Lua
- Side 3 -> Side 3
- Side 7 -> Side 7
- Munzo -> Munzo
- Zum City -> Zum City
- Loum -> Loum
- Side 5 -> Side 5
- Texas Colony / Colonie Texas -> Colônia Texas
- Island Iffish / Île Iffish -> Island Iffish
- Luna II -> Luna II
- Jaburo -> Jaburo
- Granada -> Granada
- Von Braun -> Von Braun
- Baikonur -> Baikonur
- Dakar -> Dakar
- Sydney / Sidney -> Sydney
- Earth Orbital Station -> Estação Orbital da Terra
- Colonie spatiale / colonie -> colônia espacial / colônia
- Colonie cylindrique -> colônia cilíndrica
- Zone de combat -> zona de combate
- Champ de bataille -> campo de batalha

NAVES, CLASSES E UNIDADES:
- Musai -> Musai
- Musai-class cruiser / croiseur de classe Musai -> cruzador classe Musai
- Salamis -> Salamis
- Salamis-class cruiser / croiseur de classe Salamis -> cruzador classe Salamis
- Magellan -> Magellan
- Magellan-class battleship / cuirassé de classe Magellan -> encouraçado classe Magellan
- Gwazine -> Gwazine
- Great Degwin -> Great Degwin
- Chivvay -> Chivvay
- Papua -> Papua
- Columbus -> Columbus
- White Base -> White Base
- Falmer -> Falmer
- 603rd Technical Evaluation Unit -> 603ª Unidade de Avaliação Técnica

PATENTES, CARGOS E TRATAMENTO MILITAR:
- Amiral -> Almirante
- Vice-amiral -> Vice-almirante
- Contre-amiral -> Contra-almirante
- Général -> General
- Colonel -> Coronel
- Lieutenant-colonel -> Tenente-coronel
- Major -> Major
- Commandant -> Comandante, ou Major se for patente; escolha pelo contexto
- Capitaine -> Capitão
- Lieutenant -> Tenente
- Sous-lieutenant -> Segundo-tenente
- Enseigne -> Alferes, quando for patente naval
- Sergent -> Sargento
- Caporal -> Cabo
- Soldat -> Soldado
- Cadet -> Cadete
- Officier -> Oficial
- Commandant de bord -> Comandante da nave
- Officier de pont -> Oficial de convés
- Officier d'artillerie -> Oficial de artilharia
- Chef de hangar -> Chefe de hangar
- Analyste du renseignement -> Analista de inteligência
- Technicien -> Técnico
- Scientifique / chercheur -> Cientista / pesquisador

TERMOS POLÍTICOS E DE LORE:
- Indépendance -> independência
- Autonomie -> autonomia
- Souveraineté -> soberania
- Coup d'État -> golpe de Estado
- Dictature -> ditadura
- Purge -> expurgo
- Assemblée nationale -> Assembleia Nacional
- Gouvernement fédéral -> governo federal
- Nationalisme -> nacionalismo
- Contolism / Contolisme -> Contolismo
- Deikunism / Deikunisme -> Deikunismo
- Révolution -> revolução
- Trahison -> traição
- Tyrannie -> tirania

CUIDADOS DE TRADUÇÃO FRANCÊS -> PT-BR:
- "Mon père" -> "meu pai", não "meu senhor".
- "Votre Excellence" -> "Vossa Excelência" em discurso formal; "senhor" se a legenda precisar ser curta.
- "Monsieur" -> "senhor" ou manter como tratamento natural pelo contexto.
- "Mademoiselle" -> "senhorita", mas use o nome se soar mais natural.
- "On y va" -> "Vamos" / "Vamos nessa", conforme o tom.
- "Ça suffit" -> "Já chega".
- "Dépêchez-vous" -> "Depressa!" / "Rápido!".
- "Feu!" -> "Fogo!".
- "À vos postes!" -> "A postos!".
- "En avant!" -> "Avançar!" / "Em frente!".
- "Repli!" -> "Recuar!".
- "Cible verrouillée" -> "Alvo travado".
- "Impact imminent" -> "Impacto iminente".
- "Lancement" -> "Lançamento" para nave/míssil; "decolagem" para aeronave; escolha pelo contexto.

ANTI-ERROS:
- Nunca traduza Char, Zaku, Gundam, Zeon, Deikun, Zabi, Ral, Newtype, Mobile Suit, Side, U.C. ou nomes de naves como palavras comuns.
- Não invente parentescos, títulos ou lore que não estejam na linha.
- Não misture termos de outras franquias, como Macross, Valkyrie, Fold, Protocultura ou Cavaleiros Aéreos.
- Não coloque notas entre parênteses explicando termos.
- Se o francês tiver uma palavra ambígua, escolha a tradução mais provável pelo contexto de Gundam e pela fala militar/política.

EXEMPLOS DE FORMATO:
[0] Char, vous êtes en retard.
[0] Char, você está atrasado.
[1] [T0]Bien reçu. Lancement du Zaku II!
[1] [T0]Entendido. Lançando o Zaku II!
[2] La Fédération Terrestre approche de Side 3\\NPréparez les Mobile Suits.
[2] A Federação Terrestre se aproxima de Side 3\\NPreparem os Mobile Suits.
""")


    MKVEXTRACT_PATHS = [
        r"C:\Program Files\MKVToolNix\mkvextract.exe",
        r"C:\Program Files (x86)\MKVToolNix\mkvextract.exe",
    ]
    MKVMERGE_PATHS = [
        r"C:\Program Files\MKVToolNix\mkvmerge.exe",
        r"C:\Program Files (x86)\MKVToolNix\mkvmerge.exe",
    ]

    def __init__(self, log: GerenciadorLogs):
        self.log   = log
        self.cache = {}
        self.modelo_ativo = "local-model"
        self.mkvextract = self._achar_mkvextract()
        self.mkvmerge = self._achar_mkvmerge()
        self.max_workers = 2  # Limite recomendado para RTX 5600 (8 GB VRAM) no LM Studio (seguro com contexto de 8000)
        
        self.caminho_cache = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "traducao_cache_fr.json"
        )
        self._carregar_cache()

        self.stats = {
            'mkv_total':          0,
            'extraidos':          0,
            'traduzidos':         0,
            'erros_extracao':     0,
            'erros_traducao':     0,
            'requisicoes':        0,
            'cache_hits':         0,
            'linhas_traduzidas':  0,
            'encodings_detectados': {},
        }

    # ── cache ─────────────────────────────────────────────────────────────────

    def _carregar_cache(self):
        if os.path.exists(self.caminho_cache):
            try:
                with open(self.caminho_cache, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                self.log.info(f"Cache em disco carregado: {len(self.cache)} traduções disponíveis.")
            except Exception as e:
                self.log.aviso(f"Erro ao carregar cache do disco, iniciando vazio: {e}")
                self.cache = {}
        else:
            self.cache = {}

    def _salvar_cache(self):
        try:
            with open(self.caminho_cache, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log.aviso(f"Erro ao salvar cache em disco: {e}")

    # ── infra ─────────────────────────────────────────────────────────────────

    def _achar_mkvextract(self):
        for caminho in self.MKVEXTRACT_PATHS:
            if os.path.exists(caminho):
                return caminho
        return shutil.which("mkvextract")

    def _achar_mkvmerge(self):
        for caminho in self.MKVMERGE_PATHS:
            if os.path.exists(caminho):
                return caminho
        return shutil.which("mkvmerge")

    def validar(self) -> bool:
        self.log.secao("VALIDAÇÃO DE INFRAESTRUTURA")

        # LM Studio
        self.log.debug(f"Testando LM Studio em {self.LM_URL}...")
        try:
            r = requests.get(f"{self.LM_URL}/v1/models", timeout=5)
            if r.status_code == 200:
                modelos = r.json().get('data', [])
                self.log.sucesso(f"LM Studio OK — {len(modelos)} modelo(s)")
                if modelos:
                    self.modelo_ativo = modelos[0].get('id', 'local-model')
                    self.log.info(f"Usando modelo: {self.modelo_ativo}")
            else:
                self.log.erro(f"LM Studio retornou status {r.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.log.erro("LM Studio não responde — verifique se está rodando na porta 1234")
            return False
        except Exception as e:
            self.log.erro(f"Erro ao contatar LM Studio: {e}")
            return False

        # mkvextract e mkvmerge
        self.log.debug("Verificando MKVToolNix...")
        if self.mkvextract and self.mkvmerge:
            self.log.sucesso(f"MKVToolNix OK: {self.mkvextract}")
        else:
            self.log.erro("mkvextract.exe ou mkvmerge.exe não encontrados")
            return False

        self.log.sucesso("✓ Infraestrutura validada!")
        return True

    # ── extração ──────────────────────────────────────────────────────────────

    def descobrir_track_id_ass(self, mkv_path: str) -> int:
        """Usa o mkvmerge para descobrir qual é o ID da faixa de texto ASS em francês."""
        try:
            cmd = [self.mkvmerge, "-J", mkv_path]
            res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=15)
            if res.returncode != 0:
                self.log.erro(f"mkvmerge retornou código {res.returncode}")
                return -1

            info = json.loads(res.stdout)
            faixas_ass = []
            for track in info.get("tracks", []):
                if track.get("type") == "subtitles":
                    props = track.get("properties", {})
                    codec_id = props.get("codec_id", "")
                    # Aceita SubStationAlpha ou ASS genérico
                    if "S_TEXT/ASS" in codec_id or "ASS" in track.get("codec", "").upper():
                        faixas_ass.append((track.get("id"), props.get("language", "und").lower()))

            if not faixas_ass:
                self.log.erro("Nenhuma faixa de legenda texto (.ass) encontrada no MKV.")
                return -1

            # Prioriza faixa em francês
            for track_id, idioma in faixas_ass:
                if idioma in ("fre", "fra", "fr"):
                    self.log.debug(f"Track ID francês detectado: {track_id} (idioma: {idioma})")
                    return track_id

            track_id, idioma = faixas_ass[0]
            self.log.aviso(f"Nenhuma faixa .ass em francês — usando track {track_id} (idioma: {idioma})")
            return track_id

        except Exception as e:
            self.log.erro(f"Falha ao identificar o Track ID: {e}")
            return -1

    def extrair_legenda(self, mkv_path: str, track_id: int):
        """Extrai a faixa de legenda do MKV."""
        nome = os.path.basename(mkv_path)
        base = os.path.splitext(nome)[0]
        ass  = os.path.join(os.path.dirname(mkv_path), f"{base}_extracted.ass")

        try:
            cmd = [self.mkvextract, mkv_path, "tracks", f"{track_id}:{ass}"]
            self.log.debug(f"mkvextract track={track_id} → {os.path.basename(ass)}")
            res = subprocess.run(cmd, capture_output=True, timeout=60, text=True, encoding='utf-8', errors='replace')

            if res.returncode != 0:
                self.log.erro(f"mkvextract retornou código {res.returncode}")
                self.stats['erros_extracao'] += 1
                return None

            if not os.path.exists(ass):
                self.log.erro("Arquivo .ass não foi criado")
                self.stats['erros_extracao'] += 1
                return None

            self.log.sucesso(f"Extraído: {os.path.getsize(ass):,} bytes")
            self.stats['extraidos'] += 1
            return ass

        except Exception as e:
            self.log.erro(f"Exceção na extração: {e}")
            self.stats['erros_extracao'] += 1
            return None

    # ── tags ASS ──────────────────────────────────────────────────────────────

    def mascarar_tags(self, texto_bruto: str):
        """Mapeia as tags ASS originais para marcadores temporários [T0], [T1], etc."""
        tags = re.findall(r'\{[^}]+\}', texto_bruto)
        texto_limpo = texto_bruto
        for idx_tag, tag in enumerate(tags):
            texto_limpo = texto_limpo.replace(tag, f"[T{idx_tag}]", 1)
        return texto_limpo, tags

    def restaurar_tags(self, texto_traduzido: str, tags: list):
        """Restaura as tags ASS originais nos marcadores de destino."""
        trad = texto_traduzido
        for idx_tag, tag in enumerate(tags):
            marcador = f"[T{idx_tag}]"
            if marcador in trad:
                trad = trad.replace(marcador, tag, 1)
            else:
                # Fallback tolerante a pequenas alterações de espaçamento ou case feitas pelo LLM
                trad = re.sub(rf'\[?[Tt]\s*{idx_tag}\]?', tag, trad, count=1)
        return trad

    def limpar_saida_traducao(self, texto: str) -> str:
        """Corrige deslizes comuns do LLM sem alterar o sentido da tradução."""
        texto = texto.strip()
        texto = re.sub(r"^\s*[-–•]\s*", "", texto)
        texto = re.sub(r"\[\s*[Tt]\s*(\d+)\s*\]", r"[T\1]", texto)
        texto = re.sub(r"\\\s*([Nnh])", r"\\\1", texto)
        texto = texto.replace("/N", r"\N").replace("/n", r"\n")
        texto = texto.replace("\r\n", "\n").replace("\r", "\n")
        texto = re.sub(r"\s*\n+\s*", r"\\N", texto)
        return texto

    # ── tradução ──────────────────────────────────────────────────────────────

    def _traduzir_lote(self, linhas: list, tentativa=1) -> dict:
        """Envia lote ao LM Studio e retorna o mapa de traduções indexadas."""
        payload = "\n".join(f"[{i}] {t}" for i, t in enumerate(linhas))

        corpo = {
            "model": self.modelo_ativo,
            "messages": [
                {"role": "system", "content": self.PROMPT_SISTEMA},
                {"role": "user",   "content": f"Traduza do francês para PT-BR mantendo exatamente os índices, marcadores [Tn] e escapes de legenda. Responda somente com as linhas traduzidas:\n{payload}"},
            ],
            "temperature": 0.2,
            "top_p": 0.9,
            "max_tokens":  3000,
        }

        self.stats['requisicoes'] += 1

        try:
            r = requests.post(
                self.API_URL,
                json=corpo,
                headers={"Content-Type": "application/json"},
                timeout=120,
            )
        except Exception as e:
            self.log.erro(f"Erro de conexão/timeout no LM Studio: {e}")
            if tentativa < 2:
                time.sleep(2 * tentativa)
                return self._traduzir_lote(linhas, tentativa + 1)
            raise RuntimeError("LM Studio sem conexão estável")

        if r.status_code != 200:
            self.log.erro(f"Status HTTP {r.status_code}")
            if tentativa < 2:
                time.sleep(2 * tentativa)
                return self._traduzir_lote(linhas, tentativa + 1)
            raise RuntimeError(f"Status HTTP {r.status_code}")

        bruto = r.json()['choices'][0]['message']['content'].strip()

        # Parse dos índices
        traduzidas = {}
        for idx_str, texto in re.findall(r"\[(\d+)\]\s*(.*?)(?=\[\d+\]|$)", bruto, re.DOTALL):
            idx = int(idx_str)
            if idx < 0 or idx >= len(linhas):
                continue
            texto_limpo = self.limpar_saida_traducao(texto)
            if texto_limpo:
                traduzidas[idx] = texto_limpo

        # Fallback simples se o regex falhar por completo e o número de linhas bater
        if not traduzidas:
            linhas_bruto = bruto.splitlines()
            for i, linha in enumerate(linhas_bruto[:len(linhas)]):
                linha_limpa = re.sub(r"^\[?\d+\]?[.)\s-]*", "", linha.strip()).strip()
                linha_limpa = self.limpar_saida_traducao(linha_limpa)
                if linha_limpa:
                    traduzidas[i] = linha_limpa

        # Limpeza contra conversas adicionais no final
        if traduzidas:
            ultimo_idx = max(traduzidas.keys())
            ultimo_texto = traduzidas[ultimo_idx]
            linhas_ultimo = ultimo_texto.split('\n')
            if len(linhas_ultimo) > 1:
                linhas_limpas_ultimo = []
                for l in linhas_ultimo:
                    if re.search(r"^(espero|aqui está|aqui esta|se precisar|traduzido|espero que|bonne chance|voilà)", l.strip(), re.IGNORECASE):
                        break
                    linhas_limpas_ultimo.append(l)
                traduzidas[ultimo_idx] = self.limpar_saida_traducao("\n".join(linhas_limpas_ultimo))

        if not traduzidas:
            raise RuntimeError("Impossível extrair traduções da resposta do LLM")

        return traduzidas

    def traduzir_lote_resiliente(self, lote_textos: list) -> dict:
        """
        Tenta traduzir o lote de textos. Se falhar, faz o fallback traduzindo 
        linha por linha para garantir resiliência máxima.
        """
        try:
            resultado = self._traduzir_lote(lote_textos)
            if len(resultado) == len(lote_textos):
                return resultado
            raise RuntimeError(f"Resultado incompleto: {len(resultado)}/{len(lote_textos)} linhas traduzidas")
        except Exception as e:
            self.log.aviso(f"Falha na tradução em lote ({e}). Iniciando fallback resiliente linha a linha...")
            
            resultado_final = {}
            for idx, texto in enumerate(lote_textos):
                sucesso_linha = False
                for tentativa in range(1, 4):
                    try:
                        res_indiv = self._traduzir_lote([texto])
                        if 0 in res_indiv:
                            resultado_final[idx] = res_indiv[0]
                            sucesso_linha = True
                            break
                    except Exception:
                        time.sleep(1)
                
                if not sucesso_linha:
                    self.log.erro(f"Falha definitiva ao traduzir linha: '{texto[:40]}...'")
                    resultado_final[idx] = f"[ERRO_TRADUCAO: {texto}]"
            
            return resultado_final

    # ── processamento do .ass ─────────────────────────────────────────────────

    def processar_legenda(self, ass_path: str, saida_path: str) -> bool:
        """Lê o .ass, traduz os diálogos e salva o resultado com multithreading."""
        try:
            linhas, enc_usado = ler_arquivo_com_encoding(ass_path, self.log)
            self.stats['encodings_detectados'][enc_usado] = \
                self.stats['encodings_detectados'].get(enc_usado, 0) + 1

            self.log.debug(f"Arquivo lido: {len(linhas)} linhas (encoding: {enc_usado})")

            pat = re.compile(
                r"^(Dialogue:\s*[^,]*(?:,[^,]*){8},)(.*)$"
            )

            # Estruturas para rastreamento de diálogos
            indices_arquivo = []
            textos_brutos = []
            textos_mascarados = []
            lista_tags = []

            puladas_binario = 0

            for i, linha in enumerate(linhas):
                linha_limpa = linha.strip()

                if len(linha_limpa) > 2000:
                    puladas_binario += 1
                    continue

                m = pat.match(linha_limpa)
                if not m:
                    continue

                prefixo = m.group(1)
                txt = m.group(2).strip()

                # Ignora linhas vazias ou sem texto real
                txt_sem_tags = re.sub(r'\{.*?\}', '', txt).strip()
                if not txt_sem_tags or len(txt_sem_tags) < 1:
                    continue

                # Ignora lixo binário
                if any(tag in txt for tag in [r'\font', r'\image', '0x', '\x00']):
                    puladas_binario += 1
                    continue

                # Mascara tags ASS
                texto_masc, tags = self.mascarar_tags(txt)

                indices_arquivo.append(i)
                textos_brutos.append(txt)
                textos_mascarados.append(texto_masc)
                lista_tags.append(tags)

            self.log.debug(f"Diálogos identificados: {len(textos_brutos)} (Lixo binário pulado: {puladas_binario})")

            if not textos_brutos:
                self.log.aviso("Nenhum diálogo qualificado encontrado para tradução")
                return False

            # Verificação contra Cache e preparação dos textos a traduzir
            mapa_dialogos_finais = [None] * len(textos_brutos)
            indices_para_traduzir = []
            textos_para_traduzir = []

            for idx_dialogo, texto_masc in enumerate(textos_mascarados):
                if texto_masc in self.cache:
                    # Hit de cache!
                    self.stats['cache_hits'] += 1
                    trad_masc = self.cache[texto_masc]
                    trad_final = self.restaurar_tags(trad_masc, lista_tags[idx_dialogo])
                    mapa_dialogos_finais[idx_dialogo] = trad_final
                else:
                    # Miss de cache!
                    indices_para_traduzir.append(idx_dialogo)
                    textos_para_traduzir.append(texto_masc)

            self.log.info(f"Cache Hits: {self.stats['cache_hits']} | Misses (A traduzir): {len(textos_para_traduzir)}")

            # Se existirem textos a traduzir, realiza chamadas concorrentes
            if textos_para_traduzir:
                batch_size = 8
                lotes = []
                for i in range(0, len(textos_para_traduzir), batch_size):
                    lotes.append(textos_para_traduzir[i:i+batch_size])

                self.log.debug(f"Processando {len(lotes)} lotes concorrentes (Max Threads: {self.max_workers})...")
                
                from concurrent.futures import ThreadPoolExecutor, as_completed
                
                mapa_futuros = {}
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    for idx_lote, lote in enumerate(lotes):
                        f = executor.submit(self.traduzir_lote_resiliente, lote)
                        mapa_futuros[f] = (idx_lote, lote)

                    with tqdm(total=len(lotes), desc="  Traduzindo", unit="lote", leave=False) as pbar:
                        for futuro in as_completed(mapa_futuros):
                            idx_lote, lote = mapa_futuros[futuro]
                            try:
                                resultado_lote = futuro.result()
                                offset_inicial = idx_lote * batch_size
                                for k, v in resultado_lote.items():
                                    idx_global_para_traduzir = offset_inicial + k
                                    if idx_global_para_traduzir < len(textos_para_traduzir):
                                        idx_dialogo = indices_para_traduzir[idx_global_para_traduzir]
                                        original_masc = textos_para_traduzir[idx_global_para_traduzir]
                                        
                                        # Salva no cache apenas se não for marcador de erro
                                        if "[ERRO_TRADUCAO" not in v:
                                            self.cache[original_masc] = v
                                            self.stats['linhas_traduzidas'] += 1
                                        
                                        trad_final = self.restaurar_tags(v, lista_tags[idx_dialogo])
                                        mapa_dialogos_finais[idx_dialogo] = trad_final
                            except Exception as exc:
                                self.log.erro(f"Erro ao processar lote {idx_lote}: {exc}")
                            pbar.update(1)

                # Salva o cache em disco após processar cada arquivo com sucesso
                self._salvar_cache()

            # Reconstrói as linhas do arquivo original
            for idx_dialogo, pos_arquivo in enumerate(indices_arquivo):
                traduzido = mapa_dialogos_finais[idx_dialogo]
                if traduzido is not None:
                    m = pat.match(linhas[pos_arquivo].strip())
                    if m:
                        linhas[pos_arquivo] = f"{m.group(1)}{traduzido}\n"

            # Salva o arquivo final
            with open(saida_path, 'w', encoding='utf-8') as f:
                f.writelines(linhas)

            self.log.sucesso(f"Salvo: {os.path.basename(saida_path)}")
            self.stats['traduzidos'] += 1
            return True

        except Exception as e:
            self.log.erro(f"Processamento falhou: {e}")
            self.log.traceback_completo("processar_legenda()")
            self.stats['erros_traducao'] += 1
            return False


# ============================================================================
# ENTRY POINT
# ============================================================================

def formatar_tempo(segundos):
    """Converte segundos em formato de string legível (Xm Ys)."""
    m, s = divmod(int(segundos), 60)
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"


def main():
    log = GerenciadorLogs()

    try:
        log.secao("PIPELINE INDUSTRIAL UNIFICADO — VERSÃO FRANCÊS (FR -> PT-BR)")

        pipe = Pipeline(log)

        if not pipe.validar():
            log.erro("Validação falhou — abortando")
            return

        # ── inputs ────────────────────────────────────────────────────────────
        log.secao("INPUTS")

        pasta = input(f"{Fore.CYAN}Pasta com os .mkv: {Style.RESET_ALL}").strip('" ')
        log.info(f"Pasta: {pasta}")

        if not os.path.isdir(pasta):
            log.erro(f"Pasta não existe: {pasta}")
            return

        mkv_files = sorted(f for f in os.listdir(pasta) if f.lower().endswith('.mkv'))
        log.info(f"Encontrados {len(mkv_files)} arquivo(s) .mkv")
        if not mkv_files:
            log.erro("Nenhum .mkv encontrado")
            return

        pasta_saida = os.path.join(pasta, "traducao")
        os.makedirs(pasta_saida, exist_ok=True)
        log.info(f"Saída: {pasta_saida}")

        log.salvar_config(pipe.LM_URL, pasta, "Automático (mkvmerge)", pasta_saida)

        # ── temporizador de precisão inicial ─────────────────────────────────
        tempo_inicio_global = time.time()

        # ── processamento ─────────────────────────────────────────────────────
        log.secao("PROCESSAMENTO")
        pipe.stats['mkv_total'] = len(mkv_files)

        for idx, nome_mkv in enumerate(mkv_files, 1):
            tempo_inicio_arquivo = time.time()
            log.info(f"[{idx}/{len(mkv_files)}] {nome_mkv}")

            mkv_path = os.path.join(pasta, nome_mkv)

            # 0. Descobrir Track ID
            track_id = pipe.descobrir_track_id_ass(mkv_path)
            if track_id == -1:
                log.erro("Pulando episódio por não encontrar track .ass válido")
                continue

            # 1. Extração
            ass_temp = pipe.extrair_legenda(mkv_path, track_id)
            if not ass_temp:
                log.erro("Falha na extração — pulando episódio")
                continue

            # 2. Tradução
            nome_base = os.path.splitext(nome_mkv)[0]
            ass_final = os.path.join(pasta_saida, f"{nome_base}_PTBR.ass")

            if pipe.processar_legenda(ass_temp, ass_final):
                tempo_fim_arquivo = time.time()
                decorrido_arquivo = tempo_fim_arquivo - tempo_inicio_arquivo
                decorrido_total_acumulado = tempo_fim_arquivo - tempo_inicio_global

                txt_tempo_arq = formatar_tempo(decorrido_arquivo)
                txt_tempo_total = formatar_tempo(decorrido_total_acumulado)

                log.sucesso(
                    f"✓ Episódio concluído com sucesso!"
                    f" [Tempo do arquivo: {Fore.YELLOW}{txt_tempo_arq}{Fore.GREEN}]"
                    f" [Tempo decorrido acumulado: {Fore.CYAN}{txt_tempo_total}{Fore.GREEN}]"
                )
            else:
                log.erro("✗ Falha na tradução")

            # 3. Limpeza
            try:
                os.remove(ass_temp)
                log.debug("Arquivo temporário removido")
            except Exception as e:
                log.aviso(f"Não conseguiu remover temporário: {e}")

        # ── temporizador final ───────────────────────────────────────────────
        tempo_total = time.time() - tempo_inicio_global
        tempo_total_fmt = formatar_tempo(tempo_total)

        # ── relatório final ───────────────────────────────────────────────────
        log.secao("RELATÓRIO FINAL")
        pipe.stats['tempo_total_segundos'] = tempo_total
        log.salvar_stats(pipe.stats)
        log.relatorio_final(pipe.stats, pasta_saida, tempo_total_fmt)

    except KeyboardInterrupt:
        log.aviso("Pipeline interrompido pelo usuário (Ctrl+C)")
    except Exception as e:
        log.erro(f"Erro crítico no pipeline: {e}")
        log.traceback_completo("main()")
    finally:
        log.fechar()


if __name__ == "__main__":
    main()
