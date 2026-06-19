import re
import glob
import sys

def limpar_legendas_unicorn(pasta_alvo):
    files = glob.glob(pasta_alvo + r'\*.ass')
    if not files:
        print("Nenhum arquivo .ass encontrado na pasta.")
        return

    replacements_unicorn = {
        # Lore e Gêneros Corrompidos
        r'da Tenente Riddhe': r'do Tenente Riddhe',
        r'A General Revil': r'O General Revil',
        r'\\NSela parece': r'\\NEle parece',
        r'Sela parece': r'Ele parece',
        r'Operao V': r'Operação V',
        r'mais rpido': r'mais rápido',
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

    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()

        for old, new in replacements_unicorn.items():
            content = re.sub(old, new, content)

        # Regra de Ouro (Desgruda o \N da palavra)
        content = re.sub(r'\\N([a-zA-ZáéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ])', r'\\N \1', content)

        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"Limpeza aplicada em: {file}")

if __name__ == '__main__':
    alvo = sys.argv[1] if len(sys.argv) > 1 else r"E:\animes\GUNDAM\GUNDAM UC\UC 0096 - UNICORN\Mobile Suit Gundam Unicorn Re0096\legendas_eng"
    limpar_legendas_unicorn(alvo)
