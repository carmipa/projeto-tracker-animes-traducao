import re
import glob
import sys

def limpar_legendas_86(pasta_alvo):
    files = glob.glob(pasta_alvo + r'\*.ass')
    if not files:
        print("Nenhum arquivo .ass encontrado na pasta.")
        return

    replacements_86 = {
        # Lore 86
        r'Ponta de Lança': r'Spearhead',
        r'ponta de lança': r'Spearhead',

        # Flexão de Gênero para Vladilena Milizé (Lena)
        r'\bo major\b': r'a major',
        r'\bO major\b': r'A major',
        r'\bO Major\b': r'A Major',
        r'\bdo major\b': r'da major',
        r'\bDo major\b': r'Da major',
        r'\bDo Major\b': r'Da Major',
        r'\bao major\b': r'à major',
        r'\bAo major\b': r'À major',
        r'\bAo Major\b': r'À Major',
        r'\bum major\b': r'uma major',
        r'\bUm major\b': r'Uma major',
        r'\bUm Major\b': r'Uma Major',

        r'\bo handler\b': r'a handler',
        r'\bO handler\b': r'A handler',
        r'\bO Handler\b': r'A Handler',
        r'\bdo handler\b': r'da handler',
        r'\bDo handler\b': r'Da handler',
        r'\bDo Handler\b': r'Da Handler',
        r'\bao handler\b': r'à handler',
        r'\bAo handler\b': r'À handler',
        r'\bAo Handler\b': r'À Handler',
        r'\bum handler\b': r'uma handler',
        r'\bUm handler\b': r'Uma handler',
        r'\bUm Handler\b': r'Uma Handler',

        r'\bo Capitão Milizé\b': r'a Capitã Milizé',
        r'\bO Capitão Milizé\b': r'A Capitã Milizé',

        r'major ainda está vivo\?': r'major ainda está viva?',
        r'major está bem\?': r'major está bem?', # 'bem' is neutral
        
        # Alucinações
        r'Tradução revisada: ': r'',
        r'Tradução revisada:': r'',
        r'Traduction: ': r'',
        r'ÉPISODE': r'EPISÓDIO',
        r'EPISODE': r'EPISÓDIO',
        
        # Franglês 
        r'\\Net ': r'\\N e ',
        r'\\NEt ': r'\\N E ',
        r'\\NIl ': r'\\N Ele ',
        r'\\Nmais ': r'\\N mas ',
        r'\\Nune ': r'\\N uma ',
        r'\\Nun ': r'\\N um ',
        r'\beuh\.\.\.': r'hã...',
        
        # Barras duplas 
        r'\\\\N': r'\\N',
        r'\\\\n': r'\\N',
        r'\\N\s+\\N': r'\\N',
        r'\\N  ': r'\\N '
    }

    processados = 0
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()

        for old, new in replacements_86.items():
            content = re.sub(old, new, content)

        # Regra de Ouro (Desgruda o \N da palavra)
        content = re.sub(r'\\N([a-zA-ZáéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ])', r'\\N \1', content)

        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"Limpeza 86 (Lore + Gender) aplicada em: {file}")
        processados += 1
        
    print(f"\nTotal processado: {processados} episódios.")

if __name__ == '__main__':
    alvo = sys.argv[1] if len(sys.argv) > 1 else r"C:\animes\86\86 Part1\legendas_eng"
    limpar_legendas_86(alvo)
