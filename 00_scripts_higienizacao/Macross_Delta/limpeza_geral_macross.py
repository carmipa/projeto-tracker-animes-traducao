import re
import glob
import sys

def limpar_legendas_macross(pasta_alvo):
    files = glob.glob(pasta_alvo + r'\*.ass')
    if not files:
        print("Nenhum arquivo .ass encontrado na pasta.")
        return

    replacements_macross = {
        # Lore e Patentes de Esquadrão Delta
        r'Capitão Arad': r'Major Arad',
        r'Comandante Arad': r'Major Arad',
        r'Capitão Wright': r'Major Wright',
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
        # Barras duplas e limpeza bruta de ASS
        r'\\\\N': r'\\N',
        r'\\\\n': r'\\N',
        r'\\N\s+\\N': r'\\N',
        r'\\N  ': r'\\N '
    }

    processados = 0
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()

        for old, new in replacements_macross.items():
            content = re.sub(old, new, content)

        # Regra de Ouro Universal: Desgruda o \N de qualquer caractere adjacente
        content = re.sub(r'\\N([a-zA-ZáéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ])', r'\\N \1', content)

        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"Limpeza aplicada em: {file}")
        processados += 1
        
    print(f"\nTotal processado: {processados} episódios.")

if __name__ == '__main__':
    alvo = sys.argv[1] if len(sys.argv) > 1 else r"E:\animes\MACROSS\Macross-Delta-br\macross_delta\legendas_eng"
    limpar_legendas_macross(alvo)
