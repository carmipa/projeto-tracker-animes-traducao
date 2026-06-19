import re
import glob
import sys
import os

def limpar_legendas_orgun(pasta_alvo):
    # Procura ASS e SRT
    files = glob.glob(os.path.join(pasta_alvo, '*.ass')) + glob.glob(os.path.join(pasta_alvo, '*.srt'))
    if not files:
        print("Nenhum arquivo .ass ou .srt encontrado na pasta.")
        return

    replacements_orgun = {
        # Lore Orgun
        r'\bEarth Defense Force\b': r'E.D.F.',
        r'\bEDF\b': r'E.D.F.',
        r'\bE\.D\.F\b': r'E.D.F.',
        r'\ba E.D.F.\b': r'a E.D.F.',
        r'\bo Orgun\b': r'Orgun',
        r'\bdo Orgun\b': r'de Orgun',
        r'\bao Orgun\b': r'a Orgun',

        # Formatação ASS e pequenos defeitos do Mistral em PTBR
        r'\\Net ': r'\\N e ',
        r'\\NEt ': r'\\N E ',
        r'\\\\N': r'\\N',
        r'\\\\n': r'\\N',
        r'\\N\s+\\N': r'\\N',
        r'\\N  ': r'\\N ',
        r'\[ERRO_TRADUCAO\]': r''
    }

    processados = 0
    for file in files:
        is_ass = file.lower().endswith('.ass')
        with open(file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        for old, new in replacements_orgun.items():
            content = re.sub(old, new, content, flags=re.IGNORECASE)

        if is_ass:
            # Regra de Ouro (Desgruda o \N da palavra)
            content = re.sub(r'\\N([a-zA-ZáéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ])', r'\\N \1', content)

        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"Limpeza Orgun (Lore + Formatação) aplicada em: {os.path.basename(file)}")
        processados += 1
        
    print(f"\nTotal processado: {processados} legendas.")

if __name__ == '__main__':
    alvo = sys.argv[1] if len(sys.argv) > 1 else r"E:\animes\DETONATOR ORGUN\legendas_ptbr"
    limpar_legendas_orgun(alvo)
