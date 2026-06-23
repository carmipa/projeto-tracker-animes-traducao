#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tradutor EN -> PT-BR — Mobile Suit Gundam ZZ (Double Zeta)
Motor: Mistral Nemo Instruct via LM Studio (API local OpenAI-compatible).

Uso:
  python tradutor_mistral_gundam_zz.py
  python tradutor_mistral_gundam_zz.py --entrada PASTA_ENG --saida PASTA_PTBR
  python tradutor_mistral_gundam_zz.py --arquivo ep01.ass --saida PASTA_PTBR
  python tradutor_mistral_gundam_zz.py --modelo mistral-nemo --batch-size 12
"""

import os
import sys
import re
import json
import time
import argparse
import requests
import traceback
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto

try:
    from tqdm import tqdm
except ImportError:
    print("ERRO: tqdm não instalado. Execute: pip install tqdm")
    sys.exit(1)

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    print("ERRO: colorama não instalado. Execute: pip install colorama")
    sys.exit(1)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    except (OSError, ValueError):
        pass


# ============================================================================
# TEMPORIZADORES E FORMATAÇÃO
# ============================================================================
def formatar_tempo(segundos: float, com_ms: bool = False) -> str:
    """Converte segundos em string legível (ex: 2m 15s ou 45.3s)."""
    if segundos < 0:
        return "?"
    if com_ms and segundos < 60:
        return f"{segundos:.1f}s"
    total = int(segundos)
    h, resto = divmod(total, 3600)
    m, s = divmod(resto, 60)
    if h > 0:
        return f"{h}h {m}m {s}s"
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"


def formatar_eta(segundos: float) -> str:
    if segundos < 0 or segundos > 86400:
        return "?"
    return formatar_tempo(segundos)


class Cronometro:
    """Context manager com time.perf_counter()."""

    def __init__(self):
        self.inicio = 0.0
        self.elapsed = 0.0

    def __enter__(self):
        self.inicio = time.perf_counter()
        return self

    def __exit__(self, *_args):
        self.elapsed = time.perf_counter() - self.inicio


class AuditoriaTraducao:
    """Rastreia tempos, falhas e motivos de rejeição para log e tela."""

    def __init__(self, log: "GerenciadorLogs"):
        self.log = log
        self.falhas_por_motivo: dict[str, int] = defaultdict(int)
        self.rejeicoes_validacao: list[dict] = []
        self.falhas_definitivas: list[dict] = []
        self.tempos_api_seg: list[float] = []
        self.tempos_lote_seg: list[float] = []
        self.tempos_arquivo: list[dict] = []
        self.tempo_io_seg = 0.0
        self.tempo_parse_seg = 0.0
        self.retentativas_api = 0
        self.lotes_parciais = 0
        self.fallbacks_individuais = 0

    def registrar_rejeicao(
        self,
        arquivo: str,
        indice_lote: int,
        texto_en: str,
        motivo: str,
        fase: str = "validacao",
    ):
        self.falhas_por_motivo[motivo] += 1
        registro = {
            "arquivo": arquivo,
            "indice_lote": indice_lote,
            "fase": fase,
            "motivo": motivo,
            "texto_en": texto_en[:200],
        }
        self.rejeicoes_validacao.append(registro)
        self.log.registrar_falha_traducao(
            arquivo=arquivo,
            indice=indice_lote,
            texto_en=texto_en,
            motivo=motivo,
            fase=fase,
        )

    def registrar_falha_definitiva(
        self,
        arquivo: str,
        indice_lote: int,
        texto_en: str,
        motivo: str,
        tentativas: int = 0,
        tempo_seg: float = 0.0,
    ):
        chave = f"falha_definitiva:{motivo}"
        self.falhas_por_motivo[chave] += 1
        registro = {
            "arquivo": arquivo,
            "indice_lote": indice_lote,
            "motivo": motivo,
            "tentativas": tentativas,
            "tempo_seg": round(tempo_seg, 2),
            "texto_en": texto_en[:200],
        }
        self.falhas_definitivas.append(registro)
        self.log.registrar_falha_traducao(
            arquivo=arquivo,
            indice=indice_lote,
            texto_en=texto_en,
            motivo=motivo,
            fase="definitiva",
            tentativas=tentativas,
            tempo_seg=tempo_seg,
        )

    def registrar_tempo_api(self, duracao_seg: float):
        self.tempos_api_seg.append(duracao_seg)

    def registrar_tempo_lote(self, duracao_seg: float):
        self.tempos_lote_seg.append(duracao_seg)

    def registrar_arquivo(
        self,
        nome: str,
        duracao_seg: float,
        dialogos_novos: int,
        cache_hits: int,
        erros: int,
        ok: bool,
    ):
        self.tempos_arquivo.append({
            "arquivo": nome,
            "duracao_seg": round(duracao_seg, 2),
            "dialogos_novos": dialogos_novos,
            "cache_hits": cache_hits,
            "erros": erros,
            "ok": ok,
        })

    def media_api(self) -> float:
        return sum(self.tempos_api_seg) / len(self.tempos_api_seg) if self.tempos_api_seg else 0.0

    def media_lote(self) -> float:
        return sum(self.tempos_lote_seg) / len(self.tempos_lote_seg) if self.tempos_lote_seg else 0.0

    def resumo(self) -> dict:
        return {
            "tempo_total_api_seg": round(sum(self.tempos_api_seg), 2),
            "tempo_medio_api_seg": round(self.media_api(), 2),
            "tempo_medio_lote_seg": round(self.media_lote(), 2),
            "tempo_io_seg": round(self.tempo_io_seg, 2),
            "tempo_parse_seg": round(self.tempo_parse_seg, 2),
            "requisicoes_api": len(self.tempos_api_seg),
            "retentativas_api": self.retentativas_api,
            "lotes_parciais": self.lotes_parciais,
            "fallbacks_individuais": self.fallbacks_individuais,
            "rejeicoes_validacao": len(self.rejeicoes_validacao),
            "falhas_definitivas": len(self.falhas_definitivas),
            "falhas_por_motivo": dict(self.falhas_por_motivo),
            "tempos_por_arquivo": self.tempos_arquivo,
            "falhas_detalhadas": self.falhas_definitivas[:500],
        }


# ============================================================================
# GERENCIADOR DE LOGS
# ============================================================================
class GerenciadorLogs:
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
        self._handles = []

        for nome, sufixo in (
            ("pipeline", "pipeline_zz_en"),
            ("erros", "erros_zz_en"),
            ("falhas", "falhas_zz_en"),
        ):
            caminho = os.path.join(self.pasta_logs, f"{sufixo}_{self.ts}.txt")
            handle = open(caminho, 'w', encoding='utf-8')
            setattr(self, f"f_{nome}", handle)
            self._handles.append(handle)

        self.caminho_stats  = os.path.join(self.pasta_logs, f"stats_zz_en_{self.ts}.json")
        self.caminho_config = os.path.join(self.pasta_logs, f"config_zz_en_{self.ts}.txt")
        self.caminho_relatorio = os.path.join(self.pasta_logs, f"relatorio_zz_en_{self.ts}.txt")
        self._contador_falhas_tela = 0

        header = (
            f"\n{'='*80}\n"
            f"PIPELINE DE TRADUÇÃO GUNDAM ZZ / DOUBLE ZETA (EN -> PT-BR)\n"
            f"{'='*80}\n"
            f"Início    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Python    : {sys.version.split()[0]}\n"
            f"Pasta logs: {self.pasta_logs}\n"
            f"{'='*80}\n\n"
        )
        for h in self._handles:
            h.write(header)
            h.flush()

    def _gravar(self, nivel: str, mensagem: str):
        ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
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
    def info(self, msg):    self._gravar("INFO",    msg)
    def debug(self, msg):   self._gravar("DEBUG",   msg)
    def aviso(self, msg):   self._gravar("AVISO",   msg)
    def critico(self, msg): self._gravar("CRÍTICO", msg)

    def erro(self, msg, exc=None):
        self._gravar("ERRO", msg)
        if exc:
            self.f_erros.write(f"  Exceção: {exc}\n")
            self.f_erros.flush()

    def traceback_completo(self, contexto: str = ""):
        tb = traceback.format_exc()
        bloco = (
            f"\n{'='*80}\nTRACEBACK COMPLETO\n{'='*80}\n"
            f"Contexto : {contexto}\n\n{tb}\n{'-'*80}\n\n"
        )
        self.f_erros.write(bloco)
        self.f_erros.flush()
        print(f"{Fore.RED}{tb}{Style.RESET_ALL}")

    def salvar_config(self, **kwargs):
        linhas = [
            f"\n{'='*80}\nCONFIGURAÇÃO DA EXECUÇÃO\n{'='*80}\n",
            f"Data/Hora : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        ]
        for chave, valor in kwargs.items():
            linhas.append(f"{chave:16s}: {valor}\n")
        with open(self.caminho_config, 'w', encoding='utf-8') as f:
            f.writelines(linhas)

    def registrar_falha_traducao(
        self,
        arquivo: str,
        indice: int,
        texto_en: str,
        motivo: str,
        fase: str = "validacao",
        tentativas: int = 0,
        tempo_seg: float = 0.0,
    ):
        ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        tempo_txt = f" | tempo={formatar_tempo(tempo_seg, com_ms=True)}" if tempo_seg else ""
        tent_txt = f" | tentativas={tentativas}" if tentativas else ""
        linha = (
            f"[{ts}] [{fase.upper():10s}] {arquivo} | idx={indice} | {motivo}"
            f"{tent_txt}{tempo_txt}\n"
            f"  EN: {texto_en[:180]}\n"
        )
        self.f_falhas.write(linha)
        self.f_falhas.flush()
        self.f_pipeline.write(linha)
        self.f_pipeline.flush()

        if fase == "definitiva":
            self.f_erros.write(linha)
            self.f_erros.flush()
            self._contador_falhas_tela += 1
            try:
                tqdm.write(
                    f"{Fore.RED}  ✗ NÃO TRADUZIU [{arquivo}] L{indice} | {motivo}"
                    f"{tent_txt}{tempo_txt}{Style.RESET_ALL}\n"
                    f"{Fore.YELLOW}    EN: {texto_en[:100]}{'...' if len(texto_en) > 100 else ''}{Style.RESET_ALL}"
                )
            except Exception:
                print(linha)

    def status_dinamico(self, mensagem: str):
        """Atualização dinâmica na tela (via tqdm.write, não polui o arquivo)."""
        try:
            tqdm.write(f"{Fore.CYAN}  ▸ {mensagem}{Style.RESET_ALL}")
        except Exception:
            print(mensagem)

    def relatorio_final(self, stats: dict, auditoria: dict, tempo_total_fmt: str):
        corpo = (
            f"\n{'='*80}\nRELATÓRIO FINAL — GUNDAM ZZ (EN -> PT-BR)\n{'='*80}\n\n"
            f"Tempo total de execução : {tempo_total_fmt}\n"
            f"Arquivos processados    : {stats.get('ass_ok', 0)}/{stats.get('ass_total', 0)}\n"
            f"Arquivos com falha      : {stats.get('ass_falha', 0)}\n"
            f"Arquivos pulados        : {stats.get('ass_pulados', 0)}\n"
            f"Linhas traduzidas       : {stats.get('linhas_traduzidas', 0)}\n"
            f"Linhas com erro         : {stats.get('linhas_com_erro', 0)}\n"
            f"Cache hits              : {stats.get('cache_hits', 0)}\n"
            f"Diálogos pulados        : {stats.get('dialogos_pulados', 0)}\n"
            f"Requisições API         : {stats.get('requisicoes', 0)}\n\n"
            f"--- TEMPOS ---\n"
            f"Tempo total em API      : {formatar_tempo(auditoria.get('tempo_total_api_seg', 0))}\n"
            f"Média por requisição    : {formatar_tempo(auditoria.get('tempo_medio_api_seg', 0), com_ms=True)}\n"
            f"Média por lote          : {formatar_tempo(auditoria.get('tempo_medio_lote_seg', 0), com_ms=True)}\n"
            f"Tempo I/O (leitura/grav) : {formatar_tempo(auditoria.get('tempo_io_seg', 0))}\n"
            f"Retentativas API        : {auditoria.get('retentativas_api', 0)}\n"
            f"Lotes parciais          : {auditoria.get('lotes_parciais', 0)}\n"
            f"Fallbacks individuais   : {auditoria.get('fallbacks_individuais', 0)}\n"
            f"Rejeições validação     : {auditoria.get('rejeicoes_validacao', 0)}\n"
            f"Falhas definitivas      : {auditoria.get('falhas_definitivas', 0)}\n\n"
        )
        falhas_motivo = auditoria.get('falhas_por_motivo', {})
        if falhas_motivo:
            corpo += "--- FALHAS POR MOTIVO ---\n"
            for motivo, qtd in sorted(falhas_motivo.items(), key=lambda x: -x[1]):
                corpo += f"  {qtd:4d}x  {motivo}\n"
            corpo += "\n"

        tempos_arq = auditoria.get('tempos_por_arquivo', [])
        if tempos_arq:
            corpo += "--- TEMPO POR ARQUIVO ---\n"
            for item in tempos_arq:
                status = "OK" if item.get('ok') else "FALHOU"
                corpo += (
                    f"  {item['arquivo']}: {formatar_tempo(item['duracao_seg'])} | "
                    f"novos={item['dialogos_novos']} cache={item['cache_hits']} "
                    f"erros={item['erros']} [{status}]\n"
                )
            corpo += "\n"

        falhas_det = auditoria.get('falhas_detalhadas', [])
        if falhas_det:
            corpo += "--- LINHAS NÃO TRADUZIDAS (amostra) ---\n"
            for f in falhas_det[:30]:
                corpo += (
                    f"  {f['arquivo']} | L{f['indice_lote']} | {f['motivo']}\n"
                    f"    EN: {f['texto_en'][:120]}\n"
                )
            if len(falhas_det) > 30:
                corpo += f"  ... e mais {len(falhas_det) - 30} falha(s) em falhas_zz_en_{self.ts}.txt\n"
            corpo += "\n"

        corpo += (
            f"Arquivos de log:\n"
            f"  {self.pasta_logs}\n"
            f"  pipeline_zz_en_{self.ts}.txt\n"
            f"  erros_zz_en_{self.ts}.txt\n"
            f"  falhas_zz_en_{self.ts}.txt\n"
            f"  stats_zz_en_{self.ts}.json\n"
            f"  relatorio_zz_en_{self.ts}.txt\n"
        )
        self.f_pipeline.write(corpo)
        self.f_pipeline.flush()
        with open(self.caminho_relatorio, 'w', encoding='utf-8') as f:
            f.write(corpo)
        print(corpo)

    def salvar_stats(self, stats: dict, auditoria: dict | None = None):
        payload = {
            "timestamp": self.ts,
            "data_hora": datetime.now().isoformat(),
            "stats": stats,
            "auditoria": auditoria or {},
        }
        with open(self.caminho_stats, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    def fechar(self):
        for h in self._handles:
            h.close()
        print(f"\n{Fore.GREEN}Logs salvos em: {self.pasta_logs}{Style.RESET_ALL}\n")

    def espelhar_relatorio_na_saida(self, pasta_saida: str):
        """Vault Sidonia: cópia do relatório na pasta de legendas traduzidas."""
        if not pasta_saida or not os.path.isdir(pasta_saida):
            return
        if not os.path.isfile(self.caminho_relatorio):
            return
        destino = os.path.join(pasta_saida, f"relatorio_traducao_zz_{self.ts}.txt")
        try:
            with open(self.caminho_relatorio, 'r', encoding='utf-8') as origem:
                with open(destino, 'w', encoding='utf-8') as saida:
                    saida.write(origem.read())
            self.info(f"Relatório espelhado em: {destino}")
        except OSError as e:
            self.aviso(f"Não foi possível espelhar relatório na saída: {e}")


class LmStudioIndisponivel(RuntimeError):
    """LM Studio caiu ou recusou conexão repetidamente — abortar como no módulo de reparo."""


@dataclass(frozen=True)
class ConfiguracaoZZ:
    """Parâmetros imutáveis do pipeline Gundam ZZ."""

    lm_url_padrao: str = "http://127.0.0.1:1234"
    max_ass_bytes: int = 8 * 1024 * 1024
    max_linha_dialog: int = 2000
    max_tags_por_dialog: int = 12
    pasta_saida_padrao: str = "TRADUZIDAS_ZZ"
    pasta_anime_padrao: str = r"C:\animes\Gundam_ZZ\legendas_eng"
    pastas_ignorar: frozenset = frozenset({"logs", "traduzidas_zz"})
    encodings_fallback: tuple = ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1')
    backoff_rede_seg: tuple = (5, 10, 15)
    backoff_lm_offline_seg: tuple = (20, 40, 60)
    max_tentativas_api: int = 4
    limite_falhas_consecutivas_api: int = 5
    cor_lm_offline: str = "\033[38;5;208m"
    batch_size_padrao: int = 15
    nome_cache: str = "traducao_cache_zz_en.json"

    @property
    def padrao_dialogue(self) -> re.Pattern:
        return re.compile(r"^(Dialogue:\s*[^,]*(?:,[^,]*){8},)(.*)$")


CONFIG = ConfiguracaoZZ()

# Aliases legados (compatibilidade interna)
MAX_ASS_BYTES = CONFIG.max_ass_bytes
MAX_LINHA_DIALOG = CONFIG.max_linha_dialog
MAX_TAGS_POR_DIALOG = CONFIG.max_tags_por_dialog
PASTA_SAIDA_PADRAO = CONFIG.pasta_saida_padrao
PASTA_ANIME_PADRAO = CONFIG.pasta_anime_padrao
PASTAS_IGNORAR = CONFIG.pastas_ignorar
ENCODINGS_FALLBACK = CONFIG.encodings_fallback
BACKOFF_REDE_SEG = CONFIG.backoff_rede_seg
BACKOFF_LM_OFFLINE_SEG = CONFIG.backoff_lm_offline_seg
MAX_TENTATIVAS_API = CONFIG.max_tentativas_api
LIMITE_FALHAS_CONSECUTIVAS_API = CONFIG.limite_falhas_consecutivas_api
COR_LM_OFFLINE = CONFIG.cor_lm_offline


class TipoLinhaAss(Enum):
    MANTER = auto()
    CACHE = auto()
    PENDENTE = auto()


@dataclass
class DialogoLegenda:
    """Um diálogo ASS mapeado para tradução."""

    indice_arquivo: int
    tipo: TipoLinhaAss
    prefixo: str = ""
    texto_original: str = ""
    texto_mascarado: str = ""
    tags: list = field(default_factory=list)
    linha_bruta: str = ""


@dataclass
class EstatisticasPipeline:
    """Contadores da execução — encapsulados em vez de dict solto."""

    ass_total: int = 0
    ass_ok: int = 0
    ass_falha: int = 0
    ass_pulados: int = 0
    linhas_traduzidas: int = 0
    linhas_com_erro: int = 0
    erros_traducao: int = 0
    cache_hits: int = 0
    requisicoes: int = 0
    dialogos_pulados: int = 0
    tempo_inicio: float = field(default_factory=time.perf_counter)
    abortado_lm_offline: bool = False

    def como_dict(self) -> dict:
        return {
            'ass_total': self.ass_total,
            'ass_ok': self.ass_ok,
            'ass_falha': self.ass_falha,
            'ass_pulados': self.ass_pulados,
            'linhas_traduzidas': self.linhas_traduzidas,
            'linhas_com_erro': self.linhas_com_erro,
            'erros_traducao': self.erros_traducao,
            'cache_hits': self.cache_hits,
            'requisicoes': self.requisicoes,
            'dialogos_pulados': self.dialogos_pulados,
            'tempo_inicio': self.tempo_inicio,
            'abortado_lm_offline': self.abortado_lm_offline,
        }


def normalizar_caminho(caminho: str) -> str:
    if not caminho:
        return ""
    caminho = caminho.strip().strip('"').strip("'")
    if "\0" in caminho:
        raise ValueError("Caminho inválido: contém caractere nulo.")
    return os.path.abspath(os.path.normpath(caminho))


def caminho_dentro_de(base: str, alvo: str) -> bool:
    base_abs = os.path.normcase(os.path.abspath(os.path.normpath(base)))
    alvo_abs = os.path.normcase(os.path.abspath(os.path.normpath(alvo)))
    try:
        return os.path.commonpath([base_abs, alvo_abs]) == base_abs
    except ValueError:
        return False


def validar_pasta(caminho: str, rotulo: str = "Pasta") -> str:
    caminho_abs = normalizar_caminho(caminho)
    if not caminho_abs:
        raise ValueError(f"{rotulo}: caminho vazio.")
    if not os.path.isdir(caminho_abs):
        raise ValueError(f"{rotulo} não encontrada: {caminho_abs}")
    return caminho_abs


def validar_arquivo_ass(caminho: str) -> str:
    caminho_abs = normalizar_caminho(caminho)
    if not os.path.isfile(caminho_abs):
        raise ValueError(f"Arquivo não encontrado: {caminho_abs}")
    if not caminho_abs.lower().endswith(".ass"):
        raise ValueError(f"Extensão inválida (use .ass): {caminho_abs}")
    if os.path.getsize(caminho_abs) > MAX_ASS_BYTES:
        raise ValueError(f"Arquivo acima do limite de 8 MB: {caminho_abs}")
    return caminho_abs


def gravar_arquivo_atomico(caminho: str, linhas: list):
    caminho_tmp = caminho + ".tmp"
    with open(caminho_tmp, "w", encoding="utf-8-sig") as f:
        f.writelines(linhas)
    os.replace(caminho_tmp, caminho)


def ler_arquivo_com_encoding(caminho: str, log: GerenciadorLogs):
    for enc in ENCODINGS_FALLBACK:
        try:
            with open(caminho, 'r', encoding=enc) as f:
                return f.readlines(), enc
        except UnicodeDecodeError:
            continue
    log.aviso(f"Encodings falharam em {caminho}. Usando utf-8 com replace.")
    with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
        return f.readlines(), 'utf-8-bypass'


def listar_arquivos_ass(pasta_entrada: str) -> list[str]:
    pasta_entrada = validar_pasta(pasta_entrada, "Pasta origem")
    arquivos = []
    vistos = set()
    for dirpath, dirnames, filenames in os.walk(pasta_entrada):
        dirnames[:] = [
            d for d in dirnames
            if d.lower() not in PASTAS_IGNORAR
        ]
        if not caminho_dentro_de(pasta_entrada, dirpath):
            continue
        for nome in filenames:
            if not nome.lower().endswith(".ass"):
                continue
            caminho = os.path.join(dirpath, nome)
            if not caminho_dentro_de(pasta_entrada, caminho):
                continue
            chave = os.path.normcase(caminho)
            if chave not in vistos:
                vistos.add(chave)
                arquivos.append(caminho)
    return sorted(arquivos)


def nome_saida_ptbr(nome_arq: str) -> str:
    """Gera nome PT-BR sem sobrescrever o arquivo ENG quando a saída for irmã."""
    base, ext = os.path.splitext(nome_arq)
    if "_PTBR" in base.upper():
        return nome_arq
    for sufixo in ("_ENG", "_eng", ".ENG", ".eng"):
        if base.endswith(sufixo):
            return base[:-len(sufixo)] + "_PTBR" + ext
    return f"{base}_PTBR{ext}"


def caminho_saida_relativo(pasta_entrada: str, caminho_arq: str, pasta_saida: str) -> str:
    """Espelha subpastas da entrada na saída e aplica sufixo _PTBR."""
    pasta_entrada_abs = os.path.abspath(os.path.normpath(pasta_entrada))
    caminho_arq_abs = os.path.abspath(os.path.normpath(caminho_arq))
    pasta_saida_abs = os.path.abspath(os.path.normpath(pasta_saida))
    rel_dir = os.path.relpath(os.path.dirname(caminho_arq_abs), pasta_entrada_abs)
    destino_dir = pasta_saida_abs if rel_dir == "." else os.path.join(pasta_saida_abs, rel_dir)
    return os.path.join(destino_dir, nome_saida_ptbr(os.path.basename(caminho_arq_abs)))


# ============================================================================
# VALIDAÇÃO E LORE ZZ
# ============================================================================
class ValidadorTraducaoZZ:
    """Validação anti-alucinação e pós-processamento de lore ZZ."""

    PADRAO_RESIDUO_INGLES = re.compile(
        r"\b(you|your|they|them|without|very|where|what|when|why|who|"
        r"are|was|were|will|would|could|should|this|that|these|those|"
        r"the|there|here|then|with|about|have|has|had)\b",
        re.IGNORECASE,
    )
    PADRAO_PREAMBULO_LLM = re.compile(
        r"^(esta [ée] a tradu|segue|abaixo est[áa]|abaixo seguem|claro,?\s+vou|"
        r"aqui est[áa] a|here is|translation:|note:)\b",
        re.IGNORECASE,
    )
    SUBSTITUICOES_POS = [
        # Facções, organizações e lugares
        (re.compile(r"\bNova Zeon\b", re.I), "Neo Zeon"),
        (re.compile(r"\bNovo Zeon\b", re.I), "Neo Zeon"),
        (re.compile(r"\bZeon Nova\b", re.I), "Neo Zeon"),
        (re.compile(r"\bZeon Novo\b", re.I), "Neo Zeon"),
        (re.compile(r"\bA\.E\.U\.G\b", re.I), "A.E.U.G."),
        (re.compile(r"\bAEUG\b", re.I), "A.E.U.G."),
        (re.compile(r"\bEletrônica Anaheim\b", re.I), "Anaheim Electronics"),
        (re.compile(r"\bEletrônicos Anaheim\b", re.I), "Anaheim Electronics"),
        (re.compile(r"\bShangri-la\b", re.I), "Shangri-La"),
        (re.compile(r"\bLua-Lua\b", re.I), "Moon-Moon"),
        (re.compile(r"\bMundo da Lua\b", re.I), "Moon-Moon"),
        (re.compile(r"\bO Eixo\b", re.I), "Axis"),
        (re.compile(r"\bdo Eixo\b", re.I), "de Axis"),
        (re.compile(r"\bno Eixo\b", re.I), "em Axis"),
        (re.compile(r"\bao Eixo\b", re.I), "a Axis"),

        # Personagens A.E.U.G. e aliados
        (re.compile(r"\bJudau\s+Asta\b", re.I), "Judau Ashta"),
        (re.compile(r"\bRu\s+Luka\b", re.I), "Roux Louka"),
        (re.compile(r"\bRoux\s+Luka\b", re.I), "Roux Louka"),
        (re.compile(r"\bBicha\s+Oleg\b", re.I), "Beecha Oleg"),
        (re.compile(r"\bIno\s+Abav\b", re.I), "Iino Abbav"),
        (re.compile(r"\bIino\s+Abav\b", re.I), "Iino Abbav"),
        (re.compile(r"\bMondo\s+Akage\b", re.I), "Mondo Agake"),
        (re.compile(r"\bElle\s+Viano\b", re.I), "Elle Vianno"),
        (re.compile(r"\bBrilhante\s+Noa\b", re.I), "Bright Noa"),
        (re.compile(r"\bCamille\s+Bidan\b", re.I), "Kamille Bidan"),

        # Personagens Neo Zeon
        (re.compile(r"\bHaman\s+Kan\b", re.I), "Haman Karn"),
        (re.compile(r"\bHaman\s+Khan\b", re.I), "Haman Karn"),
        (re.compile(r"\bSenhorita\s+Haman\b", re.I), "Lady Haman"),
        (re.compile(r"\bMashimar\b", re.I), "Mashymre"),
        (re.compile(r"\bMashymre\s+Cello\b", re.I), "Mashymre Cello"),
        (re.compile(r"\bChara\s+Sun\b", re.I), "Chara Soon"),
        (re.compile(r"\bGlemi\s+Toto\b", re.I), "Glemy Toto"),
        (re.compile(r"\bGlemmy\s+Toto\b", re.I), "Glemy Toto"),
        (re.compile(r"\bPuru\s+Two\b", re.I), "Ple Two"),
        (re.compile(r"\bPuru\s+Dois\b", re.I), "Ple Two"),
        (re.compile(r"\bElpeo\s+Puru\b", re.I), "Elpeo Ple"),

        # Mecha, naves e equipamentos
        (re.compile(r"\bZeta\s+Duplo\b", re.I), "Double Zeta"),
        (re.compile(r"\bZZ\s+Gundam\b", re.I), "ZZ Gundam"),
        (re.compile(r"\bCem\s+Estilos\b", re.I), "Hyaku Shiki"),
        (re.compile(r"\bMarca\s+Dois\b", re.I), "Mk-II"),
        (re.compile(r"\bRainha\s+Mansa\b", re.I), "Quin Mantha"),
        (re.compile(r"\bQueen\s+Mansa\b", re.I), "Quin Mantha"),
        (re.compile(r"\bQuin\s+Mansa\b", re.I), "Quin Mantha"),
        (re.compile(r"\bQuebeley\b", re.I), "Qubeley"),
        (re.compile(r"\bDöven\s+Wolf\b", re.I), "Doven Wolf"),
        (re.compile(r"\bLobo\s+Doven\b", re.I), "Doven Wolf"),
        (re.compile(r"\bTopo do Núcleo\b", re.I), "Core Top"),
        (re.compile(r"\bBase do Núcleo\b", re.I), "Core Base"),
        (re.compile(r"\bLutador do Núcleo\b", re.I), "Core Fighter"),
        (re.compile(r"\bCaça do Núcleo\b", re.I), "Core Fighter"),
        (re.compile(r"\bCavaleiro Mega\b", re.I), "Mega Rider"),

        # Calques frequentes do inglês
        (re.compile(r"\bEu vejo\.", re.I), "Entendo."),
        (re.compile(r"\bOlhe fora!\b", re.I), "Cuidado!"),
        (re.compile(r"\bOlha fora!\b", re.I), "Cuidado!"),
        (re.compile(r"\bDe nenhuma maneira\b", re.I), "De jeito nenhum"),
        (re.compile(r"\bRoger that\b", re.I), "Entendido"),
        (re.compile(r"\bCopy that\b", re.I), "Entendido"),
    ]

    @classmethod
    def limpar_saida(cls, texto: str) -> str:
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
        texto = re.sub(r"\.{4,}", "...", texto)
        texto = re.sub(r"(?<!\.)\.\.(?!\.)", "...", texto)
        texto = re.sub(r"\[T\s*(\d+)\]", r"[T\1]", texto)
        texto = re.sub(r"\bÉPISODE\b", "EPISÓDIO", texto, flags=re.I)
        texto = re.sub(r"\bEPISODE\b", "EPISÓDIO", texto, flags=re.I)
        texto = re.sub(r"^(tradução revisada|tradução|translation)\s*:\s*", "", texto, flags=re.I)
        for padrao, substituto in cls.SUBSTITUICOES_POS:
            texto = padrao.sub(substituto, texto)
        return texto

    @classmethod
    def valida_tags(cls, original: str, traduzido: str) -> tuple[bool, str]:
        tags_orig = re.findall(r'(\\[Nn]|{\\[^}]+}|\[T\d+\])', original)
        tags_trad = re.findall(r'(\\[Nn]|{\\[^}]+}|\[T\d+\])', traduzido)
        if sorted(tags_orig) != sorted(tags_trad):
            return False, f"Tags desalinhadas: {tags_orig} vs {tags_trad}"
        return True, "OK"

    @classmethod
    def validar(cls, original: str, traducao: str) -> tuple[bool, str]:
        if not traducao or "[ERRO_TRADUCAO" in traducao:
            return False, "Tradução vazia ou marcador de erro"
        if cls.PADRAO_PREAMBULO_LLM.match(traducao.strip()):
            return False, "Preâmbulo conversacional do LLM"

        orig_words = set(re.findall(r'\b\w+\b', original.lower()))
        for residuo in cls.PADRAO_RESIDUO_INGLES.findall(traducao):
            if residuo.lower() not in orig_words:
                return False, f"Resíduo de inglês não presente no original: '{residuo}'"

        if len(traducao) > max(250, len(original) * 8):
            return False, "Tradução longa demais (possível alucinação)"

        return cls.valida_tags(original, traducao)
# Aliases legados para reparo/import externo
PADRAO_RESIDUO_INGLES = ValidadorTraducaoZZ.PADRAO_RESIDUO_INGLES
PADRAO_PREAMBULO_LLM = ValidadorTraducaoZZ.PADRAO_PREAMBULO_LLM
SUBSTITUICOES_POS_PROCESSAMENTO = ValidadorTraducaoZZ.SUBSTITUICOES_POS


def valida_estrutura_tags(original: str, traduzido: str) -> tuple[bool, str]:
    return ValidadorTraducaoZZ.valida_tags(original, traduzido)
class MascadorTagsAss:
    """Esconde tags ASS complexas sob marcadores [Tn] para o LLM."""

    @staticmethod
    def mascarar(texto_bruto: str) -> tuple[str, list]:
        tags = re.findall(r'\{[^}]+\}', texto_bruto)
        limpo = texto_bruto
        for i, tag in enumerate(tags):
            limpo = limpo.replace(tag, f"[T{i}]", 1)
        return limpo, tags

    @staticmethod
    def restaurar(traduzido: str, tags: list) -> str:
        for i, tag in enumerate(tags):
            marcador = f"[T{i}]"
            if marcador in traduzido:
                traduzido = traduzido.replace(marcador, tag, 1)
            elif tag not in traduzido:
                traduzido = re.sub(
                    rf'\[?[Tt]\s*{i}\]?',
                    lambda _m, t=tag: t,
                    traduzido,
                    count=1,
                )
        return traduzido


class RepositorioCache:
    """Cache persistente com gravação atômica."""

    def __init__(self, caminho: str, log: GerenciadorLogs, limpar: bool = False):
        self.caminho = caminho
        self.log = log
        self._dados: dict[str, str] = {}
        if limpar and os.path.exists(caminho):
            os.remove(caminho)
            self.log.aviso("Cache anterior removido (--limpar-cache).")
        self.carregar()

    def __contains__(self, chave: str) -> bool:
        return chave in self._dados

    def get(self, chave: str) -> str | None:
        return self._dados.get(chave)

    def set(self, chave: str, valor: str):
        if chave and "[ERRO_TRADUCAO" not in valor:
            self._dados[chave] = valor

    def carregar(self):
        if not os.path.exists(self.caminho):
            self._dados = {}
            return
        try:
            with open(self.caminho, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            if not isinstance(dados, dict):
                raise ValueError("cache não é um objeto JSON")
            self._dados = dados
            self.log.info(f"Cache carregado: {len(self._dados)} itens.")
        except Exception as e:
            self.log.aviso(f"Cache inválido, iniciando vazio: {e}")
            self._dados = {}

    def salvar(self):
        try:
            caminho_tmp = self.caminho + ".tmp"
            with open(caminho_tmp, 'w', encoding='utf-8') as f:
                json.dump(self._dados, f, indent=2, ensure_ascii=False)
            os.replace(caminho_tmp, self.caminho)
        except Exception as e:
            self.log.aviso(f"Erro ao salvar cache: {e}")


class LeitorAssZZ:
    """Leitura e parsing de arquivos .ass."""

    def __init__(self, log: GerenciadorLogs, config: ConfiguracaoZZ = CONFIG):
        self.log = log
        self.config = config

    def ler_linhas(self, caminho: str) -> tuple[list[str], str]:
        for enc in self.config.encodings_fallback:
            try:
                with open(caminho, 'r', encoding=enc) as f:
                    return f.readlines(), enc
            except UnicodeDecodeError:
                continue
        self.log.aviso(f"Encodings falharam em {caminho}. Usando utf-8 com replace.")
        with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
            return f.readlines(), 'utf-8-bypass'

    def extrair_dialogos(
        self,
        linhas_ass: list[str],
        cache: RepositorioCache,
        stats: EstatisticasPipeline,
    ) -> list[DialogoLegenda]:
        resultado: list[DialogoLegenda] = []
        pat = self.config.padrao_dialogue

        for idx_linha, linha in enumerate(linhas_ass):
            linha_strip = linha.strip()
            if len(linha_strip) > self.config.max_linha_dialog:
                resultado.append(DialogoLegenda(idx_linha, TipoLinhaAss.MANTER, linha_bruta=linha))
                continue

            match = pat.match(linha_strip)
            if not match:
                resultado.append(DialogoLegenda(idx_linha, TipoLinhaAss.MANTER, linha_bruta=linha))
                continue

            prefixo = match.group(1)
            texto = match.group(2).strip()
            if not texto:
                resultado.append(DialogoLegenda(idx_linha, TipoLinhaAss.MANTER, linha_bruta=linha))
                continue

            if not re.sub(r'\{.*?\}', '', texto).strip():
                resultado.append(DialogoLegenda(idx_linha, TipoLinhaAss.MANTER, linha_bruta=linha))
                continue

            if any(m in texto for m in (r'\font', r'\image', '0x', '\x00')):
                stats.dialogos_pulados += 1
                resultado.append(DialogoLegenda(idx_linha, TipoLinhaAss.MANTER, linha_bruta=linha))
                continue

            texto_mascarado, tags = MascadorTagsAss.mascarar(texto)
            if len(tags) > self.config.max_tags_por_dialog:
                stats.dialogos_pulados += 1
                self.log.debug(f"Diálogo ignorado (>{self.config.max_tags_por_dialog} tags): {texto[:50]}...")
                resultado.append(DialogoLegenda(idx_linha, TipoLinhaAss.MANTER, linha_bruta=linha))
                continue

            if texto_mascarado in cache:
                stats.cache_hits += 1
                tipo = TipoLinhaAss.CACHE
            else:
                tipo = TipoLinhaAss.PENDENTE

            resultado.append(DialogoLegenda(
                indice_arquivo=idx_linha,
                tipo=tipo,
                prefixo=prefixo,
                texto_original=texto,
                texto_mascarado=texto_mascarado,
                tags=tags,
                linha_bruta=linha,
            ))
        return resultado

    @staticmethod
    def montar_saida(
        dialogos: list[DialogoLegenda],
        cache: RepositorioCache,
        traducoes: dict[int, str],
    ) -> list[str]:
        linhas: list[str] = []
        for dlg in dialogos:
            if dlg.tipo == TipoLinhaAss.MANTER:
                bruta = dlg.linha_bruta
                linhas.append(bruta if bruta.endswith('\n') else bruta + '\n')
                continue

            if dlg.tipo == TipoLinhaAss.CACHE:
                texto_pt = cache.get(dlg.texto_mascarado) or dlg.texto_mascarado
            else:
                texto_pt = traducoes.get(
                    dlg.indice_arquivo,
                    f"[ERRO_TRADUCAO: {dlg.texto_mascarado}]",
                )

            restaurado = MascadorTagsAss.restaurar(texto_pt, dlg.tags)
            linhas.append(f"{dlg.prefixo}{restaurado}\n")
        return linhas


# ============================================================================
# PIPELINE MISTRAL NEMO — GUNDAM ZZ
# ============================================================================
class ClienteLmStudio:
    """Cliente HTTP para LM Studio com retentativas e parse de respostas."""

    def __init__(
        self,
        log: GerenciadorLogs,
        auditoria: AuditoriaTraducao,
        stats: EstatisticasPipeline,
        prompt_sistema: str,
        lm_url: str,
        modelo: str,
        config: ConfiguracaoZZ = CONFIG,
    ):
        self.log = log
        self.auditoria = auditoria
        self.stats = stats
        self.prompt_sistema = prompt_sistema
        self.lm_url = lm_url.rstrip("/")
        self.api_url = f"{self.lm_url}/v1/chat/completions"
        self.modelo = modelo
        self.config = config
        self.arquivo_atual = ""
        self.falhas_consecutivas = 0
        self.abortar = False

    def validar_conexao(self) -> bool:
        self.log.info(f"Testando LM Studio em {self.lm_url}...")
        try:
            r = requests.get(f"{self.lm_url}/v1/models", timeout=5)
            if r.status_code != 200:
                self.log.erro(f"LM Studio HTTP {r.status_code}")
                return False
            modelos = r.json().get('data', [])
            if not modelos:
                self.log.erro("LM Studio online mas sem modelo carregado.")
                return False
            ids = [m.get('id', '') for m in modelos]
            if self.modelo == "local-model":
                self.modelo = modelos[0].get('id', 'local-model')
            elif self.modelo not in ids:
                self.log.aviso(f"Modelo '{self.modelo}' não encontrado. Usando: {modelos[0].get('id')}")
                self.modelo = modelos[0].get('id', 'local-model')
            self.log.sucesso(f"LM Studio OK. Modelo: {self.modelo}")
            return True
        except requests.exceptions.ConnectionError:
            self.log.erro(f"LM Studio inacessível em {self.lm_url}. Verifique se o servidor local está ativo.")
            return False
        except (requests.RequestException, ValueError, KeyError) as e:
            self.log.erro(f"Falha ao validar LM Studio: {e}")
            return False

    def _registrar_falha_api(self, motivo: str, linhas: list, fase: str):
        self.falhas_consecutivas += 1
        for i, texto in enumerate(linhas):
            self.auditoria.registrar_rejeicao(self.arquivo_atual, i, texto, motivo, fase=fase)
        if self.falhas_consecutivas >= self.config.limite_falhas_consecutivas_api:
            self.abortar = True
            self.stats.abortado_lm_offline = True
            raise LmStudioIndisponivel(
                f"{self.falhas_consecutivas} falhas consecutivas de API ({motivo}). "
                "LM Studio pode ter caído — abortando."
            )

    def _parse_resposta(self, bruto: str, linhas: list) -> dict[int, str]:
        with Cronometro() as cron:
            traduzidas: dict[int, str] = {}
            for idx_str, texto in re.findall(r"\[(\d+)\]\s*(.*?)(?=\[\d+\]|$)", bruto, re.DOTALL):
                idx = int(idx_str)
                if 0 <= idx < len(linhas):
                    limpo = ValidadorTraducaoZZ.limpar_saida(texto)
                    valido, motivo = ValidadorTraducaoZZ.validar(linhas[idx], limpo)
                    if valido:
                        traduzidas[idx] = limpo
                    else:
                        self.auditoria.registrar_rejeicao(self.arquivo_atual, idx, linhas[idx], motivo)

            if not traduzidas:
                for i, linha in enumerate(bruto.splitlines()[:len(linhas)]):
                    linha_limpa = re.sub(r"^\[?\d+\]?[.)\s-]*", "", linha.strip()).strip()
                    limpo = ValidadorTraducaoZZ.limpar_saida(linha_limpa)
                    if limpo:
                        valido, motivo = ValidadorTraducaoZZ.validar(linhas[i], limpo)
                        if valido:
                            traduzidas[i] = limpo
                        else:
                            self.auditoria.registrar_rejeicao(self.arquivo_atual, i, linhas[i], motivo)
        self.auditoria.tempo_parse_seg += cron.elapsed
        return traduzidas

    def traduzir_lote(self, linhas: list, tentativa: int = 1) -> dict[int, str]:
        if self.abortar:
            return {}

        payload = "\n".join(f"[{i}] {t}" for i, t in enumerate(linhas))
        corpo = {
            "model": self.modelo,
            "messages": [
                {"role": "system", "content": self.prompt_sistema},
                {
                    "role": "user",
                    "content": (
                        f"Translate exactly these {len(linhas)} numbered lines from English "
                        f"to Brazilian Portuguese.\n"
                        f"Return exactly {len(linhas)} lines with indices [0]..[{len(linhas) - 1}].\n"
                        f"Keep all [Tn] markers and \\N exactly as provided.\n"
                        f"No notes, no markdown, no extra text.\n\n"
                        f"{payload}"
                    ),
                },
            ],
            "temperature": 0.15,
            "max_tokens": min(4096, max(400, 120 * len(linhas))),
        }

        self.stats.requisicoes += 1
        t_ini = time.perf_counter()

        try:
            r = requests.post(self.api_url, json=corpo, headers={"Content-Type": "application/json"}, timeout=120)
        except requests.exceptions.ConnectionError as e:
            self.auditoria.retentativas_api += 1
            self.auditoria.registrar_tempo_api(time.perf_counter() - t_ini)
            espera = self.config.backoff_lm_offline_seg[min(tentativa - 1, len(self.config.backoff_lm_offline_seg) - 1)]
            self.log.aviso(
                f"{self.config.cor_lm_offline}[LM STUDIO OFFLINE]{Style.RESET_ALL} "
                f"tentativa {tentativa}/{self.config.max_tentativas_api}: {e} | aguardando {espera}s"
            )
            if tentativa < self.config.max_tentativas_api:
                time.sleep(espera)
                return self.traduzir_lote(linhas, tentativa + 1)
            self._registrar_falha_api(f"connection_error: {e}", linhas, "api_offline")
            return {}
        except requests.RequestException as e:
            self.auditoria.retentativas_api += 1
            self.auditoria.registrar_tempo_api(time.perf_counter() - t_ini)
            espera = self.config.backoff_rede_seg[min(tentativa - 1, len(self.config.backoff_rede_seg) - 1)]
            self.log.aviso(f"Falha de rede (tentativa {tentativa}): {e} | aguardando {espera}s")
            if tentativa < self.config.max_tentativas_api:
                time.sleep(espera)
                return self.traduzir_lote(linhas, tentativa + 1)
            self._registrar_falha_api(f"rede: {e}", linhas, "api_rede")
            return {}

        duracao = time.perf_counter() - t_ini
        self.auditoria.registrar_tempo_api(duracao)

        if r.status_code != 200:
            self.auditoria.retentativas_api += 1
            if tentativa < self.config.max_tentativas_api:
                time.sleep(5)
                return self.traduzir_lote(linhas, tentativa + 1)
            self._registrar_falha_api(f"http_{r.status_code}", linhas, "api_http")
            return {}

        try:
            bruto = r.json()['choices'][0]['message']['content'].strip()
        except (ValueError, KeyError, IndexError, TypeError) as e:
            self.auditoria.retentativas_api += 1
            if tentativa < self.config.max_tentativas_api:
                time.sleep(5)
                return self.traduzir_lote(linhas, tentativa + 1)
            self._registrar_falha_api(f"json_invalido: {e}", linhas, "api_json")
            return {}

        self.falhas_consecutivas = 0
        traduzidas = self._parse_resposta(bruto, linhas)
        if not traduzidas:
            self.log.debug(f"Lote vazio após {formatar_tempo(duracao, com_ms=True)}: {bruto[:300]}")
        return traduzidas

    def traduzir_lote_resiliente(self, linhas: list) -> dict[int, str]:
        if self.abortar:
            return {i: f"[ERRO_TRADUCAO: {t}]" for i, t in enumerate(linhas)}

        with Cronometro() as cron_lote:
            resultado = self.traduzir_lote(linhas)
            faltantes = [i for i in range(len(linhas)) if i not in resultado]

            if faltantes and resultado:
                self.auditoria.lotes_parciais += 1
                self.log.aviso(
                    f"Lote parcial {len(resultado)}/{len(linhas)} em "
                    f"{formatar_tempo(cron_lote.elapsed, com_ms=True)}. "
                    f"Retraduzindo {len(faltantes)} linha(s) individualmente..."
                )

            for idx in faltantes:
                if self.abortar:
                    break
                self.auditoria.fallbacks_individuais += 1
                sucesso = False
                t_ind_ini = time.perf_counter()
                for _ in range(3):
                    try:
                        res = self.traduzir_lote([linhas[idx]])
                    except LmStudioIndisponivel:
                        raise
                    if 0 in res:
                        resultado[idx] = res[0]
                        sucesso = True
                        break
                    time.sleep(2)
                t_ind = time.perf_counter() - t_ind_ini
                if not sucesso:
                    self.auditoria.registrar_falha_definitiva(
                        self.arquivo_atual, idx, linhas[idx],
                        "falha_apos_3_tentativas_individuais",
                        tentativas=3, tempo_seg=t_ind,
                    )
                    resultado[idx] = f"[ERRO_TRADUCAO: {linhas[idx]}]"
                    self.stats.linhas_com_erro += 1

        self.auditoria.registrar_tempo_lote(cron_lote.elapsed)
        return resultado

# ============================================================================
# PIPELINE MISTRAL NEMO — GUNDAM ZZ
# ============================================================================
class PipelineMistralZZ:
    """Orquestrador: compõe cache, leitor ASS, cliente LM Studio e auditoria."""

    LM_URL_PADRAO = CONFIG.lm_url_padrao

    PROMPT_SISTEMA = (
        "You are an expert anime subtitler specializing in Mobile Suit Gundam ZZ "
        "(Double Zeta, Universal Century year 0088).\n"
        "Translate numbered subtitle lines from English into natural, fluent Brazilian Portuguese (PT-BR).\n"
        "The output must be entirely in Brazilian Portuguese, except for protected proper nouns, "
        "faction names, mecha names, ship names, and subtitle markers.\n\n"

        "SERIES CONTEXT (Gundam ZZ / Double Zeta):\n"
        "- Set in UC 0088, immediately after Mobile Suit Zeta Gundam.\n"
        "- The story begins in the junkyard colony Shangri-La; protagonist Judau Ashta is a scavenger "
        "who joins the A.E.U.G. crew aboard the Argama.\n"
        "- Tone mixes war drama, colony life, and lighter/comedic moments — keep dialogue punchy and natural.\n"
        "- Main conflict: A.E.U.G. and allies vs Neo Zeon (Haman Karn's forces); later Glemy Toto's rebellion.\n"
        "- Recurring themes: civilian teenagers dragged into war, Newtypes, Anaheim Electronics prototypes.\n\n"

        "CRITICAL RULES:\n"
        "1. Return ONLY the numbered translated lines. No notes, headers, markdown, or commentary.\n"
        "2. Keep exact numbering and order ([0], [1], ...). Never merge, split, or skip lines.\n"
        "3. Preserve all markers exactly: [T0], [T1], \\N, \\n. Do not alter or translate them.\n"
        "4. Do not keep Japanese honorific suffixes (-san, -kun, -sama) unless clearly comedic.\n\n"

        "PROTECTED TERMS — DO NOT TRANSLATE:\n"
        "Factions/Orgs: Neo Zeon, A.E.U.G., Anaheim Electronics, Earth Federation, Karaba\n"
        "Locations: Shangri-La, Axis, Moon-Moon, Granada, Dakar, Dublin, Side 1, Side 3\n"
        "Ships/vehicles: Argama, Nahel Argama, Endra, Sadalahn, Gwanban, Mega Rider\n"
        "A.E.U.G. crew/allies: Judau Ashta, Roux Louka, Beecha Oleg, Iino Abbav, Mondo Agake, "
        "Elle Vianno, Leina Ashta, Bright Noa, Astonaige Medoz, Hayato Kobayashi, "
        "Kamille Bidan, Fa Yuiry, Emary Ounce, Shinta, Qum, Sayla Mass\n"
        "Neo Zeon: Haman Karn, Mashymre Cello, Chara Soon, Glemy Toto, Elpeo Ple, Ple Two, "
        "Gottn Goh, Gemon Bajack, Rakan Dahkaran, August Gidan, Illia Pazom, Mineva Lao Zabi\n"
        "Mecha: Double Zeta, ZZ, Zeta Gundam, Hyaku Shiki, Mk-II, Core Top, Core Base, Core Fighter, "
        "Qubeley, Zaku, Bawoo, Dreissen, Doven Wolf, Quin Mantha, Geymalk, Zssa, Hamma-Hamma, "
        "R-Jarja, Gaza-C, Gaza-D, Galluss-J, Jamru Fin, Psycho Gundam Mk-II, Methuss\n\n"

        "TERM ADAPTATIONS:\n"
        "- Newtype -> Newtype (or 'novo tipo' only if the English line uses the full phrase)\n"
        "- Minovsky particle / Minovsky -> partícula Minovsky / Minovsky\n"
        "- Colony -> colônia | Side -> Side | mobile suit -> mobile suit\n"
        "- Axis as the Neo Zeon asteroid/base stays Axis, never 'Eixo'.\n"
        "- Core Top, Core Base, Core Fighter and Mega Rider stay in English.\n"
        "- Lady Haman -> Lady Haman; do not translate as 'Senhorita Haman'.\n"
        "- Elpeo Ple and Ple Two stay exactly like that; never use Puru/Ple Dois.\n"
        "- Quin Mantha stays Quin Mantha; never translate as Queen/Rainha Mansa.\n"
        "- Roger / Roger that -> Copiado or Entendido\n"
        "- Copy that -> Entendido | Stand by -> Aguarde\n"
        "- Target locked -> Alvo travado | Sortie -> Saída para combate\n\n"

        "STYLE:\n"
        "- Natural Brazilian Portuguese for anime subtitles; concise and readable.\n"
        "- Avoid literal English calques (e.g. 'I see' as agreement -> 'Entendo').\n"
        "- Preserve military radio tone where appropriate.\n\n"

        "EXAMPLE:\n"
        "[0] Hey, Judau! Look out!\n"
        "[0] Ei, Judau! Cuidado!\n"
        "[1] The [T0]Neo Zeon fleet is here\\NWe must launch the ZZ.\n"
        "[1] A frota da [T0]Neo Zeon chegou\\NPrecisamos lançar o ZZ.\n"
    )

    def __init__(
        self,
        log: GerenciadorLogs,
        modelo: str | None = None,
        lm_url: str | None = None,
        batch_size: int | None = None,
        limpar_cache: bool = False,
        config: ConfiguracaoZZ = CONFIG,
    ):
        self.log = log
        self.config = config
        self.batch_size = max(1, batch_size or config.batch_size_padrao)
        self.auditoria = AuditoriaTraducao(log)
        self.estatisticas = EstatisticasPipeline()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.cache = RepositorioCache(os.path.join(base_dir, config.nome_cache), log, limpar_cache)
        self.leitor = LeitorAssZZ(log, config)
        self.cliente = ClienteLmStudio(
            log=log,
            auditoria=self.auditoria,
            stats=self.estatisticas,
            prompt_sistema=self.PROMPT_SISTEMA,
            lm_url=lm_url or config.lm_url_padrao,
            modelo=modelo or "local-model",
            config=config,
        )
        self.LM_URL = self.cliente.lm_url
        self.modelo_ativo = self.cliente.modelo
        self.arquivo_atual = ""

    @property
    def stats(self) -> dict:
        """Compatibilidade com logs/relatórios que esperam dict."""
        return self.estatisticas.como_dict()

    def validar_conexao(self) -> bool:
        ok = self.cliente.validar_conexao()
        self.modelo_ativo = self.cliente.modelo
        return ok

    def _salvar_cache(self):
        self.cache.salvar()

    def _processar_lotes(
        self,
        nome_arq: str,
        pendentes: list[DialogoLegenda],
    ) -> tuple[dict[int, str], int, int]:
        """Traduz diálogos pendentes em lotes; retorna (mapa idx→texto, ok, erros)."""
        textos = [d.texto_mascarado for d in pendentes]
        indices = [d.indice_arquivo for d in pendentes]
        total_lotes = (len(textos) + self.batch_size - 1) // self.batch_size
        traducoes: dict[int, str] = {}
        lotes_ok = lotes_err = 0

        self.log.info(
            f"Traduzindo {len(textos)} diálogos novos em {nome_arq} "
            f"({total_lotes} lote(s) de até {self.batch_size})"
        )
        tempo_lotes_ini = time.perf_counter()

        with tqdm(
            total=total_lotes,
            desc=f"  {nome_arq[:28]}",
            unit="lote",
            leave=False,
            colour="cyan",
            ncols=100,
        ) as pbar_lote:
            for i in range(0, len(textos), self.batch_size):
                lote_indices = indices[i:i + self.batch_size]
                lote_textos = textos[i:i + self.batch_size]
                num_lote = (i // self.batch_size) + 1

                t_lote_ini = time.perf_counter()
                try:
                    resp_lote = self.cliente.traduzir_lote_resiliente(lote_textos)
                except LmStudioIndisponivel as e:
                    self.log.critico(str(e))
                    self._salvar_cache()
                    raise
                t_lote = time.perf_counter() - t_lote_ini

                ok_lote = err_lote = 0
                for local_idx, real_idx in enumerate(lote_indices):
                    if local_idx in resp_lote:
                        valor = resp_lote[local_idx]
                        traducoes[real_idx] = valor
                        if "[ERRO_TRADUCAO" not in valor:
                            self.cache.set(lote_textos[local_idx], valor)
                            self.estatisticas.linhas_traduzidas += 1
                            ok_lote += 1
                        else:
                            self.estatisticas.erros_traducao += 1
                            err_lote += 1
                    else:
                        original = lote_textos[local_idx]
                        traducoes[real_idx] = f"[ERRO_TRADUCAO: {original}]"
                        self.estatisticas.erros_traducao += 1
                        self.estatisticas.linhas_com_erro += 1
                        err_lote += 1
                        self.auditoria.registrar_falha_definitiva(
                            nome_arq, local_idx, original,
                            "ausente_na_resposta_do_lote", tempo_seg=t_lote,
                        )

                lotes_ok += ok_lote
                lotes_err += err_lote
                decorrido = time.perf_counter() - tempo_lotes_ini
                media = decorrido / num_lote
                eta = formatar_eta(media * (total_lotes - num_lote))
                pbar_lote.set_postfix_str(
                    f"OK:{ok_lote} ERR:{err_lote} | "
                    f"lote:{formatar_tempo(t_lote, com_ms=True)} | "
                    f"API~{formatar_tempo(self.auditoria.media_api(), com_ms=True)} | "
                    f"ETA:{eta}",
                    refresh=True,
                )
                pbar_lote.update(1)
                if err_lote > 0:
                    self.log.status_dinamico(
                        f"{nome_arq} lote {num_lote}/{total_lotes}: "
                        f"{err_lote} erro(s) — ver falhas_zz_en_*.txt"
                    )

        self.log.info(
            f"{nome_arq}: lotes em {formatar_tempo(time.perf_counter() - tempo_lotes_ini)} | "
            f"traduzidas={lotes_ok} erros={lotes_err}"
        )
        return traducoes, lotes_ok, lotes_err

    def processar_arquivo(self, caminho_in: str, pasta_out: str, nome_saida: str | None = None) -> bool:
        ep_ini = time.perf_counter()
        nome_arq = os.path.basename(caminho_in)
        nome_saida = nome_saida_ptbr(nome_saida or nome_arq)
        self.arquivo_atual = nome_arq
        self.cliente.arquivo_atual = nome_arq
        self.log.secao(f"Iniciando Episódio: {nome_arq}")
        self.estatisticas.ass_total += 1
        erros_arquivo = cache_hits_arquivo = dialogos_novos = 0

        try:
            caminho_in = validar_arquivo_ass(caminho_in)
            os.makedirs(pasta_out, exist_ok=True)

            with Cronometro() as cron_io:
                linhas_ass, enc = self.leitor.ler_linhas(caminho_in)
            self.auditoria.tempo_io_seg += cron_io.elapsed
            self.log.debug(
                f"Encoding: {enc} | leitura: {formatar_tempo(cron_io.elapsed, com_ms=True)}"
            )

            dialogos = self.leitor.extrair_dialogos(linhas_ass, self.cache, self.estatisticas)
            pendentes = [d for d in dialogos if d.tipo == TipoLinhaAss.PENDENTE]
            cache_hits_arquivo = sum(1 for d in dialogos if d.tipo == TipoLinhaAss.CACHE)
            dialogos_novos = len(pendentes)

            traducoes: dict[int, str] = {}
            if pendentes:
                traducoes, _, erros_arquivo = self._processar_lotes(nome_arq, pendentes)
                self._salvar_cache()

            conteudo_final = LeitorAssZZ.montar_saida(dialogos, self.cache, traducoes)
            caminho_out = os.path.join(pasta_out, nome_saida)
            if not caminho_dentro_de(pasta_out, caminho_out):
                raise ValueError(f"Caminho de saída fora da pasta destino: {caminho_out}")

            with Cronometro() as cron_grav:
                gravar_arquivo_atomico(caminho_out, conteudo_final)
            self.auditoria.tempo_io_seg += cron_grav.elapsed

            ep_duracao = time.perf_counter() - ep_ini
            self.auditoria.registrar_arquivo(
                nome_arq, ep_duracao, dialogos_novos,
                cache_hits_arquivo, erros_arquivo, ok=True,
            )
            self.log.sucesso(
                f"Salvo: {caminho_out} | Tempo: {formatar_tempo(ep_duracao)} | "
                f"novos={dialogos_novos} cache={cache_hits_arquivo} erros={erros_arquivo}"
            )
            self.estatisticas.ass_ok += 1
            return True

        except LmStudioIndisponivel:
            self.auditoria.registrar_arquivo(
                nome_arq, time.perf_counter() - ep_ini,
                dialogos_novos, cache_hits_arquivo, erros_arquivo, ok=False,
            )
            raise
        except Exception as e:
            self.auditoria.registrar_arquivo(
                nome_arq, time.perf_counter() - ep_ini,
                dialogos_novos, cache_hits_arquivo, erros_arquivo, ok=False,
            )
            self.log.erro(f"Falha ao processar {nome_arq}: {e}", exc=e)
            self.log.traceback_completo(f"processar_arquivo({nome_arq})")
            self.estatisticas.ass_falha += 1
            return False

def validar_traducao(original: str, traducao: str) -> tuple[bool, str]:
    return ValidadorTraducaoZZ.validar(original, traducao)


# ============================================================================
# CLI E EXECUÇÃO
# ============================================================================
def obter_diretorio_operador(mensagem: str, padrao: str | None = None) -> str:
    while True:
        sufixo = f" (ENTER = {padrao})" if padrao else ""
        entrada = input(f"{Fore.YELLOW}{mensagem}{sufixo}: {Style.RESET_ALL}").strip()
        entrada = entrada.strip('"').strip("'")
        if not entrada and padrao:
            return validar_pasta(padrao, "Pasta")
        if not entrada:
            continue
        try:
            return validar_pasta(entrada, "Pasta")
        except ValueError as e:
            print(f"{Fore.RED}[ERRO] {e}{Style.RESET_ALL}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Tradutor EN→PT-BR Gundam ZZ (Double Zeta) via Mistral Nemo / LM Studio.",
    )
    parser.add_argument("--entrada", help="Pasta com legendas .ass em inglês")
    parser.add_argument(
        "--arquivo", nargs="+", metavar="CAMINHO",
        help="Um ou mais arquivos .ass (ignora --entrada)",
    )
    parser.add_argument("--saida", help="Pasta de saída PT-BR")
    parser.add_argument("--modelo", help="ID do modelo no LM Studio")
    parser.add_argument(
        "--lm-url", default=PipelineMistralZZ.LM_URL_PADRAO,
        help="URL base do LM Studio",
    )
    parser.add_argument(
        "--batch-size", type=int, default=15,
        help="Linhas por lote (padrão: 15)",
    )
    parser.add_argument(
        "--limpar-cache", action="store_true",
        help="Remove o cache antes de iniciar",
    )
    parser.add_argument(
        "--pular-existentes", action="store_true",
        help="Não reprocessa se o .ass de saída já existir",
    )
    return parser.parse_args()


def executar_pipeline(args=None):
    if args is None:
        args = parse_args()

    log = GerenciadorLogs()
    pipeline = None

    try:
        log.secao("TRADUTOR GUNDAM ZZ — EN -> PT-BR (MISTRAL NEMO)")

        pipeline = PipelineMistralZZ(
            log,
            modelo=args.modelo,
            lm_url=args.lm_url,
            batch_size=args.batch_size,
            limpar_cache=args.limpar_cache,
        )

        if not pipeline.validar_conexao():
            return 1

        jobs = []
        pasta_saida_principal = None

        if args.arquivo:
            pasta_saida = normalizar_caminho(args.saida) if args.saida else None
            if pasta_saida:
                os.makedirs(pasta_saida, exist_ok=True)
                pasta_saida_principal = pasta_saida
            for caminho in args.arquivo:
                try:
                    caminho_valido = validar_arquivo_ass(caminho)
                except ValueError as e:
                    log.erro(str(e))
                    return 1
                destino = (
                    os.path.join(pasta_saida, nome_saida_ptbr(os.path.basename(caminho_valido)))
                    if pasta_saida
                    else os.path.join(
                        os.path.dirname(caminho_valido),
                        PASTA_SAIDA_PADRAO,
                        nome_saida_ptbr(os.path.basename(caminho_valido)),
                    )
                )
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                jobs.append((caminho_valido, os.path.dirname(destino), os.path.basename(destino)))
        else:
            if args.entrada:
                pasta_in = validar_pasta(args.entrada, "Pasta origem")
            else:
                pasta_in = obter_diretorio_operador(
                    "Caminho da pasta de legendas EN (origem)",
                    PASTA_ANIME_PADRAO,
                )

            if args.saida:
                pasta_out = normalizar_caminho(args.saida)
            else:
                pasta_out = os.path.join(pasta_in, PASTA_SAIDA_PADRAO)

            os.makedirs(pasta_out, exist_ok=True)
            pasta_saida_principal = pasta_out

            for caminho in listar_arquivos_ass(pasta_in):
                destino = caminho_saida_relativo(pasta_in, caminho, pasta_out)
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                jobs.append((caminho, os.path.dirname(destino), os.path.basename(destino)))

        if not jobs:
            log.aviso("Nenhum arquivo .ass encontrado para traduzir.")
            return 1

        log.salvar_config(
            modelo=pipeline.modelo_ativo,
            lm_url=pipeline.LM_URL,
            batch_size=pipeline.batch_size,
            arquivos=len(jobs),
        )

        tempo_ini = time.perf_counter()
        pulados = 0
        log.secao("PROCESSAMENTO EM LOTE")

        with tqdm(
            total=len(jobs),
            desc="Gundam ZZ temporada",
            unit="arq",
            colour="green",
            ncols=100,
            position=0,
        ) as barra_macro:
            for idx_job, (caminho_in, pasta_out, nome_saida) in enumerate(jobs, 1):
                caminho_out = os.path.join(pasta_out, nome_saida)
                nome_arq = os.path.basename(caminho_in)

                if args.pular_existentes and os.path.isfile(caminho_out):
                    pulados += 1
                    pipeline.estatisticas.ass_pulados += 1
                    tqdm.write(
                        f"{Fore.CYAN}[{idx_job}/{len(jobs)}] Pulando (já existe): {nome_arq}{Style.RESET_ALL}"
                    )
                    barra_macro.update(1)
                    continue

                decorrido = time.perf_counter() - tempo_ini
                processados = idx_job - 1 - pulados
                if processados > 0:
                    media_arq = decorrido / processados
                    restantes = len(jobs) - idx_job + 1
                    eta_global = formatar_eta(media_arq * restantes)
                    barra_macro.set_postfix_str(
                        f"{nome_arq[:22]} ETA:{eta_global} | acum:{formatar_tempo(decorrido)}",
                        refresh=True,
                    )
                else:
                    barra_macro.set_postfix_str(nome_arq[:35], refresh=True)

                tqdm.write(
                    f"\n{Fore.YELLOW}[{idx_job}/{len(jobs)}] Traduzindo: {nome_arq}{Style.RESET_ALL}"
                )
                log.info(f"Entrada: {caminho_in}")
                log.info(f"Saída  : {caminho_out}")

                t_arq_ini = time.perf_counter()
                try:
                    sucesso = pipeline.processar_arquivo(caminho_in, pasta_out, nome_saida=nome_saida)
                except LmStudioIndisponivel as e:
                    log.critico(str(e))
                    tqdm.write(f"{Fore.RED}  [ABORTADO] LM Studio indisponível — episódios restantes não processados.{Style.RESET_ALL}")
                    break
                t_arq = time.perf_counter() - t_arq_ini

                if sucesso:
                    tqdm.write(
                        f"{Fore.GREEN}  [CONCLUÍDO] {nome_arq} | "
                        f"{formatar_tempo(t_arq)} | acumulado: "
                        f"{formatar_tempo(time.perf_counter() - tempo_ini)}{Style.RESET_ALL}"
                    )
                else:
                    tqdm.write(
                        f"{Fore.RED}  [FALHOU] {nome_arq} | "
                        f"{formatar_tempo(t_arq)}{Style.RESET_ALL}"
                    )

                barra_macro.update(1)

        tempo_total = time.perf_counter() - tempo_ini
        tempo_total_fmt = formatar_tempo(tempo_total)
        auditoria_resumo = pipeline.auditoria.resumo()

        log.secao("ESTATÍSTICAS FINAIS")
        log.info(f"Tempo total           : {tempo_total_fmt}")
        log.info(f"Arquivos OK           : {pipeline.estatisticas.ass_ok}/{pipeline.estatisticas.ass_total}")
        if pulados:
            log.info(f"Arquivos pulados      : {pulados}")
        log.info(f"Linhas traduzidas     : {pipeline.estatisticas.linhas_traduzidas}")
        log.info(f"Linhas com erro       : {pipeline.estatisticas.linhas_com_erro}")
        log.info(f"Cache hits            : {pipeline.estatisticas.cache_hits}")
        log.info(f"Requisições LLM       : {pipeline.estatisticas.requisicoes}")
        log.info(f"Tempo em API          : {formatar_tempo(auditoria_resumo['tempo_total_api_seg'])}")
        log.info(f"Média API/requisição  : {formatar_tempo(auditoria_resumo['tempo_medio_api_seg'], com_ms=True)}")
        log.info(f"Média por lote        : {formatar_tempo(auditoria_resumo['tempo_medio_lote_seg'], com_ms=True)}")
        log.info(f"Retentativas API      : {auditoria_resumo['retentativas_api']}")
        log.info(f"Fallbacks individuais : {auditoria_resumo['fallbacks_individuais']}")
        log.info(f"Rejeições validação   : {auditoria_resumo['rejeicoes_validacao']}")

        if auditoria_resumo['falhas_por_motivo']:
            log.info("Falhas por motivo:")
            for motivo, qtd in sorted(
                auditoria_resumo['falhas_por_motivo'].items(), key=lambda x: -x[1]
            ):
                log.info(f"  {qtd:4d}x  {motivo}")

        stats_final = pipeline.estatisticas.como_dict()
        stats_final['tempo_total_seg'] = round(tempo_total, 2)
        log.salvar_stats(stats_final, auditoria_resumo)
        log.relatorio_final(stats_final, auditoria_resumo, tempo_total_fmt)
        if pasta_saida_principal:
            log.espelhar_relatorio_na_saida(pasta_saida_principal)
        if pipeline.estatisticas.abortado_lm_offline:
            log.aviso(
                "Próximo passo (vault): rodar "
                "07_higienizacao_e_reparo_de_traducao/repara_erros_traducao.py "
                "nas linhas [ERRO_TRADUCAO:] após religar o Mistral Nemo."
            )
        log.sucesso("Finalizado.")
        return 0

    except KeyboardInterrupt:
        log.aviso("Interrompido pelo usuário.")
        if pipeline:
            pipeline._salvar_cache()
            auditoria = pipeline.auditoria.resumo()
            stats_final = pipeline.estatisticas.como_dict()
            stats_final['tempo_total_seg'] = round(
                time.perf_counter() - pipeline.estatisticas.tempo_inicio, 2
            )
            log.salvar_stats(stats_final, auditoria)
        return 130

    except Exception as e:
        log.critico(f"Erro fatal: {e}")
        log.traceback_completo("executar_pipeline()")
        if pipeline:
            pipeline._salvar_cache()
            log.salvar_stats(pipeline.estatisticas.como_dict(), pipeline.auditoria.resumo())
        return 1

    finally:
        log.fechar()


def principal():
    sys.exit(executar_pipeline())


# Compatível com repara_erros_traducao.py (vault: importa SYSTEM_PROMPT por série)
SYSTEM_PROMPT = PipelineMistralZZ.PROMPT_SISTEMA


if __name__ == "__main__":
    principal()
