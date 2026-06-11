#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MÓDULO: conversor_srt_para_ass.py (Modo Dinâmico com Correção de FPS)
Responsável por converter a legenda SRT traduzida para o formato estruturado ASS,
permitindo a escolha dinâmica de diretórios via console e aplicando correção matemática
de sincronismo progressivo (fator de escala de frame rate 25fps -> 23.976fps).

Author: Paulo + Gemini
Data: Maio 2026
Status: PRODUCTION SYNC CORRECTED
"""

import os
import re
import sys
from tqdm import tqdm
from colorama import init, Fore, Style

# Inicializa o Colorama para tratamento de escapes ANSI no terminal do Windows
init(autoreset=True)

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))

# Cabeçalho rígido padrão para conformidade com a especificação ASS (v4.00+)
CABEÇALHO_ASS_TEMPLATE = """[Script Info]
Title: {titulo} - Localized PT-BR
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
Collisions: Normal
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,45,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,3,0,2,30,30,45,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# Cadeia de fallback de encoding (mesmo padrão usado no pipeline de tradução)
ENCODINGS_FALLBACK = ['utf-8-sig', 'utf-8', 'cp1252', 'latin-1', 'iso-8859-1']

def ler_srt_com_encoding(caminho):
    """Tenta ler o SRT percorrendo a cadeia de encodings. Retorna (conteudo, encoding_usado)."""
    for enc in ENCODINGS_FALLBACK:
        try:
            with open(caminho, 'r', encoding=enc) as f:
                conteudo = f.read()
            return conteudo, enc
        except UnicodeDecodeError:
            continue

    print(f"{Fore.YELLOW}[AVISO] Falha na cadeia de encodings. Forçando UTF-8 com substituição.")
    with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
        conteudo = f.read()
    return conteudo, 'utf-8-bypass'

def converter_tempo_para_segundos(tempo_srt):
    """Converte a string de tempo SRT (00:00:00,000) em segundos decimais (float)."""
    vias = tempo_srt.replace(',', '.').split(':')
    horas = int(vias[0])
    minutos = int(vias[1])
    segundos = float(vias[2])
    return horas * 3600 + minutos * 60 + segundos

def converter_segundos_para_ass(segundos_totais):
    """Converte segundos decimais (float) de volta para o padrão estrito do formato ASS (0:00:00.00)."""
    if segundos_totais < 0:
        segundos_totais = 0.0
    # Arredonda antes para evitar estouro na formatação de segundos (ex: 59.999 -> 60.00)
    segundos_totais = round(segundos_totais, 2)
    horas = int(segundos_totais // 3600)
    minutos = int((segundos_totais % 3600) // 60)
    segundos = segundos_totais % 60
    # O formato ASS exige obrigatoriamente 2 casas decimais para centésimos (ex: 05.22)
    return f"{horas}:{minutos:02d}:{segundos:05.2f}"

def obter_diretorio_operador(mensagem_prompt, padrao_caminho=None):
    """Captura e valida a entrada de diretórios fornecida pelo usuário."""
    while True:
        sufixo_padrao = f" (ENTER = {padrao_caminho})" if padrao_caminho else ""
        entrada = input(f"{Fore.YELLOW}{mensagem_prompt}{sufixo_padrao}: {Style.RESET_ALL}").strip()
        entrada = entrada.strip('"').strip("'")
        
        if not entrada and padrao_caminho:
            return padrao_caminho
            
        if not entrada:
            print(f"{Fore.RED}[ERRO] O caminho não pode ser vazio.")
            continue
            
        if not os.path.isdir(entrada):
            print(f"{Fore.RED}[ERRO] O diretório especificado não existe fisicamente: {entrada}")
            continue
            
        return entrada

def executar_conversao_industrial():
    print("=" * 80)
    print(f"{Fore.CYAN}            CONVERSOR DE PARSING COM AJUSTE DE FPS: SRT ➔ ASS")
    print("=" * 80)
    
    # 1. Coleta dinâmica dos caminhos de infraestrutura
    caminho_padrao_origem = r"C:\TRACKER-ANIMES\projeto-tracker-animes-traducao\5_tradutor_de_legenda"
    # Tenta resolver o caminho dinamicamente caso o canônico (C:) não exista
    if not os.path.isdir(caminho_padrao_origem):
        projeto_dir = os.path.abspath(os.path.join(PASTA_SCRIPT, ".."))
        caminho_alternativo = os.path.join(projeto_dir, "4_tradutor_ia_gemma4", "5_tradutor_de_legenda")
        if os.path.isdir(caminho_alternativo):
            caminho_padrao_origem = caminho_alternativo
        else:
            caminho_alternativo_raiz = os.path.join(projeto_dir, "5_tradutor_de_legenda")
            if os.path.isdir(caminho_alternativo_raiz):
                caminho_padrao_origem = caminho_alternativo_raiz
                
    pasta_origem = obter_diretorio_operador("Digite a pasta onde está a legenda SRT de origem", caminho_padrao_origem)
    
    pasta_saida = obter_diretorio_operador("Digite a pasta onde deseja salvar o arquivo ASS convertido", pasta_origem)
    
    # 2. Escaneamento automático de arquivos SRT
    arquivos_srt = sorted([f for f in os.listdir(pasta_origem) if f.lower().endswith('.srt')])
    
    if not arquivos_srt:
        print(f"\n{Fore.RED}[ERRO] Nenhuma legenda SRT (.srt) localizada na pasta especificada.")
        return
    
    # Seleção de arquivo se houver múltiplos
    if len(arquivos_srt) == 1:
        arquivo_selecionado = arquivos_srt[0]
        print(f"\n{Fore.GREEN}[OK] Detectado arquivo: {arquivo_selecionado}")
    else:
        print(f"\n{Fore.CYAN}Múltiplos arquivos SRT localizados:")
        for idx, arq in enumerate(arquivos_srt, 1):
            print(f"  {idx}. {arq}")
        while True:
            try:
                num = input(f"\n{Fore.YELLOW}Selecione o número da legenda desejada: {Style.RESET_ALL}").strip()
                escolha = int(num) - 1
                if 0 <= escolha < len(arquivos_srt):
                    arquivo_selecionado = arquivos_srt[escolha]
                    break
                print(Fore.RED + "[ERRO] Opção fora do intervalo válido.")
            except ValueError:
                print(Fore.RED + "[ERRO] Digite um número inteiro correspondente.")

    arquivo_alvo = os.path.join(pasta_origem, arquivo_selecionado)
    
    # Detecção dinâmica do nome base do filme (limpa os sufixos comuns de idioma para o título)
    nome_base_detectado = re.sub(r'[_.-](ptbr|eng)\.srt$', '', arquivo_selecionado, flags=re.IGNORECASE)
    nome_base_detectado = os.path.splitext(nome_base_detectado)[0]
    
    # Escolha de fator de escala de sincronismo (FPS)
    print(f"\n{Fore.CYAN}Configuração de Sincronismo (FPS Scale):")
    print("  - Digite 1.0 se a legenda já estiver sincronizada (padrão)")
    print("  - Digite 1.042709 para converter de 25fps para 23.976fps (ex: Macross Delta)")
    
    fator_input = input(f"{Fore.YELLOW}Fator de sincronismo [1.0]: {Style.RESET_ALL}").strip()
    try:
        FATOR_SINCRO = float(fator_input) if fator_input else 1.0
    except ValueError:
        print(Fore.RED + "[AVISO] Entrada inválida. Utilizando fator padrão de 1.0")
        FATOR_SINCRO = 1.0

    # Escolha de deslocamento/atraso (Offset)
    print(f"\n{Fore.CYAN}Ajuste de Deslocamento Temporal (Offset):")
    print("  - Digite o valor em milissegundos para adiantar/atrasar a legenda (ex: 30489 ou -1500)")
    offset_input = input(f"{Fore.YELLOW}Deslocamento em milissegundos [0]: {Style.RESET_ALL}").strip()
    try:
        OFFSET_MS = float(offset_input) if offset_input else 0.0
    except ValueError:
        print(Fore.RED + "[AVISO] Entrada inválida. Utilizando offset padrão de 0 ms")
        OFFSET_MS = 0.0
        
    offset_segundos = OFFSET_MS / 1000.0
        
    # Salva mantendo a nomenclatura original (ex: _ENG.srt -> _ENG.ass, _PTBR.srt -> _PTBR.ass)
    nome_sem_ext = os.path.splitext(arquivo_selecionado)[0]
    arquivo_saida_ass = os.path.join(pasta_saida, f"{nome_sem_ext}.ass")
    
    # Garante a existência física da pasta de saída no NVMe
    os.makedirs(pasta_saida, exist_ok=True)
    
    print(f"\n{Fore.YELLOW}Iniciando conversão de {arquivo_selecionado} com Fator Sincro = {FATOR_SINCRO} e Offset = {OFFSET_MS} ms...")

    conteudo_srt, encoding_usado = ler_srt_com_encoding(arquivo_alvo)
    print(f"{Fore.GREEN}[OK] Encoding detectado: {encoding_usado.upper()}")

    # Normaliza quebras de linha (CRLF/CR -> LF) para garantir o casamento da regex
    conteudo_srt = conteudo_srt.replace('\r\n', '\n').replace('\r', '\n')

    # Expressão regular para capturar os blocos SRT estruturalmente
    # Lookahead estrito valida o índice numérico seguido de um timestamp para prevenir estouro em linhas com números
    padrao_srt = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n([\s\S]*?)(?=\n\d+\n\d{2}:\d{2}:\d{2},\d{3} --> |\Z)')
    blocos = padrao_srt.findall(conteudo_srt)

    if not blocos:
        print(f"\n{Fore.RED}[ERRO] Nenhum bloco de legenda válido foi reconhecido em {arquivo_selecionado}.")
        print(f"{Fore.RED}Verifique se o arquivo está no formato SRT padrão (número, timestamp, texto).")
        return

    eventos_ass = []
    
    # Esteira industrial com barra de progresso tqdm
    for bloco in tqdm(blocos, desc="Recalculando Timestamps", unit="bloco", 
                      bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} blocos [{elapsed}]"):
        _, inicio_bruto, fim_bruto, texto_bruto = bloco
        
        # Passo 1: Transforma as marcações de tempo fixas do SRT em segundos puros (float)
        segundos_inicio = converter_tempo_para_segundos(inicio_bruto)
        segundos_fim = converter_tempo_para_segundos(fim_bruto)
        
        # Passo 2: Multiplica o tempo pelo fator de escala e aplica o offset
        segundos_inicio_corrigido = segundos_inicio * FATOR_SINCRO + offset_segundos
        segundos_fim_corrigido = segundos_fim * FATOR_SINCRO + offset_segundos
        
        # Passo 3: Converte os segundos recalculados de volta para a string do protocolo ASS
        inicio_ass = converter_segundos_para_ass(segundos_inicio_corrigido)
        fim_ass = converter_segundos_para_ass(segundos_fim_corrigido)
        
        # Sanitização e mapeamento de quebras de linha e tags HTML para formato ASS
        texto_sanitizado = texto_bruto.strip().replace('\n', r'\N')
        texto_sanitizado = texto_sanitizado.replace('<i>', '{\\i1}').replace('</i>', '{\\i0}')
        texto_sanitizado = texto_sanitizado.replace('<b>', '{\\b1}').replace('</b>', '{\\b0}')
        texto_sanitizado = texto_sanitizado.replace('<u>', '{\\u1}').replace('</u>', '{\\u0}')
        
        linha_dialogo = f"Dialogue: 0,{inicio_ass},{fim_ass},Default,,0,0,0,,{texto_sanitizado}"
        eventos_ass.append(linha_dialogo)
        
    # 3. Consolidação final e persistência física de dados
    cabecalho = CABEÇALHO_ASS_TEMPLATE.format(titulo=nome_base_detectado)
    conteudo_final_ass = cabecalho + "\n".join(eventos_ass) + "\n"
    
    with open(arquivo_saida_ass, 'w', encoding='utf-8') as f:
        f.write(conteudo_final_ass)
        
    print("\n" + "=" * 80)
    print(f"{Fore.GREEN}[SUCESSO] Conversão finalizada com sucesso!")
    print(f"{Fore.GREEN}Novo arquivo ASS gerado em: {arquivo_saida_ass}")
    print("=" * 80)

if __name__ == "__main__":
    try:
        executar_conversao_industrial()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[AVISO] Operação interrompida pelo operador (Ctrl+C).")
        sys.exit(0)