#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PIPELINE INDUSTRIAL UNIFICADO - VERSÃO INGLÊS (EN -> PT-BR)
Alvo: Detonator Orgun (1991)
Extrai .ass e .srt → Traduz do Inglês via LM Studio (Mistral Nemo) → Salva PT-BR

Sistema de Logs Auditável com Temporizadores de Precisão e Validador Anti-Alucinação Inglês.
"""

import os
import sys
import re
import json
import time
import requests
import traceback
import glob
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
    CORES = {
        "SUCESSO": Fore.GREEN + Style.BRIGHT,
        "ERRO":    Fore.RED + Style.BRIGHT,
        "CRÍTICO": Fore.RED + Style.BRIGHT,
        "AVISO":   Fore.YELLOW,
        "INFO":    Fore.WHITE,
        "DEBUG":   Fore.CYAN,
    }

    def __init__(self):
        self.pasta_logs = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(self.pasta_logs, exist_ok=True)
        self.ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        self.f_pipeline = open(os.path.join(self.pasta_logs, f"pipeline_en_orgun_{self.ts}.txt"), 'w', encoding='utf-8')
        self.f_erros = open(os.path.join(self.pasta_logs, f"erros_en_orgun_{self.ts}.txt"), 'w', encoding='utf-8')
        self.caminho_stats  = os.path.join(self.pasta_logs, f"stats_en_orgun_{self.ts}.json")
        self.caminho_config = os.path.join(self.pasta_logs, f"config_en_orgun_{self.ts}.txt")

        header = (f"\n{'='*80}\nPIPELINE INDUSTRIAL MISTRAL INGLÊS - DETONATOR ORGUN\n{'='*80}\n"
                  f"Início    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                  f"Pasta logs: {self.pasta_logs}\n{'='*80}\n\n")
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
        bloco = (f"\n{'='*80}\nTRACEBACK COMPLETO\n{'='*80}\n"
                 f"Contexto : {contexto}\n\n{tb}\n{'-'*80}\n\n")
        self.f_erros.write(bloco)
        self.f_erros.flush()
        print(f"{Fore.RED}{tb}{Style.RESET_ALL}")

    def salvar_stats(self, stats: dict):
        payload = {"timestamp": self.ts, "data_hora": datetime.now().isoformat(), "stats": stats}
        with open(self.caminho_stats, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        self.debug(f"Stats salvo: {os.path.basename(self.caminho_stats)}")

    def fechar(self):
        for f in (self.f_pipeline, self.f_erros):
            f.close()
        print(f"\n{Fore.GREEN}✓ LOGS SALVOS EM: {self.pasta_logs}{Style.RESET_ALL}\n")


# ============================================================================
# VALIDAÇÃO ANTI-ALUCINAÇÃO E CORREÇÕES DE LORE (DETONATOR ORGUN)
# ============================================================================

# Resíduos perigosos da língua inglesa sem tradução na frase
PADRAO_RESIDUO_INGLES = re.compile(
    r"\b(you|your|the|what|how|where|when|this|that|there|here|then|they|with|about|is|are|was|were)\b",
    re.IGNORECASE,
)

PADRAO_PREAMBULO_LLM = re.compile(
    r"^(esta [ée] a tradu|segue|abaixo est[áa]|abaixo seguem|claro,?\s+vou|here is|translation:|note:)\b",
    re.IGNORECASE,
)

SUBSTITUICOES_POS_PROCESSAMENTO = [
    (re.compile(r"\bEarth Defense Force\b", re.I), "E.D.F."),
    (re.compile(r"\bEDF\b", re.I), "E.D.F."),
    # "Evoluders" é termo cunhado pela obra; LLMs tendem a traduzir
    # literalmente (Evoluidores/Evolutores/Evoluções) em vez de manter o nome.
    (re.compile(r"\bEvolu[ií]dores\b", re.I), "Evoluders"),
    (re.compile(r"\bEvolutores\b", re.I), "Evoluders"),
    (re.compile(r"\bEvolu[ií]dor\b", re.I), "Evoluder"),
    # "Solid Armor" é o nome do equipamento/sistema do Orgun, não um adjetivo comum.
    (re.compile(r"\bArmadura S[óo]lida\b", re.I), "Solid Armor"),
    # "Mhiku" é grafia propositalmente não-padrão do personagem; LLMs tendem
    # a "corrigi-la" para o nome comum japonês "Miku".
    (re.compile(r"\bMiku\b"), "Mhiku"),
]

def validar_traducao(original: str, traducao: str) -> bool:
    if not traducao or "[ERRO_TRADUCAO" in traducao:
        return False
    if PADRAO_RESIDUO_INGLES.search(traducao):
        return False
    if PADRAO_PREAMBULO_LLM.match(traducao.strip()):
        return False
    if len(traducao) > max(250, len(original) * 8):
        return False
    return True


# ============================================================================
# PIPELINE PRINCIPAL (MISTRAL NEMO)
# ============================================================================

class PipelineOrgun:
    LM_URL  = "http://127.0.0.1:1234"
    API_URL = f"{LM_URL}/v1/chat/completions"

    PROMPT_SISTEMA = (
        """Você é um tradutor e localizador especialista em legendas de anime, cyberpunk dos anos 90 e ficção científica militar.

TAREFA:
Traduza as linhas de legenda do INGLÊS para PORTUGUÊS DO BRASIL (PT-BR), mantendo impacto dramático e consistência de lore de Detonator Orgun.

REGRAS ABSOLUTAS DE SAÍDA:
1. Responda somente com as linhas traduzidas numeradas. Não explique, não cumprimente, não adicione notas.
2. Preserve os índices exatamente: se receber "[0] texto", responda "[0] tradução".
3. Preserve marcadores de formatação como [T0], [T1] e tags ASS.
4. Preserve quebras e escapes de legenda como \\N, \\n.
5. Preserve as TAGS de SRT (ex: <i>, </i>, <b>, <font>).
6. Se a linha for grito ou transmissão, traduza de forma realista (Ex: "Roger that" -> "Entendido!").

GLOSSÁRIO PRINCIPAL DE DETONATOR ORGUN:
- Detonator Orgun -> Detonator Orgun
- Orgun -> Orgun
- Tomoru Shindo / Tomoru -> Tomoru Shindo / Tomoru
- Yoko Mitsurugi / Yoko -> Yoko Mitsurugi / Yoko
- Kumi Jefferson / Kumi -> Kumi Jefferson / Kumi
- Professor Mishima -> Professor Mishima
- E.D.F. / Earth Defense Force -> E.D.F. (Força de Defesa da Terra)
- Evoluders / Evoluder -> Evoluders / Evoluder
- Zoa -> Zoa
- Lang -> Lang
- Leave -> Leave
- Mhiku -> Mhiku
- Solid Armor -> Solid Armor
- Antimatter -> antimatéria
- Spacer -> astronauta / colono espacial

ANTI-ERROS:
- Não suavize ameaças militares.
- Preserve a dualidade entre humanos e Evoluders (ciborgues/alienígenas).
- Se houver nomes próprios em caixa alta na origem, mantenha em caixa alta.
- "Leave" e "Lang" são nomes de personagens, não palavras comuns. Nunca traduza "Leave" como o verbo "sair/partir" nem "Lang" como abreviação de idioma — confirme pelo contexto da fala se é um nome sendo chamado (vocativo) antes de traduzir a frase.
- "Mhiku" é a grafia correta do nome do personagem. Nunca "corrija" para "Miku".
- Nunca traduza "Evoluders"/"Evoluder" ou "Solid Armor" literalmente — são termos próprios da obra e devem permanecer em inglês.
- Não invente parentescos, ranques militares ou eventos de lore que não estejam explícitos na linha.

EXEMPLO DE FORMATO:
[0] Tomoru, are you okay?
[0] Tomoru, você está bem?
[1] The <i>Evoluders</i> are coming\\NPrepare the E.D.F. defenses!
[1] Os <i>Evoluders</i> estão vindo\\NPreparem as defesas da E.D.F.!
""")

    def __init__(self, log: GerenciadorLogs):
        self.log   = log
        self.cache = {}
        self.modelo_ativo = "local-model"
        self.caminho_cache = os.path.join(os.path.dirname(os.path.abspath(__file__)), "traducao_cache_orgun_en.json")
        self._carregar_cache()
        self.stats = {'total_arquivos': 0, 'traduzidos': 0, 'cache_hits': 0, 'linhas_traduzidas': 0, 'erros_traducao': 0}

    def validar(self) -> bool:
        self.log.secao("VALIDAÇÃO DE INFRAESTRUTURA")
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

        self.log.sucesso("✓ Infraestrutura validada!")
        return True

    def _carregar_cache(self):
        if os.path.exists(self.caminho_cache):
            try:
                with open(self.caminho_cache, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                self.log.info(f"Cache carregado: {len(self.cache)} traduções.")
            except Exception as e:
                self.log.aviso(f"Erro ao carregar cache: {e}")
                self.cache = {}
        else:
            self.cache = {}

    def _salvar_cache(self):
        try:
            with open(self.caminho_cache, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log.aviso(f"Erro ao salvar cache em disco: {e}")

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
            trad = trad.replace(marcador, tag, 1)
        return trad

    def limpar_saida_traducao(self, texto: str) -> str:
        texto = texto.strip()
        texto = re.sub(r"\[\s*[Tt]\s*(\d+)\s*\]", r"[T\1]", texto)
        texto = re.sub(r"\\\s*([Nnh])", r"\\\1", texto)
        texto = texto.replace("/N", r"\N").replace("/n", r"\n")
        texto = re.sub(r"\s*\\N\s*", r"\\N", texto)
        for padrao, substituto in SUBSTITUICOES_POS_PROCESSAMENTO:
            texto = padrao.sub(substituto, texto)
        return texto

    def _traduzir_lote(self, linhas: list, tentativa=1) -> dict:
        payload = "\n".join(f"[{i}] {t}" for i, t in enumerate(linhas))
        corpo = {
            "model": self.modelo_ativo,
            "messages": [
                {"role": "system", "content": self.PROMPT_SISTEMA},
                {"role": "user", "content": f"Traduza as seguintes {len(linhas)} linhas (Inglês -> Português do Brasil):\n{payload}"},
            ],
            "temperature": 0.2,
            "max_tokens": 800,
        }

        try:
            r = requests.post(self.API_URL, json=corpo, headers={"Content-Type": "application/json"}, timeout=120)
        except Exception as e:
            if tentativa < 2:
                time.sleep(2)
                return self._traduzir_lote(linhas, tentativa + 1)
            return {}

        if r.status_code != 200:
            return {}

        bruto = r.json()['choices'][0]['message']['content'].strip()
        traduzidas = {}
        for idx_str, texto in re.findall(r"\[(\d+)\]\s*(.*?)(?=\[\d+\]|$)", bruto, re.DOTALL):
            idx = int(idx_str)
            if idx < 0 or idx >= len(linhas):
                continue
            texto_limpo = self.limpar_saida_traducao(texto)
            if validar_traducao(linhas[idx], texto_limpo):
                traduzidas[idx] = texto_limpo
        
        return traduzidas

    def processar_arquivo(self, caminho_entrada: str, caminho_saida: str):
        self.log.info(f"Processando: {os.path.basename(caminho_entrada)}")
        with open(caminho_entrada, 'r', encoding='utf-8', errors='replace') as f:
            linhas = f.readlines()

        novas_linhas = []
        lote_textos = []
        mapa_lote = {}
        linhas_dialogo_originais = []

        is_ass = caminho_entrada.lower().endswith('.ass')
        
        for idx_linha, linha in enumerate(linhas):
            if is_ass and linha.startswith("Dialogue:"):
                partes = linha.split(',', 9)
                if len(partes) > 9:
                    texto_bruto = partes[9].strip()
                    texto_mascarado, tags = self.mascarar_tags(texto_bruto)
                    
                    if texto_mascarado in self.cache:
                        self.stats['cache_hits'] += 1
                        texto_trad = self.restaurar_tags(self.cache[texto_mascarado], tags)
                        partes[9] = texto_trad + "\n"
                        novas_linhas.append(','.join(partes))
                    else:
                        linhas_dialogo_originais.append((idx_linha, linha, tags, partes))
                        mapa_lote[len(lote_textos)] = idx_linha
                        lote_textos.append(texto_mascarado)
                        novas_linhas.append(linha) # placeholder temporario
                else:
                    novas_linhas.append(linha)
            
            elif not is_ass and not linha.strip().isdigit() and "-->" not in linha and linha.strip():
                # É um SRT text line
                texto_bruto = linha.strip()
                if texto_bruto in self.cache:
                    self.stats['cache_hits'] += 1
                    novas_linhas.append(self.cache[texto_bruto] + "\n")
                else:
                    linhas_dialogo_originais.append((idx_linha, linha, [], None))
                    mapa_lote[len(lote_textos)] = idx_linha
                    lote_textos.append(texto_bruto)
                    novas_linhas.append(linha)
            else:
                novas_linhas.append(linha)

        # Batch translate
        tamanho_lote = 15
        pbar = tqdm(total=len(lote_textos), desc=f"Traduzindo via Mistral Nemo ({len(lote_textos)} trechos)")
        
        for i in range(0, len(lote_textos), tamanho_lote):
            lote_atual = lote_textos[i:i+tamanho_lote]
            traducoes = self._traduzir_lote(lote_atual)
            
            for j, texto_original in enumerate(lote_atual):
                idx_no_lote = j
                idx_real_na_lista = mapa_lote[i + j]
                tupla_original = linhas_dialogo_originais[i + j]
                idx_na_string, linha_original, tags, partes = tupla_original
                
                texto_traduzido = traducoes.get(idx_no_lote, "")
                if texto_traduzido:
                    self.cache[texto_original] = texto_traduzido
                    self.stats['linhas_traduzidas'] += 1
                    
                    if is_ass:
                        texto_final = self.restaurar_tags(texto_traduzido, tags)
                        partes[9] = texto_final + "\n"
                        novas_linhas[idx_real_na_lista] = ','.join(partes)
                    else:
                        novas_linhas[idx_real_na_lista] = texto_traduzido + "\n"
                else:
                    self.stats['erros_traducao'] += 1
            
            self._salvar_cache()
            pbar.update(len(lote_atual))
        pbar.close()

        with open(caminho_saida, 'w', encoding='utf-8') as f:
            f.writelines(novas_linhas)
        self.stats['total_arquivos'] += 1
        self.log.sucesso(f"Arquivo salvo: {caminho_saida}")

    def rodar_pasta(self, pasta_in: str, pasta_out: str):
        self.log.secao("PROCESSAMENTO EM LOTE")
        arquivos = glob.glob(os.path.join(pasta_in, '*_ENG.ass')) + glob.glob(os.path.join(pasta_in, '*_ENG.srt'))
        if not arquivos:
            self.log.erro("Nenhum arquivo _ENG encontrado na pasta!")
            return
            
        os.makedirs(pasta_out, exist_ok=True)
        for arq in arquivos:
            nome_saida = os.path.basename(arq).replace("_ENG", "_PTBR")
            caminho_saida = os.path.join(pasta_out, nome_saida)
            self.processar_arquivo(arq, caminho_saida)

        self.log.salvar_stats(self.stats)
        self.log.info(f"Finalizado. Traduzidos: {self.stats['linhas_traduzidas']}, Erros: {self.stats['erros_traducao']}")

if __name__ == "__main__":
    pasta_entrada = r"E:\animes\DETONATOR ORGUN\legendas_eng"
    pasta_saida = r"E:\animes\DETONATOR ORGUN\legendas_ptbr"
    
    logger = GerenciadorLogs()
    try:
        pipeline = PipelineOrgun(logger)
        if not pipeline.validar():
            logger.erro("Validação falhou — abortando")
        else:
            pipeline.rodar_pasta(pasta_entrada, pasta_saida)
    except Exception as e:
        logger.traceback_completo("Falha global no pipeline de Orgun")
    finally:
        logger.fechar()
