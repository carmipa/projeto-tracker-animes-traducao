import re
import glob
import sys

def limpar_legendas_guilty_crown(pasta_alvo):
    files = glob.glob(pasta_alvo + r'\*.ass')
    if not files:
        print("Nenhum arquivo .ass encontrado na pasta.")
        return

    replacements_guilty = {
        # Lore e Patentes GHQ
        r'Major Geral Yan': r'Major-General Yan',
        r'Tenente-General Yan': r'Major-General Yan',
        r'General de Brigada Yan': r'Major-General Yan',
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

        for old, new in replacements_guilty.items():
            content = re.sub(old, new, content)

        # Regra de Ouro (Desgruda o \N da palavra)
        content = re.sub(r'\\N([a-zA-ZáéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ])', r'\\N \1', content)

        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"Limpeza GC aplicada em: {file}")
        processados += 1
        
    print(f"\nTotal processado: {processados} episódios.")

if __name__ == '__main__':
    alvo = sys.argv[1] if len(sys.argv) > 1 else r"E:\animes\GUILTY CROWN\1080p\legendas_eng"
    limpar_legendas_guilty_crown(alvo)
