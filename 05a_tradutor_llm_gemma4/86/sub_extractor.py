#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PIPELINE INDUSTRIAL UNIFICADO - VERSÃO 86 (EN -> PT-BR)
Extrai .ass dos .mkv → Detecta Encoding → Traduz do Inglês via LM Studio → Salva

Recursos Industriais:
  - Cache persistente em disco (traducao_cache_86.json)
  - Mascaramento avançado de tags ASS [T0], [T1]... para evitar corrupções
  - Concorrência multithread controlada (ThreadPoolExecutor)
  - Fallback resiliente linha a linha em caso de falha de lote
  - Detecção automática de faixas ASS priorizando inglês
  - Temporizadores de precisão por arquivo e execução total
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

# Força codificação UTF-8 na saída padrão do Windows para suportar ícones e caracteres especiais
if sys.version_info >= (3, 7):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

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
            os.path.join(self.pasta_logs, f"pipeline_86_{self.ts}.txt"),
            'w', encoding='utf-8'
        )
        self.f_erros = open(
            os.path.join(self.pasta_logs, f"erros_86_{self.ts}.txt"),
            'w', encoding='utf-8'
        )
        self.caminho_stats  = os.path.join(self.pasta_logs, f"stats_86_{self.ts}.json")
        self.caminho_config = os.path.join(self.pasta_logs, f"config_86_{self.ts}.txt")

        header = (
            f"\n{'='*80}\n"
            f"PIPELINE DE TRADUÇÃO DE 86 (EN -> PT-BR) - LOG DE AUDITORIA\n"
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

    def salvar_config(self, lm_url, pasta_entrada, track_id, pasta_saida, model_name):
        conteudo = (
            f"\n{'='*80}\nCONFIGURAÇÃO DA EXECUÇÃO\n{'='*80}\n\n"
            f"Data/Hora      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"LM Studio URL  : {lm_url}\n"
            f"Modelo         : {model_name}\n\n"
            f"Pasta entrada  : {pasta_entrada}\n"
            f"Track ID       : {track_id}\n"
            f"Pasta saída    : {pasta_saida}\n\n"
            f"Logs:\n"
            f"  Pipeline : pipeline_86_{self.ts}.txt\n"
            f"  Erros    : erros_86_{self.ts}.txt\n"
            f"  Stats    : stats_86_{self.ts}.json\n"
            f"  Config   : config_86_{self.ts}.txt\n"
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
            f"  [DIR]  {self.pasta_logs}\n"
            f"  [FILE]  pipeline_86_{self.ts}.txt\n"
            f"  [AVISO]   erros_86_{self.ts}.txt\n"
            f"  [STATS]  stats_86_{self.ts}.json\n"
            f"  [CONFIG]   config_86_{self.ts}.txt\n"
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
        print(f"{Fore.GREEN}[OK] LOGS SALVOS EM: {self.pasta_logs}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*80}{Style.RESET_ALL}\n")
        for nome in [
            f"pipeline_86_{self.ts}.txt",
            f"erros_86_{self.ts}.txt",
            f"stats_86_{self.ts}.json",
            f"config_86_{self.ts}.txt",
        ]:
            print(f"  {nome}")
        print()


# ============================================================================
# FALLBACK CHAIN DE ENCODING
# ============================================================================

ENCODINGS_FALLBACK = [
    'utf-8',
    'utf-8-sig',
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
    Orquestrador principal da tradução de 86 (Inglês -> Português).
    """

    LM_URL  = "http://127.0.0.1:1234"
    API_URL = f"{LM_URL}/v1/chat/completions"

    PROMPT_SISTEMA = (
        "Você é um tradutor especialista em localização de animes, ficção científica, mechas e drama militar.\n"
        "Sua tarefa é traduzir as linhas de legenda enviadas do Inglês para o Português do Brasil (PT-BR) de forma extremamente natural, mantendo a seriedade e o tom militar/dramático do contexto original.\n\n"
        "REGRAS DE FORMATAÇÃO E ESTRUTURA:\n"
        "1. Mantenha os índices intactos: se receber '[0] texto', responda exatamente '[0] tradução'. Nunca omita os colchetes e números.\n"
        "2. NUNCA remova ou altere os marcadores de tag como '[T0]', '[T1]', '[T2]'. Eles representam formatações de legenda originais e devem aparecer exatamente na mesma posição e formato no texto traduzido.\n"
        "3. Preserve a tag de quebra de linha '\\N' (barra invertida N) exatamente onde ela aparece, sem alterá-la para '/N' ou para quebras de linha reais.\n"
        "4. Responda APENAS com as linhas traduzidas numeradas. Não inclua notas explicativas, introduções ou saudações.\n\n"
        "GLOSSÁRIO OBRIGATÓRIO DE 86 (EIGHTY-SIX) (EN -> PT-BR):\n"
        "  - 'Eighty-Six' / '86' -> 'Eighty-Six' / '86' (manter como no original)\n"
        "  - 'Eighty-Sixers' -> 'Eighty-Sixers'\n"
        "  - 'Handler' / 'Handlers' -> 'Handler' / 'Handlers'\n"
        "  - 'Handler One' -> 'Handler One'\n"
        "  - 'Processor' / 'Processors' -> 'Processador' / 'Processadores'\n"
        "  - 'Legion' -> 'Legião' (as máquinas inimigas)\n"
        "  - 'Shepherd' / 'Shepherds' -> 'Pastor' / 'Pastores' (unidades Legion com consciência)\n"
        "  - 'Sheepdog' / 'Sheepdogs' -> 'Sheepdog' / 'Sheepdogs'\n"
        "  - 'Black Sheep' -> 'Ovelha Negra' / 'Ovelhas Negras'\n"
        "  - 'Para-RAID' -> 'Para-RAID'\n"
        "  - 'Resonance' / 'Synchronize' -> 'Ressonância' / 'Sincronizar'\n"
        "  - 'Alba' / 'Albas' -> 'Alba' / 'Albas' (raça dominante)\n"
        "  - 'Colorata' / 'Coloratas' -> 'Colorata' / 'Coloratas' (raças oprimidas)\n"
        "  - 'Gran Mur' -> 'Gran Mur'\n"
        "  - 'Juggernaut' / 'Juggernauts' -> 'Juggernaut' / 'Juggernauts'\n"
        "  - 'Reginleif' / 'Reginleifs' -> 'Reginleif' / 'Reginleifs'\n"
        "  - 'Scavenger' / 'Scavengers' -> 'Scavenger' / 'Scavengers' (robôs coletores)\n"
        "  - 'Republic of San Magnolia' -> 'República de San Magnolia'\n"
        "  - 'Federal Republic of Giad' -> 'República Federal de Giad'\n"
        "  - 'Giad Empire' -> 'Império de Giad'\n"
        "  - 'Undertaker' -> 'Undertaker' (codinome do Shin)\n"
        "  - 'Snow Witch' -> 'Snow Witch' (codinome da Anju)\n"
        "  - 'Wehrwolf' -> 'Wehrwolf' (codinome do Raiden)\n"
        "  - 'Laughing Fox' -> 'Laughing Fox' (codinome do Theo)\n"
        "  - 'Gunslinger' -> 'Gunslinger' (codinome da Kurena)\n"
        "  - 'Fido' -> 'Fido'\n"
        "  - 'Sirins' -> 'Sirins' / 'Sirins'\n"
        "  - 'Roger' / 'Copy that' -> 'Copiado!' / 'Entendido!'\n"
    )

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
        self.max_workers = 2  # Concorrência segura para GPU/VRAM no LM Studio
        
        self.caminho_cache = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "traducao_cache_86.json"
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

        self.log.sucesso("[OK] Infraestrutura validada!")
        return True

    # ── extração ──────────────────────────────────────────────────────────────

    def descobrir_track_id_ass(self, mkv_path: str) -> int:
        """Usa o mkvmerge para descobrir qual é o ID da faixa de texto ASS em inglês."""
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
                    if "S_TEXT/ASS" in codec_id or "ASS" in track.get("codec", "").upper():
                        faixas_ass.append((track.get("id"), props.get("language", "und").lower()))

            if not faixas_ass:
                self.log.erro("Nenhuma faixa de legenda texto (.ass) encontrada no MKV.")
                return -1

            # Prioriza faixa em inglês
            for track_id, idioma in faixas_ass:
                if idioma in ("eng", "en"):
                    self.log.debug(f"Track ID inglês detectado: {track_id} (idioma: {idioma})")
                    return track_id

            track_id, idioma = faixas_ass[0]
            self.log.aviso(f"Nenhuma faixa .ass em inglês — usando track {track_id} (idioma: {idioma})")
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
        """Mapeia as tags ASS originais para marcadores temporários [T0], [T1], etc. Protege quebras de linha \\N."""
        # Trata quebras de linha \N como tags normais transformando-as em {\N} temporariamente
        texto_preparado = re.sub(r'\\N', '{\\\\N}', texto_bruto, flags=re.IGNORECASE)
        
        tags = re.findall(r'\{[^}]+\}', texto_preparado)
        texto_limpo = texto_preparado
        for idx_tag, tag in enumerate(tags):
            texto_limpo = texto_limpo.replace(tag, f"[T{idx_tag}]", 1)
        return texto_limpo, tags

    def restaurar_tags(self, texto_traduzido: str, tags: list):
        """Restaura as tags ASS originais nos marcadores de destino e reverte \\N."""
        trad = texto_traduzido
        for idx_tag, tag in enumerate(tags):
            marcador = f"[T{idx_tag}]"
            if marcador in trad:
                trad = trad.replace(marcador, tag, 1)
            else:
                trad = re.sub(rf'\[?[Tt]\s*{idx_tag}\]?', lambda m: tag, trad, count=1)
        
        # Converte as tags {\N} restauradas de volta para \N literal
        trad = re.sub(r'\{[\\/]N\}', r'\\N', trad, flags=re.IGNORECASE)
        return trad

    # ── tradução ──────────────────────────────────────────────────────────────

    def _traduzir_lote(self, linhas: list, tentativa=1) -> dict:
        """Envia lote ao LM Studio e retorna o mapa de traduções indexadas."""
        payload = "\n".join(f"[{i}] {t}" for i, t in enumerate(linhas))

        corpo = {
            "model": self.modelo_ativo,
            "messages": [
                {"role": "system", "content": self.PROMPT_SISTEMA},
                {"role": "user",   "content": f"Traduza:\n{payload}"},
            ],
            "temperature": 0.1,
            "max_tokens":  2000,
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
            texto_limpo = texto.strip()
            if texto_limpo:
                traduzidas[int(idx_str)] = texto_limpo

        # Fallback simples se o regex falhar por completo e o número de linhas bater
        if not traduzidas:
            linhas_bruto = bruto.splitlines()
            for i, linha in enumerate(linhas_bruto[:len(linhas)]):
                linha_limpa = re.sub(r"^\[?\d+\]?[.)\s-]*", "", linha.strip()).strip()
                if linha_limpa:
                    traduzidas[i] = linha_limpa

        # Limpeza contra conversas adicionais no final
        if traduzidas:
            ultimo_idx = max(traduzidas.keys())
            ultimo_texto = traduzidas[ultimo_idx]
            linhas_ultimo = ultimo_texto.split('\n')
            if len(linhas_ultimo) > 1:
                linhas_limpas_ultimo = []
                for l in os.linesep.split(ultimo_texto) if hasattr(os, 'linesep') else ultimo_texto.splitlines():
                    l_strip = l.strip()
                    if re.search(r"^(espero|aqui está|aqui esta|se precisar|traduzido|espero que|bonne chance|voilà|here is|hope this)", l_strip, re.IGNORECASE):
                        break
                    linhas_limpas_ultimo.append(l)
                traduzidas[ultimo_idx] = "\n".join(linhas_limpas_ultimo).strip()

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
        log.secao("PIPELINE INDUSTRIAL UNIFICADO — VERSÃO 86 (EN -> PT-BR)")

        pipe = Pipeline(log)

        if not pipe.validar():
            log.erro("Validação falhou — abortando")
            return

        # ── inputs ────────────────────────────────────────────────────────────
        log.secao("INPUTS")

        pasta = input(f"{Fore.CYAN}Pasta com os arquivos (.ass ou .mkv): {Style.RESET_ALL}").strip('" ')
        log.info(f"Pasta: {pasta}")

        if not os.path.isdir(pasta):
            log.erro(f"Pasta não existe: {pasta}")
            return

        # Varre os arquivos na pasta
        arquivos_ass = sorted(f for f in os.listdir(pasta) if f.lower().endswith('.ass') and not f.lower().endswith('_ptbr.ass'))
        arquivos_mkv = sorted(f for f in os.listdir(pasta) if f.lower().endswith('.mkv'))

        modo = None
        arquivos_alvo = []

        if arquivos_ass:
            modo = "ass_direct"
            arquivos_alvo = arquivos_ass
            log.info(f"Modo: Tradução Direta de Legendas (.ass) — {len(arquivos_alvo)} arquivos localizados")
        elif arquivos_mkv:
            modo = "mkv_extract"
            arquivos_alvo = arquivos_mkv
            log.info(f"Modo: Extração de Legendas do Vídeo (.mkv) — {len(arquivos_alvo)} arquivos localizados")
        else:
            log.erro("Nenhum arquivo .ass ou .mkv encontrado na pasta especificada")
            return

        pasta_saida = os.path.join(pasta, "traducao")
        os.makedirs(pasta_saida, exist_ok=True)
        log.info(f"Saída: {pasta_saida}")

        log.salvar_config(pipe.LM_URL, pasta, "ASS Direto" if modo == "ass_direct" else "Automático (mkvmerge)", pasta_saida, pipe.modelo_ativo)

        # ── temporizador de precisão inicial ─────────────────────────────────
        tempo_inicio_global = time.time()

        # ── processamento ─────────────────────────────────────────────────────
        log.secao("PROCESSAMENTO")
        pipe.stats['mkv_total'] = len(arquivos_alvo)

        for idx, nome_arq in enumerate(arquivos_alvo, 1):
            tempo_inicio_arquivo = time.time()
            log.info(f"[{idx}/{len(arquivos_alvo)}] {nome_arq}")

            caminho_in = os.path.join(pasta, nome_arq)
            nome_base = os.path.splitext(nome_arq)[0]

            if modo == "ass_direct":
                # Remove o sufixo _ENG ou _eng para a legenda traduzida
                nome_saida = nome_base
                if nome_saida.lower().endswith("_eng"):
                    nome_saida = nome_saida[:-4]
                ass_final = os.path.join(pasta_saida, f"{nome_saida}_PTBR.ass")
                
                caminho_ass_in = caminho_in
            else:
                # 0. Descobrir Track ID
                track_id = pipe.descobrir_track_id_ass(caminho_in)
                if track_id == -1:
                    log.erro("Pulando episódio por não encontrar track .ass válido")
                    continue

                # 1. Extração
                ass_temp = pipe.extrair_legenda(caminho_in, track_id)
                if not ass_temp:
                    log.erro("Falha na extração — pulando episódio")
                    continue

                ass_final = os.path.join(pasta_saida, f"{nome_base}_PTBR.ass")
                caminho_ass_in = ass_temp

            # 2. Tradução
            sucesso_processamento = pipe.processar_legenda(caminho_ass_in, ass_final)

            # 3. Limpeza (se for extração do mkv, remove o arquivo temporário)
            if modo == "mkv_extract":
                try:
                    os.remove(caminho_ass_in)
                    log.debug("Arquivo temporário removido")
                except Exception as e:
                    log.aviso(f"Não conseguiu remover temporário: {e}")

            if sucesso_processamento:
                tempo_fim_arquivo = time.time()
                decorrido_arquivo = tempo_fim_arquivo - tempo_inicio_arquivo
                decorrido_total_acumulado = tempo_fim_arquivo - tempo_inicio_global

                txt_tempo_arq = formatar_tempo(decorrido_arquivo)
                txt_tempo_total = formatar_tempo(decorrido_total_acumulado)

                log.sucesso(
                    f"[OK] Episódio concluído com sucesso!"
                    f" [Tempo do arquivo: {Fore.YELLOW}{txt_tempo_arq}{Fore.GREEN}]"
                    f" [Tempo decorrido acumulado: {Fore.CYAN}{txt_tempo_total}{Fore.GREEN}]"
                )
            else:
                log.erro("[ERRO] Falha na tradução")

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