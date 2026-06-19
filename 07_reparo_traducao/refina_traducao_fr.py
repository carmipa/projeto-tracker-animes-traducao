#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: refina_traducao_fr.py
Revisa e refina as legendas traduzidas (*_ENG.ass na pasta legendas_ptbr) via LM Studio.
- Utiliza engenharia reversa no cache traducao_cache_fr.json para obter o francês original.
- Corrige erros de gênero, concordância, patentes, pronomes e resíduos do francês.
- Atualiza o cache e gera um relatório detalhado de alterações.

Author: Antigravity + Paulo
Data: Junho 2026
"""

import os
import re
import json
import time
import sys
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import init, Fore, Style

# Garante suporte a caracteres especiais no console Windows
if sys.version_info >= (3, 7):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

try:
    from tqdm import tqdm
except ImportError:
    print("ERRO: tqdm nao instalado. Execute no ambiente correto: pip install tqdm")
    sys.exit(1)

init(autoreset=True)

# Configurações do LM Studio
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
LM_STUDIO_MODELS_URL = "http://localhost:1234/v1/models"
MODELO_ATIVO = "local-model"

# Caminhos padrão
PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PASTA_RAIZ = os.path.dirname(PASTA_SCRIPT)
CAMINHO_CACHE = os.path.join(PASTA_RAIZ, "05b_tradutor_llm_mistral_nemo", "frances_para_ptbr", "traducao_cache_fr.json")
PASTA_LEGENDAS = r"C:\animes\Mobile_Suit_Gundam_The_Origin_Advent_of_the_Red_Comet\legendas_ptbr"
CAMINHO_RELATORIO = os.path.join(PASTA_SCRIPT, "relatorio_refino.txt")

# Padrão de resíduo francês para detecção direta
PADRAO_RESIDUO_FRANCES = re.compile(
    r"\b(vous|avec|[êe]tre|êtes|été|leur|cette|alors|où|très|pour|dans|sans|"
    r"toujours|voilà|monsieur|madame|qu['’]il|qu['’]elle|c['’]est|n['’]est|"
    r"n['’]a|d['’]un|d['’]une|cet|ceci|cela|besoin|soins|enfant|oui|non|mais|pas)\b",
    re.IGNORECASE
)

# Prompt de Sistema do Revisor
SYSTEM_PROMPT = (
    "Você é um tradutor, localizador e revisor especialista em legendas de anime, ficção científica militar, mechas e no universo de Mobile Suit Gundam: The Origin / Universal Century.\n\n"
    "Sua tarefa é REVISAR e CORRIGIR a legenda em Português do Brasil (PT-BR), garantindo concordância gramatical, pronomes corretos, patentes militares consistentes e concordância de gênero perfeita (especialmente para personagens femininas).\n\n"
    "DIRETRIZES IMPORTANTES:\n"
    "1. GÊNERO FEMININO:\n"
    "   - Artesia Som Deikun / Sayla Mass é mulher. Use artigos, pronomes e adjetivos femininos (\"ela\", \"dela\", \"cansada\", \"obediente\", \"a senhorita Artesia\").\n"
    "   - Kycilia Zabi é mulher (\"ela\", \"dela\", \"chefe das Forças de Segurança\", \"a Kycilia\").\n"
    "   - Crowley Hamon é mulher (\"ela\", \"dela\", \"a Hamon\").\n"
    "   - Astraia Tor Deikun é mulher (\"ela\", \"dela\", \"a Astraia\", \"a mãe\").\n"
    "   Certifique-se de que quando falarem com elas ou sobre elas, a concordância de gênero seja estritamente feminina (ex: \"Você está bem, Artesia?\" ou \"A Sra. Roselucia faleceu\").\n\n"
    "2. PATENTES MILITARES:\n"
    "   - Amiral -> Almirante (ex: Almirante Revil)\n"
    "   - Vice-amiral -> Vice-almirante (ex: Vice-almirante Dozle Zabi)\n"
    "   - Général -> General (ex: General Gopp, General Revil, General Elran)\n"
    "   - Colonel -> Coronel\n"
    "   - Lieutenant-colonel -> Tenente-coronel\n"
    "   - Major / Commandant -> Major ou Comandante (ex: Comandante Char Aznable)\n"
    "   - Capitaine -> Capitão (ex: Capitão Ramba Ral)\n"
    "   - Lieutenant -> Tenente (ex: Tenente Char, Tenente Gaia)\n"
    "   - Sous-lieutenant -> Segundo-tenente / Subtenente (ex: Segundo-tenente Tachi)\n"
    "   - Sergent -> Sargento (ex: Sargento Cozun Graham)\n"
    "   - Caporal -> Cabo\n"
    "   - Soldat -> Soldado\n"
    "   Eles devem ter a concordância de artigo correta (ex: \"o tenente Char\", \"a capitã...\" se feminino, etc.).\n\n"
    "3. CONCORDÂNCIA E PRONOMES:\n"
    "   - \"Vous\" formal pode ser \"você\", \"senhor/senhora\", ou \"vocês\" no plural. Corrija concordâncias incorretas (ex: \"Você é Artesia e Casval\" deve ser \"Vocês são Artesia e Casval\").\n"
    "   - Evite literalismo. Adapte frases de forma natural.\n\n"
    "4. ELIMINAÇÃO DE FRANCÊS RESIDUAL:\n"
    "   - Traduza termos como \"Ceci\", \"Cela\", \"vous\", \"besoin\", \"soins\", \"enfant\" que ficaram sem tradução no português original.\n\n"
    "REGRAS DE RETORNO:\n"
    "- Responda APENAS com a tradução final em PT-BR corrigida, sem explicações, preâmbulos, notas ou markdown.\n"
    "- Preserve exatamente os marcadores de tag ASS (ex: [T0], [T1]) e escapes de quebra de linha (\\\\N, \\\\n) em seus devidos lugares lógicos na frase."
)


def verificar_lm_studio() -> bool:
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


def normalizar_texto(texto: str) -> str:
    """Normaliza o texto para busca no cache (minúsculo, sem pontuação, sem tags)."""
    # Remove tags ASS e marcadores [Tn]
    texto = re.sub(r'\{[^}]+\}', '', texto)
    texto = re.sub(r'\[T\d+\]', '', texto)
    texto = texto.replace(r'\N', ' ').replace(r'\n', ' ').replace(r'\h', ' ')
    # Remove pontuação e converte para minúsculo
    texto = re.sub(r'[^\w\s]', '', texto)
    return " ".join(texto.lower().split())


def carregar_e_inverter_cache():
    """Carrega o cache original e monta o mapeamento reverso normalizado."""
    if not os.path.exists(CAMINHO_CACHE):
        print(f"{Fore.RED}[ERRO] Cache de tradução não encontrado em: {CAMINHO_CACHE}")
        sys.exit(1)
        
    with open(CAMINHO_CACHE, 'r', encoding='utf-8') as f:
        cache_original = json.load(f)
        
    print(f"{Fore.GREEN}[OK] Carregado cache original com {len(cache_original)} entradas.")
    
    cache_reverso = {}
    for fr, pt in cache_original.items():
        pt_norm = normalizar_texto(pt)
        if pt_norm:
            # Associa o PT normalizado ao francês original
            cache_reverso[pt_norm] = fr
            
    return cache_original, cache_reverso


def chamar_api_revisao(original_fr: str, atual_pt: str, modo: str) -> str:
    """Envia a linha para o LM Studio refinar a tradução."""
    if modo == "revisao_completa":
        user_prompt = (
            f"Texto original em Francês: {original_fr}\n"
            f"Tradução atual em PT-BR (pode conter erros): {atual_pt}\n\n"
            "Instrução: Revise a tradução atual em PT-BR com base no original em Francês, aplicando todas as diretrizes de gênero, patentes, concordância e fluidez natural de Gundam. Retorne APENAS a linha de tradução corrigida final."
        )
    elif modo == "traducao_direta":
        user_prompt = (
            f"Linha em Francês para traduzir: {original_fr}\n\n"
            "Instrução: Traduza a linha do Francês para Português do Brasil (PT-BR) aplicando todas as diretrizes de gênero, patentes, concordância e fluidez natural de Gundam. Retorne APENAS a tradução final em PT-BR."
        )
    else:  # revisao_apenas_pt
        user_prompt = (
            f"Tradução atual em PT-BR para revisão: {atual_pt}\n\n"
            "Instrução: Revise e corrija a gramática, concordância de gênero, pronomes, patentes e fluidez natural desta linha em PT-BR. Retorne APENAS a linha corrigida final."
        )

    payload = {
        "model": MODELO_ATIVO,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 150
    }

    for tentativa in range(3):
        try:
            r = requests.post(LM_STUDIO_URL, json=payload, timeout=90)
            if r.status_code == 200:
                retorno = r.json()['choices'][0]['message']['content'].strip()
                # Remove aspas ou comentários adicionais
                retorno = re.sub(r'<think>.*?</think>', '', retorno, flags=re.DOTALL)
                retorno = retorno.strip().strip('"').strip("'").strip()
                if retorno:
                    return retorno
            time.sleep(2)
        except Exception:
            time.sleep(2)
    return ""


def processar_texto_com_tags(texto_pt_br: str, original_fr: str, modo: str):
    """Mascara as tags ASS, chama a API de revisão e restaura as tags."""
    # Mapeamento de tags
    tags = re.findall(r'\{[^}]+\}', texto_pt_br)
    texto_masc = texto_pt_br
    for idx, tag in enumerate(tags):
        texto_masc = texto_masc.replace(tag, f"[T{idx}]", 1)
        
    tags_fr = re.findall(r'\{[^}]+\}', original_fr)
    original_masc = original_fr
    for idx, tag in enumerate(tags_fr):
        original_masc = original_masc.replace(tag, f"[T{idx}]", 1)

    # Chama a API de revisão
    resultado = chamar_api_revisao(original_masc, texto_masc, modo)
    if not resultado:
        return None

    # Limpa e formata quebras de linha
    resultado = resultado.replace("/N", r"\N").replace("/n", r"\n")
    resultado = re.sub(r"\s+([!?:;,.])", r"\1", resultado)
    
    # Restaura as tags
    for idx, tag in enumerate(tags):
        marcador = f"[T{idx}]"
        if marcador in resultado:
            resultado = resultado.replace(marcador, tag, 1)
        else:
            resultado = re.sub(rf'\[?[Tt]\s*{idx}\]?', lambda m: tag, resultado, count=1)
            
    return resultado


def limpar_saida_para_cache(texto: str) -> str:
    """Limpa e formata a saída para salvar no cache do Mistral Nemo."""
    texto = texto.strip()
    texto = re.sub(r"^\s*[-–•]\s*", "", texto)
    texto = re.sub(r"\[\s*[Tt]\s*(\d+)\s*\]", r"[T\1]", texto)
    texto = re.sub(r"\\\s*([Nnh])", r"\\\1", texto)
    texto = texto.replace("/N", r"\N").replace("/n", r"\n")
    return texto


def precisa_de_refinamento(texto_pt: str, texto_fr: str) -> bool:
    """Retorna True se a linha em português precisa ser refinada pela IA."""
    texto_pt_lower = texto_pt.lower()
    texto_fr_lower = texto_fr.lower() if texto_fr else ""

    # 1. Se o português é idêntico ao francês, com certeza precisa de tradução/refinamento
    if texto_fr and normalizar_texto(texto_pt) == normalizar_texto(texto_fr):
        return True

    # 2. Resíduos franceses explícitos
    if PADRAO_RESIDUO_FRANCES.search(texto_pt) and (not any(w in texto_pt_lower for w in ["não", "como", "esta", "para", "você"])):
        return True

    # 3. Nomes críticos de gênero ou termos-chave de lore
    nomes_criticos = [
        "artesia", "sayla", "kycilia", "hamon", "astraia", "roselucia", 
        "zena", "mineva", "lucifer", "gato", "chat", "deikun", "daikun",
        "zabi", "ramba", "ral", "casval"
    ]
    if any(nome in texto_pt_lower for nome in nomes_criticos):
        return True
    if texto_fr_lower and any(nome in texto_fr_lower for nome in nomes_criticos):
        return True

    # 4. Ranks / Patentes militares
    patentes = [
        "amiral", "almirante", "général", "general", "colonel", "coronel",
        "commandant", "comandante", "major", "capitaine", "capitão", "capitã",
        "lieutenant", "tenente", "sous-lieutenant", "segundo-tenente", "subtenente",
        "sergent", "sargento", "caporal", "cabo", "soldat", "soldado", "officier",
        "oficial", "cadet", "cadete"
    ]
    if any(patente in texto_pt_lower for patente in patentes):
        return True
    if texto_fr_lower and any(patente in texto_fr_lower for patente in patentes):
        return True

    # 5. Padrões de pronomes que costumam ter erros de concordância
    pronomes_check = ["tu ", "vais", "vossa", "excelência", "vous", "amou", "golgotha", "gólgota"]
    if any(p in texto_pt_lower for p in pronomes_check):
        return True
    if texto_fr_lower and any(p in texto_fr_lower for p in pronomes_check):
        return True

    # 6. Padrões de concordância de gênero sutil
    adjetivos_genero = ["obrigado", "obrigada", "cansado", "cansada", "vindo", "vinda", "sozinho", "sozinha", "bonito", "linda", "lindo", "bela", "belo", "querido", "querida"]
    if any(adj in texto_pt_lower for adj in adjetivos_genero):
        return True

    # 7. Erros de capitalização no meio de frases
    if re.search(r'[a-z\u00e0-\u00fa],\s+[A-Z]', texto_pt) or (re.search(r'\b\w+\s+[A-Z][a-z]', texto_pt) and not re.search(r'\b(I|II|III|IV|V|VI|VII|VIII|IX|X|Char|Casval|Artesia|Sayla|Kycilia|Hamon|Astraia|Zabi|Deikun|Daikun|Zeon|Federados|Federação|Side|Gundam|Zaku|Mobile|Suit|Armor|Loum|British|Texas|Munzo|Zum|City|Amuro|Ray|Tem|Lalah|Sune|Bright|Noa|Mirai|Yashima|Gaia|Ortega|Mash|Revil|Great|Degwin|Gwazine|Chivvay|Papua|Columbus|White|Base|Falmel|Dren|Denim|Wakkein|Elran|Gopp|MQuve|Scott|Haro|William|Kemp|Judock)\b', texto_pt)):
        return True

    return False


def refinar_legendas():
    if not verificar_lm_studio():
        return

    cache_original, cache_reverso = carregar_e_inverter_cache()
    
    if not os.path.exists(PASTA_LEGENDAS):
        print(f"{Fore.RED}[ERRO] Pasta de legendas não encontrada: {PASTA_LEGENDAS}")
        return

    arquivos_ass = sorted([f for f in os.listdir(PASTA_LEGENDAS) if f.lower().endswith('.ass')])
    if not arquivos_ass:
        print(f"{Fore.YELLOW}[AVISO] Nenhum arquivo .ass em: {PASTA_LEGENDAS}")
        return

    print(f"\n{Fore.GREEN}[OK] Encontrados {len(arquivos_ass)} arquivos .ass para refinamento.")
    
    total_linhas_revisadas = 0
    total_linhas_alteradas = 0
    linhas_detalhes_relatorio = []
    
    pat_dialogue = re.compile(r"^(Dialogue:\s*[^,]*(?:,[^,]*){8},)(.*)$")
    
    # Limitação de concorrência segura (threads = 2)
    max_workers = 2
    
    for idx_arq, arquivo in enumerate(arquivos_ass, 1):
        caminho_file = os.path.join(PASTA_LEGENDAS, arquivo)
        print(f"\n{Fore.YELLOW}=== [{idx_arq}/{len(arquivos_ass)}] PROCESSANDO: {arquivo} ===")
        
        with open(caminho_file, 'r', encoding='utf-8-sig') as f:
            linhas = f.readlines()
 
        # Estruturas para processamento paralelo de diálogos
        dialogo_indices = []
        dialogo_textos = []
        dialogo_modos = []
        dialogo_fr_sources = []
 
        for i, linha in enumerate(linhas):
            if not linha.startswith("Dialogue:"):
                continue
                
            m = pat_dialogue.match(linha.strip())
            if not m:
                continue
                
            prefixo = m.group(1)
            texto_dialogo = m.group(2).strip()
            
            # Ignora vazios ou créditos
            texto_puro = re.sub(r'\{.*?\}', '', texto_dialogo).strip()
            if not texto_puro or "adaptation" in texto_puro.lower() or "traduction" in texto_puro.lower():
                continue
 
            # Determina o modo e o francês original
            original_fr = None
            modo = "revisao_apenas_pt"
            
            # 1. Verifica se a própria fala na legenda é francesa (não traduzida)
            if PADRAO_RESIDUO_FRANCES.search(texto_puro) and (not any(w in texto_puro.lower() for w in ["não", "como", "esta", "para", "você"])):
                # Parece francês puro na legenda!
                original_fr = texto_dialogo
                modo = "traducao_direta"
            else:
                # 2. Busca no cache reverso normalizado
                pt_norm = normalizar_texto(texto_dialogo)
                if pt_norm in cache_reverso:
                    original_fr = cache_reverso[pt_norm]
                    modo = "revisao_completa"
                elif texto_dialogo in cache_original:
                    # Se por acaso a chave original for o próprio PT (caso de alinhamento 1-1 em português puro)
                    original_fr = texto_dialogo
                    modo = "revisao_completa"
 
            # Se achou uma fala com desalinhamento óbvio no cache
            # Exemplo: O PT diz "Você é Srta. Artesia?" mas o FR diz "Docteur !\NCet enfant a besoin de soins !"
            if original_fr and "artesia" in texto_dialogo.lower() and "docteur" in original_fr.lower():
                # Força tradução direta para corrigir desalinhamentos
                modo = "traducao_direta"
 
            dialogo_indices.append(i)
            dialogo_textos.append(texto_dialogo)
            dialogo_modos.append(modo)
            dialogo_fr_sources.append(original_fr if original_fr else "")
 
        if not dialogo_textos:
            print(f"  [OK] Nenhuma linha de diálogo qualificada para refinamento.")
            continue
 
        linhas_novas = list(linhas)
        alterados_no_arquivo = 0
        
        # Processa em lote paralelo
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futuros_map = {}
            ignora_cont = 0
            for idx_d, (texto_pt, original_fr, modo) in enumerate(zip(dialogo_textos, dialogo_fr_sources, dialogo_modos)):
                if precisa_de_refinamento(texto_pt, original_fr):
                    f = executor.submit(processar_texto_com_tags, texto_pt, original_fr, modo)
                    futuros_map[f] = (idx_d, texto_pt, original_fr, modo)
                else:
                    ignora_cont += 1
                    
            print(f"  -> {ignora_cont} linha(s) mantida(s) sem refino. Processando {len(futuros_map)} suspeitas...")
            
            if futuros_map:
                with tqdm(total=len(futuros_map), desc="  Refinando", unit="linha", leave=False) as pbar:
                    for futuro in as_completed(futuros_map):
                        idx_d, texto_pt, original_fr, modo = futuros_map[futuro]
                        idx_linha = dialogo_indices[idx_d]
                    
                        try:
                            resultado = futuro.result()
                            if resultado and resultado != texto_pt:
                                # Teve alteração!
                                m = pat_dialogue.match(linhas[idx_linha].strip())
                                if m:
                                    prefixo = m.group(1)
                                    linhas_novas[idx_linha] = f"{prefixo}{resultado}\n"
                                    alterados_no_arquivo += 1
                                    total_linhas_alteradas += 1
                                    
                                    # Mostra logs em tempo real sem quebrar barra de progresso
                                    tqdm.write(f"  {Fore.GREEN}[CORRIGIDO] L{idx_linha+1}:\n    Antes : {texto_pt}\n    Depois: {resultado}")
                                    
                                    # Se temos o francês original, atualiza o cache também!
                                    if original_fr:
                                        fr_limpo = limpar_saida_para_cache(original_fr)
                                        pt_limpo = limpar_saida_para_cache(resultado)
                                        cache_original[fr_limpo] = pt_limpo

                                    linhas_detalhes_relatorio.append(
                                        f"[{arquivo} L{idx_linha+1}] ({modo})\n"
                                        f"  FR: {original_fr}\n"
                                        f"  PT_ANTIGO: {texto_pt}\n"
                                        f"  PT_NOVO:   {resultado}\n"
                                    )
                        except Exception as e:
                            tqdm.write(f"  {Fore.RED}[ERRO] Falha ao refinar linha {idx_linha+1}: {e}")
                        
                        total_linhas_revisadas += 1
                        pbar.update(1)

        # Se houve modificações, salva o arquivo .ass
        if alterados_no_arquivo > 0:
            with open(caminho_file, 'w', encoding='utf-8-sig') as f:
                f.writelines(linhas_novas)
            print(f"  {Fore.GREEN}[SALVO] {arquivo} atualizado com {alterados_no_arquivo} correções.")
            
            # Salva o cache incrementalmente
            try:
                with open(CAMINHO_CACHE, 'w', encoding='utf-8') as f:
                    json.dump(cache_original, f, indent=2, ensure_ascii=False)
            except Exception as e_cache:
                print(f"  {Fore.RED}[AVISO] Erro ao salvar cache incremental: {e_cache}")
        else:
            print(f"  [OK] {arquivo} revisado sem alterações necessárias.")

    # Escreve o relatório final
    conteudo_relatorio = [
        "================================================================================",
        "RELATÓRIO DE REFINAMENTO DE LEGENDAS E CACHE (FRANCÊS -> PT-BR) - GUNDAM ORIGIN",
        "================================================================================",
        f"Data de Execução : {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total de Linhas Revisadas: {total_linhas_revisadas}",
        f"Total de Linhas Corrigidas: {total_linhas_alteradas}",
        "================================================================================",
        "\nDETALHE DAS ALTERAÇÕES LADO A LADO:\n"
    ] + linhas_detalhes_relatorio
    
    with open(CAMINHO_RELATORIO, 'w', encoding='utf-8') as f:
        f.write("\n".join(conteudo_relatorio))
        
    print("\n" + "=" * 80)
    print(f"{Fore.GREEN}[CONCLUÍDO] Processo de refinamento concluído!")
    print(f"Linhas revisadas: {total_linhas_revisadas} | Linhas corrigidas: {total_linhas_alteradas}")
    print(f"Cache de tradução atualizado em: {CAMINHO_CACHE}")
    print(f"Relatório detalhado salvo em: {CAMINHO_RELATORIO}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        refinar_legendas()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[AVISO] Interrompido pelo operador.")
        sys.exit(0)
