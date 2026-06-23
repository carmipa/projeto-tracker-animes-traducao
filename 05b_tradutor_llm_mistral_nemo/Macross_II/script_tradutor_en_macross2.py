#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PIPELINE DE TRADUÇÃO EN -> PT-BR — Macross II: Lovers Again
Alvo: [AntBnecn] Macross II (BDRip 1440x1080p)[sxales]

Traduz legendas .ass e .srt em inglês via LM Studio (Mistral Nemo) e salva PT-BR.
Logs auditáveis, cache persistente, mascaramento de tags ASS e concorrência multithread.

Uso:
  python script_tradutor_en_macross2.py
  python script_tradutor_en_macross2.py --entrada PASTA_ENG --saida PASTA_PTBR
  python script_tradutor_en_macross2.py --arquivo ep01.ass ep02.srt --saida PASTA_PTBR
"""

import os
import sys
import re
import json
import time
import argparse
import threading
import requests
import traceback
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    Sistema de logs auditável com arquivos separados por execução.
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
        self.pasta_logs = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "logs"
        )
        os.makedirs(self.pasta_logs, exist_ok=True)

        self.ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        # Arquivos de auditoria
        self.f_pipeline = open(
            os.path.join(self.pasta_logs, f"pipeline_en_macross2_{self.ts}.txt"),
            'w', encoding='utf-8'
        )
        self.f_erros = open(
            os.path.join(self.pasta_logs, f"erros_en_macross2_{self.ts}.txt"),
            'w', encoding='utf-8'
        )
        self.caminho_stats  = os.path.join(self.pasta_logs, f"stats_en_macross2_{self.ts}.json")
        self.caminho_config = os.path.join(self.pasta_logs, f"config_en_macross2_{self.ts}.txt")

        header = (
            f"\n{'='*80}\n"
            f"PIPELINE INDUSTRIAL DE TRADUÇÃO EN -> PT-BR | MACROSS II\n"
            f"{'='*80}\n"
            f"Início    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Python    : {sys.version.split()[0]}\n"
            f"Pasta logs: {self.pasta_logs}\n"
            f"{'='*80}\n\n"
        )
        for f in (self.f_pipeline, self.f_erros):
            f.write(header)
            f.flush()

    def _gravar(self, nivel: str, mensagem: str):
        ts  = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        linha = f"[{ts}] [{nivel:8s}] {mensagem}"

        self.f_pipeline.write(linha + "\n")
        self.f_pipeline.flush()

        if nivel in ("ERRO", "CRÍTICO"):
            self.f_erros.write(linha + "\n")
            self.f_erros.flush()

        cor = self.CORES.get(nivel, Fore.WHITE)
        try:
            tqdm.write(f"{cor}{linha}{Style.RESET_ALL}")
        except Exception:
            print(f"{cor}{linha}{Style.RESET_ALL}")

    def secao(self, titulo: str):
        bloco = f"\n{'='*80}\n{titulo.center(80)}\n{'='*80}\n"
        self.f_pipeline.write(bloco + "\n")
        self.f_pipeline.flush()
        print(f"\n{Fore.MAGENTA}{titulo.center(80)}{Style.RESET_ALL}\n")

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

    def salvar_config(self, lm_url, modelo, pasta_entrada, pasta_saida, max_workers=2, batch_size=8):
        conteudo = (
            f"\n{'='*80}\nCONFIGURAÇÃO DA EXECUÇÃO\n{'='*80}\n\n"
            f"Data/Hora      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"LM Studio URL  : {lm_url}\n"
            f"Modelo Ativo   : {modelo}\n"
            f"Threads        : {max_workers}\n"
            f"Batch size     : {batch_size}\n\n"
            f"Pasta entrada  : {pasta_entrada}\n"
            f"Pasta saída    : {pasta_saida}\n\n"
            f"Logs:\n"
            f"  Pipeline : pipeline_en_macross2_{self.ts}.txt\n"
            f"  Erros    : erros_en_macross2_{self.ts}.txt\n"
            f"  Stats    : stats_en_macross2_{self.ts}.json\n"
            f"  Config   : config_en_macross2_{self.ts}.txt\n"
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

    def fechar(self):
        for f in (self.f_pipeline, self.f_erros):
            f.close()
        print(f"\n{Fore.GREEN}✓ LOGS SALVOS EM: {self.pasta_logs}{Style.RESET_ALL}\n")


# ============================================================================
# VALIDAÇÃO ANTI-ALUCINAÇÃO E LORE (MACROSS II)
# ============================================================================

MAX_TAGS_POR_DIALOG = 12

# Resíduos perigosos da língua inglesa sem tradução na frase
PADRAO_RESIDUO_INGLES = re.compile(
    r"\b(you|your|the|what|how|where|when|this|that|there|here|then|they|with|about|was|were)\b",
    re.IGNORECASE,
)

PADRAO_PREAMBULO_LLM = re.compile(
    r"^(esta [ée] a tradu|segue|abaixo est[áa]|abaixo seguem|claro,?\s+vou|here is|translation:|note:)\b",
    re.IGNORECASE,
)

# Substituições de lore para reforçar e corrigir erros comuns do LLM
SUBSTITUICOES_POS_PROCESSAMENTO = [
    (re.compile(r"\bValqu[ií]ria\b", re.I), "Valkyrie"),
    (re.compile(r"\bValqu[ií]rias\b", re.I), "Valkyries"),
    (re.compile(r"\bEmulador(?:es|a|as)?\b", re.I), "Emuladora"),
    (re.compile(r"\bMarduks?\b", re.I), "Mardook"),
    (re.compile(r"\bEsquadrão Fada\b", re.I), "Esquadrão Faerie"),
]

def validar_traducao(original: str, traducao: str) -> bool:
    if not traducao or "[ERRO_TRADUCAO" in traducao:
        return False
    # Filtro de preâmbulos conversacionais
    if PADRAO_PREAMBULO_LLM.match(traducao.strip()):
        return False
    
    # Validador de resíduos do inglês
    # Fazemos uma exceção para nomes próprios ou termos protegidos que de fato aparecem no original.
    # Se o resíduo do inglês for apenas uma palavra isolada e essa palavra NÃO estiver no original, invalidamos.
    residuos = PADRAO_RESIDUO_INGLES.findall(traducao)
    if residuos:
        orig_words = set(re.findall(r'\b\w+\b', original.lower()))
        for res in residuos:
            if res.lower() not in orig_words:
                return False
                
    if len(traducao) > max(250, len(original) * 8):
        return False
    return True


# ============================================================================
# PIPELINE DE TRADUÇÃO MISTRAL NEMO
# ============================================================================

class PipelineMacross2:
    LM_URL = "http://127.0.0.1:1234"

    SYSTEM_PROMPT = (
        "You are an expert subtitler for Japanese anime, specializing in the Macross sci-fi, military space opera, and musical drama universe (specifically Macross II: Lovers Again).\n"
        "Translate the following numbered subtitle lines from English into natural, fluent Brazilian Portuguese (PT-BR) suitable for anime subtitles.\n"
        "The final output must be entirely in Brazilian Portuguese, except for protected terms, character names, faction names, ship names, model names, and subtitle tags.\n\n"

        "CRITICAL RULES:\n"
        "1. Keep the exact same numbering, order, and line structure.\n"
        "2. Return ONLY the numbered translated lines. Do not add notes, explanations, headers, markdown, or comments.\n"
        "3. Never merge, split, reorder, remove, or duplicate numbered lines.\n"
        "4. Keep intact all subtitle markers and tags exactly as received, such as '[T0]', '[T1]', '[T2]', '{\\an8}', '<i>', '</i>', '\\N', '\\n'. They must stay in the same position and format.\n\n"

        "PROTECTED MACROSS TERMS — DO NOT TRANSLATE:\n"
        "- Valkyrie, Valkyries, Variable Fighter, VF-2SS Valkyrie II, Metal Siren, Macross Cannon, Gunpod, Gun Pod, Battroid, GERWALK\n"
        "- Mardook, Zentradi, Meltrandi, U.N. Spacy, SNN (Scramble News Network), Faerie Squadron\n"
        "- Ishtar, Hibiki Kanzaki, Sylvie Gena, Feff, Volion, Emperor Inges, Exsedol, Mash, Dennis Lone, Amy\n"
        "- Emulator (translate as Emuladora in PT-BR when referring to Ishtar or others of her class)\n"
        "- Keep song titles in English/original, such as: '2億年前のように静かだね (2 Oku Nen Mae no You ni Shizuka da ne)', 'de-ja-vu', 'Yakusoku'.\n\n"

        "TERM ADAPTATIONS:\n"
        "- Protoculture -> Protocultura\n"
        "- Zentradi -> Zentradi\n"
        "- Meltrandi -> Meltrandi\n"
        "- Fold (hyper space jump/dimension) -> Fold (e.g. 'Salto Fold', 'Navegação Fold', 'Dobra Fold')\n"
        "- Emulator -> Emuladora\n\n"

        "STYLE RULES FOR PT-BR SUBTITLES:\n"
        "1. Use natural Brazilian Portuguese suitable for anime subtitles.\n"
        "2. Avoid literal English phrasing.\n"
        "3. Keep sentences concise and readable.\n"
        "4. Preserve the dual musical, dramatic, and military tone of Macross II.\n"
        "5. Do not use exaggerated Brazilian slang unless the original line is clearly casual or comic.\n"
        "6. Translate idioms by meaning, not word-for-word.\n\n"

        "MILITARY / RADIO TRANSLATION GUIDANCE:\n"
        "'Roger' or 'Roger that' -> 'Copiado' or 'Entendido';\n"
        "'Copy that' -> 'Entendido' or 'Copiado';\n"
        "'Stand by' -> 'Aguarde';\n"
        "'Enemy unit' -> 'Unidade inimiga';\n"
        "'Target locked' -> 'Alvo travado';\n"
        "'Launch' -> 'Lançar' or 'Decolar', depending on context (e.g., VF launching is 'Decolar');\n"
        "'Sortie' -> 'Saída para combate' or 'Partida'.\n"
    )

    def __init__(
        self,
        log: GerenciadorLogs,
        modelo=None,
        max_workers=2,
        batch_size=8,
        lm_url=None,
        limpar_cache=False,
    ):
        self.log = log
        self.LM_URL = (lm_url or self.LM_URL).rstrip("/")
        self.API_URL = f"{self.LM_URL}/v1/chat/completions"
        self.cache = {}
        self.cache_lock = threading.Lock()
        self.stats_lock = threading.Lock()
        self.modelo_ativo = modelo or "local-model"
        self.max_workers = max(1, max_workers)
        self.batch_size = max(1, batch_size)

        self.caminho_cache = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "traducao_cache_macross2_en.json"
        )
        if limpar_cache and os.path.exists(self.caminho_cache):
            os.remove(self.caminho_cache)
            self.log.aviso("Cache anterior removido (--limpar-cache).")
        self._carregar_cache()

        self.stats = {
            'total_arquivos':     0,
            'traduzidos':         0,
            'erros_traducao':     0,
            'linhas_com_erro':    0,
            'requisicoes':        0,
            'cache_hits':         0,
            'linhas_traduzidas':  0,
            'dialogos_pulados':   0,
        }

    def _carregar_cache(self):
        if os.path.exists(self.caminho_cache):
            try:
                with open(self.caminho_cache, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                self.log.info(f"Cache carregado: {len(self.cache)} traduções disponíveis.")
            except Exception as e:
                self.log.aviso(f"Erro ao carregar cache do disco, iniciando vazio: {e}")
                self.cache = {}
        else:
            self.cache = {}

    def _salvar_cache(self):
        try:
            caminho_tmp = self.caminho_cache + ".tmp"
            with self.cache_lock:
                payload = dict(self.cache)
            with open(caminho_tmp, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            os.replace(caminho_tmp, self.caminho_cache)
        except Exception as e:
            self.log.aviso(f"Erro ao salvar cache em disco: {e}")

    def _atualizar_cache(self, chave: str, valor: str):
        if not chave or "[ERRO_TRADUCAO" in valor:
            return
        with self.cache_lock:
            self.cache[chave] = valor

    def _inc_stat(self, chave: str, valor: int = 1):
        with self.stats_lock:
            self.stats[chave] += valor

    def validar_conexao(self) -> bool:
        self.log.secao("VALIDAÇÃO DE INFRAESTRUTURA")
        self.log.debug(f"Testando LM Studio em {self.LM_URL}...")
        try:
            r = requests.get(f"{self.LM_URL}/v1/models", timeout=5)
            if r.status_code == 200:
                modelos = r.json().get('data', [])
                self.log.sucesso(f"LM Studio OK — {len(modelos)} modelo(s) carregado(s)")
                if not modelos:
                    self.log.erro("LM Studio online mas sem modelo carregado.")
                    return False
                if self.modelo_ativo == "local-model":
                    self.modelo_ativo = modelos[0].get('id', 'local-model')
                else:
                    ids = [m.get('id', '') for m in modelos]
                    if self.modelo_ativo not in ids:
                        self.log.aviso(
                            f"Modelo '{self.modelo_ativo}' não encontrado. "
                            f"Usando: {modelos[0].get('id', 'local-model')}"
                        )
                        self.modelo_ativo = modelos[0].get('id', 'local-model')
                self.log.info(f"Usando modelo ativo: {self.modelo_ativo}")
                return True
            else:
                self.log.erro(f"LM Studio HTTP {r.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.log.erro(
                f"LM Studio não responde em {self.LM_URL}. "
                "Certifique-se de que o LM Studio está rodando e a API local está ativa."
            )
            return False
        except Exception as e:
            self.log.erro(f"Erro ao contatar LM Studio: {e}")
            return False

    def mascarar_tags(self, texto_bruto: str):
        tags = re.findall(r'\{[^}]+\}', texto_bruto)
        texto_limpo = texto_bruto
        for idx_tag, tag in enumerate(tags):
            texto_limpo = texto_limpo.replace(tag, f"[T{idx_tag}]", 1)
        return texto_limpo, tags

    def restaurar_tags(self, texto_traduzido: str, tags: list):
        trad = texto_traduzido
        for idx_tag, tag in enumerate(tags):
            marcador = f"[T{idx_tag}]"
            while marcador in trad:
                trad = trad.replace(marcador, tag, 1)
            if f"[T{idx_tag}]" not in trad and tag not in trad:
                trad = re.sub(
                    rf'\[?[Tt]\s*{idx_tag}\]?',
                    lambda _m, t=tag: t,
                    trad,
                    count=1,
                )
        return trad

    def limpar_saida_traducao(self, texto: str) -> str:
        texto = texto.strip()
        if not re.search(r"\\[Nn]\s*[-–]", texto):
            texto = re.sub(r"^\s*[-–•]\s*", "", texto)
        texto = re.sub(r"\[\s*[Tt]\s*(\d+)\s*\]", r"[T\1]", texto)
        texto = re.sub(r"\\\s*([Nnh])", r"\\\1", texto)
        texto = texto.replace("/N", r"\N").replace("/n", r"\n")
        texto = texto.replace("\r\n", "\n").replace("\r", "\n")
        texto = re.sub(r"\s*\n+\s*", r"\\N", texto)
        texto = re.sub(r"\s*\\N\s*", r"\\N", texto)
        texto = re.sub(r"\s+([!?:;,.])", r"\1", texto)
        for padrao, substituto in SUBSTITUICOES_POS_PROCESSAMENTO:
            texto = padrao.sub(substituto, texto)
        return texto

    def _traduzir_lote_ia(self, lote_textos: list, tentativa=1) -> dict:
        payload = "\n".join(f"[{i}] {t}" for i, t in enumerate(lote_textos))
        max_tokens = min(4096, max(400, 120 * len(lote_textos)))
        corpo = {
            "model": self.modelo_ativo,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Translate exactly these {len(lote_textos)} numbered lines from English to Brazilian Portuguese.\n"
                        f"Return exactly {len(lote_textos)} lines with the same indices [0]..[{len(lote_textos)-1}].\n"
                        f"Keep all [Tn] markers and \\N exactly as provided.\n"
                        f"No notes, no markdown, no extra text.\n\n"
                        f"{payload}"
                    ),
                },
            ],
            "temperature": 0.1,
            "max_tokens": max_tokens,
        }

        self._inc_stat('requisicoes')

        try:
            r = requests.post(
                self.API_URL,
                json=corpo,
                headers={"Content-Type": "application/json"},
                timeout=120,
            )
        except Exception as e:
            self.log.erro(f"LM Studio timeout/erro na chamada: {e}")
            if tentativa < 3:
                tempo_espera = tentativa * 10
                self.log.aviso(f"LM Studio Offline. Tentativa {tentativa}/3. Aguardando {tempo_espera}s...")
                time.sleep(tempo_espera)
                return self._traduzir_lote_ia(lote_textos, tentativa + 1)
            raise e

        if r.status_code != 200:
            self.log.erro(f"HTTP {r.status_code} no lote.")
            if tentativa < 3:
                time.sleep(5)
                return self._traduzir_lote_ia(lote_textos, tentativa + 1)
            raise RuntimeError(f"HTTP {r.status_code}")

        try:
            resposta = r.json()
            bruto = resposta['choices'][0]['message']['content'].strip()
        except (ValueError, KeyError, IndexError, TypeError) as e:
            self.log.erro(f"Resposta inválida do LM Studio: {e}")
            if tentativa < 3:
                time.sleep(5)
                return self._traduzir_lote_ia(lote_textos, tentativa + 1)
            raise RuntimeError("Resposta inválida do LM Studio") from e

        # Parse por índices
        traduzidas = {}
        for idx_str, texto in re.findall(r"\[(\d+)\]\s*(.*?)(?=\[\d+\]|$)", bruto, re.DOTALL):
            idx = int(idx_str)
            if 0 <= idx < len(lote_textos):
                texto_limpo = self.limpar_saida_traducao(texto)
                if texto_limpo and validar_traducao(lote_textos[idx], texto_limpo):
                    traduzidas[idx] = texto_limpo
                elif texto_limpo:
                    self.log.debug(
                        f"Validação rejeitou idx {idx}: "
                        f"EN='{lote_textos[idx][:60]}' | PT='{texto_limpo[:60]}'"
                    )

        if not traduzidas:
            linhas_bruto = bruto.splitlines()
            for i, linha in enumerate(linhas_bruto[:len(lote_textos)]):
                linha_limpa = re.sub(r"^\[?\d+\]?[.)\s-]*", "", linha.strip()).strip()
                texto_limpo = self.limpar_saida_traducao(linha_limpa)
                if texto_limpo and validar_traducao(lote_textos[i], texto_limpo):
                    traduzidas[i] = texto_limpo

        if traduzidas:
            ultimo_idx = max(traduzidas.keys())
            ultimo_texto = traduzidas[ultimo_idx]
            linhas_ultimo = ultimo_texto.split('\n')
            if len(linhas_ultimo) > 1:
                linhas_limpas = []
                for linha_extra in linhas_ultimo:
                    if re.search(
                        r"^(here is|translation:|hope this|let me know|espero que|aqui está)",
                        linha_extra.strip(),
                        re.IGNORECASE,
                    ):
                        break
                    linhas_limpas.append(linha_extra)
                traduzidas[ultimo_idx] = self.limpar_saida_traducao("\n".join(linhas_limpas))

        if not traduzidas:
            self.log.erro(f"Resposta do LLM sem traduções válidas:\n{bruto[:500]}\n")
            raise RuntimeError("Impossível extrair traduções da resposta do LLM")

        for idx_lote, texto_ptbr in traduzidas.items():
            texto_en = lote_textos[idx_lote]
            prefixo_arq = f"[{getattr(self, 'arquivo_atual', 'Lote')}] "
            tqdm.write(
                f"  {Fore.CYAN}{prefixo_arq}EN: {texto_en} {Fore.RESET}-> "
                f"{Fore.GREEN}PT-BR: {texto_ptbr}{Style.RESET_ALL}"
            )

        return traduzidas

    def traduzir_lote_resiliente(self, lote_textos: list) -> dict:
        try:
            resultado = self._traduzir_lote_ia(lote_textos)
        except Exception as e:
            self.log.aviso(f"Falha na tradução em lote ({e}). Iniciando fallback resiliente...")
            resultado = {}

        indices_faltantes = [i for i in range(len(lote_textos)) if i not in resultado]
        if not indices_faltantes:
            return resultado

        if resultado:
            self.log.aviso(
                f"Lote parcial {len(resultado)}/{len(lote_textos)}. "
                f"Retraduzindo {len(indices_faltantes)} linha(s) individualmente..."
            )

        for idx in indices_faltantes:
            texto = lote_textos[idx]
            sucesso_linha = False
            for _ in range(3):
                try:
                    res_indiv = self._traduzir_lote_ia([texto])
                    if 0 in res_indiv:
                        resultado[idx] = res_indiv[0]
                        sucesso_linha = True
                        break
                except Exception:
                    time.sleep(2)
            if not sucesso_linha:
                self.log.erro(f"Falha definitiva ao traduzir linha: '{texto[:40]}...'")
                resultado[idx] = f"[ERRO_TRADUCAO: {texto}]"

        return resultado

    # ── processamento do .ass ─────────────────────────────────────────────────

    def processar_legenda_ass(self, entrada_path: str, saida_path: str) -> bool:
        try:
            with open(entrada_path, 'r', encoding='utf-8', errors='replace') as f:
                linhas = f.readlines()

            pat = re.compile(r"^(Dialogue:\s*[^,]*(?:,[^,]*){8},)(.*)$")

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

                # Ignora linhas vazias ou puramente com tags
                txt_sem_tags = re.sub(r'\{.*?\}', '', txt).strip()
                if not txt_sem_tags:
                    continue

                # Ignora lixo ou efeitos pesados de fonte
                if any(tag in txt for tag in [r'\font', r'\image', '0x', '\x00']):
                    puladas_binario += 1
                    continue

                texto_masc, tags = self.mascarar_tags(txt)
                if len(tags) > MAX_TAGS_POR_DIALOG:
                    puladas_binario += 1
                    self._inc_stat('dialogos_pulados')
                    self.log.debug(
                        f"Diálogo ignorado (>{MAX_TAGS_POR_DIALOG} tags ASS): "
                        f"{txt[:50]}..."
                    )
                    continue

                indices_arquivo.append(i)
                textos_brutos.append(txt)
                textos_mascarados.append(texto_masc)
                lista_tags.append(tags)

            if puladas_binario:
                self.log.info(f"Diálogos pulados (binário/tags excessivas): {puladas_binario}")

            if not textos_brutos:
                self.log.aviso(f"Nenhum diálogo qualificado no .ass: {os.path.basename(entrada_path)}")
                return False

            mapa_dialogos_finais = [None] * len(textos_brutos)
            indices_para_traduzir = []
            textos_para_traduzir = []

            cache_hits_arquivo = 0
            for idx_dialogo, texto_masc in enumerate(textos_mascarados):
                if texto_masc in self.cache:
                    cache_hits_arquivo += 1
                    self._inc_stat('cache_hits')
                    trad_masc = self.cache[texto_masc]
                    trad_final = self.restaurar_tags(trad_masc, lista_tags[idx_dialogo])
                    mapa_dialogos_finais[idx_dialogo] = trad_final
                else:
                    indices_para_traduzir.append(idx_dialogo)
                    textos_para_traduzir.append(texto_masc)

            self.log.info(
                f"Cache hits neste arquivo: {cache_hits_arquivo} | "
                f"Misses a traduzir: {len(textos_para_traduzir)}"
            )

            # Processa misses via ThreadPoolExecutor
            if textos_para_traduzir:
                lotes = []
                for i in range(0, len(textos_para_traduzir), self.batch_size):
                    lotes.append(textos_para_traduzir[i:i+self.batch_size])

                mapa_futuros = {}
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    for idx_lote, lote in enumerate(lotes):
                        f = executor.submit(self.traduzir_lote_resiliente, lote)
                        mapa_futuros[f] = (idx_lote, lote)

                    with tqdm(total=len(lotes), desc="  Processando lotes", unit="lote", leave=False, colour="cyan") as pbar:
                        for futuro in as_completed(mapa_futuros):
                            idx_lote, lote = mapa_futuros[futuro]
                            try:
                                resultado_lote = futuro.result()
                                offset = idx_lote * self.batch_size
                                for k, v in resultado_lote.items():
                                    idx_global = offset + k
                                    if idx_global < len(textos_para_traduzir):
                                        idx_dialogo = indices_para_traduzir[idx_global]
                                        original_masc = textos_para_traduzir[idx_global]

                                        self._atualizar_cache(original_masc, v)
                                        if "[ERRO_TRADUCAO" in v:
                                            self._inc_stat('linhas_com_erro')
                                        else:
                                            self._inc_stat('linhas_traduzidas')

                                        trad_final = self.restaurar_tags(v, lista_tags[idx_dialogo])
                                        mapa_dialogos_finais[idx_dialogo] = trad_final
                            except Exception as exc:
                                self.log.erro(f"Erro no lote {idx_lote}: {exc}")
                                offset = idx_lote * self.batch_size
                                for k in range(len(lote)):
                                    idx_global = offset + k
                                    if idx_global >= len(textos_para_traduzir):
                                        continue
                                    idx_dialogo = indices_para_traduzir[idx_global]
                                    if mapa_dialogos_finais[idx_dialogo] is None:
                                        erro = f"[ERRO_TRADUCAO: {textos_para_traduzir[idx_global]}]"
                                        mapa_dialogos_finais[idx_dialogo] = self.restaurar_tags(
                                            erro, lista_tags[idx_dialogo]
                                        )
                                        self._inc_stat('linhas_com_erro')
                            pbar.update(1)

                self._salvar_cache()

            # Reconstrói arquivo — falhas individuais recebem marcador visível
            for idx_dialogo, pos_arquivo in enumerate(indices_arquivo):
                traduzido = mapa_dialogos_finais[idx_dialogo]
                if traduzido is None:
                    traduzido = f"[ERRO_TRADUCAO: {textos_brutos[idx_dialogo]}]"
                    self._inc_stat('linhas_com_erro')
                m = pat.match(linhas[pos_arquivo].strip())
                if m:
                    linhas[pos_arquivo] = f"{m.group(1)}{traduzido}\n"

            with open(saida_path, 'w', encoding='utf-8') as f:
                f.writelines(linhas)

            self._inc_stat('traduzidos')
            return True

        except Exception as e:
            self.log.erro(f"Erro no processamento do ASS {entrada_path}: {e}")
            self.log.traceback_completo("processar_legenda_ass()")
            self._inc_stat('erros_traducao')
            return False

    # ── processamento do .srt ─────────────────────────────────────────────────

    def processar_legenda_srt(self, entrada_path: str, saida_path: str) -> bool:
        try:
            with open(entrada_path, 'r', encoding='utf-8', errors='replace') as f:
                linhas = f.readlines()

            blocos = extrair_blocos_srt(linhas)
            if not blocos:
                self.log.aviso(f"Nenhum diálogo no .srt: {os.path.basename(entrada_path)}")
                return False

            novas_linhas = list(linhas)
            mapa_dialogos_finais = [None] * len(blocos)
            indices_para_traduzir = []
            textos_para_traduzir = []
            cache_hits_arquivo = 0

            for idx_bloco, bloco in enumerate(blocos):
                txt = bloco['texto']
                if txt in self.cache:
                    cache_hits_arquivo += 1
                    self._inc_stat('cache_hits')
                    mapa_dialogos_finais[idx_bloco] = self.cache[txt]
                else:
                    indices_para_traduzir.append(idx_bloco)
                    textos_para_traduzir.append(txt)

            self.log.info(
                f"Cache hits neste arquivo: {cache_hits_arquivo} | "
                f"Misses a traduzir: {len(textos_para_traduzir)}"
            )

            if textos_para_traduzir:
                lotes = [
                    textos_para_traduzir[i:i + self.batch_size]
                    for i in range(0, len(textos_para_traduzir), self.batch_size)
                ]

                mapa_futuros = {}
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    for idx_lote, lote in enumerate(lotes):
                        f = executor.submit(self.traduzir_lote_resiliente, lote)
                        mapa_futuros[f] = idx_lote

                    with tqdm(
                        total=len(lotes),
                        desc="  Processando lotes",
                        unit="lote",
                        leave=False,
                        colour="cyan",
                    ) as pbar:
                        for futuro in as_completed(mapa_futuros):
                            idx_lote = mapa_futuros[futuro]
                            try:
                                resultado_lote = futuro.result()
                                offset = idx_lote * self.batch_size
                                for k, v in resultado_lote.items():
                                    idx_global = offset + k
                                    if idx_global >= len(textos_para_traduzir):
                                        continue
                                    idx_bloco = indices_para_traduzir[idx_global]
                                    original_txt = textos_para_traduzir[idx_global]
                                    self._atualizar_cache(original_txt, v)
                                    if "[ERRO_TRADUCAO" in v:
                                        self._inc_stat('linhas_com_erro')
                                    else:
                                        self._inc_stat('linhas_traduzidas')
                                    mapa_dialogos_finais[idx_bloco] = v
                            except Exception as exc:
                                self.log.erro(f"Erro no lote {idx_lote}: {exc}")
                                offset = idx_lote * self.batch_size
                                for k in range(len(lotes[idx_lote])):
                                    idx_global = offset + k
                                    if idx_global >= len(textos_para_traduzir):
                                        continue
                                    idx_bloco = indices_para_traduzir[idx_global]
                                    if mapa_dialogos_finais[idx_bloco] is None:
                                        mapa_dialogos_finais[idx_bloco] = (
                                            f"[ERRO_TRADUCAO: {textos_para_traduzir[idx_global]}]"
                                        )
                                        self._inc_stat('linhas_com_erro')
                            pbar.update(1)

                self._salvar_cache()

            for idx_bloco, bloco in enumerate(blocos):
                traduzido = mapa_dialogos_finais[idx_bloco]
                if traduzido is None:
                    traduzido = f"[ERRO_TRADUCAO: {bloco['texto']}]"
                    self._inc_stat('linhas_com_erro')
                partes = re.split(r'\\N', traduzido)
                if len(partes) == 1:
                    partes = traduzido.split('\n')
                for j, idx_linha in enumerate(bloco['indices']):
                    if j < len(partes):
                        novas_linhas[idx_linha] = partes[j].strip() + "\n"

            with open(saida_path, 'w', encoding='utf-8') as f:
                f.writelines(novas_linhas)

            self._inc_stat('traduzidos')
            return True

        except Exception as e:
            self.log.erro(f"Erro no processamento do SRT {entrada_path}: {e}")
            self.log.traceback_completo("processar_legenda_srt()")
            self._inc_stat('erros_traducao')
            return False


# ============================================================================
# EXECUÇÃO DO OPERADOR
# ============================================================================

def extrair_blocos_srt(linhas):
    """Agrupa linhas de texto do SRT por bloco (suporta legendas multilinha)."""
    blocos = []
    i = 0
    total = len(linhas)

    while i < total:
        if not linhas[i].strip().isdigit():
            i += 1
            continue

        i += 1
        if i >= total or '-->' not in linhas[i]:
            continue
        i += 1

        textos = []
        indices = []
        while i < total:
            bruto = linhas[i].rstrip('\n')
            if not bruto.strip():
                break
            if bruto.strip().isdigit() and i + 1 < total and '-->' in linhas[i + 1]:
                break
            textos.append(bruto.strip())
            indices.append(i)
            i += 1

        if textos:
            blocos.append({
                'indices': indices,
                'texto': '\\N'.join(textos),
            })

    return blocos


def listar_arquivos_legenda(pasta_entrada):
    """Lista .ass/.srt recursivamente, preservando estrutura de subpastas."""
    pasta_entrada = os.path.abspath(pasta_entrada)
    arquivos = []
    vistos = set()
    for dirpath, _dirnames, filenames in os.walk(pasta_entrada):
        for nome in filenames:
            if not nome.lower().endswith(('.ass', '.srt')):
                continue
            caminho = os.path.join(dirpath, nome)
            chave = os.path.normcase(caminho)
            if chave not in vistos:
                vistos.add(chave)
                arquivos.append(caminho)
    return sorted(arquivos)


def caminho_saida_relativo(pasta_entrada, caminho_arq, pasta_saida):
    """Espelha subpastas da entrada na saída, evitando colisão de basename."""
    pasta_entrada = os.path.abspath(pasta_entrada)
    caminho_arq = os.path.abspath(caminho_arq)
    pasta_saida = os.path.abspath(pasta_saida)
    rel = os.path.relpath(os.path.dirname(caminho_arq), pasta_entrada)
    if rel == '.':
        destino_dir = pasta_saida
    else:
        destino_dir = os.path.join(pasta_saida, rel)
    return os.path.join(destino_dir, nome_saida_ptbr(os.path.basename(caminho_arq)))


def nome_saida_ptbr(nome_arq):
    nome_saida = nome_arq.replace("_ENG", "_PTBR").replace("_eng", "_PTBR")
    if "_PTBR" not in nome_saida:
        base, ext = os.path.splitext(nome_arq)
        nome_saida = f"{base}_PTBR{ext}"
    return nome_saida

def obter_diretorio_operador(mensagem_prompt, padrao_caminho=None):
    while True:
        sufixo_padrao = f" (ENTER = {padrao_caminho})" if padrao_caminho else ""
        entrada = input(f"{Fore.YELLOW}{mensagem_prompt}{sufixo_padrao}: {Style.RESET_ALL}").strip()
        entrada = entrada.strip('"').strip("'")
        if not entrada and padrao_caminho:
            return os.path.abspath(padrao_caminho)
        if not entrada:
            continue
        if not os.path.isdir(entrada):
            print(f"{Fore.RED}[ERRO] Diretorio nao existe: {entrada}")
            continue
        return os.path.abspath(entrada)


def normalizar_caminho(caminho: str) -> str:
    return os.path.abspath(caminho.strip().strip('"').strip("'"))


def validar_arquivo_legenda(caminho: str) -> str:
    caminho = normalizar_caminho(caminho)
    if not os.path.isfile(caminho):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    if not caminho.lower().endswith(('.ass', '.srt')):
        raise ValueError(f"Extensão inválida (use .ass ou .srt): {caminho}")
    return caminho


def resolver_caminho_saida(caminho_entrada: str, pasta_saida: str | None) -> str:
    nome_saida = nome_saida_ptbr(os.path.basename(caminho_entrada))
    if pasta_saida:
        return os.path.join(normalizar_caminho(pasta_saida), nome_saida)
    return os.path.join(os.path.dirname(caminho_entrada), nome_saida)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Tradutor EN→PT-BR Macross II via LM Studio (Mistral Nemo).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exemplos:\n"
            "  python script_tradutor_en_macross2.py\n"
            "  python script_tradutor_en_macross2.py --entrada D:\\legendas_eng --saida D:\\legendas_ptbr\n"
            "  python script_tradutor_en_macross2.py --arquivo ep01.ass ep02.srt --saida D:\\legendas_ptbr\n"
            "  python script_tradutor_en_macross2.py --arquivo D:\\legendas\\ep01.ass\n"
        ),
    )
    parser.add_argument("--entrada", help="Pasta com legendas .ass/.srt em inglês")
    parser.add_argument(
        "--arquivo",
        nargs="+",
        metavar="CAMINHO",
        help="Um ou mais arquivos .ass/.srt específicos (ignora --entrada)",
    )
    parser.add_argument(
        "--saida",
        help="Pasta de saída PT-BR (obrigatória com --entrada; opcional com --arquivo)",
    )
    parser.add_argument("--modelo", help="ID do modelo no LM Studio (opcional)")
    parser.add_argument(
        "--lm-url",
        default="http://127.0.0.1:1234",
        help="URL base do LM Studio (padrão: http://127.0.0.1:1234)",
    )
    parser.add_argument("--workers", type=int, default=2, help="Threads paralelas (padrão: 2)")
    parser.add_argument("--batch-size", type=int, default=8, help="Linhas por lote (padrão: 8)")
    parser.add_argument(
        "--pular-existentes",
        action="store_true",
        help="Não reprocessa arquivo se a saída _PTBR já existir",
    )
    parser.add_argument(
        "--limpar-cache",
        action="store_true",
        help="Remove o cache de traduções antes de iniciar",
    )
    return parser.parse_args()


def formatar_eta(segundos_restantes: float) -> str:
    if segundos_restantes < 0 or segundos_restantes > 86400:
        return "?"
    m, s = divmod(int(segundos_restantes), 60)
    return f"{m}m{s:02d}s" if m else f"{s}s"


def executar_pipeline(args=None):
    if args is None:
        args = parse_args()

    log = GerenciadorLogs()
    pipe = None

    try:
        log.secao("PIPELINE INDUSTRIAL UNIFICADO — MACROSS II (EN -> PT-BR)")

        pipe = PipelineMacross2(
            log,
            modelo=args.modelo,
            max_workers=args.workers,
            batch_size=args.batch_size,
            lm_url=args.lm_url,
            limpar_cache=args.limpar_cache,
        )

        if not pipe.validar_conexao():
            log.erro("A conexão com o LM Studio local falhou. Abortando execução.")
            return

        log.secao("DIRETÓRIOS DE TRABALHO")

        caminho_padrao_origem = r"D:\PROJETOS-OPEN\animes\Macross II\legendas_eng"
        caminho_padrao_saida = r"D:\PROJETOS-OPEN\animes\Macross II\legendas_ptbr"

        pasta_saida = None
        jobs = []

        if args.arquivo:
            if args.saida:
                pasta_saida = normalizar_caminho(args.saida)
                os.makedirs(pasta_saida, exist_ok=True)
            for caminho in args.arquivo:
                try:
                    caminho_valido = validar_arquivo_legenda(caminho)
                except (FileNotFoundError, ValueError) as e:
                    log.erro(str(e))
                    return
                caminho_saida = resolver_caminho_saida(caminho_valido, pasta_saida)
                jobs.append((caminho_valido, caminho_saida))
            log.info(f"Modo arquivo: {len(jobs)} legenda(s) selecionada(s).")
            if pasta_saida:
                log.info(f"Pasta de saída: {pasta_saida}")
            else:
                log.info("Saída: mesma pasta de cada arquivo de entrada (_PTBR).")
        else:
            if args.entrada:
                pasta_entrada = normalizar_caminho(args.entrada)
                if not os.path.isdir(pasta_entrada):
                    log.erro(f"Pasta de entrada não existe: {pasta_entrada}")
                    return
            else:
                pasta_entrada = obter_diretorio_operador(
                    "Pasta com as legendas ENG (.ass / .srt)",
                    caminho_padrao_origem,
                )
            log.info(f"Pasta de entrada: {pasta_entrada}")

            if args.saida:
                pasta_saida = normalizar_caminho(args.saida)
            else:
                pasta_saida = obter_diretorio_operador(
                    "Pasta para as legendas PT-BR",
                    caminho_padrao_saida,
                )
            os.makedirs(pasta_saida, exist_ok=True)
            log.info(f"Pasta de saída: {pasta_saida}")

            for caminho_arq in listar_arquivos_legenda(pasta_entrada):
                caminho_saida = caminho_saida_relativo(pasta_entrada, caminho_arq, pasta_saida)
                jobs.append((caminho_arq, caminho_saida))

        if not jobs:
            log.erro("Nenhum arquivo de legenda (.ass ou .srt) para processar.")
            return

        log.info(f"Carregados {len(jobs)} arquivo(s) de legenda.")
        log.salvar_config(
            pipe.LM_URL,
            pipe.modelo_ativo,
            jobs[0][0] if args.arquivo else pasta_entrada,
            pasta_saida or os.path.dirname(jobs[0][1]),
            pipe.max_workers,
            pipe.batch_size,
        )

        tempo_inicio_global = time.time()
        pipe.stats['total_arquivos'] = len(jobs)
        pulados = 0

        log.secao("PROCESSANDO TRADUÇÃO EM LOTE")

        with tqdm(
            total=len(jobs),
            desc="Temporada Completa",
            unit="arq",
            colour="green",
            ncols=80,
            position=0,
        ) as barra_macro:
            for idx, (caminho_arq, caminho_saida) in enumerate(jobs, 1):
                nome_arq = os.path.basename(caminho_arq)
                pipe.arquivo_atual = nome_arq
                nome_saida = os.path.basename(caminho_saida)

                os.makedirs(os.path.dirname(caminho_saida) or ".", exist_ok=True)

                if args.pular_existentes and os.path.isfile(caminho_saida):
                    pulados += 1
                    tqdm.write(f"{Fore.CYAN}[{idx}/{len(jobs)}] Pulando (já existe): {nome_saida}")
                    barra_macro.update(1)
                    continue

                decorrido = time.time() - tempo_inicio_global
                processados = idx - 1 - pulados
                if processados > 0:
                    media = decorrido / processados
                    restantes = len(jobs) - idx + 1
                    eta = formatar_eta(media * restantes)
                    barra_macro.set_postfix_str(f"{nome_arq[:25]} ETA:{eta}")
                else:
                    barra_macro.set_postfix_str(nome_arq[:35])
                tqdm.write(f"\n{Fore.YELLOW}[{idx}/{len(jobs)}] -> Traduzindo: {nome_arq}")
                log.info(f"Entrada: {caminho_arq}")
                log.info(f"Saída  : {caminho_saida}")

                t_inicio_arq = time.time()

                if caminho_arq.lower().endswith('.ass'):
                    sucesso = pipe.processar_legenda_ass(caminho_arq, caminho_saida)
                else:
                    sucesso = pipe.processar_legenda_srt(caminho_arq, caminho_saida)

                t_elapsed_arq = time.time() - t_inicio_arq

                if sucesso:
                    tqdm.write(
                        f"{Fore.GREEN}  [CONCLUÍDO] {nome_saida} | Tempo: {t_elapsed_arq:.1f}s"
                    )
                else:
                    tqdm.write(f"{Fore.RED}  [FALHOU] Erro ao processar o arquivo: {nome_arq}")

                barra_macro.update(1)

        tempo_total = time.time() - tempo_inicio_global
        minutos, segundos = divmod(int(tempo_total), 60)

        log.secao("MÉTRICAS DA EXECUÇÃO")
        stats_relatorio = {
            'total_arquivos':    pipe.stats['total_arquivos'],
            'arquivos_salvos':   pipe.stats['traduzidos'],
            'arquivos_pulados':  pulados,
            'erros_arquivos':    pipe.stats['erros_traducao'],
            'linhas_com_erro':   pipe.stats['linhas_com_erro'],
            'dialogos_pulados':  pipe.stats['dialogos_pulados'],
            'cache_hits':        pipe.stats['cache_hits'],
            'linhas_traduzidas': pipe.stats['linhas_traduzidas'],
            'requisicoes_api':   pipe.stats['requisicoes'],
            'tempo_execucao':    f"{minutos}m {segundos}s",
        }
        log.salvar_stats(stats_relatorio)

        print("\n" + "=" * 80)
        print(f"{Fore.GREEN}✓ PROCESSAMENTO COMPLETO!")
        print(f"  Tempo Total: {minutos}m {segundos}s")
        print(f"  Arquivos Processados: {stats_relatorio['arquivos_salvos']}/{stats_relatorio['total_arquivos']}")
        if pulados:
            print(f"  Arquivos Pulados     : {pulados}")
        print(f"  Linhas Traduzidas   : {stats_relatorio['linhas_traduzidas']}")
        if stats_relatorio['linhas_com_erro']:
            print(f"  Linhas com Erro     : {stats_relatorio['linhas_com_erro']}")
        if stats_relatorio['dialogos_pulados']:
            print(f"  Diálogos Pulados    : {stats_relatorio['dialogos_pulados']}")
        print(f"  Cache Hits (Salvos) : {stats_relatorio['cache_hits']}")
        print(f"  Erros de Tradução   : {stats_relatorio['erros_arquivos']}")
        print(f"  Logs gravados na pasta: {log.pasta_logs}")
        print("=" * 80 + "\n")

    except KeyboardInterrupt:
        log.aviso("Interrompido pelo operador (Ctrl+C). Salvando cache parcial...")
        if pipe:
            pipe._salvar_cache()
    except Exception:
        log.erro("Falha crítica inesperada na execução do pipeline.")
        log.traceback_completo("executar_pipeline()")
        if pipe:
            pipe._salvar_cache()
    finally:
        if pipe:
            pipe._salvar_cache()
        log.fechar()


if __name__ == "__main__":
    executar_pipeline()
