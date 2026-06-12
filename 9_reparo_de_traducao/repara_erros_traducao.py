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
import argparse
import requests
from datetime import datetime
from tqdm import tqdm
from colorama import init, Fore, Style

init(autoreset=True)

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
LM_STUDIO_MODELS_URL = "http://localhost:1234/v1/models"
MODELO_ATIVO = "local-model"

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PASTA_RAIZ = os.path.dirname(PASTA_SCRIPT)
PASTA_UNICORN = os.path.join(PASTA_RAIZ, "4_tradutor_ia_gemma4", "tradutor_gundam_unicornio")
PASTA_ORIGIN_ZH = os.path.join(PASTA_RAIZ, "4_tradutor_ia_gemma4", "tradutor_gundam_origin_zh")
RELATORIO_FILE = os.path.join(PASTA_SCRIPT, "relatorio_reparo.txt")

SUFIXOS_ORIGEM = {
    "eng": ("_ENG.ass",),
    "zh": (".chs.ass", ".cht.ass"),
}

PADRAO_CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
MODO_REPARO = "eng"
SYSTEM_PROMPT_REPARO = ""


def adaptar_prompt_reparo(system_prompt: str) -> str:
    prompt = system_prompt
    if "numbered subtitle lines" in prompt or "linhas de legenda numeradas" in prompt or "CRITICAL RULES" in prompt or "REGRAS CRÍTICAS" in prompt:
        prompt = prompt.replace(
            "Translate the following numbered subtitle lines into Brazilian Portuguese (PT-BR).",
            "Translate the subtitle line into Brazilian Portuguese (PT-BR)."
        )
        prompt = prompt.replace(
            "Traduza as linhas de legenda numeradas fornecidas do Chinês Simplificado (CHS) para o Português do Brasil (PT-BR) de forma fluida e natural.",
            "Traduza a linha de legenda fornecida do Chinês Simplificado (CHS) para o Português do Brasil (PT-BR) de forma fluida e natural."
        )
        prompt = prompt.replace(
            "Return ONLY the numbered translated lines. Do not add notes, explanations, headers, markdown, or comments.",
            ""
        )
        prompt = prompt.replace(
            "2. Responda APENAS com as linhas traduzidas numeradas. Não adicione observações, explicações, introduções ou comentários.",
            "2. Responda APENAS com a tradução final em PT-BR, sem observações ou comentários."
        )
        prompt = prompt.replace(
            "Keep the exact same numbering, order, and line structure.",
            ""
        )
        prompt = prompt.replace(
            "1. Mantenha exatamente a mesma numeração, ordem e estrutura de linhas (ex: '1. tradução', '2. tradução').",
            ""
        )
        prompt = prompt.replace(
            "Never merge, split, reorder, remove, or duplicate numbered lines.",
            ""
        )
        prompt = prompt.replace(
            "3. Nunca mescle, divida, reordene, remova ou duplique as linhas numeradas.",
            ""
        )
        prompt = re.sub(r'\n{3,}', '\n\n', prompt).strip()
    return prompt


def carregar_prompt_reparo(modo: str) -> str:
    fallback = (
        "You are an expert subtitler for Japanese anime, specializing in the Gundam Universal Century timeline.\n"
        "Translate the subtitle line into Brazilian Portuguese (PT-BR).\n"
    )
    pasta = PASTA_ORIGIN_ZH if modo == "zh" else PASTA_UNICORN
    modulo = "batch_translator_origin_zh" if modo == "zh" else "batch_translator_unicorn"
    if pasta not in sys.path:
        sys.path.insert(0, pasta)
    try:
        mod = __import__(modulo, fromlist=["SYSTEM_PROMPT"])
        return adaptar_prompt_reparo(getattr(mod, "SYSTEM_PROMPT", fallback))
    except ImportError:
        return adaptar_prompt_reparo(fallback)
    finally:
        if sys.path and sys.path[0] == pasta:
            sys.path.pop(0)


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


def processar_traducao_reparada(texto_orig: str, traducao: str, modo: str):
    """Pós-processamento e validação específicos por idioma de origem."""
    if modo == "zh":
        if PASTA_ORIGIN_ZH not in sys.path:
            sys.path.insert(0, PASTA_ORIGIN_ZH)
        try:
            from batch_translator_origin_zh import post_processar_traducao, validar_traducao
            traducao = post_processar_traducao(traducao)
            if not validar_traducao(texto_orig, traducao):
                return None
        finally:
            if sys.path and sys.path[0] == PASTA_ORIGIN_ZH:
                sys.path.pop(0)
    elif PADRAO_CJK.search(traducao):
        return None
    return traducao


def ler_arquivo_legenda(caminho: str, modo: str):
    if modo == "zh":
        for encoding in ("utf-8-sig", "utf-8", "gb18030", "big5", "cp936"):
            try:
                with open(caminho, "r", encoding=encoding) as f:
                    return f.readlines()
            except UnicodeDecodeError:
                continue
    with open(caminho, "r", encoding="utf-8", errors="replace") as f:
        return f.readlines()


def resolver_arquivo_original(arquivo_ptbr: str, pasta_originais: str, modo: str):
    if not arquivo_ptbr.lower().endswith("_ptbr.ass"):
        return None, None
    stem = arquivo_ptbr[:-9]
    for sufixo in SUFIXOS_ORIGEM[modo]:
        nome = stem + sufixo
        caminho = os.path.join(pasta_originais, nome)
        if os.path.exists(caminho):
            return caminho, nome
    return None, None


def parse_args():
    parser = argparse.ArgumentParser(
        description="Repara linhas [ERRO_TRADUCAO: ...] em legendas *_PTBR.ass via LM Studio."
    )
    parser.add_argument("pasta_originais", nargs="?", help="Pasta das legendas de origem")
    parser.add_argument("pasta_traduzidos", nargs="?", help="Pasta das legendas *_PTBR.ass")
    parser.add_argument(
        "--modo",
        choices=("eng", "zh"),
        default="eng",
        help="eng: origem _ENG.ass (Unicorn) | zh: origem .chs/.cht.ass (Gundam The Origin)",
    )
    return parser.parse_args()


def traduzir_linha_avulsa(texto_orig, modo: str = "eng"):
    """Traduz uma única linha com batch size = 1, permitindo que o modelo
    raciocine (chain-of-thought) antes de dar a resposta final. Util para
    linhas que ja falharam na traducao automatica em lote."""
    if modo == "zh":
        instrucao_user = (
            "This Chinese (CHS/CHT) subtitle line failed automatic translation before and needs careful attention. "
            "Think step by step about the best Brazilian Portuguese (PT-BR) translation, considering "
            "Gundam The Origin / Universal Century context, tone, protected terms, and the glossary. "
            "The final output must NOT contain Chinese characters.\n\n"
            f"Line: {texto_orig}\n\n"
            "After your reasoning, output the final translation on its own line in this exact format "
            "(nothing else after it):\nFINAL: <your PT-BR translation>"
        )
    else:
        instrucao_user = (
            "This subtitle line failed automatic translation before and needs careful attention. "
            "Think step by step about the best Brazilian Portuguese (PT-BR) translation, considering "
            "the Gundam Universal Century context, tone, and protected terms. Then give your final answer.\n\n"
            f"Line: {texto_orig}\n\n"
            "After your reasoning, output the final translation on its own line in this exact format "
            "(nothing else after it):\nFINAL: <your PT-BR translation>"
        )

    payload = {
        "model": MODELO_ATIVO,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_REPARO},
            {"role": "user", "content": instrucao_user}
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
                conteudo = processar_traducao_reparada(texto_orig, conteudo, modo)
                if conteudo:
                    identico = conteudo.strip().lower() == texto_orig.strip().lower()
                    # Frases longas identicas ao original indicam falha real de traducao;
                    # nomes/interjeicoes curtas (ja' identicas em PT-BR) sao aceitas.
                    if not identico or len(texto_orig.strip()) <= 15:
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
    global SYSTEM_PROMPT_REPARO, MODO_REPARO

    args = parse_args()
    MODO_REPARO = args.modo
    SYSTEM_PROMPT_REPARO = carregar_prompt_reparo(args.modo)

    print("=" * 80)
    modo_label = "ENG -> PT-BR" if args.modo == "eng" else "CHS/CHT -> PT-BR (Gundam The Origin)"
    print(f"{Fore.CYAN}    SCRIPT DE REPARO DE FALHAS DE TRADUÇÃO ({modo_label})")
    print("=" * 80)

    if not verificar_lm_studio():
        return

    if args.pasta_originais and args.pasta_traduzidos:
        pasta_originais = args.pasta_originais
        pasta_traduzidos = args.pasta_traduzidos
    elif args.modo == "zh":
        pasta_originais = (
            r"D:\PROJETOS-OPEN\animes\[POPGO][Gundam_The_Origin_TV][MKV+ASS]"
            r"\[POPGO][Mobile_Suit_Gundam_The_Origin_Advent_of_the_Red_Comet][1080p][Webrip][ASS][CHS_CHT]"
        )
        pasta_traduzidos = (
            r"D:\PROJETOS-OPEN\animes\[POPGO][Gundam_The_Origin_TV][MKV+ASS]"
            r"\legendas_ptbr"
        )
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
    trabalho = []  # (arquivo, caminho_pt, linhas_pt, linhas_orig, indices_para_reparar)
    total_erros_geral = 0

    print(f"{Fore.CYAN}[SCAN] Procurando falhas de tradução em {len(arquivos_ptbr)} arquivo(s)...")
    for arquivo in arquivos_ptbr:
        caminho_pt = os.path.join(pasta_traduzidos, arquivo)
        caminho_orig, nome_orig = resolver_arquivo_original(arquivo, pasta_originais, args.modo)

        if not caminho_orig:
            print(
                f"{Fore.YELLOW}[AVISO] Pulando {arquivo} "
                f"(legenda original não encontrada; tentou: {', '.join(SUFIXOS_ORIGEM[args.modo])})."
            )
            continue

        linhas_pt = ler_arquivo_legenda(caminho_pt, "eng")
        linhas_orig = ler_arquivo_legenda(caminho_orig, args.modo)

        if len(linhas_pt) != len(linhas_orig):
            print(
                f"{Fore.RED}[ERRO] {arquivo} possui desalinhamento físico de linhas com {nome_orig} "
                f"({len(linhas_pt)} vs {len(linhas_orig)}). Pulando."
            )
            continue

        indices = [
            i for i in range(len(linhas_pt))
            if linhas_pt[i].startswith("Dialogue:") and "[ERRO_TRADUCAO:" in linhas_pt[i]
        ]

        if indices:
            trabalho.append((arquivo, caminho_pt, linhas_pt, linhas_orig, indices))
            total_erros_geral += len(indices)

    if total_erros_geral == 0:
        print(f"{Fore.GREEN}[OK] Nenhuma falha de tradução encontrada. Nada a reparar.")
        return

    print(f"{Fore.CYAN}[INFO] {total_erros_geral} falha(s) encontrada(s) em {len(trabalho)} arquivo(s). Iniciando reparo...\n")

    total_reparado_geral = 0
    total_falhas_geral = 0
    inicio_total = time.time()

    linhas_relatorio = [
        f"RELATORIO DE REPARO DE TRADUCAO - REPARA_ERROS_TRADUCAO ({modo_label})",
        f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 80,
    ]

    LIMITE_FALHAS_CONSECUTIVAS = 5
    falhas_consecutivas = 0
    abortado = False

    with tqdm(total=total_erros_geral, desc="Reparo Geral", unit="linha", colour="green", ncols=100, position=0) as barra:
        for idx, (arquivo, caminho_pt, linhas_pt, linhas_orig, indices) in enumerate(trabalho, 1):
            inicio_arquivo = time.time()
            linhas_corrigidas = list(linhas_pt)
            reparos_no_arquivo = 0
            falhas_no_arquivo = 0
            linhas_falhas_persistentes = []

            barra.set_postfix_str(arquivo[:30])
            tqdm.write(f"\n[{idx}/{len(trabalho)}] Analisando: {arquivo} ({len(indices)} falha(s) encontrada(s))")

            for i in indices:
                linha_pt = linhas_pt[i]
                linha_orig = linhas_orig[i]

                partes_pt = linha_pt.split(",", 9)
                partes_orig = linha_orig.split(",", 9)

                if len(partes_pt) != 10 or len(partes_orig) != 10:
                    tqdm.write(f"  {Fore.YELLOW}-> Linha {i+1}: estrutura inesperada, pulando.")
                    falhas_no_arquivo += 1
                    linhas_falhas_persistentes.append(i + 1)
                    barra.update(1)
                    continue

                metadados = ",".join(partes_pt[:9]) + ","
                texto_original = partes_orig[9].rstrip("\n")

                tags = re.findall(r'\{[^}]+\}', texto_original)

                texto_limpo = texto_original
                for idx_tag, tag in enumerate(tags):
                    texto_limpo = texto_limpo.replace(tag, f"[T{idx_tag}]", 1)

                rotulo = "CHS" if args.modo == "zh" else "ENG"
                tqdm.write(f"  -> Reparando linha {i+1} [{rotulo}: {texto_limpo[:45]}...]")

                traducao = traduzir_linha_avulsa(texto_limpo, args.modo)

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
