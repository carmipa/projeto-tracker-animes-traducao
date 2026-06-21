#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: extrai_linhas_suspeitas.py
Varre as legendas e gera um JSON consolidado contendo apenas as falas que
precisam de refinamento de gênero, pronomes, resíduos de francês ou patentes.

Author: Antigravity
Data: Junho 2026
"""

import os
import re
import json
import sys

# Caminhos
PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PASTA_RAIZ = os.path.dirname(os.path.dirname(PASTA_SCRIPT))
CAMINHO_CACHE = os.path.join(PASTA_RAIZ, "05b_tradutor_llm_mistral_nemo", "frances_para_ptbr", "traducao_cache_fr.json")
PASTA_LEGENDAS = r"C:\animes\Mobile_Suit_Gundam_The_Origin_Advent_of_the_Red_Comet\legendas_ptbr"
CAMINHO_SAIDA_JSON = os.path.join(PASTA_SCRIPT, "linhas_para_revisar.json")

# Padrão de resíduo francês para detecção direta
PADRAO_RESIDUO_FRANCES = re.compile(
    r"\b(vous|avec|[êe]tre|êtes|été|leur|cette|alors|où|très|pour|dans|sans|"
    r"toujours|voilà|monsieur|madame|qu['’]il|qu['’]elle|c['’]est|n['’]est|"
    r"n['’]a|d['’]un|d['’]une|cet|ceci|cela|besoin|soins|enfant|oui|non|mais|pas)\b",
    re.IGNORECASE
)

def normalizar_texto(texto: str) -> str:
    """Normaliza o texto para busca no cache (minúsculo, sem pontuação, sem tags)."""
    texto = re.sub(r'\{[^}]+\}', '', texto)
    texto = re.sub(r'\[T\d+\]', '', texto)
    texto = texto.replace(r'\N', ' ').replace(r'\n', ' ').replace(r'\h', ' ')
    texto = re.sub(r'[^\w\s]', '', texto)
    return " ".join(texto.lower().split())

def carregar_e_inverter_cache():
    """Carrega o cache original e monta o mapeamento reverso normalizado."""
    if not os.path.exists(CAMINHO_CACHE):
        print(f"[ERRO] Cache de tradução não encontrado em: {CAMINHO_CACHE}")
        sys.exit(1)
        
    with open(CAMINHO_CACHE, 'r', encoding='utf-8') as f:
        cache_original = json.load(f)
        
    print(f"[INFO] Carregando cache com {len(cache_original)} entradas...")
    
    cache_reverso = {}
    for fr, pt in cache_original.items():
        pt_norm = normalizar_texto(pt)
        if pt_norm:
            cache_reverso[pt_norm] = fr
            
    return cache_original, cache_reverso

def precisa_de_refinamento(texto_pt: str, texto_fr: str) -> bool:
    """Retorna True se a linha em português precisa ser refinada pela IA."""
    texto_pt_lower = texto_pt.lower()
    texto_fr_lower = texto_fr.lower() if texto_fr else ""

    # 1. Se o português é idêntico ao francês, com certeza precisa de tradução
    if texto_fr and normalizar_texto(texto_pt) == normalizar_texto(texto_fr):
        return True

    # 2. Resíduos franceses explícitos
    if PADRAO_RESIDUO_FRANCES.search(texto_pt) and (not any(w in texto_pt_lower for w in ["não", "como", "esta", "para", "você"])):
        return True

    # 3. Padrões de tradução incorreta de pronomes entre francês e português (ex: je -> você, tu -> ele, etc.)
    # Erro crítico: Daikun fala de si mesmo (je serai traîné) mas o PT diz "você será arrastado"
    if texto_fr_lower:
        if re.search(r"\b(je|moi)\b", texto_fr_lower) and re.search(r"\b(você|tu|ele|ela)\b", texto_pt_lower) and not re.search(r"\b(eu|me|mim|meu|minha)\b", texto_pt_lower):
            # Exclui casos comuns onde 'je' e 'vous' estão na mesma frase e a tradução focou no interlocutor
            if not re.search(r"\b(vous|tu)\b", texto_fr_lower):
                return True

    # 4. Termos críticos de Lore ou erros ortográficos comuns de Gundam
    termos_lore = [
        "golgotha", "guerra de cem anos", "guerra do ano um", "satélite colonizante preto",
        "tim ray", "mu zuo", "mucho também", "muzeo", "zamyam", "escuadrão", "muelle de atracag",
        "roda de repuesto", "flagship"
    ]
    if any(t in texto_pt_lower for t in termos_lore):
        return True

    # 5. Problemas de concordância de gênero com personagens femininas
    nomes_femininos = ["artesia", "sayla", "kycilia", "hamon", "astraia", "roselucia", "zena", "mineva"]
    adjetivos_masculinos = [
        r"\bcansado\b", r"\bpreocupado\b", r"\bsozinho\b", r"\bobrigado\b", 
        r"\bpronto\b", r"\bvindo\b", r"\bobediente\b", r"\bseguro\b", r"\besgotado\b",
        r"\bmorto\b", r"\btraidor\b", r"\bele\b"
    ]
    if any(nome in texto_pt_lower for nome in nomes_femininos):
        # Se na fala tiver um nome feminino E um adjetivo ou pronome masculino
        if any(re.search(adj, texto_pt_lower) for adj in adjetivos_masculinos):
            return True
        if any(re.search(rf"\bo\s+{nome}", texto_pt_lower) for nome in nomes_femininos):
            return True
        
        # Comparação direta de marcadores de gênero francês -> português
        if "seule" in texto_fr_lower and "sozinho" in texto_pt_lower:
            return True
        if "prête" in texto_fr_lower and "pronto" in texto_pt_lower:
            return True
        if "morte" in texto_fr_lower and "morto" in texto_pt_lower:
            return True
        if "fatiguée" in texto_fr_lower and "cansado" in texto_pt_lower:
            return True

    # Problemas de concordância de gênero com personagens masculinos
    nomes_masculinos = ["casval", "ramba", "ral", "dozle", "degwin", "sasro", "garma", "char"]
    adjetivos_femininos = [
        r"\bcansada\b", r"\bpreocupada\b", r"\bsozinha\b", r"\bobrigada\b", 
        r"\bpronta\b", r"\bvinda\b", r"\bobediente\b", r"\bsegura\b", r"\besgotada\b",
        r"\bmorta\b", r"\btraidora\b", r"\bela\b"
    ]
    if any(nome in texto_pt_lower for nome in nomes_masculinos):
        if any(re.search(adj, texto_pt_lower) for adj in adjetivos_femininos):
            # Ramba Ral como 'guarda-costas' (feminino) pode ser um falso positivo aceitável se for 'seu guarda-costas',
            # mas vamos extrair para garantir a concordância
            return True
        if any(re.search(rf"\ba\s+{nome}", texto_pt_lower) for nome in nomes_masculinos):
            return True

    # 6. Patentes militares em francês que possam ter vazado
    patentes_fr = ["amiral", "général", "colonel", "lieutenant", "sous-lieutenant", "sergent", "caporal"]
    if any(pat in texto_pt_lower for pat in patentes_fr):
        return True

    # 7. Erros gritantes de capitalização no meio de frases
    if re.search(r'[a-z\u00e0-\u00fa],\s+[A-Z]', texto_pt):
        return True

    return False

def extrair():
    cache_original, cache_reverso = carregar_e_inverter_cache()
    
    if not os.path.exists(PASTA_LEGENDAS):
        print(f"[ERRO] Pasta de legendas não encontrada: {PASTA_LEGENDAS}")
        return

    arquivos_ass = sorted([f for f in os.listdir(PASTA_LEGENDAS) if f.lower().endswith('.ass')])
    if not arquivos_ass:
        print(f"[AVISO] Nenhum arquivo .ass em: {PASTA_LEGENDAS}")
        return

    print(f"[INFO] Escaneando {len(arquivos_ass)} arquivos ASS...")
    linhas_para_revisar = []
    pat_dialogue = re.compile(r"^(Dialogue:\s*[^,]*(?:,[^,]*){8},)(.*)$")

    for arquivo in arquivos_ass:
        caminho_file = os.path.join(PASTA_LEGENDAS, arquivo)
        with open(caminho_file, 'r', encoding='utf-8-sig') as f:
            linhas = f.readlines()

        for idx, linha in enumerate(linhas):
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

            original_fr = None
            modo = "revisao_apenas_pt"
            
            # 1. Verifica se a própria fala na legenda é francesa
            if PADRAO_RESIDUO_FRANCES.search(texto_puro) and (not any(w in texto_puro.lower() for w in ["não", "como", "esta", "para", "você"])):
                original_fr = texto_dialogo
                modo = "traducao_direta"
            else:
                # 2. Busca no cache reverso normalizado
                pt_norm = normalizar_texto(texto_dialogo)
                if pt_norm in cache_reverso:
                    original_fr = cache_reverso[pt_norm]
                    modo = "revisao_completa"
                elif texto_dialogo in cache_original:
                    original_fr = texto_dialogo
                    modo = "revisao_completa"

            # Se achou uma fala com desalinhamento óbvio no cache
            if original_fr and "artesia" in texto_dialogo.lower() and "docteur" in original_fr.lower():
                modo = "traducao_direta"

            if precisa_de_refinamento(texto_dialogo, original_fr):
                linhas_para_revisar.append({
                    "arquivo": arquivo,
                    "linha_idx": idx,
                    "linha_num": idx + 1,
                    "texto_pt": texto_dialogo,
                    "original_fr": original_fr if original_fr else "",
                    "modo": modo
                })

    with open(CAMINHO_SAIDA_JSON, 'w', encoding='utf-8') as f:
        json.dump(linhas_para_revisar, f, indent=2, ensure_ascii=False)

    print(f"[CONCLUÍDO] Extraídas {len(linhas_para_revisar)} linhas suspeitas para {CAMINHO_SAIDA_JSON}")

if __name__ == "__main__":
    extrair()
