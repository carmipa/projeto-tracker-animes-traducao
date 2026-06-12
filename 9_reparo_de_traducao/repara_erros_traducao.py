#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MODULO: repara_erros_traducao.py
Verifica as legendas traduzidas (*_PTBR.ass) em busca de marcadores "[ERRO_TRADUCAO: ...]"
e as traduz de forma individual (batch size = 1) recorrendo ao LM Studio,
garantindo que todas as tags e posições originais sejam perfeitamente restauradas.

Author: Antigravity + Paulo
Data: Junho 2026
"""

import os
import re
import sys
import time
import requests
from datetime import datetime
from tqdm import tqdm
from colorama import init, Fore, Style

init(autoreset=True)

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
LM_STUDIO_MODELS_URL = "http://localhost:1234/v1/models"
MODELO_ATIVO = "local-model"

# Importa o SYSTEM_PROMPT do batch_translator_unicorn
PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
RELATORIO_FILE = os.path.join(PASTA_SCRIPT, "relatorio_reparo.txt")
sys.path.append(os.path.join(os.path.dirname(PASTA_SCRIPT), "4_tradutor_ia_gemma4", "tradutor_gundam_unicornio"))
try:
    from batch_translator_unicorn import SYSTEM_PROMPT
except ImportError:
    # Fallback caso não encontre
    SYSTEM_PROMPT = (
        "You are an expert subtitler for Japanese anime, specializing in the Gundam Universal Century timeline.\n"
        "Translate the following numbered subtitle lines into Brazilian Portuguese (PT-BR).\n"
        "The final output must be entirely in Brazilian Portuguese, except for protected Gundam terms, character names, faction names, ship names, model names, and subtitle tags.\n"
    )

# Adapta o prompt do lote para tradução avulsa (evitando conflito com a instrução de raciocínio e numeração)
SYSTEM_PROMPT_REPARO = SYSTEM_PROMPT
if "numbered subtitle lines" in SYSTEM_PROMPT_REPARO or "CRITICAL RULES" in SYSTEM_PROMPT_REPARO:
    SYSTEM_PROMPT_REPARO = SYSTEM_PROMPT_REPARO.replace(
        "Translate the following numbered subtitle lines into Brazilian Portuguese (PT-BR).",
        "Translate the subtitle line into Brazilian Portuguese (PT-BR)."
    )
    SYSTEM_PROMPT_REPARO = SYSTEM_PROMPT_REPARO.replace(
        "Return ONLY the numbered translated lines. Do not add notes, explanations, headers, markdown, or comments.",
        ""
    )
    SYSTEM_PROMPT_REPARO = SYSTEM_PROMPT_REPARO.replace(
        "Keep the exact same numbering, order, and line structure.",
        ""
    )
    SYSTEM_PROMPT_REPARO = SYSTEM_PROMPT_REPARO.replace(
        "Never merge, split, reorder, remove, or duplicate numbered lines.",
        ""
    )
    SYSTEM_PROMPT_REPARO = re.sub(r'\n{3,}', '\n\n', SYSTEM_PROMPT_REPARO).strip()


def formatar_duracao(segundos):
    """Formata segundos em algo legivel: '1h 02m 03s', '5m 12s' ou '8s'."""
    segundos = int(segundos)
    horas, resto = divmod(segundos, 3600)
    minutos, segs = divmod(resto, 60)
    if horas:
        return f"{horas}h {minutos:02d}m {segs:02d}s"
    if minutos:
        return f"{minutos}m {segs:02d}s"
    return f"{segs}s"


def verificar_lm_studio():
    global MODELO_ATIVO
    print(f"{Fore.CYAN}[CHECK] Verificando LM Studio em {LM_STUDIO_MODELS_URL} ...")
    try:
        resposta = requests.get(LM_STUDIO_MODELS_URL, timeout=5)
        if resposta.status_code == 200:
            dados = resposta.json()
            modelos = [m.get("id", "desconhecido") for m in dados.get("data", [])]
            if modelos:
                modelos_chat = [m for m in modelos if "embed" not in m.lower()]
                if modelos_chat:
                    MODELO_ATIVO = modelos_chat[0]
                else:
                    MODELO_ATIVO = modelos[0]
                print(f"{Fore.GREEN}[OK] LM Studio online. Modelo ativo: {MODELO_ATIVO}")
                return True
            else:
                print(f"{Fore.RED}[ERRO] LM Studio online, mas nenhum modelo carregado.")
                return False
        else:
            print(f"{Fore.RED}[ERRO] LM Studio retornou status HTTP {resposta.status_code}.")
            return False
    except Exception as e:
        print(f"{Fore.RED}[ERRO] Não foi possível conectar ao LM Studio: {e}")
        return False


def extrair_traducao_final(conteudo):
    """Extrai a traducao final de uma resposta que pode conter o raciocinio do
    modelo (tags <think>/<thinking>) e um marcador 'FINAL: ...' com a resposta."""
    # Remove blocos de raciocinio completos
    conteudo = re.sub(r'<think(?:ing)?>.*?</think(?:ing)?>', '', conteudo, flags=re.DOTALL | re.IGNORECASE)
    # Remove raciocinio que ficou aberto (truncado pelo max_tokens)
    conteudo = re.sub(r'<think(?:ing)?>.*', '', conteudo, flags=re.DOTALL | re.IGNORECASE).strip()

    # Procura o marcador da resposta final
    m = re.search(r'FINAL\s*:\s*(.+?)(?:\n|$)', conteudo, flags=re.IGNORECASE)
    if m:
        conteudo = m.group(1).strip()
    else:
        # Sem marcador: usa a ultima linha nao vazia (apos o raciocinio)
        linhas_validas = [l.strip() for l in conteudo.split('\n') if l.strip()]
        conteudo = linhas_validas[-1] if linhas_validas else ""

    # Limpa numeração residual (ex: "1. Texto") e markdown/aspas
    m = re.match(r'^\d+[\s.)\-:]+\s*(.+)', conteudo)
    if m:
        conteudo = m.group(1).strip()
    return re.sub(r'\*+|_+', '', conteudo).strip().strip('"').strip("'")


def traduzir_linha_avulsa(texto_eng):
    """Traduz uma única linha com batch size = 1, permitindo que o modelo
    raciocine (chain-of-thought) antes de dar a resposta final. Util para
    linhas que ja falharam na traducao automatica em lote."""
    payload = {
        "model": MODELO_ATIVO,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_REPARO},
            {"role": "user", "content": (
                "This subtitle line failed automatic translation before and needs careful attention. "
                "Think step by step about the best Brazilian Portuguese (PT-BR) translation, considering "
                "the Gundam Universal Century context, tone, and protected terms. Then give your final answer.\n\n"
                f"Line: {texto_eng}\n\n"
                "After your reasoning, output the final translation on its own line in this exact format "
                "(nothing else after it):\nFINAL: <your PT-BR translation>"
            )}
        ],
        "temperature": 0.2,
        "max_tokens": 3000
    }

    max_tentativas = 3
    for tentativa in range(1, max_tentativas + 1):
        try:
            resposta = requests.post(LM_STUDIO_URL, json=payload, timeout=120)
            if resposta.status_code == 200:
                conteudo_bruto = resposta.json()['choices'][0]['message']['content'].strip()
                conteudo = extrair_traducao_final(conteudo_bruto)
                if conteudo:
                    identico = conteudo.strip().lower() == texto_eng.strip().lower()
                    # Frases longas identicas ao original indicam falha real de traducao;
                    # nomes/interjeicoes curtas (ja' identicas em PT-BR) sao aceitas.
                    if not identico or len(texto_eng.strip()) <= 15:
                        return conteudo
            time.sleep(2)
        except Exception as e:
            tqdm.write(f"     {Fore.YELLOW}Erro na tentativa {tentativa}/{max_tentativas}: {e}")
            time.sleep(3)
    return None


def restaurar_tags(traducao, tags):
    """Recoloca as tags ASS originais nos marcadores [T0], [T1]... Se um marcador
    nao for encontrado de forma alguma na traducao, a tag e' preservada no inicio
    da linha para evitar perda de posicionamento/estilo (ex: {\\an8})."""
    for idx_tag, tag in enumerate(tags):
        marcador = f"[T{idx_tag}]"
        if marcador in traducao:
            traducao = traducao.replace(marcador, tag, 1)
            continue

        # Usa lambda no re.sub para evitar erros com barras invertidas e referências de grupo (\1, etc.) no padrão de substituição
        nova_traducao = re.sub(rf'\[?[Tt]{idx_tag}\]?', lambda m: tag, traducao, count=1)
        if nova_traducao != traducao:
            traducao = nova_traducao
        elif traducao.count(tag) < tags.count(tag):
            # Garante a restauração de tags duplicadas perdidas
            traducao = tag + traducao
    return traducao


def executar_reparo():
    print("=" * 80)
    print(f"{Fore.CYAN}    SCRIPT DE REPARO DE FALHAS DE TRADUÇÃO (HEAL TRANSLATION ERRORS)")
    print("=" * 80)

    if not verificar_lm_studio():
        return

    if len(sys.argv) >= 3:
        pasta_originais = sys.argv[1]
        pasta_traduzidos = sys.argv[2]
    else:
        pasta_originais = (
            r"D:\PROJETOS-OPEN\animes"
            r"\Mobile Suit Gundam Unicorn Re0096 (2016) [Season 1] [BD 1080p HEVC OPUS] [Dual-Audio]"
            r"\Season 1\legendas_eng"
        )
        pasta_traduzidos = (
            r"D:\PROJETOS-OPEN\animes"
            r"\Mobile Suit Gundam Unicorn Re0096 (2016) [Season 1] [BD 1080p HEVC OPUS] [Dual-Audio]"
            r"\Season 1\legendas_ptbr"
        )

    if not os.path.exists(pasta_originais) or not os.path.exists(pasta_traduzidos):
        print(f"{Fore.RED}[ERRO] Pastas de legendas não encontradas.")
        return

    arquivos_ptbr = sorted([f for f in os.listdir(pasta_traduzidos) if f.lower().endswith('.ass')])

    if not arquivos_ptbr:
        print(f"{Fore.YELLOW}[AVISO] Nenhum arquivo .ass em: {pasta_traduzidos}")
        return

    # ---- Pre-scan: localiza todas as falhas reparaveis antes de comecar ----
    trabalho = []  # (arquivo, caminho_pt, linhas_pt, linhas_eng, indices_para_reparar)
    total_erros_geral = 0

    print(f"{Fore.CYAN}[SCAN] Procurando falhas de tradução em {len(arquivos_ptbr)} arquivo(s)...")
    for arquivo in arquivos_ptbr:
        caminho_pt = os.path.join(pasta_traduzidos, arquivo)
        nome_eng = arquivo.replace("_PTBR.ass", "_ENG.ass")
        caminho_eng = os.path.join(pasta_originais, nome_eng)

        if not os.path.exists(caminho_eng):
            print(f"{Fore.YELLOW}[AVISO] Pulando {arquivo} (Legenda original correspondente não encontrada).")
            continue

        with open(caminho_pt, 'r', encoding='utf-8', errors='replace') as f:
            linhas_pt = f.readlines()

        with open(caminho_eng, 'r', encoding='utf-8', errors='replace') as f:
            linhas_eng = f.readlines()

        if len(linhas_pt) != len(linhas_eng):
            print(f"{Fore.RED}[ERRO] {arquivo} possui desalinhamento físico de linhas com o original ({len(linhas_pt)} vs {len(linhas_eng)}). Pulando.")
            continue

        indices = [
            i for i in range(len(linhas_pt))
            if linhas_pt[i].startswith("Dialogue:") and "[ERRO_TRADUCAO:" in linhas_pt[i]
        ]

        if indices:
            trabalho.append((arquivo, caminho_pt, linhas_pt, linhas_eng, indices))
            total_erros_geral += len(indices)

    if total_erros_geral == 0:
        print(f"{Fore.GREEN}[OK] Nenhuma falha de tradução encontrada. Nada a reparar.")
        return

    print(f"{Fore.CYAN}[INFO] {total_erros_geral} falha(s) encontrada(s) em {len(trabalho)} arquivo(s). Iniciando reparo...\n")

    total_reparado_geral = 0
    total_falhas_geral = 0
    inicio_total = time.time()

    linhas_relatorio = [
        "RELATORIO DE REPARO DE TRADUCAO - REPARA_ERROS_TRADUCAO",
        f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 80,
    ]

    LIMITE_FALHAS_CONSECUTIVAS = 5
    falhas_consecutivas = 0
    abortado = False

    with tqdm(total=total_erros_geral, desc="Reparo Geral", unit="linha", colour="green", ncols=100, position=0) as barra:
        for idx, (arquivo, caminho_pt, linhas_pt, linhas_eng, indices) in enumerate(trabalho, 1):
            inicio_arquivo = time.time()
            linhas_corrigidas = list(linhas_pt)
            reparos_no_arquivo = 0
            falhas_no_arquivo = 0
            linhas_falhas_persistentes = []

            barra.set_postfix_str(arquivo[:30])
            tqdm.write(f"\n[{idx}/{len(trabalho)}] Analisando: {arquivo} ({len(indices)} falha(s) encontrada(s))")

            for i in indices:
                linha_pt = linhas_pt[i]
                linha_eng = linhas_eng[i]

                partes_pt = linha_pt.split(",", 9)
                partes_eng = linha_eng.split(",", 9)

                if len(partes_pt) != 10 or len(partes_eng) != 10:
                    tqdm.write(f"  {Fore.YELLOW}-> Linha {i+1}: estrutura inesperada, pulando.")
                    falhas_no_arquivo += 1
                    linhas_falhas_persistentes.append(i + 1)
                    barra.update(1)
                    continue

                metadados = ",".join(partes_pt[:9]) + ","
                texto_original = partes_eng[9].rstrip("\n")

                # Extrai tags e gera placeholders
                tags = re.findall(r'\{[^}]+\}', texto_original)

                texto_limpo = texto_original
                for idx_tag, tag in enumerate(tags):
                    texto_limpo = texto_limpo.replace(tag, f"[T{idx_tag}]", 1)

                tqdm.write(f"  -> Reparando linha {i+1} [ENG: {texto_limpo[:45]}...]")

                traducao = traduzir_linha_avulsa(texto_limpo)

                if traducao:
                    traducao = restaurar_tags(traducao, tags)
                    linhas_corrigidas[i] = f"{metadados}{traducao}\n"
                    reparos_no_arquivo += 1
                    falhas_consecutivas = 0
                    tqdm.write(f"     {Fore.GREEN}OK: {traducao[:45]}...")
                else:
                    falhas_no_arquivo += 1
                    linhas_falhas_persistentes.append(i + 1)
                    falhas_consecutivas += 1
                    tqdm.write(f"     {Fore.RED}FALHA (mantido fallback)")
                    if falhas_consecutivas >= LIMITE_FALHAS_CONSECUTIVAS:
                        tqdm.write(
                            f"\n{Fore.RED}[ABORTADO] {falhas_consecutivas} falhas consecutivas. "
                            f"LM Studio pode estar offline/instavel. Interrompendo reparo."
                        )
                        abortado = True

                barra.update(1)
                if abortado:
                    break

            tempo_arquivo = time.time() - inicio_arquivo

            if reparos_no_arquivo > 0:
                with open(caminho_pt, 'w', encoding='utf-8') as f:
                    f.writelines(linhas_corrigidas)
                tqdm.write(f"  {Fore.GREEN}[SALVO] {arquivo} | Reparados: {reparos_no_arquivo} | Falhas: {falhas_no_arquivo} | Tempo: {formatar_duracao(tempo_arquivo)}")
            else:
                tqdm.write(f"  {Fore.BLUE}[OK] Nenhuma correção aplicada em {arquivo} | Falhas: {falhas_no_arquivo} | Tempo: {formatar_duracao(tempo_arquivo)}")

            info_linhas = f" | Linhas com falha: {', '.join(map(str, linhas_falhas_persistentes))}" if linhas_falhas_persistentes else ""
            linhas_relatorio.append(
                f"{arquivo} | Falhas encontradas: {len(indices)} | Reparados: {reparos_no_arquivo} | "
                f"Falhas persistentes: {falhas_no_arquivo} | Tempo: {formatar_duracao(tempo_arquivo)}{info_linhas}"
            )

            total_reparado_geral += reparos_no_arquivo
            total_falhas_geral += falhas_no_arquivo

            if abortado:
                break

    tempo_total = time.time() - inicio_total

    if abortado:
        linhas_relatorio.append("=" * 80)
        linhas_relatorio.append(
            f"[ABORTADO] Execucao interrompida apos {LIMITE_FALHAS_CONSECUTIVAS} falhas consecutivas "
            f"(possivel queda do LM Studio). Arquivos restantes nao foram processados."
        )

    linhas_relatorio.append("=" * 80)
    linhas_relatorio.append(
        f"TOTAL: {total_erros_geral} falha(s) | {total_reparado_geral} reparada(s) | "
        f"{total_falhas_geral} persistente(s) | Tempo total: {formatar_duracao(tempo_total)}"
    )

    with open(RELATORIO_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_relatorio) + "\n")

    print("\n" + "=" * 80)
    if abortado:
        print(f"{Fore.RED}[ABORTADO] Reparo interrompido por falhas consecutivas no LM Studio.")
    else:
        print(f"{Fore.GREEN}[CONCLUÍDO] Reparo de tradução finalizado!")
    print(f"{Fore.GREEN}Falhas encontradas: {total_erros_geral} | Reparadas: {total_reparado_geral} | Persistentes: {total_falhas_geral}")
    print(f"{Fore.CYAN}Tempo total: {formatar_duracao(tempo_total)}")
    print(f"{Fore.CYAN}Relatório: {RELATORIO_FILE}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        executar_reparo()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[AVISO] Interrompido pelo operador.")
        sys.exit(0)
