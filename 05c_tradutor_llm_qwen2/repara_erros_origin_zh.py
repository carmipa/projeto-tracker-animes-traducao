#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MODULO: repara_erros_origin_zh.py
Verifica legendas traduzidas (*_PTBR.ass) de Gundam The Origin em busca de marcadores "[ERRO_TRADUCAO: ...]"
e as re-traduz avulsamente (lote = 1) com suporte a raciocínio (CoT) via LM Studio.
Garante o salvamento das traduções reparadas no cache persistente (traducao_cache_origin_zh.json) e
restauração perfeita das tags Aegisub.

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
from colorama import init, Fore

init(autoreset=True)

# Garante que a pasta atual esteja no path para importar o tradutor
PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
if PASTA_SCRIPT not in sys.path:
    sys.path.insert(0, PASTA_SCRIPT)

try:
    import batch_translator_origin_zh as translator
except ImportError as e:
    print(f"\n{Fore.RED}[ERRO] Não foi possível importar 'batch_translator_origin_zh.py'. Certifique-se de que ele está na mesma pasta. Detalhe: {e}")
    sys.exit(1)

# Caminho do relatório de reparos local
RELATORIO_FILE = os.path.join(PASTA_SCRIPT, "relatorio_reparo_origin_zh.txt")


def tornar_safe_console(texto: str) -> str:
    """Substitui caracteres não suportados pelo console por '?' para evitar erros de encoding."""
    enc = sys.stdout.encoding or 'utf-8'
    try:
        texto.encode(enc)
        return texto
    except UnicodeEncodeError:
        return texto.encode(enc, errors='replace').decode(enc)


def adaptar_prompt_reparo(prompt: str) -> str:
    """Adapta o prompt do tradutor de lote para a tradução avulsa de linha única."""
    if not prompt:
        return ""
    prompt = prompt.replace(
        "Traduza as linhas de legenda numeradas fornecidas do Chinês Simplificado (CHS) para o Português do Brasil (PT-BR) de forma fluida e natural.",
        "Traduza a linha de legenda fornecida do Chinês Simplificado (CHS) para o Português do Brasil (PT-BR) de forma fluida e natural."
    )
    prompt = prompt.replace(
        "2. Responda APENAS com as linhas traduzidas numeradas. Não adicione observações, explicações, introduções ou comentários.",
        "2. Responda APENAS com a tradução final em PT-BR, sem observações ou comentários."
    )
    prompt = prompt.replace(
        "1. Mantenha exatamente a mesma numeração, ordem e estrutura de linhas (ex: '1. tradução', '2. tradução').",
        ""
    )
    prompt = prompt.replace(
        "3. Nunca mescle, divida, reordene, remova ou duplique as linhas numeradas.",
        ""
    )
    return re.sub(r'\n{3,}', '\n\n', prompt).strip()


def extrair_traducao_final(conteudo: str) -> str:
    """Extrai a tradução final removendo o raciocínio (tags <think>) e marcadores 'FINAL:'."""
    # Remove blocos de raciocínio
    conteudo = re.sub(r'<think(?:ing)?>.*?</think(?:ing)?>', '', conteudo, flags=re.DOTALL | re.IGNORECASE)
    conteudo = re.sub(r'<think(?:ing)?>.*', '', conteudo, flags=re.DOTALL | re.IGNORECASE).strip()

    # Procura todos os marcadores FINAL:
    candidatos = re.findall(r'FINAL\s*:\s*(.+?)(?:\n|$)', conteudo, flags=re.IGNORECASE)
    candidato_escolhido = None
    
    if candidatos:
        # Preferimos o último candidato que não contenha ideogramas chineses (CJK)
        for cand in reversed(candidatos):
            cand_clean = cand.strip()
            if not translator.PADRAO_CJK.search(cand_clean):
                candidato_escolhido = cand_clean
                break
        
        # Se todos contiverem CJK, usamos o último candidato gerado
        if candidato_escolhido is None:
            candidato_escolhido = candidatos[-1].strip()
            
        conteudo = candidato_escolhido
    else:
        # Pega a última linha não vazia
        linhas = [l.strip() for l in conteudo.split('\n') if l.strip()]
        conteudo = linhas[-1] if linhas else ""

    # Limpa numeração
    m = re.match(r'^\d+[\s.)\-:]+\s*(.+)', conteudo)
    if m:
        conteudo = m.group(1).strip()

    return re.sub(r'\*+|_+', '', conteudo).strip().strip('"').strip("'")


def traduzir_linha_avulsa(texto_orig: str, model_id: str, system_prompt: str) -> str:
    """Traduz uma única linha com chain-of-thought, retornando a tradução limpa."""
    instrucao_user = (
        "Esta linha de legenda em chinês falhou na tradução automática anterior e precisa de atenção cuidadosa. "
        "Pense passo a passo sobre a melhor tradução para o Português do Brasil (PT-BR), considerando o contexto "
        "de Gundam The Origin / Universal Century, o tom, os termos protegidos e o glossário. "
        "A saída final NÃO deve conter caracteres chineses.\n\n"
        f"Linha: {texto_orig}\n\n"
        "Após o seu raciocínio, forneça a tradução final em sua própria linha neste formato exato "
        "(nada mais depois dele):\nFINAL: <sua tradução em PT-BR>"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                "Esta linha de legenda em chinês falhou na tradução automática anterior e precisa de atenção cuidadosa. "
                "Pense passo a passo sobre a melhor tradução para o Português do Brasil (PT-BR), considerando o contexto "
                "de Gundam The Origin / Universal Century, o tom, os termos protegidos e o glossário. "
                "A saída final NÃO deve conter caracteres chineses.\n\n"
                "Linha: 敌人的抵抗基本上被排除了...\n\n"
                "Após o seu raciocínio, forneça a tradução final em sua própria linha neste formato exato "
                "(nada mais depois dele):\nFINAL: <sua tradução em PT-BR>"
            )
        },
        {
            "role": "assistant",
            "content": (
                "Raciocínio:\n"
                "A frase '敌人的抵抗基本上被排除了...' fala sobre a resistência do inimigo que foi basicamente eliminada. "
                "No contexto de combate em Gundam, o tom deve ser militar e sério. A tradução fluida e natural é 'A resistência dos inimigos foi praticamente eliminada...'. "
                "Não há caracteres chineses na tradução final.\n\n"
                "FINAL: A resistência dos inimigos foi praticamente eliminada..."
            )
        },
        {"role": "user", "content": instrucao_user}
    ]

    payload = {
        "model": model_id,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 3000
    }

    for tentativa in range(1, 4):
        try:
            payload["temperature"] = 0.2 + (tentativa - 1) * 0.15
            resposta = requests.post(translator.LM_STUDIO_URL, json=payload, timeout=120)
            if resposta.status_code == 200:
                conteudo_bruto = resposta.json()['choices'][0]['message']['content'].strip()
                conteudo = extrair_traducao_final(conteudo_bruto)
                conteudo = translator.post_processar_traducao(conteudo)
                if conteudo and translator.validar_traducao(texto_orig, conteudo):
                    identico = conteudo.strip().lower() == texto_orig.strip().lower()
                    if not identico or len(texto_orig.strip()) <= 15:
                        return conteudo
            time.sleep(2)
        except Exception as e:
            tqdm.write(f"     {Fore.YELLOW}Erro na tentativa {tentativa}/3: {e}")
            time.sleep(3)
    return None


def resolver_arquivo_original(arquivo_ptbr: str, pasta_originais: str, padrao: str):
    if not arquivo_ptbr.lower().endswith("_ptbr.ass"):
        return None
    # Substitui "_PTBR.ass" pelo padrão original (ex: ".chs.ass")
    nome_orig = re.sub(r'_ptbr\.ass$', padrao, arquivo_ptbr, flags=re.IGNORECASE)
    caminho = os.path.join(pasta_originais, nome_orig)
    if os.path.exists(caminho):
        return caminho
    return None


def obter_diretorio_operador(descricao, padrao):
    print(f"{descricao} (ENTER = {padrao}): ", end="")
    entrada = input().strip()
    if not entrada:
        return padrao
    return os.path.abspath(entrada)


def executar_reparo():
    parser = argparse.ArgumentParser(
        description="Repara legendas *_PTBR.ass de Gundam Origin com erros de tradução avulsa."
    )
    parser.add_argument("--originais", help="Pasta com as legendas originais .chs.ass")
    parser.add_argument("--traduzidas", help="Pasta com as legendas traduzidas *_PTBR.ass")
    parser.add_argument("--modelo", help="Força modelo específico do LM Studio")
    parser.add_argument("--padrao", default=".chs.ass", help="Sufixo de legenda original")
    args = parser.parse_args()

    print("=" * 80)
    print(f"{Fore.CYAN}    REPARADOR LOCAL GUNDAM THE ORIGIN ZH -> PT-BR")
    print("=" * 80)

    # 1. Verifica LM Studio e carrega modelo
    translator.verificar_lm_studio(args.modelo)
    model_id = translator.MODELO_ATIVO

    # 2. Carrega cache
    translator.carregar_cache()

    # 3. Resolve diretórios
    caminho_padrao_origem = (
        r"D:\PROJETOS-OPEN\animes\[POPGO][Gundam_The_Origin_TV][MKV+ASS]"
        r"\[POPGO][Mobile_Suit_Gundam_The_Origin_Advent_of_the_Red_Comet][1080p][Webrip][ASS][CHS_CHT]"
    )
    caminho_padrao_saida = (
        r"D:\PROJETOS-OPEN\animes\[POPGO][Gundam_The_Origin_TV][MKV+ASS]"
        r"\ptbr"
    )

    pasta_origem = args.originais or obter_diretorio_operador("Pasta com legendas originais", caminho_padrao_origem)
    pasta_saida = args.traduzidas or obter_diretorio_operador("Pasta com legendas traduzidas", caminho_padrao_saida)

    if not os.path.exists(pasta_origem) or not os.path.exists(pasta_saida):
        print(f"{Fore.RED}[ERRO] Diretório de entrada ou saída não existe.")
        return

    # 4. Lista arquivos
    arquivos_ptbr = sorted([f for f in os.listdir(pasta_saida) if f.lower().endswith('.ass')])
    if not arquivos_ptbr:
        print(f"{Fore.YELLOW}[AVISO] Nenhuma legenda .ass localizada em: {pasta_saida}")
        return

    # 5. Pre-scan
    trabalho = []
    total_erros = 0
    system_prompt = adaptar_prompt_reparo(translator.SYSTEM_PROMPT)

    print(f"{Fore.CYAN}[SCAN] Escaneando falhas em {len(arquivos_ptbr)} arquivos...")
    for arquivo in arquivos_ptbr:
        caminho_pt = os.path.join(pasta_saida, arquivo)
        caminho_orig = resolver_arquivo_original(arquivo, pasta_origem, args.padrao)

        if not caminho_orig:
            continue

        linhas_pt, _ = translator.ler_arquivo_legenda(caminho_pt)
        linhas_orig, _ = translator.ler_arquivo_legenda(caminho_orig)

        if len(linhas_pt) != len(linhas_orig):
            print(f"{Fore.RED}[ERRO] {arquivo} possui desalinhamento com {os.path.basename(caminho_orig)}. Pulando.")
            continue

        indices = [
            i for i in range(len(linhas_pt))
            if linhas_pt[i].startswith("Dialogue:") and "[ERRO_TRADUCAO:" in linhas_pt[i]
        ]

        if indices:
            trabalho.append((arquivo, caminho_pt, linhas_pt, linhas_orig, indices))
            total_erros += len(indices)

    if total_erros == 0:
        print(f"{Fore.GREEN}[SUCESSO] Nenhuma linha com [ERRO_TRADUCAO:] localizada!")
        return

    print(f"{Fore.CYAN}[INFO] Localizadas {total_erros} falhas para reparar. Iniciando...")

    total_reparados = 0
    total_falhas = 0
    tempo_inicio = time.time()
    linhas_relatorio = [
        "RELATORIO DE REPARO LOCAL - GUNDAM THE ORIGIN ZH",
        f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Modelo: {model_id}",
        "=" * 80,
    ]

    with tqdm(total=total_erros, desc="Reparando legendas", unit="linha", colour="green", ncols=100) as barra:
        for idx, (arquivo, caminho_pt, linhas_pt, linhas_orig, indices) in enumerate(trabalho, 1):
            linhas_corrigidas = list(linhas_pt)
            reparados_arq = 0
            falhas_arq = 0
            linhas_falhas = []

            barra.set_postfix_str(arquivo[:30])
            tqdm.write(f"\n[{idx}/{len(trabalho)}] Processando: {arquivo}")

            for i in indices:
                linha_pt = linhas_pt[i]
                linha_orig = linhas_orig[i]

                partes_pt = [p.strip() for p in linha_pt.split(",", 9)]
                partes_orig = [p.strip() for p in linha_orig.split(",", 9)]

                if len(partes_pt) != 10 or len(partes_orig) != 10:
                    falhas_arq += 1
                    barra.update(1)
                    continue

                metadados = ",".join(linha_pt.split(",", 9)[:9]) + ","
                texto_original = linha_orig.split(",", 9)[9].rstrip("\n")

                # Mascara tags
                texto_limpo, tags = translator.mascarar_tags(texto_original)

                tqdm.write(f"  -> Linha {i+1} [CHS: {tornar_safe_console(texto_limpo[:45])}...]")

                traducao = traduzir_linha_avulsa(texto_limpo, model_id, system_prompt)

                if traducao:
                    # Restaura tags
                    trad_final = translator.restaurar_tags(traducao, tags)
                    linhas_corrigidas[i] = f"{metadados}{trad_final}\n"
                    reparados_arq += 1

                    # IMPORTANTE: Salva no cache com lock para uso futuro!
                    original_masc, _ = translator.mascarar_tags(texto_limpo)
                    traducao_masc, _ = translator.mascarar_tags(traducao)
                    if original_masc and translator.validar_traducao(original_masc, traducao_masc):
                        translator.atualizar_cache(original_masc, traducao_masc)

                    tqdm.write(f"     {Fore.GREEN}OK: {trad_final[:45]}...")
                else:
                    falhas_arq += 1
                    linhas_falhas.append(i + 1)
                    tqdm.write(f"     {Fore.RED}FALHA (mantida)")

                barra.update(1)

            if reparados_arq > 0:
                with open(caminho_pt, 'w', encoding='utf-8') as f:
                    f.writelines(linhas_corrigidas)
                tqdm.write(f"  {Fore.GREEN}[SALVO] {arquivo} | Reparados: {reparados_arq} | Falhas: {falhas_arq}")
            else:
                tqdm.write(f"  {Fore.BLUE}[INFO] Nenhuma alteração em {arquivo}")

            info_err = f" (Linhas falhas: {linhas_falhas})" if linhas_falhas else ""
            linhas_relatorio.append(
                f"{arquivo} | Erros: {len(indices)} | Reparados: {reparados_arq} | Falhas: {falhas_arq}{info_err}"
            )

            total_reparados += reparados_arq
            total_falhas += falhas_arq

    # Grava o cache consolidado no final
    translator.salvar_cache()

    tempo_total = time.time() - tempo_inicio
    m, s = divmod(int(tempo_total), 60)
    duracao_str = f"{m}m {s}s" if m > 0 else f"{s}s"

    linhas_relatorio.append("=" * 80)
    linhas_relatorio.append(
        f"TOTAL: {total_erros} erros | {total_reparados} reparados | {total_falhas} falhas | Tempo: {duracao_str}"
    )

    with open(RELATORIO_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_relatorio) + "\n")

    print("\n" + "=" * 80)
    print(f"{Fore.GREEN}[CONCLUÍDO] Reparo de Gundam Origin finalizado!")
    print(f"Erros detectados: {total_erros} | Reparados: {total_reparados} | Falhas persistentes: {total_falhas}")
    print(f"Relatório gravado em: {RELATORIO_FILE}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        executar_reparo()
    except KeyboardInterrupt:
        translator.salvar_cache()
        print(f"\n{Fore.YELLOW}[AVISO] Operação cancelada. Cache parcial salvo.")
        sys.exit(0)
