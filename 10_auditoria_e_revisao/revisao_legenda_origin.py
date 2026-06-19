#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: revisao_legenda_origin.py (Adaptado para pipeline Francês)
Revisa e corrige erros específicos de lore/tradução nas legendas de Gundam Origin.
- Corrige os arquivos de legenda .ass na pasta legendas_fr/traducao.
- Opcionalmente remuxa de volta para os MKVs originais em uma pasta 'corrigidos'.
- Gera um Log de Auditoria ao final.

Author: Antigravity + Paulo
Data: Junho 2026
"""

import os
import re
import sys
import shutil
import subprocess
import datetime
from colorama import init, Fore, Style

init(autoreset=True)

class TeeLogger(object):
    """
    Redireciona o stdout para capturar todos os prints e gravar em arquivo de log,
    removendo os códigos ANSI (cores).
    """
    def __init__(self, original_stdout):
        self.terminal = original_stdout
        self.log = []
        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def write(self, message):
        self.terminal.write(message)
        self.log.append(self.ansi_escape.sub('', message))

    def flush(self):
        self.terminal.flush()

original_stdout = sys.stdout
logger_obj = TeeLogger(original_stdout)
sys.stdout = logger_obj

if sys.version_info >= (3, 7):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Caminhos padrão (podem ser ajustados conforme o projeto)
PASTA_LEGENDA_PADRAO = r"C:\animes\Mobile_Suit_Gundam_The_Origin_Advent_of_the_Red_Comet\legendas_ptbr"
PASTA_ANIME_PADRAO = r"C:\animes\Mobile_Suit_Gundam_The_Origin_Advent_of_the_Red_Comet"

# Bug 01 — Padrões de metadados/créditos parasitas de fansub
PADROES_METADADOS_FANSUB = [
    re.compile(r"(?i)traduz(?:ido|ção|ao)\s+por"),
    re.compile(r"(?i)dedicad[oa]\s+a\b"),
    re.compile(r"(?i)\bagradecimento"),
    re.compile(r"(?i)\bfansub\b"),
    re.compile(r"(?i)créditos?\s+da\s+(?:tradução|traducao)"),
    re.compile(r"(?i)subtitles?\s+by\b"),
    re.compile(r"(?i)translated?\s+by\b"),
    re.compile(r"(?i)\bin memoriam\b"),
    re.compile(r"(?i)\bencoded?\s+by\b"),
    re.compile(r"(?i)\b(?:raw|qc|timer|editor)\s+by\b"),
    re.compile(r"(?i)produ[çc][aã]o\s+das\s+legendas"),
    re.compile(r"(?i)\bdublagem\s+d[ao]\b"),
    re.compile(r"(?i)bbs\.popgo\.org"),
    re.compile(r"(?i)https?://"),
    re.compile(r"(?i)^legendas:\s+\w"),
    re.compile(r"(?i)\bYW7\b"),
    re.compile(r"(?i)\bSHINJICO\b"),
    re.compile(r"(?i)Crystal\s+Computer\s+Fairy\s+Tale"),
    re.compile(r"(?i)Tri\s+(?:Yw7|Yamato)\s+Shinjico"),
]

def limpar_tags_ass(texto):
    """Remove todas as tags ASS {\\...} do texto para análise do conteúdo puro."""
    return re.sub(r'\{[^}]*\}', '', texto)

def eh_metadado_fansub(texto_dialogo):
    """Retorna True se o texto contém créditos/dedicatórias de fansub."""
    texto_puro = limpar_tags_ass(texto_dialogo)
    return any(p.search(texto_puro) for p in PADROES_METADADOS_FANSUB)

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

def obter_diretorio_obrigatorio(mensagem_prompt, padrao_caminho=None):
    while True:
        sufixo_padrao = f"\n  (ENTER = {padrao_caminho})" if padrao_caminho else ""
        entrada = input(f"{Fore.YELLOW}{mensagem_prompt}{sufixo_padrao}\n> {Style.RESET_ALL}").strip()
        entrada = entrada.strip('"').strip("'")
        if not entrada and padrao_caminho:
            return padrao_caminho
        if not entrada:
            continue
        if not os.path.isdir(entrada):
            print(f"{Fore.RED}[ERRO] Diretório não existe: {entrada}")
            continue
        return entrada

def obter_pasta_saida(mensagem_prompt, padrao_caminho=None):
    """Pede uma pasta de saída; cria-a se não existir."""
    while True:
        sufixo_padrao = f"\n  (ENTER = {padrao_caminho})" if padrao_caminho else ""
        entrada = input(f"{Fore.YELLOW}{mensagem_prompt}{sufixo_padrao}\n> {Style.RESET_ALL}").strip()
        entrada = entrada.strip('"').strip("'")
        if not entrada and padrao_caminho:
            entrada = padrao_caminho
        if not entrada:
            continue
        os.makedirs(entrada, exist_ok=True)
        return entrada

def aplicar_correcao_linha_ass(texto_dialogo):
    """Aplica as correções determinísticas de lore no texto traduzido de uma linha ASS."""
    original = texto_dialogo
    
    # 1. Correções estritas de frases completas (ou quase completas) do gato
    if "Gólgota não está sendo cuidado" in texto_dialogo:
        texto_dialogo = texto_dialogo.replace("Gólgota não está sendo cuidado", "O Lúcifer está sem ninguém para cuidar dele")
    elif re.sub(r'\{[^}]*\}', '', texto_dialogo).strip() == "Gólgota?":
        texto_dialogo = texto_dialogo.replace("Gólgota?", "Lúcifer?")
    elif "Executar a Operação Gólgota" in texto_dialogo:
        texto_dialogo = texto_dialogo.replace("Executar a Operação Gólgota", "Executar a operação de resgate do Lúcifer")
    elif "Esqueci de avisar o tio: Gólgota captura estranhos" in texto_dialogo:
        texto_dialogo = texto_dialogo.replace("Esqueci de avisar o tio: Gólgota captura estranhos", "Esqueci de avisar o tio: o Lúcifer arranha estranhos")
    elif "Vai para Gólgota" in texto_dialogo:
        texto_dialogo = texto_dialogo.replace("Vai para Gólgota", "Vem, Lúcifer")
    elif "Gólgota acordou com estranhos sons de sono há pouco" in texto_dialogo:
        texto_dialogo = texto_dialogo.replace("Gólgota acordou com estranhos sons de sono há pouco", "O Lúcifer estava roncando estranho agora há pouco")
    elif "Gólgota também está ficando velho" in texto_dialogo:
        texto_dialogo = texto_dialogo.replace("Gólgota também está ficando velho", "O Lúcifer também está ficando velho")
    elif "Gólgota, desculpe" in texto_dialogo:
        texto_dialogo = texto_dialogo.replace("Gólgota, desculpe", "Lúcifer, desculpe")
    
    # 2. Correção da família Ral
    if "Leve a família Ral para Gólgota" in texto_dialogo:
        texto_dialogo = texto_dialogo.replace("Leve a família Ral para Gólgota", "Eliminem a família Ral")
        
    # 3. Correção da nave Grande Degwin
    if "pilotando o Gólgota sozinho" in texto_dialogo:
        texto_dialogo = texto_dialogo.replace("pilotando o Gólgota sozinho", "com a Grande Degwin avançando sozinha")
    elif "Príncipe Zeon pilotando o Gólgota" in texto_dialogo:
        texto_dialogo = texto_dialogo.replace("Príncipe Zeon pilotando o Gólgota", "Príncipe Zeon com a Grande Degwin")

    # 4. Substituições gerais de termos
    # Guerra de Um Ano
    texto_dialogo = re.sub(r"\bGuerra (?:de|dos|do)?\s?(?:Cem|100) Anos\b", "Guerra de Um Ano", texto_dialogo, flags=re.I)
    texto_dialogo = re.sub(r"\bGuerra do Ano Um\b", "Guerra de Um Ano", texto_dialogo, flags=re.I)

    # Lúcifer (nome do gato com acento)
    texto_dialogo = re.sub(r"\bL[uú]cifer\b", "Lúcifer", texto_dialogo)
    texto_dialogo = re.sub(r"\bL[uú]cifero\b", "Lúcifer", texto_dialogo)

    # Principado de Zeon
    texto_dialogo = re.sub(r"\bPrincipado de Dion\b", "Principado de Zeon", texto_dialogo, flags=re.I)

    # --- CORREÇÕES DE LORE — análise completa EPs 01-13 ---

    # Munzo (colônia Side 3) — múltiplas grafias incorretas do pipeline
    texto_dialogo = re.sub(r"\bMu\s+Zuo\b", "Munzo", texto_dialogo, flags=re.I)
    texto_dialogo = re.sub(r"\bMucho\b(?=\s+tamb[eé]m|\s+tem|\s+tinha|\s+também)", "Munzo", texto_dialogo, flags=re.I)
    texto_dialogo = re.sub(r"\bMuzeo\b", "Munzo", texto_dialogo, flags=re.I)
    texto_dialogo = re.sub(r"\b(?<!\w)Muzo\b", "Munzo", texto_dialogo, flags=re.I)
    texto_dialogo = re.sub(r"\bZamyam\b", "Munzo", texto_dialogo, flags=re.I)
    texto_dialogo = re.sub(r"\bSIDE\s*3\s+Mu[Zz][oa-z]+\b", "SIDE 3 Munzo", texto_dialogo, flags=re.I)

    # "Lobo Vermelho" → "Cometa Vermelho" (apelido do Char Aznable)
    texto_dialogo = re.sub(r"\bLobo\s+Vermelho\b", "Cometa Vermelho", texto_dialogo, flags=re.I)

    # "Satélite Colonizante Preto" → "Colônia Texas" (Texas Colony, Side 5 Bunch 30)
    texto_dialogo = re.sub(r"\bSat[eé]lite\s+Colonizante\s+Preto\b", "Colônia Texas", texto_dialogo, flags=re.I)

    # "Karlma" → "Garma" (Garma Zabi, filho de Degwin)
    texto_dialogo = re.sub(r"\bKarlma\b", "Garma", texto_dialogo, flags=re.I)

    # "Tim Ray" → "Tem Ray" (pai do Amuro, engenheiro-chefe)
    texto_dialogo = re.sub(r"\bTim\s+Ray\b", "Tem Ray", texto_dialogo, flags=re.I)

    # Parentesco: "filho do diretor de desenvolvimento Amuro Ray" → "Tem Ray"
    texto_dialogo = re.sub(
        r"\bfilho\s+do\s+diretor\s+de\s+desenvolvimento\s+Amuro\s+Ray\b",
        "filho do diretor de desenvolvimento Tem Ray",
        texto_dialogo, flags=re.I
    )

    # "Mobil Suit" → "Mobile Suit" (erro ortográfico do pipeline)
    texto_dialogo = re.sub(r"\bMobil\s+Suit\b", "Mobile Suit", texto_dialogo, flags=re.I)

    # "escuadrão" (espanhol) → "esquadrão" (português)
    texto_dialogo = re.sub(r"\bescuadr[aã]o\b", "esquadrão", texto_dialogo, flags=re.I)

    # "muelle de atracag" (espanhol) → "cais de atracagem"
    texto_dialogo = re.sub(r"\bmuelle\s+de\s+atracag[ae]m?\b", "cais de atracagem", texto_dialogo, flags=re.I)
    texto_dialogo = re.sub(r"\bmuelle\b", "cais", texto_dialogo, flags=re.I)

    # "roda de repuesto" (espanhol) → "roda sobressalente"
    texto_dialogo = re.sub(r"\broda\s+de\s+repuesto\b", "roda sobressalente", texto_dialogo, flags=re.I)

    # "flagship" isolado → "nave capitânia"
    texto_dialogo = re.sub(r"\bflagship\b", "nave capitânia", texto_dialogo, flags=re.I)

    # Operação British (nome oficial)
    texto_dialogo = re.sub(
        r"\bOpera[çc][aã]o\s+Brit[aâ]ni[ao]\b",
        "Operação British",
        texto_dialogo, flags=re.I
    )

    # --- BUG 03 — Guarda: loop de repetição "Amuro Ray, do Amuro Ray..." ---
    texto_dialogo = re.sub(
        r"((?:do|de)\s+Amuro\s+Ray)(?:[,\s]+(?:do|de)\s+Amuro\s+Ray)+",
        r"\1", texto_dialogo, flags=re.I
    )
    # Corrige parentesco: Amuro é o filho, o pai é Tem Ray
    texto_dialogo = re.sub(r"\bfilho\s+d[eo]\s+Amuro\s+Ray\b", "filho do Dr. Tem Ray", texto_dialogo, flags=re.I)
    texto_dialogo = re.sub(r"\bfilho\s+d[eo]\s+Amuro\b", "filho do Dr. Tem Ray", texto_dialogo, flags=re.I)

    # --- BUG 04 — Área restrita: "Segurança" solto/descontextualizado ---
    texto_dialogo = re.sub(r"\binvadir\s+a\s+segurança\b", "invadir o setor de segurança", texto_dialogo, flags=re.I)
    texto_dialogo = re.sub(r"\bzona\s+de\s+segurança\b", "área restrita", texto_dialogo, flags=re.I)
    texto_dialogo = re.sub(r"\bviolando\s+a\s+segurança\b", "violando o perímetro de segurança", texto_dialogo, flags=re.I)
    texto_dialogo = re.sub(r"^((?:\{[^}]*\})*)Segurança!$", r"\1Área restrita!", texto_dialogo)

    # --- BUG 05 — Numeração de plano militar vazando em diálogos seguintes ---
    texto_dialogo = re.sub(r"^((?:\{[^}]*\})*)([5-9]|[1-9]\d+)\.\s+", r"\1", texto_dialogo)

    # Retorna o texto corrigido e se houve modificação
    return texto_dialogo, texto_dialogo != original


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


def corrigir_arquivos_ass(pasta_legendas):
    print(f"\n{Fore.CYAN}--- CORREÇÃO DOS ARQUIVOS .ASS ---")
    if not os.path.exists(pasta_legendas):
        print(f"{Fore.RED}[ERRO] Pasta de legendas não encontrada: {pasta_legendas}")
        return False
        
    arquivos_ass = sorted([f for f in os.listdir(pasta_legendas) if f.lower().endswith('.ass')])
    if not arquivos_ass:
        print(f"{Fore.YELLOW}[AVISO] Nenhum arquivo .ass localizado em: {pasta_legendas}")
        return False
        
    print(f"{Fore.GREEN}[OK] Localizados {len(arquivos_ass)} arquivos .ass para revisão.")
    
    total_modificacoes_geral = 0
    
    for idx, arquivo in enumerate(arquivos_ass, 1):
        caminho_file = os.path.join(pasta_legendas, arquivo)
        linhas, encoding = ler_arquivo_legenda(caminho_file)
        
        linhas_corrigidas = []
        modificacoes_no_arquivo = 0
        
        for num_linha, linha in enumerate(linhas, 1):
            if linha.startswith("Dialogue:"):
                partes = linha.split(",", 9)
                if len(partes) == 10:
                    metadados = ",".join(partes[:9]) + ","
                    texto_dialogo = partes[9].rstrip("\n")

                    # Bug 01 — Remover metadados/créditos de fansub
                    if eh_metadado_fansub(texto_dialogo):
                        modificacoes_no_arquivo += 1
                        print(f"  ↳ [{arquivo} L{num_linha}] {Fore.MAGENTA}METADADO FANSUB REMOVIDO: {Style.RESET_ALL}{texto_dialogo[:100]}")
                        linha = f"{metadados}\n"
                        linhas_corrigidas.append(linha)
                        continue

                    texto_novo, modificado = aplicar_correcao_linha_ass(texto_dialogo)
                    if modificado:
                        modificacoes_no_arquivo += 1
                        linha = f"{metadados}{texto_novo}\n"
                        print(f"  ↳ [{arquivo} L{num_linha}] Correção:")
                        print(f"      Antes: {Fore.RED}{texto_dialogo}")
                        print(f"      Depois: {Fore.GREEN}{texto_novo}")
            
            linhas_corrigidas.append(linha)
            
        if modificacoes_no_arquivo > 0:
            # Sobrescreve com as correções
            with open(caminho_file, 'w', encoding='utf-8') as f:
                f.writelines(linhas_corrigidas)
            print(f"  {Fore.GREEN}[SALVO] {arquivo} | {modificacoes_no_arquivo} correções aplicadas.")
            total_modificacoes_geral += modificacoes_no_arquivo
        else:
            print(f"  [OK] {arquivo} analisado (nenhuma inconsistência encontrada).")
            
    print(f"\n{Fore.GREEN}[CONCLUÍDO] Correção das legendas finalizada! Total de {total_modificacoes_geral} linhas corrigidas.")
    return True


def detectar_linhas_sem_traducao(pasta_legendas):
    """Varre os .ass e reporta linhas que parecem não ter sido traduzidas para PT-BR."""
    print(f"\n{Fore.CYAN}--- AUDITORIA: LINHAS SEM TRADUÇÃO OU COM RESÍDUOS ---")

    RE_FRANCES = re.compile(
        r"\b(vous|avec|[êe]tre|êtes|été|est|sont|leur|cette|alors|où|très|pour|dans|sans|toujours|"
        r"voilà|monsieur|madame|qu['’]il|qu['’]elle|c['’]est|n['’]est|n['’]a|d['’]un|d['’]une|"
        r"cet|ceci|cela|besoin|soins|enfant|enfants|qui|une|elle|elles|un\s+MS|rouge)\b",
        re.I
    )
    RE_ERRO_PIPELINE = re.compile(r'\[ERRO_TRADUCAO[_:]', re.I)

    arquivos_ass = sorted([f for f in os.listdir(pasta_legendas) if f.lower().endswith('.ass')])
    relatorio = []

    for arquivo in arquivos_ass:
        caminho_file = os.path.join(pasta_legendas, arquivo)
        linhas, _ = ler_arquivo_legenda(caminho_file)
        for num_linha, linha in enumerate(linhas, 1):
            if not linha.startswith("Dialogue:"):
                continue
            partes = linha.split(",", 9)
            if len(partes) != 10:
                continue
            texto = partes[9].rstrip("\n")
            puro = limpar_tags_ass(texto).strip()
            if not puro:
                continue

            motivo = None
            if RE_FRANCES.search(puro):
                motivo = "RESÍDUO_FRANCÊS"
            elif RE_ERRO_PIPELINE.search(puro):
                motivo = "ERRO_PIPELINE"

            if motivo:
                entrada = f"  [{arquivo} L{num_linha}] ({motivo}) {puro[:120]}"
                relatorio.append(entrada)

    if relatorio:
        print(f"{Fore.YELLOW}[ATENÇÃO] {len(relatorio)} linhas suspeitas encontradas:")
        for r in relatorio:
            print(r)
        caminho_relatorio = os.path.join(pasta_legendas, "_relatorio_sem_traducao.txt")
        with open(caminho_relatorio, 'w', encoding='utf-8') as f:
            f.write("\n".join(relatorio))
        print(f"\n{Fore.GREEN}[OK] Resumo salvo na pasta como: _relatorio_sem_traducao.txt")
    else:
        print(f"{Fore.GREEN}[OK] Nenhuma linha sem tradução/francesa detectada.")

    return relatorio


def remuxar_legendas_mkv(pasta_mkv, pasta_legendas, pasta_saida=None):
    print(f"\n{Fore.CYAN}--- RE-MULTIPLEXAÇÃO DOS MKVs ---")
    if not MKVMERGE_PATH:
        print(f"{Fore.RED}[ERRO] mkvmerge não encontrado no sistema. Remuxing abortado.")
        return False

    if not pasta_saida:
        pasta_saida = os.path.join(pasta_mkv, "corrigidos")
    os.makedirs(pasta_saida, exist_ok=True)
    
    arquivos_mkv = sorted([f for f in os.listdir(pasta_mkv) if f.lower().endswith('.mkv')])
    if not arquivos_mkv:
        print(f"{Fore.YELLOW}[AVISO] Nenhum arquivo .mkv localizado na pasta de vídeos: {pasta_mkv}")
        return False
        
    print(f"{Fore.GREEN}[OK] Localizados {len(arquivos_mkv)} arquivos MKV para processamento.")
    print(f"Os novos arquivos corrigidos serão salvos em: {pasta_saida}")
    
    # Mapear legendas por número de episódio no nome
    legendas_ass = [f for f in os.listdir(pasta_legendas) if f.lower().endswith('.ass')]
    
    for idx, nome_mkv in enumerate(arquivos_mkv, 1):
        caminho_mkv = os.path.join(pasta_mkv, nome_mkv)
        
        # Encontra o ep correspondente no nome do mkv (ex: [01])
        m_ep = re.search(r'\[(\d+)\]', nome_mkv)
        if not m_ep:
            m_ep = re.search(r'E(\d+)', nome_mkv, re.I)
            
        if not m_ep:
            print(f"  {Fore.YELLOW}[AVISO] Não foi possível identificar o número do episódio no MKV: {nome_mkv}. Pulando remux.")
            continue
            
        ep_num = m_ep.group(1)
        
        # Acha a legenda correspondente com o mesmo número de ep
        legenda_correta = None
        for leg in legendas_ass:
            m_leg = re.search(r'\[(\d+)\]', leg)
            if not m_leg:
                m_leg = re.search(r'E(\d+)', leg, re.I)
            if m_leg and m_leg.group(1) == ep_num:
                legenda_correta = leg
                break
                
        if not legenda_correta:
            print(f"  {Fore.RED}[ERRO] Nenhuma legenda PT-BR encontrada para o episódio {ep_num}. Pulando remux.")
            continue
            
        caminho_legenda = os.path.join(pasta_legendas, legenda_correta)
        nome_saida = nome_mkv.replace(".mkv", "_PTBR.mkv")
        caminho_saida = os.path.join(pasta_saida, nome_saida)
        
        print(f"  [{idx}/{len(arquivos_mkv)}] Remuxando Ep {ep_num}...")
        
        # O mkvmerge vai pegar as faixas de vídeo e áudio originais, e adicionar a legenda ASS como padrão
        cmd = [
            MKVMERGE_PATH,
            "-o", caminho_saida,
            "--no-subtitles", caminho_mkv, # Ignora as legendas antigas
            "--language", "0:por",
            "--track-name", "0:Português (Brasil)",
            "--default-track", "0:yes",
            caminho_legenda
        ]
        
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
            if res.returncode == 0:
                print(f"    {Fore.GREEN}✓ Sucesso! -> {nome_saida}")
            else:
                print(f"    {Fore.RED}✗ Erro no mkvmerge: código {res.returncode}")
        except Exception as e:
            print(f"    {Fore.RED}✗ Exceção ao rodar mkvmerge: {e}")

    print(f"\n{Fore.GREEN}[CONCLUÍDO] Remuxing finalizado!")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Revisão e remuxing de legendas (Francês -> PT-BR) - Gundam Origin")
    parser.add_argument("--legendas", default=PASTA_LEGENDA_PADRAO, help="Pasta com as legendas .ass")
    parser.add_argument("--mkv", default=None, help="Pasta com os MKVs originais (ou 'pular')")
    parser.add_argument("--saida", default=None, help="Pasta de saída dos vídeos finais com legenda")
    parser.add_argument("--sim", action="store_true", help="Pular confirmação interativa")
    parser.add_argument("--auditar", action="store_true", help="Auditar linhas sem tradução por padrão")
    args, unknown = parser.parse_known_args()

    usando_cli = len(sys.argv) > 1

    print(f"{Fore.MAGENTA}================================================================================")
    print("      REVISÃO E REMUXING DE LEGENDAS (FRANCÊS -> PT-BR) - GUNDAM ORIGIN")
    print(f"================================================================================{Style.RESET_ALL}\n")

    if usando_cli or args.sim:
        pasta_legendas = args.legendas
        if not pasta_legendas:
            pasta_legendas = PASTA_LEGENDA_PADRAO
        if not pasta_legendas or not os.path.isdir(pasta_legendas):
            print(f"{Fore.RED}[ERRO] Pasta de legendas inválida ou não informada: {pasta_legendas}")
            sys.exit(1)
            
        pasta_mkv = args.mkv
        if pasta_mkv and pasta_mkv.lower() == 'pular':
            pasta_mkv = None
            
        pasta_saida_mkv = args.saida
        if pasta_mkv and not pasta_saida_mkv:
            pasta_saida_mkv = os.path.join(pasta_mkv, "corrigidos")
            
        opcao_auditoria = 's' if args.auditar else 'n'
        confirma = 's' if args.sim else 'n'
    else:
        # Fluxo interativo antigo
        print(f"{Fore.CYAN}[1/2] PASTA COM AS LEGENDAS .ASS (PT-BR já traduzidas do Francês)")
        pasta_legendas = obter_diretorio_obrigatorio(
            "Pasta com os arquivos .ass", PASTA_LEGENDA_PADRAO
        )

        print()
        print(f"{Fore.CYAN}[2/2] PASTA COM OS ARQUIVOS .MKV ORIGINAIS (necessária para embutir as legendas)")
        print("      Digite 'pular' para não embutir as legendas nos MKVs agora.")
        resp_mkv = input(f"{Fore.YELLOW}Pasta dos MKVs originais (ou 'pular')\n> {Style.RESET_ALL}").strip().strip('"').strip("'")
        pasta_mkv = None if (not resp_mkv or resp_mkv.lower() == 'pular') else resp_mkv

        pasta_saida_mkv = None
        if pasta_mkv and os.path.isdir(pasta_mkv):
            print()
            print(f"{Fore.CYAN}[EXTRA] PASTA DE SAÍDA PARA OS MKVs FINALIZADOS")
            padrao_saida = os.path.join(pasta_mkv, "corrigidos")
            pasta_saida_mkv = obter_pasta_saida(
                "Pasta de saída dos vídeos finais com legenda", padrao_saida
            )
        elif pasta_mkv:
            print(f"{Fore.RED}[AVISO] Pasta de vídeos MKV não encontrada: {pasta_mkv}. Remuxing será pulado.")
            pasta_mkv = None
            
        # ── RESUMO ──────────────────────────────────────────────────────────────────
        print("\n" + "=" * 80)
        print(f"{Fore.CYAN}CONFIGURAÇÃO CONFIRMADA:")
        print(f"  Legendas    : {pasta_legendas}")
        print(f"  MKVs        : {pasta_mkv or '(pulado)'}")
        print(f"  Saída MKVs  : {pasta_saida_mkv or '(pulado)'}")
        print("=" * 80)
        confirma = input(f"{Fore.YELLOW}Confirma e inicia o processamento? (s/n): {Style.RESET_ALL}").strip().lower()
        opcao_auditoria = None

    if confirma != 's':
        print(f"{Fore.YELLOW}[CANCELADO] Nenhuma alteração foi feita.")
        return

    # ── EXECUÇÃO ─────────────────────────────────────────────────────────────────
    # 1. Corrigir arquivos .ass (Regex + Metadados)
    corrigir_arquivos_ass(pasta_legendas)

    # 2. Auditoria de linhas sem tradução ou com resíduo francês
    if opcao_auditoria is None:
        print("\n" + "=" * 80)
        opcao_auditoria = input(f"{Fore.YELLOW}Auditar linhas por palavras em francês esquecidas? (s/n): {Style.RESET_ALL}").strip().lower()
    
    if opcao_auditoria == 's':
        detectar_linhas_sem_traducao(pasta_legendas)

    # 3. Remuxar
    if pasta_mkv:
        remuxar_legendas_mkv(pasta_mkv, pasta_legendas, pasta_saida_mkv)

    print("\n" + "=" * 80)
    print(f"{Fore.GREEN}[FIM] Processo concluído! Obrigado por manter a integridade da Universal Century!")
    print("=" * 80)

    # --- SALVAR LOG DE AUDITORIA ---
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_log = f"log_auditoria_{timestamp}.txt"
    caminho_log = os.path.join(pasta_legendas, nome_log)
    try:
        with open(caminho_log, "w", encoding="utf-8") as f:
            f.write("".join(logger_obj.log))
        
        # Imprime no original_stdout para não ser capturado pelo TeeLogger (evitando loop ou log sujo)
        original_stdout.write(f"\n\x1b[32m[OK] Relatório completo de auditoria salvo em: {caminho_log}\x1b[0m\n")
    except Exception as e:
        original_stdout.write(f"\n\x1b[31m[ERRO] Falha ao salvar log de auditoria: {e}\x1b[0m\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        original_stdout.write(f"\n\x1b[33m[AVISO] Interrompido pelo operador.\x1b[0m\n")
        sys.exit(0)
