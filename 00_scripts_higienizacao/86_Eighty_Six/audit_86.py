import re
import glob
import sys

def auditar_86(pasta_alvo, arquivo_saida):
    files = glob.glob(pasta_alvo + r'\*.ass')
    if not files:
        print("Nenhum arquivo .ass encontrado na pasta.")
        return

    # Patentes e jargões icônicos de 86
    ranks = [r'major', r'capitão', r'capitao', r'handler', r'undertaker', r'spearhead', r'processador', r'processor', r'juggernaut', r'legion', r'alba', r'colorata']
    regex_ranks = re.compile(r'\b(?:' + '|'.join(ranks) + r')\b', flags=re.IGNORECASE)

    regex_anomalies = [
        (r'\\N[a-zA-ZáéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ]', "N grudado"),
        (r'\\\\N|\\\\n', "Barra dupla"),
        (r'Tradução revisada:|Traduction:|ÉPISODE', "Alucinação LLM"),
        (r'\\Net\b|\\NIl\b', "Franglês residual")
    ]

    output_lines = []
    output_lines.append("# Auditoria de 86 (Eighty Six) - Patentes e Lore\n")

    total_format_errors = 0
    for file in sorted(files):
        ep_match = re.search(r'_(\d{2})_', file)
        ep_name = ep_match.group(1) if ep_match else "Unknown"
        
        with open(file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        ep_issues = []
        for i, line in enumerate(lines):
            line = line.strip()
            if not line.startswith('Dialogue:'):
                continue
                
            parts = line.split(',', 9)
            if len(parts) > 9:
                text = parts[9]
                
                # Check formatação de IA
                for p, name in regex_anomalies:
                    if re.search(p, text):
                        total_format_errors += 1
                
                # Check Lore de 86
                matches = regex_ranks.findall(text)
                if matches:
                    ep_issues.append(f"- **L{i+1}** (Lore: {', '.join(matches)}): `{text}`")
                    
        if ep_issues:
            output_lines.append(f"## Episódio {ep_name}")
            output_lines.extend(ep_issues[:20]) # Amostragem de até 20 menções
            if len(ep_issues) > 20:
                output_lines.append(f"... (e mais {len(ep_issues)-20} menções à lore)")
            output_lines.append("\n")

    output_lines.insert(1, f"**TOTAL DE ERROS DE FORMATAÇÃO DA IA (\\\\N colado, etc): {total_format_errors}**\n")

    with open(arquivo_saida, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    print(f"Auditoria pesada de 86 concluída! Relatório salvo em {arquivo_saida}")
    print(f"Total de bugs de formatação identificados: {total_format_errors}")

if __name__ == '__main__':
    alvo = sys.argv[1] if len(sys.argv) > 1 else r"E:\animes\86\legendas_eng"
    saida = sys.argv[2] if len(sys.argv) > 2 else r"C:\Users\Paulo\.gemini\antigravity-ide\brain\7e7da94d-6e7f-4cb9-9363-8a967fba6560\scratch\86_report.md"
    auditar_86(alvo, saida)
