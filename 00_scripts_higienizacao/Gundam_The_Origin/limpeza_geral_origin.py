import re
import glob
import sys

def limpar_legendas_origin(pasta_alvo):
    files = glob.glob(pasta_alvo + r'\*.ass')
    if not files:
        print("Nenhum arquivo .ass encontrado na pasta.")
        return

    replacements_origin = {
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
        # Patentes
        r'VAml\b': r'Vice-Almirante',
        r'Lt\b': r'Tenente',
        r'commandant\b': r'Comandante',
        # Barras duplas
        r'\\\\N': r'\\N',
        r'\\\\n': r'\\N',
        r'\\N\s+\\N': r'\\N',
        # Espaços duplos
        r'\\N  ': r'\\N '
    }

    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()

        for old, new in replacements_origin.items():
            content = re.sub(old, new, content)

        # Regra de Ouro (Desgruda o \N da palavra)
        content = re.sub(r'\\N([a-zA-ZáéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ])', r'\\N \1', content)

        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"Limpeza aplicada em: {file}")

if __name__ == '__main__':
    # Alvo default ou pelo arg
    alvo = sys.argv[1] if len(sys.argv) > 1 else r"C:\animes\Mobile_Suit_Gundam_The_Origin_Advent_of_the_Red_Comet\legendas_ptbr"
    limpar_legendas_origin(alvo)
