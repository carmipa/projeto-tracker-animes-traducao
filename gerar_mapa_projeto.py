#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UTILITÁRIO: gerar_mapa_projeto.py
Varre todas as pastas físicas do repositório, extrai as docstrings de cabeçalho
de todos os scripts Python e gera um arquivo Markdown unificado ('mapa_projeto.md')
com o mapa estrutural completo. Ideal para fornecer como contexto para LLMs (como Qwen/Claude).
"""

import os
import re

PASTAS_IGNORAR = {".git", ".venv", "__pycache__", ".idea", ".cursor", ".claude", "docs", "multiplexar", "legendas-traduzidas-ptbr"}

def extrair_docstring(caminho_arquivo):
    """Extrai os primeiros comentários ou docstrings do script Python."""
    docstring = []
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8', errors='replace') as f:
            linhas = f.readlines()
            
        lendo_docstring_tripla = False
        
        for linha in linhas[:40]:  # Analisa as primeiras 40 linhas do script
            linha_strip = linha.strip()
            
            # Pula shebang ou encoding
            if linha_strip.startswith("#!") or "coding:" in linha_strip:
                continue
                
            # Trata docstrings triplas (python standard)
            if '"""' in linha_strip or "'''" in linha_strip:
                if not lendo_docstring_tripla:
                    lendo_docstring_tripla = True
                    # Tenta pegar conteúdo na mesma linha se houver
                    conteudo = linha_strip.replace('"""', '').replace("'''", "").strip()
                    if conteudo:
                        docstring.append(conteudo)
                else:
                    lendo_docstring_tripla = False
                continue
                
            if lendo_docstring_tripla:
                docstring.append(linha.rstrip('\n'))
                continue
                
            # Trata comentários normais do topo (#)
            if linha_strip.startswith("#"):
                docstring.append(linha_strip.lstrip("#").strip())
            elif not linha_strip and not docstring:
                # Pula linhas em branco no comeco, mas se ja começou a ler, mantém
                continue
            elif not lendo_docstring_tripla and not linha_strip.startswith("#") and docstring:
                # Sai se encontrar codigo e ja terminou os comentarios do topo
                break
    except Exception as e:
        return f"Erro ao ler arquivo: {e}"
        
    return "\n".join(docstring).strip()

def gerar_mapa():
    pasta_raiz = os.path.dirname(os.path.abspath(__file__))
    linhas_mapa = [
        "# MAPA ESTRUTURAL DO PROJETO - TRACKER ANIMES",
        f"Gerado em: {os.path.basename(pasta_raiz)}",
        "Este documento serve como mapa de contexto para LLMs atualizarem a documentação oficial.",
        "---",
        ""
    ]
    
    # Lista e ordena as pastas na raiz do projeto
    itens = sorted(os.listdir(pasta_raiz))
    pastas_projeto = []
    
    for item in itens:
        caminho = os.path.join(pasta_raiz, item)
        if os.path.isdir(caminho) and item not in PASTAS_IGNORAR:
            pastas_projeto.append(item)
            
    # Varre cada pasta e seus arquivos .py
    for pasta in pastas_projeto:
        linhas_mapa.append(f"## 📁 Pasta: `{pasta}/`")
        caminho_pasta = os.path.join(pasta_raiz, pasta)
        
        # Procura arquivos .py de forma recursiva dentro da subpasta
        arquivos_py = []
        for root, dirs, files in os.walk(caminho_pasta):
            for file in files:
                if file.lower().endswith('.py'):
                    caminho_rel = os.path.relpath(os.path.join(root, file), pasta_raiz)
                    arquivos_py.append(caminho_rel)
                    
        arquivos_py.sort()
        
        if not arquivos_py:
            linhas_mapa.append("*(Nenhum script Python nesta pasta)*\n")
            continue
            
        for arq in arquivos_py:
            caminho_completo = os.path.join(pasta_raiz, arq)
            doc = extrair_docstring(caminho_completo)
            nome_basename = os.path.basename(arq)
            
            linhas_mapa.append(f"### 📄 Arquivo: `{arq}`")
            if doc:
                linhas_mapa.append("```text")
                linhas_mapa.append(doc)
                linhas_mapa.append("```")
            else:
                linhas_mapa.append("*(Sem docstring ou cabeçalho explicativo)*")
            linhas_mapa.append("")
            
        linhas_mapa.append("---")
        
    caminho_saida = os.path.join(pasta_raiz, "mapa_projeto.md")
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        f.write("\n".join(linhas_mapa) + "\n")
        
    print(f"[SUCESSO] Mapa do projeto gerado em: {caminho_saida}")

if __name__ == "__main__":
    gerar_mapa()
