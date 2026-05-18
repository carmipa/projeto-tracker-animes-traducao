#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PIPELINE INDUSTRIAL UNIFICADO - VERSÃO FINAL DE PRODUÇÃO
Extrai .ass dos .mkv → Detecta Encoding → Traduz via LM Studio → Salva

Sistema de Logs Auditável:
  logs/pipeline_YYYY-MM-DD_HH-MM-SS.txt  → Log completo
  logs/erros_YYYY-MM-DD_HH-MM-SS.txt     → Apenas erros + tracebacks
  logs/stats_YYYY-MM-DD_HH-MM-SS.json    → Estatísticas estruturadas
  logs/config_YYYY-MM-DD_HH-MM-SS.txt    → Configuração da execução

Correção de Encoding:
  Fallback chain: utf-8 → utf-8-sig → cp1252 → latin-1 → iso-8859-1 → bypass

Author: Paulo + Claude
Data: Maio 2026
Status: PRODUCTION FINAL
"""

import os
import sys
import re
import json
import time
import subprocess
import requests
import traceback
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
            os.path.join(self.pasta_logs, f"pipeline_{self.ts}.txt"),
            'w', encoding='utf-8'
        )
        self.f_erros = open(
            os.path.join(self.pasta_logs, f"erros_{self.ts}.txt"),
            'w', encoding='utf-8'
        )
        self.caminho_stats  = os.path.join(self.pasta_logs, f"stats_{self.ts}.json")
        self.caminho_config = os.path.join(self.pasta_logs, f"config_{self.ts}.txt")

        header = (
            f"\n{'='*80}\n"
            f"PIPELINE INDUSTRIAL UNIFICADO - LOG DE AUDITORIA\n"
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
            f"Hardware       : AMD RX 7800 XT 16 GB\n\n"
            f"Pasta entrada  : {pasta_entrada}\n"
            f"Track ID       : {track_id}\n"
            f"Pasta saída    : {pasta_saida}\n\n"
            f"Logs:\n"
            f"  Pipeline : pipeline_{self.ts}.txt\n"
            f"  Erros    : erros_{self.ts}.txt\n"
            f"  Stats    : stats_{self.ts}.json\n"
            f"  Config   : config_{self.ts}.txt\n"
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

    def relatorio_final(self, stats: dict, pasta_saida: str):
        corpo = (
            f"\n{'='*80}\nRELATÓRIO FINAL\n{'='*80}\n\n"
            f"Arquivos .mkv    : {stats.get('mkv_total', 0)}\n"
            f"Extraídos        : {stats.get('extraidos', 0)}\n"
            f"Traduzidos       : {stats.get('traduzidos', 0)}\n"
            f"Erros extração   : {stats.get('erros_extracao', 0)}\n"
            f"Erros tradução   : {stats.get('erros_traducao', 0)}\n"
            f"Requisições API  : {stats.get('requisicoes', 0)}\n"
            f"Cache hits       : {stats.get('cache_hits', 0)}\n"
            f"Linhas traduzidas: {stats.get('linhas_traduzidas', 0)}\n"
            f"\nEncodings detectados:\n"
        )
        for enc, n in stats.get('encodings_detectados', {}).items():
            corpo += f"  {enc}: {n} arquivo(s)\n"
        corpo += (
            f"\nArquivos de log:\n"
            f"  📁  {self.pasta_logs}\n"
            f"  📄  pipeline_{self.ts}.txt\n"
            f"  ⚠️   erros_{self.ts}.txt\n"
            f"  📊  stats_{self.ts}.json\n"
            f"  ⚙️   config_{self.ts}.txt\n"
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
            f"pipeline_{self.ts}.txt",
            f"erros_{self.ts}.txt",
            f"stats_{self.ts}.json",
            f"config_{self.ts}.txt",
        ]:
            print(f"  {nome}")
        print()


# ============================================================================
# FALLBACK CHAIN DE ENCODING
# ============================================================================

ENCODINGS_FALLBACK = [
    'utf-8',
    'utf-8-sig',   # BOM - comum em fansubs antigos
    'cp1252',      # Windows Latin - gg subs legacy
    'latin-1',     # ISO 8859-1 base
    'iso-8859-1',  # variante
]

def ler_arquivo_com_encoding(caminho: str, log: GerenciadorLogs):
    """
    Tenta ler o arquivo percorrendo a cadeia de encodings.
    Em último caso usa utf-8 com errors='replace' (nunca falha).
    Retorna (linhas, encoding_usado).
    """
    log.debug(f"Detectando encoding: {os.path.basename(caminho)}")

    for enc in ENCODINGS_FALLBACK:
        try:
            with open(caminho, 'r', encoding=enc) as f:
                linhas = f.readlines()
            log.sucesso(f"Encoding detectado: {enc.upper()}")
            return linhas, enc
        except UnicodeDecodeError:
            log.debug(f"  ✗ {enc.upper()} falhou, tentando próximo...")
            continue

    # Fallback absoluto — nunca deve lançar exceção
    log.aviso("Todos os encodings falharam. Usando utf-8 + errors='replace'")
    with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
        linhas = f.readlines()
    log.aviso("Bytes inválidos substituídos por '?' — texto pode ter ruído mínimo")
    return linhas, 'utf-8-bypass'


# ============================================================================
# PIPELINE PRINCIPAL
# ============================================================================

class Pipeline:

    LM_URL  = "http://127.0.0.1:1234"
    API_URL = f"{LM_URL}/v1/chat/completions"

    PROMPT_SISTEMA = (
        "Você é um tradutor especialista em animes de ficção científica, mechas e aviação militar.\n"
        "Traduza APENAS o texto fornecido do inglês para português do Brasil (PT-BR).\n"
        "Regras estritas:\n"
        "1. Mantenha os índices intactos: '[0] tradução', '[1] tradução'...\n"
        "2. Responda APENAS com as linhas traduzidas. Zero observações ou saudações.\n"
        "3. Preserve termos técnicos militares de forma natural e fluida."
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

    # ── infra ─────────────────────────────────────────────────────────────────

    def _achar_mkvextract(self):
        for caminho in self.MKVEXTRACT_PATHS:
            if os.path.exists(caminho):
                return caminho
        return None

    def _achar_mkvmerge(self):
        for caminho in self.MKVMERGE_PATHS:
            if os.path.exists(caminho):
                return caminho
        return None

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
                for m in modelos:
                    self.log.debug(f"  · {m.get('id', '?')}")
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
            self.log.erro("mkvextract.exe ou mkvmerge.exe não encontrados — instale MKVToolNix")
            return False

        self.log.sucesso("✓ Infraestrutura validada!")
        return True

    # ── extração ──────────────────────────────────────────────────────────────

    def descobrir_track_id_ass(self, mkv_path: str) -> int:
        """Usa o mkvmerge para descobrir qual é o ID da faixa de texto ASS."""
        try:
            cmd = [self.mkvmerge, "-J", mkv_path]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if res.returncode != 0:
                self.log.erro(f"mkvmerge retornou código {res.returncode}")
                return -1

            info = json.loads(res.stdout)
            for track in info.get("tracks", []):
                # Procura por faixas do tipo 'subtitles' com codec 'S_TEXT/ASS'
                if track.get("type") == "subtitles":
                    props = track.get("properties", {})
                    codec_id = props.get("codec_id", "")
                    if "S_TEXT/ASS" in codec_id:
                        track_id = track.get("id")
                        self.log.debug(f"Track ID detectado automaticamente: {track_id} ({codec_id})")
                        return track_id

            self.log.erro("Nenhuma faixa de legenda texto (.ass) encontrada no MKV.")
            return -1

        except Exception as e:
            self.log.erro(f"Falha ao identificar o Track ID: {e}")
            return -1

    def extrair_legenda(self, mkv_path: str, track_id: int):
        """Extrai a faixa de legenda do MKV. Retorna caminho do .ass ou None."""
        nome = os.path.basename(mkv_path)
        base = os.path.splitext(nome)[0]
        ass  = os.path.join(os.path.dirname(mkv_path), f"{base}_extracted.ass")

        try:
            cmd = [self.mkvextract, mkv_path, "tracks", f"{track_id}:{ass}"]
            self.log.debug(f"mkvextract track={track_id} → {os.path.basename(ass)}")
            res = subprocess.run(cmd, capture_output=True, timeout=60, text=True)

            if res.returncode != 0:
                self.log.erro(f"mkvextract retornou código {res.returncode}")
                self.log.debug(f"STDERR: {res.stderr[:300]}")
                self.stats['erros_extracao'] += 1
                return None

            if not os.path.exists(ass):
                self.log.erro("Arquivo .ass não foi criado")
                self.stats['erros_extracao'] += 1
                return None

            self.log.sucesso(f"Extraído: {os.path.getsize(ass):,} bytes")
            self.stats['extraidos'] += 1
            return ass

        except subprocess.TimeoutExpired:
            self.log.erro("Timeout (60 s) na extração")
            self.stats['erros_extracao'] += 1
            return None
        except Exception as e:
            self.log.erro(f"Exceção na extração: {e}")
            self.log.traceback_completo(f"Extração de {nome}")
            self.stats['erros_extracao'] += 1
            return None

    # ── tradução ──────────────────────────────────────────────────────────────

    def _traduzir_lote(self, linhas: list, tentativa=1) -> dict:
        """Envia lote ao LM Studio. Retorna dict {idx: texto}."""
        payload = "\n".join(f"[{i}] {t}" for i, t in enumerate(linhas))

        # cache em memória
        if payload in self.cache:
            self.stats['cache_hits'] += 1
            return self.cache[payload]

        corpo = {
            "model": self.modelo_ativo,
            "messages": [
                {"role": "system", "content": self.PROMPT_SISTEMA},
                {"role": "user",   "content": f"Traduzir:\n{payload}"},
            ],
            "temperature": 0.7,
            "max_tokens":  2000,
        }

        self.stats['requisicoes'] += 1
        self.log.debug(f"API call — {len(linhas)} linhas (tentativa {tentativa})")

        try:
            r = requests.post(
                self.API_URL,
                json=corpo,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
        except requests.exceptions.Timeout:
            self.log.erro("Timeout (30 s) no LM Studio")
            if tentativa < 2:
                time.sleep(2 * tentativa)
                return self._traduzir_lote(linhas, tentativa + 1)
            raise RuntimeError("Timeout persistente no LM Studio")
        except requests.exceptions.ConnectionError as e:
            self.log.erro(f"Conexão recusada: {e}")
            raise RuntimeError("LM Studio sem conexão")

        if r.status_code != 200:
            self.log.erro(f"Status HTTP {r.status_code}")
            self.log.debug(f"Response: {r.text[:300]}")
            if tentativa < 2:
                time.sleep(2 * tentativa)
                return self._traduzir_lote(linhas, tentativa + 1)
            raise RuntimeError(f"Status HTTP {r.status_code}")

        bruto = r.json()['choices'][0]['message']['content'].strip()
        self.log.debug(f"Resposta: {len(bruto)} chars")

        # parse dos índices
        traduzidas = {}
        for idx_str, texto in re.findall(r"\[(\d+)\]\s*(.*?)(?=\[\d+\]|$)", bruto, re.DOTALL):
            texto_limpo = texto.strip()
            if texto_limpo:
                traduzidas[int(idx_str)] = texto_limpo

        if not traduzidas:
            self.log.aviso("Parse por índice falhou — tentando fallback linha a linha")
            for i, linha in enumerate(bruto.splitlines()[:len(linhas)]):
                if linha.strip():
                    traduzidas[i] = linha.strip()

        if not traduzidas:
            raise RuntimeError("Impossível extrair traduções da resposta")

        self.cache[payload] = traduzidas
        self.stats['linhas_traduzidas'] += len(traduzidas)
        return traduzidas

    # ── processamento do .ass ─────────────────────────────────────────────────

    def processar_legenda(self, ass_path: str, saida_path: str) -> bool:
        """Lê o .ass, traduz os diálogos e salva o resultado."""
        try:
            # ── ENCODING RESILIENTE ──────────────────────────────────────────
            linhas, enc_usado = ler_arquivo_com_encoding(ass_path, self.log)
            self.stats['encodings_detectados'][enc_usado] = \
                self.stats['encodings_detectados'].get(enc_usado, 0) + 1

            self.log.debug(f"Arquivo lido: {len(linhas)} linhas (encoding: {enc_usado})")

            # ── PARSE DOS DIÁLOGOS ───────────────────────────────────────────
            #
            # REGEX INDUSTRIAL (Paulo + Claude — v2)
            # (?:,[^,]*){8} → pula as 9 colunas de metadados (Start, End, Style,
            # Name, MarginL, MarginR, MarginV, Effect) sem importar conteúdo.
            # Captura apenas o texto final após a 9ª vírgula.
            #
            pat = re.compile(
                r"^(Dialogue:\s*[^,]*(?:,[^,]*){8},)(.*)$"
            )

            indices, textos = [], []
            puladas_binario = 0

            for i, linha in enumerate(linhas):

                # Normaliza a linha (remove \r, espaços extras)
                linha_limpa = linha.strip()

                # ── FILTRO 1: linhas gigantescas de fontes embutidas em Base64 ──
                # Diálogos reais raramente ultrapassam 500 chars.
                # Blocos de fonte/imagem do grupo [Cleo] chegam a milhares.
                if len(linha_limpa) > 2000:
                    puladas_binario += 1
                    continue

                m = pat.match(linha_limpa)
                if not m:
                    continue

                prefixo = m.group(1)
                txt = m.group(2).strip()

                # ── FILTRO 2: linhas vazias ou de efeito puro ───────────────
                # Limpa tags {...} para ver se sobra algum texto de verdade
                txt_sem_tags = re.sub(r'\{.*?\}', '', txt).strip()
                if not txt_sem_tags or len(txt_sem_tags) < 1:
                    continue

                # ── FILTRO 3: lixo binário residual ────────────────────────
                # Linhas com marcadores de fonte/imagem embutida
                if any(tag in txt for tag in [r'\font', r'\image', '0x', '\x00']):
                    puladas_binario += 1
                    continue

                indices.append(i)
                textos.append(txt)

            self.log.debug(f"Diálogos para traduzir : {len(textos)}")
            self.log.debug(f"Linhas binárias puladas: {puladas_binario}")

            if not textos:
                self.log.aviso("Nenhum diálogo encontrado — verifique o Track ID")
                return False

            # ── TRADUÇÃO POR LOTES ───────────────────────────────────────────
            mapa_traduzido = {}
            with tqdm(total=len(textos), desc="  Traduzindo", unit="ln", leave=False) as pbar:
                for i in range(0, len(textos), 20):
                    lote = textos[i:i+20]
                    try:
                        resultado = self._traduzir_lote(lote)
                        for k, v in resultado.items():
                            mapa_traduzido[i + k] = v
                    except Exception as e:
                        self.log.erro(f"Lote {i//20 + 1} falhou: {e}")
                        self.stats['erros_traducao'] += 1
                    pbar.update(len(lote))

            # ── RECONSTRUÇÃO DO ARQUIVO ──────────────────────────────────────
            for pos_atual, pos_arquivo in enumerate(indices):
                if pos_atual in mapa_traduzido:
                    m = pat.match(linhas[pos_arquivo].strip())
                    if m:
                        linhas[pos_arquivo] = f"{m.group(1)}{mapa_traduzido[pos_atual]}\n"

            # ── SALVA EM UTF-8 ───────────────────────────────────────────────
            with open(saida_path, 'w', encoding='utf-8') as f:
                f.writelines(linhas)

            self.log.sucesso(f"Salvo: {os.path.basename(saida_path)}")
            self.stats['traduzidos'] += 1
            return True

        except Exception as e:
            self.log.erro(f"Processamento falhou: {e}")
            self.log.traceback_completo(f"processar_legenda({os.path.basename(ass_path)})")
            self.stats['erros_traducao'] += 1
            return False


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    log = GerenciadorLogs()

    try:
        log.secao("PIPELINE INDUSTRIAL UNIFICADO — VERSÃO FINAL DE PRODUÇÃO")

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

        mkv_files = sorted(f for f in os.listdir(pasta) if f.endswith('.mkv'))
        log.info(f"Encontrados {len(mkv_files)} arquivo(s) .mkv")
        if not mkv_files:
            log.erro("Nenhum .mkv encontrado")
            return

        pasta_saida = os.path.join(pasta, "traducao")
        os.makedirs(pasta_saida, exist_ok=True)
        log.info(f"Saída: {pasta_saida}")

        log.salvar_config(pipe.LM_URL, pasta, "Automático (mkvmerge)", pasta_saida)

        # ── processamento ─────────────────────────────────────────────────────
        log.secao("PROCESSAMENTO")
        pipe.stats['mkv_total'] = len(mkv_files)

        for idx, nome_mkv in enumerate(mkv_files, 1):
            log.info(f"[{idx}/{len(mkv_files)}] {nome_mkv}")

            mkv_path = os.path.join(pasta, nome_mkv)

            # 0. DESCOBRIR TRACK ID
            track_id = pipe.descobrir_track_id_ass(mkv_path)
            if track_id == -1:
                log.erro("Pulando episódio por não encontrar track .ass válido")
                continue

            # 1. EXTRAÇÃO
            ass_temp = pipe.extrair_legenda(mkv_path, track_id)
            if not ass_temp:
                log.erro("Falha na extração — pulando episódio")
                continue

            # 2. TRADUÇÃO
            nome_base = os.path.splitext(nome_mkv)[0]
            ass_final = os.path.join(pasta_saida, f"{nome_base}_PTBR.ass")

            if pipe.processar_legenda(ass_temp, ass_final):
                log.sucesso("✓ Episódio concluído")
            else:
                log.erro("✗ Falha na tradução")

            # 3. LIMPEZA
            try:
                os.remove(ass_temp)
                log.debug("Arquivo temporário removido")
            except Exception as e:
                log.aviso(f"Não conseguiu remover temporário: {e}")

        # ── relatório final ───────────────────────────────────────────────────
        log.secao("RELATÓRIO FINAL")
        log.salvar_stats(pipe.stats)
        log.relatorio_final(pipe.stats, pasta_saida)

    except KeyboardInterrupt:
        log.aviso("Pipeline interrompido pelo usuário (Ctrl+C)")
    except Exception as e:
        log.erro(f"Erro crítico no pipeline: {e}")
        log.traceback_completo("main()")
    finally:
        log.fechar()


if __name__ == "__main__":
    main()