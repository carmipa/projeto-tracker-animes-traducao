#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: revisao_legenda_gundam_unicornio.py
Revisa e corrige erros de tradução em diálogos do Episódio 1 e padroniza as letras 
das músicas (Into the Sky e RE:I AM) de todos os 22 episódios de Gundam Unicorn RE:0096,
re-multiplexando o vídeo MKV final.

Author: Antigravity + Paulo
Data: Junho 2026
"""

import os
import re
import sys
import shutil
import subprocess
from colorama import init, Fore, Style

# Inicializa o colorama para tratar escapes ANSI no console do Windows
init(autoreset=True)

# Força codificação UTF-8 na saída padrão do Windows
if sys.version_info >= (3, 7):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Caminhos padrão
PASTA_ANIME = r"E:\animes\GUNDAM\GUNDAM UC\UC 0096 - UNICORN\Mobile Suit Gundam Unicorn Re0096"
PASTA_LEGENDA = os.path.join(PASTA_ANIME, "legendas_ptbr")
PASTA_VIDEO_OUT = os.path.join(PASTA_ANIME, "corrigidos")

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

def extrair_numero_episodio(nome_arquivo):
    m = re.search(r'E(\d+)', nome_arquivo)
    if m:
        return int(m.group(1))
    return None

def corrigir_abertura(texto_original):
    m_tags = re.match(r"^(\{[^}]*\})(.*)$", texto_original)
    if m_tags:
        tags, rest = m_tags.groups()
    else:
        tags, rest = "", texto_original
        
    rest_clean = rest.strip()
    rest_lower = rest_clean.lower()
    
    if "sozinho" in rest_lower:
        rest = "Você se sente sozinho?"
    elif "ouvir agora" in rest_lower or "me ouvir" in rest_lower:
        rest = "Você consegue me ouvir agora?"
    elif "mente" in rest_lower and ("terra" in rest_lower or "earth" in rest_lower):
        rest = "Sua mente está tão longe, ainda na Terra"
    elif "prateleira" in rest_lower:
        rest = "Você não pode ser apenas uma vida na prateleira"
    elif "unicorn" in rest_lower or "unicórnio" in rest_lower:
        rest = "Só você pode fazer este novo Unicorn voar para o céu"
    elif "facas" in rest_lower or "fere com" in rest_lower or "corta com" in rest_lower or "machuca com" in rest_lower:
        rest = "E é sempre que você se machuca com mentiras"
    elif "chamando" in rest_lower and "nome" in rest_lower:
        rest = "E eu estou chamando o seu nome de novo"
    elif "medo" in rest_lower:
        rest = "Se você estiver se apegando ao medo"
    elif "cego" in rest_lower or "cegos" in rest_lower:
        rest = "Se eu soubesse que os olhos podem se abrir"
    elif "luz" in rest_lower and ("passar" in rest_lower or "entrar" in rest_lower or "brilhar" in rest_lower):
        rest = "Deixe a luz entrar"
    elif "digo" in rest_lower:
        rest = "E eu pergunto:"
    elif "sacrifício" in rest_lower or "sacrificio" in rest_lower:
        rest = "Por que não podemos parar com todos estes sacrifícios?"
    elif "mentiras" in rest_lower and "pedra" in rest_lower:
        rest = "Eu sei que todas as mentiras viraram pedra no seu coração"
    elif "sobreviver" in rest_lower:
        rest = "Eu me pergunto por quanto tempo você vai sobreviver"
    elif "significado" in rest_lower:
        rest = "Nós não vimos todo o seu significado"
    elif "ferindo" in rest_lower or "machucando" in rest_lower or "fere" in rest_lower or "machuca" in rest_lower:
        rest = "Muitas vezes você está se machucando"
        
    return f"{tags}{rest}"

def corrigir_encerramento_next2u(texto_original):
    m_tags = re.match(r"^(\{[^}]*\})(.*)$", texto_original)
    if m_tags:
        tags, rest = m_tags.groups()
    else:
        tags, rest = "", texto_original
        
    rest_clean = rest.strip()
    rest_lower = rest_clean.lower()
    
    if "conectando sonhos" in rest_lower or "respostas que são apenas um ato" in rest_lower:
        rest = "Conectando respostas e apoios de fachada,\\Nligando o calor que carregam"
    elif "lenda sorridente" in rest_lower:
        rest = "A esperança que abraça o zero absoluto sorridente"
    elif "expectativas para escolher" in rest_lower:
        rest = "Em manhãs sem expectativas alinhadas para escolher"
    elif "girar parou" in rest_lower:
        rest = "Deixei de depender dos outros"
    elif "traçando anéis" in rest_lower or "amor tocado pela mão esquerda" in rest_lower:
        rest = "Gentilmente traçando o anel,\\Na mão esquerda tocou o amor e o vazio"
    elif "cantando um hino" in rest_lower or "processo sem propósito" in rest_lower:
        rest = "Uma órbita limpa cantada, um processo sem propósito"
    elif "eco distante" in rest_lower:
        rest = "O som de uma glória instável"
    elif "desfaçam meu ídolo" in rest_lower:
        rest = "Desfaçam meu ídolo procurado"
    elif "respirar fundo" in rest_lower:
        rest = "Então poderei respirar fundo"
    elif "sombra cruel" in rest_lower:
        rest = "A sombra cruel de um adulto desapareceu, como se sobrepondo"
    elif "ideal confiável" in rest_lower:
        rest = "Se for um ideal frágil, vamos descartá-lo"
    elif "vestido e coroa" in rest_lower and "dormir em paz" in rest_lower:
        rest = "Tirem meu vestido e minha coroa,\\npara que eu possa adormecer profundamente"
    elif "palavras secas" in rest_lower:
        rest = "A chuva de palavras secas\\nse foi como poeira"
    elif "perdi e deixei a chave" in rest_lower:
        rest = "Chave perdida e esquecida"
    elif "gelo daquele futuro" in rest_lower:
        rest = "O gelo daquele futuro"
        
    return f"{tags}{rest}"

def corrigir_encerramento_re_i_am(texto_original):
    m_tags = re.match(r"^(\{[^}]*\})(.*)$", texto_original)
    if m_tags:
        tags, rest = m_tags.groups()
    else:
        tags, rest = "", texto_original
        
    rest_clean = rest.strip()
    rest_lower = rest_clean.lower()
    
    if "ainda estão chorando" in rest_lower:
        rest = "Eles ainda estão chorando"
    elif "guerra de matança" in rest_lower or "guerra de carnificina" in rest_lower:
        rest = "Quem pode deter esta guerra de carnificina?"
    elif "recusar" in rest_lower:
        rest = "Não há quem se recuse"
    elif "não importa" in rest_lower or "não faz realmente diferença" in rest_lower:
        rest = "Isso realmente não importa"
    elif "trair-me" in rest_lower or "trair a mim" in rest_lower:
        rest = "Trair a mim mesmo para salvar a alma de outrem"
    elif "queira sair daqui" in rest_lower or "querer sair daqui" in rest_lower:
        rest = "Embora eu queira sair daqui"
    elif "liberdade sem volta" in rest_lower or "liberdade sem retorno" in rest_lower:
        rest = "Continuaremos correndo rumo ao vento sem retorno"
    elif "greedy glow" in rest_lower or "brilho de ganância" in rest_lower:
        rest = "Você sorri, com aquele brilho de ganância em seus olhos frenéticos"
    elif "odeio" in rest_lower and "negar" in rest_lower:
        rest = "Eu odeio isso, mas não posso negar"
    elif "não quero ser como" in rest_lower:
        rest = "Não quero ser como você"
    elif "disputa" in rest_lower or "conflito" in rest_lower or "rivalidade" in rest_lower:
        rest = "A disputa entre nós se aprofunda ainda mais"
    elif "pagamentos trágicos" in rest_lower or "mágoa trágica" in rest_lower or "salários trágicos" in rest_lower or "peso de tragédia" in rest_lower:
        rest = "Em meio a trágicas consequências"
    elif "luto contra isso" in rest_lower or "jamais resisto" in rest_lower:
        rest = "Não suporto, mas jamais luto contra isso"
    elif "provas suficientes" in rest_lower or "provado" in rest_lower:
        rest = "Embora eu não tenha provas suficientes"
    elif "carisma-ta" in rest_lower or "carisma" in rest_lower:
        rest = "Hipnotizado pelo seu carisma"
    elif "verdadeiro" in rest_lower or "falso" in rest_lower or "nunca será real" in rest_lower or "você nunca será real" in rest_lower:
        rest = "Ninguém percebe que você nunca será real"
    elif "se eu estivesse do seu lado" in rest_lower:
        rest = "Mas sei que você teria razão, se eu estivesse do seu lado"
    elif "tão confusa" in rest_lower or "tão confuso" in rest_lower:
        rest = "Tão confuso..."
    elif "julgamento" in rest_lower and ("castigo" in rest_lower or "punição" in rest_lower):
        rest = "Deus, que julgamento... Será o meu castigo?"
    elif "destino sangrento" in rest_lower or "maldito destino" in rest_lower:
        rest = "Não posso escapar do meu destino sangrento?"
    elif "fragmento" in rest_lower:
        rest = "Onde está o meu fragmento? Perdido no momento"
    elif "olhar para trás" in rest_lower or "o que fizemos" in rest_lower:
        rest = "Preciso olhar para trás e ver o que fizemos..."
        
    return f"{tags}{rest}"

def corrigir_encerramento_ed_en(texto_original):
    m_tags = re.match(r"^(\{[^}]*\})(.*)$", texto_original)
    if m_tags:
        tags, rest = m_tags.groups()
    else:
        tags, rest = "", texto_original
        
    rest_clean = rest.strip()
    rest_lower = rest_clean.lower()
    
    if "não finjo ser uma adulta" in rest_lower:
        rest = "Faz muito tempo, não posso fingir ser adulta"
    elif "enquanto estive bem perto" in rest_lower:
        rest = "Eu posso ser uma garota comum\\nenquanto estiver bem ao seu lado"
    elif "o amor que senti\\n" in rest_lower or "o amor que senti\\N" in rest_lower:
        rest = "Você nunca soube o amor que senti"
        
    return f"{tags}{rest}"

def aplicar_correcao_linha(texto, style, ep_num):
    original = texto
    
    # 1. Correções da Abertura (OPL2)
    if style == "OPL2":
        texto = corrigir_abertura(texto)
        return texto, texto != original
        
    # 2. Correções do Encerramento 1 (ED)
    if style == "ED":
        texto = corrigir_encerramento_next2u(texto)
        return texto, texto != original

    # 3. Correções do Encerramento 2 (ED2)
    if style == "ED2":
        texto = corrigir_encerramento_re_i_am(texto)
        return texto, texto != original

    # 4. Correções do Encerramento Inglês (ED - EN)
    if style == "ED - EN":
        texto = corrigir_encerramento_ed_en(texto)
        return texto, texto != original

    # 5. Correções de Diálogos Globais (Lore & Gênero)
    # Guerra de Um Ano
    texto = re.sub(r"Guerra do Ano Um", "Guerra de Um Ano", texto)
    
    # Gênero/Tratamento da Marida Cruz (incluindo tratamento de tags de quebra de linha \N ou \n)
    texto = re.sub(r"Sr\.\s*Marida", "Srta. Marida", texto)
    texto = re.sub(r"(?:\\N|\\n|\b)o\s+Tenente\s+Marida\b", " a Tenente Marida", texto, flags=re.IGNORECASE)
    texto = re.sub(r"deixando Marida para lutar sozinho", "deixando Marida para lutar sozinha", texto)
    texto = re.sub(r"- Mas Marida é um\(a\)-", "- Mas a Marida é uma...", texto)
    
    # Termos Técnicos
    texto = re.sub(r"\bFunneis\b", "Funnels", texto)
    texto = re.sub(r"\bEspacoinoides\b", "Espaçonoides", texto, flags=re.IGNORECASE)

    # 6. Correções específicas do Episódio 1
    if ep_num == 1:
        texto = re.sub(r"\bEnvie o Marida\b", "Envie a Marida", texto)
        texto = re.sub(r"colidiu com alguns Sleeves", "confrontou alguns Sleeves", texto)
        texto = re.sub(r"\bdaybreak\b", "amanhecendo", texto, flags=re.IGNORECASE)
        texto = re.sub(r"Eu vamos passar por isso", "Eu vou passar por isso", texto)

    return texto, texto != original

def processar_legendas():
    print(f"\n{Fore.CYAN}=== INICIANDO PROCESSAMENTO DE LEGENDAS DO GUNDAM UNICORN RE:0096 ===")
    if not os.path.exists(PASTA_LEGENDA):
        print(f"{Fore.RED}[ERRO] Diretório de legendas não existe: {PASTA_LEGENDA}")
        return False

    arquivos = [f for f in os.listdir(PASTA_LEGENDA) if f.lower().endswith("_eng.ass")]
    arquivos.sort()

    print(f"Localizados {len(arquivos)} arquivos de legenda para processamento.")
    print("-" * 80)

    total_correcoes = 0

    for arq in arquivos:
        ep_num = extrair_numero_episodio(arq)
        if ep_num is None:
            print(f"{Fore.YELLOW}[AVISO] Não foi possível deduzir o número do episódio para: {arq}. Pulando.")
            continue

        caminho_in = os.path.join(PASTA_LEGENDA, arq)
        caminho_out = os.path.join(PASTA_LEGENDA, arq.replace("_PTBR_ENG.ass", "_PTBR.ass"))

        linhas, encoding = ler_arquivo_legenda(caminho_in)
        linhas_novas = []
        correcoes_arq = 0

        for idx, line in enumerate(linhas, 1):
            if line.startswith("Dialogue:"):
                parts = line.split(",", 9)
                if len(parts) == 10:
                    metadados = ",".join(parts[:9]) + ","
                    style = parts[3].strip()
                    texto_dialogo = parts[9].rstrip("\n")

                    texto_corrigido, modificado = aplicar_correcao_linha(texto_dialogo, style, ep_num)
                    if modificado:
                        correcoes_arq += 1
                        line = f"{metadados}{texto_corrigido}\n"

            linhas_novas.append(line)

        # Salva o arquivo corrigido na mesma pasta em UTF-8 com BOM
        with open(caminho_out, "w", encoding="utf-8-sig") as f:
            f.writelines(linhas_novas)

        if correcoes_arq > 0:
            print(f"{Fore.GREEN}[OK] Processado EP {ep_num:02d} | {correcoes_arq} modificações salvas em: {os.path.basename(caminho_out)}")
            total_correcoes += correcoes_arq
        else:
            print(f"[OK] Processado EP {ep_num:02d} | Nenhuma modificação necessária.")

    print(f"\n{Fore.GREEN}[FIM] Revisão finalizada! Total de {total_correcoes} correções aplicadas nos 22 arquivos.")
    return True

def remuxar_videos():
    print(f"\n{Fore.CYAN}=== INICIANDO RE-MULTIPLEXAÇÃO DOS VÍDEOS ===")
    if not MKVMERGE_PATH:
        print(f"{Fore.RED}[ERRO] mkvmerge não encontrado. Remuxing abortado.")
        return False

    os.makedirs(PASTA_VIDEO_OUT, exist_ok=True)

    videos_mkv = sorted([f for f in os.listdir(PASTA_ANIME) if f.lower().endswith(".mkv")])
    if not videos_mkv:
        print(f"{Fore.YELLOW}[AVISO] Nenhum arquivo .mkv localizado na pasta: {PASTA_ANIME}")
        return False

    print(f"[OK] Encontrados {len(videos_mkv)} arquivos MKV originais.")
    print(f"Os vídeos com a nova legenda corrigida serão salvos em: {PASTA_VIDEO_OUT}")
    print("-" * 80)

    legendas_corrigidas = [f for f in os.listdir(PASTA_LEGENDA) if f.lower().endswith("_ptbr.ass")]

    for idx, video in enumerate(videos_mkv, 1):
        ep_num = extrair_numero_episodio(video)
        if ep_num is None:
            print(f"{Fore.YELLOW}[AVISO] Não foi possível identificar o número do episódio em: {video}. Pulando remux.")
            continue

        # Encontra a legenda corrigida correspondente
        legenda_correta = None
        for leg in legendas_corrigidas:
            leg_ep = extrair_numero_episodio(leg)
            if leg_ep == ep_num:
                legenda_correta = leg
                break

        if not legenda_correta:
            print(f"{Fore.RED}[ERRO] Legenda corrigida para o EP {ep_num:02d} não encontrada. Pulando remux.")
            continue

        caminho_mkv_in = os.path.join(PASTA_ANIME, video)
        caminho_legenda = os.path.join(PASTA_LEGENDA, legenda_correta)
        caminho_mkv_out = os.path.join(PASTA_VIDEO_OUT, video)

        print(f"[{idx}/{len(videos_mkv)}] Remuxando EP {ep_num:02d}...")
        print(f"  ↳ Origem: {video}")
        print(f"  ↳ Legenda: {legenda_correta}")

        cmd = [
            MKVMERGE_PATH,
            "-o", caminho_mkv_out,
            "--no-subtitles",            # Remove legendas antigas que continham erros
            caminho_mkv_in,
            "--language", "0:por",
            "--track-name", "0:Português (Revisada - Abertura & Lore)",
            "--default-track", "0:yes",
            caminho_legenda
        ]

        res = subprocess.run(cmd, capture_output=True)
        if res.returncode == 0 and os.path.exists(caminho_mkv_out):
            print(f"  {Fore.GREEN}[SUCESSO] Multiplexado! Salvo em: corrigidos\\{video}")
        else:
            print(f"  {Fore.RED}[ERRO] Falha ao executar o mkvmerge para {video}.")
        print("-" * 50)

    print(f"\n{Fore.GREEN}[OK] Processo de remuxing finalizado com sucesso!")
    return True

def main():
    print("=" * 80)
    print(f"{Fore.CYAN}    REVISÃO DE LEGENDAS E REMUX DE VÍDEOS: GUNDAM UNICORN RE:0096")
    print("=" * 80)

    # 1. Processar a correção de legendas
    sucesso_legendas = processar_legendas()

    if sucesso_legendas:
        # 2. Perguntar se deseja remuxar os vídeos
        print("\n" + "=" * 80)
        opcao = input(f"{Fore.YELLOW}Deseja multiplexar (remux) as novas legendas nos arquivos .mkv originais? (s/n): {Style.RESET_ALL}").strip().lower()
        if opcao == "s":
            remuxar_videos()

    print("\n" + "=" * 80)
    print(f"{Fore.GREEN}[FIM] Operação finalizada!")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[AVISO] Interrompido pelo operador.")
        sys.exit(0)
