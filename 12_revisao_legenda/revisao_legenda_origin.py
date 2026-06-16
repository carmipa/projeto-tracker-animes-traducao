#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: revisao_legenda_origin.py
Revisa e corrige erros específicos de lore/tradução nas legendas de Gundam Origin.
- Corrige o cache persistente da IA (traducao_cache_origin_zh.json).
- Corrige os arquivos de legenda .ass na pasta legendas_ptbr.
- Opcionalmente remuxa de volta para os MKVs originais em uma pasta 'corrigidos'.

Erros corrigidos:
- "Guerra de cem anos" / "Guerra dos 100 anos" -> "Guerra de Um Ano"
- Gato "Lucifer" traduzido incorretamente como "Gólgota" ou grafado como "Lucifer/Lucifero".
- "Leve a família Ral para Gólgota" -> "Eliminem a família Ral"
- Nave "大德金号" traduzida como "Gólgota" -> "Grande Degwin"

Author: Antigravity + Paulo
Data: Junho 2026
"""

import os
import re
import sys
import json
import shutil
import subprocess
from colorama import init, Fore, Style

init(autoreset=True)

if sys.version_info >= (3, 7):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Caminhos padrão do projeto
PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PASTA_RAIZ = os.path.dirname(PASTA_SCRIPT)
CAMINHO_CACHE_PADRAO = os.path.join(PASTA_RAIZ, "11_chines_LLM_alibaba_qwen2", "traducao_cache_origin_zh.json")

# Caminhos padrão das legendas e vídeos do usuário
PASTA_ANIME_PADRAO = r"D:\PROJETOS-OPEN\animes\[POPGO][Gundam_The_Origin_TV][MKV+ASS]\mkv_final_ptbr"
PASTA_LEGENDA_PADRAO = os.path.join(PASTA_ANIME_PADRAO, "legendas_ptbr")

# Dicionário de correções exatas do Cache (de CHS para o PT-BR oficial)
CORRECOES_CACHE_ESTRITAS = {
    # Erro clássico: Guerra dos cem anos
    "世称「一年战争」的导火索": "Considerada como o gatilho da Guerra de Um Ano",
    "[T0]一年战争": "[T0]Guerra de Um Ano",
    
    # Erro clássico: Gato Lúcifer traduzido como Gólgota
    "路西法没人照料": "O Lúcifer está sem ninguém para cuidar dele.",
    "路西法？": "Lúcifer?",
    "路西法是只猫？": "Lúcifer é um gato?",
    "路西法最怕孤单了": "O Lúcifer é o que mais teme a solidão.",
    "叔叔一定带回那只路西法": "O tio certamente trará de volta o Lúcifer.",
    "执行营救路西法作战": "Executar a operação de resgate do Lúcifer",
    "忘记告诉叔叔 路西法会抓陌生人的": "Esqueci de avisar o tio: o Lúcifer arranha estranhos.",
    "被路西法那小东西挠的": "Foi aquele pequeno Lúcifer que me arranhou.",
    "路西法 过来": "Lúcifer, vem aqui.",
    "不可以叫 路西法": "Não chame ele de Lúcifer",
    "来 路西法": "Vem, Lúcifer.",
    "刚才路西法发出了奇怪的鼾声": "O Lúcifer estava roncando estranho agora há pouco.",
    "路西法也上年纪了": "O Lúcifer também está ficando velho.",
    "路西法 抱歉": "Lúcifer, desculpe.",
    "路西法 你觉得妈妈一个人太孤单": "Lúcifer, você acha que a mamãe está muito sozinha?",
    "路西法也死了": "O Lúcifer também morreu.",
    
    # Erro de contexto: Mandar família Ral para o outro lado (送拉尔一家上路)
    "送拉尔一家上路": "Eliminem a família Ral.",
    
    # Erro de contexto: Nave Grande Degwin (大德金号)
    "我见公王陛下的座舰大德金号孤身在前…": "Pude ver a nau capitânia de Sua Majestade, a Grande Degwin, avançando sozinha na frente...",

    # Ranks, Falmel, Munzo e Sequestro de Casval/Artesia
    "多兹鲁上校来了 打起精神！": "O Coronel Dozle chegou! Vamos nos esforçar!",
    "校长！多兹鲁上校": "Diretor! Coronel Dozle",
    "没有 上校阁下": "Não, Coronel.",
    "上校阁下 我有一个请求": "Coronel, tenho um pedido a fazer.",
    "夏亚中尉 能够恢复士官官职": "Tenente Char, você poderá recuperar seu posto de oficial.",
    "红色士官服倒是很适合你啊 中尉": "O uniforme vermelho de oficial realmente fica bem em você, Tenente.",
    "将破格连升两级 成为少校": "Você será promovido duas patentes de uma vez, tornando-se Major.",
    "这样的话 就让你也晋升少校…": "Nesse caso, farei você ser promovido a Major também...",
    "我现在是最精锐的空降师团的少校": "Agora sou Major na divisão de paraquedistas de elite.",
    "虽然军衔是少校": "Embora a minha patente seja Major,",
    "是夏亚·阿兹纳布尔少校了": "É o Major Char Aznable.",
    "夏亚少校 前往执行任务": "Major Char, partindo para executar a missão.",
    "别开玩笑了 少校大人": "Não brinque comigo, Major.",
    "本舰是夏亚·阿兹纳布尔少校座舰 法美尔号": "Esta é a Falmel, a nau capitânia do Major Char Aznable.",
    "等等 夏亚少校": "Espere, Major Char.",
    "中尉大人 夏亚少校出舰外了": "Tenente, o Major Char saiu da nave.",
    "少校大人": "Major.",
    "盖亚上尉 马修中尉 奥尔迪加中尉": "Capitão Gaia, Tenente Mash, Tenente Ortega.",
    "不才德伦中尉 奉命接任代理舰长": "Eu, o humilde Tenente Dren, assumo como capitão interino.",
    "[T0]全权委任马·克贝中将": "[T0]Plenipotenciário Tenente-General M'Quve",
    "我言明在先 马·克贝中将": "Deixe-me deixar claro, Tenente-General M'Quve.",
    "马·克贝中将": "Tenente-General M'Quve",
    "联邦军的载具抢走了卡斯帕尔 e 阿尔黛西亚？": "Os veículos da Federação sequestraram Casval e Artesia?",
    "联邦军的载具抢走了卡斯帕尔和阿尔黛西亚？": "Os veículos da Federação sequestraram Casval e Artesia?",
    "夏亚先生说的学校？": "A escola que o Sr. Char mencionou?",
    "同鲁姆出身 夏亚·阿兹纳布尔": "Também nascido em Loum, Char Aznable.",
    "上校 那家伙疯了": "Coronel, aquele cara está louco.",
    "是呢 伯格曼少校": "Sim, Major Bergman.",
    "伯格曼少校": "Major Bergman.",
    "提安姆中将的舰队": "A frota do Almirante Tianem.",
    "正赶赴与吉翁军会战宙域的提安姆中将舰队": "A frota do Almirante Tianem, a caminho da zona de combate contra as forças de Zeon.",
    "德伦中尉": "Tenente Dren",
    "舰长是你啊 德伦中尉": "O capitão é você, Tenente Dren.",
    "我在您和卡斯帕尔少爷逃出慕佐时": "Quando você e o Sr. Casval escaparam de Munzo"
}

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
        sufixo_padrao = f" (ENTER = {padrao_caminho})" if padrao_caminho else ""
        entrada = input(f"{Fore.YELLOW}{mensagem_prompt}{sufixo_padrao}: {Style.RESET_ALL}").strip()
        entrada = entrada.strip('"').strip("'")
        if not entrada and padrao_caminho:
            return padrao_caminho
        if not entrada:
            continue
        if not os.path.isdir(entrada):
            print(f"{Fore.RED}[ERRO] Diretorio nao existe: {entrada}")
            continue
        return entrada


def carregar_json(caminho):
    with open(caminho, 'r', encoding='utf-8') as f:
        return json.load(f)


def salvar_json(caminho, dados):
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)


def aplicar_correcao_linha_ass(texto_dialogo):
    """Aplica as correções determinísticas de lore no texto traduzido de uma linha ASS."""
    original = texto_dialogo
    
    # 1. Correções estritas de frases completas (ou quase completas) do gato
    if "Gólgota não está sendo cuidado" in texto_dialogo:
        texto_dialogo = texto_dialogo.replace("Gólgota não está sendo cuidado", "O Lúcifer está sem ninguém para cuidar dele")
    elif "Gólgota?" in texto_dialogo:
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

    # 4. Correções de patentes, sequestro e naves/locais
    texto_dialogo = texto_dialogo.replace("roubaram Casval e Artesia", "sequestraram Casval e Artesia")
    texto_dialogo = texto_dialogo.replace("serem roubados", "serem sequestrados")
    texto_dialogo = texto_dialogo.replace("Este é o navio Fafnir, do tenente-coronel Char Aznable.", "Esta é a Falmel, a nau capitânia do Major Char Aznable.")
    texto_dialogo = texto_dialogo.replace("Espera, Tenente Char.", "Espera, Major Char.")
    texto_dialogo = texto_dialogo.replace("Tenente-general, o Tenente Char saiu do navio.", "Tenente, o Major Char saiu da nave.")
    texto_dialogo = texto_dialogo.replace("O melhor dos melhores, o Tenente Char...", "O melhor dos melhores, o Major Char...")
    texto_dialogo = texto_dialogo.replace("É o Subtenente Char Aznable.", "É o Major Char Aznable.")
    texto_dialogo = texto_dialogo.replace("É o Subtenente Char", "É o Tenente Char")
    texto_dialogo = texto_dialogo.replace("Tenente Char, indo executar uma missão.", "Major Char, partindo para executar a missão.")
    texto_dialogo = texto_dialogo.replace("Tenente Char, você pode recuperar o cargo de sargento.", "Tenente Char, você poderá recuperar seu posto de oficial.")
    texto_dialogo = texto_dialogo.replace("O uniforme vermelho de sargento realmente te fica bem, Tenente.", "O uniforme vermelho de oficial realmente fica bem em você, Tenente.")
    texto_dialogo = texto_dialogo.replace("Será promovido de graça dois níveis e se tornará tenente", "Você será promovido duas patentes de uma vez, tornando-se Major.")
    texto_dialogo = texto_dialogo.replace("Assim você também será promovido a tenente...", "Nesse caso, farei você ser promovido a Major também...")
    texto_dialogo = texto_dialogo.replace("Agora sou o tenente da mais elite divisão de paratroops.", "Agora sou Major na divisão de paraquedistas de elite.")
    texto_dialogo = texto_dialogo.replace("Aunque eu seja tenente,", "Embora a minha patente seja Major,")
    texto_dialogo = texto_dialogo.replace("Pare com isso, Coronel", "Não brinque comigo, Major.")
    texto_dialogo = texto_dialogo.replace("Tenente Ramba Ral foi ordenado a assumir o cargo de tenente-comandante interino.", "Eu, o humilde Tenente Dren, fui ordenado a assumir como capitão interino.")
    texto_dialogo = texto_dialogo.replace("O General-mor Marc Kibei declara.", "O Tenente-General M'Quve declara.")
    texto_dialogo = texto_dialogo.replace("Almirante Marckbe", "Tenente-General M'Quve")
    texto_dialogo = texto_dialogo.replace("Plenipotenciário Al·Kbat, Tenente Coronel", "Plenipotenciário Tenente-General M'Quve")
    texto_dialogo = texto_dialogo.replace("O Tenente-Coronel Dozle chegou! Vamos nos esforçar mais!", "O Coronel Dozle chegou! Vamos nos esforçar!")
    texto_dialogo = texto_dialogo.replace("Tenente Gaia, Tenente Matthew, Tenente Ordiga.", "Capitão Gaia, Tenente Mash, Tenente Ortega.")
    texto_dialogo = texto_dialogo.replace("O Cometa Vermelho falou sobre uma escola?", "A escola que o Sr. Char mencionou?")
    texto_dialogo = texto_dialogo.replace("Como origem Loum, Char Aznable", "Também nascido em Loum, Char Aznable.")
    texto_dialogo = texto_dialogo.replace("Como o azul de Casval Rem Deikun.", "Tão azul quanto o de Casval Rem Deikun.")
    texto_dialogo = texto_dialogo.replace("Mu Zoa", "Munzo")
    texto_dialogo = texto_dialogo.replace("Mu Zou", "Munzo")

    # 5. Substituições gerais de termos
    # Guerra de Um Ano
    texto_dialogo = re.sub(r"\bGuerra (?:de|dos|do)?\s?(?:Cem|100) Anos\b", "Guerra de Um Ano", texto_dialogo, flags=re.I)
    texto_dialogo = re.sub(r"\bGuerra do Ano Um\b", "Guerra de Um Ano", texto_dialogo, flags=re.I)
    
    # Lúcifer (nome do gato com acento)
    # Evita duplicar acentuação no Lúcifer
    texto_dialogo = re.sub(r"\bL[uú]cifer\b", "Lúcifer", texto_dialogo)
    texto_dialogo = re.sub(r"\bL[uú]cifero\b", "Lúcifer", texto_dialogo)
    
    # Principado de Zeon
    texto_dialogo = re.sub(r"\bPrincipado de Dion\b", "Principado de Zeon", texto_dialogo, flags=re.I)
    
    # Retorna o texto corrigido e se houve modificação
    return texto_dialogo, texto_dialogo != original


def corrigir_cache_traducao(caminho_cache):
    print(f"\n{Fore.CYAN}--- CORREÇÃO DO CACHE DE TRADUÇÃO ---")
    if not os.path.exists(caminho_cache):
        print(f"{Fore.RED}[ERRO] Cache de tradução não encontrado em: {caminho_cache}")
        return False
        
    # Backup de segurança
    caminho_bak = caminho_cache + ".bak"
    shutil.copyfile(caminho_cache, caminho_bak)
    print(f"{Fore.GREEN}[OK] Backup de segurança do cache criado em: {caminho_bak}")
    
    cache = carregar_json(caminho_cache)
    corrigidos_estritos = 0
    corrigidos_genericos = 0
    
    # 1. Correções estritas pré-mapeadas
    for k, v in CORRECOES_CACHE_ESTRITAS.items():
        if k in cache:
            if cache[k] != v:
                print(f"  ↳ [ESTRITO] Corrigido chave {Fore.YELLOW}{k}{Style.RESET_ALL} -> de '{cache[k]}' para '{v}'")
                cache[k] = v
                corrigidos_estritos += 1

    # 2. Correções genéricas em todos os valores
    for k, v in cache.items():
        valor_novo, modificado = aplicar_correcao_linha_ass(v)
        if modificado and k not in CORRECOES_CACHE_ESTRITAS:
            print(f"  ↳ [GENÉRICO] Corrigido valor -> de '{v}' para '{valor_novo}'")
            cache[k] = valor_novo
            corrigidos_genericos += 1
            
    salvar_json(caminho_cache, cache)
    print(f"{Fore.GREEN}[OK] Cache de tradução atualizado com sucesso!")
    print(f"{Fore.GREEN}Total corrigido: {corrigidos_estritos} estritos, {corrigidos_genericos} genéricos.")
    return True


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
                    
                    texto_novo, modificado = aplicar_correcao_linha_ass(texto_dialogo)
                    if modificado:
                        modificacoes_no_arquivo += 1
                        linha = f"{metadados}{texto_novo}\n"
                        # Printar a modificação de forma legível
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


def remuxar_legendas_mkv(pasta_mkv, pasta_legendas):
    print(f"\n{Fore.CYAN}--- RE-MULTIPLEXAÇÃO DOS MKVs ---")
    if not MKVMERGE_PATH:
        print(f"{Fore.RED}[ERRO] mkvmerge não encontrado no sistema. Remuxing abortado.")
        return False
        
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
            m_leg_ep = re.search(r'\[(\d+)\]', leg)
            if not m_leg_ep:
                m_leg_ep = re.search(r'E(\d+)', leg, re.I)
            if m_leg_ep and m_leg_ep.group(1) == ep_num:
                legenda_correta = leg
                break
                
        if not legenda_correta:
            print(f"  {Fore.RED}[ERRO] Legenda corrigida correspondente não encontrada para o EP {ep_num} ({nome_mkv}).")
            continue
            
        caminho_legenda = os.path.join(pasta_legendas, legenda_correta)
        caminho_saida_mkv = os.path.join(pasta_saida, nome_mkv)
        
        print(f"\n[{idx}/{len(arquivos_mkv)}] Remuxando EP {ep_num}: {nome_mkv}...")
        print(f"  ↳ Utilizando legenda: {legenda_correta}")
        
        cmd = [
            MKVMERGE_PATH,
            "-o", caminho_saida_mkv,
            "--no-subtitles",       # Descarta a legenda anterior com erro
            caminho_mkv,            # Vídeo/Áudio originais
            "--language", "0:por",
            "--track-name", "0:Português (Revisada - Lúcifer & Um Ano)",
            "--default-track", "0:yes",
            caminho_legenda         # Nova legenda corrigida
        ]
        
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode == 0 and os.path.exists(caminho_saida_mkv):
            print(f"  {Fore.GREEN}[SUCESSO] Multiplexado! Salvo em: corrigidos\\{nome_mkv}")
        else:
            print(f"  {Fore.RED}[ERRO] Falha ao executar mkvmerge para {nome_mkv}.")
            
    print(f"\n{Fore.GREEN}[OK] Processo de remuxing finalizado!")
    return True


def main():
    print("=" * 80)
    print(f"{Fore.CYAN}       STEWARDESS DE REVISÃO E COMPLIANCE DE LORE: GUNDAM ORIGIN")
    print("=" * 80)
    
    # 1. Carregar e corrigir o cache de tradução
    caminho_cache = obter_diretorio_obrigatorio("Caminho completo do cache de tradução JSON", CAMINHO_CACHE_PADRAO)
    if not os.path.isfile(caminho_cache):
        # Caso o usuário passe apenas a pasta
        caminho_cache = os.path.join(caminho_cache, "traducao_cache_origin_zh.json")
        
    corrigir_cache_traducao(caminho_cache)
    
    # 2. Corrigir os arquivos de legenda .ass já extraídos
    pasta_legendas = obter_diretorio_obrigatorio("Pasta com arquivos de legenda .ass extraídos", PASTA_LEGENDA_PADRAO)
    corrigir_arquivos_ass(pasta_legendas)
    
    # 3. Perguntar se deseja remuxar
    print("\n" + "=" * 80)
    opcao = input(f"{Fore.YELLOW}Deseja remuxar as legendas corrigidas nos arquivos .mkv originais? (s/n): {Style.RESET_ALL}").strip().lower()
    
    if opcao == 's':
        pasta_mkv = obter_diretorio_obrigatorio("Pasta com os arquivos .mkv originais", PASTA_ANIME_PADRAO)
        remuxar_legendas_mkv(pasta_mkv, pasta_legendas)
        
    print("\n" + "=" * 80)
    print(f"{Fore.GREEN}[FIM] Processo concluído! Obrigado por manter a integridade da Universal Century!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[AVISO] Interrompido pelo operador.")
        sys.exit(0)
